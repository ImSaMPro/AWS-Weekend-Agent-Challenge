# 🖋️ Daily Haiku Agent

An always-on creative agent that generates a unique, themed haiku every morning and delivers it to your inbox — powered by Amazon Bedrock (Nova Micro) and deployed entirely with AWS CloudFormation.

## What It Does

Every day at 8:00 AM UTC, this agent:

1. Determines the current **season** and a **day-of-week theme** (e.g., Monday = new beginnings, Friday = gratitude)
2. Crafts a prompt incorporating those themes
3. Calls **Amazon Bedrock (Nova Micro)** to generate a contemplative haiku
4. Sends the haiku to your email via **Amazon SNS**

You wake up, check your email, and there's a fresh haiku waiting. No apps to open, no buttons to press.

## Architecture

```
┌────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌───────────┐
│  EventBridge   │──────▶│  AWS Lambda      │──────▶│ Amazon Bedrock  │       │           │
│  (Cron: 8AM)   │       │  (Python 3.12)   │◀──────│ (Nova Micro)    │       │  Amazon   │
└────────────────┘       │                  │──────▶│                 │       │   SNS     │
                         └─────────────────┘       └─────────────────┘       │  (Email)  │
                                                                              └───────────┘
```

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| EventBridge | Cron trigger (daily schedule) | Always free |
| Lambda | Runs the haiku generation logic | 1M requests/month free |
| Bedrock (Nova Micro) | AI text generation | Free tier credits for new accounts |
| SNS | Email delivery | 1,000 emails/month free |
| CloudWatch Logs | Lambda execution logs | 5GB/month free |

## Prerequisites

- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) installed and configured
- AWS account with Bedrock model access enabled for **Amazon Nova Micro** in your region
- A valid email address for receiving haikus

### Enable Bedrock Model Access

Before deploying, you must enable access to Nova Micro in the AWS Console:

1. Go to **Amazon Bedrock** → **Model access** in your region
2. Click **Manage model access**
3. Enable **Amazon Nova Micro**
4. Wait for access to be granted (usually instant)

## Deployment

### Step 1: Deploy the Stack

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name daily-haiku-agent \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides EmailAddress=your@email.com \
  --region us-east-1
```

### Step 2: Confirm Your Email

Check your inbox for a subscription confirmation email from AWS SNS. Click the **Confirm subscription** link. Without this, you won't receive haikus.

### Step 3: Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name daily-haiku-agent \
  --query "Stacks[0].Outputs" \
  --output table \
  --region us-east-1
```

### Step 4: Test It Immediately

Use the **TestUrl** from the stack outputs to trigger a haiku right now:

```bash
curl <YOUR-FUNCTION-URL>
```

Or open the URL in your browser. You should receive a haiku email within seconds.

> **Troubleshooting "Forbidden" error**: If the Function URL returns `{"Message":"Forbidden"}`, manually add both required permissions (required since Oct 2025):
> ```bash
> aws lambda add-permission \
>   --function-name daily-haiku-agent \
>   --statement-id FunctionURLAllowPublicInvokeUrl \
>   --action lambda:InvokeFunctionUrl \
>   --principal "*" \
>   --function-url-auth-type NONE \
>   --region us-east-1
>
> aws lambda add-permission \
>   --function-name daily-haiku-agent \
>   --statement-id FunctionURLAllowPublicInvoke \
>   --action lambda:InvokeFunction \
>   --principal "*" \
>   --region us-east-1
> ```
> Then retry the URL. Both permissions are needed for public Function URLs.

## Customization

| Parameter | Default | Description |
|-----------|---------|-------------|
| `EmailAddress` | *(required)* | Where to send haikus |
| `ScheduleExpression` | `cron(0 8 * * ? *)` | When to generate (UTC) |
| `BedrockModelId` | `amazon.nova-micro-v1:0` | Which Bedrock model to use |

To change the schedule (e.g., 7:30 AM UTC):

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name daily-haiku-agent \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides EmailAddress=your@email.com ScheduleExpression="cron(30 7 * * ? *)" \
  --region us-east-1
```

## Cleanup

### Automated Cleanup (Delete the Stack)

This single command removes **all** resources created by the template:

```bash
aws cloudformation delete-stack \
  --stack-name daily-haiku-agent \
  --region us-east-1
```

Wait for deletion to complete:

```bash
aws cloudformation wait stack-delete-complete \
  --stack-name daily-haiku-agent \
  --region us-east-1
```

### Manual Verification (If Automated Cleanup Fails or Misses Something)

If the stack deletion fails or you want to be absolutely sure nothing is left running:

#### 1. Check the stack is actually deleted

```bash
aws cloudformation describe-stacks \
  --stack-name daily-haiku-agent \
  --region us-east-1 2>&1
