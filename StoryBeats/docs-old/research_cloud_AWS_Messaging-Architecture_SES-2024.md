# AWS SES — Messaging Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS SES — Messaging Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "Messaging Architecture"
Target_Edition: "AWS SES 2024"
Architecture_Context: "Applications requiring transactional and marketing email sending — covering email delivery, sender reputation management, bounce/complaint handling, email authentication (SPF/DKIM/DMARC), email receiving and processing, configuration sets, event publishing, dedicated IP management, Virtual Deliverability Manager, and Mail Manager"
Official_Source_URL: "https://docs.aws.amazon.com/ses/latest/dg/Welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to SES feature updates, regional expansion, and Mail Manager evolution"
```

---

## Executive Summary

Amazon Simple Email Service (Amazon SES) is AWS's cloud-based email platform that provides a cost-effective, scalable infrastructure for sending and receiving email. SES supports both transactional email (order confirmations, password resets, notifications) and marketing email (campaigns, newsletters, promotional content) via the SES v2 API, SMTP interface, or console. SES handles underlying mail server management, network configuration, IP address reputation, and ISP relationship management — eliminating the operational complexity of self-hosted email infrastructure. The service operates on a pay-per-use model ($0.10 per 1,000 emails sent, with the first 62,000 emails/month free when sent from EC2) and is available in multiple AWS Regions, with each region maintaining independent identity verification, sending quotas, SMTP credentials, and suppression lists.

The 2024 edition's most architecturally significant advances are: (1) **Mail Manager** — a comprehensive email gateway feature set providing ingress endpoints, traffic policies, rule sets, SMTP relay, email archiving, and third-party Email Add Ons for advanced inbound email processing and compliance; (2) **Virtual Deliverability Manager (VDM)** — an AI-powered deliverability optimization feature providing a dashboard with ISP-level insights (delivery rates, bounce/complaint rates, engagement metrics per sending identity and configuration set) and an advisor that flags infrastructure problems (missing SPF/DKIM/DMARC records, short DKIM key lengths) with actionable remediation guidance; (3) **SES v2 API with 40 MB message size support** — expanding from the v1 API's 10 MB limit, enabling large attachment workflows without S3 pre-staging; (4) **Account-level and configuration-set-level suppression lists** — granular control over which addresses are suppressed for bounces, complaints, or both, with per-configuration-set override capability. These changes position SES as a full-featured email platform supporting both high-volume sending with deliverability intelligence and sophisticated inbound email processing with compliance archival.

The three most critical architecture guardrails for SES are: (1) **always implement SPF, DKIM, and DMARC authentication on all sending domains** — without proper email authentication, messages are increasingly rejected or spam-foldered by major ISPs (Google, Microsoft, Yahoo all require DMARC alignment as of 2024); (2) **configure event publishing via configuration sets to monitor bounces, complaints, and deliveries** — without event tracking, reputation damage is invisible until SES pauses sending capability; (3) **enable the account-level suppression list for both bounces and complaints** — sending to addresses that have previously bounced or complained damages sender reputation and can trigger SES account suspension.

---

## Cloud Architecture Glossary

```
Term: Verified Identity
Definition: A domain or email address that you have proven ownership of to Amazon SES. Verification is required before SES allows sending from that identity. Domain verification uses DNS records (CNAME for DKIM, TXT for SPF/custom MAIL FROM). Email address verification uses a confirmation link. Verification is per-region — an identity verified in us-east-1 is not verified in eu-west-1.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/verify-addresses-and-domains.html
Architect Usage: Always verify at the domain level (not individual email addresses) for production. Domain verification enables sending from any address at that domain. Use email-level verification only for sandbox testing. Verified identities are the fundamental trust boundary in SES — they determine who can send email and from which addresses.
Common Confusion: Verifying a domain does NOT configure email authentication (DKIM/SPF). Verification proves ownership; authentication (Easy DKIM, custom MAIL FROM) must be configured separately. Also, verification in one region does not carry to other regions.

Term: Configuration Set
Definition: A named group of rules applied to emails sent through SES. Configuration sets contain event destinations (where to publish sending metrics), IP pool assignments (which dedicated IPs to use), suppression list overrides, and sending options (TLS enforcement, reputation metrics tracking). A configuration set is specified per email at send time or as a default on a verified identity.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/using-configuration-sets.html
Architect Usage: Use configuration sets to segment sending behavior by email type (transactional vs marketing), by application, or by business unit. Each configuration set can have up to 10 event destinations publishing to CloudWatch, SNS, Firehose, or EventBridge. Assign default configuration sets to verified identities so that all email from that identity automatically uses the configuration set without requiring per-send specification. Maximum 10,000 configuration sets per region.
Common Confusion: Configuration sets are NOT required to send email — they are optional but strongly recommended for production. Without a configuration set, you cannot use event publishing, dedicated IP pools, or configuration-set-level suppression overrides. A configuration set is not a "sending profile" — it does not control the From address or content.

Term: Sandbox
Definition: The initial state of every new SES account in each AWS Region. In sandbox mode, sending is restricted to: 200 emails per 24-hour period, 1 email per second sending rate, and recipients must be verified email addresses or domains. To send to unverified recipients at production volumes, you must request production access (sandbox removal) per region.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html
Architect Usage: Sandbox removal is per-region. Plan for this in deployment timelines — approval can take 24-48 hours. For multi-region deployments, submit production access requests for all target regions simultaneously. Use the SES mailbox simulator for testing in sandbox without consuming quota or affecting reputation.
Common Confusion: Sandbox status is independent per region. Being out of sandbox in us-east-1 does NOT remove sandbox in eu-west-1. Also, production access does not grant unlimited sending — quotas increase gradually based on sending quality and volume patterns.

Term: Sending Quota
Definition: Two limits that govern how much email you can send: (1) Daily sending quota — maximum number of emails (counted per recipient) in a 24-hour period; (2) Maximum send rate — maximum number of emails per second. Both are per-region and increase automatically as SES observes consistent, high-quality sending patterns.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/quotas.html
Architect Usage: Monitor quotas via GetAccount API or CloudWatch Reputation.DailySendingQuota metric. Design applications to handle throttling (HTTP 454 or Throttling exception). For burst capacity needs, request quota increases in advance through AWS Support. SES counts recipients, not messages — an email with 10 recipients counts as 10 toward your quota.
Common Confusion: Sending quota is per-recipient, not per-API call. An email to 50 recipients (the maximum per message) counts as 50 sends. Also, quota increases are not instant — they happen gradually based on demonstrated sending quality (low bounces, low complaints, consistent volume).

Term: Bounce
Definition: A failed email delivery. Hard bounce: permanent failure (address doesn't exist, domain doesn't exist). Soft bounce: temporary failure (mailbox full, server unavailable — SES retries for up to 72 hours). Hard bounces damage sender reputation and should trigger address removal. SES distinguishes bounce types in notification payloads.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/send-email-concepts-process.html
Architect Usage: Hard bounce rate must stay below 5% (SES review threshold) and ideally below 2%. Addresses that hard-bounce should be immediately suppressed (account-level suppression list handles this automatically when enabled). Monitor Reputation.BounceRate in CloudWatch. Design systems to process bounce notifications and remove invalid addresses from mailing lists.
Common Confusion: SES counts hard bounces toward your bounce rate metric. Soft bounces that ultimately fail (after SES retry exhaustion) are reported as hard bounces in event notifications. The account-level suppression list only captures hard bounces (not soft bounces). Gmail does not provide complaint feedback to SES.

Term: Complaint
Definition: A recipient marking your email as spam/junk in their email client. ISPs that participate in feedback loops (FBL) report complaints back to SES. Complaints are a strong negative reputation signal — a complaint rate above 0.1% triggers SES review, and above 0.5% may pause sending.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/send-email-concepts-process.html
Architect Usage: Complaint rate must stay below 0.1% (SES review threshold). Process complaint notifications to immediately unsubscribe the recipient — continuing to send to complainers compounds reputation damage. Use List-Unsubscribe headers to give recipients an alternative to marking as spam. Not all ISPs provide complaint feedback — Gmail notably does NOT report complaints to SES.
Common Confusion: Gmail does not participate in SES feedback loops — you will NOT receive complaint notifications for Gmail recipients marking you as spam. This makes Gmail reputation opaque. Yahoo, Outlook/Hotmail, and AOL do provide complaint feedback. Complaint rate is calculated only from recipients whose ISPs report complaints, which biases the metric.

