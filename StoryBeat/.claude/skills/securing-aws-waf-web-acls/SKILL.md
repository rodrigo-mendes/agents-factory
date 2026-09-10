---
name: securing-aws-waf-web-acls
description: "Configures and architects AWS WAF (WAFv2) web ACLs for internet-facing production workloads on AWS. Use when designing, deploying, or reviewing AWS WAF rule sets, bot control, fraud prevention (ATP/ACFP), AI traffic management (WBA, Monetize), WCU budgeting, or org-wide WAF governance for CloudFront, ALB, API Gateway, Cognito, or Bedrock AgentCore Gateway."
---

## Function
Specialist in AWS WAF (WAFv2) security architecture — web ACL design, managed rule groups, bot control, fraud prevention (ATP/ACFP), AI traffic management (WBA, Monetize), WCU budgeting, and org-wide governance for AWS internet-facing production workloads.

## Version Context

**Technology**: AWS WAF (WAFv2)
**Target edition**: AWS WAF 2026
**Research date**: 2026-08-26
**Currency threshold**: 2027-08-26
**Support status**: Active (AWS WAF Classic is in planned EOL — use WAFv2 for all new designs)

**Critical 2026 changes**:
- Bot Control v6.1 (Jul 2026) — new signatures across AI, Advertising, SEO, Webhooks categories
- WBA (Web Bot Authentication) expanded to all regional WAF in v6.0 (May 2026; was CloudFront-only in v4.0)
- AI Traffic Monetization GA (Jun 2026) — Monetize action, CloudFront-only, HTTP 402 x402 payments
- Bedrock AgentCore Gateway WAF protection GA (Jun 2026)
- Dynamic label interpolation `${namespace:}` — Apr 2026
- Anti-DDoS AMR (`AWSManagedRulesAntiDDoSRuleSet`) GA — Jun 2025

**Deprecated / EOL**:
- AWS WAF Classic (WAFv1): per-Region EOL milestones in AWS Health dashboard; no global EOL date published
- Security Automations for AWS WAF CloudFormation solution: retiring December 2026

⚠️ **CRITICAL — Agent Warning**:
This skill targets AWS WAF 2026 (WAFv2 API). Reject WAF Classic patterns. CLOUDFRONT-scope resources must always be in us-east-1. The 5,000 WCU hard cap per web ACL is immutable.

## Quick Navigation

