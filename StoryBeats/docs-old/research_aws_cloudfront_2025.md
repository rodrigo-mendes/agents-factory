---
cloud_provider: AWS
service: CloudFront
edition: AWS CloudFront 2025
researched: 2026-07-31
audience: Cloud Architects and Tech Leads
---

# AWS CloudFront (2025) — Architecture Best-Practices Knowledge Base

> **Version Absolutism.** This document targets **Amazon CloudFront, 2025 current edition**, as
> documented in the *Amazon CloudFront Developer Guide* (`/latest/`), which is continuously
> maintained against the current stable service. Every claim below traces to an official AWS URL
> with an access date of **2026-07-31**. Where the docs did not confirm a claim, it is marked
> **`[unverified]`** rather than guessed.
>
> **Naming discipline.** This KB uses exact AWS service names only: **Amazon CloudFront**,
> **AWS WAF** (WebACL, `CLOUDFRONT` scope), **AWS Certificate Manager (ACM)**, **Amazon S3**,
> **AWS Lambda@Edge**, **CloudFront Functions**, **Amazon Kinesis Data Streams**,
> **Amazon Kinesis Data Firehose**, **Amazon CloudWatch Logs**, **AWS KMS**,
> **CloudFront Origin Access Control (OAC)**, **CloudFront Origin Access Identity (OAI, legacy)**.

---

## Section 1 — Framework Pillars (AWS Well-Architected alignment for CloudFront)

Amazon CloudFront is a content delivery network (CDN) that serves static and dynamic content from a
global network of edge locations, with **regional edge caches** as a mid-tier layer between edge
locations and origins. A viewer request is routed to the lowest-latency edge location over the AWS
backbone; on a cache miss it flows edge location → regional edge cache → (optional Origin Shield) →
origin. (Source: *What is Amazon CloudFront?* — access 2026-07-31.)

The six AWS Well-Architected pillars map to CloudFront capabilities as follows:

| WAF Pillar | CloudFront capability / control | Primary levers |
|---|---|---|
| **Security** | HTTPS enforcement, TLS security policy, AWS WAF at the edge, OAC for S3, signed URLs/cookies, field-level encryption, geo-restriction | `ViewerProtocolPolicy`, security policy, WebACL (`CLOUDFRONT` scope), OAC, trusted key groups |
| **Reliability** | Origin failover (origin groups), Origin Shield high availability (≥3 AZs), continuous deployment (staging distributions), custom error pages | Origin groups, `OriginShield`, staging distribution + continuous-deployment policy |
| **Performance Efficiency** | Global edge + regional edge caches, cache policies / TTL tuning, Origin Shield cache-hit improvement, HTTP/2 & HTTP/3, CloudFront Functions at the edge | Cache key + cache policy, Origin Shield, edge functions |
| **Cost Optimization** | Price classes, free origin DTO from AWS origins, cache-hit-ratio optimization, free standard logs | `PriceClass_All/200/100`, cache policy tuning, standard logs (free) |
| **Operational Excellence** | Standard logs, real-time logs, CloudWatch metrics, continuous deployment, IaC (CloudFormation) | Standard logging v2, real-time logs, `AWS::CloudFront::Distribution` |
| **Sustainability** | Higher cache-hit ratio and Origin Shield reduce redundant origin fetches and data transfer | Cache policy tuning, Origin Shield consolidation |

Sources: *What is Amazon CloudFront?*; *Use Amazon CloudFront Origin Shield*; *Optimize high
availability with CloudFront origin failover*; *AWS Well-Architected Framework* — all access 2026-07-31.

---

## Section 2 — Mandatory Patterns (Always Do)

### Pattern: Enforce HTTPS for viewer connections
**Why:** Protects data in transit and prevents downgrade/eavesdropping (Security pillar). CloudFront
lets you require HTTPS per cache behavior via **Viewer Protocol Policy**.
**AWS Service:** Amazon CloudFront (cache behavior), AWS Certificate Manager (ACM) for custom domains.
**Architecture Decision:**
  Set `ViewerProtocolPolicy` to `redirect-to-https` (301/307 redirect of HTTP to HTTPS) or
  `https-only` (HTTP → 403 Forbidden). Never use `allow-all` in production. For custom domains use an
  ACM certificate (in **us-east-1** for CloudFront) or import into ACM.
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.DefaultCacheBehavior.ViewerProtocolPolicy"`
  Expected: `"redirect-to-https"` or `"https-only"`.
