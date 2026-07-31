# Integration Patterns — Amazon CloudFront

> Full configuration details and troubleshooting for key CloudFront integrations.
> All AWS entries verified against the Amazon CloudFront Developer Guide (access 2026-07-31).
> Non-AWS columns in the Equivalence Map are provider approximations — verify against
> each provider's current docs before design decisions.

---

## Pattern 1: CloudFront + Amazon S3 (Static Site / OAC)

**Use case:** Serve a React SPA, static website, or media assets from Amazon S3 — privately,
through CloudFront only.

### Architecture

```
Viewer → CloudFront (HTTPS) → OAC (SigV4) → Amazon S3 (private bucket, Block Public Access on)
```

### Key Configuration

```yaml
# CloudFront Origin
Origins:
  - DomainName: BUCKET.s3.REGION.amazonaws.com          # REST endpoint (not website endpoint)
    S3OriginConfig:
      OriginAccessIdentity: ""                            # empty — OAC replaces OAI
    OriginAccessControlId: OAC_ID

# CloudFront Distribution
DefaultRootObject: index.html
DefaultCacheBehavior:
  ViewerProtocolPolicy: redirect-to-https
  CachePolicyId: <Managed-CachingOptimized>               # or custom policy

# Custom error page for SPA routing (redirect 404 back to index.html)
CustomErrorResponses:
  - ErrorCode: 403
    ResponsePagePath: /index.html
    ResponseCode: 200
    ErrorCachingMinTTL: 10
  - ErrorCode: 404
    ResponsePagePath: /index.html
    ResponseCode: 200
    ErrorCachingMinTTL: 10
```

```json
// Amazon S3 bucket policy
{
  "Effect": "Allow",
  "Principal": { "Service": "cloudfront.amazonaws.com" },
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::BUCKET/*",
  "Condition": {
    "StringEquals": {
      "AWS:SourceArn": "arn:aws:cloudfront::ACCOUNT:distribution/DIST_ID"
    }
  }
}
```

### SSE-KMS Extension

Add to the KMS key policy:
```json
{
  "Effect": "Allow",
  "Principal": { "Service": "cloudfront.amazonaws.com" },
  "Action": ["kms:Decrypt", "kms:GenerateDataKey*"],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "AWS:SourceArn": "arn:aws:cloudfront::ACCOUNT:distribution/DIST_ID"
    }
  }
}
```

### Common Troubleshooting

- **403 on every object** → OAC not attached or bucket policy missing/incorrect `AWS:SourceArn` condition.
- **403 on SSE-KMS objects only** → KMS key policy missing CloudFront service principal grant.
- **SPA routing 404** → Add custom error responses mapping 403/404 → `index.html` with HTTP 200.
- **S3 website redirect not working** → Website endpoint requires custom origin (not S3 origin); OAC cannot be used; use a signed URL approach or CloudFront Functions redirect instead.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html (access 2026-07-31)

---

## Pattern 2: CloudFront + Amazon API Gateway / Application Load Balancer (ALB)

**Use case:** Accelerate and protect a REST API or dynamic web application behind API Gateway or ALB.

### Architecture

```
Viewer → CloudFront (HTTPS + WAF) → Custom HTTP Origin → Amazon API Gateway / ALB → Backend
```

### Key Configuration

```yaml
# CloudFront Origin
Origins:
  - DomainName: API_ID.execute-api.REGION.amazonaws.com   # API Gateway
    CustomOriginConfig:
      OriginProtocolPolicy: https-only
      HTTPSPort: 443
    OriginCustomHeaders:
      - HeaderName: x-origin-verify
        HeaderValue: SECRET_VALUE                           # Shared secret for WAF/origin auth

DefaultCacheBehavior:
  ViewerProtocolPolicy: https-only
  CachePolicyId: <Managed-CachingDisabled>                 # Dynamic APIs usually non-cacheable
  OriginRequestPolicyId: <Managed-AllViewer>               # Forward all headers to origin
  AllowedMethods: [GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE]

# For ALB: restrict direct access to ALB at the load balancer security group
# Allow only CloudFront managed prefix list (com.amazonaws.global.cloudfront.origin-facing)
```

### Caching Selective Endpoints

