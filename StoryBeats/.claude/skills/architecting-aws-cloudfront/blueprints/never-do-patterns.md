# Never-Do Patterns — Amazon CloudFront

> 7 critical anti-patterns. Each entry shows ❌ Wrong and ✅ Correct with exact AWS service names,
> risk level, blast radius, detection command, and real-world impact.
> All sources accessed 2026-07-31.

---

## Anti-Pattern 1: Allowing HTTP-Only Viewer Connections

**Risk Level:** CRITICAL  
**Blast Radius:** All viewers of the affected cache behavior(s) — potentially every user of the distribution.

❌ **Wrong:**
```
Amazon CloudFront cache behavior:
  ViewerProtocolPolicy: allow-all
```
HTTP requests are served as-is over cleartext. Data (credentials, tokens, PII, session cookies)
is transmitted unencrypted between the viewer and the nearest CloudFront edge location.

✅ **Correct:**
```
Amazon CloudFront cache behavior:
  ViewerProtocolPolicy: redirect-to-https   # 301/307 redirect HTTP → HTTPS

AWS Certificate Manager (ACM) — certificate in us-east-1:
  ViewerCertificate:
    ACMCertificateArn: arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT_ID
    MinimumProtocolVersion: TLSv1.2_2021
    SSLSupportMethod: sni-only
```
All viewer connections negotiated over TLS; HTTP requests redirected before any data is transmitted.

**Detection:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.[DefaultCacheBehavior,CacheBehaviors.Items[]][].ViewerProtocolPolicy" \
  --output text
# Flag any output containing "allow-all"
```

**Impact:** Data breach / credential theft / session hijacking / man-in-the-middle attack.
Non-compliance with PCI DSS, HIPAA, and most enterprise security standards.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https-viewers-to-cloudfront.html (access 2026-07-31)

---

## Anti-Pattern 2: Public-Facing Distribution with No AWS WAF WebACL

**Risk Level:** HIGH  
**Blast Radius:** Entire distribution and its origin — all endpoints and all objects served.

❌ **Wrong:**
```
Amazon CloudFront distribution:
  WebACLId: ""   # empty — no WAF filtering
```
Every request from the internet reaches the origin without L7 inspection. SQLi, XSS, bad bots,
credential stuffing, and HTTP floods hit the origin directly.

✅ **Correct:**
```
AWS WAF WebACL (scope: CLOUDFRONT, Region: us-east-1):
  Rules:
    - AWSManagedRulesCommonRuleSet        # Core rule set (OWASP Top 10)
    - AWSManagedRulesKnownBadInputsRuleSet
    - (custom rate-limit rule)

Amazon CloudFront distribution:
  WebACLId: arn:aws:wafv2:us-east-1:ACCOUNT:global/webacl/NAME/ID
```
WAF inspects and filters requests at the edge before they consume origin capacity.

**Detection:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.WebACLId"
# Empty string or null = finding
```

**Impact:** Application compromise, SQL injection / XSS exploitation, data exfiltration, origin
overload / availability impact. WAF cost is low compared to a breach response.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-aws-waf.html (access 2026-07-31)

---

## Anti-Pattern 3: Caching CORS or Authenticated Responses Without Cache-Key Awareness

**Risk Level:** HIGH  
**Blast Radius:** All viewers sharing the cached edge object — can be thousands of users simultaneously.

❌ **Wrong:**
```
Amazon CloudFront cache policy:
  HeadersConfig:
    HeaderBehavior: none   # Origin header not in cache key

Origin response includes:
  Access-Control-Allow-Origin: *       # or per-user body
  Cache-Control: max-age=3600
```
CloudFront caches the response without the `Origin` (or `Authorization`) header in the cache key.
The first cached response — which may contain `Access-Control-Allow-Origin: *` or a specific user's
data — is served to all subsequent viewers.

✅ **Correct — Option A (CORS with varying Access-Control-Allow-Origin):**
```
Amazon CloudFront cache policy:
  HeadersConfig:
    HeaderBehavior: whitelist
    Headers: [Origin]    # Include Origin in cache key so each requesting origin gets its own cache entry
```

