# Cloud Architecture Research — AWS SES Simple Email Service

## Metadata
```yaml
Full_Name: "AWS SES Simple Email Service"
Cloud_Provider: "AWS"
Architecture_Domain: "Messaging Architecture - SES Simple Email Service"
Target_Edition: "AWS SES 2026"
Architecture_Context: "web application"
Official_Source_URL: "https://docs.aws.amazon.com/ses/latest/dg/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-30"
Currency_Threshold: "2027-08-30"
Research_Depth: "exhaustive"
Max_Iterations: 8
Research_Quality_Score: "84%"
Gap_Loop_Ran: "true"
Iterations_Used: "6 of 8"
Triangulated_Count: "75"
Unverified_Count: "4"
Irresolvable_Count: "8"
```

---

## Executive Summary

Amazon Simple Email Service (SES) is AWS's cloud-based email sending and receiving platform, positioned within the Messaging Architecture domain as the primary mechanism for transactional and marketing email dispatch from web applications. In a cloud-native web application, SES integrates directly with application-tier compute (Lambda, ECS, EC2) via the SES API v2 and with downstream event-processing services (SNS, EventBridge, Kinesis Data Firehose) for deliverability feedback. SES enforces a region-scoped model: verified identities, sending quotas, SMTP credentials, suppression lists, and configuration sets are all independently managed per AWS Region, making multi-region design an explicit architectural concern rather than a default.

In AWS SES 2026, the most significant changes are the introduction of a three-tier pricing model (Essentials/Pro/Enterprise, GA July 21, 2026), automated bot/interaction detection via the `isBotEvent` field in event notifications (GA August 7, 2026), inbox placement metrics and blocklist monitoring via an extended Virtual Deliverability Manager (GA May 29, 2026), and tenant-level suppression lists with a new `TenantName` API parameter (GA June 1, 2026). The Mail Manager component received Invoke Lambda and Bounce rule actions plus mutual TLS ingress support (GA April 1, 2026). Gmail and Yahoo bulk sender requirements — mandatory DKIM domain alignment, custom MAIL FROM for SPF/DMARC, and one-click unsubscribe — have been enforced since February/June 2024 and now represent a non-negotiable compliance baseline; Microsoft extended similar requirements for senders over 5,000 messages/day in May 2025. SES API v1 (2010-12-01) has not been deprecated as of August 2026, but all new features are exclusive to API v2.

The three most critical architecture guardrails for a web application context are: (1) sender authentication — SPF with custom MAIL FROM, DKIM via Easy DKIM (2048-bit), and DMARC (`p=none` minimum, progressing to `p=reject`) are mandatory to pass Gmail, Yahoo, and Microsoft delivery policies; (2) bounce and complaint handling — the absence of an SNS event destination processing bounce/complaint events is the single most common cause of SES account suspension, and the account-level suppression list must be confirmed enabled; (3) API v2 over SMTP — the SES API v2 with IAM execution roles eliminates static credential management, enables Global Endpoints for active-active multi-region, and provides CloudTrail data event visibility, while SMTP-based sending does none of these.

---

## Cloud Architecture Glossary

10–20 terms that the architect must understand precisely — defined from official AWS documentation, not informal usage:

```
Term: Verified Identity
Definition: An email address or domain that has been confirmed as owned by the sender. SES only sends mail from verified identities.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/verify-addresses-and-domains.html
Architect Usage: Always prefer domain identities over email address identities — a domain identity covers all addresses under that domain and its subdomains. Override hierarchy (fine-to-coarse): email address > subdomain > domain.
Common Confusion: Confused with "verified recipient" (sandbox restriction). Verification applies to the sending identity, not to who receives mail.
```

```
Term: Email Address Identity
Definition: A specific email address (e.g., sender@example.com) verified via a click-link confirmation. Verification is per-region.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/verify-email-addresses.html
Architect Usage: Use only for test/development scenarios where a domain cannot be verified. Email address identities do not inherit domain-level DKIM.
Common Confusion: Confused with domain identity. Email address identities require separate DNS setup for DKIM; domain identities auto-cover subdomains.
```

```
Term: Domain Identity
Definition: A domain (e.g., example.com) verified via DNS record publication. A domain identity covers all sub-addresses and subdomains. Up to 10,000 verified identities per region.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/verify-domain-procedure.html
Architect Usage: The standard production choice. Configure Easy DKIM CNAMEs during verification. Subdomain delegation is automatic (no additional verification needed).
Common Confusion: Confused with "email address identity." Domain identities require DNS CNAME records; email address identities require only email click confirmation.
```

```
Term: Easy DKIM
Definition: AWS-managed DKIM signing where SES generates a 2048-bit RSA key pair, publishes the public key as three DNS CNAME records, and signs every outbound message automatically. Default key size is 2048-bit; 1024-bit available for DNS providers that do not support 2048.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html
Architect Usage: The recommended production DKIM mechanism. Cannot switch to the same key length already configured; cannot switch more than once per 24 hours.
Common Confusion: Confused with BYODKIM (Bring Your Own DKIM). Easy DKIM is AWS-managed; BYODKIM requires the customer to generate and manage the private key.
```

```
Term: BYODKIM (Bring Your Own DKIM)
Definition: A DKIM configuration mode where the customer generates a private/public RSA key pair (1024–2048 bit), publishes the public key in DNS as a TXT record, and provides the private key to SES.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-bring-your-own.html
Architect Usage: Use when existing DKIM keys are already published and the organization wants to maintain control of the private key outside AWS. Architect is responsible for rotation.
Common Confusion: Confused with Easy DKIM. BYODKIM is customer-managed; key rotation is a manual operation.
```

```
Term: DEED (Domain-based Easy DKIM)
Definition: A mechanism that replicates DKIM signing configuration across multiple AWS Regions from a parent domain, so that a single set of DNS CNAME records enables consistent DKIM in all regions where the domain identity is active.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy-managing.html
Architect Usage: Mandatory when using SES Global Endpoints (MREP) for active-active multi-region. Eliminates the need to publish per-region CNAME records.
Common Confusion: Confused with cross-account DKIM delegation. DEED is cross-region within the same account; cross-account delegation uses SES sending authorization policies.
```

```
Term: Custom MAIL FROM Domain
Definition: A customer-owned subdomain (e.g., bounce.example.com) configured as the SMTP envelope MAIL FROM address. Requires an SPF TXT record and an MX record pointing to the SES feedback endpoint.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/mail-from.html
Architect Usage: Required for DMARC SPF alignment. The default SES MAIL FROM is an amazonses.com subdomain, which passes SPF but fails DMARC SPF alignment checks at Gmail, Yahoo, and Microsoft.
Common Confusion: Confused with the From: header address. The MAIL FROM is the SMTP envelope sender (used for SPF/DMARC); the From: header is what recipients see.
```

```
Term: DMARC (Domain-based Message Authentication, Reporting & Conformance)
Definition: An email authentication policy published in DNS that instructs receiving mail servers how to handle messages that fail SPF and/or DKIM alignment checks. Policies: p=none (monitor), p=quarantine (spam folder), p=reject (drop).
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html
Architect Usage: Start at p=none with DMARC reporting to identify all mail streams, then progress to p=quarantine and ultimately p=reject. Mandatory at p=none minimum for Gmail/Yahoo/Microsoft bulk sending compliance.
Common Confusion: Confused with SPF or DKIM individually. DMARC requires alignment — the From: header domain must align with either the SPF MAIL FROM domain (relaxed or strict) or the DKIM signing domain (strict is SES default).
```

```
Term: DMARC Alignment
Definition: The requirement that the domain in the message From: header matches (relaxed = organizational domain match; strict = exact match) the domain used in SPF authentication (MAIL FROM) or DKIM signing.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html
Architect Usage: SES default DKIM alignment is strict (adkim=s). SPF alignment is relaxed (aspf=r) when using a subdomain MAIL FROM. At least one alignment (SPF or DKIM) must pass for DMARC to pass.
Common Confusion: Confused with "SPF pass" or "DKIM pass." A message can pass SPF and DKIM individually but still fail DMARC if neither aligns with the From: header domain.
```

```
Term: Sandbox
Definition: The default SES sending mode for new accounts in each region. Limits: 200 messages per 24 hours, 1 message per second, only verified email addresses and domains as recipients.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html
Architect Usage: Sandbox is per-region. Exiting sandbox requires a production access request via the SES console or the sesv2 put-account-details API. Mail type (TRANSACTIONAL or MARKETING) is declared at exit time.
Common Confusion: Confused with the account-level suppression list. The sandbox is a sending restriction for new accounts; the suppression list is a reputation-protection mechanism for production accounts.
```

```
Term: Sending Quota
Definition: The maximum number of email recipients (To + CC + BCC each count as 1) that an account can send to within a 24-hour rolling period, and the maximum send rate (messages per second). Both are per-region.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/manage-sending-quotas.html
Architect Usage: Quota counts per recipient, not per message. Quota auto-increases as reputation improves. For burst traffic, buffer sends via SQS to stay below the max send rate.
Common Confusion: Confused with "per-message limit." A single SendEmail call with 3 recipients consumes 3 of the daily sending quota.
```

