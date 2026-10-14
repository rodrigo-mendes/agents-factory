# AWS CloudFront — CDN Architecture Research (AWS CloudFront 2026)

## Metadata
```yaml
Full_Name: "AWS CDN Architecture - CloudFront"
Cloud_Provider: "AWS"
Architecture_Domain: "CDN Architecture - CloudFront"
Target_Edition: "AWS CloudFront 2026"
Architecture_Context: "General-purpose production CDN (not supplied by requester)"
Official_Source_URL: "https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-26"
Research_Depth: exhaustive
Currency_Threshold: "2027-08-26"
Confidence: High (all patterns triangulated against official AWS documentation + 2025/2026 What's-New announcements)
```

> **Scope note:** `ARCHITECTURE_CONTEXT` was not supplied in the invocation. This research targets a
> general-purpose production web/media CDN workload. Re-run with an explicit context (e.g., "video
> streaming", "multi-tenant B2B SaaS", "regulated financial services") to receive context-specific
> guardrails.

---

## Executive Summary

Amazon CloudFront is AWS's globally distributed content delivery network (CDN). It caches content at
edge locations and regional edge caches, terminating viewer TLS at the edge and pulling from
origins (Amazon S3, Application/Network Load Balancers, EC2, MediaPackage, or any custom HTTP
origin). In `AWS CloudFront 2026` the service is positioned not only as a cache but as a full edge
security and compute perimeter — bundling AWS WAF, AWS Shield DDoS protection, edge functions, and
TLS termination in front of application origins.

The most consequential changes reaching `AWS CloudFront 2026` versus prior editions:
**(1) Flat-rate pricing plans** — launched November 2025 and expanded March 24, 2026 (Free / Pro
$15 / Business $200 / Premium $1,000 per month) bundling CDN + WAF + DDoS + bot management + DNS +
edge compute into a single monthly price with no overage charges.
**(2) VPC origins** (GA November 2024, WebSocket support added May 1, 2026) — lets CloudFront reach
ALBs, NLBs, and EC2 instances in **private subnets** with no public IPs.
**(3) New TLS security policies** `TLSv1.2_2025` and `TLSv1.3_2025`, plus **quantum-safe key
exchanges** (`X25519MLKEM768`, `SecP256r1MLKEM768`) on TLS 1.3.
**(4) IPv6 origins** (September 2025) enabling end-to-end IPv6.
**(5) Three new CloudFront Functions capabilities** (November 2025): edge-location/Regional-Edge-Cache
metadata, raw query-string retrieval, and advanced origin overrides (including SNI).

The three most critical architecture guardrails for a general production CDN in this edition:
**(a)** lock origins private — use Origin Access Control (OAC) for S3 and VPC origins for
ALB/NLB/EC2, never leave the origin publicly reachable; **(b)** require HTTPS end-to-end with a
modern security policy (`TLSv1.2_2021` or newer) and attach an AWS WAF web ACL; and **(c)** engineer
the cache key deliberately with cache policies + CloudFront Functions to maximize cache hit ratio
and shield the origin.

---

## Cloud Architecture Glossary

```
Term: Distribution
Definition: The top-level CloudFront configuration object that maps a set of origins and cache
  behaviors to a delivery domain (dNNN.cloudfront.net or a custom alternate domain name).
Provider Docs Section: DeveloperGuide — Distributions
Architect Usage: One distribution per delivery domain/security boundary. Geo-restriction and WAF
  web ACL attach at the distribution level.
Common Confusion: Confused with a "cache behavior" — a distribution contains multiple behaviors.
```
```
Term: Cache behavior
Definition: A path-pattern-scoped rule set inside a distribution that binds a path (e.g., /api/*)
  to an origin, a viewer protocol policy, a cache policy, an origin request policy, and edge functions.
Provider Docs Section: DeveloperGuide — Cache behavior settings
Architect Usage: Split static vs dynamic vs API paths into separate behaviors to apply different
  caching, TLS, and function logic. Behaviors are evaluated in listed order; the default (*) is last.
Common Confusion: People try to apply per-object caching in one behavior; use path patterns instead.
```
```
Term: Edge location
Definition: A CloudFront point of presence that terminates viewer connections and serves cached content.
Provider Docs Section: DeveloperGuide — How CloudFront works
Architect Usage: First cache tier. Cache misses escalate to a regional edge cache.
Common Confusion: Confused with regional edge cache (a larger mid-tier cache) and Origin Shield.
```
```
Term: Regional edge cache (REC)
Definition: A mid-tier caching layer between edge locations and origins that consolidates requests
  and improves hit ratio for a geographic region.
Provider Docs Section: DeveloperGuide — How CloudFront works / Regional edge caches
Architect Usage: Automatic; no configuration. Origin Shield adds a further consolidation layer on top.
Common Confusion: Confused with Origin Shield, which is an *opt-in single Region* consolidation layer.
```
```
Term: Origin Access Control (OAC)
Definition: The recommended mechanism for CloudFront to send SigV4-signed authenticated requests to
  an S3 (and other AWS) origin so the bucket can stay private.
Provider Docs Section: DeveloperGuide — Restrict access to an Amazon S3 origin
Architect Usage: Always prefer OAC over the legacy OAI. Supports SSE-KMS, all Regions (incl. opt-in
  Regions after Dec 2022), and dynamic PUT/DELETE requests.
Common Confusion: Confused with OAI (legacy) and with VPC origins (for ALB/NLB/EC2, not S3).
```
```
Term: Origin Access Identity (OAI)
Definition: The legacy special CloudFront principal used to grant an S3 bucket access. Superseded by OAC.
Provider Docs Section: DeveloperGuide — Use an origin access identity (legacy, not recommended)
Architect Usage: Do not adopt for new work; migrate existing OAI to OAC. Does not support SSE-KMS,
  dynamic requests, or Regions launched after January 2023.
Common Confusion: Assumed equivalent to OAC — it is strictly less capable.
```
```
Term: VPC origins
Definition: A CloudFront capability to use ALBs, NLBs, and EC2 instances located in private VPC
  subnets as origins, reachable only through CloudFront via an AWS-managed connection.
Provider Docs Section: DeveloperGuide — Restrict access with VPC origins
Architect Usage: Removes the need for a public ALB. Pair with the CloudFront managed prefix list /
  service-managed security group. WebSocket supported as of May 1, 2026.
Common Confusion: Confused with OAC (S3 only) and with PrivateLink.
```
```
Term: Origin Shield
Definition: An optional additional caching layer in a single chosen AWS Region that sits in front of
  the origin, consolidating requests from all regional edge caches into as few as one origin request.
Provider Docs Section: DeveloperGuide — Use Amazon CloudFront Origin Shield
Architect Usage: Enable in the Region with lowest latency to the origin. Best for global viewers,
  just-in-time packaging, on-prem origins, and multi-CDN. Incurs extra per-request charges.
Common Confusion: Confused with the regional edge cache (which is automatic and free).
```
```
Term: Cache policy
Definition: A reusable policy defining the cache key (headers, cookies, query strings) plus TTL and
  compression settings for a cache behavior.
Provider Docs Section: DeveloperGuide — Control the cache key with a policy
Architect Usage: Include the fewest values in the cache key to raise the hit ratio. Use AWS managed
  cache policies (e.g., CachingOptimized) where possible.
Common Confusion: Confused with origin request policy (what CloudFront forwards to the origin, which
  is NOT part of the cache key).
```
```
Term: Origin request policy
Definition: A reusable policy defining which headers/cookies/query strings CloudFront forwards to
  the origin — independent of the cache key.
Provider Docs Section: DeveloperGuide — Control origin requests with a policy
Architect Usage: Forward values the origin needs (e.g., CloudFront-Viewer-Country) without polluting
  the cache key.
Common Confusion: Believed to affect caching — it does not.
```
```
Term: Response headers policy
Definition: A reusable policy that adds/removes HTTP response headers (CORS, HSTS, security headers)
  without changing origin or function code.
Provider Docs Section: DeveloperGuide — Add response headers with a policy
Architect Usage: Centralize security headers (Strict-Transport-Security, X-Content-Type-Options).
Common Confusion: Confused with edge functions; response headers policies need no code.
```
```
Term: CloudFront Functions
Definition: Lightweight JavaScript (ECMAScript 5.1 / runtime 2.0) functions running at edge
  locations on viewer request/response events at sub-millisecond duration and massive scale.
Provider Docs Section: DeveloperGuide — Customize at the edge with CloudFront Functions
Architect Usage: Cache-key normalization, header manipulation, URL rewrites/redirects, JWT checks.
  Only runtime for CloudFront KeyValueStore.
Common Confusion: Confused with Lambda@Edge (heavier, more triggers, network access).
```
```
Term: Lambda@Edge
Definition: Node.js/Python functions triggered on any of four CloudFront events (viewer request/
  response, origin request/response) with network/filesystem access and higher limits.
Provider Docs Section: DeveloperGuide — Customize at the edge with Lambda@Edge
Architect Usage: Use when you need the request body, third-party libraries, network calls, or
  origin-facing logic; up to 30 s duration.
Common Confusion: Assumed to run at all edge locations — origin-facing triggers run at the REC/Origin
  Shield Region.
```
```
Term: CloudFront KeyValueStore (KVS)
Definition: A globally distributed, low-latency key-value datastore readable from CloudFront
  Functions (JavaScript runtime 2.0 only).
Provider Docs Section: DeveloperGuide — Amazon CloudFront KeyValueStore
Architect Usage: Externalize redirect maps, feature flags, and A/B config from function code.
Common Confusion: Not available to Lambda@Edge.
```
```
Term: Origin group / origin failover
Definition: A pairing of a primary and secondary origin; CloudFront fails over to the secondary on
  configured failover status codes or connection/timeout failures.
Provider Docs Section: DeveloperGuide — Optimize high availability with CloudFront origin failover
Architect Usage: High availability across two origins; failover only for GET/HEAD/OPTIONS methods.
Common Confusion: Assumed to load-balance — it does not; all requests go to primary first.
```
```
Term: Security policy (minimum SSL/TLS version)
Definition: The named policy that sets the minimum viewer TLS version and the cipher suite for a
  distribution (e.g., TLSv1.2_2021, TLSv1.2_2025, TLSv1.3_2025).
Provider Docs Section: DeveloperGuide — Supported protocols and ciphers between viewers and CloudFront
Architect Usage: Use TLSv1.2_2021 or newer for new distributions; TLSv1.3_2025 for the strictest.
Common Confusion: Confused with the origin protocol policy (CloudFront-to-origin TLS).
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**M1 — Lock S3 origins with Origin Access Control (OAC)**
- Pillar Alignment: Security
- Why: OAC lets the S3 bucket stay fully private while CloudFront sends SigV4-signed requests. AWS
  explicitly recommends OAC over legacy OAI because OAC supports all Regions (including opt-in
  Regions launched after Dec 2022), SSE-KMS, and dynamic `PUT`/`DELETE` requests.
- AWS Services: CloudFront OAC, Amazon S3 bucket policy, AWS KMS (for SSE-KMS)
- Architecture Decision: Create an `AWS::CloudFront::OriginAccessControl` with
  `SigningBehavior: always` and `SigningProtocol: sigv4`; set S3 Object Ownership to
  **Bucket owner enforced**; grant `cloudfront.amazonaws.com` `s3:GetObject` scoped by
  `AWS:SourceArn` = the distribution ARN. For SSE-KMS, add `kms:Decrypt`/`Encrypt`/`GenerateDataKey*`
  to the key policy with the same `SourceArn` condition.
- Verification: `aws cloudfront get-distribution-config` shows `OriginAccessControlId` set and
  `OriginAccessIdentity` empty; S3 `get-public-access-block` shows all four blocks `true`.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (accessed 2026-08-26)

**M2 — Require HTTPS end-to-end with a modern security policy**
- Pillar Alignment: Security
- Why: Viewer protocol policy `Redirect HTTP to HTTPS` or `HTTPS only` guarantees encrypted transit;
  a modern security policy removes weak protocols/ciphers.
- AWS Services: CloudFront viewer protocol policy, AWS Certificate Manager (ACM, us-east-1 for
  CloudFront), CloudFront security policy
- Architecture Decision: Set Viewer Protocol Policy to `Redirect HTTP to HTTPS` (or `HTTPS only`);
  attach an ACM certificate for custom domains (must be in us-east-1); set security policy to
  `TLSv1.2_2021` minimum (`TLSv1.3_2025` for strictest, enabling quantum-safe key exchange). Use SNI
  (default) rather than dedicated-IP custom SSL unless legacy clients require it.
- Verification: `openssl s_client -connect <domain>:443 -tls1_1` should fail;
  `aws cloudfront get-distribution-config` shows the chosen `MinimumProtocolVersion`.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https-viewers-to-cloudfront.html ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html (accessed 2026-08-26)

**M3 — Attach an AWS WAF web ACL and rely on AWS Shield Standard**
- Pillar Alignment: Security / Reliability
- Why: A WAF web ACL provides Layer-7 filtering (SQLi, XSS, rate limiting, geo-match, bot control)
  at the edge; AWS Shield Standard DDoS protection is automatic and free for all distributions.
- AWS Services: AWS WAF (WAFv2, scope `CLOUDFRONT`, created in us-east-1), AWS Shield Standard
  (default), AWS Shield Advanced (optional)
- Architecture Decision: Create a WAFv2 web ACL with scope `CLOUDFRONT` in us-east-1, attach via the
  distribution's `WebACLId`; add AWS managed rule groups + a rate-based rule. Consider Shield
  Advanced for business-critical workloads (24/7 SRT support, DDoS cost protection).
- Verification: `aws wafv2 get-web-acl-for-resource` returns the ACL for the distribution ARN.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/cloudfront-chapter.html (accessed 2026-08-26)

**M4 — Keep ALB/NLB/EC2 origins private with VPC origins**
- Pillar Alignment: Security
- Why: VPC origins let CloudFront reach load balancers and instances in private subnets over an
  AWS-managed connection, eliminating the public ALB and shrinking the attack surface.
- AWS Services: CloudFront VPC origins, Application/Network Load Balancer or EC2 in private subnets,
  CloudFront managed prefix list, service-managed security group `CloudFront-VPCOrigins-Service-SG`
- Architecture Decision: Place the ALB/NLB/EC2 in private subnets; create a VPC origin;
  update the origin resource's security group to allow inbound from the CloudFront managed prefix
  list. WebSocket traffic supported as of May 1, 2026.
- Verification: Origin resource has no public IP; direct public curl to the ALB times out; requests
  succeed only through the distribution domain.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html ; https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-cloudfront-vpc-origins (accessed 2026-08-26)

**M5 — Engineer the cache key with cache policies for a high cache hit ratio**
- Pillar Alignment: Performance Efficiency / Cost Optimization
- Why: The cache key determines cache hits. Including fewer headers/cookies/query strings raises the
  hit ratio, reducing origin load, latency, and cost.
- AWS Services: CloudFront cache policy, origin request policy, response headers policy, CloudFront Functions
- Architecture Decision: Use AWS managed cache policies (e.g., `CachingOptimized`) for static assets;
  forward origin-only values via an origin request policy (not the cache key); normalize the cache
  key in a CloudFront Function; enable automatic compression (Gzip/Brotli) in the cache policy.
- Verification: Monitor `CacheHitRate` in the CloudFront console/CloudWatch; inspect
  `x-edge-detailed-result-type` in logs (`Hit`, `OriginShieldHit`, `Miss`).
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/controlling-the-cache-key.html (accessed 2026-08-26)

**M6 — Serve private content with signed URLs/cookies using trusted key groups**
- Pillar Alignment: Security
- Why: For per-user access control, signed URLs/cookies restrict content by expiry (and, with a
  custom policy, by IP range and start time). Trusted **key groups** are the recommended signer
  mechanism (no root AWS account keys required).
- AWS Services: CloudFront signed URLs / signed cookies, trusted key groups (RSA 2048 or ECDSA 256)
- Architecture Decision: Upload a public key, reference it in a key group on the distribution, sign
  with the private key in your application. Use canned policy for single-file/expiry-only; custom
  policy for wildcards, IP restriction, or a start time. Use signed cookies for multiple files
  without changing URLs.
- Verification: Unsigned request returns HTTP 403; tampered signature returns 403.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-signed-urls.html (accessed 2026-08-26)

**M7 — Enable logging and monitoring (standard logs + CloudWatch)**
- Pillar Alignment: Operational Excellence
- Why: Standard access logs (free) and real-time logs give request-level visibility (including
  `x-edge-detailed-result-type` for cache diagnosis and `sc-status` 403 for geo/WAF blocks).
- AWS Services: CloudFront standard logs (v2), CloudFront real-time logs, Amazon CloudWatch metrics
- Architecture Decision: Enable standard logs to S3/CloudWatch/Firehose; add real-time logs only
  where sub-second visibility is needed (extra cost); alarm on `4xxErrorRate`, `5xxErrorRate`,
  `OriginLatency`, `CacheHitRate`.
- Verification: Log entries arrive in the configured destination; CloudWatch shows CloudFront metrics.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/real-time-logs.html (accessed 2026-08-26)

### ⚠️ Architectural Decisions

**D1 — CloudFront Functions vs Lambda@Edge**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | CloudFront Functions | CloudFront Functions (JS ES5.1 / runtime 2.0) | Sub-ms latency, millions rps, cost, KVS access | No network/filesystem/body access; viewer events only; 2 MB mem, 10 KB code | Cache-key normalization, header rewrites, redirects, JWT validation |
  | Lambda@Edge | Lambda@Edge (Node.js/Python) | Network + filesystem + body access, 3rd-party libs, 4 event triggers | ≤10,000 rps/Region, higher latency, up to 30 s | Origin-facing logic, request body inspection, AWS SDK/API calls |

- Cost Profile: CloudFront Functions ≈ 1/6 the price per invocation and much lower latency; Lambda@Edge billed per request + duration.
- Scaling Characteristics: Functions scale to millions rps; Lambda@Edge caps at 10,000 rps per Region.
- Lock-in Assessment: Both AWS-proprietary; Functions logic (ES5.1) is more portable than Lambda@Edge integrations.
- Architect Instruction: "Ask whether the logic needs the request body, network calls, third-party
  libraries, or origin-facing triggers — if yes, Lambda@Edge; otherwise CloudFront Functions."
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html (accessed 2026-08-26)

**D2 — Pay-as-you-go vs flat-rate pricing plans (2026)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Pay-as-you-go | CloudFront standard pricing | Pay only for actual usage; unlimited scale | Cost variability; DDoS/traffic-spike cost exposure | Predictable/steady or very large workloads with committed discounts |
  | Flat-rate plan | CloudFront plans (Free/Pro $15/Business $200/Premium $1,000 per month) | Fixed monthly price, no overage, bundled WAF+DDoS+bot mgmt+DNS | Feature gating by tier (e.g., viewer mTLS = Premium; bot controls ≥ Business) | Small/medium sites wanting predictable spend and bundled protection |

- Cost Profile: Flat-rate absorbs spikes up to ~3x the monthly allowance with no overage; Lambda@Edge
  invocations still billed separately at standard rates even on plans.
- Lock-in Assessment: Both AWS-only; plans do not change the underlying architecture.
- Architect Instruction: "Ask for expected monthly traffic volume and spike profile — small/medium
  predictable workloads favor a flat-rate plan; high-volume workloads with committed-use discounts
  favor pay-as-you-go. Confirm required features against the tier gate (mTLS, bot controls, AI dashboard)."
- Source: https://aws.amazon.com/blogs/networking-and-content-delivery/amazon-cloudfront-flat-rate-pricing-plans-new-features-and-expanded-capabilities/ (accessed 2026-08-26)
  > ⚠️ Source dated 2026-03; verify current tier pricing/feature gates before committing.

**D3 — Origin Shield: enable or not**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Origin Shield enabled | CloudFront Origin Shield (single Region) | Higher hit ratio, fewer origin requests, better origin availability | Extra per-request charges; not for low-cacheability dynamic content | Global viewers, JIT packaging/live video, on-prem/bandwidth-limited origins, multi-CDN |
  | No Origin Shield | Default REC tier | No extra cost | Duplicate origin requests across RECs | Low-traffic or single-region viewer base |

- Cost Profile: Charged per request that traverses Origin Shield as an incremental layer; requests
  landing in the same Region as Origin Shield are skipped (no charge).
- Lock-in Assessment: AWS-only feature, per-origin toggle — reversible.
- Architect Instruction: "Ask about viewer geographic spread and origin type — enable Origin Shield
  in the Region with lowest latency to the origin for global/multi-CDN/JIT-packaging workloads; skip
  it for low-cacheability dynamic content."
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html (accessed 2026-08-26)

**D4 — CloudFront geo-restriction vs AWS WAF geo-match vs third-party geolocation**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | CloudFront geo-restriction | CloudFront geographic restrictions | Simple country allow/deny for the whole distribution | Country-level only; whole-distribution scope; ~99.8% IP accuracy | Blanket country licensing rules |
  | AWS WAF geo-match | AWS WAF geo-match rule | Per-path/per-rule granularity, combinable with other WAF logic | Requires WAF; still country-level | Mixed rules, partial-path restrictions |
  | Third-party geolocation | External service + signed URLs | City/postal/lat-long granularity, per-file | Custom app logic; extra vendor | Sub-country granularity or per-file control |

- Architect Instruction: "Ask whether restriction is country-level (use CloudFront geo-restriction or
  WAF geo-match) or finer than country/per-file (use a third-party geolocation service with signed URLs)."
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html (accessed 2026-08-26)

### 🚫 Anti-Patterns

**A1 — Publicly reachable origin behind CloudFront**
- Risk Level: CRITICAL
- Why: Attackers bypass CloudFront (and its WAF/Shield/geo controls) by hitting the origin's public
  IP/DNS directly — violates Security pillar.
- ❌ Wrong: Public S3 bucket with Block Public Access disabled as an origin; or a public
  internet-facing ALB in a public subnet as an origin.
- ✅ Correct: S3 bucket private with **Block Public Access enabled** + CloudFront **OAC**
  (`SigningBehavior: always`); ALB/NLB/EC2 in **private subnets** reached via **VPC origins** with
  the CloudFront managed prefix list on the origin security group.
- Detection: `aws s3api get-public-access-block`; test direct curl to the origin's public endpoint
  (should fail); check ALB scheme is `internal` or fronted by a VPC origin.
- Impact: Data breach / control bypass.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html (accessed 2026-08-26)

**A2 — Using legacy OAI for new S3 origins**
- Risk Level: MEDIUM
- Why: OAI does not support SSE-KMS, dynamic requests, or Regions launched after January 2023;
  it needs workarounds and is explicitly not recommended.
- ❌ Wrong: New distribution configured with `OriginAccessIdentity` (OAI) pointing at an SSE-KMS bucket.
- ✅ Correct: `AWS::CloudFront::OriginAccessControl` (OAC) with `SigningBehavior: always`,
  `SigningProtocol: sigv4`, and a KMS key-policy grant to `cloudfront.amazonaws.com`.
- Detection: `aws cloudfront get-distribution-config` shows a non-empty `OriginAccessIdentity`.
- Impact: Broken SSE-KMS delivery / future Region incompatibility.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (accessed 2026-08-26)

**A3 — Allowing HTTP or weak TLS to viewers**
- Risk Level: HIGH
- Why: Cleartext HTTP and deprecated TLS (TLSv1/1.1, SSLv3) expose content to interception — Security pillar.
- ❌ Wrong: Viewer Protocol Policy `HTTP and HTTPS` with security policy `TLSv1` (or `SSLv3`).
- ✅ Correct: Viewer Protocol Policy `Redirect HTTP to HTTPS` or `HTTPS only` with security policy
  `TLSv1.2_2021` minimum (or `TLSv1.3_2025` for quantum-safe key exchange).
- Detection: `openssl s_client -tls1_1` succeeds (should fail); distribution `MinimumProtocolVersion`
  is a `TLSv1*`/`SSLv3` value.
- Impact: Data interception / compliance violation.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html (accessed 2026-08-26)

**A4 — No AWS WAF web ACL on an internet-facing distribution**
- Risk Level: HIGH
- Why: Without a web ACL there is no L7 filtering (SQLi/XSS/bot/rate limiting) at the edge — Security/Reliability.
- ❌ Wrong: Public distribution serving an API with no `WebACLId` associated.
- ✅ Correct: WAFv2 web ACL (scope `CLOUDFRONT`, us-east-1) with AWS managed rule groups + a
  rate-based rule associated to the distribution.
- Detection: `aws wafv2 get-web-acl-for-resource` returns empty for the distribution ARN.
- Impact: Application-layer compromise / DDoS amplification.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/cloudfront-chapter.html (accessed 2026-08-26)

**A5 — Over-inclusive cache key (forwarding all headers/cookies/query strings to the cache key)**
- Risk Level: MEDIUM
- Why: Forwarding everything into the cache key fragments the cache, collapses the hit ratio, and
  hammers the origin — Performance/Cost pillars.
- ❌ Wrong: Legacy "forward all cookies / all query strings" or a cache policy that includes every
  viewer header in the cache key.
- ✅ Correct: A cache policy that includes only the values that vary the response; forward
  origin-only values via an **origin request policy** (outside the cache key); normalize with a
  CloudFront Function.
- Detection: `CacheHitRate` metric persistently low; many `Miss` in `x-edge-detailed-result-type`.
- Impact: Cost overrun / origin overload.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/controlling-the-cache-key.html (accessed 2026-08-26)

**A6 — Single origin with no failover for high-availability workloads**
- Risk Level: MEDIUM
- Why: A single origin is a single point of failure for cache-miss traffic — Reliability pillar.
- ❌ Wrong: One origin, no origin group, default 30 s (3×10 s) connection behavior for a latency-
  sensitive streaming workload.
- ✅ Correct: An **origin group** (primary + secondary) with failover status codes (e.g., 500, 502,
  503, 504) and tuned origin connection timeout/attempts; note failover only applies to GET/HEAD/OPTIONS.
- Detection: Distribution has no origin group on the cache behavior.
- Impact: Service outage on origin failure.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html (accessed 2026-08-26)

---

## Cloud-Native Design Patterns

**Static site + SPA delivery (S3 + OAC + CloudFront)**
- Category: Scalability
- Problem: Serve a static/single-page app globally with low latency and a private origin.
- Solution on AWS: Private S3 bucket (Block Public Access on) + OAC; `CachingOptimized` cache policy;
  a CloudFront Function to rewrite SPA deep links to `/index.html`; custom error responses mapping
  403/404 to `/index.html` (200).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Latency | Edge-cached, sub-ms function rewrites | Function invocation cost (minimal) |
  | Security | Origin never public | OAC + bucket policy setup |

- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (accessed 2026-08-26)

**Dynamic/API acceleration (VPC-origin ALB behind CloudFront)**
- Category: Communication / Security
- Problem: Accelerate and protect a dynamic API whose origin should not be public.
- Solution on AWS: Private ALB as a VPC origin; separate cache behavior for `/api/*` with a
  short/zero TTL and an origin request policy forwarding needed headers; WAF web ACL with a
  rate-based rule; HTTP/2 and HTTP/3 enabled for viewers.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | No public ALB; WAF at edge | VPC origin + SG/prefix-list config |
  | Performance | TLS termination + HTTP/3 at edge | Low cacheability for dynamic paths |

- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html (accessed 2026-08-26)

**Edge personalization/routing without origin round-trips (CloudFront Functions + KeyValueStore)**
- Category: Scalability
- Problem: Redirects, A/B routing, or header injection at scale without adding origin latency.
- Solution on AWS: CloudFront Function (runtime 2.0) reading a redirect/flag map from CloudFront
  KeyValueStore on the viewer-request event; use new (Nov 2025) edge-location/REC metadata for
  geo-specific routing.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Latency | Sub-ms, no origin call | ES5.1/runtime-2.0 constraints (no network/body) |
  | Operability | Config in KVS, not code | KVS update propagation |

- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html ; https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-cloudfront-3-functions-capabilities (accessed 2026-08-26)

---

## Security Architecture

**Edge perimeter (WAF + Shield + geo-restriction + TLS)**
- AWS Services: AWS WAF (scope CLOUDFRONT, us-east-1), AWS Shield Standard (auto) / Advanced (opt-in),
  CloudFront geographic restrictions, ACM certificate, CloudFront security policy
- Architecture: Viewer → CloudFront edge (TLS terminate with `TLSv1.2_2021`+ / quantum-safe on
  `TLSv1.3_2025`) → WAF web ACL evaluation → geo-restriction check → cache/origin. Shield Standard
  absorbs L3/4 DDoS automatically; Shield Advanced adds SRT + cost protection.
- Compliance Alignment: Encryption-in-transit and network perimeter controls (framework reference
  only, not legal advice). Note: `/.well-known/pki-validation/` is exempt from geo-restriction so
  CloudFront managed certificate validation succeeds — do not let WAF/bot rules block that path.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/cloudfront-chapter.html ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html (accessed 2026-08-26)

**Private content (signed URLs / signed cookies + field-level encryption)**
- AWS Services: CloudFront signed URLs, signed cookies, trusted key groups (RSA 2048 / ECDSA 256),
  field-level encryption
- Architecture: Application authorizes the user and signs a URL/cookie (canned or custom policy);
  CloudFront validates the signature with the key group's public key and enforces expiry (and IP/
  start-time in a custom policy). Field-level encryption protects sensitive POSTed fields end-to-end.
- Compliance Alignment: Access control + data-in-transit field protection (framework reference only).
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-signed-urls.html (accessed 2026-08-26)

**Mutual TLS (mTLS)**
- AWS Services: CloudFront viewer mTLS (Premium plan tier), origin mTLS (Business tier and above on
  flat-rate plans)
- Architecture: Viewer mTLS requires client certificates from viewers; origin mTLS authenticates
  CloudFront to the origin. Availability is gated by flat-rate plan tier (viewer mTLS = Premium).
- Source: https://aws.amazon.com/blogs/networking-and-content-delivery/amazon-cloudfront-flat-rate-pricing-plans-new-features-and-expanded-capabilities/ (accessed 2026-08-26)
  > ⚠️ Source dated 2026-03; verify tier gating before design commitment.

---

## Operational Patterns

**Observability**
- AWS Services: CloudFront standard logs (v2, free), real-time logs (paid), CloudWatch metrics
- Architecture: Standard logs → S3/CloudWatch/Firehose; alarm on `4xx/5xxErrorRate`, `OriginLatency`,
  `CacheHitRate`; diagnose caching with `x-edge-detailed-result-type` (`Hit`, `Miss`, `OriginShieldHit`).
- Cost Profile: Low (standard logs free; real-time logs and Origin Shield add cost).
- Automation: Automate log delivery + alarms; manual review of WAF/geo 403 spikes.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html (logging fields) (accessed 2026-08-26)

**High availability (origin failover)**
- RTO/RPO: Failover is near-immediate on configured status codes; default primary attempt window is
  30 s (3 attempts × 10 s) before failover — tune down for streaming.
- AWS Services: CloudFront origin groups (primary/secondary), Route 53 DNS failover (complementary)
- Architecture: Origin group with failover codes (400, 403, 404, 416, 429, 500, 502, 503, 504);
  failover only for GET/HEAD/OPTIONS; `OPTIONS` must be a cached method for failover on OPTIONS.
- Cost Profile: Low (no extra charge for origin groups themselves).
- Automation: Failover is automatic; pair with custom error pages per origin.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html (accessed 2026-08-26)

---

## Reference Architectures

**Global static/SPA site**
- Context: Marketing site / SPA served worldwide.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Edge | CloudFront distribution | Global cache + TLS + HTTP/3 |
  | Security | AWS WAF (CLOUDFRONT) + Shield Standard | L7 filtering + DDoS |
  | Origin access | OAC | Private S3 access |
  | Origin | Private S3 bucket (BPA on) | Static assets |
  | Edge logic | CloudFront Function | SPA path rewrite |
  | Certs | ACM (us-east-1) | Custom domain TLS |

- Key Decisions: cache policy (managed `CachingOptimized`), custom error → index.html, security policy.
- Scaling Path: Add Origin Shield when viewer base goes global/multi-CDN; add KVS for redirect maps.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (accessed 2026-08-26)

**Dynamic web app / API**
- Context: Authenticated API + web app with a private compute tier.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Edge | CloudFront distribution | TLS terminate, route by path |
  | Security | AWS WAF + Shield (Advanced optional) | L7 + DDoS |
  | Origin access | VPC origins | Reach private ALB |
  | Origin | Private ALB → ECS/EKS/EC2 | Compute |
  | Static | S3 + OAC (separate behavior) | Static assets |
  | Edge logic | Lambda@Edge / CloudFront Functions | Auth, header injection |
  | HA | Origin group (primary/secondary) | Failover |

- Key Decisions: per-path cache behaviors, origin request policy for dynamic paths, failover codes.
- Scaling Path: Add Origin Shield, second-Region secondary origin, Route 53 failover.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html (accessed 2026-08-26)

---

## Service Equivalence Map

> `CLOUD_PROVIDER` = AWS (single provider). Cross-provider CDN mapping included to aid architects
> evaluating alternatives; equivalence ≠ feature parity.

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| CDN | **CloudFront** | Cloud CDN / Media CDN | Front Door / Azure CDN | OCI CDN |
| Edge functions (light) | CloudFront Functions | (Cloud CDN + Cloud Run funcs) | Front Door Rules Engine | — |
| Edge functions (full) | Lambda@Edge | Cloud Run / Cloud Functions | Azure Functions (origin) | OCI Functions (origin) |
| Edge WAF | AWS WAF (CLOUDFRONT scope) | Cloud Armor | Azure WAF (Front Door) | OCI WAF |
| DDoS | AWS Shield Standard/Advanced | Cloud Armor (Adaptive Protection) | Azure DDoS Protection | OCI DDoS Protection |
| Private origin access (object) | OAC (S3) | Signed URLs + IAM | Private endpoints / SAS | Pre-authenticated requests |
| Private origin access (compute) | VPC origins | Serverless NEG / internal LB | Private Link / Private Origin | Private endpoints |
| Edge KV store | CloudFront KeyValueStore | — | — | — |
| Certificates | ACM (us-east-1) | Google-managed certs | Azure-managed certs | OCI Certificates |

Source: blueprint service map + https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/ (accessed 2026-08-26)

---

## Provider Differentiators

- **CloudFront Functions + KeyValueStore**: Sub-millisecond JS at the edge with a globally
  replicated KV store readable in-function — no direct equivalent in other CDNs. Architecture impact:
  move redirect/routing/flag logic to the edge without origin round-trips or code redeploys.
  Caveat: KVS only with JavaScript runtime 2.0. Source:
  https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html
- **VPC origins**: Native private-subnet ALB/NLB/EC2 origins over an AWS-managed connection, no
  public ALB required. WebSocket support since May 1, 2026. Caveat: no Gateway Load Balancers,
  dual-stack NLBs, NLBs with TLS listeners, gRPC, or Lambda@Edge origin triggers. Source:
  https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html
- **Quantum-safe TLS 1.3 key exchange**: `X25519MLKEM768` / `SecP256r1MLKEM768` on `TLSv1.3_2025`.
  Architecture impact: forward-secrecy against future quantum attacks for the most sensitive
  workloads. Caveat: TLS 1.3 only. Source:
  https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html
- **Flat-rate pricing plans (2026)**: Fixed monthly, no-overage bundle of CDN + WAF + DDoS + bot
  management + DNS. Caveat: feature gating by tier. Source:
  https://aws.amazon.com/blogs/networking-and-content-delivery/amazon-cloudfront-flat-rate-pricing-plans-new-features-and-expanded-capabilities/

---

## Scenario Coverage

**Standard Case**: Global site/app with static assets on S3 and a dynamic API on private compute.
- Approach: One distribution; `/*` static behavior → S3 + OAC with `CachingOptimized`; `/api/*`
  behavior → VPC-origin ALB with an origin request policy + short TTL; WAF web ACL + Shield Standard;
  `Redirect HTTP to HTTPS` + `TLSv1.2_2021`; standard logs + CloudWatch alarms.
- Key Decisions: cache-key design per behavior; failover origin group for the API; Origin Shield if global.

**Edge Case**: Live-streaming / just-in-time packaging with global audience and an on-prem/MediaPackage origin.
- Approach: Enable Origin Shield in the Region closest to the origin to consolidate REC requests;
  tune origin connection timeout/attempts for fast failover; origin group with media-quality-score
  selection for MediaPackage v2; real-time logs for sub-second visibility.

**Anti-Pattern Case**: Request to "just make the S3 bucket/ALB public and point CloudFront at it."
- Clarification: Refuse and flag (A1). Ask whether the origin can be made private via OAC (S3) or
  VPC origins (ALB/NLB/EC2); confirm Block Public Access and security-group/prefix-list configuration
  before proceeding.

---

## §7 Research Iteration Changelog

| Iteration | Item | Action | Source | Status |
|-----------|------|--------|--------|--------|
| 0 | All core areas (OAC, TLS, cache, edge functions, failover, VPC origins, Origin Shield, geo, WAF, pricing) | Initial exhaustive fetch across official DeveloperGuide + What's-New + Networking blog | Official AWS docs + announcements | Verified |
| 0 | AWS WAF integration + VPC origins pages initially returned header-only | Re-queried via WAF chapter + What's-New/re:Post/official VPC-origins doc | https://docs.aws.amazon.com/waf/.../cloudfront-chapter.html ; VPC origins doc | Resolved |
| — | Zero unverified items remaining | Gap-loop terminated early (before MAX_ITERATIONS=5) | — | Complete |

---

## Source Bibliography

All accessed 2026-08-26. Primary source hierarchy: official AWS documentation > official AWS What's-New / Networking & Content Delivery blog.

1. Restrict access to an Amazon S3 origin (OAC / OAI) — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html
2. Restrict access with VPC origins — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html
3. Amazon CloudFront announces VPC origins (What's New, Nov 2024) — https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-cloudfront-vpc-origins
4. Use signed URLs — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-signed-urls.html
5. Control the cache key with a policy — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/controlling-the-cache-key.html
6. Differences between CloudFront Functions and Lambda@Edge — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html
7. Optimize high availability with CloudFront origin failover — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html
8. Require HTTPS between viewers and CloudFront — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https-viewers-to-cloudfront.html
9. Supported protocols and ciphers between viewers and CloudFront (security policies, quantum-safe) — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html
10. Use Amazon CloudFront Origin Shield — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html
11. Restrict the geographic distribution of your content — https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html
12. AWS WAF + CloudFront chapter — https://docs.aws.amazon.com/waf/latest/developerguide/cloudfront-chapter.html
13. CloudFront flat-rate pricing plans: new features and expanded capabilities (Networking & Content Delivery blog, Mar 2026) — https://aws.amazon.com/blogs/networking-and-content-delivery/amazon-cloudfront-flat-rate-pricing-plans-new-features-and-expanded-capabilities/  ⚠️ dated 2026-03
14. Amazon CloudFront announces 3 new CloudFront Functions capabilities (What's New, Nov 2025) — https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-cloudfront-3-functions-capabilities
15. Amazon CloudFront announces support for IPv6 origins (What's New, Sep 2025) — https://aws.amazon.com/about-aws/whats-new/2025/09/amazon-cloudfront-ipv6-origins

---

> **Next step:** Run `/skill-best-practices-validator` on this file, and consider
> `/skill-creator` to convert it into a SKILL.md. Re-run this research with an explicit
> `ARCHITECTURE_CONTEXT` for context-specific guardrails (e.g., video streaming, regulated workloads).
