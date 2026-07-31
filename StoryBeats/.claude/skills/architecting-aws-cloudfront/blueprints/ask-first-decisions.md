# Ask-First Decisions — Amazon CloudFront

> 6 architectural decisions that require context before committing to an approach.
> Confirm each with the client or architect before design is finalized.
> All sources accessed 2026-07-31.

---

## Decision 1: Origin Type Selection

**When to ask:** Whenever the workload type (static, dynamic, serverless, on-premises) is not specified, or when the team defaults to a single origin type for all content.

### Decision Table

| Origin Type | Best For | Access Control | Origin-to-CloudFront DTO | Notes |
|---|---|---|---|---|
| **Amazon S3 (REST endpoint)** | Static assets, SPA bundles, media, logs | **OAC** (recommended, sigv4) | **Free** | Must use regular bucket, not website endpoint; Block Public Access on |
| **Amazon S3 website endpoint** | Legacy static hosting with server-side redirects | Treated as **custom origin** (no OAC/OAI) | **Free** | OAC/OAI cannot be used; bucket remains semi-public for CloudFront serving |
| **Application Load Balancer (ALB/ELB)** | Dynamic web apps, EC2/ECS/EKS backends | Custom secret header + AWS WAF; VPC Origins for private ALBs | **Free** | Use HTTPS on origin protocol; restrict direct access with a secret header + WAF |
| **Amazon API Gateway** | REST/HTTP APIs, serverless backends | Custom origin + AWS WAF | **Free** | HTTP API or REST API; use HTTPS; add WAF for full L7 protection |
| **Custom HTTP origin (EC2, on-premises)** | Existing web servers, non-AWS origins | Custom secret header + AWS WAF; Origin Shield for capacity-limited on-prem | Billed (egress from on-prem) | Origin protocol policy governs TLS negotiation; Origin Shield reduces on-prem connection fan-out |

### Ask the Architect

1. Is the content static (cacheable) or dynamic (per-request)?
2. Does the origin need server-side redirects or custom error pages at the origin level?
3. Is the origin inside a VPC (private ALB) or publicly addressable?
4. Is data transfer cost from origin a concern? (AWS origins → CloudFront is free)
5. Does the origin need to receive the original viewer IP (use `X-Forwarded-For` header policy)?

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (access 2026-07-31)

---

## Decision 2: OAC vs OAI for Amazon S3 Origins

**When to ask:** Whenever an S3 origin is added to a distribution, or when reviewing an existing distribution that still uses OAI.

### Decision Table

| Criterion | OAC (Current, Recommended) | OAI (Legacy) |
|---|---|---|
| **New distributions** | ✅ Use for all new S3 origins | ❌ Do not use |
| **SSE-KMS encrypted objects** | ✅ Supported | ❌ Not supported |
| **Dynamic requests (PUT/DELETE)** | ✅ Supported | ❌ Not supported |
| **Opt-in AWS Regions (post-Jan 2023)** | ✅ All Regions supported | ❌ Broken in new Regions |
| **Existing OAI distributions** | Plan migration | Keep until migrated |
| **Bucket policy principal** | `cloudfront.amazonaws.com` with `AWS:SourceArn` condition | `arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity OAIID` |

### Migration Path (OAI → OAC)

1. Create a new OAC (sigv4, `SigningBehavior: always`).
2. Add the OAC principal to the bucket policy as an additional `Allow` statement (dual-principal period).
3. Update the CloudFront distribution to reference the new OAC and remove OAI.
4. Verify requests succeed with OAC.
5. Remove the OAI principal from the bucket policy.
6. Delete the OAI resource.

### Ask the Architect

1. Are any S3 objects encrypted with SSE-KMS? (OAC required — OAI cannot decrypt)
2. Does the application use PUT/DELETE to S3 through CloudFront? (OAC required)
3. Is the S3 bucket in a Region launched after January 2023? (OAC required)
4. Is migration from OAI acceptable now, or is it deferred to a later sprint?

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (access 2026-07-31)

---

## Decision 3: Logging Strategy

**When to ask:** When defining observability requirements, cost constraints, or security response SLAs for a distribution.

### Decision Table

| Option | Latency | Cost | Destination Options | Use When |
|---|---|---|---|---|
| **Standard logs (v2)** | Best-effort, minutes+ | **Free** (plus destination storage/ingestion) | Amazon S3, Amazon CloudWatch Logs, Amazon Kinesis Data Firehose | Audit, troubleshooting, offline analytics; default choice |
| **Real-time logs** | Seconds (streaming) | **Additional per-request charge** | **Amazon Kinesis Data Streams** only | Live monitoring, fraud detection, attack response, sampling (configurable %) |
| **CloudFront CloudWatch metrics** | Near real-time (aggregated) | Standard CloudWatch metrics cost; additional metrics available | Amazon CloudWatch | Dashboards and alarms on error rates and request volumes — not per-request detail |

### Cost Profile

- Standard logs: No CloudFront charge; you pay S3 storage, CloudWatch Logs ingestion, or Firehose
  delivery charges on the destination.
- Real-time logs: Charged per record delivered to Kinesis Data Streams, plus Kinesis stream charges.
  Use sampling rate (1–100%) to control cost.
