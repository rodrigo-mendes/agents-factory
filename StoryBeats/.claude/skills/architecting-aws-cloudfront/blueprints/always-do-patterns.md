# Always-Do Patterns — Amazon CloudFront

> 14 mandatory patterns. Every pattern cites an official AWS source accessed 2026-07-31.
> All AWS service names are exact (no generic terms).
> Run the Verification commands after every distribution creation or change.

---

### Pattern 1: Enforce HTTPS for Viewer Connections

**Why:** Protects data in transit; prevents interception, tampering, and credential theft.
Alignment: Security pillar — `ViewerProtocolPolicy` controls per-cache-behavior HTTPS enforcement.

**AWS Service:** Amazon CloudFront (cache behavior `ViewerProtocolPolicy`), AWS Certificate Manager (ACM) for custom domains.

**Architecture Decision:**
Set `ViewerProtocolPolicy` to `redirect-to-https` (301/307 redirect of HTTP to HTTPS) or
`https-only` (HTTP returns 403 Forbidden). Apply to the **default cache behavior** AND every
additional cache behavior. For custom domains, provision or import a certificate in **AWS Certificate
Manager (ACM) in us-east-1** (required for CloudFront global distributions). Default CloudFront
domains (`*.cloudfront.net`) use a CloudFront-managed certificate automatically.

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.DefaultCacheBehavior.ViewerProtocolPolicy"
# Expected: "redirect-to-https" or "https-only"

# Check all additional cache behaviors too
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.CacheBehaviors.Items[].ViewerProtocolPolicy"
# Expected: no "allow-all" in the output
```

**Trade-offs:** `redirect-to-https` bills the original HTTP request + the redirected HTTPS request
(two billed requests). Negligible in practice; the security benefit outweighs the cost.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https-viewers-to-cloudfront.html (access 2026-07-31)

---

### Pattern 2: Set a Modern Minimum TLS Security Policy

**Why:** The security policy controls which TLS protocol versions and cipher suites CloudFront
negotiates with viewers. Legacy policies allow TLS 1.0/1.1, which are deprecated and non-compliant
with PCI DSS and other security baselines. Alignment: Security pillar.

**AWS Service:** Amazon CloudFront (`ViewerCertificate.MinimumProtocolVersion`).

**Architecture Decision:**
Use `TLSv1.2_2021` as the baseline minimum. Prefer `TLSv1.2_2025` or `TLSv1.3_2025` where
client compatibility allows. CloudFront supports TLS 1.3 and quantum-safe key exchanges
(`X25519MLKEM768`, `SecP256r1MLKEM768`) on TLS 1.3 connections. The stronger policies require
**SNI** (Server Name Indication) — they are incompatible with dedicated IP (legacy) SSL at the edge.

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.ViewerCertificate.MinimumProtocolVersion"
# Expected: "TLSv1.2_2021" or newer (TLSv1.2_2025 / TLSv1.3_2025)
```

**Trade-offs:** Stronger policies exclude very old clients that only support TLS 1.0/1.1. Acceptable
for nearly all production workloads — TLS 1.0/1.1 client share is below 0.1% globally.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html (access 2026-07-31)

---

### Pattern 3: Attach AWS WAF WebACL (CLOUDFRONT Scope) to Every Public Distribution

**Why:** Filters malicious traffic at the edge before it reaches the origin — mitigates OWASP Top 10
and volumetric attacks, reduces origin load. Alignment: Security pillar.

**AWS Service:** AWS WAF (WebACL, scope `CLOUDFRONT`), Amazon CloudFront.

**Architecture Decision:**
1. Create the WebACL in **us-east-1** with scope `CLOUDFRONT` (CloudFront WebACLs must be global).
2. Attach AWS Managed Rule Groups: **AWSManagedRulesCommonRuleSet** (Core rule set) and
   **AWSManagedRulesKnownBadInputsRuleSet** as a minimum baseline.
3. Add custom rules as needed (rate limiting, IP reputation, geo blocking).
4. Associate the WebACL ARN to the CloudFront distribution (`WebACLId` field).
5. Confirm WAF rules do **not** block `/.well-known/pki-validation/` (required for certificate
   validation workflows).

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.WebACLId"
# Expected: non-empty ARN — arn:aws:wafv2:us-east-1:ACCOUNT:global/webacl/NAME/ID

# Verify WebACL has at least one rule group
aws wafv2 get-web-acl --scope CLOUDFRONT --region us-east-1 \
  --name "$WEBACL_NAME" --id "$WEBACL_ID" \
  --query "WebACL.Rules[].Name"
