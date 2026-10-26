# Always Do Patterns — delivering-cloudfront-cdn

Full mandatory patterns M1-M7 with verification. Summary in [../SKILL.md](../SKILL.md).
Source: research_cloud_AWS_CloudFront_CDN_2026.md (research date 2026-08-26; official AWS docs accessed 2026-08-26).

---

## M1 — Lock S3 origins with Origin Access Control (OAC)

**Pillar**: Security

OAC keeps the bucket fully private; CloudFront sends SigV4-signed requests. OAC supports all Regions (including opt-in Regions launched after Dec 2022), SSE-KMS and dynamic PUT/DELETE. Legacy OAI does not.

- Create `AWS::CloudFront::OriginAccessControl` with `SigningBehavior: always` and `SigningProtocol: sigv4`.
- Set S3 Object Ownership to **Bucket owner enforced**.
- Enable S3 Block Public Access (all four blocks `true`).
- Bucket policy: grant `cloudfront.amazonaws.com` `s3:GetObject`, scoped by `AWS:SourceArn` = distribution ARN.
- SSE-KMS: add `kms:Decrypt`, `kms:Encrypt`, `kms:GenerateDataKey*` to the key policy with the same `AWS:SourceArn` condition.

**Verification**:
```bash
aws cloudfront get-distribution-config --id <DIST_ID> \
  --query 'DistributionConfig.Origins.Items[].S3OriginConfig.OriginAccessIdentity'
# Expected: [""] (OAI not used); OriginAccessControlId set on the origin
aws s3api get-public-access-block --bucket <BUCKET>
# Expected: all four fields true
```

Source: [Restrict access to an S3 origin](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html) (accessed 2026-08-26)

---

## M2 — Require HTTPS end-to-end with a modern security policy

**Pillar**: Security

- Viewer Protocol Policy `Redirect HTTP to HTTPS` or `HTTPS only` on every cache behavior.
- ACM certificate for custom domains must be in `us-east-1`.
- Security policy `TLSv1.2_2021` minimum; `TLSv1.3_2025` for the strictest posture (quantum-safe key exchange `X25519MLKEM768`, `SecP256r1MLKEM768`; TLS 1.3 only).
- Use SNI (default); dedicated-IP custom SSL only if legacy clients require it.

**Verification**:
```bash
aws cloudfront get-distribution-config --id <DIST_ID> \
  --query 'DistributionConfig.ViewerCertificate.MinimumProtocolVersion'
# Expected: "TLSv1.2_2021" or newer
openssl s_client -connect <domain>:443 -tls1_1 2>&1 | grep "handshake"
# Expected: handshake failure
```

Sources: [Require HTTPS between viewers and CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https-viewers-to-cloudfront.html); [Supported viewer protocols and ciphers](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/secure-connections-supported-viewer-protocols-ciphers.html) (accessed 2026-08-26)

---

## M3 — Attach an AWS WAF web ACL; rely on Shield Standard

**Pillar**: Security / Reliability

- WAFv2 web ACL with `scope: CLOUDFRONT`, created in `us-east-1`.
- Add AWS managed rule groups plus a rate-based rule.
- Associate through the distribution `WebACLId`.
- Shield Standard is automatic and free. Consider Shield Advanced for business-critical workloads (24/7 SRT support, DDoS cost protection).
- Do not let WAF/bot rules block `/.well-known/pki-validation/` (CloudFront managed certificate validation).

**Verification**:
```bash
aws wafv2 get-web-acl-for-resource \
  --resource-arn arn:aws:cloudfront::<ACCOUNT>:distribution/<DIST_ID> \
  --scope CLOUDFRONT --region us-east-1
# Expected: WebACL object returned
```

Source: [AWS WAF + CloudFront](https://docs.aws.amazon.com/waf/latest/developerguide/cloudfront-chapter.html) (accessed 2026-08-26)

---

## M4 — Keep ALB/NLB/EC2 origins private with VPC origins

**Pillar**: Security

- Place ALB/NLB/EC2 in private subnets; create a CloudFront VPC origin.
- Origin security group: allow inbound from the CloudFront managed prefix list, or use the service-managed SG `CloudFront-VPCOrigins-Service-SG`.
- WebSocket supported as of 2026-05-01. No public IP on the origin.
- Known caveats (research): no Gateway Load Balancers, dual-stack NLBs, NLBs with TLS listeners, gRPC, or Lambda@Edge origin triggers.

**Verification**:
```bash
curl --max-time 5 http://<ALB-DNS>
# Expected: connection timeout (origin not reachable directly)
curl --max-time 5 https://<DISTRIBUTION-DOMAIN>/health
# Expected: 200 OK
```

Sources: [VPC origins](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html); [VPC origins announcement, Nov 2024](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-cloudfront-vpc-origins) (accessed 2026-08-26)

---

## M5 — Engineer the cache key with cache policies

**Pillar**: Performance Efficiency / Cost Optimization

- Static assets: AWS managed policy `CachingOptimized`.
- Cache key contains only values that change the response.
- Origin-only values (e.g. `CloudFront-Viewer-Country`) go in an **origin request policy**, which is not part of the cache key.
- Normalize query strings/headers in a CloudFront Function before caching.
- Enable automatic compression (Gzip/Brotli) in the cache policy.
- Optionally centralize security headers (HSTS, X-Content-Type-Options) with a response headers policy.

**Verification**:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront --metric-name CacheHitRate \
  --dimensions Name=DistributionId,Value=<DIST_ID> \
  --start-time <ISO_START> --end-time <ISO_END> \
  --period 3600 --statistics Average
# Expected: > 70% for static assets (tune per workload)
```
Inspect `x-edge-detailed-result-type` in logs: `Hit`, `OriginShieldHit`, `Miss`, `Error`.

Source: [Control the cache key with a policy](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/controlling-the-cache-key.html) (accessed 2026-08-26)

---

## M6 — Serve private content with signed URLs/cookies and trusted key groups

**Pillar**: Security

- Upload a public key (RSA 2048 or ECDSA 256), reference it in a key group on the distribution, sign with the private key in the application.
- Canned policy: single file / expiry only. Custom policy: wildcards, IP restriction, start time.
- Signed cookies: many files without changing URLs.
- Never use root AWS account keys as the signer.

**Verification**: an unsigned request returns HTTP 403; a tampered signature returns 403.

Source: [Signed URLs](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-signed-urls.html) (accessed 2026-08-26)

---

## M7 — Enable logging and monitoring

**Pillar**: Operational Excellence

- Standard access logs (v2, free) to S3, CloudWatch Logs or Firehose.
- Real-time logs only where sub-second visibility is needed (extra cost).
- CloudWatch alarms on `4xxErrorRate`, `5xxErrorRate`, `OriginLatency`, `CacheHitRate`.
- Review WAF/geo 403 spikes manually (`sc-status` 403).

**Verification**: log entries arrive in the configured destination; CloudWatch shows CloudFront metrics for the distribution.

Sources: [Standard logging](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html); [Real-time logs](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/real-time-logs.html) (accessed 2026-08-26)