**Trade-offs:** With `redirect-to-https`, an HTTP request that is redirected is billed as two
requests. Negligible complexity; strong security gain.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https-viewers-to-cloudfront.html (access 2026-07-31)

### Pattern: Set a modern minimum TLS security policy
**Why:** The **security policy** sets the minimum SSL/TLS protocol and cipher suites CloudFront will
negotiate. Legacy policies permit TLS 1.0/1.1, which are non-compliant with modern baselines.
**AWS Service:** Amazon CloudFront (viewer certificate `MinimumProtocolVersion`).
**Architecture Decision:**
  Use `TLSv1.2_2021` or newer (`TLSv1.2_2025`, `TLSv1.3_2025`) as the minimum protocol version.
  CloudFront supports TLS 1.3 and quantum-safe key exchanges (`X25519MLKEM768`, `SecP256r1MLKEM768`)
  on TLS 1.3. Note: the strongest policies require **SNI** (custom SSL, not dedicated IP legacy).
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.ViewerCertificate.MinimumProtocolVersion"`
  Expected: `"TLSv1.2_2021"` (or newer).
**Trade-offs:** Excludes very old clients that only support TLS 1.0/1.1. Acceptable for nearly all
production workloads.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html (access 2026-07-31)

### Pattern: Attach AWS WAF (WebACL, CLOUDFRONT scope) to public distributions
**Why:** Filters malicious traffic at the edge before it reaches the origin, mitigating OWASP Top 10
and volumetric attacks (Security pillar), and reducing origin load and cost.
**AWS Service:** AWS WAF (WebACL), Amazon CloudFront.
**Architecture Decision:**
  Create a WebACL with **scope `CLOUDFRONT`** (global), attach managed rule groups (e.g., Core rule
  set, Known Bad Inputs) plus custom rules, and associate the WebACL to the distribution. Ensure WAF
  rules do **not** block `/.well-known/pki-validation/` (needed for CloudFront managed cert validation).
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.WebACLId"`
  Expected: a non-empty WebACL ARN.
**Trade-offs:** AWS WAF request/WCU charges; managed rules require tuning to avoid false positives.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-aws-waf.html ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html (access 2026-07-31)

### Pattern: Enable access logging (standard logs) to Amazon S3 with lifecycle policies
**Why:** Provides per-request records for troubleshooting, security analysis, and audit
(Operational Excellence). **Standard logs are provided free of charge.**
**AWS Service:** Amazon CloudFront standard logging (v2), Amazon S3 (with lifecycle rules).
**Architecture Decision:**
  Enable **standard logging (v2)** — it supports delivery to **Amazon S3**, **Amazon CloudWatch
  Logs**, and **Amazon Kinesis Data Firehose** (legacy standard logging supports S3 only). Apply an
  S3 **lifecycle policy** to transition to infrequent-access/Glacier and expire per retention policy.
  Note: CloudFront delivers logs on a best-effort basis (not a billing-grade count).
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.Logging"`
  Expected: `Enabled: true` with a target bucket (legacy) or verify a delivery via
  `aws cloudfront list-realtime-log-configs` / logging v2 config.
**Trade-offs:** Standard logs are free; S3 storage cost applies (mitigated by lifecycle rules).
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html (access 2026-07-31)

### Pattern: Define an explicit cache policy and TTL strategy
**Why:** The **cache key** and **cache policy** control hit ratio, origin load, and latency
(Performance + Cost). By default an object stays cached 24 hours; min TTL is 0, and there is no
maximum expiration time. Including too many values (e.g., `User-Agent`, session cookies) in the
cache key causes duplicate objects and low hit ratio.
**AWS Service:** Amazon CloudFront cache policy (Min/Default/Max TTL) and origin request policy.
**Architecture Decision:**
  Use a **cache policy** to set `MinTTL`, `DefaultTTL`, `MaxTTL` and to include only the minimum
  necessary headers/cookies/query strings in the cache key. Put values the origin needs for
  analytics but that do not change the response into an **origin request policy** (forwarded but not
  in the cache key).
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.DefaultCacheBehavior.CachePolicyId"`
  Expected: a cache policy ID (not legacy `ForwardedValues`).
**Trade-offs:** Broader cache keys reduce hit ratio; narrow keys risk serving stale/wrong variants.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-the-cache-key.html ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html (access 2026-07-31)

