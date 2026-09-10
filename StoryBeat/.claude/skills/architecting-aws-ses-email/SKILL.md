---
name: architecting-aws-ses-email
description: "Designs and implements AWS SES email sending architecture with sender authentication, deliverability, reputation management, and IAM least-privilege. Use when building transactional or marketing email pipelines on AWS using Amazon SES API v2 in web application contexts."
---

## Function

Specialist in AWS SES messaging architecture for production web applications: SPF/DKIM/DMARC sender authentication, bounce and complaint reputation management, configuration sets and event-driven observability, IAM execution-role security, and multi-region active-active sending with Global Endpoints.

## Version Context

**Technology**: Amazon Simple Email Service (SES)
**Target edition**: AWS SES 2026 (API v2 — `2019-09-27`)
**Research date**: 2026-08-30
**Currency threshold**: 2027-08-30

**Key changes in 2026**:
- Three-tier pricing model (Essentials / Pro / Enterprise) — GA July 21, 2026
- Automated bot/interaction detection via `isBotEvent` field in Open/Click events — GA August 7, 2026
- VDM inbox placement metrics and blocklist monitoring extended — GA May 29, 2026
- Tenant-level suppression lists with `TenantName` API parameter — GA June 1, 2026
- Mail Manager: Invoke Lambda + Bounce rule actions, mutual TLS ingress — GA April 1, 2026

**Compliance baseline (non-negotiable since 2024–2025)**:
- Gmail + Yahoo: mandatory DKIM alignment, custom MAIL FROM (SPF/DMARC), one-click unsubscribe — enforced since Feb/June 2024
- Microsoft: same requirements for senders >5,000 messages/day to Outlook/Hotmail/live.com — enforced May 5, 2025

**API v1 status**: Not deprecated as of August 2026, but all new features are API v2 exclusive. Email receiving actions (receipt rules) remain API v1 only.