Not all API paths are dynamic. Reduce origin load for cacheable endpoints:

```yaml
CacheBehaviors:
  - PathPattern: /api/static/*
    CachePolicyId: <custom-policy with 5 min TTL>
  - PathPattern: /api/user/*
    CachePolicyId: <Managed-CachingDisabled>    # per-user, non-cacheable
```

### Common Troubleshooting

- **502 Bad Gateway** → CloudFront cannot reach the origin; check Security Group rules for ALB (add CloudFront prefix list), or check API Gateway endpoint URL.
- **Requests missing expected headers** → Verify origin request policy includes the required headers.
- **CORS errors** → Include `Origin` header in both cache key and origin request policy; configure API to respond with specific `Access-Control-Allow-Origin` (not `*` for credentialed requests).

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html (access 2026-07-31)

---

## Pattern 3: CloudFront + Lambda@Edge / CloudFront Functions

**Use case:** Execute code at the edge — URL normalization, auth token validation, A/B testing,
dynamic header injection, or request modification.

### Selection Guide

| Task | Runtime | Event |
|---|---|---|
| Normalize URL / remove trailing slash | **CloudFront Functions** | viewer-request |
| Redirect HTTP to HTTPS (if not using `redirect-to-https`) | **CloudFront Functions** | viewer-request |
| Add security headers (HSTS, CSP, X-Frame-Options) | **CloudFront Functions** | viewer-response |
| Simple JWT validation (no network) | **CloudFront Functions** | viewer-request |
| Validate auth token against DynamoDB / external API | **AWS Lambda@Edge** | viewer-request or origin-request |
| A/B testing with weighted cookie | **AWS Lambda@Edge** | viewer-request |
| Generate presigned S3 URL dynamically | **AWS Lambda@Edge** | origin-request |
| Resize images on cache miss | **AWS Lambda@Edge** | origin-response |

### CloudFront Functions Example (add security headers)

```javascript
// Runs at viewer-response — sub-millisecond
function handler(event) {
  var response = event.response;
  var headers = response.headers;
  headers['strict-transport-security'] = { value: 'max-age=63072000; includeSubdomains; preload' };
  headers['x-content-type-options'] = { value: 'nosniff' };
  headers['x-frame-options'] = { value: 'DENY' };
  return response;
}
```

### Lambda@Edge Constraints

- Functions must be deployed in **us-east-1** and are replicated globally by CloudFront.
- Maximum execution timeout: **5s** (viewer events), **30s** (origin events).
- No Lambda layers, no EFS mounts, no VPC (Lambda@Edge runs outside VPC).
- Changes propagate globally — allow several minutes for full propagation.

### Common Troubleshooting

- **CloudFront Functions size error** → Package > 10 KB; move logic to Lambda@Edge.
- **Lambda@Edge `AccessDeniedException`** → Lambda execution role must trust `edgelambda.amazonaws.com` AND `lambda.amazonaws.com`.
- **Lambda@Edge not invoked** → Check event type (`viewer-request` vs `origin-request`); confirm function association is on the correct cache behavior.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html (access 2026-07-31)

---

## Pattern 4: CloudFront + AWS WAF v2 + Shield Advanced

**Use case:** Comprehensive edge security for public-facing distributions — L7 filtering,
DDoS protection, and operational response team access.

### Architecture

```
Viewer → CloudFront → AWS WAF (CLOUDFRONT scope, us-east-1) → Origin
                    ↑
               Shield Advanced (wraps CloudFront distribution)
```

### AWS WAF Configuration Essentials

```yaml
# WebACL must be created in us-east-1 with scope CLOUDFRONT
WebACL:
  Scope: CLOUDFRONT
  Rules:
    - Name: AWSManagedRulesCommonRuleSet      # OWASP Top 10 mitigations
      Priority: 1
    - Name: AWSManagedRulesKnownBadInputsRuleSet
      Priority: 2
    - Name: AWSManagedRulesAmazonIpReputationList  # Known bad IPs / bots
      Priority: 3
    - Name: RateLimit-per-IP                   # Custom rule: 2000 req/5min per IP
      Priority: 10
      Action: Block
```

**Do not block** `/.well-known/pki-validation/` — needed for ACM certificate validation.

