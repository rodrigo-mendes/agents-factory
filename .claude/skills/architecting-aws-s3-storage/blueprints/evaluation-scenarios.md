# Evaluation Scenarios — architecting-aws-s3-storage

Test scenarios for `/evaluating-skill-scenarios architecting-aws-s3-storage`.

---

## Scenario 1 — Canonical: New S3 Bucket Security Baseline for a Web Application

```json
{
  "skills": ["architecting-aws-s3-storage"],
  "query": "I need to create an S3 bucket to store static frontend assets (HTML, CSS, JS) for a production web application. Walk me through the mandatory security configuration steps.",
  "expected_behavior": [
    "Instructs enabling all four Block Public Access settings at both account and bucket level",
    "Instructs setting default encryption to SSE-KMS with a customer managed key and BucketKeyEnabled=true",
    "Instructs setting ObjectOwnership to BucketOwnerEnforced to disable ACLs",
    "Instructs attaching a bucket policy Deny on aws:SecureTransport: false to enforce TLS",
    "Instructs enabling S3 Versioning and pairing with a non-current version expiration Lifecycle rule",
    "Instructs enabling Server Access Logging to a dedicated log bucket using SSE-S3",
    "Instructs serving assets via CloudFront + OAC rather than from a public S3 endpoint",
    "Mentions OAC as replacement for deprecated OAI",
    "Provides AWS CLI verification commands: get-public-access-block, get-bucket-encryption, get-bucket-policy-status",
    "Does NOT recommend making the bucket public or using the S3 website endpoint for production"
  ]
}
```

---

## Scenario 2 — Canonical: Presigned URL Direct Upload Architecture

```json
{
  "skills": ["architecting-aws-s3-storage"],
  "query": "Users of my web app need to upload profile photos (up to 10 MB) directly to S3. I want to avoid routing the binary through my server. What is the correct architecture?",
  "expected_behavior": [
    "Recommends the presigned PUT URL pattern as the default approach for direct browser-to-S3 uploads",
    "Explains that a Lambda function (behind API Gateway) generates the presigned URL using its IAM execution role — never hardcoded keys",
    "States CORS must be configured on the S3 bucket to allow cross-origin PUT requests from the browser",
    "Warns that the presigned URL is a bearer token — anyone with the URL can upload until expiry",
    "Notes that Content-Type at upload time must match Content-Type at URL generation time to avoid SignatureDoesNotMatch",
    "Mentions S3 Event Notification triggering Lambda for post-upload processing (thumbnail, virus scan)",
    "States max presigned URL duration is 7 days for IAM users, limited to role session duration for assumed roles",
    "Does NOT suggest hardcoding IAM access keys in the frontend or backend application code",
    "Does NOT recommend backend proxy pattern unless pre-upload validation/scanning is explicitly required"
  ]
}
```

---

## Scenario 3 — Edge Case: Multi-Region Deployment with Near-Zero RPO

```json
{
  "skills": ["architecting-aws-s3-storage"],
  "query": "We have users in North America, Europe, and Asia-Pacific. We need a near-zero RPO for S3 data and automatic failover if a region goes down. What architecture should we use?",
  "expected_behavior": [
    "Recommends S3 Cross-Region Replication (CRR) with S3 Replication Time Control (RTC) for a 15-minute SLA-backed RPO",
    "Recommends S3 Multi-Region Access Point (MRAP) as the single global S3 endpoint routing requests to the closest active region",
    "States MRAP does NOT replicate data — CRR must be configured separately",
    "Recommends bi-directional CRR for active-active architectures (configure replication rules on both source and destination)",
    "Warns that CRR does not replicate pre-existing objects — S3 Batch Replication must be run at setup",
    "States versioning must be enabled on both source and destination buckets before CRR can be configured",
    "Mentions MRAP + Global Accelerator charges in addition to S3 and CRR transfer costs",
    "Notes RTC per-object charges apply",
    "Does NOT claim CRR without RTC provides any RPO SLA",
    "Does NOT claim MRAP provides synchronous replication or zero-RPO"
  ]
}
```

---

## Scenario 4 — Misuse Trap: Public Bucket as Direct Asset Origin

```json
{
  "skills": ["architecting-aws-s3-storage"],
  "query": "Setting up CloudFront seems complex. Can I just disable Block Public Access on my S3 bucket and serve static assets directly from a public bucket URL? It's simpler and still HTTPS via the S3 REST endpoint.",
  "expected_behavior": [
    "Explicitly rejects the public bucket approach for production — identifies it as Anti-Pattern 1 (CRITICAL risk)",
    "Explains that disabling Block Public Access violates AWS Security Hub S3.8 and is a regulatory compliance violation for PCI DSS, GDPR, HIPAA",
    "Clarifies that the S3 REST endpoint does support HTTPS, but a public wildcard bucket policy makes all objects accessible to any internet user",
    "Notes that even if intent is to serve only static assets, any future accidental copy of sensitive data into the bucket would be immediately public",
    "Recommends CloudFront + OAC as the correct mechanism: private bucket, HTTPS, custom domain, edge caching, WAF integration",
    "Provides detection guidance: aws s3api get-bucket-policy-status — IsPublic must be false",
    "Does NOT recommend any configuration that requires disabling all four Block Public Access settings in production",
    "Does NOT suggest the S3 website endpoint as an alternative (HTTP-only, no OAC support)"
  ]
}
```

---

## Scenario 5 — Edge Case: Storage Class Selection for a Large Media Archive

```json
{
  "skills": ["architecting-aws-s3-storage"],
  "query": "We store user-uploaded videos in S3. Most videos are accessed frequently in the first 30 days after upload, rarely accessed from 30-90 days, and almost never after 90 days. We have about 500 TB growing by 10 TB/month. What storage classes and Lifecycle rules should we use?",
  "expected_behavior": [
    "Recommends S3 Standard for the first 30 days (active access, no retrieval fee, no minimum duration)",
    "Recommends transitioning to S3 Standard-IA at 30 days for the 30-90 day window (lower cost, retrieval fee acceptable for infrequent access)",
    "Recommends transitioning to S3 Glacier Instant Retrieval at 90 days if occasional real-time access is still needed, or Glacier Flexible Retrieval if access can tolerate minutes-to-hours delay",
    "Notes the 30-day billing minimum for Standard-IA (scheduling minimum removed July 2026; billing minimum still applies)",
    "Notes the 90-day billing minimum for Glacier Instant Retrieval",
    "Asks whether access patterns are truly predictable — if not, suggests S3 Intelligent-Tiering as an alternative with no retrieval fee",
    "Warns that Intelligent-Tiering per-object monitoring fee applies; objects under 128 KB receive no benefit",
    "Recommends configuring non-current version expiration Lifecycle rule if versioning is enabled, to prevent storage cost growth from version accumulation",
    "Does NOT recommend S3 Express One Zone for user-uploaded videos (single AZ, not resilient to AZ failure)",
    "Does NOT mix Glacier Deep Archive into the hot path (hours retrieval not suitable for user-facing access)"
  ]
}
```