> CRITICAL — Agent Warning: This skill targets AWS SES API v2 (`sesv2` CLI prefix). Reject any patterns using the legacy `ses` CLI prefix for sending unless the pattern is email receiving (receipt rules).

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 operational patterns
- **[Integration Patterns](#integration-patterns)** — async pipeline, event-driven bounce processing
- **[Verification Loop](#verification-loop)** — AWS CLI validation commands
- **[Quick Reference](#quick-reference)** — critical limits and essential commands
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 5 test cases
- **[External Resources](#external-resources)** — official documentation links

---

## Blueprints & Guardrails

### ✅ Always Do

**1. SPF + DKIM + DMARC Sender Authentication** — Required by Gmail, Yahoo, and Microsoft. Failure causes delivery rejection, not spam-folder placement.

- Enable Easy DKIM on domain identity (2048-bit RSA, 3 CNAME records). SES auto-signs all outbound messages.
- Configure a custom MAIL FROM subdomain (e.g., `bounce.example.com`) with SPF TXT `v=spf1 include:amazonses.com ~all` and MX record pointing to `feedback-smtp.<region>.amazonses.com`.
- Publish DMARC TXT at `_dmarc.example.com`, starting at `p=none` with `rua=` reporting; escalate to `p=quarantine` then `p=reject` after validating mail stream coverage.

```bash
# Verify identity authentication status
aws sesv2 get-email-identity --email-identity example.com \
  --query '{DKIM: DkimAttributes.Status, MAILFROM: MailFromAttributes.MailFromDomainStatus}'
# Expected: {"DKIM": "SUCCESS", "MAILFROM": "SUCCESS"}
```

**2. Bounce and Complaint Handling via SNS + Lambda** — Absence of this pipeline is the single most common cause of SES account suspension.

- Attach SNS event destination to each configuration set for `Bounce` and `Complaint` event types.
- Lambda subscriber parses JSON notification and calls `sesv2 put-suppressed-destination` with reason `BOUNCE` or `COMPLAINT`.
- Note: Gmail spam-button reports do NOT appear in SES complaint events — use Gmail Postmaster Tools or VDM Global Deliverability for Gmail-specific signals.

**3. Account-Level Suppression List Enabled** — Prevents charges and reputation damage from repeat sends to known-bad addresses.

```bash
# Confirm suppression list is processing bounces and complaints
aws sesv2 get-account --query 'SuppressionAttributes'
# Expected: {"SuppressedReasons": ["BOUNCE", "COMPLAINT"]}
# If empty (accounts pre-November 25, 2019), enable:
aws sesv2 put-account-suppression-attributes --suppressed-reasons BOUNCE COMPLAINT
```

**4. Configuration Sets on Every Production Send** — Without a configuration set there is no event destination, no IP pool routing, no open/click tracking, and no TLS policy enforcement.

- Create one configuration set per sending use case (e.g., `transactional-config`, `marketing-config`).
- Set as default on each verified identity: `aws sesv2 update-email-identity --email-identity example.com --configuration-set-name transactional-config`
- For SMTP integrations: add `X-SES-CONFIGURATION-SET: transactional-config` header.

**5. Least-Privilege IAM for Sending Roles** — Over-permissioned roles allow deletion of verified identities and configuration sets.

```json
{
  "Effect": "Allow",
  "Action": ["ses:SendEmail", "ses:SendRawEmail"],
  "Resource": "arn:aws:ses:<region>:<account>:identity/<domain>",
  "Condition": {
    "StringEquals": {"ses:FromAddress": "noreply@example.com"}
  }
}
```
Use IAM execution roles (Lambda execution role, ECS task role, EC2 instance profile) — never static access keys for API v2 sends.

**6. Bounce/Complaint Rate CloudWatch Alarms with Circuit Breaker** — SES autonomously pauses accounts that cross thresholds; early alarms enable controlled remediation.

- `Reputation.BounceRate` ≥ 5% → WARNING; ≥ 10% → CRITICAL (pause sending)
- `Reputation.ComplaintRate` ≥ 0.1% → WARNING; ≥ 0.5% → CRITICAL (pause sending)
- CRITICAL alarm action: SNS → Lambda → `aws sesv2 put-account-sending-attributes --sending-enabled false`
- For granular pause: `aws sesv2 put-configuration-set-sending-options --configuration-set-name <name> --sending-enabled false`

---

### ⚠️ Ask First

**Dedicated IP Pool Selection** — Choice depends on volume, sending pattern, and ISP allowlisting requirements.

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Shared IP Pool (default) | Zero extra cost, instant availability | Reputation isolation | Volume < 100K/month, startups |
| Dedicated IP Standard | Static/known IPs, full isolation | Manual warmup burden, per-IP cost | High-volume with ISP allowlisting requirements |
| Dedicated IP Managed | Auto-warmup per ISP, auto-scales | Flat $15/month + $0.08/1K surcharge, IPs not static | Variable high-volume senders |

> Ask: "Does this organization have existing ISP allowlisting for specific IP ranges?" (Standard) · "How predictable is sending volume?" (Managed vs. Standard)

**Multi-Region Sending Strategy** — Global Endpoints require API v2 only; SMTP integrations cannot use MREP.

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Single-region | Simplicity, single suppression list | No HA | Low volume, non-critical |
| Manual multi-region failover | Region redundancy | Split suppression lists, manual runbooks | DR with manual runbooks |
| Global Endpoints (MREP) + DEED | Active-active, auto traffic shift | API v2 only, duplicate config in secondary | HA/DR for transactional email |

> Ask: "Is the application exclusively on SES API v2 (no SMTP)?" · "Does the secondary region have production access and matching quotas?"

**SES API v2 vs. SMTP Interface** — All new integrations should use API v2; SMTP remains valid only for legacy/third-party software.

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| SES API v2 | IAM role auth, CloudTrail data events, Global Endpoints, 40 MB attachments | Requires SDK integration | All new web application integrations |
| SMTP Interface | Drop-in for existing SMTP libraries | Static credentials required, no Global Endpoints, not CloudTrail-logged | Legacy migration, third-party software |

> Ask: "Is an SMTP interface a hard requirement, or is the AWS SDK available in the runtime?"

---

### 🚫 Never Do

| Anti-Pattern | Why | Correct Alternative |
|---|---|---|
| **Embed SES SMTP credentials in application code or environment variables** | SMTP credentials are static, long-lived secrets derived from IAM secret access key. No in-place rotation — rotation requires deleting the IAM SMTP user. | Use SES API v2 with IAM execution role (no static credentials). If SMTP is unavoidable, store credentials in AWS Secrets Manager with a rotation Lambda. |
| **Send without a configuration set** | No event destination → no bounce/complaint feedback → reputation degrades silently until SES suspends the account. | Set a default configuration set on each identity or pass `--configuration-set-name` on every `send-email` call. |
| **Build no bounce/complaint suppression pipeline** | Repeated sends to hard-bounced or complained-about addresses escalate `Reputation.BounceRate` and `Reputation.ComplaintRate` to enforcement thresholds, triggering account suspension. | Configuration Set SNS event destination (Bounce + Complaint) → Lambda → `sesv2 put-suppressed-destination`. |
| **Use `ses:*` wildcard in sending-only IAM roles** | Grants ability to delete verified identities, modify configuration sets, and exfiltrate templates — far beyond send scope. | Scope to `["ses:SendEmail", "ses:SendRawEmail"]` with `Resource` locked to the specific identity ARN and `ses:FromAddress` condition key. |
| **Leave MAIL FROM as the default SES amazonses.com subdomain** | Default MAIL FROM fails DMARC SPF alignment at Gmail, Yahoo, and Microsoft. With `p=reject` DMARC, messages are dropped at destination. | Configure custom MAIL FROM subdomain (e.g., `bounce.example.com`) with SPF TXT and MX records. |

---

## Integration Patterns

**Decoupled Async Send Pipeline**: Application tier → SQS Standard Queue → Lambda (SQS ESM) → SES API v2

- Absorbs SES per-second rate limit bursts without `TooManyRequestsException` propagation to application tier.
- Lambda configuration: `visibility timeout > function timeout`; `ReportBatchItemFailures` for partial-batch response.
- Idempotency: embed a UUID `messageId` in the SQS payload; DynamoDB conditional `PutItem` before each SES call (TTL 24h). For FIFO queues: `MessageDeduplicationId` provides 5-minute deduplication window without DynamoDB.
- DLQ with `maxReceiveCount` 3–5 for persistently failing messages.

**Event-Driven Bounce and Complaint Processing**: Configuration Set → SNS event destination → Lambda → `sesv2 put-suppressed-destination`

- Alternative for analytics: Configuration Set → Kinesis Data Firehose → S3 (buffering 60–900s).
- Alternative for fan-out: Configuration Set → EventBridge → multiple consumers.
- 2026 addition: `isBotEvent` field (`"Likely"` / `"Unlikely"`) automatically included in Open and Click events — filter before recording engagement metrics.
- Gmail blind spot: Gmail spam-button reports NOT surfaced in SES complaint events. Use VDM Global Deliverability or Gmail Postmaster Tools.

**Common Problems**:
- **Problem**: `TooManyRequestsException` on burst sends → **Solution**: Buffer via SQS queue; do not retry synchronously in web request handlers.
- **Problem**: Sandbox silently drops messages to unverified recipients → **Solution**: Request production access at least 3 business days before launch.
- **Problem**: DMARC alignment failure at Gmail/Yahoo despite SPF pass → **Solution**: SPF MAIL FROM must use a custom subdomain aligned with the From: domain; the default `amazonses.com` MAIL FROM fails DMARC SPF alignment.

---

## Verification Loop

Run after configuring SES infrastructure:

### 1. Sender Authentication

```bash
# DKIM and MAIL FROM status
aws sesv2 get-email-identity --email-identity example.com \
  --query '{DKIM: DkimAttributes.Status, MAILFROM: MailFromAttributes.MailFromDomainStatus}'
# Expected: {"DKIM": "SUCCESS", "MAILFROM": "SUCCESS"}

# DMARC DNS record
dig TXT _dmarc.example.com +short
# Expected: "v=DMARC1; p=none; rua=mailto:dmarc@example.com"
```

### 2. Suppression List and Configuration

```bash
# Suppression list active
aws sesv2 get-account --query 'SuppressionAttributes'
# Expected: {"SuppressedReasons": ["BOUNCE", "COMPLAINT"]}

# Configuration set exists with event destinations
aws sesv2 get-configuration-set-event-destinations --configuration-set-name transactional-config
# Expected: at least one destination with Bounce and Complaint event types
```

### 3. Sandbox Status

```bash
aws sesv2 get-account --query 'SendingEnabled'
# Expected: true (production access granted)
aws sesv2 get-account --query 'Details.SendingQuota'
# Expected: MaxSendRate > 1, Max24HourSend >> 200 (confirms out-of-sandbox)
```

**Troubleshooting**:
- `DKIM Status = PENDING` → DNS CNAME records not yet propagated (allow up to 72h)
- `MAILFROM Status = FAILED` → Check SPF TXT and MX records on the MAIL FROM subdomain
- `SendingEnabled = false` → Account paused; check `Reputation.BounceRate` / `Reputation.ComplaintRate` alarms; contact AWS Support if SES-enforced

---

## Quick Reference

**Critical limits**:

| Resource | Limit | Scope |
|----------|-------|-------|
| Daily sending quota (default production) | Auto-increases with reputation | Per region, per recipient (To+CC+BCC each = 1) |
| Max send rate (default production) | Auto-increases with reputation | Per region, messages/second |
| Sandbox daily limit | 200 messages / 1 msg/sec | Per region; recipients must be verified |
| Bounce rate review threshold | 5% | Account-level; pause at 10% |
| Complaint rate review threshold | 0.1% | Account-level; pause at 0.5% |
| Email templates | 20,000 per region, 500 KB each | API v2 `CreateEmailTemplate` |
| `SendBulkEmail` destinations per call | 50 | API v2 |
| Max attachment size | 40 MB | API v2 only |
| Sending authorization policies per identity | 20 (4 KB each) | Resource-based |
| Verified identities per region | 10,000 | Domains + email addresses combined |

**Essential CLI commands**:
```bash
# Verify identity (domain)
aws sesv2 create-email-identity --email-identity example.com \
  --dkim-signing-attributes '{SigningAttributesOrigin: AWS_SES}'

# Request production access
aws sesv2 put-account-details --mail-type TRANSACTIONAL \
  --website-url https://example.com --use-case-description "..."

# Send test email (API v2)
aws sesv2 send-email \
  --from-email-address noreply@example.com \
  --destination '{"ToAddresses":["test@example.com"]}' \
  --content '{"Simple":{"Subject":{"Data":"Test"},"Body":{"Text":{"Data":"Test body"}}}}' \
  --configuration-set-name transactional-config

# Check reputation metrics
aws sesv2 get-account --query 'ReputationMetrics'
```

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/architecting-aws-ses-email/
├── SKILL.md                          <- This file (summary + guardrails)
└── blueprints/
    └── evaluation-scenarios.md       <- 5 test scenarios for skill-evaluator
```

---

## External Resources

### Official Documentation
- [SES Developer Guide (2026)](https://docs.aws.amazon.com/ses/latest/dg/) — Primary reference
- [SES API v2 Reference](https://docs.aws.amazon.com/ses/latest/APIReference-V2/) — SendEmail, configuration sets, suppression list APIs
- [DMARC Configuration](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html) — SPF/DKIM/DMARC alignment guide
- [Easy DKIM Setup](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html) — 2048-bit RSA, CNAME records
- [Configuration Sets](https://docs.aws.amazon.com/ses/latest/dg/using-configuration-sets.html) — Event destinations, IP pools, TLS policy
- [Account-Level Suppression List](https://docs.aws.amazon.com/ses/latest/dg/sending-email-suppression-list.html) — Bounce/complaint suppression, tenant-level (2026)
- [Dedicated IP Addresses](https://docs.aws.amazon.com/ses/latest/dg/dedicated-ip.html) — Standard vs. Managed
- [Global Endpoints (MREP)](https://docs.aws.amazon.com/ses/latest/dg/global-endpoints.html) — Active-active multi-region
- [Sending Authorization](https://docs.aws.amazon.com/ses/latest/dg/sending-authorization-overview.html) — Cross-account delegation
- [IAM and SES Access Control](https://docs.aws.amazon.com/ses/latest/dg/control-user-access.html) — Condition keys, least-privilege

### 2025–2026 Release Announcements
- [Three-Tier Pricing Plans](https://aws.amazon.com/about-aws/whats-new/2026/07/amazon-ses-pricing-plans/) — GA 2026-07-21
- [Bot/Automated Interaction Detection](https://aws.amazon.com/about-aws/whats-new/2026/08/amazon-ses-automated-email-interactions/) — `isBotEvent`, GA 2026-08-07
- [Tenant-Level Suppression Lists](https://aws.amazon.com/about-aws/whats-new/2026/06/amazon-ses-tenant-level-suppression-lists/) — GA 2026-06-01
- [Tenant Isolation + Automated Reputation Policies](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-ses-tenant-isolation-automated-reputation-policies) — GA 2025-08-01
- [IP Observability for Dedicated IP (Managed)](https://aws.amazon.com/about-aws/whats-new/2025/10/amazon-ses-ip-observability-dedicated-op-addresses-managed/) — GA 2025-10-21
- [Bulk Sender Requirements (Gmail/Yahoo/Microsoft)](https://aws.amazon.com/blogs/messaging-and-targeting/navigate-bulk-sender-requirements-with-amazon-ses) — 2024–2025 enforcement baseline