```

If this returns "Stack does not exist", you're good. If it shows `DELETE_FAILED`, check the events:

```bash
aws cloudformation describe-stack-events \
  --stack-name daily-haiku-agent \
  --region us-east-1 \
  --query "StackEvents[?ResourceStatus=='DELETE_FAILED']"
```

#### 2. Delete the Lambda function manually (if stuck)

```bash
aws lambda delete-function \
  --function-name daily-haiku-agent \
  --region us-east-1
```

#### 3. Delete the SNS topic manually

```bash
# Find the topic ARN
aws sns list-topics --region us-east-1 --query "Topics[?contains(TopicArn, 'daily-haiku')]"

# Delete it
aws sns delete-topic \
  --topic-arn arn:aws:sns:us-east-1:<YOUR-ACCOUNT-ID>:daily-haiku-agent-topic \
  --region us-east-1
```

#### 4. Delete the EventBridge rule manually

```bash
# Remove targets first (required before rule deletion)
aws events remove-targets \
  --rule daily-haiku-agent-schedule \
  --ids HaikuLambdaTarget \
  --region us-east-1

# Delete the rule
aws events delete-rule \
  --name daily-haiku-agent-schedule \
  --region us-east-1
```

#### 5. Delete the IAM role manually

```bash
# Remove inline policies first
aws iam delete-role-policy \
  --role-name daily-haiku-agent-lambda-role \
  --policy-name CloudWatchLogsPolicy

aws iam delete-role-policy \
  --role-name daily-haiku-agent-lambda-role \
  --policy-name BedrockInvokePolicy

aws iam delete-role-policy \
  --role-name daily-haiku-agent-lambda-role \
  --policy-name SNSPublishPolicy

# Delete the role
aws iam delete-role --role-name daily-haiku-agent-lambda-role
```

#### 6. Delete CloudWatch Log Group (not deleted by CloudFormation by default)

```bash
aws logs delete-log-group \
  --log-group-name /aws/lambda/daily-haiku-agent \
  --region us-east-1
```

> **Important**: CloudWatch Log Groups created by Lambda are NOT automatically deleted when you delete the stack. This is the most commonly missed resource. It won't cost much, but clean it up to be thorough.

#### 7. Verify no resources remain

```bash
# Check Lambda functions
aws lambda list-functions --region us-east-1 \
  --query "Functions[?contains(FunctionName, 'haiku')]"

# Check SNS topics
aws sns list-topics --region us-east-1 \
  --query "Topics[?contains(TopicArn, 'haiku')]"

# Check EventBridge rules
aws events list-rules --region us-east-1 \
  --query "Rules[?contains(Name, 'haiku')]"

# Check CloudWatch log groups
aws logs describe-log-groups --region us-east-1 \
  --log-group-name-prefix /aws/lambda/daily-haiku
```

If all of these return empty results, everything is cleaned up and you will **not** be charged.

## Cost Considerations

With normal usage (1 invocation/day), this project costs effectively **$0**:

| Resource | Monthly Usage | Cost |
|----------|--------------|------|
| Lambda | ~30 invocations, <1s each | Free tier |
| Bedrock Nova Micro | ~30 requests, ~100 tokens each | Free tier credits / negligible |
| SNS | ~30 emails | Free tier |
| EventBridge | ~30 rule evaluations | Free tier |
| CloudWatch Logs | <1 MB | Free tier |

## How It Works

1. **EventBridge** fires a cron event at 8:00 AM UTC daily
2. **Lambda** wakes up, determines today's season + weekday theme
3. A creative prompt is built and sent to **Amazon Bedrock (Nova Micro)**
4. Bedrock returns a 3-line haiku (5-7-5 syllable structure)
5. The haiku is formatted into a clean email and published to **SNS**
6. SNS delivers the email to your confirmed address

## Example Output

```
========================================
   YOUR DAILY HAIKU
   Friday, August 15, 2026
========================================

Golden leaves descend
Friday's quiet gratitude
Wind carries them home

────────────────────────────────────────
Season: Summer
Theme: gratitude and celebration (Friday)
────────────────────────────────────────

Generated by Daily Haiku Agent
Powered by Amazon Bedrock (Nova Micro)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Trigger | Amazon EventBridge (Cron) |
| Compute | AWS Lambda (Python 3.12) |
| AI/ML | Amazon Bedrock (Nova Micro) |
| Delivery | Amazon SNS (Email) |
| IaC | AWS CloudFormation (SAM) |
| Testing | Lambda Function URL |

---

*Designed & built by Soumyadeep*