### Shield Advanced Enrollment

Shield Advanced protects the CloudFront distribution (as a resource type `AWS::CloudFront::Distribution`).
Benefits over Shield Standard (included free):
- DDoS response team (DRT) access during active events.
- Automatic application-layer DDoS mitigation (WAF rule auto-deployment during attacks).
- Cost protection for scaling during volumetric attacks.
- Enhanced CloudWatch metrics for DDoS visibility.

```bash
# Enable Shield Advanced on a CloudFront distribution
aws shield create-protection \
  --name "my-cloudfront-protection" \
  --resource-arn "arn:aws:cloudfront::ACCOUNT:distribution/DIST_ID"
```

**Note:** Shield Advanced requires a subscription (additional charge) and is associated at the AWS
account or Organization level. Verify pricing and coverage with AWS before enrolling.

### Common Troubleshooting

- **WAF blocking legitimate traffic** → Switch rules from Block to Count mode; review WAF sampled requests; add IP set or regex pattern exceptions.
- **WAF not blocking attacks** → Confirm WebACL is correctly associated to the distribution (`WebACLId` in distribution config is non-empty).
- **`/.well-known/` blocked** → Add an explicit Allow rule at high priority for the path before managed rules.

**Source (WAF):** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-aws-waf.html (access 2026-07-31)

---

## Pattern 5: CloudFront + AWS Certificate Manager (ACM)

**Use case:** Serve CloudFront distributions over HTTPS with a custom domain (e.g., `cdn.example.com`).

### Key Requirements

- ACM certificate **must be in the `us-east-1` Region** — CloudFront is a global service and only
  reads certificates from us-east-1.
- The certificate must cover all CNAMEs (aliases) configured on the distribution.
- ACM certificates for CloudFront must use **SNI** (Server Name Indication) — not dedicated IP.

### Configuration Flow

```
1. Request certificate in ACM (us-east-1):
   aws acm request-certificate \
     --domain-name cdn.example.com \
     --validation-method DNS \
     --region us-east-1

2. Add the CNAME validation record to DNS (Route 53 or external).
3. Wait for ACM to issue the certificate (Status: ISSUED).

4. Reference in CloudFront distribution:
   ViewerCertificate:
     ACMCertificateArn: arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT_ID
     MinimumProtocolVersion: TLSv1.2_2021
     SSLSupportMethod: sni-only

5. Add the CloudFront distribution domain as a CNAME alias on the distribution.
6. Create DNS record pointing custom domain → CloudFront domain:
   cdn.example.com CNAME d1234567890.cloudfront.net
   (or Route 53 Alias record)
```

### ACM Auto-Renewal

ACM auto-renews managed certificates before expiry. For DNS validation, the CNAME record must
remain in DNS permanently — removing it breaks renewal. For email validation, the domain owner
receives renewal emails.

### Common Troubleshooting

- **Certificate not appearing in CloudFront console** → Certificate must be in `us-east-1`; if in another Region, it will not appear.
- **SSL handshake failure** → Certificate SAN does not match the request's `Host` header / CNAME; verify all distribution aliases are covered.
- **Certificate renewal failure** → DNS CNAME validation record was removed; re-add it.

**Source:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https-viewers-to-cloudfront.html ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html (access 2026-07-31)

---

## Pattern 6: CloudFront + Amazon Route 53 (Latency Routing + Health Checks)

**Use case:** Custom domain routing to CloudFront with latency-based records or failover.

### Alias Records (Recommended)

Route 53 Alias records point directly to CloudFront distribution domains without a CNAME hop:

```
cdn.example.com  A/AAAA  ALIAS  d1234567890.cloudfront.net
                          (Evaluate Target Health: optional)
```

Alias records are free (no per-query charge for Route 53 Alias to CloudFront) and support apex
domains (e.g., `example.com` directly).

### Multi-Distribution Latency Routing

When running multiple CloudFront distributions per region (e.g., for different origin locations),
use Route 53 latency records to route viewers to the distribution with lowest measured latency:

```
cdn.example.com  A  LATENCY  d1111111111.cloudfront.net  (us-east-1)
cdn.example.com  A  LATENCY  d2222222222.cloudfront.net  (eu-west-1)
```