Term: DKIM (DomainKeys Identified Mail)
Definition: An email authentication mechanism that allows the receiver to verify that an email was authorized by the domain owner. SES supports Easy DKIM (SES generates and manages DKIM keys, you publish CNAME records) and BYODKIM (you provide your own DKIM signing key). DKIM signing adds a cryptographic signature to email headers that receivers validate against DNS-published public keys.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim.html
Architect Usage: Always enable DKIM on all sending domains — it is a prerequisite for DMARC compliance. Use Easy DKIM with 2048-bit keys (default since 2024). DKIM configuration is per-region. The Virtual Deliverability Manager advisor flags domains with missing or weak (1024-bit) DKIM. For high-security requirements, use BYODKIM with customer-managed key rotation.
Common Confusion: Easy DKIM CNAME records are published once in DNS but are region-specific — each SES region generates different CNAME values. The DKIM domain may be region-specific (not always dkim.amazonses.com). DKIM alone does not prevent spoofing — you need DMARC alignment (DKIM domain must match From domain or organizational domain).

Term: SPF (Sender Policy Framework)
Definition: An email authentication mechanism that allows receiving servers to verify that email from a domain was sent from an authorized IP address. For SES, SPF is configured via a custom MAIL FROM domain that publishes an SPF TXT record authorizing SES IP ranges (include:amazonses.com). Without custom MAIL FROM, SES uses its own MAIL FROM domain (amazonses.com), which passes SPF but does not align with your From domain for DMARC purposes.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-spf.html
Architect Usage: Configure a custom MAIL FROM domain (e.g., mail.yourdomain.com) to achieve SPF alignment for DMARC. Publish an MX record pointing to the SES feedback endpoint and a TXT record with SPF authorization. Without custom MAIL FROM, SPF passes but DMARC alignment via SPF fails (the MAIL FROM domain is amazonses.com, not yourdomain.com). DKIM alignment alone satisfies DMARC, but both SPF and DKIM alignment provide defense-in-depth.
Common Confusion: Simply adding an SPF record to your root domain does NOT work for SES — SPF validates the MAIL FROM domain (envelope sender), not the From header domain. You need a custom MAIL FROM subdomain with its own SPF record. Many architects confuse "SPF passes" with "SPF aligns for DMARC" — they are different checks.

Term: DMARC (Domain-based Message Authentication, Reporting, and Conformance)
Definition: An email authentication policy that builds on SPF and DKIM to prevent domain spoofing. DMARC requires alignment — either SPF or DKIM must authenticate AND align with the From header domain. DMARC policies (none, quarantine, reject) tell receivers what to do with messages that fail alignment. As of 2024, Google and Yahoo require DMARC for bulk senders.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html
Architect Usage: Deploy DMARC in phases: p=none (monitor), p=quarantine (soft enforcement), p=reject (full enforcement). For SES, achieve DMARC alignment via DKIM (Easy DKIM with your domain) and/or SPF (custom MAIL FROM domain). Always configure DMARC reporting (rua/ruf tags) to receive aggregate and forensic reports. As of Feb 2024, Google/Yahoo require DMARC for senders exceeding 5,000 messages/day.
Common Confusion: DMARC is NOT something you configure in SES — it is a DNS TXT record on your domain (_dmarc.yourdomain.com) that instructs receivers. SES provides the mechanisms (DKIM, custom MAIL FROM) to achieve DMARC alignment. A p=none DMARC policy does NOT block anything — it only monitors.

Term: Dedicated IP Address
Definition: An IP address leased exclusively for your SES sending (vs shared IPs used by default). Dedicated IPs give full reputation control but require IP warm-up and sufficient volume to maintain reputation (minimum ~10,000 emails/day recommended). Available as Standard Dedicated IPs ($24.95/month per IP, manual warm-up) or Managed Dedicated IPs ($15/month per IP, automatic warm-up and scaling).
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/dedicated-ip.html
Architect Usage: Use dedicated IPs when: sending volume > 100K emails/day, need reputation isolation between email types (marketing vs transactional), compliance requires known/fixed IP addresses, or need IP warm-up control. Use shared IPs for low-volume senders (< 10K/day) where shared reputation is beneficial. Managed Dedicated IPs handle warm-up and scaling automatically — prefer over Standard for most use cases.
Common Confusion: Dedicated IPs require warm-up — you cannot immediately send at full volume. New dedicated IPs have no reputation and will be throttled by ISPs. Managed Dedicated IPs automate this but Standard requires manual warm-up over 2-6 weeks. Also, having dedicated IPs does not improve deliverability by itself — it gives you reputation isolation, which can be good or bad depending on your sending quality.