```
Term: Configuration Set
Definition: A named collection of rules attached to email sending that controls: event destinations (where to publish sending events), dedicated IP pools (which IP pool to use), tracking (open/click), TLS policy, and suppression list options.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/using-configuration-sets.html
Architect Usage: Every production identity must have a default configuration set. Specify per API call via ConfigurationSetName or per identity as a default. A per-call specification overrides the identity default.
Common Confusion: Confused with IAM policies. Configuration sets control email sending behavior and observability; IAM policies control who can call SES APIs.
```

```
Term: Message Tag
Definition: A name=value pair attached to an email send operation (via EmailTags API parameter or X-SES-MESSAGE-TAGS SMTP header) that segments event publishing data for reporting and filtering.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/monitor-using-event-publishing-setup-set-up-sns.html
Architect Usage: Use message tags to segment events by campaign, customer segment, or product area. Tags appear in CloudWatch metrics dimensions and SNS/Firehose event payloads.
Common Confusion: Confused with AWS resource tags (cost allocation). Message tags are per-email metadata for deliverability analytics; they do not appear in AWS Cost Explorer.
```

```
Term: Auto-Tag
Definition: A set of message tags automatically included by SES in every event notification regardless of whether the sender specified any tags. Fixed set: ses:caller-identity, ses:configuration-set, ses:from-domain, ses:outgoing-ip, ses:source-ip, ses:source-tls-version, ses:outgoing-tls-version.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/monitor-using-event-publishing-setup-set-up-sns.html
Architect Usage: Use ses:from-domain and ses:configuration-set auto-tags in CloudWatch metric filters to isolate per-domain or per-config-set reputation metrics without custom tagging.
Common Confusion: Confused with manually specified message tags. Auto-tags are always present; manual tags are optional additions.
```

```
Term: VDM (Virtual Deliverability Manager)
Definition: An optional SES add-on with two tiers: SES Deliverability ($0.07/1,000 emails — dashboard, advisor, per-ISP/identity/config-set metrics) and Global Deliverability ($1,250/month/region — inbox placement testing, blocklist monitoring across multiple ISPs).
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/vdm.html
Architect Usage: Enable VDM SES Deliverability tier from day one in production. The Advisor surfaces actionable recommendations. Global Deliverability tier is necessary only when inbox placement accuracy across multiple ISPs is a business requirement.
Common Confusion: Confused with CloudWatch SES metrics. VDM provides deliverability intelligence (ISP-level inbox placement, advisor); CloudWatch provides operational metrics (send rate, bounce rate, quota usage).
```

```
Term: Shared IP Pool
Definition: The default pool of IP addresses shared across all SES customers not using dedicated IPs. No additional cost.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/dedicated-ip.html
Architect Usage: Appropriate for low or irregular sending volume. Reputation is shared across all SES customers on those IPs; AWS monitors and manages reputation.
Common Confusion: Confused with Dedicated IP (Managed). Shared IPs have no additional cost but no reputation isolation; Dedicated IPs (Managed) have a flat monthly fee but provide automated warmup and isolation.
```

```
Term: Dedicated IP Standard
Definition: Static dedicated IP addresses manually assigned to an SES account's dedicated IP pool. Customer is responsible for manual IP warmup. Cost: per-IP monthly charge.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/dedicated-ip.html
Architect Usage: Use when specific ISPs require known/static IP addresses on an allowlist. Manual warmup is an operational overhead. Best for high-volume senders with controlled sending schedules.
Common Confusion: Confused with Dedicated IP (Managed). Standard requires manual warmup and provides static IPs; Managed provides auto-warmup and auto-scaling but IPs are not static.
```

```
Term: Dedicated IP Managed
Definition: A Dedicated IP configuration where AWS automatically provisions, warms up (per ISP), and scales IP addresses based on sending volume. Cost: flat monthly fee plus per-message surcharge.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/dedicated-ip-managed.html
Architect Usage: The recommended dedicated IP choice for variable high-volume senders. Removes operational burden of warmup scheduling. Includes CloudWatch Metrics for Microsoft SNDS feedback per IP (IP Observability, GA October 2025).
Common Confusion: Confused with Dedicated IP Standard. Managed IPs are not static (IP addresses may change); Standard IPs are static and known.
```

```
Term: SES API v2
Definition: The current SES API version (2019-09-27), surfaced as the aws sesv2 CLI prefix. Provides a unified SendEmail action (replaces SendEmail + SendTemplatedEmail + SendBulkTemplatedEmail from v1), up to 40 MB attachment support, VDM programmatic configuration, Global Endpoints, and all features introduced after 2019. Email receiving remains on API v1.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/Welcome.html
Architect Usage: All new integrations must use API v2. SMTP-based sending is not compatible with Global Endpoints; API v2 with IAM roles eliminates static credential management.
Common Confusion: Confused with SES API v1 (aws ses CLI prefix, 2010-12-01 API version). API v1 is not deprecated as of August 2026 but receives no new features. Email receiving actions (ReceiveEmail receipt rules) remain v1-only.
```

---

## Architecture Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**SPF + DKIM + DMARC Sender Authentication** 🟢
- Pillar Alignment: Security; Operational Excellence (deliverability continuity)
- Why: Gmail and Yahoo enforce mandatory DKIM domain alignment, custom MAIL FROM for SPF/DMARC alignment, and DMARC p=none minimum for all bulk senders since February–June 2024. Microsoft extended equivalent requirements effective May 5, 2025 for senders >5,000 messages/day. Failure to comply results in delivery rejection at destination.
- AWS Services: Amazon SES (Easy DKIM, Custom MAIL FROM), Amazon Route 53 (DNS records for SPF TXT, DKIM CNAME, DMARC TXT, MAIL FROM MX)
- Architecture Decision:
  1. Enable Easy DKIM on the domain identity (3 CNAME records, 2048-bit default). SES auto-signs every outbound message.
  2. Configure a custom MAIL FROM subdomain (e.g., `bounce.example.com`) with an SPF TXT record (`v=spf1 include:amazonses.com ~all`) and an MX record pointing to `feedback-smtp.<region>.amazonses.com`.
  3. Publish a DMARC TXT record at `_dmarc.example.com` starting with `p=none` for monitoring, then progress to `p=quarantine` and `p=reject` as confidence in mail stream coverage increases.
  4. DKIM alignment: strict by default in SES (`adkim=s`). SPF alignment: relaxed (`aspf=r`) via subdomain MAIL FROM.
- Verification:
  - CLI: `aws sesv2 get-email-identity --email-identity example.com` — verify `DkimAttributes.Status = SUCCESS` and `MailFromAttributes.MailFromDomainStatus = SUCCESS`.
  - DNS: `dig TXT _dmarc.example.com` — verify DMARC policy present.
  - SES Console: Identity detail page shows green checkmarks for DKIM and MAIL FROM status.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html]

**Bounce and Complaint Handling via SNS/Event Notifications** 🟢
- Pillar Alignment: Reliability; Operational Excellence
- Why: SES will automatically place an account under review at bounce rate ≥5% and may pause sending at ≥10%. Complaint rate review threshold is ≥0.1% and pause threshold is ≥0.5%. Without automated processing of bounce and complaint events, rates escalate until account suspension.
- AWS Services: Amazon SES (Configuration Sets, Event Destinations), Amazon SNS, AWS Lambda, Amazon DynamoDB or SES Account Suppression List (`PutSuppressedDestination`)
- Architecture Decision:
  1. Create a configuration set and attach an SNS event destination for Bounce and Complaint event types.
  2. Subscribe a Lambda function to the SNS topic. The Lambda parses the SNS message body (JSON bounce/complaint notification) and calls `sesv2 put-suppressed-destination` with reason `BOUNCE` or `COMPLAINT`.
  3. Confirm the account-level suppression list is enabled: `aws sesv2 get-account` — verify `SuppressionAttributes.SuppressedReasons` includes `BOUNCE` and `COMPLAINT`. For accounts created before November 25, 2019, call `PutAccountSuppressionAttributes` to enable.
  4. Note: Only hard bounces are auto-added to the suppression list; soft bounces are NOT. Gmail spam reports do NOT appear in SES complaint events — VDM or postmaster tools are required for Gmail-specific spam signal.
- Verification:
  - SES Console: Configuration Set → Event Destinations — verify SNS destination for Bounce/Complaint.
  - CLI: `aws sesv2 get-account` → `SuppressionAttributes`.
  - CloudWatch: alarm on `Reputation.BounceRate` ≥5% and `Reputation.ComplaintRate` ≥0.1%.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity-using-notifications.html]

