# Never Do Patterns — delivering-cloudfront-cdn

Full anti-patterns A1-A6 with wrong/correct examples. Summary in [../SKILL.md](../SKILL.md).
Source: research_cloud_AWS_CloudFront_CDN_2026.md (research date 2026-08-26; official AWS docs accessed 2026-08-26).

---

## A1 — Publicly reachable origin behind CloudFront [CRITICAL]

**Why**: attackers bypass CloudFront WAF/Shield/geo controls by hitting the origin directly.

- 🚫 WRONG: public S3 bucket with Block Public Access disabled; or an internet-facing ALB in a public subnet used as origin.
- ✅ CORRECT: private S3 with Block Public Access + OAC (`SigningBehavior: always`); ALB/NLB/EC2 in private subnets via VPC origins, with the CloudFront managed prefix list on the origin security group.

**Detection**: `aws s3api get-public-access-block`; direct curl to the origin public endpoint must fail; ALB scheme is `internal` or fronted by a VPC origin.
**Impact**: data breach, control bypass.

Sources: [S3 origin access](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html); [VPC origins](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html) (accessed 2026-08-26)

---

## A2 — Legacy OAI for new S3 origins [MEDIUM]

**Why**: OAI lacks SSE-KMS and dynamic request support, and does not work in Regions launched after January 2023.

- 🚫 WRONG: new distribution with `OriginAccessIdentity` pointing at an SSE-KMS bucket.
- ✅ CORRECT: `AWS::CloudFront::OriginAccessControl` with `SigningBehavior: always`, `SigningProtocol: sigv4`, plus a KMS key-policy grant to `cloudfront.amazonaws.com`.

**Detection**: `aws cloudfront get-distribution-config` shows a non-empty `OriginAccessIdentity`.
**Impact**: broken SSE-KMS delivery, future Region incompatibility.

Source: [S3 origin access](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html) (accessed 2026-08-26)

---

## A3 — Allowing HTTP or weak TLS to viewers [HIGH]

**Why**: cleartext HTTP and deprecated TLS (TLSv1/1.1, SSLv3) allow interception.

- 🚫 WRONG: Viewer Protocol Policy `HTTP and HTTPS` with security policy `TLSv1` or `SSLv3`.
- ✅ CORRECT: `Redirect HTTP to HTTPS` or `HTTPS only` with `TLSv1.2_2021` minimum (`TLSv1.3_2025` for quantum-safe key exchange).

**Detection**: `openssl s_client -tls1_1` succeeds (should fail); `MinimumProtocolVersion` is a `TLSv1*`/`SSLv3` value.
**Impact**: data interception, compliance violation.

Source: [Supported viewer protocols and ciphers](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html) (accessed 2026-08-26)

---

## A4 — No AWS WAF web ACL on an internet-facing distribution [HIGH]

**Why**: no L7 filtering (SQLi, XSS, bot, rate limiting) at the edge.

- 🚫 WRONG: public distribution serving an API with no `WebACLId`.
- ✅ CORRECT: WAFv2 web ACL (scope `CLOUDFRONT`, `us-east-1`) with AWS managed rule groups plus a rate-based rule.

**Detection**: `aws wafv2 get-web-acl-for-resource --scope CLOUDFRONT --region us-east-1` returns empty for the distribution ARN. A creation error "InvalidScope" means wrong scope or Region.
**Impact**: application-layer compromise, DDoS amplification.

Source: [AWS WAF + CloudFront](https://docs.aws.amazon.com/waf/latest/developerguide/cloudfront-chapter.html) (accessed 2026-08-26)

---

## A5 — Over-inclusive cache key [MEDIUM]

**Why**: forwarding everything into the cache key fragments the cache, collapses hit ratio and loads the origin.

- 🚫 WRONG: legacy "forward all cookies / all query strings", or a cache policy including every viewer header.
- ✅ CORRECT: cache policy with only response-varying values; origin-only values via an origin request policy; normalize with a CloudFront Function.

**Detection**: persistently low `CacheHitRate`; many `Miss` in `x-edge-detailed-result-type`.
**Impact**: cost overrun, origin overload.

Source: [Control the cache key](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/controlling-the-cache-key.html) (accessed 2026-08-26)

---

## A6 — Single origin with no failover for HA workloads [MEDIUM]

**Why**: one origin is a single point of failure for cache-miss traffic.

- 🚫 WRONG: one origin, no origin group, default 30 s (3 attempts x 10 s) connection behavior on a latency-sensitive streaming workload.
- ✅ CORRECT: origin group (primary + secondary) with failover status codes and tuned connection timeout/attempts.

**Details**:
- SKILL.md failover codes: 500, 502, 503, 504. Research lists the full supported set: 400, 403, 404, 416, 429, 500, 502, 503, 504.
- Failover applies only to GET, HEAD, OPTIONS; OPTIONS must be a cached method to fail over.
- An origin group is not load balancing: all requests go to the primary first.

**Detection**: the cache behavior has no origin group.
**Impact**: outage on origin failure.

Source: [Origin failover](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html) (accessed 2026-08-26)
