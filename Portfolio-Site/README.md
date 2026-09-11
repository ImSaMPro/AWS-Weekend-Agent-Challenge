# ☁️ Portfolio Site (S3 + CloudFront)

A fast, responsive single-page **portfolio website** hosted on a **private Amazon S3 bucket** served securely over HTTPS through **Amazon CloudFront** using **Origin Access Control (OAC)**. The entire infrastructure is defined in a single AWS CloudFormation template and stays comfortably within the **AWS Free Tier**.

Built by **Soumyadeep Mandal** — [linkedin.com/in/imsampro](https://www.linkedin.com/in/imsampro)

---

## Features

- **Private by default** — the S3 bucket blocks all public access; only CloudFront can read it
- **HTTPS everywhere** — CloudFront redirects HTTP → HTTPS automatically
- **Fast global delivery** — CDN caching, gzip/Brotli compression, HTTP/2 + HTTP/3
- **Responsive design** — looks good on mobile, tablet, and desktop
- **Zero servers, zero maintenance** — pure static hosting
- **Single-file front end** — `index.html` with inline CSS and JS (no build step)
- **Free Tier friendly** — `PriceClass_100`, minimal resources

## Architecture

```
┌─────────────┐        ┌──────────────────┐        ┌────────────┐
│   Browser   │──HTTPS──▶  CloudFront CDN  │──OAC───▶  S3 Bucket │
│   (Visitor) │◀────────│  (Distribution)  │◀───────│  (Private) │
└─────────────┘        └──────────────────┘        └────────────┘
```

- **S3 Bucket** — stores `index.html` (private, all public access blocked, SSE-S3 encrypted)
- **CloudFront** — serves content over HTTPS with caching and compression
- **Origin Access Control (OAC)** — securely connects CloudFront to S3 without making the bucket public; the bucket policy is scoped to this exact distribution via `AWS:SourceArn`
- **CloudFormation** — one `template.yaml` provisions everything

## Prerequisites

- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) installed
- An AWS account with permission to create S3, CloudFront, and IAM resources
- Configured credentials (`aws configure`, or `aws sso login` + `--profile <name>`)

> All commands below use `us-east-1`. Add `--profile <your-profile>` to each command if you use named profiles.

---

## Deployment (step by step)

### Step 1 — Deploy the CloudFormation stack

From inside the `Portfolio-Site` folder:

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name portfolio-site \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

CloudFront distribution creation typically takes **3–5 minutes**. Wait for the stack to reach `CREATE_COMPLETE`.

### Step 2 — Read the stack outputs

```bash
aws cloudformation describe-stacks \
  --stack-name portfolio-site \
  --query "Stacks[0].Outputs" \
  --output table \
  --region us-east-1
```

You'll get:

| Output | Meaning |
|--------|---------|
| **S3BucketName** | The bucket to upload your site into |
| **CloudFrontDomainName** | The public HTTPS URL of your portfolio |
| **CloudFrontDistributionId** | Used for cache invalidation on updates |

### Step 3 — Upload the site

Replace `<YOUR-BUCKET-NAME>` with the `S3BucketName` from Step 2:

```bash
aws s3 cp index.html s3://<YOUR-BUCKET-NAME>/index.html \
  --content-type "text/html" \
  --region us-east-1
```

> Uploading more assets later? Use `aws s3 sync . s3://<YOUR-BUCKET-NAME>/ --exclude "template.yaml" --exclude "README.md"` and set correct `--content-type` values (or add per-type `sync` calls).

### Step 4 — Open your portfolio

Open the **CloudFrontDomainName** URL in a browser. It looks like:

```
https://d1234abcdef8.cloudfront.net
```

> First-time propagation can take a few minutes.

### Step 5 — Updating the site later

After editing `index.html`, re-upload (Step 3) and then invalidate the CloudFront cache so visitors see the change immediately:

```bash
aws cloudfront create-invalidation \
  --distribution-id <YOUR-DISTRIBUTION-ID> \
  --paths "/*" \
  --region us-east-1
```

Use the `CloudFrontDistributionId` from Step 2.

---

## 🧹 Cleanup / Teardown

Remove **everything** to avoid any ongoing charges. Order matters — the bucket must be emptied before the stack can be deleted.

### Step 1 — Empty the S3 bucket

```bash
aws s3 rm s3://<YOUR-BUCKET-NAME> --recursive --region us-east-1
```

### Step 2 — Delete the CloudFormation stack

```bash
aws cloudformation delete-stack \
  --stack-name portfolio-site \
  --region us-east-1
```

### Step 3 — Confirm deletion (optional)

```bash
aws cloudformation wait stack-delete-complete \
  --stack-name portfolio-site \
  --region us-east-1
```

When this returns with no error, all resources (S3 bucket, bucket policy, OAC, and CloudFront distribution) have been removed.

> If `delete-stack` ever fails because the bucket is not empty, re-run Step 1 and delete again.

---

## Cost

Designed for the **AWS Free Tier**:

- **S3** — a few KB of storage and minimal requests
- **CloudFront** — 1 TB/month data transfer out and 10M requests/month are free for the first 12 months (`PriceClass_100` limits edge locations to the cheapest regions)
- **CloudFormation** — free

Idle cost is effectively **\$0** for a personal portfolio.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Front end | HTML5, CSS3, Vanilla JavaScript (single file) |
| Hosting | Amazon S3 (private bucket) |
| CDN / TLS | Amazon CloudFront (HTTPS + caching) |
| Security | Origin Access Control (OAC) |
| IaC | AWS CloudFormation |

---

Built by **Soumyadeep Mandal** — [linkedin.com/in/imsampro](https://www.linkedin.com/in/imsampro)
