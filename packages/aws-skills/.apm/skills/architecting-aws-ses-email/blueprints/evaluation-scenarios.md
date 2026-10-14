# Evaluation Scenarios — architecting-aws-ses-email

Skill version tested: AWS SES 2026 (Research Date: 2026-08-30)

---

## Scenario 1 — Canonical: New Transactional Email Integration

```json
{
  "skills": ["architecting-aws-ses-email"],
  "query": "We are launching a SaaS web application on AWS. The application tier runs on ECS (Fargate). We need to send transactional emails (password reset, order confirmation) to users. Design the SES integration from scratch.",
  "expected_behavior": [
    "Recommends SES API v2 (not SMTP) with ECS task role IAM execution — no static credentials",
    "Instructs to verify a domain identity and enable Easy DKIM (2048-bit, 3 CNAME records)",
    "Instructs to configure a custom MAIL FROM subdomain with SPF TXT and MX records",
    "Instructs to publish DMARC TXT at p=none with rua= reporting address, with a plan to escalate",
    "Creates a configuration set (e.g., transactional-config) and sets it as the default on the identity",
    "Attaches an SNS event destination for Bounce and Complaint event types",
    "Deploys a Lambda function to parse SNS notifications and call sesv2 put-suppressed-destination",
    "Confirms account-level suppression list is enabled (sesv2 get-account SuppressionAttributes)",
    "Creates CloudWatch alarms: BounceRate >= 5% WARNING, >= 10% CRITICAL; ComplaintRate >= 0.1% WARNING, >= 0.5% CRITICAL",
    "Recommends requesting production access at least 3 business days before launch",
    "IAM policy scoped to ses:SendEmail / ses:SendRawEmail with Resource locked to identity ARN and ses:FromAddress condition"
  ]
}
```

---

## Scenario 2 — Edge Case: Multi-Region High-Availability Requirement

```json
{
  "skills": ["architecting-aws-ses-email"],
  "query": "Our transactional email SLA requires an RTO of under 5 minutes on a regional AWS failure. The application already uses the AWS SDK (not SMTP). How do we architect SES for this?",
  "expected_behavior": [
    "Recommends SES Global Endpoints (MREP) as the active-active multi-region mechanism",
    "States the DEED prerequisite: DEED must be configured on the domain identity to replicate DKIM signing across regions without per-region CNAME records",
    "Lists prerequisites: (1) API v2 exclusively — SMTP cannot use Global Endpoints, (2) configuration sets duplicated in secondary region, (3) production access and matching quotas in secondary region",
    "Warns that AWS does not publish guaranteed RTO/RPO values for Global Endpoints — only DNS TTL guidance (positive ~60s, negative ~10s)",
    "Flags that inbound email (receipt rules) is single-region — multi-region email receiving requires asymmetric architecture",
    "Does NOT promise sub-60-second RTO as guaranteed by AWS"
  ]
}
```

---

## Scenario 3 — Anti-Pattern Detection: SMTP Credentials in Lambda Environment Variables

```json
{
  "skills": ["architecting-aws-ses-email"],
  "query": "Our team wants to configure SES with SMTP. They plan to store the SMTP username and password as Lambda environment variables because it's the fastest approach. Is this acceptable?",
  "expected_behavior": [
    "Flags this as a CRITICAL anti-pattern: SMTP credentials are static, long-lived secrets derived from IAM secret access key with no in-place rotation",
    "Explains that rotation requires deleting the IAM SMTP user and generating new credentials, making any hardcoded credential permanently long-lived until explicit action",
    "Proposes Option A: switch to SES API v2 with Lambda execution role — no static credentials at all, and eliminates the concern",
    "If SMTP is a hard requirement, proposes Option B: store credentials in AWS Secrets Manager and inject at runtime; implement rotation Lambda that deletes and recreates the IAM SMTP user",
    "Does NOT validate or accept the original proposal as acceptable"
  ]
}
```

---

## Scenario 4 — Compliance: Gmail and Yahoo Bulk Sender Requirements

```json
{
  "skills": ["architecting-aws-ses-email"],
  "query": "We send 50,000 marketing emails per day. A team member says we just need DKIM to comply with Gmail and Yahoo bulk sender requirements. Is that correct?",
  "expected_behavior": [
    "States this is incomplete — Gmail and Yahoo require three things together: (1) DKIM domain alignment, (2) custom MAIL FROM for DMARC SPF alignment (the default amazonses.com MAIL FROM fails DMARC SPF alignment), (3) DMARC record at p=none minimum",
    "Additionally requires one-click unsubscribe per RFC 8058 (List-Unsubscribe-Post header) for bulk senders",
    "Microsoft extended same requirements for senders >5,000 messages/day to Outlook/Hotmail/live.com, effective May 5, 2025",
    "Explains DMARC alignment: DKIM pass alone satisfies DMARC only if the DKIM signing domain aligns with the From: header domain. SPF alignment requires custom MAIL FROM.",
    "Recommends escalating DMARC from p=none to p=quarantine and then p=reject after validating mail stream coverage via DMARC aggregate reports"
  ]
}
```

---

## Scenario 5 — Misuse: Using ses:* IAM Policy for an Email-Sending Lambda

```json
{
  "skills": ["architecting-aws-ses-email"],
  "query": "We assigned our email-sending Lambda the ses:* action on Resource: * in the IAM policy to avoid permission errors. This works in our tests. Can we ship this to production?",
  "expected_behavior": [
    "Flags this as a HIGH-risk anti-pattern violating the Security pillar (least privilege)",
    "Enumerates what ses:* enables beyond sending: delete verified identities, modify/delete configuration sets, delete email templates, modify suppression lists, read all account settings",
    "Provides the correct scoped policy: Action [ses:SendEmail, ses:SendRawEmail], Resource locked to the specific identity ARN arn:aws:ses:<region>:<account>:identity/<domain>",
    "Recommends adding ses:FromAddress condition key to prevent unauthorized From address substitution",
    "Recommends running IAM Access Analyzer to detect the overly permissive policy",
    "Does NOT endorse shipping ses:* to production under any qualification"
  ]
}
```
