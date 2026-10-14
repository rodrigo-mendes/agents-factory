---
name: delivering-cloudfront-cdn
description: "Designs and implements secure, high-performance AWS CloudFront CDN distributions for production workloads. Use when architecting or reviewing a CloudFront distribution covering origin security, TLS policy, WAF integration, cache-key design, edge functions, or high-availability failover."
---

## Function

Specialist in AWS CloudFront CDN architecture for production web and media workloads on AWS CloudFront 2026.

## Version Context

**Technology**: AWS CloudFront CDN
**Target version**: AWS CloudFront 2026
**Research date**: 2026-08-26
**Support status**: Active (Generally Available)
**Currency threshold**: 2027-08-26

**Key additions in this edition**:
- Flat-rate pricing plans (Free / Pro $15 / Business $200 / Premium $1,000/month) bundling CDN + WAF + DDoS + bot management + DNS — launched Nov 2025, expanded Mar 2026
- VPC origins GA (Nov 2024) + WebSocket support (May 2026) — reach private ALBs/NLBs/EC2 with no public IP
- New security policies `TLSv1.2_2025` and `TLSv1.3_2025` with quantum-safe key exchanges (`X25519MLKEM768`, `SecP256r1MLKEM768`)
- IPv6 origins (Sep 2025) — end-to-end IPv6 support
- CloudFront Functions three new capabilities (Nov 2025): edge-location/REC metadata, raw query-string retrieval, advanced origin overrides including SNI

**Deprecated**: Origin Access Identity (OAI) — superseded by Origin Access Control (OAC). Do not use OAI for new distributions.