✅ **Correct — Option B (authenticated/user-specific responses, non-cacheable):**
```
Origin response:
  Cache-Control: no-store, private

Amazon CloudFront cache behavior:
  CachePolicyId: <Managed-CachingDisabled policy ID>
  # MinTTL: 0 — object is not cached at the edge
```
Mark user-specific responses as non-cacheable so CloudFront never stores them at the edge.

**Detection:**
```bash
aws cloudfront get-cache-policy --id "$CACHE_POLICY_ID" \
  --query "CachePolicy.CachePolicyConfig.ParametersInCacheKeyAndForwardedToOrigin.HeadersConfig"
# Verify "Origin" and "Authorization" are included in the cache key when responses vary by those values
```

**Impact:** Cross-user data leakage (one user's private body served to others); broken CORS
security boundary (wildcard CORS policy persisted to all origins).

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/understanding-the-cache-key.html (access 2026-07-31)

---

## Anti-Pattern 4: Using Legacy OAI Instead of OAC for a New Amazon S3 Origin

**Risk Level:** MEDIUM  
**Blast Radius:** The S3-backed distribution — SSE-KMS content inaccessible; dynamic operations fail; broken in new Regions.

❌ **Wrong:**
```
Amazon CloudFront origin:
  S3OriginConfig:
    OriginAccessIdentity: origin-access-identity/cloudfront/OAIID

Amazon S3 bucket policy (OAI principal):
  Principal:
    CanonicalUser: OAIID_canonical_user_ID
```
OAI does not support SSE-KMS, PUT/DELETE operations, or Regions launched after January 2023.
Any bucket encrypted with SSE-KMS will return 403 for CloudFront reads.

✅ **Correct:**
```
CloudFront Origin Access Control (OAC):
  SigningBehavior: always
  SigningProtocol: sigv4

Amazon CloudFront origin:
  OriginAccessControlId: OAC_ID
  S3OriginConfig:
    OriginAccessIdentity: ""   # empty — OAC replaces OAI

Amazon S3 bucket policy:
  Principal:
    Service: cloudfront.amazonaws.com
  Condition:
    StringEquals:
      AWS:SourceArn: arn:aws:cloudfront::ACCOUNT:distribution/DIST_ID
```

**Detection:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.Origins.Items[].S3OriginConfig.OriginAccessIdentity"
# Non-empty value on a new or recently migrated origin = finding
```

**Impact:** Blocked SSE-KMS content (403 on every read); dynamic PUT/DELETE operations fail;
distribution breaks if bucket is in a Region launched post-Jan 2023.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (access 2026-07-31)

---

## Anti-Pattern 5: Publicly Readable S3 Bucket Behind CloudFront (Origin Bypass)

**Risk Level:** HIGH  
**Blast Radius:** All objects in the bucket — directly accessible to anyone on the internet via the S3 endpoint URL.

❌ **Wrong:**
```
Amazon S3 bucket:
  BlockPublicAccess: disabled (or partial)
  BucketPolicy: AllowPublicRead (Principal: "*")

Amazon CloudFront origin:
  OriginAccessControlId: ""   # no OAC
```
Viewers — or attackers — can retrieve any object directly from the S3 REST endpoint URL
(`https://BUCKET.s3.REGION.amazonaws.com/KEY`), completely bypassing CloudFront, AWS WAF,
signed URL enforcement, and access logging.

✅ **Correct:**
```
Amazon S3 bucket:
  BlockPublicAccess: all four settings enabled
  ObjectOwnership: BucketOwnerEnforced   # ACLs disabled

CloudFront Origin Access Control (OAC):
  SigningBehavior: always

Amazon S3 bucket policy:
  Effect: Allow
  Principal:
    Service: cloudfront.amazonaws.com
  Action: s3:GetObject
  Resource: arn:aws:s3:::BUCKET/*
  Condition:
    StringEquals:
      AWS:SourceArn: arn:aws:cloudfront::ACCOUNT:distribution/DIST_ID
```

**Detection:**
```bash
aws s3api get-bucket-policy-status --bucket "$BUCKET_NAME"
# Expected: IsPublic: false

aws s3api get-public-access-block --bucket "$BUCKET_NAME"
# Expected: all four settings = true

aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.Origins.Items[?contains(DomainName,'s3')].OriginAccessControlId"
# Expected: non-empty OAC ID for each S3 origin
```

**Impact:** Origin bypass — unlogged, unfiltered, bypasses signed URL restrictions, bypasses WAF,
bypasses CloudFront access control. Potential data exposure to arbitrary internet clients.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (access 2026-07-31)

---

## Anti-Pattern 6: No Origin Failover for a Critical Workload

**Risk Level:** HIGH  
**Blast Radius:** All viewers during an origin outage — 100% of traffic for the affected distribution.

❌ **Wrong:**
```
Amazon CloudFront cache behavior:
  TargetOriginId: primary-origin-only
  # No origin group — single origin
```
Any origin-side failure (5xx, timeout, health check failure) surfaces directly to all viewers as
an error — no automatic recovery path. Recovery requires manual intervention.

✅ **Correct:**
```
Amazon CloudFront origin group:
  Members:
    - OriginId: primary-alb-origin     # ALB or S3 or API GW
    - OriginId: secondary-s3-failover  # static fallback or replica
  FailoverCriteria:
    StatusCodes: [500, 502, 503, 504]

Amazon CloudFront cache behavior:
  TargetOriginId: origin-group-id

Amazon CloudFront custom error responses:
  - ErrorCode: 503
    ResponsePagePath: /maintenance.html
    ResponseCode: 503
    ErrorCachingMinTTL: 30
```
On primary failure, CloudFront automatically retries on the secondary origin for GET/HEAD/OPTIONS
requests without the viewer experiencing an error (or shows a controlled maintenance page).

**Detection:**
```bash
aws cloudfront get-distribution-config --id "$DIST_ID" \
  --query "DistributionConfig.OriginGroups.Quantity"
# 0 on a distribution classified as critical = finding
```

**Impact:** Full service outage for all viewers during any single-origin failure event.
Mean time to recover (MTTR) determined by manual response rather than automatic failover.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html (access 2026-07-31)

---

## Anti-Pattern 7: Neglecting Signed-URL / Signed-Cookie Key Rotation

**Risk Level:** MEDIUM  
**Blast Radius:** All private content protected by the compromised key — potentially the entire paid/private content library.

❌ **Wrong:**
```
CloudFront trusted key group:
  Keys: [public-key-id-created-3-years-ago]
  # Never rotated; private key stored in a shared config file
```
A single, never-rotated signing key in continuous use for years. If the private key is exposed
(source-code leak, employee departure, credential dump), the attacker can generate valid signed
URLs for all private content indefinitely until someone notices and manually rotates.

✅ **Correct — Zero-Downtime Key Rotation Procedure:**
```
Step 1: Generate a new RSA-2048 key pair (keep private key in AWS Secrets Manager or AWS KMS).
Step 2: Upload the new PUBLIC key to CloudFront → get new public-key ID.
Step 3: Add the new public-key ID to the existing trusted key group (group now has 2 keys).
Step 4: Update the signing application to use the new private key for all new signed URLs/cookies.
Step 5: Allow existing signed URLs/cookies signed with the old key to expire (per their expiry).
Step 6: Remove the old public-key ID from the trusted key group once all old tokens are expired.
Step 7: Delete the old public key resource from CloudFront.
```

Additionally: set short expiry windows on signed URLs/cookies (hours, not months) to limit the
blast radius of a key compromise even before rotation is performed.

**Detection:**
```bash
aws cloudfront get-key-group --id "$KEY_GROUP_ID" \
  --query "KeyGroup.KeyGroupConfig.Items"
# Review each key ID

aws cloudfront get-public-key --id "$PUBLIC_KEY_ID" \
  --query "PublicKey.PublicKeyConfig.{Name:Name,CreatedTime:Comment}"
# Check key age against rotation policy (recommended: rotate at least annually)
```

**Impact:** Compromised private key → attacker generates unlimited valid signed URLs for all
protected content until the key is rotated. Revenue loss, content piracy, compliance violation.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PrivateContent.html (access 2026-07-31)