### Pattern: Configure custom error pages with error caching TTL
**Why:** Prevents leaking origin error internals and reduces origin load during faults (Reliability +
Security). CloudFront can return a custom page and cache the error response for a configurable time.
**AWS Service:** Amazon CloudFront custom error responses.
**Architecture Decision:**
  Map specific HTTP status codes (e.g., 403, 404, 500, 502, 503, 504) to custom response pages and
  set an appropriate **error caching minimum TTL**. Combine with origin failover so primary/secondary
  origin errors both surface a controlled page.
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.CustomErrorResponses"`
  Expected: entries mapping error codes to response pages and `ErrorCachingMinTTL`.
**Trade-offs:** Overly long error TTL can prolong a stale error after the origin recovers.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html (custom error pages with origin failover); https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html (error caching default 10s) (access 2026-07-31)

### Pattern: Configure origin failover with origin groups for critical workloads
**Why:** High availability — if the primary origin fails or returns configured failover status codes,
CloudFront automatically routes to a secondary origin (Reliability pillar).
**AWS Service:** Amazon CloudFront origin groups.
**Architecture Decision:**
  Create an **origin group** with a primary and secondary origin; select failover status codes from
  `400, 403, 404, 416, 429, 500, 502, 503, 504`; reference the origin group in the cache behavior.
  Failover occurs only for `GET`, `HEAD`, `OPTIONS` viewer methods (and `OPTIONS` must be in cached
  methods). Tune origin connection timeout (1–10s), attempts (1–3), and response timeout (1–120s).
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.OriginGroups"`
  Expected: an origin group with two members and `StatusCodes`.
**Trade-offs:** Failover adds a second origin fetch on failure (latency); Lambda@Edge origin triggers
can fire twice (primary + secondary).
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html (access 2026-07-31)

### Pattern: Enable Origin Shield for high-cache-hit / multi-region / multi-CDN origins
**Why:** Adds a caching layer in front of the origin so all regional edge caches consolidate through
one point, improving cache-hit ratio and reducing origin load (Performance + Reliability + Cost).
**AWS Service:** Amazon CloudFront Origin Shield (property of the origin).
**Architecture Decision:**
  Enable Origin Shield per origin in the AWS Region with lowest latency to the origin (Origin Shield
  is available only in Regions that host a regional edge cache — e.g., `us-east-1`, `us-west-2`,
  `eu-west-1`, etc.). Best for globally distributed viewers, just-in-time packaging, capacity-limited
  on-prem origins, and multi-CDN. It is compatible with origin groups (each origin uses its own shield).
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.Origins.Items[].OriginShield"`
  Expected: `{ "Enabled": true, "OriginShieldRegion": "<region>" }`.
**Trade-offs:** Incremental per-request charges; **not** a good fit for low-cacheability/dynamic
content, and not supported for gRPC (requests bypass the shield).
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html (access 2026-07-31)

### Pattern: Apply geo-restriction where distribution rights are geographic
**Why:** Enforces content licensing / regulatory boundaries at the edge (Security + Compliance).
**AWS Service:** Amazon CloudFront geographic restrictions (country-level).
**Architecture Decision:**
  Use the built-in **allowlist** or **blocklist** of countries. It applies to the entire distribution
  at country granularity; blocked viewers receive `403 (Forbidden)`. For finer granularity (city,
  postal, lat/long) or per-path rules, use **AWS WAF geo match** or a third-party geolocation service
  with signed URLs. Do not block `/.well-known/pki-validation/` (certificate validation).
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.Restrictions.GeoRestriction"`
  Expected: `RestrictionType` of `whitelist`/`blacklist` with country codes.
**Trade-offs:** Country-level only; IP-to-country accuracy is ~99.8% and applies distribution-wide.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html (access 2026-07-31)

### Pattern: Use OAC to lock down Amazon S3 origins (never leave the bucket public)
**Why:** Ensures viewers can only reach S3 content through CloudFront, not directly (Security pillar).
**AWS Service:** CloudFront Origin Access Control (OAC), Amazon S3 bucket policy, AWS KMS (if SSE-KMS).
**Architecture Decision:**
  Create an **OAC** with `SigningBehavior: always` (`sigv4`), set S3 **Object Ownership** to
  **Bucket owner enforced**, and grant only the `cloudfront.amazonaws.com` service principal with an
  `AWS:SourceArn` condition scoped to the distribution ARN. For SSE-KMS objects, add a KMS key-policy
  statement allowing the distribution to `kms:Decrypt`/`GenerateDataKey*`.
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.Origins.Items[].OriginAccessControlId"`
  plus confirm the S3 bucket policy restricts `Principal.Service = cloudfront.amazonaws.com` with
  the `AWS:SourceArn` condition.
