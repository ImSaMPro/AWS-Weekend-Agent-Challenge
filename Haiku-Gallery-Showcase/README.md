# 🖋️ Haiku Gallery Showcase

An always-on creative agent that generates a unique, themed haiku every morning, emails it to you, **and** publishes it to a beautiful public web gallery served over HTTPS. This is the season-finale showcase build — it combines an autonomous AI agent with a static web app into one polished project.

## Vision

The best creative tool is one you never have to open. This agent runs on its own every morning: it reads the season and the day of the week, asks Amazon Bedrock for a haiku, then delivers it two ways — straight to your inbox and onto a live web page anyone can visit. You wake up, and today's haiku is already waiting.

## What It Does

Every day at 8:00 AM UTC, the agent:

1. Determines the current **season** and a **day-of-week theme** (Monday = new beginnings, Friday = gratitude, etc.)
2. Prompts **Amazon Bedrock (Nova Micro)** to write a 5-7-5 haiku
3. **Emails** it via Amazon SNS
4. **Publishes** it as `latest.json` to S3
5. The static web page reads that JSON and renders today's haiku in an elegant gallery — served securely through CloudFront

## Architecture

```
                        ┌──────────────────┐
   EventBridge (cron) ──▶  AWS Lambda       │──▶ Amazon Bedrock (Nova Micro)
        8 AM UTC        │  (Python 3.12)    │◀── returns haiku
                        │                   │
                        │                   │──▶ Amazon SNS ──▶ 📧 Email
                        │                   │──▶ S3: latest.json
                        └──────────────────┘         │
                                                      ▼
   Browser ──HTTPS──▶ CloudFront ──OAC──▶ S3 (private bucket)
                                          index.html + latest.json
```

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| EventBridge | Daily cron trigger | Always free |
| Lambda | Generation + publishing logic | 1M requests/month free |
| Bedrock (Nova Micro) | AI haiku generation | Free tier credits for new accounts |
| SNS | Email delivery | 1,000 emails/month free |
| S3 | Hosts the site + daily JSON | 5GB free |
| CloudFront | HTTPS delivery + caching | 1TB/month free |

## Prerequisites

- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) installed and configured
- Bedrock model access enabled for **Amazon Nova Micro** in your region
- A valid email address

### Enable Bedrock Model Access

1. Open **Amazon Bedrock** → **Model access** in your region
2. Click **Manage model access**
3. Enable **Amazon Nova Micro** and save

## Deployment

### Step 1: Deploy the Stack

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name haiku-gallery \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides EmailAddress=your@email.com \
  --region us-east-1
```

### Step 2: Confirm Your Email

Check your inbox for the AWS SNS subscription confirmation and click **Confirm subscription**.

### Step 3: Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name haiku-gallery \
  --query "Stacks[0].Outputs" \
  --output table \
  --region us-east-1
```

Note the **S3BucketName**, **GalleryUrl**, **TestUrl**, and **CloudFrontDistributionId**.

### Step 4: Upload the Web Page

```bash
aws s3 cp index.html s3://<YOUR-BUCKET-NAME>/index.html \
  --content-type "text/html" \
  --region us-east-1
```

### Step 5: Generate the First Haiku

Trigger the agent so `latest.json` exists (otherwise the page shows "not ready yet"):

```bash
curl <YOUR-TEST-URL>
```

> **Troubleshooting "Forbidden" on the Test URL**: Public Function URLs require two permissions (since Oct 2025). If you get a Forbidden error, add them manually:
> ```bash
> aws lambda add-permission --function-name haiku-gallery-agent \
>   --statement-id UrlInvokeUrl --action lambda:InvokeFunctionUrl \
>   --principal "*" --function-url-auth-type NONE --region us-east-1
>
> aws lambda add-permission --function-name haiku-gallery-agent \
>   --statement-id UrlInvoke --action lambda:InvokeFunction \
>   --principal "*" --region us-east-1
> ```

### Step 6: Visit the Gallery

Open the **GalleryUrl** in your browser. Today's haiku is live.

> CloudFront may take a few minutes to propagate after the first deploy.

## Cleanup

**⚠️ Follow this fully to avoid any ongoing charges.**

### Automated Cleanup

The S3 bucket must be emptied before the stack can delete:

```bash
# 1. Empty the S3 bucket (required before stack deletion)
aws s3 rm s3://<YOUR-BUCKET-NAME> --recursive --region us-east-1

# 2. Delete the stack
aws cloudformation delete-stack \
  --stack-name haiku-gallery \
  --region us-east-1

# 3. Wait for deletion to complete
aws cloudformation wait stack-delete-complete \
  --stack-name haiku-gallery \
  --region us-east-1
```

