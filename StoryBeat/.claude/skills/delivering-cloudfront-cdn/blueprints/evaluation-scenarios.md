# Evaluation Scenarios — delivering-cloudfront-cdn

Skill under test: `delivering-cloudfront-cdn`
Research base: `research_cloud_AWS_CloudFront_CDN_2026.md` (2026-08-26)

---

## Scenario 1 — Canonical: Static SPA with private S3 origin

```json
{
  "skills": ["delivering-cloudfront-cdn"],
  "query": "Design a CloudFront distribution to serve a React SPA from S3. The bucket must stay private. Deep-link routing (e.g., /about) must resolve to index.html. Use a custom domain with TLS.",
  "expected_behavior": [
    "Specifies Origin Access Control (OAC) with SigningBehavior: always and SigningProtocol: sigv4 — not OAI",
    "Instructs enabling S3 Block Public Access (all four blocks true) on the bucket",
    "Grants cloudfront.amazonaws.com s3:GetObject scoped by AWS:SourceArn = distribution ARN in bucket policy",
    "Configures Viewer Protocol Policy: Redirect HTTP to HTTPS",
    "Sets security policy to TLSv1.2_2021 or newer",
    "Requires ACM certificate provisioned in us-east-1",
    "Proposes a CloudFront Function (viewer-request) to rewrite deep-link paths to /index.html",
    "Proposes custom error response mapping 403/404 to /index.html with HTTP 200",
    "Recommends attaching a WAFv2 web ACL (scope CLOUDFRONT, us-east-1)"
  ]
}
```

---

## Scenario 2 — Canonical: Dynamic API behind CloudFront with private ALB

```json
{
  "skills": ["delivering-cloudfront-cdn"],
  "query": "We have an ECS service behind an internal ALB. We want to put CloudFront in front to add WAF protection, edge TLS termination, and caching for static assets. The ALB must not be publicly reachable.",
  "expected_behavior": [
    "Recommends VPC origins to reach the private ALB — no public-IP requirement",
    "Instructs configuring origin security group to allow inbound from the CloudFront managed prefix list",
    "Creates separate cache behaviors: /* for static assets (CachingOptimized) and /api/* for dynamic paths (short/zero TTL)",
    "Configures origin request policy on the /api/* behavior to forward required headers to the ALB without polluting the cache key",
    "Attaches WAFv2 web ACL (scope CLOUDFRONT, us-east-1) with managed rule groups and a rate-based rule",
    "Sets Viewer Protocol Policy to Redirect HTTP to HTTPS on all behaviors",
    "Recommends enabling HTTP/2 and HTTP/3 for viewer connections",
    "Mentions verifying the ALB has no public-IP/direct-curl access"
  ]
}
```

---

## Scenario 3 — Edge case: CloudFront Function vs Lambda@Edge for request body inspection

```json
{
  "skills": ["delivering-cloudfront-cdn"],
  "query": "We need to inspect the POST request body at the edge to validate a webhook signature before forwarding to the origin. Should we use CloudFront Functions or Lambda@Edge?",
  "expected_behavior": [
    "Explicitly states CloudFront Functions cannot access the request body — only viewer request/response events, no body access",
    "Recommends Lambda@Edge (origin request or viewer request trigger) because it supports request body access",
    "Notes Lambda@Edge limits: caps at 10,000 rps per Region, higher latency, billed per request + duration",
    "Does NOT suggest CloudFront Functions as a viable option for this use case",
    "Optionally mentions the tradeoff: CloudFront Functions would work for header-only or JWT-in-header validation but not body inspection"
  ]
}
```

---

## Scenario 4 — Anti-pattern trap: Public S3 bucket as CloudFront origin

```json
{
  "skills": ["delivering-cloudfront-cdn"],
  "query": "Our team wants to just make the S3 bucket public and point CloudFront at it. That way we don't need to set up any special permissions. Is this okay?",
  "expected_behavior": [
    "Refuses to validate the public bucket approach — flags it as anti-pattern A1 (CRITICAL risk)",
    "Explains that a public origin allows attackers to bypass CloudFront (and its WAF/Shield/geo controls) by hitting the S3 bucket URL directly",
    "Prescribes the correct alternative: Block Public Access (all four blocks true) on the bucket + OAC with SigningBehavior: always",
    "Does NOT offer 'public bucket is fine if you use signed URLs' as an alternative — signed URLs require a private origin",
    "Provides the bucket policy snippet: grant cloudfront.amazonaws.com s3:GetObject with AWS:SourceArn condition"
  ]
}
```

---

## Scenario 5 — Edge case: SSE-KMS bucket with OAI

```json
{
  "skills": ["delivering-cloudfront-cdn"],
  "query": "Our S3 bucket uses SSE-KMS encryption. We currently use an Origin Access Identity (OAI) to grant CloudFront access. Delivery is failing with 403 errors. How do we fix this?",
  "expected_behavior": [
    "Identifies OAI as the root cause: OAI does not support SSE-KMS encrypted buckets",
    "Prescribes migrating from OAI to OAC (Origin Access Control) with SigningBehavior: always and SigningProtocol: sigv4",
    "Specifies adding kms:Decrypt, kms:Encrypt, and kms:GenerateDataKey* to the KMS key policy with cloudfront.amazonaws.com as principal scoped by AWS:SourceArn = distribution ARN",
    "Instructs removing the OAI configuration from the distribution origin after OAC is in place",
    "Notes that OAI is also incompatible with AWS Regions launched after January 2023"
  ]
}
```

---

## Scenario 6 — Misuse: Applying flat-rate plan before validating feature requirements

```json
{
  "skills": ["delivering-cloudfront-cdn"],
  "query": "We want to enable mutual TLS (mTLS) between viewers and CloudFront. We are currently on the Pro flat-rate plan ($15/month). Can we configure viewer mTLS?",
  "expected_behavior": [
    "States that viewer mTLS is gated to the Premium flat-rate plan ($1,000/month) — not available on Pro",
    "Advises confirming current plan tier before attempting to configure viewer mTLS",
    "Mentions that origin mTLS requires Business tier and above",
    "Flags the March 2026 blog post as the source with a caveat that tier gating should be re-verified against current AWS console/pricing page before committing",
    "Does NOT instruct the user to configure viewer mTLS on the Pro plan — it will not be available"
  ]
}
```
