# Morning Briefing Agent - AWS Weekend Challenge

An AI-powered agent deployed on AWS that generates a personalized motivational morning brief and a developer productivity tip every day, sent straight to your email.

The agent is powered by **AWS Lambda**, **Amazon Bedrock (Amazon Nova Micro)**, and **Amazon SNS**.

## Architecture Overview

```mermaid
graph TD
    Cron[EventBridge Rule: Daily 8 AM] -->|Triggers| Lambda[Morning Brief Lambda]
    HTTP[Lambda Function URL: HTTP Trigger] -->|Triggers (Test Anytime)| Lambda
    Lambda -->|1. Invoke Model| Bedrock[Amazon Bedrock: Amazon Nova Micro]
    Bedrock -->|2. Returns Quote/Tip| Lambda
    Lambda -->|3. Publish Message| SNS[SNS Topic: MorningBriefingTopic]
    SNS -->|4. Email Notification| Email[Developer's Email Inbox]
```

## Features

- **Daily Automation**: Automatically triggered every morning at 8:00 AM UTC via AWS EventBridge (CloudWatch Events).
- **Test-Anytime Function URL**: Includes a public Lambda Function URL endpoint so you can trigger a briefing immediately at any time without waiting for 8:00 AM.
- **Amazon Nova Micro**: Uses Amazon Bedrock's lightweight, high-performance Nova model for cost-efficient text content generation.
- **SNS Integration**: Dispatches briefings to an SNS topic configured to forward messages to your email address.

---

## Prerequisites

Before deploying, ensure you have the following set up:

1. **AWS CLI** configured with administrative permissions.
2. **Verify Bedrock Model Access**:
   Verify that **Amazon Nova Micro** is available in your region (recommended: `us-west-2`) using the AWS CLI:
   ```bash
   aws bedrock list-foundation-models --region us-west-2
   ```
   If the AWS Console "Model access" page fails to load, this command is the most reliable way to check active model permissions.
3. **Python 3.9+** (if you want to run the test and demo helper scripts locally).

---

## Deployment Instructions

### Option 1: Deploying via the AWS CLI (CloudFormation)

1. Open `template.yaml` and update the `AgentSNSSubscription` resource's `Endpoint` property with your email address:
   ```yaml
     AgentSNSSubscription:
       Type: AWS::SNS::Subscription
       Properties:
         TopicArn: !Ref AgentSNSTopic
         Endpoint: "YOUR_EMAIL@EXAMPLE.COM" # Change this to your email
         Protocol: email
   ```
2. Deploy the stack using the AWS CLI (targeting `us-west-2`):
   ```bash
   aws cloudformation deploy \
     --template-file template.yaml \
     --stack-name morning-brief-agent \
     --capabilities CAPABILITY_IAM \
     --region us-west-2
   ```

### Option 2: Deploying via the AWS Console
1. Copy the contents of `template.yaml`.
2. Go to the **AWS CloudFormation Console** -> **Create Stack** -> **With new resources (standard)**.
3. Select **Template is ready** -> **Upload a template file** (or paste it using Designer). Upload `template.yaml`.
4. Enter a stack name (e.g., `morning-brief-agent`).
5. Complete the wizard and check **I acknowledge that AWS CloudFormation might create IAM resources**. Click **Submit**.

---

## Post-Deployment Setup (Crucial!)

1. **Confirm Email Subscription**:
   - Check the inbox of the email address you specified.
   - Look for an email from **AWS Notifications** with the subject **AWS Notification - Subscription Confirmation**.
   - Click the **Confirm Subscription** link in the email.
   - *Note: You will not receive any briefings until this subscription is confirmed.*

2. **Retrieve the Function Test URL**:
   - In the AWS CloudFormation Console, select your stack (`morning-brief-agent`).
   - Navigate to the **Outputs** tab.
   - Copy the value of the **`TestUrl`** output (e.g. `https://xxxx.lambda-url.us-east-1.on.aws/`).

---

## Testing & Demo Guide

We provide a helper script, `demo.py`, to make testing and validation easy.

### 1. Local Dry-Run (Test Bedrock setup without deploying)
You can run Bedrock locally to verify your AWS credentials, regional settings, and model access:
```bash
# Install boto3 dependency if you haven't already
pip install boto3

# Run the local dry-run (targeting us-west-2)
python demo.py local --region us-west-2
```

### 2. Test Deployed Agent via Function URL (Test Anytime)
Trigger your deployed Lambda function immediately using the public Function URL (no AWS credentials required on the client side):
```bash
# Using the demo script:
python demo.py url --url https://xxxx.lambda-url.us-east-1.on.aws/

# Or using curl/Invoke-WebRequest:
curl https://xxxx.lambda-url.us-east-1.on.aws/
```
If successful, you will receive the HTTP 200 response: `"Briefing sent successfully!"`, and a briefing email will land in your inbox.

### 3. Test Deployed Agent via AWS SDK (Invoke Lambda)
Trigger the Lambda function directly using your local AWS CLI credentials:
```bash
python demo.py sdk --function MorningBriefAgent --region us-west-2
```

---

## Troubleshooting

- **Error: "ModelNotAllowedException" or Access Denied when calling Bedrock**:
  Ensure you are deploying in a region where Bedrock is active and Nova Micro is enabled (recommended: `us-west-2`). Verify this using:
  ```bash
  aws bedrock list-foundation-models --region us-west-2
  ```
- **No emails received**:
  - Verify that you confirmed the SNS subscription from the automated email.
  - Check your spam folder.
  - Review the Lambda logs in **Amazon CloudWatch** (log group `/aws/lambda/MorningBriefAgent`) to check for any execution errors.