- **[Blueprints & Guardrails](#blueprints--guardrails)** — ✅⚠️🚫 mandatory patterns, decisions, anti-patterns
- **[Integration Patterns](#integration-patterns)** — WAF ↔ CloudFront / ALB / Bedrock AgentCore / Firewall Manager
- **[Verification Loop](#verification-loop)** — CLI validation commands
- **[Quick Reference](#quick-reference)** — WCU budget table, key CLI, quotas, pricing
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 6 test cases
- **[External Resources](#external-resources)** — Official docs (all accessed 2026-08-26)

---

## Blueprints & Guardrails

### ✅ Always Do

**1. Deploy managed rules and new rules in Count mode before enforcing Block**
Set every new rule group or rule to Count (or apply a Count override) during an initial 24–72 hour observation window. Monitor `AWS/WAFV2` `CountedRequests` metric by rule dimension and review Sampled Requests in the console. Switch to Block only after confirming no legitimate traffic is caught.
- Consequence if omitted: HTTP 403 for legitimate users; immediate production impact with no automatic recovery.
- Source: [AWS WAF best practices](https://docs.aws.amazon.com/waf/latest/developerguide/best-practices.html), 2026-08-26.

**2. Create CLOUDFRONT-scope web ACLs exclusively in us-east-1**
All `Scope: CLOUDFRONT` WAF resources (web ACL, rule groups, IP sets, regex pattern sets) must be in `us-east-1`. This includes AWS Amplify, which appears in regional docs but is an exception requiring CLOUDFRONT scope. In Terraform, use a separate provider alias:
```hcl
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}
```
- Consequence if omitted: CloudFront or Amplify association fails; resource has no WAF protection.

**3. Enable logging on all web ACLs**
Call `PutLoggingConfiguration` for every web ACL. Logging destination name must start with `aws-waf-logs-`. Use CloudWatch Logs for real-time exploration; add S3 + Athena for long-term retention. Configure a CloudWatch alarm on `BlockedRequests` spikes.
- Consequence if omitted: no visibility for incident investigation or rule tuning; compliance audit failure.
- Source: [AWS WAF logging destinations](https://docs.aws.amazon.com/waf/latest/developerguide/logging-destinations.html), 2026-08-26.

**4. Use AWS Managed Rules as the baseline for every web ACL**
Start with CRS (`AWSManagedRulesCommonRuleSet`, 700 WCU) + Known Bad Inputs (200 WCU) + Amazon IP Reputation List (25 WCU) = 925 WCU. Subscribe to the AWS Managed Rules SNS topic for version-change notifications. Note: IP reputation groups auto-update silently — no SNS notifications available.
- Source: [AWS Managed Rules list](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-list.html), 2026-08-26.

**5. Plan WCU budget explicitly before adding rule groups**
Run `aws wafv2 check-capacity` before every IaC change. Hard cap: 5,000 WCU per web ACL (immutable). Cost increases above 1,500 WCU ($0.20/million requests per additional 500 WCU). Gate CI/CD to fail if estimated WCU > 4,500.

| Rule group | WCU |
|---|---|
| CRS (`AWSManagedRulesCommonRuleSet`) | 700 |
| Known Bad Inputs | 200 |
| Amazon IP Reputation | 25 |
| Anonymous IP | 50 |
| SQLi | 200 |
| Bot Control | 50 |
| ATP or ACFP (each) | 50 |
| Rate-based rule per custom aggregation key | +30 |
| **Full-stack web app baseline** | **1,225** |

- Source: [AWS WAF capacity units](https://docs.aws.amazon.com/waf/latest/developerguide/aws-waf-capacity-units.html), 2026-08-26.

### ⚠️ Ask First

**1. Bot Control tier: Common vs Targeted**
Ask whether the endpoint is targeted by sophisticated bots (scrapers, credential stuffers, residential proxies). If yes, Targeted is required (ML + fingerprinting + CAPTCHA/Challenge). If general automation suppression for a public page is sufficient, Common is adequate and cheaper.

| Option | Subscription | Free tier | Best when |
|---|---|---|---|
| Common | $10/mo | First 10M req/month | Public marketing pages, general bot suppression |
| Targeted | $10/mo | First 1M req/month | Login pages, APIs, scraping targets |

**2. Fraud control: ATP vs ACFP vs neither**
Ask whether login-endpoint credential stuffing or registration fraud has been observed or is a business risk. ATP adds AWS stolen-credential database detection for `/login` endpoints ($10/mo, 50 WCU). ACFP adds bulk registration fraud detection ($10/mo, 50 WCU). Neither can be used with Cognito user pool associations.

**3. L7 protection placement: CloudFront edge vs ALB regional vs both**
Ask whether all production traffic routes through CloudFront. For internet-facing production apps, prefer defense in depth (CLOUDFRONT WAF + REGIONAL ALB WAF). Single-tier is acceptable only for internal APIs or cost-constrained scenarios.

| Topology | Cost | When |
|---|---|---|
| CloudFront edge only | 1 web ACL | All traffic through CloudFront; cost-constrained |
| ALB regional only | 1 web ACL | Internal APIs; CloudFront not feasible |
| Both (defense in depth) | 2 web ACLs | Internet-facing production; regulated environments |

**4. Rate-based rule evaluation window**
Ask whether the attack profile is short, sharp bursts (use 60 s window) or sustained floods (300 s or 600 s). Set threshold from observed p99 request rates in CloudWatch. Rate-based rules cannot use Allow as their action.

**5. WAF governance: per-account web ACLs vs Firewall Manager**
For organizations with 5+ accounts or regulatory coverage requirements, Firewall Manager WAF policies are strongly preferred. Auto-remediates tampered web ACLs; auto-enrolls new accounts/resources. Ask about account count, OU structure, and compliance requirements before recommending per-account management.

### 🚫 Never Do

| Anti-pattern | Risk | Correct alternative |
|---|---|---|
| Deploy new rule group directly in Block without Count-mode validation | HIGH — HTTP 403 for legitimate users immediately | Deploy in Count; observe 24–72 h; review sampled requests; then promote to Block |
| Create CLOUDFRONT-scope web ACL outside us-east-1 | HIGH — deployment fails; CloudFront/Amplify unprotected | All `Scope: CLOUDFRONT` WAF resources in us-east-1 |
| Associate Amplify app with a REGIONAL-scope web ACL | HIGH — association fails; app unprotected | Use CLOUDFRONT-scope web ACL in us-east-1 for Amplify |
| Use ATP or ACFP rule groups with a Cognito user pool | MEDIUM — AssociateWebACL returns error | Separate web ACL without ATP/ACFP for Cognito; move ATP/ACFP to ALB or API Gateway layer |
| Associate a CloudFront web ACL with any Regional resource | MEDIUM — blocked operation; architects believe dual coverage exists | Create separate web ACLs: CLOUDFRONT scope for CloudFront, REGIONAL scope for ALB |
| Ignore WCU limits until deployment fails | MEDIUM — 5,000 WCU hard cap blocks deployment; cost overruns above 1,500 WCU | Run `aws wafv2 check-capacity` in CI/CD; maintain a running WCU budget |
| Disable or omit logging on production web ACLs | MEDIUM — no incident visibility; compliance audit failure | All production web ACLs have a `aws-waf-logs-*` logging configuration |

---

## Integration Patterns

**AWS WAF ↔ Amazon CloudFront (CLOUDFRONT scope, us-east-1)**
- All CLOUDFRONT-scope WAF resources (web ACL, rule groups, IP sets) must be in us-east-1. ARN format: `arn:aws:wafv2:us-east-1:*`.
- Bot Control Targeted + WBA (v6.0+) available at edge; Monetize action enables AI traffic pricing (CloudFront-only).
- ATP response inspection available for CloudFront paths (inspects up to 64 KB of response body).

**AWS WAF ↔ Application Load Balancer (REGIONAL scope)**
- REGIONAL web ACL must be in the same region as the ALB.
- Use rate-based rules with IP + JA4 fingerprint aggregation keys for credential-stuffing defense.
- ATP available for request inspection; response inspection requires CloudFront.

**AWS WAF ↔ Amazon Bedrock AgentCore Gateway (REGIONAL scope, GA Jun 2026)**
- Direct WAF association GA June 2026. Use Bot Control Targeted with WBA to allow verified AI agents while blocking unverified scrapers.
- Body inspection limit: up to 16 KB for AgentCore Gateway.
- Use rate-based rules with ASN aggregation for volumetric protection.

**AWS WAF ↔ AWS Firewall Manager (org-wide governance)**
- Firewall Manager WAF policy defines mandatory rule groups and scope (account/OU/tag). Individual accounts add custom rules on top.
- Auto-remediates tampered web ACLs within minutes; auto-enrolls new accounts/resources.
- Requires Firewall Manager admin designation in AWS Organizations management account.

**Common problems**:
- `WAFNonexistentItemException` on association → verify scope matches resource type; confirm CLOUDFRONT resources are in us-east-1
- `WAFUnavailableEntityException` → web ACL WCU would exceed 5,000; remove or downsize a rule group first
- Amplify association fails → switch to CLOUDFRONT-scope web ACL in us-east-1

---

## Verification Loop

Run after every web ACL create/update:

### 1. Verify CLOUDFRONT-scope web ACL is in us-east-1
```bash
aws wafv2 list-web-acls --scope CLOUDFRONT --region us-east-1
# Expected: web ACL appears; no CLOUDFRONT-scope ACLs exist outside us-east-1
```

### 2. Verify logging configuration
```bash
aws wafv2 get-logging-configuration --resource-arn <web-acl-arn>
# Expected: JSON with LogDestinationConfigs pointing to aws-waf-logs-* destination
# ResourceNotFoundException → logging not configured; add PutLoggingConfiguration immediately
```

### 3. Check WCU budget before deployment
```bash
aws wafv2 check-capacity --scope REGIONAL --rules file://rules.json
# Expected: returned capacity < 4,500 (leave headroom for future rules)
# Hard limit: 5,000; deployment fails above this
```

### 4. Verify managed rules are in Count mode (not yet Block)
```bash
aws wafv2 get-web-acl --name <acl-name> --scope REGIONAL --id <acl-id>
# Inspect each ManagedRuleGroupStatement: OverrideAction should be Count during validation
# Switch to None (use rule group default action) after 24-72h observation confirms no false positives
```

### 5. Verify Bot Control/ATP scope-down is configured (cost control)
```bash
# In web ACL JSON, confirm ManagedRuleGroupStatement for Bot Control / ATP / ACFP
# contains a ScopeDownStatement (e.g., UriPath starts with /api/ or /login)
# Scope-down prevents per-request charges for static assets and health checks
```

**Troubleshooting**:
- `WAFInvalidParameterException: CLOUDFRONT scope not in us-east-1` → move all CLOUDFRONT resources to us-east-1
- Capacity deployment error → run `check-capacity`; add scope-down statements to paid rule groups; remove unused rule groups
- Amplify WAF association fails → confirm web ACL is CLOUDFRONT scope created in us-east-1

---

## Quick Reference

**Essential CLI commands**:
```bash
# List web ACLs
aws wafv2 list-web-acls --scope REGIONAL --region <region>
aws wafv2 list-web-acls --scope CLOUDFRONT --region us-east-1

# Check WCU before deployment
aws wafv2 check-capacity --scope REGIONAL --rules file://rules.json

# Verify logging
aws wafv2 get-logging-configuration --resource-arn <web-acl-arn>

# List available managed rule groups
aws wafv2 list-available-managed-rule-groups --scope REGIONAL

# List rule group versions (for pinning in IaC)
aws wafv2 list-available-managed-rule-group-versions \
  --vendor-name AWS --name AWSManagedRulesCommonRuleSet --scope REGIONAL
```

**Critical limits**:

| Resource | Limit | Notes |
|---|---|---|
| WCU per web ACL | **5,000** (hard cap) | Cost boundary at 1,500; overage charged above |
| Rate-based rules per web ACL | 10 | Max 4 per rule group |
| Minimum rate-based threshold | 10 requests | |
| Max unique IPs tracked per rate-based rule | 10,000 | |
| IP addresses (CIDR) per IP set | 10,000 | |
| Geo match countries per rule | 50 | |
| Text transformations per statement | 10 | |
| Regex patterns per regex set | 10 | |
| Resource associations per web ACL | 100 (per Regional type) | |

**Pricing baseline** (USD; verify at https://aws.amazon.com/waf/pricing/):

| Item | Price |
|---|---|
| Web ACL | $5.00/month |
| Per rule | $1.00/month |
| Requests | $0.60/million |
| WCU overage (>1,500) | $0.20/million req per 500 WCU |
| Bot Control subscription | $10.00/month per web ACL |
| ATP or ACFP subscription | $10.00/month each per web ACL |
| CAPTCHA | $0.40/thousand attempts |

---

## Blueprints Directory Structure

```
StoryBeat/.claude/skills/securing-aws-waf-web-acls/
├── SKILL.md                         <- This file (guardrails + quick reference)
└── blueprints/
    └── evaluation-scenarios.md      <- 6 test cases for skill-evaluator
```

---

## External Resources

### Official Documentation
- [AWS WAF Developer Guide](https://docs.aws.amazon.com/waf/latest/developerguide/) — Primary reference
- [How AWS WAF works — resources](https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-resources.html) — Scope, resource types, Amplify exception (2026-08-26)
- [AWS WAF best practices](https://docs.aws.amazon.com/waf/latest/developerguide/best-practices.html) — Count-mode workflow, guardrails (2026-08-26)
- [AWS WAF capacity units](https://docs.aws.amazon.com/waf/latest/developerguide/aws-waf-capacity-units.html) — WCU limits and pricing boundary (2026-08-26)
- [AWS WAF quotas](https://docs.aws.amazon.com/waf/latest/developerguide/limits.html) — Fixed and adjustable limits (2026-08-26)
- [AWS WAF doc history](https://docs.aws.amazon.com/waf/latest/developerguide/doc-history.html) — 2025-2026 changelog (2026-08-26)

### Managed Rules & Bot/Fraud Control
- [AWS Managed Rules list](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-list.html) — All available managed rule groups (2026-08-26)
- [Bot Control managed rule group](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html) — WBA, v6.0/v6.1 changes (2026-08-26)
- [ATP managed rule group](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-atp.html) — Credential stuffing defense (2026-08-26)
- [ACFP managed rule group](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-acfp.html) — Registration fraud defense (2026-08-26)
- [AWS Managed Rules changelog](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-changelog.html) — Version history (2026-08-26)

### 2026 Features
- [AI traffic monetization](https://docs.aws.amazon.com/waf/latest/developerguide/waf-ai-traffic-monetization.html) — Monetize action, x402 (2026-08-26)
- [Bedrock AgentCore Gateway WAF (What's New 2026-06-29)](https://aws.amazon.com/about-aws/whats-new/2026/06/aws-waf-amazon-bedrock-agentcore/) — GA announcement (2026-08-26)
- [Dynamic label interpolation](https://docs.aws.amazon.com/waf/latest/developerguide/waf-dynamic-label-interpolation.html) — `${namespace:}` syntax (2026-08-26)

### Security & Governance
- [Firewall Manager WAF policies](https://docs.aws.amazon.com/waf/latest/developerguide/waf-policies.html) — Org-wide governance (2026-08-26)
- [Logging destinations](https://docs.aws.amazon.com/waf/latest/developerguide/logging-destinations.html) — CloudWatch Logs, S3, Firehose (2026-08-26)
- [AWS WAF pricing](https://aws.amazon.com/waf/pricing/) — Current pricing (2026-08-26)
- [Associating with AWS resources](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-associating-aws-resource.html) — Scope rules, Cognito restriction (2026-08-26)