**Trade-offs:** Requires bucket-policy + (optional) KMS-policy management. Regular S3 bucket required
(not an S3 website endpoint — those need a custom origin and cannot use OAC/OAI).
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (access 2026-07-31)

### Pattern: Serve private content with signed URLs / signed cookies using trusted key groups
**Why:** Restricts access to paid/sensitive content and adds expiry control (Security pillar).
**AWS Service:** Amazon CloudFront signed URLs / signed cookies with **trusted key groups**.
**Architecture Decision:**
  Use **trusted key groups** (AWS recommends these over legacy trusted signers based on AWS-account
  root CloudFront key pairs). Choose **signed URLs** for individual files / clients that don't support
  cookies; **signed cookies** for multiple files or to keep existing URLs unchanged. Pair with OAC so
  the origin cannot be reached directly.
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.DefaultCacheBehavior.TrustedKeyGroups"`
  Expected: `Enabled: true` with one or more key group IDs.
**Trade-offs:** Application must generate/sign tokens; requires disciplined **key rotation** of the
public keys in the key group.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PrivateContent.html (access 2026-07-31)

### Pattern: Use field-level encryption for specific sensitive POST fields
**Why:** Encrypts designated fields at the edge (close to the user) so plaintext never traverses the
application stack; only components with the private key can decrypt (Security + Compliance).
**AWS Service:** Amazon CloudFront field-level encryption (asymmetric RSA-2048, AWS Encryption SDK).
**Architecture Decision:**
  Create a public key + field-level-encryption profile + configuration and link it to a cache
  behavior. Encrypt **up to 10 fields** per request in `application/x-www-form-urlencoded` POST bodies
  (e.g., credit-card or PII fields). Requires HTTPS-only viewer policy, POST/PUT allowed methods,
  origin protocol `match-viewer`/`https-only`, and an origin that supports chunked encoding.
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.DefaultCacheBehavior.FieldLevelEncryptionId"`
  Expected: a non-empty FLE configuration ID.
**Trade-offs:** Origin must integrate the AWS Encryption SDK to decrypt; max 10 fields and 10
configurations per account; adds development overhead.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/field-level-encryption.html (access 2026-07-31)

### Pattern: Select the correct price class for the required global coverage
**Why:** Balances global performance against cost (Cost Optimization). Data transfer from AWS origins
(Amazon S3, Elastic Load Balancing, Amazon API Gateway) to CloudFront is free; you pay for edge DTO
and requests, which vary by geographic Region.
**AWS Service:** Amazon CloudFront price class (`PriceClass_All` / `PriceClass_200` / `PriceClass_100`).
**Architecture Decision:**
  - `PriceClass_All` — all CloudFront edge locations (best global performance, highest cost).
  - `PriceClass_200` — most Regions **except** the most expensive (excludes some of South America /
    Australia / New Zealand).
  - `PriceClass_100` — lowest-cost Regions only (North America, Europe, and Israel).
  Choose based on where your viewers actually are.
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.PriceClass"`
  Expected: one of `PriceClass_All` / `PriceClass_200` / `PriceClass_100`.
**Trade-offs:** Lower price classes increase latency for viewers in excluded Regions (they are served
from a farther edge). `[Edge-location membership per class — see CloudFront pricing page; the
Developer Guide PriceClass topic now redirects to the pricing page.]`
**Source:** https://aws.amazon.com/cloudfront/pricing/ (PriceClass topic redirects here); https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html (free DTO from AWS origins) (access 2026-07-31)

### Pattern: Prefer CloudFront Functions for lightweight edge logic; Lambda@Edge for heavier logic
**Why:** Right-sizing edge compute controls latency and cost (Performance + Cost). See Section 3 for
the full decision; treat "use the lightest tool that meets the requirement" as mandatory.
**AWS Service:** CloudFront Functions (JavaScript, sub-ms, edge) vs AWS Lambda@Edge (Node.js/Python,
up to 30s, regional edge cache).
**Architecture Decision:**
  Use **CloudFront Functions** for cache-key normalization, header manipulation, URL rewrites/redirects,
  and simple token validation (viewer request/response only). Use **Lambda@Edge** when you need network
  access, filesystem, request body, third-party libraries/AWS SDK, or >2 MB memory / longer runtime.
**Verification:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.DefaultCacheBehavior.FunctionAssociations"`
  and `...LambdaFunctionAssociations`.
**Trade-offs:** CloudFront Functions cannot do network/filesystem/body access; Lambda@Edge costs more
and scales to ~10,000 req/s per Region vs millions/s for CloudFront Functions.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html (access 2026-07-31)