> **CRITICAL — Agent Warning**
> This skill targets AWS CloudFront 2026. Reject OAI-based S3 access patterns (pre-2022). Do not mix legacy
> "forward all headers/cookies" cache-key patterns with current cache policy architecture.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — Mandatory, decision, and anti-pattern summaries
- **[Always Do Patterns](./blueprints/always-do-patterns.md)** — Full patterns with CLI verification commands
- **[Ask First Decisions](./blueprints/ask-first-decisions.md)** — Decision matrices with tradeoff tables
- **[Never Do Patterns](./blueprints/never-do-patterns.md)** — Anti-patterns with wrong/correct side-by-side
- **[Integration Patterns](#integration-patterns)** — Reference architectures for static and dynamic workloads
- **[Verification Loop](#verification-loop)** — CLI validation commands and expected outputs
- **[Quick Reference](#quick-reference)** — Critical limits and essential commands
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — Test cases for skill validation
- **[External Resources](#external-resources)** — Dated official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

For full patterns with code and CLI verification, see [Always Do Patterns](./blueprints/always-do-patterns.md).

**M1 — Lock S3 origins with Origin Access Control (OAC)**
Create `AWS::CloudFront::OriginAccessControl` with `SigningBehavior: always` and `SigningProtocol: sigv4`. Enable S3 Block Public Access (all four blocks `true`). Grant `cloudfront.amazonaws.com` `s3:GetObject` scoped by `AWS:SourceArn` = distribution ARN. For SSE-KMS buckets, add `kms:Decrypt`/`Encrypt`/`GenerateDataKey*` to the KMS key policy with the same condition. Never use legacy OAI for new distributions.

**M2 — Require HTTPS end-to-end with a modern security policy**
Set Viewer Protocol Policy to `Redirect HTTP to HTTPS` or `HTTPS only` on every cache behavior. Attach an ACM certificate (must be provisioned in `us-east-1` for CloudFront) for custom domains. Set the distribution security policy to `TLSv1.2_2021` minimum; use `TLSv1.3_2025` for quantum-safe key exchange on sensitive workloads. Use SNI (default); avoid dedicated-IP SSL.

**M3 — Attach an AWS WAF web ACL and rely on AWS Shield Standard**
Create a WAFv2 web ACL with `scope: CLOUDFRONT` in `us-east-1`. Add AWS managed rule groups plus a rate-based rule. Associate via `WebACLId` on the distribution. Shield Standard DDoS protection is automatic and free. Evaluate Shield Advanced for business-critical workloads (24/7 SRT + DDoS cost protection).

**M4 — Keep ALB/NLB/EC2 origins private with VPC origins**
Place the load balancer or EC2 instance in private subnets. Create a CloudFront VPC origin. Update the origin resource's security group to allow inbound from the CloudFront managed prefix list or use the service-managed security group `CloudFront-VPCOrigins-Service-SG`. WebSocket traffic supported as of May 1, 2026. No public IP on the origin.

**M5 — Engineer the cache key deliberately with cache policies**
Use AWS managed cache policies (e.g., `CachingOptimized`) for static assets. Include only the values that vary the response in the cache key. Forward origin-only values (e.g., `CloudFront-Viewer-Country`) via an origin request policy — not the cache key. Normalize query strings and headers with a CloudFront Function before caching. Enable automatic compression (Gzip/Brotli) in the cache policy. Monitor `CacheHitRate` in CloudWatch.

**M6 — Serve private content with signed URLs/cookies using trusted key groups**
Upload a public key and reference it in a key group on the distribution. Sign with the corresponding private key in the application. Use canned policy for single-file/expiry-only access; custom policy for wildcard paths, IP restriction, or start-time control. Use signed cookies when serving multiple files without changing URLs. Never use root AWS account keys as the signer.

**M7 — Enable logging and monitoring (standard logs + CloudWatch alarms)**
Enable standard access logs (v2, free) to S3, CloudWatch Logs, or Firehose. Add real-time logs only where sub-second visibility is required (extra cost). Create CloudWatch alarms on: `4xxErrorRate`, `5xxErrorRate`, `OriginLatency`, `CacheHitRate`. Diagnose cache behavior via `x-edge-detailed-result-type` field (`Hit`, `OriginShieldHit`, `Miss`, `Error`).

---

### ⚠️ Ask First

For complete decision matrices with code examples, see [Ask First Decisions](./blueprints/ask-first-decisions.md).

**D1 — CloudFront Functions vs Lambda@Edge**
Ask whether the logic needs the **request body, network calls, third-party libraries, or origin-facing triggers (origin request/response events)**. If yes → Lambda@Edge (Node.js/Python, up to 30 s, all four event triggers). Otherwise → CloudFront Functions (sub-ms, ~1/6 the cost, scales to millions rps, supports KeyValueStore). CloudFront Functions are limited to viewer events only, ES5.1 (runtime 2.0), 2 MB memory, 10 KB code, no network/filesystem access.

**D2 — Pay-as-you-go vs flat-rate pricing plans (2026)**
Ask for expected monthly traffic volume and spike profile. Small/medium sites with unpredictable spikes or wanting bundled WAF/DDoS/bot/DNS → flat-rate plan. High-volume workloads with committed-use discounts → pay-as-you-go. Confirm required features against tier gates: viewer mTLS = Premium plan; bot controls and AI dashboard = Business tier and above. Note: Lambda@Edge invocations are billed at standard rates even on flat-rate plans.

**D3 — Origin Shield: enable or not**
Ask about viewer geographic spread and origin type. Enable Origin Shield (in the Region with lowest latency to the origin) for global viewer bases, just-in-time video packaging, on-prem/bandwidth-limited origins, or multi-CDN setups. Skip for low-cacheability dynamic content or single-region viewer base. Incurs extra per-request charge for requests that traverse Origin Shield as an incremental layer.

**D4 — CloudFront geo-restriction vs AWS WAF geo-match vs third-party geolocation**
Country-level blanket restriction for the whole distribution → CloudFront geographic restrictions. Per-path or combined-rule country restriction → AWS WAF geo-match rule (requires WAF). Sub-country granularity (city/postal/lat-long) or per-file control → third-party geolocation service + signed URLs. Both CloudFront and WAF geo-match are country-level only (~99.8% IP accuracy).

---

### 🚫 Never Do

For full anti-patterns with wrong/correct code examples, see [Never Do Patterns](./blueprints/never-do-patterns.md).

| Anti-pattern | Risk | Correct alternative |
|---|---|---|
| **A1 — Publicly reachable origin behind CloudFront** | CRITICAL — attackers bypass WAF/Shield/geo by hitting the origin directly | S3: Block Public Access + OAC. ALB/NLB/EC2: private subnets + VPC origins + CloudFront managed prefix list |
| **A2 — Using legacy OAI for new S3 origins** | MEDIUM — no SSE-KMS support, broken in post-Jan-2023 Regions | `AWS::CloudFront::OriginAccessControl` with `SigningBehavior: always`, `SigningProtocol: sigv4` |
| **A3 — Allowing HTTP or weak TLS to viewers** | HIGH — data interception, compliance violation | Viewer Protocol Policy `Redirect HTTP to HTTPS` + security policy `TLSv1.2_2021` minimum |
| **A4 — No WAF web ACL on an internet-facing distribution** | HIGH — no L7 filtering; DDoS amplification risk | WAFv2 web ACL (scope `CLOUDFRONT`, us-east-1) with managed rule groups + rate-based rule |
| **A5 — Over-inclusive cache key (forwarding all headers/cookies/query strings)** | MEDIUM — collapses cache hit ratio, hammers origin, cost overrun | Cache policy with only response-varying values; origin-only values via origin request policy; normalize with CloudFront Function |
| **A6 — Single origin with no failover for HA workloads** | MEDIUM — single point of failure on cache-miss traffic | Origin group (primary + secondary) with failover status codes (500, 502, 503, 504); tune connection timeout/attempts |

---

## Integration Patterns

**Pattern 1 — Static site / SPA (S3 + OAC + CloudFront)**
Private S3 bucket (Block Public Access on) with OAC; `CachingOptimized` managed cache policy; CloudFront Function (viewer-request) rewrites SPA deep links to `/index.html`; custom error responses mapping 403/404 → `/index.html` (HTTP 200). Security policy `TLSv1.2_2021`+; WAF web ACL attached.

**Pattern 2 — Dynamic API acceleration (VPC-origin ALB)**
Separate cache behavior at `/api/*` with short/zero TTL and an origin request policy forwarding needed headers; WAF web ACL with rate-based rule; HTTP/2 and HTTP/3 enabled for viewers; ALB in private subnets reached via VPC origin; origin group for failover on 500/502/503/504.

**Pattern 3 — Edge personalization / routing (CloudFront Functions + KeyValueStore)**
CloudFront Function (JavaScript runtime 2.0) reads redirect map or feature flags from CloudFront KeyValueStore on viewer-request event. Use edge-location/REC metadata (Nov 2025 capability) for geo-specific routing without origin round-trips. Update routing config by pushing to KVS — no code redeploy. Only available with runtime 2.0 (not Lambda@Edge).

**Common problems**:
- **ACM certificate in wrong Region** → provision or import the certificate in `us-east-1`; CloudFront cannot use certificates from other Regions.
- **WAF web ACL created in wrong Region or scope** → WAFv2 for CloudFront must have `scope: CLOUDFRONT` and reside in `us-east-1`.
- **`/.well-known/pki-validation/` blocked by WAF/bot rules** → exempt this path so CloudFront managed certificate validation succeeds.
- **KVS not accessible from Lambda@Edge** → CloudFront KeyValueStore is only available to CloudFront Functions (runtime 2.0).

---

## Verification Loop

Run after each distribution configuration change or IaC deployment:

### 1. Origin access (S3)
```bash
# OAC set, OAI empty
aws cloudfront get-distribution-config --id <DIST_ID> \
  --query 'DistributionConfig.Origins.Items[].S3OriginConfig.OriginAccessIdentity'
# Expected: [""] for all origins (empty = OAI not used)

aws s3api get-public-access-block --bucket <BUCKET>
# Expected: all four fields true
```

### 2. TLS / security policy
```bash
aws cloudfront get-distribution-config --id <DIST_ID> \
  --query 'DistributionConfig.ViewerCertificate.MinimumProtocolVersion'
# Expected: "TLSv1.2_2021" or newer

openssl s_client -connect <domain>:443 -tls1_1 2>&1 | grep "handshake"
# Expected: handshake failure (TLS 1.1 rejected)
```

### 3. WAF attachment
```bash
aws wafv2 get-web-acl-for-resource \
  --resource-arn arn:aws:cloudfront::<ACCOUNT>:distribution/<DIST_ID> \
  --scope CLOUDFRONT --region us-east-1
# Expected: WebACL object returned (not empty)
```

### 4. VPC origin (ALB not public)
```bash
curl --max-time 5 http://<ALB-DNS>
# Expected: connection timeout (origin not reachable directly)
curl --max-time 5 https://<DISTRIBUTION-DOMAIN>/health
# Expected: 200 OK
```

### 5. Cache hit ratio
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront --metric-name CacheHitRate \
  --dimensions Name=DistributionId,Value=<DIST_ID> \
  --start-time $(date -u -d "1 hour ago" +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 --statistics Average
# Expected: > 70% for static assets (tune per workload)
```

**Troubleshooting**:
- Low `CacheHitRate` → check cache policy includes only response-varying values; inspect `x-edge-detailed-result-type` in logs
- 403 on private S3 content → verify OAC `SigningBehavior: always`; confirm `s3:GetObject` grant with `AWS:SourceArn` condition
- WAFv2 creation error "InvalidScope" → confirm scope is `CLOUDFRONT` and Region is `us-east-1`

---

## Quick Reference

**Essential AWS CLI commands**:
```bash
# List distributions
aws cloudfront list-distributions --query 'DistributionList.Items[].{Id:Id,Domain:DomainName}'

# Invalidate cache path
aws cloudfront create-invalidation --distribution-id <DIST_ID> --paths "/*"

# Check distribution status
aws cloudfront get-distribution --id <DIST_ID> --query 'Distribution.Status'
# Expected: "Deployed"
```

**Critical limits and constraints**:

| Resource | Limit | Notes |
|---|---|---|
| ACM certificate Region | `us-east-1` only | CloudFront cannot use certs from other Regions |
| WAFv2 scope for CloudFront | `CLOUDFRONT`, `us-east-1` | Regional WAF (scope `REGIONAL`) will not attach |
| CloudFront Functions code size | 10 KB | Use KVS to externalize data; not Lambda@Edge |
| CloudFront Functions memory | 2 MB | Sub-ms duration; no network/filesystem access |
| Lambda@Edge rps | 10,000 rps / Region | CloudFront Functions scales to millions rps |
| Origin failover methods | GET, HEAD, OPTIONS only | POST/PUT/DELETE do not trigger failover |
| KVS availability | Functions runtime 2.0 only | Not available to Lambda@Edge |
| Flat-rate viewer mTLS | Premium plan only | Confirm tier before design commitment |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/delivering-cloudfront-cdn/
├── SKILL.md                              <- This file (summary + guardrails)
└── blueprints/
    ├── always-do-patterns.md             <- M1-M7 full patterns with CLI verification
    ├── ask-first-decisions.md            <- D1-D4 decision matrices with tradeoff tables
    ├── never-do-patterns.md              <- A1-A6 wrong/correct side-by-side examples
    └── evaluation-scenarios.md           <- Test cases for skill-evaluator
```

---

## External Resources

### Official Documentation (all accessed 2026-08-26)
- [CloudFront Developer Guide](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/) — Primary reference
- [Restrict access to S3 origin (OAC/OAI)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- [Restrict access with VPC origins](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html)
- [Control the cache key with a policy](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/controlling-the-cache-key.html)
- [CloudFront Functions vs Lambda@Edge (choosing)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html)
- [Supported viewer protocols and ciphers (security policies)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html)
- [Origin failover](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html)
- [Origin Shield](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html)
- [Geographic restrictions](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html)
- [Signed URLs](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-signed-urls.html)

### What's New / Blog (2025-2026)
- [VPC origins announcement (Nov 2024)](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-cloudfront-vpc-origins)
- [3 new CloudFront Functions capabilities (Nov 2025)](https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-cloudfront-3-functions-capabilities)
- [IPv6 origins (Sep 2025)](https://aws.amazon.com/about-aws/whats-new/2025/09/amazon-cloudfront-ipv6-origins)
- [Flat-rate pricing plans: new features (Networking blog, Mar 2026)](https://aws.amazon.com/blogs/networking-and-content-delivery/amazon-cloudfront-flat-rate-pricing-plans-new-features-and-expanded-capabilities/) — ⚠️ dated 2026-03; verify current tier gates before design commitment

### Security
- [AWS WAF + CloudFront](https://docs.aws.amazon.com/waf/latest/developerguide/cloudfront-chapter.html)
