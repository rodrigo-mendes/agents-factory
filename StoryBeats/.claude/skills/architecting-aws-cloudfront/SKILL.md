---
name: architecting-aws-cloudfront
description: "Architects secure, performant, and cost-optimized content delivery on Amazon CloudFront following AWS Well-Architected Framework (6-pillar) principles. Use when designing, reviewing, or implementing CloudFront distributions for static sites, dynamic APIs, private content delivery, or multi-origin architectures on AWS."
---

## Function

Specialist in Amazon CloudFront CDN architecture — HTTPS enforcement, edge security (AWS WAF), origin access control (OAC), cache policy design, signed content delivery, field-level encryption, and origin failover — aligned to the AWS Well-Architected Framework (6 pillars) and the CloudFront feature state as of July 2026.

## Version Context

**Technology**: Amazon CloudFront  
**Target State**: 2025 current edition (CloudFront Developer Guide — continuously updated `/latest/`)  
**Research Date**: 2026-07-31  
**Currency Threshold**: Review after 2027-07-31 — CloudFront evolves continuously

**Exact AWS service names** (always use these — no generic terms):

| Generic | Correct AWS name |
|---|---|
| "CDN" | **Amazon CloudFront** |
| "Edge WAF" | **AWS WAF** (WebACL, `CLOUDFRONT` scope) |
| "TLS cert service" | **AWS Certificate Manager (ACM)** — must be in **us-east-1** for CloudFront |
| "S3 access control" | **CloudFront Origin Access Control (OAC)** — replaces legacy **OAI** |
| "Lightweight edge compute" | **CloudFront Functions** |
| "Heavy edge compute" | **AWS Lambda@Edge** |
| "CDN private content" | signed URLs / signed cookies with **trusted key groups** |
| "CDN logs (free)" | **standard logs (v2)** |
| "CDN logs (real-time)" | **real-time logs** via **Amazon Kinesis Data Streams** |

⚠️ **Version Lock**: OAI is legacy — use **OAC** for all new S3 origins. OAI does not support SSE-KMS, dynamic requests, or AWS Regions launched after January 2023.

## Quick Navigation

- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — 14 mandatory patterns: HTTPS, TLS, WAF, logging, cache policy, error pages, origin failover, Origin Shield, geo-restriction, OAC, signed URLs, field-level encryption, price class, edge compute selection
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — 6 architectural decisions: origin type, OAC vs OAI, logging strategy, distribution topology, IPv6, continuous deployment
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — 7 critical anti-patterns with ❌ wrong / ✅ correct CLI/config pairs and blast-radius analysis
- **[Integration Patterns](./blueprints/integration-patterns.md)** — CloudFront + S3 (OAC), API Gateway, ALB, Lambda@Edge, WAF + Shield, ACM, Route 53; Service Equivalence Map
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 4 scenarios: React SPA, private video streaming, credential misuse rejection, HTTP-only anti-pattern trap
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands for post-deployment checks
- **[Quick Reference](#quick-reference)** — CloudFront limits and essential commands
- **[External Resources](#external-resources)** — Official AWS documentation

---

## Blueprints & Guardrails

### ✅ Always Do

For full patterns with CLI verification, WAF pillar alignment, and official source links, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**Mandatory patterns** (Complex tier — all 14 required; security-critical, multi-pillar):

- **Enforce HTTPS for viewer connections** — Set `ViewerProtocolPolicy` to `redirect-to-https` or `https-only` per cache behavior; back with ACM certificate in `us-east-1`. Never use `allow-all` in production.
- **Set TLSv1.2_2021+ as minimum TLS version** — Use `TLSv1.2_2021`, `TLSv1.2_2025`, or `TLSv1.3_2025` for `MinimumProtocolVersion`. TLS 1.0/1.1 are non-compliant with modern security baselines.
- **Attach AWS WAF WebACL (CLOUDFRONT scope) to every public distribution** — Create the WebACL in `us-east-1` (global scope required), attach managed rule groups, and associate to the distribution. Do not block `/.well-known/pki-validation/`.
- **Enable standard logging (v2) with S3 lifecycle policies** — Free per-request logs; standard logs v2 supports S3, Amazon CloudWatch Logs, and Amazon Kinesis Data Firehose. Pair with S3 lifecycle rules for retention.
- **Define explicit cache policy: Min/Default/Max TTL and minimal cache key** — Narrow the cache key (no unnecessary headers/cookies/query strings); move origin-only values into a separate **origin request policy**.
- **Configure custom error pages for 4xx/5xx with error caching TTL** — Map 403, 404, 500, 502, 503, 504 to custom response pages; set `ErrorCachingMinTTL` per code.
- **Configure origin groups (primary + secondary) for critical workloads** — Failover status codes: `400, 403, 404, 416, 429, 500–504`; reference the origin group in the cache behavior. Applies to `GET`, `HEAD`, `OPTIONS` only.
- **Enable Origin Shield for high-cache-hit or multi-region origins** — Choose the AWS Region with lowest latency to the origin. Not suitable for low-cacheability dynamic content or gRPC.
- **Apply geo-restriction (allowlist/blocklist) where content rights require it** — Country-level; blocked viewers receive `403`. For city/postal/per-path granularity, use AWS WAF geo match rules or signed URLs instead.
- **Use OAC for all Amazon S3 origins — keep buckets private** — `SigningBehavior: always`; S3 Object Ownership = **Bucket owner enforced**; bucket policy grants `s3:GetObject` to `cloudfront.amazonaws.com` scoped by `AWS:SourceArn` to the distribution ARN.
- **Use trusted key groups for signed URLs / signed cookies on private content** — Preferred over legacy trusted-signer (AWS-account CloudFront key pairs). Signed URLs for individual files; signed cookies for multiple files with unchanged URLs.
- **Use field-level encryption for sensitive POST fields** — Asymmetric RSA-2048; up to 10 fields per request in `application/x-www-form-urlencoded`; HTTPS-only viewer policy required; origin must integrate AWS Encryption SDK.
- **Choose price class matching actual viewer geography** — `PriceClass_All` (global, best performance), `PriceClass_200` (all except most-expensive Regions), `PriceClass_100` (North America + Europe + Israel only).
- **Right-size edge compute: CloudFront Functions for lightweight, Lambda@Edge for heavy logic** — CloudFront Functions: cache-key normalization, header manipulation, URL rewrites, simple auth (viewer request/response, sub-ms, JS only). Lambda@Edge: network access, AWS SDK, third-party libraries, body access, >2 MB memory.

### ⚠️ Ask First

For decision tables, cost profiles, and "Ask The Architect" questions, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**Architectural decisions** (confirm before committing to an approach):

- **Origin type** — S3 REST endpoint + OAC vs S3 website endpoint (custom origin, no OAC) vs Application Load Balancer vs Amazon API Gateway vs custom HTTP origin. Determines access-control mechanism, origin-to-CloudFront DTO pricing, and TLS options.
- **OAC vs OAI for S3 origins** — OAC is the current standard; OAI is legacy (no SSE-KMS, no Regions post-Jan 2023, no dynamic requests). Use OAC for all new distributions; plan migration for existing OAI.
- **Logging strategy** — Standard logs v2 (free, best-effort, minutes latency) vs real-time logs via Kinesis Data Streams (billed, seconds latency) vs CloudWatch metrics (aggregated only). Default to standard logs; add real-time only where sub-minute reaction is required.
- **Distribution topology** — Single distribution with multiple cache behaviors/origins vs multiple distributions vs multi-tenant (CloudFront SaaS Manager). Geo-restriction and some settings apply distribution-wide; split when per-property policies diverge.
- **IPv6** — Enable (default-friendly, dual-stack) vs disable. Disable only when downstream systems cannot process IPv6 client IP addresses.
- **Continuous deployment with staging distributions** — Route a subset of real production traffic to a staging distribution (header or weight-based) before promoting. Use for high-risk changes (cache policy, WAF, TLS, origin) on business-critical distributions.

### 🚫 Never Do

For ❌ wrong / ✅ correct pairs with detection commands and blast-radius analysis, see [Never Do Patterns](./blueprints/never-do-patterns.md).

**Critical prohibitions** (all 7 must be flagged before proceeding):

- **`ViewerProtocolPolicy: allow-all` on any cache behavior** — CRITICAL: cleartext HTTP exposes all viewer data to interception. Use `redirect-to-https` or `https-only` + ACM certificate.
- **Public-facing distribution with no AWS WAF WebACL** — HIGH: no edge filtering of SQLi, XSS, bad bots, or volumetric attacks. Attach a WebACL with `CLOUDFRONT` scope.
- **Caching CORS or authenticated responses without cache-key awareness** — HIGH: cached `Access-Control-Allow-Origin: *` or per-user response bodies are served to all viewers. Include relevant headers in the cache key or mark as non-cacheable.
- **Using legacy OAI on a new S3 origin** — MEDIUM: no SSE-KMS support, no Regions post-Jan 2023, no dynamic requests. Use OAC with `SigningBehavior: always` instead.
- **Public-read S3 bucket behind CloudFront (origin bypass)** — HIGH: direct S3 URL access bypasses WAF, signed URLs, and logs. Block Public Access on, OAC signing, bucket policy scoped to `cloudfront.amazonaws.com`.
- **No origin failover on a critical workload** — HIGH: single origin is a single point of failure. Create an origin group with primary + secondary origins and failover status codes.
- **Never-rotating signed-URL/cookie signing keys** — MEDIUM: long-lived compromised keys expose all private content. Rotate by adding a new key to the trusted key group → migrate signing → remove old key.

---

## Integration Patterns

For full configuration, troubleshooting, and the Service Equivalence Map, see [Integration Patterns](./blueprints/integration-patterns.md).

**Key integrations**:

- **CloudFront + Amazon S3 (OAC)** — Private bucket (Block Public Access on); OAC with `SigningBehavior: always`; bucket policy grants `s3:GetObject` to `cloudfront.amazonaws.com` with `AWS:SourceArn` condition. SSE-KMS: add KMS key-policy grant to the distribution.
- **CloudFront + Amazon API Gateway / ALB** — Custom HTTP origin; free DTO from AWS origins to CloudFront; restrict origin with custom secret header + AWS WAF; enforce HTTPS on the origin protocol.
- **CloudFront + Lambda@Edge / CloudFront Functions** — CloudFront Functions at viewer request/response for sub-ms logic; Lambda@Edge at viewer/origin request/response for network calls, AWS SDK, or body inspection.
- **CloudFront + AWS WAF v2 + Shield Advanced** — WebACL (`CLOUDFRONT` scope, `us-east-1`) with managed rule groups; Shield Advanced adds DDoS response team access, cost protection, and enhanced metrics.
- **CloudFront + AWS Certificate Manager (ACM)** — Request or import certificate in **us-east-1**; attach to `ViewerCertificate`; ACM auto-renews managed certificates before expiry.
- **CloudFront + Amazon Route 53** — Alias record pointing to CloudFront distribution domain; Route 53 latency-based routing for multi-distribution architectures; health checks for DNS-level failover.

---

## Verification Loop

Run after any CloudFront distribution creation or configuration change.

### 1. Verify HTTPS enforcement

```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.DefaultCacheBehavior.ViewerProtocolPolicy"
# Expected: "redirect-to-https" or "https-only"
```

### 2. Verify TLS security policy

```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.ViewerCertificate.MinimumProtocolVersion"
# Expected: "TLSv1.2_2021" or newer
```

### 3. Verify AWS WAF WebACL attached

```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.WebACLId"
# Expected: non-empty WebACL ARN (arn:aws:wafv2:us-east-1:ACCOUNT:global/webacl/NAME/ID)
```

### 4. Verify OAC on S3 origins and bucket privacy

```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.Origins.Items[].OriginAccessControlId"
# Expected: non-empty OAC ID for each S3 origin

aws s3api get-public-access-block --bucket "$BUCKET_NAME"
# Expected: BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy,
#           RestrictPublicBuckets all = true
```

### 5. Verify cache policy (not legacy ForwardedValues)

```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.DefaultCacheBehavior.CachePolicyId"
# Expected: a non-null cache policy ID
```

### 6. Verify origin groups for critical distributions

```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.OriginGroups.Quantity"
# Expected: >= 1 for any critical workload
```

**Troubleshooting**:

- `403` from S3 origin → Confirm OAC is attached to the origin; verify bucket policy grants `s3:GetObject` to `cloudfront.amazonaws.com` with the correct `AWS:SourceArn` condition.
- `403` from WAF → Check WebACL rule order and managed-rule false-positive rate; confirm `/.well-known/pki-validation/` is not blocked.
- Low cache-hit ratio → Inspect cache key for unnecessary headers/cookies/query strings; consider enabling Origin Shield.
- Custom error page not serving → Confirm `ErrorCachingMinTTL` is set on the error code; verify the custom error page object exists at the configured path on the origin.

---

## Quick Reference

**Essential CLI commands**:

```bash
# List all distributions with status
aws cloudfront list-distributions \
  --query "DistributionList.Items[].{Id:Id,Domain:DomainName,Status:Status}"

# Invalidate cache (1,000 paths/month free; billed beyond)
aws cloudfront create-invalidation \
  --distribution-id "$DIST_ID" --paths "/*"

# List custom cache policies
aws cloudfront list-cache-policies --type custom

# List real-time log configurations
aws cloudfront list-realtime-log-configs

# Check OAC assignments across all origins
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.Origins.Items[].{Origin:DomainName,OAC:OriginAccessControlId}"
```

**CloudFront service limits** (source: [CloudFront quotas](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-limits.html), accessed 2026-07-31):

| Resource | Default Limit | Notes |
|---|---|---|
| Distributions per account | 200 | Increasable via AWS Support |
| Origins per distribution | 25 | |
| Cache behaviors per distribution | 25 | |
| Field-level encryption fields per request | 10 | |
| Field-level encryption configs per account | 10 | |
| Free cache invalidations | 1,000 paths/month | Billed beyond this threshold |
| Lambda@Edge memory | 128–3,008 MB | Max 30s timeout (origin request/response) |
| CloudFront Functions package size | 10 KB | Sub-millisecond; viewer request/response only |

---

## External Resources

### Official Documentation (continuously updated)

- [Amazon CloudFront Developer Guide](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html) — primary reference (accessed 2026-07-31)
- [Require HTTPS between viewers and CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https-viewers-to-cloudfront.html) — accessed 2026-07-31
- [Supported protocols and ciphers (TLS security policies)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html) — accessed 2026-07-31
- [Use AWS WAF with a CloudFront distribution](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-aws-waf.html) — accessed 2026-07-31
- [Restrict access to an Amazon S3 origin (OAC vs OAI)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html) — accessed 2026-07-31
- [Understand the cache key](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-the-cache-key.html) — accessed 2026-07-31
- [Origin failover with origin groups](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html) — accessed 2026-07-31
- [CloudFront Functions vs Lambda@Edge](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html) — accessed 2026-07-31
- [Serve private content with signed URLs and signed cookies](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PrivateContent.html) — accessed 2026-07-31
- [Use field-level encryption](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/field-level-encryption.html) — accessed 2026-07-31
- [Amazon CloudFront pricing (price classes)](https://aws.amazon.com/cloudfront/pricing/) — accessed 2026-07-31
- [Continuous deployment with staging distributions](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment.html) — accessed 2026-07-31
- [Origin Shield](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html) — accessed 2026-07-31
- [Geo-restriction](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html) — accessed 2026-07-31

### Framework Guidance

- [AWS Well-Architected Framework — Pillars](https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html) — accessed 2026-07-31

### Research Source

- [Research file](../../../docs/research_aws_cloudfront_2025.md) — source-dated 2026-07-31