---

## Section 3 — Architectural Decisions (Ask First)

### Decision: Origin type — Amazon S3 vs ALB vs Amazon API Gateway vs custom HTTP origin
**Options / Trade-offs:**
| Origin | Best for | Access-control mechanism | Notes |
|---|---|---|---|
| **Amazon S3 (REST endpoint)** | Static assets, SPA bundles, media | **OAC** (recommended) | Free DTO S3→CloudFront; use regular bucket, not website endpoint |
| **Amazon S3 website endpoint** | Legacy static hosting with redirects | Treated as **custom origin** | Cannot use OAC/OAI |
| **Application Load Balancer (ELB)** | Dynamic web/API behind EC2/ECS/EKS | Custom headers + AWS WAF; VPC origins | Free DTO ELB→CloudFront |
| **Amazon API Gateway** | REST/HTTP APIs, serverless backends | Custom origin + WAF | Free DTO API GW→CloudFront |
| **Custom HTTP origin (EC2 / on-prem)** | Existing web servers | Restrict via custom secret header + WAF; Origin Shield for on-prem | Origin protocol policy governs TLS |
**When:** Choose S3+OAC for static; ALB/API Gateway for dynamic/serverless; custom HTTP for existing
or on-prem servers (add Origin Shield for capacity-limited on-prem origins).
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (access 2026-07-31)

### Decision: OAC vs OAI for Amazon S3 origins
**Options:** **OAC** (current, recommended) vs **OAI** (legacy).
**Trade-offs:** OAC supports **all S3 Regions** (including opt-in Regions after Dec 2022),
**SSE-KMS**, and **dynamic `PUT`/`DELETE`** requests. OAI does **not** support these and does not
work in Regions launched after January 2023.
**When:** Use **OAC for all new distributions**. Keep OAI only for unmigrated legacy stacks, and plan
migration (dual-principal bucket policy → switch distribution to OAC → remove OAI statement).
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (access 2026-07-31)

### Decision: Real-time logs (Kinesis Data Streams) vs standard logs (S3/CloudWatch/Firehose) vs CloudWatch metrics
**Options / Trade-offs:**
| Option | Latency | Cost | Use when |
|---|---|---|---|
| **Standard logs (v2)** | Best-effort, minutes+ | **Free** (plus destination storage) | Audit, troubleshooting, offline analytics; deliver to S3, CloudWatch Logs, or Kinesis Data Firehose |
| **Real-time logs** | Seconds (via **Amazon Kinesis Data Streams**) | **Additional charge** | Live monitoring/alerting, security response, sampling a % of requests with chosen fields |
| **CloudFront CloudWatch metrics** | Near real-time aggregates | Standard/additional metrics cost | Dashboards/alarms on request/error rates, not per-request detail |
**When:** Start with free standard logs; add real-time logs only where sub-minute reaction is
required (fraud, attack response, live ops).
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html (access 2026-07-31)

### Decision: Single distribution vs multi-distribution strategy
**Options:** One distribution with multiple cache behaviors/origins vs multiple distributions (or a
**multi-tenant distribution** via CloudFront SaaS Manager).
**Trade-offs:** Geo-restriction and some settings apply to the **entire distribution**, so
per-tenant/per-region policy differences force separate distributions. A single distribution
simplifies management and cost. **Multi-tenant distributions** are purpose-built for SaaS providers
serving many similar sites with shared config.
**When:** Split distributions when you need different geo rules, WAF policies, certificates, or
lifecycle per property; use multi-tenant for SaaS fan-out.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html (standard vs multi-tenant) ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html (distribution-wide scope) (access 2026-07-31)

### Decision: IPv6 enabled vs disabled
**Options:** Enable IPv6 on the distribution (default-friendly) vs disable.
**Trade-offs:** Enabling IPv6 serves dual-stack viewers directly. If downstream logic depends on
`c-ip` for allow/deny lists or geo logic, confirm it handles IPv6 addresses; some legacy
integrations only parse IPv4.
**When:** Enable IPv6 unless a downstream system cannot process IPv6 client addresses.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html (distribution settings) — `[IPv6 field behavior: confirm against "All distribution settings reference"]` (access 2026-07-31)

### Decision: Continuous deployment with staging distributions
**Options:** Direct edit of the production distribution vs **continuous deployment** with a staging
distribution and a continuous-deployment policy.
**Trade-offs:** Continuous deployment lets you route a **subset of real production traffic** (by a
single header or by weight) to a staging distribution, validate in real time, then promote to the
primary distribution — instead of testing with simulated traffic. Adds process overhead and has its
own quotas/considerations.
**When:** Use for any high-risk change (cache policy, WAF, TLS, origin) on business-critical
distributions.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment.html (access 2026-07-31)