### DNS-Level Failover with Health Checks

Route 53 health checks can evaluate an HTTP/HTTPS endpoint (e.g., a CloudFront distribution health
path) and trigger DNS-level failover to a secondary distribution:

```
Primary:   cdn.example.com  FAILOVER PRIMARY   d1111111111.cloudfront.net  (health check attached)
Secondary: cdn.example.com  FAILOVER SECONDARY d2222222222.cloudfront.net
```

**Note:** CloudFront distributions do not have per-AZ IPs — Route 53 health checks for CloudFront
should target the distribution domain and a meaningful health endpoint (e.g., `/health`). Combine
with CloudFront origin groups for faster in-CDN failover (origin groups fail over within seconds,
Route 53 DNS failover within the TTL of the health check interval + propagation).

### Common Troubleshooting

- **Apex domain not resolving** → Use Route 53 Alias records, not CNAME (CNAME at apex violates DNS spec).
- **Distribution domain not available in alias target** → Distribution must be deployed (Status: Deployed) and have at least one CNAME alias configured.

**Note:** Route 53 integration details are not covered in the CloudFront research bibliography.
Validate current Route 53 behavior against: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/ before finalizing.

---

## Service Equivalence Map — Multi-Cloud CDN and Edge Security

> AWS entries verified against the Amazon CloudFront Developer Guide (access 2026-07-31).
> Non-AWS columns are provider-mapping approximations — marked `[verify per provider]`.
> Do not use non-AWS entries as design decisions without validating against each provider's current docs.

| Capability | AWS (verified) | Azure `[verify]` | GCP `[verify]` | OCI `[verify]` |
|---|---|---|---|---|
| CDN / edge delivery | **Amazon CloudFront** | Azure Front Door / Azure CDN | Cloud CDN (with external Application Load Balancer) | OCI Content Delivery Network (CDN) |
| Edge WAF | **AWS WAF** WebACL (`CLOUDFRONT` scope) | Azure WAF on Front Door | Google Cloud Armor | OCI Web Application Firewall (WAF) |
| Origin access lockdown (object store) | **OAC** for **Amazon S3** | Private Link / Front Door origin auth → Azure Blob Storage | Signed URLs / IAM for Cloud Storage | Pre-authenticated / private OCI Object Storage |
| Edge compute (lightweight, sub-ms) | **CloudFront Functions** (JavaScript) | Front Door Rules Engine | (limited edge rules) | (rules-based routing) |
| Edge compute (heavy, regional) | **AWS Lambda@Edge** | Azure Functions (regional) | Cloud Functions / Cloud Run (regional) | OCI Functions (regional) |
| Managed TLS certificates | **AWS Certificate Manager (ACM)** | Azure-managed certs on Front Door | Google-managed SSL certificates | OCI Certificates |
| Signed / tokenized private content | Signed URLs / signed cookies (**trusted key groups**) | Front Door token auth / SAS on Blob | Signed URLs (Cloud CDN) | CDN token authentication |
| Origin failover / HA | **Origin groups** (primary + secondary) | Front Door origin groups + health probes | Backend service failover / health checks | Origin failover configuration |
| Geo-restriction | CloudFront geo-restriction (country) + **AWS WAF** geo match | Front Door geo-filtering / WAF geomatch | Cloud Armor region rules | WAF geo rules |
| Real-time logs | Real-time logs → **Amazon Kinesis Data Streams** | Front Door diagnostic logs → Log Analytics / Event Hubs | Cloud CDN logs → Cloud Logging | OCI Logging |
| DDoS baseline (included) | **AWS Shield Standard** (edge, included at no charge) | Azure DDoS Protection | Cloud Armor / Google front-end | OCI DDoS protection |
| DDoS advanced (paid) | **AWS Shield Advanced** (subscription) | Azure DDoS Network Protection | Cloud Armor Managed Protection Plus | OCI DDoS Advanced |

**AWS column sources:** https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html ; .../distribution-web-aws-waf.html ; .../private-content-restricting-access-to-s3.html ; .../high_availability_origin_failover.html ; .../georestrictions.html ; .../PrivateContent.html (all access 2026-07-31)