```

**Trade-offs:** AWS WAF incurs per-request and per-WCU charges. Managed rules may produce false
positives on first deployment — run in Count mode initially, then switch to Block after tuning.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-aws-waf.html (access 2026-07-31)

---

### Pattern 4: Enable Standard Logging (v2) to Amazon S3 with Lifecycle Policies

**Why:** Provides per-request records for security analysis, troubleshooting, and audit.
**Standard logs are provided free of charge.** Alignment: Operational Excellence pillar.

**AWS Service:** Amazon CloudFront standard logging (v2), Amazon S3 (log delivery target), Amazon
CloudWatch Logs and Amazon Kinesis Data Firehose (alternative v2 destinations).

**Architecture Decision:**
Enable **standard logging v2** on the distribution. Standard logs v2 supports three delivery
targets: Amazon S3, Amazon CloudWatch Logs, and Amazon Kinesis Data Firehose. Legacy standard
logging supports only S3. Apply an S3 **lifecycle policy** on the log bucket to:
- Transition to S3 Standard-IA after 30 days.
- Transition to S3 Glacier Instant Retrieval after 90 days.
- Expire after the retention period required by policy (e.g., 365 or 2555 days).

Note: CloudFront delivers logs on a best-effort basis (not billing-grade counts). Use real-time
logs (see Ask First) where per-request completeness is critical.

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.Logging"
# Expected: Enabled: true with Bucket and Prefix populated (legacy standard logging)
# For standard logs v2, check the logging v2 delivery configuration separately
```

**Trade-offs:** Standard logs are free; S3 storage and CloudWatch Logs ingestion costs apply.
Lifecycle rules mitigate storage cost growth.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html (access 2026-07-31)

---

### Pattern 5: Define an Explicit Cache Policy and Minimal Cache Key

**Why:** Cache-hit ratio, origin load, and viewer latency are all determined by the cache key. A
broad cache key (e.g., including `User-Agent` or session cookies) creates per-user object copies,
collapsing hit ratio. Alignment: Performance Efficiency + Cost Optimization pillars.

**AWS Service:** Amazon CloudFront cache policy (Min/Default/Max TTL, cache key components),
Amazon CloudFront origin request policy (values forwarded to origin but excluded from cache key).

**Architecture Decision:**
- Create a **cache policy** to set `MinTTL`, `DefaultTTL`, and `MaxTTL`.
- Include only the minimum necessary values in the cache key: headers, cookies, and query strings
  that genuinely change the response (e.g., `Accept-Language`, `Accept-Encoding`).
- Values that the origin needs for analytics or routing but that do not change the response content
  belong in an **origin request policy** (forwarded to origin but not part of the cache key).
- Never use legacy `ForwardedValues` in new distributions — use named cache policies instead.

Default CloudFront TTL if `Cache-Control` is absent: 24 hours. Min TTL default: 0.

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.DefaultCacheBehavior.CachePolicyId"
# Expected: a non-null cache policy ID (not using legacy ForwardedValues)

aws cloudfront get-cache-policy --id "$CACHE_POLICY_ID" \
  --query "CachePolicy.CachePolicyConfig.ParametersInCacheKeyAndForwardedToOrigin"
# Review included headers/cookies/querystrings — confirm minimum required
```

**Trade-offs:** Broader cache keys reduce hit ratio and increase origin load. Overly narrow keys
risk serving the wrong response variant to a viewer (e.g., wrong language).

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-the-cache-key.html (access 2026-07-31)

---

### Pattern 6: Configure Custom Error Pages for 4xx/5xx with Error Caching TTL

**Why:** Prevents leaking origin error internals (stack traces, server names) to viewers and reduces
origin load during faults. CloudFront can return a custom page and cache the error response.
Alignment: Reliability + Security pillars.

**AWS Service:** Amazon CloudFront custom error responses (`CustomErrorResponses`).

**Architecture Decision:**
Map each HTTP status code to a custom response page object path and HTTP response code:
- `403` → `/error/403.html` (or `200` with SPA index for OAC-blocked requests)
- `404` → `/error/404.html`
- `500`, `502`, `503`, `504` → `/error/5xx.html`

Set `ErrorCachingMinTTL` per code. Default for unspecified codes is 10 seconds. Combine with
origin failover (origin groups) so that primary origin errors also surface a controlled page.

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.CustomErrorResponses"
# Expected: Items array with entries mapping error codes to response page paths and ErrorCachingMinTTL
```