---

## Section 4 — Anti-Patterns (Never Do)

### Anti-Pattern: Allowing HTTP-only viewer connections
**Why:** Security — cleartext transport exposes data to interception/tampering.
**Risk Level:** CRITICAL
**Blast Radius:** All viewers of the affected cache behavior(s).
❌ **Wrong:**
  Amazon CloudFront cache behavior with `ViewerProtocolPolicy = allow-all` (HTTP served as-is).
✅ **Correct:**
  Amazon CloudFront cache behavior with `ViewerProtocolPolicy = redirect-to-https` (or `https-only`),
  backed by an AWS Certificate Manager (ACM) certificate and a `TLSv1.2_2021`+ security policy.
**Detection:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.*CacheBehavior*.ViewerProtocolPolicy"`
  — flag any `allow-all`.
**Impact:** Data breach / credential theft / session hijacking.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https-viewers-to-cloudfront.html (access 2026-07-31)

### Anti-Pattern: Public-facing distribution with no AWS WAF WebACL
**Why:** Security — no edge filtering of L7 attacks (SQLi, XSS, bad bots, floods).
**Risk Level:** HIGH
**Blast Radius:** Entire distribution and its origin.
❌ **Wrong:**
  Amazon CloudFront distribution with `WebACLId` empty, exposing the origin to raw internet traffic.
✅ **Correct:**
  AWS WAF **WebACL** (scope `CLOUDFRONT`) with managed rule groups + custom rules associated to the
  distribution; verify it does not block `/.well-known/pki-validation/`.
**Detection:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.WebACLId"` — empty = finding.
**Impact:** Application compromise, data exfiltration, origin overload.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-aws-waf.html (access 2026-07-31)

### Anti-Pattern: Caching permissive CORS / authenticated responses at the edge without cache-key awareness
**Why:** Security + correctness — caching `Access-Control-Allow-Origin: *` or per-user responses at a
shared edge can serve one user's private response (or a wildcard CORS policy) to others.
**Risk Level:** HIGH
**Blast Radius:** All viewers hitting the cached object.
❌ **Wrong:**
  Cache policy that omits `Origin`/`Authorization` from the cache key while the origin varies its
  response by those values — cached wildcard CORS or authenticated body served to everyone.
✅ **Correct:**
  Include the relevant headers (e.g., `Origin`, and where responses are user-specific, `Authorization`)
  in the **cache policy** cache key, or mark authenticated responses as non-cacheable (`MinTTL 0` +
  `Cache-Control: no-store`); reflect a specific allowed origin rather than `*`.
**Detection:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.*CacheBehavior*.CachePolicyId"`
  then inspect the cache policy's included headers vs the origin's `Vary` behavior.
**Impact:** Cross-user data leakage / broken CORS security boundary.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-the-cache-key.html (access 2026-07-31)

### Anti-Pattern: Using legacy OAI instead of OAC for a new Amazon S3 origin
**Why:** Reliability + Security + future-proofing — OAI lacks SSE-KMS, dynamic requests, and new-Region
support, and requires workarounds.
**Risk Level:** MEDIUM
**Blast Radius:** The S3-backed distribution (and any KMS-encrypted content it should serve).
❌ **Wrong:**
  Amazon CloudFront origin using `OriginAccessIdentity` (OAI) for a new S3 bucket, with an
  `arn:aws:iam::cloudfront:user/...` principal in the bucket policy.
✅ **Correct:**
  **CloudFront Origin Access Control (OAC)** with `SigningBehavior: always`, S3 Object Ownership
  **Bucket owner enforced**, bucket policy granting `cloudfront.amazonaws.com` with an
  `AWS:SourceArn` condition on the distribution ARN (plus KMS key-policy grant if SSE-KMS).
**Detection:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.Origins.Items[].S3OriginConfig.OriginAccessIdentity"`
  — non-empty OAI value on a new origin = finding.
**Impact:** Blocked SSE-KMS content, no dynamic requests, breakage in newer Regions.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (access 2026-07-31)

### Anti-Pattern: Publicly readable S3 bucket behind CloudFront (origin bypass)
**Why:** Security — viewers (or attackers) can hit the S3 URL directly, bypassing CloudFront, WAF,
signed URLs, and logging.
**Risk Level:** HIGH
**Blast Radius:** All objects in the bucket.
❌ **Wrong:**
  Amazon S3 bucket with public read (or ACLs enabled) used as a CloudFront origin with no OAC.
