# AWS Weekend Agent Challenge

Welcome to the AWS Weekend Agent Challenge repository! This repository hosts a collection of AI-powered agent solutions built on AWS serverless technologies.

## Projects in this Repository

### 1. [Morning Brief Agent](file:///d:/Projects/GitHub/AWS-Weekend-Agent-Challenge/Morning%20Brief%20Agent)
An automated AI agent that sends a motivating morning quote and a developer productivity tip directly to your email inbox every day at 8:00 AM UTC. 

- **Key Technologies**: AWS Lambda, Amazon Bedrock (Amazon Nova Micro), Amazon SNS, EventBridge.
- **Key Enhancements**: Includes a **Test-Anytime Function URL** allowing you to trigger a test briefing instantly via HTTP.
- **Links**:
  - [App Code (app.py)](file:///d:/Projects/GitHub/AWS-Weekend-Agent-Challenge/Morning%20Brief%20Agent/app.py)
  - [CloudFormation Template (template.yaml)](file:///d:/Projects/GitHub/AWS-Weekend-Agent-Challenge/Morning%20Brief%20Agent/template.yaml)
  - [Project README](file:///d:/Projects/GitHub/AWS-Weekend-Agent-Challenge/Morning%20Brief%20Agent/README.md)
  - [Testing Helper (demo.py)](file:///d:/Projects/GitHub/AWS-Weekend-Agent-Challenge/Morning%20Brief%20Agent/demo.py)

---

## Quick Start

To deploy and test the Morning Brief Agent, follow these steps:

1. **Verify Model Availability**: Verify that **Amazon Nova Micro** is available in your region (recommended: `us-west-2`) using the AWS CLI:
   ```bash
   aws bedrock list-foundation-models --region us-west-2
   ```
2. **Configure Email**: Open [template.yaml](file:///d:/Projects/GitHub/AWS-Weekend-Agent-Challenge/Morning%20Brief%20Agent/template.yaml) and update the `Endpoint` under `AgentSNSSubscription` with your email.
3. **Deploy the Stack**:
   ```bash
   cd "Morning Brief Agent"
   aws cloudformation deploy \
     --template-file template.yaml \
     --stack-name morning-brief-agent \
     --capabilities CAPABILITY_IAM \
     --region us-west-2
   ```
4. **Confirm Subscription**: Check your email and click the confirmation link sent by AWS SNS.
5. **Test Anytime**: Retrieve the `TestUrl` output from CloudFormation and trigger a briefing instantly:
   ```bash
   python "Morning Brief Agent/demo.py" url --url <YOUR_LAMBDA_FUNCTION_URL>
   ```

For detailed deployment steps, architecture flows, and troubleshooting, read the [Morning Brief Agent README](file:///d:/Projects/GitHub/AWS-Weekend-Agent-Challenge/Morning%20Brief%20Agent/README.md).