**Trade-offs:** An overly long `ErrorCachingMinTTL` can prolong a stale error state after the
origin recovers. Set a short TTL (30–60s) unless you specifically need longer caching.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html (custom error pages with origin failover) (access 2026-07-31)

---

### Pattern 7: Configure Origin Groups (Primary + Secondary) for Critical Workloads

**Why:** High availability — CloudFront automatically routes to the secondary origin when the
primary returns a configured failover status code or is unreachable. Alignment: Reliability pillar.

**AWS Service:** Amazon CloudFront origin groups.

**Architecture Decision:**
1. Create an origin group with a **primary** and **secondary** origin.
2. Select failover status codes from `{400, 403, 404, 416, 429, 500, 502, 503, 504}`.
3. Reference the origin group ID in the cache behavior (`TargetOriginId`).
4. Tune per-origin connection timeout (1–10s), connection attempts (1–3), and response
   timeout (1–120s) to control how quickly failover is triggered.

Constraints: Failover applies only to `GET`, `HEAD`, and `OPTIONS` viewer methods
(`OPTIONS` must be in cached methods). Lambda@Edge origin triggers may fire twice
(once for primary, once for secondary).

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.OriginGroups"
# Expected: Quantity >= 1; Items[] with Members listing primary and secondary origins + StatusCodes
```

**Trade-offs:** Failover adds one additional origin fetch per failed primary request (latency spike
on the failure path). Lambda@Edge origin-trigger invocation doubles on failover events.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html (access 2026-07-31)

---

### Pattern 8: Enable Origin Shield for High-Cache-Hit or Multi-Region Origins

**Why:** Origin Shield adds a dedicated caching layer between the regional edge caches and the
origin, consolidating all cache misses through one Region. Reduces origin load, lowers latency on
cache miss, and improves cache-hit ratio for globally distributed viewers.
Alignment: Performance Efficiency + Reliability + Cost Optimization pillars.

**AWS Service:** Amazon CloudFront Origin Shield (per-origin property).

**Architecture Decision:**
Enable Origin Shield on each origin that benefits:
- **Best for:** Globally distributed viewers, just-in-time media packaging, capacity-limited
  on-premises origins, multi-CDN architectures.
- **Not for:** Low-cacheability dynamic content, gRPC origins (gRPC requests bypass the shield).

Choose the `OriginShieldRegion` as the AWS Region with lowest latency to the origin. Origin Shield
is available only in Regions that host a regional edge cache (e.g., `us-east-1`, `us-west-2`,
`eu-west-1`, `ap-northeast-1`). Origin Shield is compatible with origin groups — each origin in
the group gets its own shield configuration.

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.Origins.Items[].{Origin:DomainName,Shield:OriginShield}"
# Expected: { "Enabled": true, "OriginShieldRegion": "<region>" } for applicable origins
```

**Trade-offs:** Incremental per-request charges for Origin Shield traffic. For origins with
predominantly dynamic, non-cacheable content, the benefit does not offset the cost.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html (access 2026-07-31)

---

### Pattern 9: Apply Geo-Restriction Where Content Rights Require It

**Why:** Enforces content licensing, regulatory, and distribution-rights boundaries at the edge.
Blocked requests never reach the origin. Alignment: Security + Compliance.

**AWS Service:** Amazon CloudFront geographic restrictions (country-level allowlist or blocklist).

**Architecture Decision:**
Use the built-in allowlist (`whitelist`) or blocklist (`blacklist`) of ISO 3166-1 alpha-2 country
codes. Blocked viewers receive `403 Forbidden`. Geo-restriction applies to the **entire
distribution** — you cannot apply different country rules per cache behavior with the built-in feature.

For finer granularity:
- **Per path or city/postal/lat-long**: Use **AWS WAF geo match** rule conditions (requires WebACL attached).
- **Token-based per-viewer**: Use signed URLs with custom policy geo conditions.