✅ **Correct:**
  Private S3 bucket (Block Public Access on), **OAC** signing, and a bucket policy that allows only
  `cloudfront.amazonaws.com` scoped by `AWS:SourceArn` to the distribution.
**Detection:**
  `aws s3api get-bucket-policy-status --bucket <bucket>` (expect `IsPublic: false`) and confirm the
  distribution origin has an `OriginAccessControlId`.
**Impact:** Origin bypass → unlogged, unfiltered, uncharged-to-CDN direct access / data exposure.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (access 2026-07-31)

### Anti-Pattern: No origin failover for a critical workload
**Why:** Reliability — a single origin is a single point of failure.
**Risk Level:** HIGH
**Blast Radius:** All viewers during an origin outage.
❌ **Wrong:**
  Amazon CloudFront cache behavior pointing at a single origin with no origin group; an origin 5xx
  surfaces directly to viewers.
✅ **Correct:**
  Amazon CloudFront **origin group** (primary + secondary) with failover status codes
  (e.g., 500/502/503/504) referenced by the cache behavior; optionally combine with custom error pages
  and Origin Shield.
**Detection:**
  `aws cloudfront get-distribution-config --id <ID> --query "DistributionConfig.OriginGroups.Quantity"`
  — `0` on a critical distribution = finding.
**Impact:** Service outage on single-origin failure.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html (access 2026-07-31)

### Anti-Pattern: Neglecting signed-URL / signed-cookie key rotation
**Why:** Security — long-lived, never-rotated signing keys widen the blast radius of a key compromise.
**Risk Level:** MEDIUM
**Blast Radius:** All private content protected by the compromised key.
❌ **Wrong:**
  A single CloudFront public key in a trusted key group, in use for years with no rotation and no
  removal of retired keys.
✅ **Correct:**
  Rotate keys by adding a new public key to the **trusted key group**, migrating signing to it, then
  removing the old key; keep signed-URL/cookie expirations short and store private keys in a secure
  location (e.g., AWS KMS / Secrets Manager-backed workflow).
**Detection:**
  `aws cloudfront get-key-group --id <KEY_GROUP_ID>` and review key age/rotation cadence against policy.
**Impact:** Compromised key → unauthorized access to all protected private content until rotated.
**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PrivateContent.html (access 2026-07-31)

---

## Section 5 — Service Equivalence Map (multi-cloud CDN / edge security)

> Cross-cloud equivalents are provided for architectural mapping only. Feature parity is approximate;
> validate against each provider's current docs before design decisions. AWS entries are verified
> against the *Amazon CloudFront Developer Guide* (access 2026-07-31). Non-AWS columns are provider
> equivalents and should be confirmed on the respective official docs — marked `[verify per provider]`.

| Capability | AWS (verified) | Azure `[verify per provider]` | GCP `[verify per provider]` | OCI `[verify per provider]` |
|---|---|---|---|---|
| CDN / edge delivery | **Amazon CloudFront** | Azure Front Door / Azure CDN | Cloud CDN (with external Application Load Balancer) | OCI Content Delivery Network (CDN) |
| Edge WAF | **AWS WAF** WebACL (`CLOUDFRONT` scope) | Azure WAF on Front Door | Google Cloud Armor | OCI Web Application Firewall (WAF) |
| Origin access lockdown for object store | **OAC** for **Amazon S3** | Private Link / Front Door origin auth to Azure Blob Storage | Signed URLs / IAM for Cloud Storage | Pre-authenticated / private OCI Object Storage |
| Edge compute (light) | **CloudFront Functions** (JS) | Front Door Rules Engine | (limited edge rules) | (rules-based routing) |
| Edge compute (heavy) | **AWS Lambda@Edge** | Azure Functions (regional) | Cloud Functions / Cloud Run (regional) | OCI Functions (regional) |
| Managed TLS certs | **AWS Certificate Manager (ACM)** | Azure-managed certs on Front Door | Google-managed SSL certs | OCI Certificates |
| Signed/tokenized private content | Signed URLs / signed cookies (**trusted key groups**) | Front Door token auth / SAS on Blob | Signed URLs (Cloud CDN) | CDN token authentication |
| Origin failover / HA | **Origin groups** (primary + secondary) | Front Door origin groups + health probes | Backend service failover / health checks | Origin failover config |
| Geo-restriction | CloudFront geo-restriction (country) + **AWS WAF** geo match | Front Door geo-filtering / WAF geomatch | Cloud Armor region rules | WAF geo rules |
| Real-time logs | Real-time logs via **Amazon Kinesis Data Streams** | Front Door diagnostic logs → Log Analytics/Event Hubs | Cloud CDN logs → Cloud Logging | OCI Logging |
| DDoS baseline | AWS Shield Standard (edge, included) | Azure DDoS Protection | Cloud Armor / Google front-end | OCI DDoS protection |

