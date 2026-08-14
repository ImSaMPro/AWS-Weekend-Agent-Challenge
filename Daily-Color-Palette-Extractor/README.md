# 🎨 Daily Color Palette Extractor

A serverless, client-side web application that extracts the 5 dominant colors from any uploaded image. Runs entirely in the browser with no backend or AI APIs required.

## Features

- **Drag & drop** or click-to-upload image input
- **Median Cut algorithm** for accurate color quantization
- **5 dominant colors** displayed as visual swatches
- **Click-to-copy** hex codes to clipboard with visual feedback
- **Keyboard accessible** (Tab + Enter/Space to copy)
- **Responsive** design that works on mobile and desktop
- **Zero backend** — all processing happens in the browser via Canvas API

## Architecture

```
┌─────────────┐        ┌──────────────────┐        ┌────────────┐
│   Browser   │──HTTPS──▶  CloudFront CDN  │──OAC───▶  S3 Bucket │
│  (User)     │◀────────│  (Distribution)  │◀───────│  (Private) │
└─────────────┘        └──────────────────┘        └────────────┘
```

- **S3 Bucket**: Stores `index.html` (private, no public access)
- **CloudFront**: Serves content over HTTPS with caching and compression
- **Origin Access Control (OAC)**: Securely connects CloudFront to S3 without making the bucket public

## Prerequisites

- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) installed and configured
- An AWS account with permissions to create S3, CloudFront, and IAM resources
- AWS CLI profile configured (`aws configure`)

## Deployment Instructions

### Step 1: Deploy the CloudFormation Stack

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name daily-color-palette-extractor \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

> **Note**: `us-east-1` is recommended for CloudFront distributions, but any region works.

Wait for the stack to complete (typically 3-5 minutes for CloudFront distribution creation).

### Step 2: Get the S3 Bucket Name

```bash
aws cloudformation describe-stacks \
  --stack-name daily-color-palette-extractor \
  --query "Stacks[0].Outputs" \
  --output table \
  --region us-east-1
```

This will show:
- **S3BucketName** — The bucket to upload files to
- **CloudFrontDomainName** — The URL to access your app
- **CloudFrontDistributionId** — Useful for cache invalidation

### Step 3: Upload the Application

```bash
aws s3 cp index.html s3://<YOUR-BUCKET-NAME>/index.html \
  --content-type "text/html" \
  --region us-east-1
```

Replace `<YOUR-BUCKET-NAME>` with the S3BucketName from the stack outputs.

### Step 4: Access the Application

Open the **CloudFrontDomainName** URL from the stack outputs in your browser. It looks like:

```
https://d1234abcdef8.cloudfront.net
```

> **Note**: CloudFront may take a few minutes to propagate after initial deployment.

## Cleanup

To remove all resources and avoid ongoing charges:

```bash
# Empty the S3 bucket first (required before stack deletion)
aws s3 rm s3://<YOUR-BUCKET-NAME> --recursive

# Delete the CloudFormation stack
aws cloudformation delete-stack \
  --stack-name daily-color-palette-extractor \
  --region us-east-1
```

## How It Works

1. User uploads an image (drag-and-drop or file picker)
2. Image is drawn to a hidden `<canvas>` element, scaled down for performance
3. `getImageData()` reads all pixel RGBA values
4. The **Median Cut** algorithm recursively splits the color space along the channel (R, G, or B) with the greatest range, dividing pixels into 5 buckets
5. Each bucket is averaged to produce a representative dominant color
6. Colors are sorted by luminance (dark → light) and rendered as swatches
7. Clicking a swatch copies the hex code to clipboard via the Clipboard API

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Algorithm | Median Cut Color Quantization |
| Hosting | Amazon S3 (static files) |
| CDN | Amazon CloudFront (HTTPS + caching) |
| IaC | AWS CloudFormation |
| Security | Origin Access Control (OAC) |