Do not configure geo-restriction rules that accidentally block `/.well-known/pki-validation/` paths
(needed for certificate validation).

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.Restrictions.GeoRestriction"
# Expected: RestrictionType of "whitelist" or "blacklist" with Quantity and country codes in Items
```

**Trade-offs:** IP-to-country accuracy is approximately 99.8%. Country-level only; applies
distribution-wide, so per-path geo rules require WAF or signed URLs.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html (access 2026-07-31)

---

### Pattern 10: Use OAC to Lock Down Amazon S3 Origins (Never Leave the Bucket Public)

**Why:** Ensures viewers can only reach S3 content through CloudFront — WAF, signed URLs, and
logging are applied. A public bucket allows direct S3 access, bypassing all CloudFront controls.
Alignment: Security pillar.

**AWS Service:** CloudFront Origin Access Control (OAC), Amazon S3 bucket policy, AWS KMS (if SSE-KMS).

**Architecture Decision:**
1. Create an OAC with `SigningBehavior: always` (SigV4 signing on every request).
2. Set S3 **Object Ownership** to **Bucket owner enforced** (ACLs disabled).
3. Enable all four **Block Public Access** settings on the bucket.
4. Grant the bucket policy statement: `s3:GetObject` to `Principal: { Service: cloudfront.amazonaws.com }`
   with `Condition: { StringEquals: { "AWS:SourceArn": "arn:aws:cloudfront::ACCOUNT:distribution/DIST_ID" } }`.
5. For **SSE-KMS** objects: add a KMS key-policy statement granting `kms:Decrypt` and
   `kms:GenerateDataKey*` to the CloudFront distribution's service principal.

Constraints: Requires a **regular S3 bucket** (REST endpoint). S3 website endpoints are custom
origins and cannot use OAC.

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.Origins.Items[].OriginAccessControlId"
# Expected: non-empty OAC ID

aws s3api get-bucket-policy-status --bucket "$BUCKET_NAME"
# Expected: IsPublic: false

aws s3api get-public-access-block --bucket "$BUCKET_NAME"
# Expected: all four settings = true
```

**Trade-offs:** Requires bucket-policy management (and optional KMS-policy management). Regular S3
bucket only — S3 website endpoints with server-side redirects need custom origin (OAC cannot be used).

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (access 2026-07-31)

---

### Pattern 11: Use Trusted Key Groups for Signed URLs / Signed Cookies on Private Content

**Why:** Restricts access to paid or sensitive content; adds expiry control and per-viewer
scoping. AWS recommends trusted key groups over the legacy trusted-signer model (AWS-account root
CloudFront key pairs). Alignment: Security pillar.

**AWS Service:** Amazon CloudFront signed URLs / signed cookies with trusted key groups.

**Architecture Decision:**
- Create a **CloudFront public key** (upload your RSA-2048 public key PEM).
- Create a **key group** referencing one or more public keys.
- Set `TrustedKeyGroups` on the applicable cache behavior(s) with `Enabled: true`.
- **Signed URLs**: one URL per object; client follows the signed URL directly. Preferred when:
  a client cannot store cookies, or access is to individual files.
- **Signed cookies**: cover multiple files under a path pattern without changing URLs. Preferred
  when existing bookmarks/URLs must remain valid.
- Pair with OAC (Pattern 10) so the origin cannot be reached directly.
- Store the private signing key in AWS Secrets Manager or AWS KMS — never in source control.

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.DefaultCacheBehavior.TrustedKeyGroups"
# Expected: Enabled: true with one or more key group IDs

aws cloudfront list-key-groups --query "KeyGroupList.Items[].KeyGroup.KeyGroupConfig.{Name:Name,Keys:Items}"
```

**Trade-offs:** Application must generate and sign tokens at request time. Keys must be rotated
regularly (see Pattern 14 / Never-Do 7). Signed-URL/cookie generation adds application complexity.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PrivateContent.html (access 2026-07-31)

---

### Pattern 12: Use Field-Level Encryption for Sensitive POST Fields

**Why:** Encrypts designated POST body fields at the edge, as close to the viewer as possible.
Plaintext never traverses the application layer — only components with the corresponding private
key can decrypt. Alignment: Security + Compliance pillars (PII, payment card data).

**AWS Service:** Amazon CloudFront field-level encryption (asymmetric RSA-2048), AWS Encryption SDK (at origin).

**Architecture Decision:**
1. Upload an RSA-2048 **public key** to CloudFront (same public-key object as Pattern 11, or separate).
2. Create a **field-level encryption profile** listing the fields to encrypt (e.g., `card_number`, `ssn`).
3. Create a **field-level encryption configuration** referencing the profile and specifying the
   `ContentTypeProfileConfig` for `application/x-www-form-urlencoded`.
4. Attach the FLE configuration ID to the applicable cache behavior via `FieldLevelEncryptionId`.
5. The origin must use the **AWS Encryption SDK** to decrypt the encrypted field values using
   the corresponding private RSA key.

Constraints: `application/x-www-form-urlencoded` POST bodies only; maximum 10 fields per request;
maximum 10 FLE configurations per account. Requires `ViewerProtocolPolicy: https-only`,
POST/PUT methods allowed, and `OriginProtocolPolicy: match-viewer` or `https-only`.

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.DefaultCacheBehavior.FieldLevelEncryptionId"
# Expected: non-empty FLE configuration ID

aws cloudfront list-field-level-encryption-configs \
  --query "FieldLevelEncryptionList.Items[].{Id:Id,Comment:Comment}"
```