**Source (AWS column):** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html ;
.../distribution-web-aws-waf.html ; .../private-content-restricting-access-to-s3.html ;
.../high_availability_origin_failover.html ; .../georestrictions.html ; .../PrivateContent.html (all access 2026-07-31)

---

## Section 6 — Source Bibliography

All sources are the official **Amazon CloudFront Developer Guide** (`/latest/`) and adjacent official
AWS documentation. The `/latest/` guide is continuously maintained against the current stable service,
so it is the version-absolute source of truth for **AWS CloudFront 2025**. No source used here is
undated community content. Access date for all entries: **2026-07-31**.

### Primary — Amazon CloudFront Developer Guide (official)
1. What is Amazon CloudFront? — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html (access 2026-07-31)
2. Require HTTPS between viewers and CloudFront — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https-viewers-to-cloudfront.html (access 2026-07-31)
3. Supported protocols and ciphers (security policies / min TLS) — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html (access 2026-07-31)
4. Use AWS WAF with a CloudFront distribution — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-aws-waf.html (access 2026-07-31)
5. Access logs (standard logs) — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html (access 2026-07-31)
6. Understand the cache key (cache policy / TTL) — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-the-cache-key.html (access 2026-07-31)
7. Optimize high availability with origin failover (origin groups, custom error pages, timeouts) — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html (access 2026-07-31)
8. Use Amazon CloudFront Origin Shield — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html (access 2026-07-31)
9. Restrict the geographic distribution of your content (geo-restriction) — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html (access 2026-07-31)
10. Restrict access to an Amazon S3 origin (OAC vs OAI) — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (access 2026-07-31)
11. Serve private content with signed URLs and signed cookies (trusted key groups) — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PrivateContent.html (access 2026-07-31)
12. Use field-level encryption to help protect sensitive data — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/field-level-encryption.html (access 2026-07-31)
13. Differences between CloudFront Functions and Lambda@Edge — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html (access 2026-07-31)
14. Use CloudFront continuous deployment (staging distributions) — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment.html (access 2026-07-31)

### Supporting — official AWS
15. Amazon CloudFront pricing (price classes, DTO) — https://aws.amazon.com/cloudfront/pricing/ (access 2026-07-31; the Developer Guide `PriceClass.html` topic redirects here)
16. AWS Well-Architected Framework — https://docs.aws.amazon.com/wellarchitected/ (access 2026-07-31)
17. AWS::CloudFront::Distribution (CloudFormation reference) — https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-cloudfront-distribution-origin.html (access 2026-07-31)

---

## Research Gaps / Unverified Items
- **Price-class edge-location membership** (exact Regions per `PriceClass_200` / `PriceClass_100`):
  the Developer Guide `PriceClass.html` topic now redirects to the pricing page; the North America /
  Europe / Israel (100) and "excludes most expensive" (200) summary reflects the pricing page but the
  precise edge list should be confirmed on https://aws.amazon.com/cloudfront/pricing/ at design time.
- **IPv6 distribution-setting behavior**: general enable/disable is a standard distribution setting;
  confirm exact field semantics in "All distribution settings reference" before codifying.
- **Non-AWS columns of the Service Equivalence Map** are provider-mapping approximations
  (`[verify per provider]`) and were not validated against Azure/GCP/OCI official docs in this pass.

## Verification Checklist (run before hand-off)
- [x] All 6 mandatory sections present (Pillars, Always, Ask-First, Never, Equivalence Map, Bibliography)
- [x] Every pattern cites an official AWS URL with access date (2026-07-31)
- [x] Every Never-Do entry has ❌ Wrong / ✅ Correct using exact AWS service names
- [x] Sources: all official AWS `/latest/` (current stable) — none >12 months stale; the single
      redirected topic (PriceClass → pricing) is flagged inline
- [x] Service Equivalence Map covers CloudFront / Azure Front Door / GCP Cloud CDN / OCI CDN
- [x] AWS-specific names used throughout (Amazon CloudFront, AWS WAF, OAC, ACM, Lambda@Edge, etc.)