- CloudWatch additional metrics: flat monthly charge per distribution metric group.

### Ask the Architect

1. What is the required log latency for security response? (>5 minutes is fine → standard; <1 minute → real-time)
2. Is there a regulatory requirement to retain logs for a specific period? (Drives S3 lifecycle policy)
3. Is per-request log completeness required, or are aggregate metrics sufficient?
4. What percentage of requests need real-time log sampling? (Cost lever for real-time logs)
5. Is the destination system (SIEM, data lake, monitoring platform) already connected to Kinesis or S3?

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html (access 2026-07-31)

---

## Decision 4: Single Distribution vs Multi-Distribution Strategy

**When to ask:** When the workload serves multiple tenants, geographic markets, or properties with diverging security or policy requirements.

### Decision Table

| Strategy | Best For | Key Constraint | Management Overhead |
|---|---|---|---|
| **Single distribution, multiple cache behaviors** | One property, segmented content paths | Geo-restriction, WAF, and TLS certificate apply to the entire distribution | Low |
| **Multiple distributions** | Different WAF policies, geo rules, certs, or lifecycle per property or market | Each distribution has its own quota, cost, and TTL propagation | High |
| **Multi-tenant distribution (CloudFront SaaS Manager)** | SaaS providers with many similar sites (fan-out) | Purpose-built for shared-config tenancy; has its own quotas | Medium (automated) |

### When to Split into Multiple Distributions

- Different geo-restriction rules per property (geo-restriction is distribution-wide).
- Different WAF WebACL policies per property.
- Different TLS certificates (different domains) requiring separate `ViewerCertificate` configs.
- Different lifecycle, maintenance windows, or continuous-deployment policies per property.
- Regulatory or compliance isolation requirements between tenants.

### Ask the Architect

1. Do different properties or tenants require different geo-restriction rules? (If yes → split distributions)
2. Do different properties need different WAF policies? (If yes → split distributions)
3. Is this a SaaS platform with many similar tenant sites? (CloudFront SaaS Manager may fit)
4. What is the expected number of distributions? (Soft limit: 200 per account; quota increase available)
5. Are maintenance windows and deployment cadences the same across all properties?

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html (access 2026-07-31)

---

## Decision 5: IPv6 Enabled vs Disabled

**When to ask:** When the organization has downstream systems that perform IP-based filtering, geo lookups, or rate limiting based on the `c-ip` (client IP) field in CloudFront logs or headers.

### Decision Table

| Setting | Behavior | Use When |
|---|---|---|
| **IPv6 enabled** (default-friendly) | Dual-stack: CloudFront serves both IPv4 and IPv6 viewers; viewer IP may be IPv6 | No downstream IPv4-only dependencies |
| **IPv6 disabled** | CloudFront accepts only IPv4 viewer connections | Downstream system cannot parse IPv6 addresses (allow/deny lists, geo-IP lookups, legacy WAF rules) |

### Implications of Enabling IPv6

- `c-ip` field in logs may contain IPv6 addresses.
- Any `X-Forwarded-For` header parsing in origin, Lambda@Edge, or CloudFront Functions code must
  handle both IPv4 and IPv6 address formats.
- AWS WAF IP sets can contain both IPv4 and IPv6 CIDRs — confirm WAF rules are dual-stack.

### Ask the Architect

1. Does any downstream system (origin, Lambda, WAF, SIEM, allow/deny list) parse `c-ip` as IPv4-only?
2. Are any existing WAF IP sets IPv4-only and not yet updated to include IPv6 ranges?
3. Is IPv6 support a stated requirement from the business or end-users?

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html (distribution settings reference) (access 2026-07-31)

---

## Decision 6: Continuous Deployment with Staging Distributions

**When to ask:** Before any high-risk configuration change (cache policy, WAF rules, TLS version, origin endpoint) on a business-critical distribution in production.

### Decision Table

| Approach | Risk | Testing Method | Rollback |
|---|---|---|---|
| **Direct edit of production distribution** | High (change applies to 100% of traffic immediately) | Synthetic tests only before change | Revert config manually |
| **Continuous deployment with staging distribution** | Low (subset of real traffic to staging; promote when validated) | Real production traffic subset (header or weight-based routing) | Stop routing to staging; delete or update policy |

### How Continuous Deployment Works

1. Create a **staging distribution** (separate from the primary distribution).
2. Create a **continuous-deployment policy** defining traffic routing:
   - **Header-based**: route requests with a specific header (e.g., `x-cloudfront-staging: true`) to staging.
   - **Weight-based**: route a percentage (e.g., 10%) of all traffic to staging.
3. Associate the policy with the primary distribution.
4. Validate staging distribution behavior using the routing rule.
5. **Promote**: copy the staging distribution config to the primary distribution to apply globally.

### Ask the Architect

1. Is this change to a business-critical distribution where unexpected behavior would cause user impact?
2. Does the team have the process overhead to manage a staging distribution?
3. Is header-based or weight-based traffic split preferred for validation?
4. What is the validation criteria and duration before promoting to production?

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment.html (access 2026-07-31)