**Account-Level Suppression List Enabled** 🟢
- Pillar Alignment: Reliability; Cost Optimization (avoids charges for undeliverable sends)
- Why: Suppressed addresses are accepted by SES (counted against quota) but not delivered to the ISP; the undelivered messages are excluded from `Reputation.BounceRate` and `Reputation.ComplaintRate` metrics, preventing reputation damage from repeated sends to known-bad addresses.
- AWS Services: Amazon SES Account Suppression List, SES API v2 (`PutSuppressedDestination`, `GetSuppressedDestination`, `DeleteSuppressedDestination`, `ListSuppressedDestinations`)
- Architecture Decision:
  1. Confirm suppression list is active (default for accounts after November 25, 2019). Older accounts must call `sesv2 put-account-suppression-attributes --suppressed-reasons BOUNCE COMPLAINT`.
  2. In the bounce/complaint Lambda (see above), call `sesv2 put-suppressed-destination` for each bounced/complained address.
  3. Provide recipients with an unsubscribe mechanism. For bulk senders, implement one-click unsubscribe per RFC 8058 (`List-Unsubscribe-Post` header) as required by Gmail/Yahoo/Microsoft policies.
  4. Tenant-level suppression (GA June 1, 2026): use `TenantName` parameter in suppression API calls for multi-tenant SaaS architectures.
- Verification:
  - CLI: `aws sesv2 get-account` — check `SuppressionAttributes`.
  - CLI: `aws sesv2 list-suppressed-destinations` — verify suppressed addresses are being written.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/sending-email-suppression-list.html]

**Configuration Sets for Every Production Send** 🟢
- Pillar Alignment: Operational Excellence (observability and traceability)
- Why: Without a configuration set, there is no event destination, no reputation isolation, no dedicated IP pool routing, no per-campaign/per-identity tracking, and no ability to enforce TLS policy.
- AWS Services: Amazon SES Configuration Sets, Event Destinations (SNS, Kinesis Data Firehose, CloudWatch, EventBridge, Pinpoint)
- Architecture Decision:
  1. Create at least one configuration set per sending domain or sending use case (transactional vs. marketing).
  2. Set a default configuration set on each verified identity: `aws sesv2 update-email-identity --email-identity example.com --configuration-set-name transactional-config`.
  3. For SMTP integrations, specify via the `X-SES-CONFIGURATION-SET` header.
  4. Attach event destinations for all required event types: Send, Delivery, Bounce, Complaint, Reject, Open, Click, RenderingFailure.
- Verification:
  - CLI: `aws sesv2 get-configuration-set --configuration-set-name <name>` — verify SendingOptions.SendingEnabled = true and event destinations exist.
  - CLI: `aws sesv2 get-email-identity --email-identity <domain>` — verify ConfigurationSetName is set.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/using-configuration-sets.html]

**Least-Privilege IAM for Sending Roles** 🟢
- Pillar Alignment: Security
- Why: Over-permissioned IAM roles for sending-only workloads can allow deletion of verified identities, modification of configuration sets, and exfiltration of email templates — far beyond what a send-only role requires.
- AWS Services: AWS IAM (execution roles for Lambda/ECS/EC2), SES IAM condition keys
- Architecture Decision:
  1. Grant only `ses:SendEmail` and/or `ses:SendRawEmail`. Scope the `Resource` to specific verified identity ARNs (`arn:aws:ses:<region>:<account>:identity/<domain>`).
  2. Add the `ses:FromAddress` condition key to prevent sending from unauthorized From addresses.
  3. For SMTP: use the `AWSSESSendingGroupDoNotRename` IAM group with the `AmazonSesSendingAccess` policy (only `ses:SendRawEmail`). Post-September 6, 2024, new SMTP users use group-based policies, not inline policies.
  4. Never use `ses:*` for sending-only roles.
  5. Use IAM execution roles (Lambda, ECS task roles, EC2 instance profiles) — no static access keys for API v2 sends.
- Verification:
  - IAM Access Analyzer: check for overly permissive SES policies.
  - CLI: `aws iam get-role-policy --role-name <lambda-role> --policy-name <policy>` — verify no `ses:*` wildcards.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/control-user-access.html]

**Bounce/Complaint Rate CloudWatch Alarms** 🟢
- Pillar Alignment: Reliability; Operational Excellence
- Why: SES will autonomously place accounts under review and pause sending at defined thresholds. Early warning via CloudWatch enables a circuit-breaker response before SES-enforced suspension.
- AWS Services: Amazon CloudWatch (Alarms), Amazon SNS (Alarm notifications), AWS Lambda (automated pause), Amazon SES (`PutAccountSendingAttributes`, `PutConfigurationSetSendingOptions`)
- Architecture Decision:
  1. Create CloudWatch alarms:
     - `Reputation.BounceRate` ≥5% → WARNING alarm; ≥10% → CRITICAL alarm (trigger sending pause).
     - `Reputation.ComplaintRate` ≥0.1% → WARNING alarm; ≥0.5% → CRITICAL alarm.
  2. Alarm action: SNS → Lambda → `sesv2 put-account-sending-attributes --sending-enabled false` (account-level pause) or `sesv2 put-configuration-set-sending-options --configuration-set-name <name> --sending-enabled false` (isolated pause per config set).
  3. CRITICAL alarms should page on-call — account suspension recovery requires contacting AWS Support.
- Verification:
  - CloudWatch Console: Alarms — verify alarm states and SNS actions.
  - SES Console: Reputation Metrics page — verify metrics are actively updated.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/reputationdashboard-cloudwatch-alarm.html]

---

### ⚠️ Architectural Decisions

**Dedicated IP Pool Selection** 🟢
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Shared IP Pool | SES default pool | Zero additional cost, instant availability | Reputation isolation, no control over IP history | Low or irregular volume (<100K/month), startups |
  | Dedicated IP Standard | SES Dedicated IP (Standard) | Static/known IPs, full reputation isolation | Manual warmup operational burden, per-IP cost | High-volume senders needing ISP allowlisting, compliance-controlled environments |
  | Dedicated IP Managed | SES Dedicated IP (Managed) | Auto-warmup per ISP, auto-scales, reputation isolation | Flat monthly cost + per-msg surcharge, IPs not static | Variable high-volume senders, irregular burst patterns |