**Trade-offs:** Origin integration requires the AWS Encryption SDK; adds development overhead. Hard
limits of 10 fields and 10 FLE configs per account; only works with form-encoded bodies.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/field-level-encryption.html (access 2026-07-31)

---

### Pattern 13: Choose Price Class Matching Actual Viewer Geography

**Why:** CloudFront edge-location DTO and request charges vary by geographic Region. Serving all
Regions when viewers are concentrated in a subset wastes cost with no performance benefit to your
audience. Alignment: Cost Optimization pillar.

**AWS Service:** Amazon CloudFront price class (`PriceClass_All`, `PriceClass_200`, `PriceClass_100`).

**Architecture Decision:**
- **`PriceClass_All`** — all CloudFront edge locations globally; best performance for global
  audiences; highest cost.
- **`PriceClass_200`** — all Regions except the most expensive (excludes some of South America,
  Australia/New Zealand); balances coverage and cost.
- **`PriceClass_100`** — North America, Europe, and Israel only; lowest cost; increases latency
  for viewers in excluded Regions (they are served from the nearest included edge).

Base the selection on real viewer geography data (e.g., CloudWatch metrics, server access logs)
rather than defaulting to `PriceClass_All`.

Data transfer from AWS origins (Amazon S3, Amazon Elastic Load Balancing, Amazon API Gateway) to
CloudFront is **free of charge** regardless of price class.

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.PriceClass"
# Expected: "PriceClass_All", "PriceClass_200", or "PriceClass_100"
```

**Trade-offs:** Lower price classes increase latency for viewers in excluded Regions (they are
routed to the nearest edge in an included Region). Precise edge-location membership per class
changes over time — confirm on https://aws.amazon.com/cloudfront/pricing/ at design time.

**Source:** https://aws.amazon.com/cloudfront/pricing/ (PriceClass topic redirects here); https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html (free DTO from AWS origins) (access 2026-07-31)

---

### Pattern 14: Right-Size Edge Compute — CloudFront Functions for Lightweight, Lambda@Edge for Heavy Logic

**Why:** Edge functions execute on every matched request. Choosing the heavier runtime for simple
tasks adds latency and cost; choosing the lighter runtime for tasks requiring network access or
SDK calls will fail. Alignment: Performance Efficiency + Cost Optimization pillars.

**AWS Service:** CloudFront Functions (JavaScript, viewer event only), AWS Lambda@Edge (Node.js / Python,
viewer and origin events).

**Architecture Decision:**

| Requirement | Use |
|---|---|
| Cache-key normalization | **CloudFront Functions** |
| URL rewrite / redirect | **CloudFront Functions** |
| Simple header manipulation | **CloudFront Functions** |
| Simple token / JWT validation (no network call) | **CloudFront Functions** |
| Network access (external API, DynamoDB) | **AWS Lambda@Edge** |
| AWS SDK calls | **AWS Lambda@Edge** |
| Third-party library usage | **AWS Lambda@Edge** |
| Request body inspection or modification | **AWS Lambda@Edge** |
| Memory > 2 MB or runtime > 2s | **AWS Lambda@Edge** |

CloudFront Functions run at viewer request and viewer response events only; sub-millisecond
execution; 10 KB package limit; no network/filesystem access.

Lambda@Edge runs at viewer request, viewer response, origin request, and origin response events;
up to 30s timeout at origin events; up to 128–3,008 MB memory; full Node.js or Python runtime.

**Verification:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.DefaultCacheBehavior.FunctionAssociations"
# CloudFront Functions associations

aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.DefaultCacheBehavior.LambdaFunctionAssociations"
# Lambda@Edge associations — verify EventType matches the function's capability
```

**Trade-offs:** CloudFront Functions cannot perform network or filesystem access; Lambda@Edge costs
more and has per-Region scaling limits (~10,000 req/s) vs CloudFront Functions (millions req/s).
Lambda@Edge functions are replicated to edge Regions — changes propagate globally and can take
several minutes.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html (access 2026-07-31)