Term: Account-Level Suppression List
Definition: A per-region list of email addresses that SES will not attempt to deliver to. Addresses are automatically added when hard bounces or complaints occur (configurable for one or both). SES accepts the send API call but suppresses delivery — the send counts toward daily quota but not toward bounce/complaint reputation metrics.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/sending-email-suppression-list.html
Architect Usage: Enable the account-level suppression list with both BOUNCE and COMPLAINT reasons. This is the first line of defense against reputation damage from known-bad addresses. Suppression is per-region. Accounts created after November 2019 have suppression enabled by default. Suppression list entries persist until manually removed. Monitor suppression list growth as an indicator of list quality.
Common Confusion: SES has TWO suppression lists: the Global Suppression List (maintained by AWS across all accounts — addresses that have recently bounced from any SES sender) and the Account-Level Suppression List (your account's private list). They operate independently. Being on the account list means SES accepts but doesn't deliver; being on the global list means the same but is shared across all SES users.

Term: Virtual Deliverability Manager (VDM)
Definition: An SES feature that provides deliverability insights and recommendations. VDM Dashboard shows sending metrics at account, ISP, sending identity, and configuration set levels (delivery rates, bounce rates, open rates, click rates). VDM Advisor flags infrastructure issues (missing authentication records, DKIM key length, suppression configuration) with remediation guidance.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/vdm.html
Architect Usage: Enable VDM on all production SES accounts. VDM provides ISP-level visibility that raw metrics cannot — you can see if Gmail is accepting your email at a different rate than Outlook. Use VDM Advisor recommendations to proactively fix deliverability issues before they impact sending. VDM incurs additional cost per email ($0.0007 per message for engagement tracking).
Common Confusion: VDM engagement tracking (opens, clicks) requires enabling at both account level AND per configuration set or identity. VDM is NOT the same as event publishing — VDM aggregates insights for the dashboard, while event publishing delivers per-message events to your destinations. Both should be enabled for complete observability.

Term: Mail Manager
Definition: A set of SES email gateway features for inbound email processing, including: Ingress Endpoints (receive email from the internet), Traffic Policies (allow/deny based on sender IP, authentication results), Rule Sets (route, archive, relay, or process email based on conditions), SMTP Relay (forward to other SMTP servers), Email Archiving (long-term storage with search), and Email Add Ons (third-party security integrations).
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/eb.html
Architect Usage: Use Mail Manager for sophisticated inbound email workflows that exceed the capabilities of basic SES receipt rules. Mail Manager provides enterprise-grade email routing, compliance archiving (with search and export), and integration with third-party security scanning. It replaces the need for self-hosted email gateways (Postfix, Exchange Edge Transport) for inbound processing. Maximum 10 open ingress endpoints, 50 authorized ingress endpoints per account.
Common Confusion: Mail Manager is NOT required for basic email receiving — SES receipt rules (the legacy mechanism) still work for simple S3/SNS/Lambda routing. Mail Manager is the evolution for organizations needing advanced routing, archiving, and security scanning. Mail Manager ingress endpoints have their own DNS (MX records), separate from legacy SES receipt rule endpoints.

Term: Event Destination
Definition: A component of a configuration set that specifies where SES publishes email sending events (sends, deliveries, bounces, complaints, opens, clicks, rejects, delivery delays, subscriptions, rendering failures). Supported destinations: Amazon CloudWatch, Amazon SNS, Amazon Data Firehose, and Amazon EventBridge. Maximum 10 event destinations per configuration set.
Provider Docs Section: https://docs.aws.amazon.com/ses/latest/dg/event-destinations-manage.html
Architect Usage: Configure at minimum a CloudWatch event destination for operational metrics (sends, deliveries, bounces, complaints) and an SNS destination for real-time bounce/complaint processing. Use Firehose for detailed per-event analytics (piped to S3/Redshift/OpenSearch). Use EventBridge for triggering automated workflows on specific events. Always track bounces and complaints — they are the primary reputation indicators.
Common Confusion: Event destinations only fire when a configuration set is specified (or defaulted) on the email being sent. If no configuration set is associated, no events are published to event destinations. Also, "feedback notifications" (the legacy mechanism via SNS on verified identities) and "event publishing" (via configuration sets) are independent systems — you can use one or both.
```

---

## Architecture Framework Analysis: AWS Well-Architected — Email Messaging Pillar Alignment

```
Pillar: Reliability
Definition: The ability of a workload to perform its intended function correctly and consistently when it's expected to.
Key Design Principles:
  - Automatically recover from failure (process bounces to clean lists, use suppression lists for automatic protection)
  - Test recovery procedures (use SES mailbox simulator for bounce/complaint testing without reputation impact)
  - Scale horizontally (SES scales automatically, sending quotas increase with demonstrated quality)
  - Manage change in automation (IaC for identities, configuration sets, event destinations, DKIM/SPF records)
Applies To Email Messaging: SES provides automatic retry for soft bounces (up to 72 hours), account-level suppression to prevent delivery to known-bad addresses, and gradual quota increases tied to sending quality. Multi-region deployment enables failover if one SES region experiences issues. The mailbox simulator enables testing without impacting production reputation.
Assessment Questions:
  1. Are bounces and complaints processed in real-time to remove invalid/unwilling recipients from mailing lists?
  2. Is the account-level suppression list enabled for both bounces and complaints?
  3. Is there a multi-region failover strategy for critical transactional email?
Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html

Pillar: Security
Definition: The ability to protect data, systems, and assets while delivering business value through risk assessments and mitigation strategies.
Key Design Principles:
  - Apply security at all layers (email authentication SPF/DKIM/DMARC, IAM policies for SES API access, TLS enforcement)
  - Enable traceability (CloudTrail for SES API calls, event publishing for sending activity)
  - Implement least privilege (IAM policies restricting ses:SendEmail to specific identities and configuration sets)
  - Protect data in transit (TLS enforcement on SMTP connections, HTTPS-only API calls)
Applies To Email Messaging: Email authentication (SPF, DKIM, DMARC) prevents domain spoofing and improves deliverability. IAM policies must restrict which principals can send email from which identities. Sending authorization policies enable controlled cross-account sending. TLS enforcement (RequireTls in configuration sets) ensures message confidentiality in transit. SMTP credentials must be rotated and treated as secrets.
Assessment Questions:
  1. Are SPF, DKIM (2048-bit), and DMARC configured on all sending domains with DMARC policy at least p=quarantine?
  2. Are IAM policies restricted to specific ses:SendEmail actions with condition keys for ses:FromAddress and ses:Recipients?
  3. Is TLS enforcement enabled for all outbound SMTP connections via configuration sets?
Source: https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication.html

Pillar: Performance Efficiency
Definition: The ability to use computing resources efficiently to meet system requirements and to maintain that efficiency as demand changes.
Key Design Principles:
  - Use managed services (SES eliminates self-hosted MTA infrastructure — Postfix, SendGrid self-hosted)
  - Experiment more often (SES mailbox simulator for load testing without reputation impact)
  - Consider mechanical sympathy (batch sending via SendBulkEmail, template pre-compilation, appropriate message size)
Applies To Email Messaging: Use SendBulkEmail for high-volume campaigns (up to 50 destinations per call). Use email templates for repeated content to reduce payload size and enable server-side rendering. Choose SES v2 API over SMTP for programmatic sending (lower latency, batch support). Size messages appropriately — messages > 10 MB are subject to bandwidth throttling.
Assessment Questions:
  1. Are bulk sends using SendBulkEmail API with templates rather than individual SendEmail calls?
  2. Is the SES v2 API used for programmatic sending rather than SMTP (unless integrating legacy systems)?
  3. Are message sizes optimized to avoid bandwidth throttling (< 10 MB for high-throughput)?
Source: https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/welcome.html

Pillar: Cost Optimization
Definition: The ability to run systems to deliver business value at the lowest price point.
Key Design Principles:
  - Adopt a consumption model (SES charges $0.10 per 1,000 emails — pay only for what you send)
  - Measure overall efficiency (cost per delivered email, cost per engagement)
  - Analyze and attribute expenditure (configuration sets for per-use-case tracking, tagging)
Applies To Email Messaging: First 62,000 emails/month free when sent from EC2. Use shared IPs for low-volume (< 10K/day) to avoid dedicated IP costs ($24.95/mo per IP). Use suppression lists to avoid paying for emails that won't deliver. Monitor VDM additional costs ($0.0007/message for engagement tracking). Clean mailing lists regularly to avoid sending to disengaged recipients (wasted cost + reputation harm).
Assessment Questions:
  1. Are dedicated IPs justified by volume and reputation isolation needs, or are shared IPs sufficient?
  2. Is VDM engagement tracking cost-justified for the sending volume?
  3. Are mailing lists regularly cleaned to remove disengaged recipients (reducing wasted sends)?
Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html

Pillar: Operational Excellence
Definition: The ability to support development and run workloads effectively, gain insight into operations, and continuously improve.
Key Design Principles:
  - Perform operations as code (IaC for SES identities, configuration sets, DKIM records, event destinations)
  - Make frequent, small, reversible changes (gradual IP warm-up, phased DMARC enforcement)
  - Anticipate failure (bounce/complaint monitoring with CloudWatch alarms, quota monitoring)
  - Learn from operational failures (VDM dashboard analysis, bounce reason categorization)
Applies To Email Messaging: All SES configurations must be IaC-managed (CloudFormation/Terraform). Configure CloudWatch alarms on Reputation.BounceRate (> 5%) and Reputation.ComplaintRate (> 0.1%). Use VDM dashboard for trend analysis. Implement automated bounce processing to maintain list hygiene. Monitor sending quotas to prevent throttling during campaigns.
Assessment Questions:
  1. Are all SES configurations (identities, configuration sets, event destinations) managed via Infrastructure as Code?
  2. Are CloudWatch alarms configured on Reputation.BounceRate and Reputation.ComplaintRate thresholds?
  3. Is there an automated pipeline for processing bounce/complaint notifications and updating mailing lists?
Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html

Pillar: Sustainability
Definition: Minimizing the environmental impact of running cloud workloads.
Key Design Principles:
  - Minimize unnecessary processing (suppression lists prevent sending to known-bad addresses)
  - Use managed services (SES eliminates self-hosted email server infrastructure)
  - Maximize utilization (batch sending reduces per-message overhead)
Applies To Email Messaging: Suppression lists eliminate network/compute waste from sending to addresses that will bounce. List hygiene reduces email volume to disengaged recipients. Template-based sending reduces redundant payload transmission. Shared IPs (default) maximize infrastructure utilization across SES customers.
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Email Authentication: SPF + DKIM + DMARC on All Sending Domains**
- Pillar Alignment: Security, Reliability
- Why: As of February 2024, Google and Yahoo require DMARC-aligned authentication for bulk senders (> 5,000 messages/day). Without DKIM and aligned SPF, email is increasingly rejected or spam-foldered by major ISPs. DMARC prevents domain spoofing — protecting brand reputation and recipients from phishing using your domain.
- AWS Services: Amazon SES (Easy DKIM, custom MAIL FROM domain), Amazon Route 53 (DNS records), Virtual Deliverability Manager (advisor alerts)
- Architecture Decision:
  1. Enable Easy DKIM with 2048-bit keys on all verified domain identities (SES generates CNAME records to publish in DNS). 2. Configure a custom MAIL FROM subdomain (e.g., `mail.yourdomain.com`) with MX record pointing to SES feedback endpoint and TXT record with `v=spf1 include:amazonses.com ~all`. 3. Publish DMARC DNS record at `_dmarc.yourdomain.com` — start with `p=none` for monitoring, advance to `p=quarantine`, then `p=reject`. 4. Enable DMARC reporting (rua tag) to receive aggregate authentication reports.
- Verification:
  ```bash
  # Verify DKIM is enabled and passing
  aws sesv2 get-email-identity --email-identity yourdomain.com
  # Check DkimAttributes.Status = "SUCCESS" and DkimAttributes.SigningKeyLength = "RSA_2048_BIT"

  # Verify custom MAIL FROM
  aws sesv2 get-email-identity --email-identity yourdomain.com
  # Check MailFromAttributes.MailFromDomain is set and MailFromAttributes.MailFromDomainStatus = "SUCCESS"

  # Verify DMARC record externally
  dig TXT _dmarc.yourdomain.com
  ```
- Trade-offs: DMARC with p=reject blocks all email not passing alignment — ensure all legitimate sending sources (marketing platforms, SaaS tools) are accounted for before enforcement. Custom MAIL FROM requires additional DNS records per region.
- Source: https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html

**Account-Level Suppression List Enabled for Bounces and Complaints**
- Pillar Alignment: Reliability, Operational Excellence
- Why: Continuing to send to addresses that have previously hard-bounced or complained damages sender reputation. SES will pause sending capability if bounce rate exceeds 10% or complaint rate exceeds 0.5%. The account-level suppression list automatically prevents delivery to known-bad addresses without application-level logic.
- AWS Services: Amazon SES (account-level suppression list, configuration-set-level overrides)
- Architecture Decision:
  Enable account-level suppression for both BOUNCE and COMPLAINT reasons. Leave enabled for all configuration sets unless there is a specific, justified override (e.g., a re-engagement campaign configuration set that overrides suppression for previously complained addresses — high risk, requires explicit business justification). Monitor suppression list growth as a list quality indicator.
- Verification:
  ```bash
  aws sesv2 get-account
  # Check SuppressionAttributes.SuppressedReasons includes both "BOUNCE" and "COMPLAINT"
  ```
- Trade-offs: Suppressed sends still count toward daily sending quota (but not reputation metrics). Addresses remain suppressed indefinitely until manually removed — legitimate addresses suppressed due to temporary issues (e.g., mailbox full that became a hard bounce) require manual investigation.
- Source: https://docs.aws.amazon.com/ses/latest/dg/sending-email-suppression-list.html

**Configuration Sets with Event Publishing on All Production Sending**
- Pillar Alignment: Operational Excellence, Security
- Why: Without event publishing, you have no visibility into per-email delivery outcomes. Reputation damage (rising bounces, complaints) is invisible until SES dashboard metrics breach thresholds or sending is paused. Event publishing enables real-time bounce/complaint processing, delivery confirmation, and engagement tracking.
- AWS Services: Amazon SES (configuration sets, event destinations), Amazon CloudWatch (metrics), Amazon SNS (real-time notifications), Amazon Data Firehose (detailed analytics)
- Architecture Decision:
  Create configuration sets per email type (transactional, marketing, notifications). Configure event destinations: (1) CloudWatch for aggregate metrics (bounces, complaints, deliveries, sends — used for alarms), (2) SNS for real-time bounce/complaint processing (triggers Lambda to update recipient lists), (3) Firehose for detailed event analytics (pipe to S3 for historical analysis). Assign a default configuration set to each verified identity so all sending is tracked.
- Verification:
  ```bash
  # List configuration sets
  aws sesv2 list-configuration-sets

  # Check event destinations for a configuration set
  aws sesv2 get-configuration-set --configuration-set-name transactional
  # Verify EventDestinations array is non-empty with appropriate event types

  # Check default configuration set on identity
  aws sesv2 get-email-identity --email-identity yourdomain.com
  # Check ConfigurationSetName is set
  ```
- Trade-offs: CloudWatch event destination has per-metric cost. SNS delivery adds small latency to event processing. Firehose adds data transfer and storage costs. Without event publishing, monitoring is limited to account-level aggregate metrics (insufficient for root-cause analysis).
- Source: https://docs.aws.amazon.com/ses/latest/dg/monitor-using-event-publishing.html

**Bounce and Complaint Rate Monitoring with CloudWatch Alarms**
- Pillar Alignment: Operational Excellence, Reliability
- Why: SES sends a warning when bounce rate exceeds 5% and may pause sending at 10%. For complaints, warning at 0.1% and pause at 0.5%. Without proactive monitoring, reputation degradation is detected only when SES intervenes (account review or sending pause) — by which point significant damage has occurred.
- AWS Services: Amazon SES (reputation metrics), Amazon CloudWatch (alarms), Amazon SNS (alarm notifications)
- Architecture Decision:
  Configure CloudWatch alarms on SES reputation metrics: (1) `Reputation.BounceRate > 0.03` (3%) — WARNING, investigate immediately; (2) `Reputation.BounceRate > 0.05` (5%) — CRITICAL, pause marketing sending until resolved; (3) `Reputation.ComplaintRate > 0.001` (0.1%) — CRITICAL, investigate content/targeting immediately. Route alarms to on-call via SNS → PagerDuty/Slack.
- Verification:
  ```bash
  aws cloudwatch describe-alarms --alarm-name-prefix "SES-"
  # Verify alarms exist for Reputation.BounceRate and Reputation.ComplaintRate
  ```
- Trade-offs: Aggressive alarm thresholds may cause noise for senders with small volumes (statistical variance in small samples). For accounts sending < 1,000 emails/day, a single bounce can spike the rate — consider absolute count alarms in addition to rate alarms.
- Source: https://docs.aws.amazon.com/ses/latest/dg/monitor-sender-reputation.html

**TLS Enforcement for Outbound Email**
- Pillar Alignment: Security
- Why: Without TLS enforcement, email may be delivered in plaintext between SES and the recipient's mail server if the receiving server does not support STARTTLS. TLS enforcement (RequireTls) ensures SES only delivers email over encrypted connections — if the receiver cannot negotiate TLS, delivery fails rather than sending in plaintext.
- AWS Services: Amazon SES (configuration set TLS policy)
- Architecture Decision:
  Set `TlsPolicy: REQUIRE` on configuration sets used for sensitive email (password resets, financial notifications, personal data). Use `TlsPolicy: OPTIONAL` (default) for marketing email where deliverability trumps encryption guarantee — most major ISPs support TLS, but some smaller domains may not.
- Verification:
  ```bash
  aws sesv2 get-configuration-set --configuration-set-name transactional
  # Check DeliveryOptions.TlsPolicy = "REQUIRE"
  ```
- Trade-offs: REQUIRE may cause delivery failure to recipient mail servers that don't support TLS (rare for major ISPs but possible for small/legacy domains). For transactional email where delivery is critical AND content is not sensitive, OPTIONAL may be appropriate.
- Source: https://docs.aws.amazon.com/ses/latest/dg/creating-configuration-sets.html

**IAM Least-Privilege for SES Sending**
- Pillar Alignment: Security
- Why: Unrestricted `ses:SendEmail` or `ses:SendRawEmail` permissions allow a compromised or misconfigured application to send email from any verified identity in the account — enabling phishing from your domain, spam that destroys your reputation, or data exfiltration via email.
- AWS Services: Amazon SES (IAM condition keys), AWS IAM (policies)
- Architecture Decision:
  Use IAM condition keys to restrict sending: `ses:FromAddress` (limits which From addresses the principal can use), `ses:Recipients` (limits who can be emailed), `ses:FeedbackAddress` (limits Return-Path). Grant only `ses:SendEmail` or `ses:SendRawEmail` — never `ses:*`. Use resource-level permissions with identity ARNs where possible. For cross-account sending, use SES sending authorization policies rather than broad IAM cross-account access.
  ```json
  {
    "Effect": "Allow",
    "Action": ["ses:SendEmail", "ses:SendRawEmail"],
    "Resource": "arn:aws:ses:us-east-1:123456789012:identity/yourdomain.com",
    "Condition": {
      "StringLike": {
        "ses:FromAddress": "*@yourdomain.com"
      }
    }
  }
  ```
- Verification:
  ```bash
  # Review IAM policies attached to SES-sending roles
  aws iam get-role-policy --role-name EmailSenderRole --policy-name SESPolicy
  # Verify Resource is specific identity ARN, not "*"
  # Verify Condition keys restrict FromAddress
  ```
- Trade-offs: Condition key restrictions require updating IAM policies when new sending addresses are added. Overly narrow restrictions may block legitimate sends — test in sandbox first.
- Source: https://docs.aws.amazon.com/ses/latest/dg/control-user-access.html

---

### ⚠️ Architectural Decisions

**Shared IPs vs Dedicated IPs vs Managed Dedicated IPs**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Shared IPs (default) | SES shared pool | Zero management, immediate warm reputation, cost | Reputation isolation, IP predictability, compliance (fixed IP) | Volume < 10K emails/day; startup/low-volume senders; diverse sending patterns |
  | Standard Dedicated IPs | SES dedicated IP ($24.95/mo per IP) | Full reputation control, IP predictability, compliance | Requires warm-up (2-6 weeks), needs consistent volume (10K+/day), cost | Volume > 100K/day; need IP allowlisting by receivers; compliance requires known IPs; manual warm-up control needed |
  | Managed Dedicated IPs | SES managed pool ($15/mo per IP) | Automatic warm-up, automatic scaling, reputation isolation | Less manual control, still needs volume (10K+/day recommended) | Volume > 50K/day; want dedicated reputation without operational overhead; prefer AWS-managed warm-up |

- Cost Profile: Shared = $0 (included in per-email pricing). Standard Dedicated = $24.95/month per IP (need 1+ IPs based on volume — roughly 1 IP per 50K emails/day). Managed Dedicated = $15/month per IP with automatic pool management.
- Scaling Characteristics: Shared scales automatically. Dedicated IPs require adding more IPs for higher volume. Each dedicated IP can sustain ~50K emails/day after warm-up. Managed Dedicated auto-scales within the pool.
- Lock-in Assessment: IPs are SES-specific. If migrating away from SES, dedicated IP reputation does not transfer. Managed Dedicated IPs cannot be individually addressed or allowlisted.
- Architect Instruction: "Ask 'Is sending volume consistently above 50K emails/day, and do you need reputation isolation between email types or compliance-mandated fixed IPs?' — if NO, use Shared IPs. If YES with operational capacity for warm-up, use Standard. If YES without wanting operational overhead, use Managed."
- Source: https://docs.aws.amazon.com/ses/latest/dg/dedicated-ip.html

**SES vs SNS for Notification Delivery**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Amazon SES | SES (email sending) | Rich content (HTML/attachments), branding, deliverability management, high volume | Latency (email delivery is inherently async), recipient must check email | Formal communications, marketing, transactional email (receipts, shipping), content requiring formatting |
  | Amazon SNS (email protocol) | SNS → email subscription | Simplicity (no identity verification for topic subscribers), fan-out to multiple channels | No branding, plaintext only, no bounce/complaint management, no authentication control | Simple system notifications, internal alerts, CloudWatch alarm notifications |
  | Amazon SNS (SMS/push) | SNS → SMS/push | Immediate delivery, high open rates | Cost (SMS expensive), character limits, no rich content | Time-sensitive alerts, 2FA codes, real-time notifications |

- Cost Profile: SES: $0.10/1,000 emails. SNS email: $0 (included in SNS topic delivery). SNS SMS: $0.00581-$0.0645+ per message (varies by country). SNS push: $0.50/million.
- Architect Instruction: "Ask 'Is this a branded communication requiring HTML content, deliverability tracking, and authentication compliance?' — if YES, use SES. If it's a simple internal notification or system alert, use SNS email subscription. If time-sensitive and brief, use SNS SMS or push."
- Source: https://docs.aws.amazon.com/ses/latest/dg/Welcome.html

**SES Receipt Rules vs Mail Manager for Inbound Email**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | SES Receipt Rules (legacy) | SES receipt rules + IP filters | Simplicity, low cost, direct AWS integration (S3, Lambda, SNS, WorkMail, bounce) | Limited routing logic, no archiving, no third-party security integrations, max 200 rules per rule set | Simple inbound workflows (store in S3, trigger Lambda, forward to WorkMail), low complexity requirements |
  | Mail Manager | SES Mail Manager (ingress endpoints, traffic policies, rule sets, archiving, SMTP relay) | Advanced routing, compliance archiving with search, traffic policy filtering, third-party security Add Ons, SMTP relay | Higher complexity, additional cost, newer feature (less community documentation) | Enterprise inbound email processing, compliance archiving requirements, advanced security scanning, multi-destination routing, hybrid environments with SMTP relay |

- Cost Profile: Receipt Rules: included in SES receiving pricing ($0 per 1,000 emails received, first 1,000/month). Mail Manager: ingress endpoint hours + message processing + archive storage (check current pricing).
- Operational Burden: Receipt Rules are simple to configure via IaC. Mail Manager requires more operational surface (ingress endpoints, traffic policies, rule sets, archives) but provides significantly more capability.
- Architect Instruction: "Ask 'Do you need email archiving with search, third-party security scanning, SMTP relay to on-premises systems, or advanced traffic filtering beyond IP/recipient-based rules?' — if YES, use Mail Manager. If basic S3/Lambda/SNS routing suffices, use Receipt Rules."
- Source: https://docs.aws.amazon.com/ses/latest/dg/eb.html

**Single-Region vs Multi-Region SES Deployment**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Single-Region | SES in one region | Simplicity, single identity verification, unified suppression list | No failover, single point of failure for sending, higher latency from distant origins | Non-critical email, single-geography application, low complexity tolerance |
  | Multi-Region Active-Passive | SES in primary + secondary region (failover) | Resilience (failover if primary region has issues), acceptable latency | Duplicate configuration (identities, config sets verified per region), complexity of failover logic | Critical transactional email where delivery availability is paramount, SLA requirements |
  | Multi-Region Active-Active | SES in multiple regions (route by geography) | Lowest latency (send from nearest region), maximum availability | Full duplication of all configurations per region, separate suppression lists per region, separate quotas per region | Global applications with latency sensitivity, highest availability requirements, regulatory data residency |

- Cost Profile: All options have same per-email pricing. Multi-region adds operational cost (managing identities, quotas, DNS records in multiple regions) but no additional SES charges.
- Architect Instruction: "Ask 'Is email delivery availability critical enough to justify duplicate SES configuration in multiple regions, and do you have global latency requirements?' — if email can tolerate occasional delays during regional issues, single-region is sufficient. For critical transactional email (password resets, 2FA), consider multi-region."
- Source: https://docs.aws.amazon.com/ses/latest/dg/regions.html

**SMTP Interface vs SES v2 API for Sending**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | SMTP Interface | SES SMTP endpoint (port 587/465/2587) | Compatibility (works with any SMTP client/library/MTA), legacy integration | No batch sending, no template support, SMTP credential management, connection overhead | Integrating with existing applications that use SMTP (WordPress, legacy apps, on-premises MTAs), SMTP-only clients |
  | SES v2 API (SendEmail) | SES API via AWS SDK | Full feature access (templates, batch, tags, configuration sets), IAM auth (no SMTP credentials), lower latency | Requires AWS SDK integration, not compatible with generic SMTP clients | New applications, programmatic sending, template-based email, batch operations, serverless (Lambda) |
  | SES v2 API (SendBulkEmail) | SES API via AWS SDK | High-volume batch sending (up to 50 destinations per call), template-based personalization | Only works with templates, requires AWS SDK | Marketing campaigns, newsletters, bulk notifications with per-recipient personalization |

- Cost Profile: Same pricing regardless of interface used. SMTP may have slightly higher latency due to protocol overhead.
- Architect Instruction: "Ask 'Is this a new application with AWS SDK access, or an existing system that only speaks SMTP?' — new applications should always use the SES v2 API. Existing systems that cannot be modified should use SMTP. For bulk campaigns, always use SendBulkEmail."
- Source: https://docs.aws.amazon.com/ses/latest/dg/send-email.html

---

### 🚫 Anti-Patterns

**Sending Without Email Authentication (No DKIM/SPF/DMARC)**
- Risk Level: CRITICAL
- Why: Violates Security pillar. As of 2024, Google and Yahoo require DMARC-aligned authentication for bulk senders. Without DKIM and aligned SPF, email is routed to spam or rejected outright. Additionally, your domain is vulnerable to spoofing — anyone can send email appearing to come from your domain.
- Instead: Enable Easy DKIM (2048-bit) on all sending domains. Configure custom MAIL FROM for SPF alignment. Publish DMARC record starting with p=none, advancing to p=reject. Use VDM Advisor to identify authentication gaps.
- Detection:
  ```bash
  aws sesv2 get-email-identity --email-identity yourdomain.com
  # Alert if DkimAttributes.Status != "SUCCESS" or DkimAttributes.SigningKeyLength = "RSA_1024_BIT"
  # Alert if MailFromAttributes.MailFromDomainStatus != "SUCCESS"

  # Check DMARC externally
  dig TXT _dmarc.yourdomain.com
  # Alert if no DMARC record or p=none without active monitoring
  ```
- Impact: Spam folder delivery (50-90% of email lost), domain spoofing exposure, compliance violation (DMARC required by major ISPs), sender reputation damage.
- Source: https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html

**No Bounce/Complaint Processing Pipeline**
- Risk Level: CRITICAL
- Why: Violates Reliability and Operational Excellence pillars. Continuing to send to addresses that have bounced or complained accelerates reputation degradation. SES will pause sending at 10% bounce rate or 0.5% complaint rate. Without automated processing, invalid addresses accumulate in mailing lists, creating a reputation death spiral.
- Instead: Configure SNS event destination for bounce and complaint events. Implement a Lambda function (or equivalent) that processes these events in real-time and removes/suppresses the affected addresses from all mailing lists. Enable account-level suppression list as a safety net.
- Detection:
  ```bash
  # Check if any configuration set has event destinations for bounces/complaints
  aws sesv2 get-configuration-set-event-destinations --configuration-set-name <NAME>
  # Alert if no event destination handles BOUNCE and COMPLAINT event types

  # Check current reputation metrics
  aws sesv2 get-account
  # Alert if SendQuota.SendRatePerSecond is below expected (may indicate throttling)
  ```
- Impact: Account sending pause (SES disables sending), permanent reputation damage requiring months to recover, lost transactional email delivery (password resets, order confirmations).
- Source: https://docs.aws.amazon.com/ses/latest/dg/monitor-sender-reputation.html

**Sending to Purchased/Unverified Mailing Lists**
- Risk Level: CRITICAL
- Why: Violates Security and Reliability pillars. Purchased lists contain spam traps (addresses operated by ISPs/anti-spam organizations to identify spammers), invalid addresses (high bounce rate), and unwilling recipients (high complaint rate). A single send to a purchased list can trigger SES account suspension.
- Instead: Only send to recipients who have explicitly opted in (double opt-in preferred). Implement List-Unsubscribe headers. Use SES subscription management features. Clean lists regularly by removing disengaged recipients (no opens/clicks in 90+ days).
- Detection:
  Monitor Reputation.BounceRate and Reputation.ComplaintRate metrics after any send to new list segments. A sudden spike (bounce > 5% or complaint > 0.1%) indicates list quality issues. VDM Dashboard shows these metrics per configuration set.
- Impact: Immediate account suspension, permanent IP/domain blacklisting, SES account termination, legal liability (CAN-SPAM, GDPR violations).
- Source: https://docs.aws.amazon.com/ses/latest/dg/best-practices.html

**Sending Production Email from Sandbox**
- Risk Level: HIGH
- Why: Violates Reliability pillar. Sandbox accounts are limited to 200 emails/day, 1/second rate, and only to verified recipients. Attempting production workloads from sandbox results in delivery failures to real customers, hard-to-diagnose issues (silent rejection to unverified recipients), and inability to scale.
- Instead: Request production access before any non-development use. Plan for 24-48 hour approval time in deployment timelines. Submit requests for all target regions simultaneously. Use mailbox simulator for testing in sandbox.
- Detection:
  ```bash
  aws sesv2 get-account
  # Check ProductionAccessEnabled = true
  # If false and application is attempting production email — critical misconfiguration
  ```
- Impact: Silent delivery failures (email to unverified recipients is rejected without notification in sandbox), customer-facing outage for transactional email, missed notifications.
- Source: https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html

**Hardcoded SMTP Credentials in Application Code**
- Risk Level: CRITICAL
- Why: Violates Security pillar. SES SMTP credentials are IAM-derived secrets. If exposed (in version control, logs, or configuration files), they enable unauthorized email sending from your verified identities — potentially for phishing, spam, or reputation destruction.
- Instead: Store SMTP credentials in AWS Secrets Manager with automatic rotation. For programmatic sending, use IAM roles with the SES v2 API (no credentials to manage). For SMTP-based applications, retrieve credentials from Secrets Manager at runtime. Never commit credentials to source control.
- Detection:
  ```bash
  # Scan for SMTP credentials in code repositories
  # SMTP credentials start with "AKIA" (IAM access key format)
  grep -r "AKIA" --include="*.{py,js,java,ts,env,yml,yaml,json}" .
  ```
  Use AWS Config rule or git-secrets to prevent commits containing credentials.
- Impact: Unauthorized email sending, domain reputation destruction, phishing attacks using your domain, SES account compromise, compliance violation.
- Source: https://docs.aws.amazon.com/ses/latest/dg/smtp-credentials.html

**Ignoring Sending Quota Limits in Application Design**
- Risk Level: HIGH
- Why: Violates Reliability and Performance Efficiency pillars. SES enforces sending quotas (daily limit and per-second rate). Applications that burst-send without quota awareness receive throttling errors (HTTP 454 or Throttling exception), resulting in lost email, retry storms, and degraded application performance.
- Instead: Implement exponential backoff retry logic for SES API calls. Monitor daily quota usage (GetAccount API). Queue outbound email via SQS for rate-limited sending. Request quota increases proactively before campaigns. Design for graceful degradation when quota is approached.
- Detection:
  ```bash
  aws sesv2 get-account
  # Compare SendQuota.SentLast24Hours against SendQuota.Max24HourSend
  # Alert if utilization > 80%

  # Monitor CloudWatch for throttling
  aws cloudwatch get-metric-statistics --namespace AWS/SES --metric-name Reputation.SendRate
  ```
- Impact: Lost transactional email (customer-facing outage), retry storms (cascading failures), application errors, customer-impacting delays.
- Source: https://docs.aws.amazon.com/ses/latest/dg/manage-sending-quotas.html

**Using SES for Unsolicited Commercial Email (Spam)**
- Risk Level: CRITICAL
- Why: Violates AWS Acceptable Use Policy and Security pillar. SES explicitly prohibits sending unsolicited email. AWS actively monitors sending patterns and will immediately suspend accounts engaged in spam. Additionally, spam destroys IP/domain reputation, blacklists your domain, and creates legal liability.
- Instead: Only send to opted-in recipients. Include clear unsubscribe mechanism (List-Unsubscribe header). Honor unsubscribe requests within 10 business days (CAN-SPAM) or immediately (GDPR). Use SES subscription management features.
- Detection:
  AWS monitors complaint rates, spam trap hits, and ISP feedback loops. High complaint rates (> 0.1%) and blacklist appearances are early indicators.
- Impact: Immediate account suspension/termination, domain permanent blacklisting, legal prosecution (CAN-SPAM fines up to $51,744 per email, GDPR fines), inability to send legitimate email from the domain.
- Source: https://docs.aws.amazon.com/ses/latest/dg/best-practices.html

---

## Cloud-Native Design Patterns

**Transactional Email Pipeline (Event-Driven)**
- Category: Communication
- Problem: Applications need to send transactional emails (order confirmations, password resets, shipping notifications) reliably without blocking application logic, with delivery confirmation and failure handling.
- Solution on AWS:
  Application publishes send request to SQS queue → Lambda consumer retrieves messages at controlled rate → Lambda calls SES v2 API SendEmail with configuration set → SES sends email and publishes events to configured destinations → SNS/Lambda processes bounce/complaint events to update application state.
- Services Used: Amazon SQS (request buffering and rate control), AWS Lambda (send orchestration), Amazon SES (email delivery), Amazon SNS (event notifications), Amazon DynamoDB (email status tracking)
- When to Apply: Transactional email must not block application response time. Need guaranteed delivery (retry on failure). Need delivery status tracking. Volume requires rate-limited sending to stay within SES quotas.
- When NOT to Apply: Simple, low-volume notification (< 100/day) where inline SES API call in application is acceptable. Real-time email isn't critical to user experience.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Reliability | SQS guarantees message persistence; Lambda retries on failure | Additional infrastructure (SQS queue, Lambda function) |
  | Performance | Non-blocking send — application responds immediately | Small delivery delay (SQS→Lambda→SES adds seconds) |
  | Observability | Full event trail from request through delivery | Event destination configuration and processing logic |
  | Rate Control | SQS controls consumption rate, preventing quota exhaustion | Requires tuning Lambda concurrency to match SES quota |

- Complements: Dead-Letter Queue (for failed sends), CloudWatch Alarms (quota monitoring), Suppression List (reputation protection)
- Source: https://docs.aws.amazon.com/ses/latest/dg/send-email-concepts-process.html

**Bulk Marketing Email with Personalization**
- Category: Scalability
- Problem: Marketing campaigns need to send millions of personalized emails efficiently, with engagement tracking (opens, clicks), list management (unsubscribes), and controlled sending to protect reputation.
- Solution on AWS:
  Campaign orchestrator reads recipient segments from DynamoDB → Generates batches of 50 recipients → Calls SES v2 SendBulkEmail with email templates (server-side personalization) → Configuration set routes events to Firehose → Firehose delivers to S3 for analytics → VDM Dashboard monitors deliverability and engagement per ISP. Sending is paced via Step Functions with wait states or SQS with controlled Lambda concurrency.
- Services Used: Amazon SES (SendBulkEmail API, templates), AWS Step Functions (campaign orchestration), Amazon DynamoDB (recipient lists), Amazon Data Firehose (event analytics), Amazon S3 (event storage), Virtual Deliverability Manager (ISP insights)
- When to Apply: Marketing campaigns exceeding 10K recipients. Need per-recipient personalization. Need engagement analytics (opens, clicks). Need controlled send pacing for reputation management.
- When NOT to Apply: Simple notification to a few recipients. Content doesn't require personalization. Don't need engagement tracking.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Throughput | SendBulkEmail: 50 destinations per API call vs 1 for SendEmail | Requires pre-defined templates (no inline HTML per recipient) |
  | Personalization | Server-side template rendering with per-recipient variables | Template max 500 KB; limited template logic |
  | Analytics | Full engagement tracking via VDM + event publishing | VDM cost ($0.0007/email); Firehose data transfer costs |
  | Reputation | Paced sending protects reputation during large campaigns | Campaign takes longer to complete; orchestration complexity |

- Complements: SES Subscription Management, Account-Level Suppression List, Dedicated IP Pools (reputation isolation from transactional)
- Source: https://docs.aws.amazon.com/ses/latest/dg/send-email-api.html

**Inbound Email Processing Pipeline**
- Category: Communication
- Problem: Applications need to receive email (customer support, automated processing, compliance) and route it to appropriate systems — extracting content, attachments, and metadata for downstream processing.
- Solution on AWS:
  DNS MX record points to SES inbound endpoint (or Mail Manager ingress endpoint) → Receipt rules (or Mail Manager rule sets) evaluate incoming email → Actions: store raw email in S3, publish notification to SNS, invoke Lambda for processing, forward to WorkMail. Lambda extracts content/attachments from S3, processes business logic, and routes to appropriate system (ticketing, CRM, archive).
- Services Used: Amazon SES (receipt rules or Mail Manager), Amazon S3 (email storage), AWS Lambda (processing logic), Amazon SNS (notifications), Amazon WorkMail (optional — user mailboxes)
- When to Apply: Need programmatic email processing (auto-responders, ticket creation, data extraction). Need email archiving for compliance. Need to route email to multiple downstream systems.
- When NOT to Apply: Just need traditional mailboxes (use WorkMail or Google Workspace directly). Don't need programmatic processing. Email receiving not supported in target region.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Flexibility | Full programmatic control over email routing and processing | Custom code required for processing logic |
  | Cost | $0 for first 1,000 emails/month received; S3 storage for content | Lambda invocation costs; S3 storage for retained email |
  | Compliance | Mail Manager archiving with search and export | Mail Manager has additional pricing; archive storage costs |
  | Limitations | Max 40 MB email size (S3); max 150 KB for SNS notification body | Email receiving only available in specific SES regions |

- Complements: Mail Manager (advanced routing), S3 lifecycle policies (archive tiering), KMS (encryption at rest for stored email)
- Source: https://docs.aws.amazon.com/ses/latest/dg/receiving-email.html

**Reputation-Isolated Multi-Tenant Email Architecture**
- Category: Resilience
- Problem: A SaaS platform sends email on behalf of multiple tenants. One tenant's poor sending practices (high bounces, spam complaints) must not affect other tenants' email deliverability.
- Solution on AWS:
  Create separate configuration sets per tenant (or tenant tier). Assign dedicated IP pools per tenant (or per tier — premium tenants get dedicated IPs, standard tenants share). Each configuration set has its own event destinations and suppression list overrides. Monitor per-tenant reputation via VDM Dashboard (configuration-set-level metrics). Implement per-tenant sending quotas in application logic (SES quotas are account-level, not per-tenant).
- Services Used: Amazon SES (configuration sets, dedicated IP pools), Virtual Deliverability Manager (per-configuration-set metrics), Amazon CloudWatch (per-tenant alarms), application-level quota enforcement
- When to Apply: Multi-tenant SaaS where tenants control email content. Different tenants have different sending quality. Need to protect high-quality tenants from low-quality tenants' reputation impact.
- When NOT to Apply: Single-tenant application. All email content is platform-controlled (same sending quality). Low volume where shared reputation is acceptable.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Isolation | Per-tenant reputation protection via IP pools | Dedicated IPs cost $15-25/month each; need volume to maintain |
  | Monitoring | Per-configuration-set metrics identify problematic tenants | More configuration sets to manage; 10K limit per region |
  | Complexity | Granular control per tenant | Application must manage tenant→configuration set mapping |
  | Cost | Only premium tenants need dedicated IPs | IP pool management overhead; warm-up per new IP |

- Complements: Sending Authorization (allow tenants to verify their own domains), Dedicated IP Pools, VDM Dashboard
- Source: https://docs.aws.amazon.com/ses/latest/dg/dedicated-ip-pools.html

**IP Warm-Up Pattern for New Dedicated IPs**
- Category: Scalability
- Problem: New dedicated IP addresses have no sending reputation. ISPs throttle or reject email from unknown IPs. Immediately sending at full volume from a new IP triggers spam filters and delays delivery.
- Solution on AWS:
  Start with small volumes (100-500 emails/day) from the new dedicated IP. Gradually increase volume daily over 2-6 weeks following a warm-up schedule: Day 1-3: 200/day → Day 4-7: 500/day → Week 2: 1,000/day → Week 3: 5,000/day → Week 4: 10,000/day → Week 5-6: target volume. During warm-up, send ONLY to your most engaged recipients (opened/clicked within 30 days) to maximize positive engagement signals. Use Managed Dedicated IPs (automatic warm-up) to eliminate manual scheduling.
- Services Used: Amazon SES (Managed Dedicated IPs for automatic warm-up, or Standard Dedicated IPs for manual), application-level volume control, recipient engagement segmentation
- When to Apply: Every time a new dedicated IP is added. When moving from shared to dedicated IPs. When adding capacity for growing volume.
- When NOT to Apply: Using shared IPs. Using Managed Dedicated IPs (automatic warm-up handles this). IP already has established reputation (existing sending history).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Reputation | Builds positive reputation progressively | 2-6 weeks before full volume; campaigns delayed |
  | Deliverability | ISPs learn to trust the IP gradually | Premature volume increase triggers throttling |
  | Automation | Managed Dedicated IPs automate entirely | Less control over warm-up pace |
  | Risk | Low risk of blacklisting vs immediate full send | Revenue impact from delayed campaign sends |

- Complements: VDM Dashboard (monitor ISP acceptance during warm-up), Engagement-based segmentation, CloudWatch metrics
- Source: https://docs.aws.amazon.com/ses/latest/dg/dedicated-ip-warming.html

---

## Security Architecture

**Identity & Access Management for Email Sending**
- AWS Services: AWS IAM (policies, roles), Amazon SES (sending authorization policies, verified identities), AWS Secrets Manager (SMTP credential rotation)
- Architecture:
  Application roles have IAM policies granting `ses:SendEmail` and `ses:SendRawEmail` restricted by resource ARN (identity ARN) and conditions (`ses:FromAddress`, `ses:Recipients`). For cross-account sending (partner/vendor needs to send from your domain), use SES Sending Authorization Policies attached to the identity — these are resource-based policies that grant specific external principals limited sending permission with conditions. SMTP credentials (for legacy SMTP integrations) are stored in Secrets Manager with automatic rotation. CloudTrail logs all SES API calls for audit.
- Compliance Alignment: SOC2 CC6.1 (logical access controls), GDPR Art.32 (security of processing), PCI-DSS 7.1 (restrict access by business need)
- Source: https://docs.aws.amazon.com/ses/latest/dg/control-user-access.html

**Email Authentication Architecture (Anti-Spoofing)**
- AWS Services: Amazon SES (Easy DKIM, custom MAIL FROM), Amazon Route 53 (DNS records), Virtual Deliverability Manager (advisor)
- Architecture:
  Three-layer authentication: (1) DKIM — Easy DKIM with 2048-bit keys, SES signs all outbound email with domain key; CNAME records in DNS publish public key for receiver verification. (2) SPF — Custom MAIL FROM subdomain with TXT record authorizing SES IP ranges. (3) DMARC — TXT record at `_dmarc.domain` specifying alignment policy (aspf/adkim) and enforcement level (p=reject for production). VDM Advisor continuously monitors authentication status and alerts on misconfigurations.
- Compliance Alignment: NIST 800-177 (email security), PCI-DSS 4.0 (authentication requirements), DMARC/BIMI industry standards, Google/Yahoo 2024 bulk sender requirements
- Source: https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication.html

**Data Protection for Email Content**
- AWS Services: Amazon SES (TLS enforcement), AWS KMS (encryption for stored email in S3), Amazon S3 (server-side encryption for received email)
- Architecture:
  In-transit: SES enforces TLS for all API connections (HTTPS). For SMTP, ports 587/465/2587 require STARTTLS or implicit TLS. Configuration set `TlsPolicy: REQUIRE` ensures SES-to-receiver transmission is encrypted. At-rest: Received email stored in S3 is encrypted via SSE-KMS (customer-managed key for audit trail). Mail Manager archives are encrypted. Email templates stored in SES are encrypted at rest by the service.
- Compliance Alignment: HIPAA (PHI in transit/at rest encryption), PCI-DSS 4.1 (encryption in transit), GDPR Art.32 (encryption as security measure)
- Source: https://docs.aws.amazon.com/ses/latest/dg/receiving-email-permissions.html

---

## Operational Patterns

**Sending Reputation Monitoring**
- AWS Services: Amazon SES (reputation metrics), Amazon CloudWatch (alarms, dashboards), Virtual Deliverability Manager (ISP-level insights), Amazon SNS (alarm notifications)
- Cost Profile: Low — CloudWatch metrics for SES are free (standard resolution). VDM adds $0.0007/email for engagement tracking. CloudWatch Alarms: $0.10/alarm/month.
- Automation:
  CloudWatch Alarms trigger on: Reputation.BounceRate > 3% (warning), > 5% (critical). Reputation.ComplaintRate > 0.05% (warning), > 0.1% (critical). Daily sending quota utilization > 80% (warning). Automated response: Lambda triggered by alarm pauses marketing configuration set sending (via application flag) while transactional continues. VDM Dashboard provides daily review surface for deliverability trends.
- Runbook Skeleton:
  1. **Detection**: CloudWatch alarm fires on bounce/complaint rate threshold
  2. **Triage**: Check VDM Dashboard for ISP-level breakdown; identify if spike is from specific configuration set, identity, or ISP
  3. **Resolution**: If list quality issue — pause marketing sends, clean list, identify source of bad addresses. If infrastructure issue — check authentication records, IP reputation, recent changes. If ISP-specific — check for IP blacklisting, submit delisting requests
  4. **Post-mortem**: Document root cause, implement preventive automation (better list validation, engagement-based segmentation)
- Source: https://docs.aws.amazon.com/ses/latest/dg/monitor-sender-reputation.html

**Multi-Region Email Failover**
- RTO/RPO: RTO: 1-5 minutes (DNS TTL + health check interval). RPO: 0 (no email loss — queue-based architecture retries from alternate region).
- AWS Services: Amazon SES (multi-region), Amazon Route 53 (health checks, failover routing), Amazon SQS (cross-region replication or per-region queues), AWS Lambda (send orchestration)
- Cost Profile: Medium — duplicate identity verification across regions, separate quotas, cross-region SQS/Lambda if using active-passive.
- Automation:
  Route 53 health check monitors SES sending capability in primary region (custom health check Lambda that calls SES GetAccount and verifies SendingEnabled=true). On failure, application switches to secondary region's SES endpoint. SQS Dead-Letter Queue in primary retries from secondary. DNS for MAIL FROM domains includes records for both regions.
- Runbook Skeleton:
  1. **Detection**: Route 53 health check fails for primary SES region or CloudWatch alarm on consecutive send failures
  2. **Triage**: Confirm SES service issue vs application issue (check AWS Health Dashboard, SES console)
  3. **Resolution**: Failover to secondary region (automatic via Route 53 or manual application config change). Verify secondary region has production access, warm reputation, and sufficient quota
  4. **Recovery**: Monitor primary region health. When restored, gradually shift traffic back. Verify suppression list consistency across regions
- Source: https://docs.aws.amazon.com/ses/latest/dg/regions.html

**Email Deliverability Optimization (FinOps)**
- AWS Services: Amazon SES (list management, suppression lists), Virtual Deliverability Manager (engagement insights), Amazon CloudWatch (cost metrics)
- Cost Profile: Primary cost drivers: per-email sending charge ($0.10/1K), dedicated IP fees ($15-25/month each), VDM engagement tracking ($0.0007/email), data transfer for large attachments. Key optimization: don't send to disengaged recipients (wasted cost + reputation harm).
- Automation:
  Automated list hygiene: Lambda processes engagement events (opens, clicks) and flags recipients with no engagement in 90 days for re-engagement campaign or removal. Suppress disengaged recipients to reduce send volume (cost saving) and improve engagement rates (reputation benefit). Use SendBulkEmail (50 destinations/call) instead of individual SendEmail calls to reduce API overhead.
- Runbook Skeleton:
  1. **Measure**: Track cost per delivered email and cost per engaged email (opened/clicked) via Firehose → Athena
  2. **Identify waste**: Recipients with 0 engagement in 90+ days are costing money and harming reputation
  3. **Optimize**: Re-engagement campaign (one final attempt) → If no engagement, remove from active list
  4. **Validate**: Monitor post-cleanup metrics — engagement rates should increase, bounce/complaint rates decrease
- Source: https://docs.aws.amazon.com/ses/latest/dg/best-practices.html

---

## Reference Architectures

**Transactional Email Platform**
- Context: Application sending password resets, order confirmations, shipping notifications, and account alerts — high deliverability requirements, low latency sensitivity, moderate volume (10K-100K emails/day).
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Request Queue | Amazon SQS | Buffer send requests, control rate, enable retry |
  | Send Orchestration | AWS Lambda | Consume from SQS, call SES API, handle errors |
  | Email Delivery | Amazon SES (v2 API) | Send email with configuration set |
  | Templates | SES Email Templates | Server-side personalization |
  | Event Processing | SNS + Lambda | Real-time bounce/complaint handling |
  | Analytics | Data Firehose + S3 | Email event storage for reporting |
  | Monitoring | CloudWatch + VDM | Reputation and deliverability monitoring |
  | Secrets | Secrets Manager | SMTP credentials (if SMTP path needed) |

- Key Decisions: Use SES v2 API (not SMTP) for Lambda-based sending. Use templates for repeated email types. Enable TLS enforcement for sensitive transactional email. Use shared IPs unless volume justifies dedicated.
- Scaling Path: Start with shared IPs → Add dedicated IP pool for transactional at 50K+/day → Multi-region active-passive at 100K+/day for availability → Multi-region active-active at global scale.
- Source: https://docs.aws.amazon.com/ses/latest/dg/send-email-concepts-process.html

**Marketing Email Platform with Engagement Analytics**
- Context: Marketing team sending campaigns, newsletters, and promotional email — engagement tracking (opens/clicks), list management, reputation isolation from transactional.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Campaign Orchestration | AWS Step Functions | Manage campaign lifecycle, pacing, warm-up |
  | Recipient Management | Amazon DynamoDB | Store lists, preferences, engagement history |
  | Email Delivery | Amazon SES (SendBulkEmail) | Batch personalized sending with templates |
  | IP Isolation | Dedicated IP Pool (marketing) | Separate reputation from transactional |
  | Engagement Tracking | VDM + Event Publishing | Open/click rates per ISP, per campaign |
  | Analytics | Firehose + S3 + Athena | Detailed engagement analytics and reporting |
  | List Hygiene | Lambda (scheduled) | Remove disengaged recipients, process unsubscribes |
  | Unsubscribe | SES Subscription Management | List-Unsubscribe header, one-click unsubscribe |

- Key Decisions: Separate configuration set and IP pool from transactional. Enable VDM engagement tracking. Implement gradual send pacing (Step Functions wait states). Use SendBulkEmail with templates. Clean lists based on engagement data.
- Scaling Path: Start with shared IPs → Managed Dedicated IPs at 50K+/day → Standard Dedicated IPs with custom warm-up for full control → Multiple IP pools for A/B reputation testing.
- Source: https://docs.aws.amazon.com/ses/latest/dg/send-email-api.html

---

## Scenario Coverage

**Standard Case**: Transactional email for a web application (password resets, order confirmations, notifications)
- Approach: SES v2 API with configuration set, Easy DKIM + custom MAIL FROM + DMARC, account-level suppression enabled, event publishing to CloudWatch (metrics) + SNS (bounce/complaint processing). Shared IPs for volume < 50K/day.
- Key Decisions: Architect must decide TLS enforcement level, multi-region requirement, and whether to add SQS buffering based on send volume and application tolerance for inline API calls.

**Edge Case**: Multi-tenant SaaS where customers bring their own sending domains
- Approach: Each tenant verifies their domain in SES. Use sending authorization policies to allow the platform to send on behalf of tenant domains. Per-tenant configuration sets with dedicated IP pools (for premium tiers). Application enforces per-tenant quotas. VDM monitors per-configuration-set metrics.
- Key Decisions: Who manages DNS (DKIM CNAME, MAIL FROM MX/TXT, DMARC)? Platform provides DNS instructions, tenant publishes. What happens when a tenant's reputation degrades? Auto-throttle via application logic, notify tenant.

**Anti-Pattern Case**: Client wants to send to a 500K purchased email list for a product launch
- Clarification: "Where did this list originate? Purchased/rented lists violate AWS Acceptable Use Policy and will trigger immediate account suspension. What is the opt-in mechanism — can you demonstrate explicit consent for each recipient? What is the expected bounce rate for this list? If answers are unsatisfactory, refuse to implement and recommend: build an organic list via double opt-in, start with a small engaged segment, warm up gradually."
