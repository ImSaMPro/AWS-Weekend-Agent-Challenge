# 💸 AWS Cost Whisperer

> *"Will this cost me money?"* — the question every AWS beginner whispers before clicking **Deploy**.

The **Cost Whisperer** is a friendly, on-demand chat agent that answers exactly that. Ask it anything about AWS billing, the Free Tier, or whether a service you just spun up is quietly running up a bill — and it replies in calm, plain English, always flagging the Free-Tier angle so you can breathe easy.

No dashboards to decode. No pricing PDFs. Just a conversation.

---

## Why this exists

AWS pricing is genuinely intimidating when you're starting out. The Billing console is a wall of line items, and the official docs assume you already know what a "request" or an "egress GB" is. The Cost Whisperer sits in front of all that with one job: **reduce the fear**. It talks to you like a patient friend who happens to know AWS, not like a spreadsheet.

## What it does

- **Chats in real time** — type a question, get a friendly answer in a second or two.
- **Always surfaces the Free-Tier angle** — if something *usually* stays free, it says so; if there's a gotcha, it warns you kindly.
- **Never scares you with a raw error** — if the model hiccups, it reassures you ("nothing was charged — try again") instead of dumping a stack trace.
- **Friendly first run** — it greets you and offers three one-tap starter questions, so you're never staring at a blank box.

## Architecture

One Lambda does everything. It serves its own chat page on `GET` and answers questions on `POST`. That's the whole backend.

```
   ┌──────────────┐   GET  /  (serves the chat UI)
   │   Browser    │ ───────────────────────────────┐
   │  (chat UI)   │   POST /  { "message": "..." }  │
   └──────────────┘ ──────────────┐                 │
          ▲                        ▼                 ▼
          │              ┌───────────────────────────────┐
          └──────────────│   Lambda Function URL (NONE)   │
             JSON reply  │   cost-whisperer  (arm64/128MB)│
                         └───────────────┬───────────────┘
                                         │ InvokeModel
                                         ▼
                         ┌───────────────────────────────┐
                         │  Amazon Bedrock — Nova Micro   │
                         │     (the Whisperer persona)    │
                         └───────────────────────────────┘
```

**Deliberately minimal:** no S3, no API Gateway, no DynamoDB, no CloudFront. A single Lambda with a Function URL *is* the app — it even hosts its own HTML. That's the cheapest shape that still delivers a real conversational agent.

## AWS services used

| Service | Role | Free Tier |
|---------|------|-----------|
| **AWS Lambda** (arm64, 128 MB) | Serves the UI and runs the chat logic | 1M requests + 400k GB-seconds / month |
| **Lambda Function URL** | Public HTTPS endpoint, no API Gateway | Included with Lambda |
| **Amazon Bedrock** (Nova Micro) | The agent's "brain" / personality | Low per-token cost; tiny for text chat |
| **Amazon CloudWatch Logs** | Function logs, retention capped at 14 days | 5 GB ingestion / month |
| **AWS IAM** | Least-privilege role (logs + one model) | Free |

## Prerequisites

- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html), configured (`aws configure` or `aws sso login`).
- **Amazon Bedrock model access** for **Nova Micro** enabled in your region. In the Bedrock console → *Model access* → request access to `amazon.nova-micro-v1:0`. This is a one-time click and is required, or the agent can't think.
- Region used throughout: **`us-east-1`**.

## Deploy

From inside the `Cost-Whisperer/` folder:

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name cost-whisperer \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

> `CAPABILITY_NAMED_IAM` is needed because the template creates a named IAM role (`cost-whisperer-role`).

Deployment takes under a minute — there's no CloudFront distribution to wait on.

## Use it

Grab the chat URL from the stack outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name cost-whisperer \
  --query "Stacks[0].Outputs" \
  --output table \
  --region us-east-1
```

Open the **`WhispererUrl`** value in your browser — it looks like
`https://<id>.lambda-url.us-east-1.on.aws/`. Say hi and start asking.

Prefer the terminal? The same endpoint answers JSON:

```bash
curl -s -X POST "<WhispererUrl>" \
  -H "Content-Type: application/json" \
  -d '{"message":"Does leaving an S3 bucket empty cost anything?"}'
```

## Cleanup / Teardown

No bucket to empty, so teardown is a single command:

```bash
aws cloudformation delete-stack \
  --stack-name cost-whisperer \
  --region us-east-1
```

The template creates its own CloudWatch Log Group (`/aws/lambda/cost-whisperer`) with retention set, so deleting the stack removes the logs too — no orphaned log group left behind to quietly accrue.

Confirm it's gone:

```bash
aws cloudformation describe-stacks \
  --stack-name cost-whisperer \
  --region us-east-1
# -> "Stack with id cost-whisperer does not exist" means fully torn down.
```

## Cost note

Chatting a few dozen times a day with Nova Micro over text costs cents at most, and Lambda + Function URL + CloudWatch stay inside the Free Tier for this kind of usage. The agent itself will happily explain this to you — just ask it *"will running you cost me money?"*

---

Built by **Soumyadeep Mandal** · [LinkedIn](https://www.linkedin.com/in/imsampro) · part of the [AWS Weekend Agent Challenge](https://github.com/ImSaMPro/AWS-Weekend-Agent-Challenge).