- Cost Profile: Shared = no additional charge. Standard = per-IP monthly fee (check current pricing). Managed = $15/month flat + $0.08/1,000 messages surcharge.
- Lock-in Assessment: IP pools are SES-native. Migrating to another provider requires re-warming equivalent IPs, which typically takes 4–8 weeks. Historical reputation does not transfer.
- Architect Instruction: "Ask whether the organization has existing ISP allowlisting requirements for specific IP ranges when evaluating Dedicated IP Standard; ask about sending volume predictability when evaluating Dedicated IP Managed vs. Standard."
- Source: [https://docs.aws.amazon.com/ses/latest/dg/dedicated-ip.html]

**Multi-Region Sending Strategy** 🟡
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Single-region | SES (one region) | Simplicity, single suppression list | No HA, quota limited to one region | Low volume, non-critical notifications |
  | Manual multi-region failover | SES (multiple regions) | Region redundancy | Manual quota/identity duplication, split suppression lists | DR requirements with manual runbooks |
  | Global Endpoints (MREP) | SES Global Endpoints + DEED | Active-active, auto traffic shift on impairment, no DNS burden with DEED | API v2 only (not SMTP, not VPC endpoints), requires duplicate config sets and identities in secondary | HA/DR requirements for transactional email, production web applications |

- Cost Profile: Global Endpoints: no endpoint surcharge; standard SES sending charges apply in both regions. DNS TTL guidance: positive ~60s, negative ~10s. HTTP connection TTL ~60s. [UNVERIFIED: RTO/RPO guarantees — AWS documents DNS TTL guidance only, not guaranteed RTO/RPO values]
- Lock-in Assessment: Global Endpoints use SES-proprietary MREP feature. Switching to manual multi-region requires DNS changes and runbook updates, no data migration required.
- Architect Instruction: "Ask whether the application already uses SES API v2 exclusively (SMTP users cannot use Global Endpoints); ask whether the secondary region has production access and matching quotas before enabling MREP."
- Source: [https://docs.aws.amazon.com/ses/latest/dg/global-endpoints.html]

**SES API v2 vs. SMTP Interface** 🟢
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | SES API v2 | SESv2 SDK / CLI | IAM role auth, no static creds, Global Endpoints, CloudTrail data events, 40 MB attachments | Application code change from SMTP | All new web application integrations |
  | SMTP Interface | SES SMTP endpoint | Drop-in for existing SMTP libraries, no SDK required | Static credentials required (no temporary creds), no Global Endpoints, not CloudTrail-logged, port 25 blocked in VPCs | Legacy application migration, third-party software that only supports SMTP |

- Cost Profile: Identical per-message pricing. SMTP credential storage in Secrets Manager adds negligible cost.
- Lock-in Assessment: API v2 is AWS-proprietary SDK. SMTP is protocol-portable; migrating from SMTP to API v2 requires code changes but no credential migration.
- Architect Instruction: "Confirm whether the application framework supports AWS SDK v2 before recommending API v2; if the integration point is a third-party software that only supports SMTP, document the static credential storage in Secrets Manager and the absence of CloudTrail SMTP logging as accepted risks."
- Source: [https://docs.aws.amazon.com/ses/latest/dg/send-email-concepts-credentials.html]

---

### 🚫 Anti-Patterns

**Embedding SES SMTP Credentials in Application Code** 🟢
- Risk Level: CRITICAL
- Why: Violates Security pillar. SES SMTP credentials are static IAM-derived secrets (HMAC-SHA256 of secret access key). Temporary credentials cannot be used to derive SMTP credentials. There is no in-place rotation — credential rotation requires deleting the IAM user and generating new credentials, meaning any hardcoded credential is a long-lived secret.
- ❌ Wrong:
  Application code (Lambda, ECS task, EC2 instance) contains SMTP username and password as environment variables or in a configuration file committed to source control. No credential rotation scheduled.
- ✅ Correct:
  Option A: Use SES API v2 with IAM execution role (Lambda execution role, ECS task role, EC2 instance profile) — no static credentials at all.
  Option B (if SMTP is unavoidable): Generate SMTP credentials once, store in AWS Secrets Manager, inject via Secrets Manager API at runtime. Implement rotation by registering a Lambda rotation function that deletes and recreates the IAM SMTP user.
- Detection:
  - `grep -r "SMTP_PASSWORD\|SMTP_USER\|smtp_password" .` in application repositories.
  - AWS Secrets Manager: confirm SES SMTP credentials are stored as secrets, not in environment variables.
  - AWS Config rule: `restricted-smtp` or custom Config rule detecting SMTP env vars.
- Impact: Data breach (email content exposure), account takeover (attacker sends spam from your domain, destroying reputation and triggering SES account suspension)
- Source: [https://docs.aws.amazon.com/ses/latest/dg/smtp-credentials.html]

**Sending Without a Configuration Set** 🟢
- Risk Level: HIGH
- Why: Violates Operational Excellence pillar. Without a configuration set there is no event destination for bounce/complaint feedback, no IP pool assignment, no open/click tracking, and no ability to enforce TLS policy per sending stream.
- ❌ Wrong:
  `aws sesv2 send-email --from-email-address noreply@example.com --destination '{"ToAddresses":["user@example.com"]}' --content '...'` — no `--configuration-set-name` parameter.
- ✅ Correct:
  Option A: Set a default configuration set on the verified identity: `aws sesv2 update-email-identity --email-identity example.com --configuration-set-name transactional-config`.
  Option B: Pass `--configuration-set-name transactional-config` on every `send-email` call.
  Option C: For SMTP, include `X-SES-CONFIGURATION-SET: transactional-config` header.
- Detection:
  - CloudWatch: absence of SES event metrics for a sending domain indicates no event destination (implies no configuration set).
  - SES Console: verified identity detail → check ConfigurationSetName field.
- Impact: No visibility into bounce/complaint rates; reputation degradation goes undetected until SES enforces account suspension
- Source: [https://docs.aws.amazon.com/ses/latest/dg/using-configuration-sets.html]

**No Bounce/Complaint Suppression Pipeline** 🟢
- Risk Level: CRITICAL
- Why: Violates Reliability pillar. Repeated sends to hard-bounced or complained-about addresses inflate `Reputation.BounceRate` and `Reputation.ComplaintRate`, the two metrics SES uses to enforce account suspension. Gmail spam reports are not surfaced in SES complaint events, creating an additional blind spot.
- ❌ Wrong:
  Application sends email directly via SES API with no SNS event destination for Bounce/Complaint events. DLQ messages from failed sends are ignored. No suppression list processing exists.
- ✅ Correct:
  Configuration Set with SNS event destination (Bounce + Complaint types) → Lambda → parse notification → `sesv2 put-suppressed-destination`. Enable account-level suppression list. Monitor `Reputation.BounceRate` and `Reputation.ComplaintRate` via CloudWatch alarms.
- Detection:
  - SES Console: Configuration Set → Event Destinations — if no SNS/Firehose destination for Bounce/Complaint, this anti-pattern is present.
  - `aws sesv2 get-account` — check `SuppressionAttributes.SuppressedReasons`; empty means suppression list is not processing bounces/complaints.
- Impact: Account suspension (SES pauses all sending), revenue loss, reputation destruction requiring weeks of recovery
- Source: [https://docs.aws.amazon.com/ses/latest/dg/sending-email-suppression-list.html]

**Using `ses:*` Wildcard for Sending-Only IAM Roles** 🟢
- Risk Level: HIGH
- Why: Violates Security pillar (least privilege). `ses:*` grants ability to delete verified identities, modify or delete configuration sets, delete email templates, modify suppression lists, read/list all account settings — none of which are required for a sending-only role.
- ❌ Wrong:
  IAM policy for Lambda email-sending function: `"Action": "ses:*"`, `"Resource": "*"`.
- ✅ Correct:
  `"Action": ["ses:SendEmail", "ses:SendRawEmail"]`, `"Resource": "arn:aws:ses:<region>:<account>:identity/<domain>"`. Add `"Condition": {"StringEquals": {"ses:FromAddress": "noreply@example.com"}}` to prevent unauthorized From address substitution.
- Detection:
  - IAM Access Analyzer: findings for overly permissive SES policies.
  - CLI: `aws iam simulate-principal-policy --action-names ses:DeleteEmailIdentity` on the sending role — should return `implicitDeny`.
- Impact: Privilege escalation (attacker with Lambda role access can delete all verified identities, destroying sending capability), data exfiltration (email template content retrieval)
- Source: [https://docs.aws.amazon.com/ses/latest/dg/control-user-access.html]

**Sending Without DMARC SPF Alignment (Using Default MAIL FROM)** 🟢
- Risk Level: HIGH
- Why: Violates Security and Operational Excellence pillars. The default SES MAIL FROM is an `amazonses.com` subdomain. While this passes SPF for `amazonses.com`, it fails DMARC SPF alignment against the sender's From: header domain (e.g., `example.com`). With Gmail, Yahoo, and Microsoft now enforcing DMARC, messages with SPF misalignment and no DKIM alignment pass will be rejected or quarantined.
- ❌ Wrong:
  Domain identity `example.com` is verified with Easy DKIM, but MAIL FROM is left as the SES default (`amazonses.com` subdomain). DMARC record published at `_dmarc.example.com` with `p=reject`. SPF alignment fails; if DKIM also fails (e.g., DKIM signature broken by a relay), DMARC fails and messages are rejected.
- ✅ Correct:
  Configure custom MAIL FROM subdomain `bounce.example.com`. Publish SPF TXT `v=spf1 include:amazonses.com ~all` at `bounce.example.com`. Publish MX record pointing to `feedback-smtp.<region>.amazonses.com`. Use relaxed SPF alignment (`aspf=r`) in DMARC record to allow `@bounce.example.com` to satisfy `example.com` DMARC.
- Detection:
  - DNS: check `dig MX bounce.example.com` and `dig TXT bounce.example.com`.
  - CLI: `aws sesv2 get-email-identity --email-identity example.com` → `MailFromAttributes.MailFromDomain` — should not be empty and should not end with `amazonses.com`.
  - DMARC reporting: `rua` aggregate reports will show SPF alignment failures if custom MAIL FROM is not configured.
- Impact: Delivery rejection at Gmail/Yahoo/Microsoft, revenue loss from undelivered transactional email, reputational damage
- Source: [https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html]

---

## Cloud-Native Design Patterns

**Decoupled Async Send Pipeline (SQS → Lambda → SES)** 🟢
- Category: Resilience (Queue-Based Load Leveling)
- Problem: SES per-second sending rate limits cause synchronous API call failures (`TooManyRequestsException`) when application-tier traffic bursts. Synchronous call failure means email is lost unless the caller implements retry logic, which is complex in web request handlers.
- Solution on AWS: Application tier enqueues email payloads to an Amazon SQS Standard queue. AWS Lambda processes the queue via SQS Event Source Mapping (ESM). Lambda calls `sesv2 send-email`. A Dead Letter Queue (DLQ) captures messages that fail after `maxReceiveCount` retries.
  - Key Lambda + SQS configuration: visibility timeout > Lambda function timeout (prevent premature requeue). Batch window up to 5 minutes (reduce Lambda invocations for low-volume queues). Partial batch response (`ReportBatchItemFailures`) ensures only failed individual messages return to the queue, preventing full-batch retry on single-message SES errors.
  - Idempotency: include a message-specific idempotency key in the SQS payload; check DynamoDB before calling SES to prevent duplicate sends on at-least-once redelivery.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Resilience | Absorbs SES rate limit bursts; DLQ prevents message loss | Additional SQS + Lambda cost |
  | Latency | Near-real-time for normal loads; buffer adds seconds under burst | Not suitable for sub-second delivery SLA |
  | Complexity | Decoupled retry without application code change | Idempotency logic required in Lambda |
  | Observability | SQS queue depth and DLQ depth are native CloudWatch metrics | Lambda execution logs require structured logging setup |

- Source: [https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html]

**Event-Driven Bounce and Complaint Processing** 🟢
- Category: Communication (Reactive Event-Driven Architecture for Reputation Management)
- Problem: SES does not automatically remove complained or soft-bounced addresses from future sends. Without automated processing, repeat sends to bad addresses drive reputation metrics to enforcement thresholds.
- Solution on AWS: SES Configuration Set Event Destination → Amazon SNS (for real-time Lambda trigger) or Amazon Kinesis Data Firehose (for batch analytics/S3 archival) or Amazon EventBridge (for routing to multiple consumers). Lambda subscriber parses bounce/complaint JSON notification and calls `sesv2 put-suppressed-destination`.
  - Event types available: Send, Delivery, Bounce (Hard/Soft/Undetermined), Complaint, Reject, RenderingFailure, DeliveryDelay, Subscription, Open, Click.
  - Auto-tags on every event: `ses:caller-identity`, `ses:configuration-set`, `ses:from-domain`, `ses:outgoing-ip`, `ses:source-ip`, `ses:source-tls-version`.
  - Gmail blind spot: Gmail spam-button reports are NOT surfaced in SES Complaint events. Use Gmail Postmaster Tools or VDM Global Deliverability tier for Gmail-specific complaint signals.
  - New 2026: `isBotEvent` field (GA August 7, 2026) auto-included in Open and Click event notifications. Values: `"Likely"` or `"Unlikely"`. Use to filter bot-inflated engagement metrics with no configuration change required.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Reputation protection | Automated suppression prevents rate escalation | Lambda cold starts may delay suppression by seconds |
  | Analytics | Firehose destination enables S3/Athena deliverability analytics | Firehose buffering (60s–900s) delays analytics freshness |
  | Gmail blind spot | VDM Global Deliverability covers multi-provider inbox | $1,250/month/region for Global Deliverability tier |

- Source: [https://docs.aws.amazon.com/ses/latest/dg/monitor-using-event-publishing.html]

**Templated Email Sending at Scale** 🟢
- Category: Scalability (Personalization at Scale)
- Problem: Sending individualized emails to large recipient lists requires either repeated API calls with unique content (slow, expensive) or a batch templating mechanism.
- Solution on AWS: Use SES API v2 `CreateEmailTemplate` to store templates (up to 20,000 templates/region, 500 KB/template). Call `SendBulkEmail` (up to 50 destinations per call) with per-recipient template data substitution (`{{variablename}}` syntax).
  - For one-off sends with no stored resource: use inline templates (max 1 MB per input JSON).
  - RenderingFailure events are emitted when template data is malformed — configure an SNS event destination to capture these.
  - Template management: use v2 `CreateEmailTemplate` / `UpdateEmailTemplate` / `GetEmailTemplate` / `ListEmailTemplates`.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Throughput | 50 destinations per SendBulkEmail call vs. 1 per SendEmail | Template data prep complexity increases with destination count |
  | Template management | Centralized templates, version-controlled via IaC | 500 KB/template limit constrains complex HTML |
  | Observability | RenderingFailure events surface bad template data | Requires SNS event destination for RenderingFailure |

- Source: [https://docs.aws.amazon.com/ses/latest/dg/send-personalized-email-api.html]

**Inbound Email Processing Pipeline (Receipt Rules)** 🟡
- Category: Communication (Inbound Email Processing)
- Problem: Web applications that need to receive email (e.g., support ticket creation, reply-to-thread, email-to-action workflows) require a structured inbound processing pipeline.
- Solution on AWS: SES Receipt Rules define ordered actions on incoming messages. Action types: S3 (store full message, max 40 MB), Lambda (process synchronously or asynchronously), SNS (notify, max 150 KB), Add Header, Return Bounce, Stop Rule Set, WorkMail.
  - Recipient conditions are evaluated against the SMTP envelope `RCPT TO` address (not the To:/Cc: message headers).
  - Email receiving is available only in specific AWS Regions (not all SES regions).
  - Mail Manager alternative (newer): Ingress Endpoint with STARTTLS or mTLS, rule sets with Invoke Lambda and Bounce actions, archive capability, Vade Advanced Email Security add-on for spam/phishing/malware filtering.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Simplicity | Receipt rules are straightforward for basic routing | 150 KB SNS limit means large messages must go to S3 first |
  | Security | Mail Manager mTLS for authenticated partner ingestion | Mail Manager is an additional cost layer |
  | Flexibility | Lambda action enables arbitrary processing logic | Lambda synchronous action adds to SES processing latency |

- Source: [https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html]

**Idempotency and Dead-Letter Queue Safety** 🟢
- Category: Resilience (At-Least-Once Safety)
- Problem: SQS delivers messages at least once, meaning Lambda may process the same email payload multiple times. Without idempotency controls, duplicate emails are sent to recipients — a severe user experience violation for transactional email.
- Solution on AWS: Embed a unique `messageId` (UUID) in the SQS message payload. Before calling SES, Lambda writes a conditional `PutItem` to DynamoDB with a TTL of 24 hours. If the `PutItem` fails (item already exists), skip the SES call and return success. For FIFO SQS queues, `MessageDeduplicationId` provides a 5-minute deduplication window without DynamoDB. SQS DLQ with `maxReceiveCount` (recommend 3–5) captures persistently failing messages for manual review.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Correctness | No duplicate emails even under Lambda retry | DynamoDB `PutItem` adds ~1–5ms latency per send |
  | Failure isolation | Partial batch response isolates per-message failures | Requires Lambda code changes |
  | Auditability | DLQ provides audit trail of failed sends | DLQ messages require manual remediation process |

- Source: [https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html]

**Reputation-Based Circuit Breaker** 🟢
- Category: Resilience (Proactive Sending Pause)
- Problem: SES will autonomously pause an entire account's sending if bounce/complaint rate thresholds are crossed. An automated circuit breaker that pauses sending before SES intervenes enables controlled remediation rather than emergency recovery.
- Solution on AWS: CloudWatch alarms on `Reputation.BounceRate` (WARNING at ≥5%, CRITICAL at ≥10%) and `Reputation.ComplaintRate` (WARNING at ≥0.1%, CRITICAL at ≥0.5%) → SNS → Lambda. Lambda at CRITICAL threshold calls:
  - Account-level pause: `aws sesv2 put-account-sending-attributes --sending-enabled false`
  - Config-set-level pause (less disruptive): `aws sesv2 put-configuration-set-sending-options --configuration-set-name <name> --sending-enabled false`
  - Page the on-call team for investigation before re-enabling.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Availability | Prevents SES-enforced suspension; resumption is self-service | Proactive pause causes temporary email outage |
  | Granularity | Config-set-level pause isolates one sending stream | Requires multiple alarms (one per config set) |
  | Recovery speed | Account-controlled pause can resume after list hygiene | SES-enforced suspension may require AWS Support engagement |

- Source: [https://docs.aws.amazon.com/ses/latest/dg/reputationdashboard-cloudwatch-alarm.html]

---

## Security Architecture

**IAM Identity-Based Policies and Condition Keys** 🟢
- AWS Services: AWS IAM (Identity-Based Policies, Condition Keys), Amazon SES
- Architecture: Grant `ses:SendEmail` / `ses:SendRawEmail` minimum. Scope `Resource` to specific verified identity ARNs. Enforce source address restrictions via `ses:FromAddress` condition key. Additional condition keys for fine-grained control:
  - `ses:Recipients` — restricts To/CC/BCC on SendEmail/SendRawEmail
  - `ses:FromDisplayName` — restricts display name in From: header
  - `ses:FeedbackAddress` — restricts Return-Path (bounce address)
  - `ses:MultiRegionEndpointId` — enforces routing through specific Global Endpoint
  - `ses:ApiVersion` — restricts to specific API version
  - AWS-wide conditions also applicable: `aws:SecureTransport`, `aws:SourceIp`, `aws:SourceVpc`, `aws:SourceVpce`, `aws:CurrentTime`
  For SMTP: `AWSSESSendingGroupDoNotRename` group + `AmazonSesSendingAccess` policy (only `ses:SendRawEmail`). Post-September 6, 2024 new SMTP users use group-based policies, not inline.
- Compliance Alignment: SOC 2, PCI DSS, FedRAMP, HIPAA — compliance reports available via AWS Artifact.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/control-user-access.html]

**Sending Authorization (Resource-Based Cross-Account Delegation)** 🟢
- AWS Services: Amazon SES (Sending Authorization Policies on verified identities), AWS IAM
- Architecture: Identity owner attaches a resource-based authorization policy to a verified SES identity granting a delegate AWS account (or IAM user ARN, or AWS service) the right to send from that identity. Delegate passes `FromEmailAddressIdentityArn` (API v2) or `X-SES-SOURCE-ARN` header (SMTP) to assert the delegated identity.
  - Limits: 20 policies per identity; 4 KB per policy; 64-character policy names.
  - Sending quotas and reputation metrics are counted against the delegate sender's account, not the identity owner's account.
  - Must operate from the same AWS Region where the identity is verified.
- Compliance Alignment: SOC 2 (access control, multi-party authorization)
- Source: [https://docs.aws.amazon.com/ses/latest/dg/sending-authorization-overview.html]

**Encryption in Transit** 🟢
- AWS Services: Amazon SES (API, SMTP), AWS Certificate Manager (TLS), SES FIPS Endpoints
- Architecture:
  - API calls: HTTPS, TLS 1.2/1.3. FIPS endpoints available (`email-fips.<region>.amazonaws.com`).
  - SMTP: STARTTLS (RFC 3207) or TLS Wrapper (SMTPS). Both support TLS 1.2/1.3. Ports: 25 (blocked in most VPCs), 465, 587, 2465, 2587.
  - Outbound delivery (SES to receiving mail server): opportunistic TLS — always attempts TLS, falls back to plaintext if unavailable.
  - RequireTLS policy: set `TlsPolicy=REQUIRE` on a configuration set to force TLS or drop the message if the receiving server does not support TLS.
  - S/MIME and PGP: supported (end-to-end encryption handled by sender/recipient clients, not by SES).
  - Mail Manager 2026: Optional TLS (STARTTLS) and Mutual TLS (mTLS) on Ingress Endpoints.
- Compliance Alignment: PCI DSS (data in transit), HIPAA (ePHI transmission), FedRAMP (FIPS endpoints)
- Source: [https://docs.aws.amazon.com/ses/latest/dg/security-protocols.html]

**Encryption at Rest** 🟢
- AWS Services: Amazon SES, AWS KMS (Customer Managed Keys)
- Architecture:
  - Default: AWS-owned keys, no additional charge, no configuration required.
  - Customer Managed Key (CMK): symmetric KMS key, key usage `ENCRYPT_DECRYPT`. Required KMS key policy permissions for SES service principal (`"Service": "ses.amazonaws.com"`): `kms:DescribeKey`, `kms:GenerateDataKey`, `kms:Decrypt`.
  - Encryption context for CMK: `"aws:ses:arn": "<resource-ARN>"`.
  - Note: S3 receipt rule encryption is configured at the S3 bucket level, not within SES itself. [IRRESOLVABLE — configured at S3 bucket level, not in SES docs]
- Compliance Alignment: HIPAA (data at rest), PCI DSS, FedRAMP
- Source: [https://docs.aws.amazon.com/ses/latest/dg/encryption-rest.html]

**VPC Endpoints (AWS PrivateLink)** 🟢
- AWS Services: Amazon SES, AWS PrivateLink (VPC Interface Endpoints)
- Architecture:
  - SES API (port 443): search `email` in VPC Endpoint services. FIPS API: search `email-fips`.
  - SES SMTP (ports 465, 587, 2465, 2587): search `smtp`. Note: port 25 is NOT used for VPC endpoint SMTP.
  - AZ limitations for SMTP endpoint: `use1-az2`, `use1-az3`, `use1-az5`, `usw1-az2`, `usw2-az4`, `apne2-az4`, `cac1-az3`, `cac1-az4` are NOT supported.
  - VPC endpoint policies can restrict which principals can use the endpoint. [IRRESOLVABLE — SES-specific VPC endpoint policy documentation not found in SES docs]
- Compliance Alignment: PCI DSS (network segmentation), HIPAA (private network transmission), FedRAMP
- Source: [https://docs.aws.amazon.com/ses/latest/dg/send-email-set-up-vpc-endpoints.html]

**CloudTrail Audit Logging** 🟢
- AWS Services: Amazon SES, AWS CloudTrail, Amazon CloudWatch Logs
- Architecture:
  - Management events (CreateEmailIdentity, DeleteEmailIdentity, CreateConfigurationSet, etc.): logged by default, 90-day retention in CloudTrail event history.
  - Data events (SendEmail, SendRawEmail, etc.): NOT logged by default. Require advanced event selectors in a CloudTrail trail with additional CloudWatch Logs charges.
  - SMTP sending: NOT logged to CloudTrail under any configuration.
  - Sensitive data masking: To/CC/BCC, message subject, and body are masked as `"HIDDEN_DUE_TO_SECURITY_REASONS"` in CloudTrail records. Source (From:) address is visible.
  - TLS metadata included in each CloudTrail event: `tlsVersion`, `cipherSuite`, `clientProvidedHostHeader`.
- Compliance Alignment: SOC 2 (audit logging), PCI DSS (log monitoring), FedRAMP
- Source: [https://docs.aws.amazon.com/ses/latest/dg/logging-using-cloudtrail.html]

**DKIM Key Management** 🟡
- AWS Services: Amazon SES (Easy DKIM, BYODKIM), Amazon Route 53 (DNS)
- Architecture:
  - Easy DKIM: 2048-bit RSA default; 1024-bit available for DNS providers that do not support 2048. No automatic scheduled rotation — manual rotation requires changing the key length (triggers new key pair generation). Cannot switch to the same key length already configured; cannot switch more than once per 24 hours.
  - DEED: enables consistent DKIM signing across regions from a parent domain without publishing per-region CNAME records.
  - SMTP credentials are derived from AWS secret access key via HMAC-SHA256 (version byte `0x04`, fixed date `"11111111"`). Rotation: delete IAM SMTP user + generate new credentials (no in-place rotation). Temporary credentials CANNOT be used to derive SMTP credentials.
  - No formal deprecation of 1024-bit DKIM through August 2026. [IRRESOLVABLE — no official deprecation notice]
- Compliance Alignment: NIST SP 800-177 (email security guidelines)
- Source: [https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim.html]

---

## Operational Patterns

**Deliverability Observability Stack** 🟢
- RTO/RPO (if applicable): RTO for detection of deliverability degradation depends on CloudWatch alarm evaluation period (minimum 1 data point = 1 minute for high-resolution metrics). [UNVERIFIED: Global Endpoints RTO/RPO — AWS documents DNS TTL guidance only, not guaranteed values]
- AWS Services: Amazon SES (Configuration Sets, Event Destinations), Amazon CloudWatch, Amazon SNS, Amazon Kinesis Data Firehose, VDM (SES Deliverability + Global Deliverability)

  | Method | Events Covered | Granularity |
  |--------|---------------|-------------|
  | SES Console — Account Dashboard | Sent, quota, bounces, complaints | Account-wide |
  | SES Console — Reputation Metrics | Bounce rate, complaint rate | Account-wide |
  | VDM SES Deliverability | Sent, delivered, complaints, bounces, opens, clicks, by ISP/identity/config set | Multi-dimension |
  | VDM Global Deliverability | Inbox placement %, blocklist monitoring, pre-send testing | Per provider/domain |
  | SES API `GetSendStatistics` | Deliveries, bounces, complaints, rejects | Account totals only |
  | CloudWatch Event Publishing | All event types with message tags | Per user-defined dimension/tag |
  | SNS Feedback Notifications | Deliveries, bounces, complaints | Per-event (real-time) |

- Cost Profile: Basic SES metrics in CloudWatch (quota, sending rate) are free. Event publishing creates custom CloudWatch metrics (billed per metric put). VDM SES Deliverability: $0.07/1,000 emails. VDM Global Deliverability: $1,250/month/region/account.
- Automation: Automate bounce/complaint processing via Lambda (SNS trigger). Automate sending pause via CloudWatch alarm → Lambda circuit breaker. Manual decision: whether to re-enable account after a pause requires list hygiene review.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html]

**Sending Quota and Production Access Management** 🟢
- RTO/RPO (if applicable): N/A (quota management is a pre-launch checklist item, not a failover procedure)
- AWS Services: Amazon SES (Account Dashboard, sending quotas), AWS Support (production access requests)
- Architecture:
  - Sandbox exit: SES Console → Account Dashboard → "Request production access", or `aws sesv2 put-account-details --mail-type TRANSACTIONAL`. Specify mail type (TRANSACTIONAL or MARKETING), website URL, and use case description.
  - Quota is per-region, per-recipient (To + CC + BCC each count as 1 recipient).
  - Auto-increase over time as sending reputation improves. Manual increase request via SES console or AWS Support case.
  - Multi-region: duplicate production access requests per region. Quotas are not shared across regions.
- Cost Profile: Quota management itself has no direct cost. Standard SES pricing applies: $0.10/1,000 emails, $0.12/GB attachments, $0.15/1,000 inbound.
- Automation: Automate quota monitoring via CloudWatch alarm on `Max24HourSend` metric approaching limit.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html]

**Multi-Region Active-Active with Global Endpoints** 🟡
- RTO/RPO (if applicable): [UNVERIFIED — AWS documents DNS TTL guidance (positive ~60s, negative ~10s, HTTP connection TTL ~60s) but does not publish guaranteed RTO/RPO values for Global Endpoints]
- AWS Services: SES Global Endpoints (MREP), SES API v2, DEED, Amazon Route 53
- Architecture:
  1. Enable DEED on the domain identity to replicate DKIM signing to the secondary region.
  2. Duplicate verified identities, configuration sets, and IP pool assignments in the secondary region.
  3. Request and confirm production access (matching quotas) in the secondary region.
  4. Create a Global Endpoint with primary region + secondary region.
  5. Application sends via the Global Endpoint URL — SES auto-routes to the primary region and shifts traffic to secondary on impairment detection.
  6. Cross-region metrics via CloudWatch dimension `ses:multi-region-endpoint-id`.
  - Constraints: API v2 only (SMTP not supported); VPC endpoints not supported with Global Endpoints.
- Cost Profile: Standard SES sending charges in both regions; no endpoint surcharge. Secondary region idle infra costs are minimal (no dedicated EC2 for SES itself).
- Automation: DEED propagation is automatic after initial setup. Quota monitoring in both regions should be automated.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/global-endpoints.html]

**Tenant Isolation for Multi-Tenant SaaS (2025–2026)** 🟢
- RTO/RPO (if applicable): N/A
- AWS Services: Amazon SES (Tenant Isolation, Automated Reputation Policies, Tenant-Level Suppression Lists), Amazon EventBridge
- Architecture:
  - Named tenants per SES account with dedicated config sets, identities, and templates per tenant.
  - Independent reputation metrics per tenant.
  - Automated reputation policy modes: Standard, Strict, None. Auto-pause/resume per tenant based on reputation thresholds.
  - EventBridge publishes tenant status changes for integration with application-tier tenant status management.
  - Tenant-level suppression lists (GA June 1, 2026): `TenantName` parameter added to `PutSuppressedDestination`, `GetSuppressedDestination`, `DeleteSuppressedDestination`, `ListSuppressedDestinations`. Suppression `Scope`: `TENANT` or `ACCOUNT`.
  - [UNVERIFIED: tenant limit counts (10,000 tenants / 300,000 identities) — from search metadata, not directly verified against official documentation page]
- Cost Profile: Standard SES pricing; no per-tenant surcharge beyond sending volume.
- Automation: EventBridge tenant status changes enable automated application-tier tenant suspension/re-activation.
- Source: [https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-ses-tenant-isolation-automated-reputation-policies]

---

## Reference Architectures

**Transactional Email in a 3-Tier Web Application** 🟡
- Context: Production web application (SaaS, e-commerce, user onboarding, password reset, order confirmation) requiring reliable transactional email delivery with full deliverability observability. [IRRESOLVABLE: No single official AWS reference architecture document for this pattern — synthesized from multiple official SES documentation pages]
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Entry / TLS Termination | ALB + CloudFront | TLS termination, DDoS protection |
  | Application | EC2 / ECS / Lambda | Business logic; triggers SES API v2 with IAM execution role |
  | Send Buffer | Amazon SQS (Standard) | Queue-based load leveling against SES rate limits |
  | Email Sending | Amazon SES (SESv2 API) | Transactional email dispatch |
  | Configuration | SES Configuration Sets | Event publishing, IP pool routing, TLS policy, open/click tracking |
  | Event Processing | Amazon SNS → AWS Lambda | Real-time bounce/complaint processing → suppression list update |
  | Analytics | Amazon Kinesis Data Firehose → S3 | Deliverability event archival and Athena analytics |
  | Suppression | SES Account-Level Suppression List | Prevents resending to hard-bounced/complained addresses |
  | Deliverability Intelligence | VDM (SES Deliverability) | ISP-level metrics dashboard, Advisor |
  | Reputation Alarms | Amazon CloudWatch → SNS → Lambda | Bounce/complaint rate circuit breaker |
  | HA / DR | SES Global Endpoints (MREP) + DEED | Active-active multi-region, auto failover |
  | IP Reputation Isolation | SES Dedicated IP Pools | Separate transactional vs. marketing IP reputation |
  | Secrets Management | AWS Secrets Manager / IAM Roles | Zero static credentials in application code |
  | DNS | Amazon Route 53 | SPF TXT, DKIM CNAME, DMARC TXT, MAIL FROM MX records |

- Key Decisions:
  1. Use SES API v2 (not SMTP) from application code for IAM role auth and CloudTrail visibility.
  2. Always specify a configuration set on every send (or set as default on the identity).
  3. Separate dedicated IP pools for transactional vs. marketing sends to isolate reputation.
  4. Subscribe SNS event destination for Bounce and Complaint events from day one.
  5. Enable VDM SES Deliverability tier at account activation, not retroactively.
  6. Request production access and confirm matching quotas in the secondary MREP region before enabling Global Endpoints.
- Scaling Path: Start with shared IPs (zero additional cost) → migrate to Dedicated IP Managed when consistent volume >50,000/day → add Dedicated IP Standard if ISP allowlisting becomes a requirement → enable Global Endpoints when DR SLA requires multi-region HA.
- Source: Synthesized from [https://docs.aws.amazon.com/ses/latest/dg/] multiple pages

**Multi-Tenant SaaS Sending Platform** 🟢
- Context: A SaaS platform that sends email on behalf of its customers, requiring per-tenant reputation isolation, independent suppression lists, and automated pause/resume.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Tenant Identity Management | SES Tenant Isolation (2025 GA) | Named tenants with dedicated config sets, identities, templates |
  | Reputation Isolation | SES Automated Reputation Policies | Per-tenant auto-pause/resume on threshold breach |
  | Status Events | Amazon EventBridge | Tenant status change events for application integration |
  | Suppression | SES Tenant-Level Suppression Lists (2026 GA) | Per-tenant suppression via TenantName parameter |
  | Cross-Account Delegation | SES Sending Authorization Policies | Grant delegate accounts/services send-from identity rights |
  | Deliverability | VDM SES Deliverability | Per-tenant deliverability segmentation via config sets |
  | Audit | AWS CloudTrail | API-level audit trail (management events by default) |

- Key Decisions: Use Tenant Isolation (GA August 2025) rather than separate SES accounts per tenant to consolidate quota and management overhead. Set reputation policy mode to `Strict` for enterprise tenants with contractual SLA requirements.
- Scaling Path: Tenant Isolation → if per-tenant dedicated IPs needed, use Dedicated IP Standard pools per tenant config set.
- Source: [https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-ses-tenant-isolation-automated-reputation-policies]

---

## Service Equivalence Map

This section is scoped to single-provider (AWS). Cross-provider comparison is included only where it aids architectural decision-making for teams evaluating SES against alternatives.

| Capability | Amazon SES | SendGrid | Mailgun | Notes |
|------------|-----------|---------|---------|-------|
| IAM role-based auth (no static credentials) | Yes (API v2) | No | No | SES differentiator for AWS-native workloads |
| Sending authorization (cross-account) | Yes | No | No | SES differentiator for SaaS |
| Global Endpoints (active-active multi-region) | Yes (MREP) | No | No | SES differentiator |
| VDM Advisor (AI-driven recommendations) | Yes | Partial | No | SES differentiator |
| Inbound email receiving (receipt rules) | Yes | No (MX to webhook) | Yes (routes) | SES more integrated with Lambda/S3 |
| Tenant isolation native | Yes (2025) | No (subaccount) | Subaccount | SES differentiator |
| DKIM 2048-bit Easy DKIM | Yes | Yes | Yes | Parity |
| Global Deliverability (inbox placement) | Yes ($1,250/mo) | Yes (paid) | No | Parity at enterprise tier |
| Pricing per 1K emails | $0.10 | ~$0.85+ | ~$0.80+ | SES significantly cheaper at volume |

---

## Provider Differentiators

**VDM (Virtual Deliverability Manager) — ISP-Level Deliverability Intelligence** 🟢
- SES provides per-ISP, per-identity, per-configuration-set deliverability metrics including inbox placement, spam folder rate, open/click rates (with `isBotEvent` bot filtering as of August 2026), and a proactive Advisor with actionable recommendations. The Global Deliverability tier adds multi-provider inbox placement testing and blocklist monitoring at $1,250/month/region.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/vdm.html]

**IAM Role-Based Authentication (No Static Credentials)** 🟢
- SES API v2 uses standard AWS IAM execution roles (Lambda execution roles, ECS task roles, EC2 instance profiles). No application-level credential management is required. This is not available with SMTP interfaces and is a unique advantage vs. third-party email providers that mandate API keys or SMTP credentials.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/control-user-access.html]

**Sending Authorization for Cross-Account Delegation** 🟢
- SES resource-based authorization policies on verified identities enable multi-account and SaaS architectures where one identity owner grants sending rights to multiple delegate accounts. Reputation and quota are attributed to the delegate's account, not the identity owner's. This pattern is native to SES and not available in third-party providers without custom proxy infrastructure.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/sending-authorization-overview.html]

**Global Endpoints (MREP) with DEED** 🟡
- SES Global Endpoints provide active-active multi-region email sending with automatic traffic shift on regional impairment detection. DEED eliminates the operational burden of publishing per-region DKIM DNS records. No equivalent feature exists in comparable third-party email providers as of August 2026.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/global-endpoints.html]

**Tenant Isolation with Automated Reputation Policies** 🟢
- Native per-tenant reputation isolation within a single SES account, with automated pause/resume based on configurable reputation policy modes (Standard, Strict, None) and EventBridge status change events. This eliminates the need for separate SES accounts per tenant in SaaS architectures.
- Source: [https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-ses-tenant-isolation-automated-reputation-policies]

**Mail Manager — Inbound + Outbound Processing Pipeline** 🟢
- Mail Manager provides Ingress Endpoints (STARTTLS + mTLS for authenticated ingress), rule sets with Invoke Lambda and Bounce actions, archive capability, and third-party add-ons (Vade Advanced Email Security for spam/phishing/malware filtering via AI/ML). This positions SES as a full inbound/outbound email processing platform, not just a sending API.
- Source: [https://aws.amazon.com/about-aws/whats-new/2026/04/ses-mail-manager-introduces-new-features]

**Suppression List (Two-Tier)** 🟢
- SES provides both a global SES-managed suppression list (AWS removes known-bad addresses for up to 14 days) and an account-level customer-managed suppression list. The 2026 addition of tenant-level suppression (per-tenant `TenantName` scoping) makes the suppression system the most granular available among cloud email providers.
- Source: [https://docs.aws.amazon.com/ses/latest/dg/sending-email-suppression-list.html]

**Dedicated IP Pools — Standard and Managed** 🟢
- SES offers two dedicated IP modes: Standard (static IPs, manual warmup) for ISP allowlisting requirements, and Managed (auto-warmup per ISP, auto-scaling) for variable high-volume senders. Managed IPs include IP Observability with CloudWatch Metrics for Microsoft SNDS feedback per IP (GA October 2025).
- Source: [https://docs.aws.amazon.com/ses/latest/dg/dedicated-ip.html]

---

## Scenario Coverage

**Standard Case**: Transactional email for a production web application (user registration, password reset, order confirmation) sending 10K–500K messages/day.
- Approach: SES API v2 (IAM execution role, no static credentials) → default configuration set on verified domain identity → SNS event destination for Bounce/Complaint → Lambda suppression handler → account-level suppression list → CloudWatch alarms on bounce/complaint rates → VDM SES Deliverability for ISP-level visibility → shared IP pool (unless volume warrants Dedicated IP Managed).
- Key Decisions:
  1. Enable Easy DKIM (2048-bit) and configure custom MAIL FROM subdomain before first send.
  2. Confirm DMARC record at `p=none` with rua= reporting address before launch; schedule escalation to `p=quarantine` after 30 days of monitoring.
  3. Configure CloudWatch alarms for `Reputation.BounceRate` ≥5% and `Reputation.ComplaintRate` ≥0.1%.
  4. Request production access at least 3 business days before launch (AWS approval typically within 1 business day but not guaranteed).

**Edge Case**: Multi-region active-active with sub-60-second failover requirement; DR SLA for email sending must match application-tier RTO.
- Approach: SES API v2 + Global Endpoints (MREP). Prerequisites: DEED configured on domain identity, configuration sets duplicated in secondary region, production access and matching quotas in secondary region, application uses SES API v2 (SMTP cannot use Global Endpoints). DNS TTL guidance: positive ~60s, negative ~10s. HTTP connection TTL ~60s. [UNVERIFIED: AWS does not publish guaranteed RTO/RPO values for Global Endpoints — architect must validate with AWS Solutions Architect for SLA requirements.]
  For inbound email in multi-region: SES email receiving is single-region; inbound traffic cannot be made active-active with standard receipt rules. Mail Manager Ingress Endpoints have a region scope. Architect must accept asymmetric HA (outbound = active-active, inbound = single-region) or implement DNS-based region routing with separate inbound endpoints.

**Anti-Pattern Case**: Development team proposes to use SES SMTP with credentials in environment variables, without configuration sets, and without bounce/complaint processing — citing speed of implementation.
- Clarification: Before accepting, architect must ask:
  1. "Do you have a plan for rotating the SMTP credentials when they are inevitably committed to source control?" (SMTP credentials have no in-place rotation.)
  2. "How will you detect and act on bounce/complaint rate increases?" (No configuration set = no event destination = no visibility.)
  3. "Have you confirmed production access is in place and the daily sending quota covers peak load?" (Sandbox limits will silently drop messages above 200/day.)
  4. "Is SMTP a hard requirement, or is the SES SDK available in your runtime?" (If SDK is available, API v2 with IAM role eliminates all three concerns.)
  
  Correct path: SES API v2 with IAM execution role + configuration set with SNS Bounce/Complaint event destination + account-level suppression list enabled. If SMTP is unavoidable (legacy software), store credentials in AWS Secrets Manager with a rotation Lambda.

---

## Research Iteration Changelog

> Mandatory when `RESEARCH_DEPTH` is `standard`, `deep`, or `exhaustive`.

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Changelog | SES Pricing Plans — Three-Tier Model (Essentials/Pro/Enterprise) | Added — GA July 21, 2026 | https://aws.amazon.com/about-aws/whats-new/2026/07/amazon-ses-pricing-plans/ (2026-07-21) |
| 1 | Changelog | Bot/Automated Interaction Detection — `isBotEvent` field | Added — GA August 7, 2026 | https://aws.amazon.com/about-aws/whats-new/2026/08/amazon-ses-automated-email-interactions/ (2026-08-07) |
| 1 | Changelog | Inbox Placement Metrics and Blocklist Monitoring (VDM extension) | Added — GA May 29, 2026 | https://aws.amazon.com/about-aws/whats-new/2026/05/amazon-ses-global-deliverability/ (2026-05-29) |
| 1 | Changelog | Tenant-Level Suppression Lists — `TenantName` API parameter | Added — GA June 1, 2026; API change to 4 suppression APIs | https://aws.amazon.com/about-aws/whats-new/2026/06/amazon-ses-tenant-level-suppression-lists/ (2026-06-01) |
| 1 | Changelog | SES Mail Manager — Invoke Lambda, Bounce actions; STARTTLS + mTLS Ingress | Added — GA April 1, 2026 | https://aws.amazon.com/about-aws/whats-new/2026/04/ses-mail-manager-introduces-new-features (2026-04-01) |
| 1 | Changelog | Tenant Isolation with Automated Reputation Policies | Added — GA August 1, 2025 | https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-ses-tenant-isolation-automated-reputation-policies (2025-08-01) |
| 1 | Changelog | IP Observability for Dedicated IP (Managed) + SNDS CloudWatch Metrics | Added — GA October 21, 2025 | https://aws.amazon.com/about-aws/whats-new/2025/10/amazon-ses-ip-observability-dedicated-op-addresses-managed/ (2025-10-21) |
| 1 | Changelog | Vade Advanced Email Security Add-On for Mail Manager | Added — GA March 21, 2025 | https://aws.amazon.com/about-aws/whats-new/2025/03/amazon-ses-advanced-email-security-add-on/ (2025-03-21) |
| 1 | Changelog | VDM Tiered Pricing | Added — GA February 14, 2025 | https://aws.amazon.com/about-aws/whats-new/2025/02/amazon-ses-tiered-pricing-virtual-deliverability-manager/ (2025-02-14) |
| 1 | Changelog | Mail Manager Regional Expansion to 17 Regions | Added — GA January 30, 2025 | https://aws.amazon.com/about-aws/whats-new/2025/01/ses-mail-manager-available-new-regions/ (2025-01-30) |
| 1 | Changelog | Gmail and Yahoo Bulk Sender Requirements (mandatory Feb/June 2024) | Added — ongoing enforcement baseline | https://aws.amazon.com/blogs/messaging-and-targeting/navigate-bulk-sender-requirements-with-amazon-ses (2024) |
| 1 | Changelog | Microsoft Bulk Sender Requirements (enforced May 5, 2025) | Added — senders >5K msgs/day to Outlook/Hotmail/live.com | https://aws.amazon.com/blogs/messaging-and-targeting/navigate-bulk-sender-requirements-with-amazon-ses (2025) |
| 2 | Changelog | SES API v1 formal deprecation timeline | ⚠️ IRRESOLVABLE — no official deprecation notice found as of August 2026 | — |
| 2 | Security | S3 receipt rule encryption at rest in SES | ⚠️ IRRESOLVABLE — configured at S3 bucket level, not documented in SES-specific pages | — |
| 2 | Security | VPC endpoint policies for SES endpoints | ⚠️ IRRESOLVABLE — not documented in SES-specific VPC endpoint documentation | — |
| 2 | Security | SES-specific SCP patterns | ⚠️ IRRESOLVABLE — found only in AWS Organizations documentation, not SES | — |
| 2 | Security | DKIM automatic rotation schedule | ⚠️ IRRESOLVABLE — no officially documented automatic rotation frequency | — |
| 2 | Design Patterns | SES-specific TooManyRequestsException Lambda handling | ⚠️ IRRESOLVABLE — no single official SES documentation page covers this | — |
| 2 | Design Patterns | SES v2 native `ClientToken` idempotency parameter | ⚠️ UNVERIFIED — not confirmed in fetched documentation pages | — |
| 2 | Changelog | One-click unsubscribe SES-native header injection | ⚠️ IRRESOLVABLE — whether SES auto-adds `List-Unsubscribe-Post` headers not confirmed from official page | — |
| 3 | Operational | Tenant limit counts (10,000 tenants / 300,000 identities) | ⚠️ UNVERIFIED — from search metadata only, not directly verified | — |
| 3 | Operational | Dedicated IP Standard — minimum 256 IP requirement | ⚠️ UNVERIFIED — from pricing page extraction, not directly verified | — |
| 3 | Operational | RTO/RPO SLAs for Global Endpoints | ⚠️ UNVERIFIED — AWS documents DNS TTL guidance only, not guaranteed RTO/RPO | — |
| 4 | Reference Architectures | Official 3-tier reference architecture document | ⚠️ IRRESOLVABLE — no single official AWS document; synthesized from multiple SES documentation pages | — |