### Manual Cleanup (If Automated Cleanup Fails or Misses Anything)

CloudFormation sometimes leaves resources behind (especially non-empty buckets and log groups). Verify and clean up manually if needed.

#### 1. Confirm the stack is gone

```bash
aws cloudformation describe-stacks --stack-name haiku-gallery --region us-east-1 2>&1
```

"Stack does not exist" means success. If it says `DELETE_FAILED`, check what's stuck:

```bash
aws cloudformation describe-stack-events --stack-name haiku-gallery --region us-east-1 \
  --query "StackEvents[?ResourceStatus=='DELETE_FAILED']"
```

#### 2. Empty and delete the S3 bucket (most common blocker)

```bash
aws s3 rm s3://<YOUR-BUCKET-NAME> --recursive --region us-east-1
aws s3 rb s3://<YOUR-BUCKET-NAME> --region us-east-1
```

#### 3. Delete the CloudWatch Log Group (NOT auto-deleted)

```bash
aws logs delete-log-group \
  --log-group-name /aws/lambda/haiku-gallery-agent \
  --region us-east-1
```

> **This is the most commonly missed resource.** Lambda creates it automatically and CloudFormation does not remove it.

#### 4. Delete remaining resources manually (only if stack delete failed)

```bash
# Lambda function
aws lambda delete-function --function-name haiku-gallery-agent --region us-east-1

# SNS topic
aws sns delete-topic \
  --topic-arn arn:aws:sns:us-east-1:<YOUR-ACCOUNT-ID>:haiku-gallery-topic \
  --region us-east-1

# EventBridge rule (remove targets first)
aws events remove-targets --rule haiku-gallery-schedule --ids HaikuLambdaTarget --region us-east-1
aws events delete-rule --name haiku-gallery-schedule --region us-east-1

# IAM role (delete inline policies first)
aws iam delete-role-policy --role-name haiku-gallery-lambda-role --policy-name CloudWatchLogsPolicy
aws iam delete-role-policy --role-name haiku-gallery-lambda-role --policy-name BedrockInvokePolicy
aws iam delete-role-policy --role-name haiku-gallery-lambda-role --policy-name SNSPublishPolicy
aws iam delete-role-policy --role-name haiku-gallery-lambda-role --policy-name S3WritePolicy
aws iam delete-role --role-name haiku-gallery-lambda-role
```

> **Note on CloudFront**: The distribution is deleted by the stack automatically. If you deleted resources manually, CloudFront distributions take ~15 minutes to fully disable and delete — this is normal and incurs no charge once initiated.

#### 5. Final verification (everything should return empty)

```bash
aws lambda list-functions --region us-east-1 --query "Functions[?contains(FunctionName, 'haiku')]"
aws sns list-topics --region us-east-1 --query "Topics[?contains(TopicArn, 'haiku')]"
aws events list-rules --region us-east-1 --query "Rules[?contains(Name, 'haiku')]"
aws s3 ls | grep haiku-gallery
aws logs describe-log-groups --region us-east-1 --log-group-name-prefix /aws/lambda/haiku-gallery
```

If all return empty, everything is cleaned up and you will **not** be charged.

## Cost

With normal usage (1 run/day), this project costs effectively **$0** — every service stays comfortably within the AWS Free Tier.

## What I Learned Across the Summer

- **Week 1 (Wishlist app)** taught me to scope tightly and ship
- **Week 2 (Creative app)** — the Color Palette Extractor — got me comfortable with pure client-side processing and S3 + CloudFront hosting with Origin Access Control
- **Week 3 (Agent)** — the Daily Haiku Agent — introduced EventBridge scheduling, Bedrock, and SNS for an autonomous, always-on workflow
- **This finale** brought it together: an agent that not only acts on its own but also feeds a polished web front-end. The key lesson was that combining small, well-scoped builds produces something that feels far bigger than the sum of its parts.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Trigger | Amazon EventBridge (Cron) |
| Compute | AWS Lambda (Python 3.12) |
| AI/ML | Amazon Bedrock (Nova Micro) |
| Delivery | Amazon SNS (Email) |
| Storage | Amazon S3 |
| CDN | Amazon CloudFront + OAC |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| IaC | AWS CloudFormation |

---

*Designed & built by Soumyadeep*
