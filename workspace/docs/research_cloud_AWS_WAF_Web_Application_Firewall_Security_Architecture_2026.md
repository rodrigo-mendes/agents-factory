# AWS WAF — Security Architecture: WAF Web Application Firewall (AWS WAF 2026)

## Metadata
```yaml
Full_Name: "AWS Security Architecture — WAF Web Application Firewall"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture - WAF Web Application Firewall"
Target_Edition: "AWS WAF 2026"
Architecture_Context: "Internet-facing production workloads (general); ARCHITECTURE_CONTEXT not supplied by caller — patterns are written provider-canonical, not tenant-specific"
Official_Source_URL: "https://docs.aws.amazon.com/waf/latest/developerguide/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-26"
Currency_Threshold: "2027-08-26"
Research_Depth: "exhaustive"
Max_Iterations: 5
```

> **⚠️ Scope note:** `ARCHITECTURE_CONTEXT` was not provided in the arguments. This research is written to be provider-canonical (valid for any internet-facing production workload on AWS). Before applying compliance-specific (SOC2/HIPAA/PCI-DSS) or cost-committed guidance, re-scope with the architect (see Ask-First section).

---

## Executive Summary

**AWS WAF 2026** is AWS's managed web application firewall service that provides fine-grained control over HTTP(S) requests to protected resources. The core construct is the **web ACL** (also called a "protection pack" in the 2026 console), which contains rules evaluated in priority order; the first terminating match determines the action applied (Allow, Block, Count, CAPTCHA, Challenge, or the new CloudFront-only **Monetize** action). AWS WAF integrates with ten resource types — Amazon CloudFront, API Gateway REST API, Application Load Balancer, AWS AppSync, Amazon Cognito user pools, AWS App Runner, **Amazon Bedrock AgentCore Gateway** (GA June 2026), AWS Verified Access, and AWS Amplify — plus Amazon CloudWatch as a monitoring target. [Source: [How AWS WAF works — resources](https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-resources.html), accessed 2026-08-26]

**What changed most in the 2026 edition** is concentrated in three areas: (1) **AI bot management** — Bot Control v6.1 (July 2026) expands detection across advertising, AI, content fetcher, and SEO categories, and Web Bot Authentication (WBA) cryptographic verification for AI agents, which was CloudFront-only in Bot Control v4.0 (Nov 2025), has been expanded to all regional resources in v6.0 (May 2026); (2) **AI traffic monetization** — a new Monetize action (GA June 2026) lets CloudFront-backed publishers price, meter, and collect x402 payments from AI bots/agents at the edge; (3) **agentic workload protection** — AWS WAF can now directly protect Amazon Bedrock AgentCore Gateway. Additionally, the **simplified console / "protection packs" rename** (GA June 2025) reduces configuration steps by ~80% via use-case pre-configured packs, and **dynamic label interpolation** (April 2026) enables one rule to handle an entire label namespace. [Source: [AWS WAF doc history](https://docs.aws.amazon.com/waf/latest/developerguide/doc-history.html), accessed 2026-08-26]

**The three most critical architecture guardrails** for internet-facing production workloads are: (1) **deploy managed rules in Count mode first** — never push a new rule group directly to Block without a validation period, because AWS WAF applies rules to all matching traffic immediately; (2) **understand the CLOUDFRONT vs REGIONAL scope boundary** — a web ACL and all its resources (rule groups, IP sets, regex sets) must be created in the same scope/region as the protected resource, and CLOUDFRONT scope must always be in us-east-1; (3) **plan WCU budgets explicitly** — 5,000 WCUs is the hard cap per web ACL, cost increases above 1,500 WCUs, and intelligent threat mitigation rule groups (Bot Control, ATP, ACFP) carry separate subscription fees. [Source: [AWS WAF best practices](https://docs.aws.amazon.com/waf/latest/developerguide/best-practices.html), accessed 2026-08-26]

---

## Cloud Architecture Glossary

```
Term: Web ACL (Protection Pack)
Definition: The primary AWS WAF resource — a container for rules that evaluates HTTP(S) requests to associated protected resources. The 2026 console calls it a "protection pack"; the API/CloudFormation term remains "WebACL" (AWS::WAFv2::WebACL).
Provider Docs Section: web-acl
Architect Usage: Create one web ACL per logical protection boundary; associate it with the resource(s) to protect. Default action (Allow/Block) applies when no rule terminates evaluation.
Common Confusion: "Protection pack" and "web ACL" are the same resource — the rename is cosmetic. The API/IaC term is still WebACL. Do not confuse scope (CLOUDFRONT/REGIONAL) with environment (prod/staging).
```
```
Term: Scope (CLOUDFRONT vs REGIONAL)
Definition: A web ACL and all its referenced resources must be created in a single scope. CLOUDFRONT scope must be in us-east-1 (AWS Global); REGIONAL scope must be in the same Region as the protected resource.
Provider Docs Section: how-aws-waf-works-resources
Architect Usage: Use CLOUDFRONT scope for CloudFront distributions and Amplify apps (even though Amplify is "regional"). Use REGIONAL scope for all other resource types.
Common Confusion: AWS Amplify appears in the Regional resource type list but requires a CLOUDFRONT-scope web ACL created in us-east-1 — NOT a Regional web ACL.
```
```
Term: Web ACL Capacity Unit (WCU)
Definition: AWS WAF's unit measuring compute cost of rules, rule groups, and text transformations in a web ACL. Does not affect how traffic is inspected. Max per web ACL: 5,000 (fixed). Pricing boundary: 1,500 WCUs included in base price; overages billed above 1,500.
Provider Docs Section: aws-waf-capacity-units
Architect Usage: Budget WCUs before adding rule groups; use the CheckCapacity API to compute. CRS uses 700 WCU; Bot Control 50 WCU; ATP/ACFP 50 WCU each.
Common Confusion: "1,500 WCU max" is a common misconception — 1,500 is the free-tier boundary; the actual hard maximum is 5,000 WCUs. Exceeding 1,500 costs more but does not break deployment.
```
```
Term: Rule Action
Definition: What AWS WAF does when a rule matches a request. Terminating actions (Allow, Block, Monetize) stop evaluation immediately. Non-terminating actions (Count) continue to subsequent rules. CAPTCHA and Challenge are non-terminating if the request has a valid token, otherwise terminating (blocks).
Provider Docs Section: waf-rule-action
Architect Usage: Use Count to observe traffic patterns before enforcing. Use Block for absolute denial. Use Challenge for silent browser verification. Use CAPTCHA when human proof is required.
Common Confusion: CAPTCHA and Challenge are often assumed to always block — they only block when the request lacks a valid unexpired token. With a valid token they behave like Count and do not stop evaluation.
```
```
Term: Rule Group
Definition: A reusable set of rules with an immutable WCU capacity setting, added to a web ACL. Cannot contain another rule group reference statement (no nesting rule groups). Has no default action. Not directly associated with resources.
Provider Docs Section: waf-rule-groups
Architect Usage: Use to share common rule logic across multiple web ACLs. Remember the WCU capacity is fixed at rule group creation and counts toward the web ACL's 5,000 WCU limit.
Common Confusion: Rule groups cannot be nested inside other rule groups. A rule group statement can only appear inside a web ACL, not inside another rule group.
```
```
Term: Rate-Based Rule
Definition: Aggregates request counts over a configurable window (60/120/300/600 s; default 300 s) per aggregation key (IP, ASN, custom keys) and triggers an action when the rate exceeds a threshold. Minimum threshold: 10. Not nestable in other statements.
Provider Docs Section: waf-rule-statement-type-rate-based
Architect Usage: Use to throttle volumetric traffic by source IP, ASN, or custom keys (JA3/JA4 fingerprints, cookie, header, URI path). Add a scope-down statement to limit which requests count toward the rate.
Common Confusion: Rate-based rules cannot use Allow as their action. The evaluation window is a lookback period, not a fixed time slot — AWS WAF evaluates frequently within the window.
```
```
Term: Label
Definition: Metadata added to a request when a rule matches, persisting only for the duration of web ACL evaluation. Available to subsequent rules via a label match statement. All AWS Managed Rules add labels.
Provider Docs Section: waf-labels
Architect Usage: Use labels to set rules to Count (plus label) then react in a subsequent rule using a label match — enables multi-stage evaluation before blocking. Use as a rate-based aggregation key.
Common Confusion: Labels are ephemeral — they exist only during web ACL evaluation of a single request. They are not stored or passed to the backend application.
```
```
Term: Bot Control
Definition: Paid intelligent-threat-mitigation managed rule group (AWSManagedRulesBotControlRuleSet, WCU 50) that detects and manages bot traffic. Two tiers: Common (self-identifying bots, static analysis) and Targeted (sophisticated bots via fingerprinting, ML, rate limiting, and CAPTCHA/Challenge).
Provider Docs Section: aws-managed-rule-groups-bot
Architect Usage: Add Bot Control when you need to differentiate human from automated traffic. Use Common for general bot suppression; Targeted for scraper/credential-stuffing defense. Always deploy in Count mode first.
Common Confusion: Bot Control v6.1 (Jul 2026) and WBA are two separate things — Bot Control detects/blocks bots; Web Bot Authentication (WBA) cryptographically verifies legitimate AI agents. WBA-verified bots are auto-allowlisted in CategoryAI.
```
```
Term: Web Bot Authentication (WBA)
Definition: Cryptographic bot verification mechanism within Bot Control (v4.0+) that lets legitimate AI bots/agents prove their identity. Adds labels bot:web_bot_auth:{verified|invalid|expired|unknown_bot}. WBA-verified bots are not matched by TGT_TokenAbsent.
Provider Docs Section: aws-managed-rule-groups-bot (v4.0 changelog)
Architect Usage: Use when you want to allow verified AI agents (e.g., Bedrock AgentCore) while blocking unverified bots. Available for CloudFront (v4.0, Nov 2025) and all regional WAF (v6.0, May 2026).
Common Confusion: WBA is not the same as the Monetize action — WBA verifies identity; Monetize charges AI traffic. Both can coexist in a web ACL.
```
```
Term: AI Traffic Monetization
Definition: 2026 feature (Monetize action, CloudFront-only) that returns HTTP 402 Payment Required with x402 payment instructions to AI bots/agents, enabling publishers to price, meter, and collect micropayments at the edge. Requires MonetizationConfig on the web ACL.
Provider Docs Section: waf-ai-traffic-monetization
Architect Usage: Use on CloudFront web ACLs to charge AI crawlers/agents per request. Cannot be used as a rate-based rule action. Min price: $0.00001/request; max: $100/request.
Common Confusion: The Monetize action is terminating and CloudFront-only. It cannot be used in Regional web ACLs or as a rate-based rule action.
```
```
Term: Scope-Down Statement
Definition: A nestable statement added inside a managed rule group statement or rate-based statement to narrow which requests are passed to the containing rule. Adds no WCU cost of its own.
Provider Docs Section: waf-rule-scope-down-statements
Architect Usage: Use to restrict Bot Control or ATP/ACFP to specific URIs or request patterns, reducing both false positives and per-request processing costs for pay-per-request rule groups.
Common Confusion: Text transformations and forwarded-IP configs in a scope-down apply only to the scope-down; the containing rule receives the original, unmodified request.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Deploy managed rules and new rules in Count mode before enforcing Block**
- Pillar Alignment: Security; Reliability (AWS Well-Architected)
- Why: AWS WAF applies rules immediately to all matching production traffic. Without a Count-mode validation period you risk false-positive blocking of legitimate users. Count mode lets you inspect sampled requests and CloudWatch metrics without impact.
- AWS Services: AWS WAF (web ACL, Count action override), Amazon CloudWatch (AllowedRequests, BlockedRequests, CountedRequests metrics), AWS WAF Sampled Requests.
- Architecture Decision: For every new rule group or rule, set the action to Count (or override rule group rules to Count) during an initial observation window (typically 24–72 hours). Monitor BlockedRequests/CountedRequests metrics and sampled requests. Switch to Block only after confirming legitimate traffic is not caught.
- Verification: Console → web ACL → Sampled Requests tab → verify Count matches (not Block); CloudWatch namespace `AWS/WAFV2` metric `CountedRequests` by rule dimension; no legitimate traffic appearing in sampled blocked requests.
- Source: [AWS WAF best practices](https://docs.aws.amazon.com/waf/latest/developerguide/best-practices.html), accessed 2026-08-26. `[✓✓ Triangulated | Best practices doc + waf-rule-action page]`

**Create CLOUDFRONT-scope web ACLs exclusively in us-east-1**
- Pillar Alignment: Reliability; Operational Excellence
- Why: AWS WAF enforces that CLOUDFRONT-scope web ACLs and all referenced resources (rule groups, IP sets, regex pattern sets) are created in us-east-1. A CLOUDFRONT-scope web ACL created in any other region cannot be associated with a CloudFront distribution; deployment will fail.
- AWS Services: AWS WAF (CLOUDFRONT scope), Amazon CloudFront, AWS Amplify (uses CLOUDFRONT scope despite being a regional service).
- Architecture Decision: Tag all IaC (CloudFormation, Terraform) for CloudFront and Amplify WAF resources with region = us-east-1. When using the CLI, always include `--scope=CLOUDFRONT --region=us-east-1`. Use separate provider/region configuration blocks for WAF vs regional resources.
- Verification: `aws wafv2 list-web-acls --scope CLOUDFRONT --region us-east-1` returns the web ACL. Any CloudFront distribution has a WAFWebACLArn pointing to a us-east-1 ARN.
- Source: [How AWS WAF works — resources](https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-resources.html) and [CreateWebACL API](https://docs.aws.amazon.com/waf/latest/APIReference/API_CreateWebACL.html), accessed 2026-08-26.

**Enable logging for all web ACLs and monitor CloudWatch metrics**
- Pillar Alignment: Security; Operational Excellence
- Why: Without logging you lose the ability to tune rules, investigate incidents, and demonstrate compliance. Logging is best-effort (rare drops are possible), so alerting on CloudWatch metrics provides a real-time complement. Logging has an additional charge beyond WAF usage fees.
- AWS Services: AWS WAF (PutLoggingConfiguration), Amazon CloudWatch Logs / Amazon S3 / Amazon Data Firehose (logging destinations), Amazon CloudWatch (metrics + alarms), AWS CloudTrail (API audit).
- Architecture Decision: Choose a logging destination whose name starts with `aws-waf-logs-`. Use CloudWatch Logs for low-latency log exploration via the 2026 console log explorer; use S3 + Athena for long-term analysis. Configure CloudWatch alarms on `BlockedRequests` spikes. Enable CloudTrail for all AWS WAF API calls.
- Verification: `aws wafv2 get-logging-configuration --resource-arn <web-acl-arn>` returns a logging configuration. CloudWatch namespace `AWS/WAFV2` has data for the web ACL. CloudTrail logs show CreateWebACL, PutLoggingConfiguration events.
- Source: [AWS WAF logging destinations](https://docs.aws.amazon.com/waf/latest/developerguide/logging-destinations.html) + [WAF monitoring with CloudWatch](https://docs.aws.amazon.com/waf/latest/developerguide/monitoring-cloudwatch.html), accessed 2026-08-26.

**Use AWS Managed Rules as the baseline for every web ACL**
- Pillar Alignment: Security
- Why: AWS Managed Rules provide AWS-maintained, continuously updated protection for common attack vectors (OWASP Top 10, known bad inputs, IP reputation). Building equivalent rules from scratch requires significant security expertise and operational maintenance.
- AWS Services: AWS WAF (`AWSManagedRulesCommonRuleSet` 700 WCU, `AWSManagedRulesKnownBadInputsRuleSet` 200 WCU, `AWSManagedRulesAmazonIpReputationList` 25 WCU).
- Architecture Decision: Start with CRS (core rule set) + Known Bad Inputs + Amazon IP Reputation List as the baseline (925 WCU combined). Add use-case specific groups (SQLi, Linux/POSIX, Windows, PHP, WordPress) as needed. Subscribe to managed rule group SNS notifications to stay ahead of version changes (IP reputation groups do not provide SNS updates).
- Verification: `aws wafv2 list-available-managed-rule-groups --scope REGIONAL` shows available groups; web ACL config includes the three baseline groups; SNS subscription exists for the AWS Managed Rules topic.
- Source: [AWS Managed Rules list](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-list.html) + [baseline rule groups](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-baseline.html), accessed 2026-08-26.

**Plan WCU budget explicitly before adding rule groups to a web ACL**
- Pillar Alignment: Cost Optimization; Reliability
- Why: The 5,000 WCU hard cap per web ACL is immutable. Exceeding it causes deployment failures. Cost increases above 1,500 WCUs ($0.20/million requests per additional 500 WCUs). Intelligent threat mitigation groups (Bot Control, ATP, ACFP) carry separate subscription fees in addition to WCU costs.
- AWS Services: AWS WAF (CheckCapacity API), Amazon CloudWatch (usage metrics in `AWS/Usage` namespace — `ResourceCount` with dimension `Resource = WebAclsPerAccountRegional`).
- Architecture Decision: Use `aws wafv2 check-capacity` before adding rule groups. Track running WCU total: CRS (700) + Known Bad Inputs (200) + IP Rep (25) + Anonymous IP (50) + SQLi (200) + Bot Control (50) = 1,225 WCU baseline for a full-stack web app. Leave headroom for custom rules and rate-based rules (+30 WCU per custom aggregation key).
- Verification: `aws wafv2 check-capacity --scope REGIONAL --rules <json>` returns estimated WCU. Web ACL total WCU is visible in the console and must be < 5,000.
- Source: [AWS WAF capacity units](https://docs.aws.amazon.com/waf/latest/developerguide/aws-waf-capacity-units.html) + [WAF quotas](https://docs.aws.amazon.com/waf/latest/developerguide/limits.html), accessed 2026-08-26.

### ⚠️ Architectural Decisions

**Bot Control tier: Common vs Targeted**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Common | Bot Control (AWSManagedRulesBotControlRuleSet, Common) | Cost (lower per-request fees; first 10M/month free) | Does not detect sophisticated bots that don't self-identify | General bot suppression; public marketing sites |
  | Targeted | Bot Control (AWSManagedRulesBotControlRuleSet, Targeted) | Sophisticated bot detection (ML + fingerprinting + CAPTCHA/Challenge) | Higher cost (first 1M/month free; per-request after) | Login pages, API endpoints, scraping targets, anything with credential stuffing risk |

- Cost Profile: Both require $10/month Bot Control subscription per web ACL. Common: first 10M requests/month free. Targeted: first 1M requests/month free, then per-million (verify current tier rate on pricing page — see unverified items §21).
- Lock-in Assessment: AWS-native; switching between Common and Targeted is a rule group configuration change.
- Architect Instruction: "Ask whether the endpoint is targeted by sophisticated bots (scrapers, credential stuffers) — if yes, Targeted is required. If general automation suppression for a public page is sufficient, Common is adequate and cheaper."
- Source: [Bot Control managed rule group](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html), accessed 2026-08-26.

**Fraud Control: ATP vs ACFP vs neither**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Account Takeover Prevention (ATP) | AWSManagedRulesATPRuleSet (WCU 50, $10/mo) | Credential-stuffing detection against stolen-credential database; response inspection on CloudFront | Cost; not available for Cognito user pools | Apps with a login endpoint attacked by credential stuffers |
  | Account Creation Fraud Prevention (ACFP) | AWSManagedRulesACFPRuleSet (WCU 50, $10/mo) | Bulk fraudulent account creation detection (aggregates by IP/session/phone/address) | Cost; not available for Cognito user pools | Apps with a sign-up endpoint targeted by fraud rings |
  | Neither | Custom rate-based + IP reputation rules | Cost | Less precise fraud signal | Low-traffic / internal apps |

- Cost Profile: Each is $10/month subscription per web ACL + tiered per-request fees (10,000 requests/month free; then tiered from $1,000/million down to $50/million).
- Lock-in Assessment: AWS-native paid managed rule groups; response inspection requires CloudFront.
- Architect Instruction: "Ask whether login-endpoint credential stuffing or registration fraud has been observed in traffic or is a business risk. If yes, ATP/ACFP add significant detection beyond what rate-based rules alone provide."
- Source: [ATP managed rule group](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-atp.html) + [ACFP managed rule group](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-acfp.html), accessed 2026-08-26.

**L7 protection placement: CloudFront edge vs ALB regional vs both**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | CloudFront edge only | CloudFront + WAF (CLOUDFRONT scope, us-east-1) | Blocks at edge, reduces origin load; global cache | Cannot protect non-CloudFront paths; CloudFront added latency | Browser-facing apps where all traffic routes through CloudFront |
  | ALB regional only | ALB + WAF (REGIONAL scope) | Simpler topology; covers non-cached API traffic | Attack reaches the region; no edge-level filtering | Internal APIs or apps where CloudFront is not feasible |
  | Both (defense in depth) | CloudFront + WAF + ALB + WAF | Edge filters volumetric attacks; ALB WAF catches escaped traffic | Two separate web ACL costs + rule duplication | High-value internet-facing apps; regulated environments |

- Cost Profile: Each web ACL = $5/month + $1/rule/month + $0.60/million requests. Running two (CloudFront + ALB) doubles baseline WAF costs.
- Lock-in Assessment: WAF is AWS-native; defense-in-depth adds flexibility for future topology changes.
- Architect Instruction: "For internet-facing production apps, prefer defense in depth (CloudFront WAF + ALB WAF). The CloudFront WAF filters the majority of bot/DDoS traffic before it reaches the region; the ALB WAF is the last line of defense for traffic that bypasses CloudFront."
- Source: [How AWS WAF works — resources](https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-resources.html), accessed 2026-08-26.

**Rate-based rule evaluation window**
- Options:

  | Option | Window | Optimizes | Sacrifices | Best When |
  |--------|--------|-----------|------------|-----------|
  | 60 s | 1 min | Fastest response to spikes | May trigger on brief legitimate bursts | DDoS or flash-crowd scenarios |
  | 300 s (default) | 5 min | Balanced; good for sustained attacks | Slower reaction to brief spikes | General rate limiting |
  | 600 s | 10 min | Smooths out legitimate burst patterns | Slowest reaction | APIs with variable but predictable peak loads |

- Architect Instruction: "Ask whether the attack profile is short, sharp bursts (favor 60 s) or sustained floods (300 s or 600 s). Set the threshold based on observed p99 request rates in CloudWatch, not guesses."
- Source: [Rate-based rule high-level settings](https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based-high-level-settings.html), accessed 2026-08-26.

**Managed rule group centralization: Firewall Manager vs per-account web ACLs**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Per-account web ACLs | AWS WAF (per account) | Full per-app customization | Drift; no auto-remediation; no OU/account-wide enforcement | Small number of accounts; highly differentiated security profiles |
  | Firewall Manager WAF policy | AWS Firewall Manager + AWS Organizations | Org-wide enforcement; auto-remediation; auto-applies to new accounts/resources | Less per-account flexibility; requires Firewall Manager admin setup | Multi-account Organizations; regulated environments needing proven coverage |

- Architect Instruction: "For any organization with 5+ accounts or regulatory coverage requirements, Firewall Manager WAF policies are strongly preferred. The auto-remediation and new-resource auto-enrollment close the coverage gap that manual management misses."
- Source: [Firewall Manager WAF policies](https://docs.aws.amazon.com/waf/latest/developerguide/waf-policies.html), accessed 2026-08-26.

### 🚫 Anti-Patterns

**Deploying a new rule group or rule directly in Block without a Count-mode validation period**
- Risk Level: HIGH
- Why: Security/Reliability — AWS WAF applies rules to all matching production traffic immediately. A rule that incorrectly classifies legitimate requests as threats will block real users with no warning.
- ❌ Wrong: Adding `AWSManagedRulesCommonRuleSet` with action BLOCK directly in a production web ACL without Count-mode testing.
- ✅ Correct: Add `AWSManagedRulesCommonRuleSet` with override action Count; monitor sampled requests and CloudWatch CountedRequests metric for 24–72 hours; check for legitimate traffic in the sample; then switch to BLOCK after confirming no false positives.
- Detection: Web ACL rules show BLOCK action for a managed rule group with no prior CountedRequests history in CloudWatch; sampled requests include any legitimate traffic patterns.
- Impact: Service outage for legitimate users; blocked traffic returns HTTP 403 with no automatic recovery.
- Source: [AWS WAF best practices](https://docs.aws.amazon.com/waf/latest/developerguide/best-practices.html), accessed 2026-08-26.

**Creating a CLOUDFRONT-scope web ACL outside of us-east-1**
- Risk Level: HIGH
- Why: Reliability — AWS WAF enforces that CLOUDFRONT-scope resources are in us-east-1. Attempting to associate a web ACL created in another region with a CloudFront distribution will fail with an error.
- ❌ Wrong: IaC that creates `AWS::WAFv2::WebACL` with `Scope: CLOUDFRONT` in `eu-west-1`; CloudFormation stack deploy fails with association error.
- ✅ Correct: All `Scope: CLOUDFRONT` WAF resources (web ACL, rule groups, IP sets, regex pattern sets) deployed in `us-east-1`. In Terraform: separate `provider "aws" { alias = "us_east_1" region = "us-east-1" }` for WAF and CloudFront resources.
- Detection: `aws wafv2 list-web-acls --scope CLOUDFRONT --region eu-west-1` returns empty or error; WAF association to CloudFront fails.
- Impact: Blocked deployment; if misconfigured previously, CloudFront distribution has no WAF protection.
- Source: [CreateWebACL API — Scope](https://docs.aws.amazon.com/waf/latest/APIReference/API_CreateWebACL.html), accessed 2026-08-26.

**Using AWS Amplify with a REGIONAL-scope web ACL**
- Risk Level: HIGH
- Why: Reliability — Amplify is listed in the Regional resource type docs but is an exception: it requires a CLOUDFRONT-scope web ACL created in us-east-1. A REGIONAL web ACL cannot be associated with an Amplify app.
- ❌ Wrong: Creating a REGIONAL web ACL in ap-southeast-1 and associating it with an Amplify app.
- ✅ Correct: Create a CLOUDFRONT-scope web ACL in us-east-1 and associate it with the Amplify app.
- Detection: AssociateWebACL call for an Amplify app ARN using a REGIONAL web ACL returns an error.
- Impact: Amplify app has no WAF protection; deployment fails.
- Source: [How AWS WAF works — resources](https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-resources.html), accessed 2026-08-26.

**Using ATP or ACFP managed rule groups with a Cognito user pool**
- Risk Level: MEDIUM
- Why: Security/Reliability — AWS WAF explicitly prohibits associating a web ACL that contains the ATP (`AWSManagedRulesATPRuleSet`) or ACFP (`AWSManagedRulesACFPRuleSet`) managed rule groups with an Amazon Cognito user pool. The association will fail.
- ❌ Wrong: Web ACL containing `AWSManagedRulesATPRuleSet` associated with a Cognito user pool.
- ✅ Correct: Use a separate web ACL without ATP/ACFP for Cognito user pool associations; protect the ATP/ACFP login/registration endpoints at the ALB or API Gateway layer instead.
- Detection: AssociateWebACL for Cognito user pool ARN with a web ACL containing ATP/ACFP returns an error.
- Impact: Blocked deployment; Cognito user pool is unprotected while the team troubleshoots.
- Source: [Associating AWS WAF with an AWS resource](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-associating-aws-resource.html), accessed 2026-08-26.

**Associating a CloudFront web ACL with any Regional resource type**
- Risk Level: MEDIUM
- Why: Reliability — a web ACL that has been associated with a CloudFront distribution cannot be associated with any other resource type. Attempting to do so returns an error.
- ❌ Wrong: Reusing a CloudFront web ACL by also associating it with an ALB.
- ✅ Correct: Create separate web ACLs for CloudFront (CLOUDFRONT scope, us-east-1) and ALB (REGIONAL scope, same region as ALB).
- Detection: AssociateWebACL for ALB ARN using the CloudFront web ACL ARN returns an error about resource type exclusivity.
- Impact: Blocked operation; architects incorrectly believe one web ACL covers both layers.
- Source: [Associating AWS WAF with an AWS resource](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-associating-aws-resource.html), accessed 2026-08-26.

**Ignoring WCU limits until deployment fails**
- Risk Level: MEDIUM
- Why: Cost Optimization; Reliability — the 5,000 WCU hard cap per web ACL is a fixed constraint. Rule groups over the cap cannot be added; once the limit is approached, adding new rules requires removing existing ones. Cost increases silently above 1,500 WCUs.
- ❌ Wrong: Adding rule groups ad hoc without tracking WCU totals; discovering the 5,000 cap at deployment time in production.
- ✅ Correct: Maintain a WCU budget document (or IaC output); use `aws wafv2 check-capacity` in CI/CD as a gate; set a CloudWatch alarm on `AWS/Usage ResourceCount WebAclsPerAccountRegional` approaching quota limits.
- Detection: `aws wafv2 check-capacity` returns WCU > 5,000 for the planned rule set; deployment fails with a capacity error.
- Impact: Blocked production deployment; cost overrun above 1,500 WCUs without visibility.
- Source: [AWS WAF capacity units](https://docs.aws.amazon.com/waf/latest/developerguide/aws-waf-capacity-units.html) + [WAF quotas](https://docs.aws.amazon.com/waf/latest/developerguide/limits.html), accessed 2026-08-26.

**Disabling logging on web ACLs**
- Risk Level: MEDIUM
- Why: Security; Operational Excellence — without logging, you have no record of what traffic was blocked, counted, or allowed. Tuning rules, investigating incidents, and meeting compliance requirements all depend on WAF logs.
- ❌ Wrong: Production web ACL with no PutLoggingConfiguration set; relying only on sampled requests (limited to 100 requests per rule per 3 hours).
- ✅ Correct: All production web ACLs have a logging configuration pointing to an `aws-waf-logs-*` destination. For compliance environments, log to both CloudWatch Logs (real-time analysis) and S3 (long-term retention + Athena).
- Detection: `aws wafv2 get-logging-configuration --resource-arn <web-acl-arn>` returns a ResourceNotFoundException.
- Impact: No visibility into blocked requests; incident investigation is blind; compliance audit failure.
- Source: [AWS WAF logging management](https://docs.aws.amazon.com/waf/latest/developerguide/logging-management.html), accessed 2026-08-26.

---

## Cloud-Native Design Patterns

**Defense-in-depth WAF at edge and regional tier**
- Category: Security
- Problem: HTTP attacks (SQLi, XSS, bot floods, credential stuffing) that bypass network-layer controls and target application logic.
- Solution on AWS: CloudFront (CLOUDFRONT-scope WAF with CRS + Bot Control + Anti-DDoS AMR) → ALB (REGIONAL-scope WAF with CRS + use-case managed rules + rate-based rules) → private application tier. CloudFront WAF absorbs volumetric bot/flood traffic at the edge; ALB WAF catches traffic that bypasses CloudFront (e.g., direct-to-ALB).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Two independent inspection layers; edge filters save origin compute | Two web ACL costs ($5/mo each) + rule duplication risk |
  | Latency | Volumetric attacks absorbed before entering the region | Marginal added latency at each inspection point |
  | Ops | Separate tuning of edge vs regional policies | More rules to maintain; drift between the two |

- Source: [How AWS WAF works — resources](https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-resources.html) + [best practices](https://docs.aws.amazon.com/waf/latest/developerguide/best-practices.html), accessed 2026-08-26.

**Label-based multi-stage evaluation (Count + Label → Block)**
- Category: Security; Flexibility
- Problem: A single rule that blocks on first match may over-block legitimate traffic; you want multiple signals to combine before taking a terminating action.
- Solution on AWS: Set early rules (e.g., managed rule groups) to Count + add a label. Write a subsequent label match rule that fires only when two or more earlier labels are present (via AND logic). The label match rule takes the terminating Block action.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Precision | Reduces false positives by requiring multiple correlated signals | Adds WCU overhead; requires careful label-namespace design |
  | Flexibility | Allows different rules to contribute signals without independently blocking | More complex rule logic to maintain |

- Source: [AWS WAF labels](https://docs.aws.amazon.com/waf/latest/developerguide/waf-labels.html), accessed 2026-08-26.

**AI bot management with WBA allowlisting and Monetize charging**
- Category: Security; Revenue
- Problem: AI crawlers/agents (GPTBot, ClaudeBot, Amazon Nova) accessing content; need to differentiate legitimate verified AI agents from scrapers, and optionally charge AI agents for access.
- Solution on AWS (2026): Enable Bot Control Targeted with WBA support (v6.0+). WBA-verified AI bots receive `bot:web_bot_auth:verified` label and are auto-allowlisted in `CategoryAI`. For CloudFront distributions, optionally add a Monetize action rule that fires on `bot:category:ai` and `bot:web_bot_auth:verified` to return HTTP 402 x402 payment instructions to paying AI agents.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Precision | Verified AI agents pass; unverified scrapers blocked | Bot Control Targeted subscription + per-request fees |
  | Revenue | Monetize action converts AI traffic to micropayment revenue | CloudFront-only; requires MonetizationConfig; cannot use as rate-based action |
  | Ops | Auto-allowlisting reduces manual exception management | Monitoring `bot:web_bot_auth:*` labels requires log/metric setup |

- Source: [Bot Control v6.0 changelog](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-changelog.html) + [AI traffic monetization](https://docs.aws.amazon.com/waf/latest/developerguide/waf-ai-traffic-monetization.html), accessed 2026-08-26.

**Scope-down statement to limit paid-rule-group inspection to high-value paths**
- Category: Cost Optimization
- Problem: Bot Control and ATP/ACFP are charged per request processed. Running them on all traffic (including static assets, health checks, favicon.ico) is expensive and unnecessary.
- Solution on AWS: Add a scope-down statement inside the Bot Control / ATP / ACFP managed rule group reference that narrows processing to specific URI prefixes (e.g., `/api/`, `/login`, `/signup`). Only requests matching the scope-down are evaluated by the containing rule; others skip it entirely.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost | Significant reduction in per-request charges for intelligent threat groups | Bot/fraud activity targeting non-scoped paths is not inspected |
  | Precision | Focuses inspection on high-value attack surfaces | Requires knowing and maintaining the list of sensitive URI paths |

- Source: [Scope-down statements](https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-scope-down-statements.html), accessed 2026-08-26.

---

## Security Architecture

**Web application threat defense layers**
- AWS Services: AWS WAF (L7 filtering — SQLi, XSS, RCE, bot control, rate limiting), AWS Managed Rules (CRS, Known Bad Inputs, IP Reputation, SQLi, Bot Control), AWS Shield / Shield Advanced (L3/L4/L7 DDoS, with Anti-DDoS AMR), Amazon CloudFront (edge TLS termination + WAF integration), Amazon Cognito (identity — protect user pool with REGIONAL-scope web ACL without ATP/ACFP), AWS Firewall Manager (org-wide WAF governance).
- Architecture: CloudFront (edge) → CLOUDFRONT-scope WAF (CRS + Bot Control + IP Rep + Anti-DDoS AMR) → ALB or API Gateway (regional) → REGIONAL-scope WAF (CRS + use-case rules + ATP/ACFP + rate-based rules) → application.
- Compliance Alignment: Supports AWS Well-Architected Security pillar (SEC 05 — protect network layers; SEC 06 — protect compute layers). CRS covers OWASP Top 10 categories. Framework reference only — not legal compliance certification. Re-scope for SOC2/PCI-DSS/HIPAA before asserting specific control coverage.
- Source: [AWS WAF Developer Guide](https://docs.aws.amazon.com/waf/latest/developerguide/) + [best practices](https://docs.aws.amazon.com/waf/latest/developerguide/best-practices.html), accessed 2026-08-26.

**Credential and account fraud defense**
- AWS Services: AWS WAF ATP (`AWSManagedRulesATPRuleSet`) for login-endpoint credential stuffing, ACFP (`AWSManagedRulesACFPRuleSet`) for registration fraud, Bot Control Targeted for volumetric automated attacks, CAPTCHA/Challenge actions for human verification, Amazon Cognito (protect with WAF — REGIONAL scope, no ATP/ACFP).
- Architecture: Login endpoint → ATP rule group (scope-down to `/login` URI) → response inspection (CloudFront only, 64 KB) → labels on suspicious sessions → rate-based rule on session labels → CAPTCHA challenge for threshold breaches.
- Source: [ATP](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-atp.html) + [ACFP](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-acfp.html), accessed 2026-08-26.

---

## Operational Patterns

**WAF rule lifecycle: Count → Block → Monitor**
- RTO/RPO: Not applicable (WAF is a filtering control, not a data recovery mechanism). Target: zero legitimate user impact after rule promotion to Block.
- AWS Services: AWS WAF (action overrides, Count mode), Amazon CloudWatch (metrics, alarms), AWS WAF Sampled Requests, Amazon Athena (S3 log analysis for deep investigation).
- Cost Profile: Low — CloudWatch metric queries are near-free; Athena queries are priced per data scanned. Bot Control and ATP/ACFP add per-request costs during validation.
- Automation: Automate Count-mode deployment via IaC (action override = Count). Manual decision point: promote to Block only after human review of sampled requests and CountedRequests metrics.
- Source: [AWS WAF best practices](https://docs.aws.amazon.com/waf/latest/developerguide/best-practices.html), accessed 2026-08-26.

**Managed rule group version management**
- RTO/RPO: Not applicable.
- AWS Services: AWS WAF (ListAvailableManagedRuleGroupVersions API, SNS version update notifications), Amazon SNS, AWS WAF changelog.
- Cost Profile: Low — SNS subscriptions and API calls are inexpensive.
- Automation: Subscribe to the AWS Managed Rules SNS topic to receive version-change notifications. Pin specific static versions in production IaC; test new versions in a staging web ACL (with the same Count-mode workflow) before pinning to production.
- Key constraint: **IP reputation rule groups do NOT provide SNS notifications or versioning** — they auto-update silently.
- Source: [Managed rule group versioning](https://docs.aws.amazon.com/waf/latest/developerguide/waf-managed-rule-groups-versioning.html), accessed 2026-08-26.

**Cross-account WAF governance with Firewall Manager**
- RTO/RPO: Firewall Manager auto-remediates tampered web ACLs within minutes; new accounts/resources auto-enrolled.
- AWS Services: AWS Firewall Manager, AWS Organizations, AWS WAF, AWS Config (compliance monitoring), Amazon SNS (findings notifications).
- Cost Profile: Medium — Firewall Manager has per-policy per-account charges (see Firewall Manager pricing); WAF costs continue per web ACL.
- Automation: Firewall Manager WAF policy = fully automated; define managed rule groups and scope (account/OU/tag) centrally. Individual accounts can add their own rules on top of Firewall Manager-defined rules (in supported mode).
- Source: [Firewall Manager WAF policies](https://docs.aws.amazon.com/waf/latest/developerguide/waf-policies.html) + [Firewall Manager blog](https://aws.amazon.com/blogs/security/use-aws-firewall-manager-to-deploy-protection-at-scale-in-aws-organizations/), accessed 2026-08-26.

---

## Reference Architectures

**Standard internet-facing web application (browser clients)**
- Context: Production web application serving browser users, behind CloudFront + ALB, with login and registration flows.
- Services Composition:

  | Layer | Service | WAF Rules / Config |
  |-------|---------|-------------------|
  | Edge | Amazon CloudFront (CLOUDFRONT scope WAF, us-east-1) | CRS (700 WCU) + Known Bad Inputs (200) + Amazon IP Reputation (25) + Anonymous IP (50) + Bot Control Common (50) + Anti-DDoS AMR (50) = 1,075 WCU |
  | Regional | Application Load Balancer (REGIONAL scope WAF) | CRS (700) + SQLi (200) + Known Bad Inputs (200) + Rate-based IP (base 2) + ATP scoped to /login (50) + ACFP scoped to /register (50) = 1,204 WCU |
  | Governance | AWS Firewall Manager WAF policy | Enforces CRS + IP Rep across all accounts/regions |
  | Monitoring | Amazon CloudWatch + S3 + Athena | Metrics, alarms, long-term log analysis |
  | AI bots (optional) | Bot Control Targeted + WBA | Allowlist verified AI agents; optionally Monetize via CloudFront |

- Key Decisions: Count mode before Block for all managed rules; CAPTCHA immunity time (default 300 s); ATP response inspection on CloudFront only; rate-based rule threshold tuned to p99 traffic.
- Scaling Path: Add Global Accelerator for multi-region; add ACFP for sign-up fraud; extend Firewall Manager policy to new OUs; adopt Bot Control Targeted for login/API paths.
- Cost Baseline: Medium — 2 web ACLs ($10/mo) + rules ($2–5/mo) + requests ($0.60/million); Bot Control + ATP/ACFP add $20–30/month subscription plus per-request overages.
- Source: Synthesized from [AWS WAF Developer Guide](https://docs.aws.amazon.com/waf/latest/developerguide/) sections, accessed 2026-08-26.

**Agentic AI workload protection (Bedrock AgentCore Gateway)**
- Context: AWS Bedrock AgentCore Gateway fronting agentic AI workflows; needs IP-based access control, rate limiting, and bot management.
- Services Composition:

  | Layer | Service | WAF Rules / Config |
  |-------|---------|-------------------|
  | AI gateway | Amazon Bedrock AgentCore Gateway (REGIONAL scope WAF) | CRS (700) + Known Bad Inputs (200) + Amazon IP Reputation (25) + Bot Control Targeted with WBA (50) + Rate-based IP (2) |
  | Monitoring | Amazon CloudWatch | Bot category metrics; AI Traffic Analysis dashboard |

- Key Decisions: WBA to allow legitimate Bedrock AgentCore agents while blocking scrapers; rate-based rules with ASN aggregation for volumetric protection; body inspection limit up to 16 KB for AgentCore Gateway.
- Source: [AWS WAF for Bedrock AgentCore Gateway (What's New 2026-06-29)](https://aws.amazon.com/about-aws/whats-new/2026/06/aws-waf-amazon-bedrock-agentcore/) + [Bedrock AgentCore Gateway WAF docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-waf.html), accessed 2026-08-26.

---

## Service Equivalence Map

Included as a cross-provider aid for architects evaluating WAF solutions (feature parity is NOT implied).

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|--------------|-------|--------------------|
| **Web Application Firewall** | AWS WAF (WAFv2) | Cloud Armor security policies | Azure WAF (on Front Door / App Gateway) | OCI WAF |
| **Managed rule sets** | AWS Managed Rules (CRS, SQLi, Bot Control, Anti-DDoS AMR) | Cloud Armor preconfigured WAF rules (ModSecurity CRS) | Azure-managed WAF rule sets (OWASP CRS) | OCI protection rules |
| **Bot management** | Bot Control (Common + Targeted + WBA) | Cloud Armor Adaptive Protection (rate-based) | Azure WAF Bot Manager rule set | OCI WAF bot management |
| **Fraud / ATO prevention** | ATP (account takeover) + ACFP (account creation fraud) | No native equivalent | No native equivalent | No native equivalent |
| **Rate limiting** | Rate-based rules (IP, ASN, custom keys, JA3/JA4, ML) | Cloud Armor rate-based ban rules | Azure WAF rate limiting (preview) | OCI WAF rate limiting |
| **L7 DDoS** | Anti-DDoS AMR (`AWSManagedRulesAntiDDoSRuleSet`) + Shield Advanced | Cloud Armor Adaptive Protection | Azure DDoS Protection (Standard) + WAF | OCI DDoS Protection + WAF |
| **AI traffic monetization** | Monetize action (x402, CloudFront-only, 2026) | No equivalent | No equivalent | No equivalent |
| **Org-wide WAF governance** | AWS Firewall Manager WAF policies | Cloud Armor organization policies | Azure Policy + Defender for Cloud | OCI Security Zones |

> **⚠️ Important**: Service equivalence does NOT mean feature parity. AWS WAF's Bot Control WBA, ATP/ACFP fraud control, dynamic label interpolation, and AI traffic monetization have no exact counterparts on other providers. Validate against `AWS WAF 2026` documentation before architectural decisions.
[Sources: AWS rows verified in this research; other-provider rows are directional mappings — verify against each provider's current docs before use.]

---

## Provider Differentiators

```
Differentiator: Bot Control with Web Bot Authentication (WBA) for AI agents
Category: Security
Unique Value: Cryptographic verification of legitimate AI agents/bots (v4.0 CloudFront Nov 2025; v6.0 regional May 2026). WBA-verified bots receive bot:web_bot_auth:verified label and are auto-allowlisted in CategoryAI — distinguishing legitimate AI crawlers from scrapers without blocking desired AI indexing.
Architecture Impact: Enables AI-safe deployments that selectively allow verified AI agents while blocking unverified scrapers — no other major WAF provider has an equivalent cryptographic verification mechanism for AI agents.
When to Leverage: Content publishers, API providers, or AI-accessed resources where differentiating legitimate AI agent traffic from scraper traffic is required.
Caveat: Requires Bot Control Targeted tier. WBA ecosystem (which AI agents support it) is growing but not yet universal.
Source: https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html (accessed 2026-08-26)
```
```
Differentiator: ATP + ACFP fraud control managed rule groups
Category: Security
Unique Value: AWS-managed, continuously updated detection of credential stuffing (ATP) and account creation fraud (ACFP) using AWS's stolen-credential database from dark-web feeds, plus response inspection on CloudFront to correlate request patterns with actual login/registration success/failure rates.
Architecture Impact: Reduces the engineering investment needed to build and maintain credential-stuffing and fraud detection — typically weeks of custom development replaced by managed rule group configuration.
When to Leverage: Any internet-facing login or registration endpoint where credential stuffing or synthetic account creation is a business risk.
Caveat: Both are paid ($10/mo subscription each); cannot be used with Cognito user pool associations; response inspection requires CloudFront.
Source: https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-atp.html (accessed 2026-08-26)
```
```
Differentiator: AI Traffic Monetization (Monetize action, 2026)
Category: Revenue / Security
Unique Value: CloudFront-only action that returns HTTP 402 Payment Required with x402 payment instructions to AI bots/agents, enabling publishers to price and meter AI traffic at the WAF layer without application changes. Configurable per-request price from $0.00001 to $100.
Architecture Impact: Shifts AI-traffic revenue from an application-layer problem to an infrastructure-layer concern; edge enforcement means no AI agent bypasses payment before reaching origin.
When to Leverage: Content publishers or API providers who want to charge AI crawlers/agents for access to proprietary content or APIs.
Caveat: CloudFront-only (not available in Regional web ACLs); cannot be used as a rate-based rule action; requires MonetizationConfig.
Source: https://docs.aws.amazon.com/waf/latest/developerguide/waf-ai-traffic-monetization.html (accessed 2026-08-26)
```
```
Differentiator: Dynamic label interpolation
Category: Flexibility / Operations
Unique Value: `${namespace:}` syntax (April 2026) resolves label values at evaluation time in custom request headers, response headers, and response bodies — one rule covers an entire label namespace rather than requiring one rule per label value.
Architecture Impact: Significantly reduces rule count for label-heavy designs (e.g., geo-routing, bot category–based routing); avoids WCU waste from redundant per-value rules.
When to Leverage: Architectures that use labels from multiple AWS Managed Rules groups to drive routing or custom response logic; any design where label values are dynamic.
Source: https://docs.aws.amazon.com/waf/latest/developerguide/waf-dynamic-label-interpolation.html (accessed 2026-08-26)
```
```
Differentiator: JA3 and JA4 TLS fingerprint matching and rate limiting
Category: Security
Unique Value: AWS WAF can match on TLS Client Hello fingerprints (JA3: 32-char hash; JA4: 36-char hash) as match criteria and as rate-based rule aggregation keys (JA4 added March 2025). Fingerprints identify specific TLS client implementations — a strong bot/scraper signal that survives IP rotation.
Architecture Impact: Adds a fingerprint-based layer that persists across IP rotation and proxy chains; correlates requests by TLS implementation rather than IP address.
When to Leverage: Advanced bot defense where attackers rotate IPs or use residential proxies; credential-stuffing defense where volumetric rules alone miss low-rate attacks.
Caveat: JA3/JA4 logged only when a match statement is used; logged only for CloudFront and ALB (not other resource types).
Source: https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based-aggregation-options.html (accessed 2026-08-26)
```

---

## Scenario Coverage

**Standard Case**: Internet-facing production web app with login flow.
- Approach: CloudFront (CLOUDFRONT WAF: CRS + Bot Control Common + IP Rep + Anti-DDoS AMR) → ALB (REGIONAL WAF: CRS + SQLi + ATP scoped to /login + rate-based on IP, 5 min window) → private app tier. Deploy all managed rules in Count mode; observe 48 hours; promote to Block. Enable logging to CloudWatch Logs. Firewall Manager enforces CRS across all accounts.
- Key Decisions: Bot Control Common vs Targeted (depends on observed bot sophistication); ATP cost justification (depends on login attack history); rate-based rule threshold (tune to observed p99).

**Edge Case**: API-only endpoint under credential-stuffing attack from residential proxies.
- Approach: Rate-based rules with IP aggregation alone are insufficient (residential proxies distribute across many IPs). Add Bot Control Targeted to enable fingerprinting and ML-based coordinated-activity detection (`TGT_ML_CoordinatedActivityMedium`). Add ATP with scope-down to the `/api/auth` path. Use JA4 fingerprint as an additional rate-based aggregation key. Allow 24 hours for ML baseline establishment.
- Key Decisions: JA4 rate key (requires at least one JA4 match statement to enable logging); ML rule baseline delay means initial 24 hours are partially blind.

**Edge Case**: Multi-tenant SaaS needing per-tenant WAF rules.
- Approach: Use rate-based rules with custom aggregation keys (e.g., a tenant-ID HTTP header or cookie) to enforce per-tenant rate limits without separate web ACLs per tenant. Use label match rules to route per-tenant traffic to different custom response paths.
- Key Decisions: Custom aggregation key adds 30 WCU per key; header/cookie values are limited to first 32 chars in rate-based rule customValues log field.

**Anti-Pattern Case**: Team has existing AWS WAF Classic (WAF v1) and wants to extend it.
- Clarification: AWS WAF Classic is in a planned end-of-life process with per-Region sunset milestones visible in the AWS Health dashboard. All new development must use AWS WAFv2. Migrate using the official migration guide (waf-migrating-from-classic.html). WAFv1 and WAFv2 coexist during migration; WAFv2 provides significantly more capability (managed rules, labels, rate-based custom keys, Bot Control, CAPTCHA/Challenge).

**Anti-Pattern Case**: Team wants to use ATP and ACFP on a Cognito user pool.
- Clarification: Both ATP and ACFP are explicitly prohibited from web ACLs associated with Cognito user pools. Protect the Cognito user pool with a separate web ACL using only CRS, Known Bad Inputs, IP reputation, and rate-based rules. Move ATP/ACFP protection to the ALB or API Gateway layer in front of Cognito.

---

## Quotas & Pricing Reference

### Key Fixed Quotas (cannot be changed)
| Item | Limit |
|------|-------|
| Max WCUs per web ACL | **5,000** |
| Max WCUs per rule group | **5,000** |
| Rate-based rules per web ACL | 10 |
| Rate-based rules per rule group | 4 |
| Minimum rate-based threshold | 10 requests |
| Max unique IPs rate-limited per rate-based rule | 10,000 |
| Geo match country codes per rule | 50 |
| Text transformations per rule statement | 10 |
| String match / each regex pattern | 200 characters |
| Unique regex patterns per regex set | 10 |
| IP addresses (CIDR) per IP set | 10,000 |
| Token domains per web ACL list | 10 |
| Resource associations per web ACL (each Regional type) | 100 |

### Key Adjustable Defaults (per account per Region)
| Resource | Default |
|----------|---------|
| Web ACLs | 100 |
| Rule groups | 100 |
| IP sets | 100 |
| Regex pattern sets | 10 |
| Requests per second per web ACL | 100,000 |

### Pricing Summary (USD; verify on live pricing page)
| Item | Price |
|------|-------|
| Web ACL | $5.00/month |
| Rule | $1.00/month each |
| Requests | $0.60/million |
| WCU overage (above 1,500) | $0.20/million requests per additional 500 WCUs |
| Body inspection overage | $0.30/million requests per additional 16 KB |
| Managed rule group | $1.00/month each |
| Bot Control subscription | $10.00/month per web ACL |
| ATP or ACFP subscription | $10.00/month per web ACL per component |
| CAPTCHA | $0.40/thousand CAPTCHA attempts |

Source: https://aws.amazon.com/waf/pricing/ (accessed 2026-08-26)

---

## 2025–2026 Changelog (Critical Changes)

| Date | Change |
|------|--------|
| Aug 12, 2026 | SQL database rule group **v2.4** — improved SQLi detection |
| Jul 29, 2026 | Pre-parse text transformations + 10 new transformations (Uppercase, Trim, Remove Whitespace, SHA256, etc.) |
| Jul 24, 2026 | Bot Control **v6.1** — new signatures across Advertising, AI, Content Fetcher, SEO, Webhooks categories |
| Jun 29, 2026 | Amazon Bedrock AgentCore Gateway WAF protection GA |
| Jun 15, 2026 | AI Traffic Monetization GA (Monetize action, CloudFront-only) |
| May 22, 2026 | Bot Control **v6.0** — WBA expanded to all regional AWS WAF (was CloudFront-only) |
| Apr 1, 2026 | Dynamic label interpolation (`${namespace:}`) |
| Feb 25, 2026 | Bot Control **v5.0** — 400+ new bots; Page Preview + Webhooks categories |
| Nov 17, 2025 | Web Bot Authentication (WBA) GA — Bot Control v4.0 for CloudFront |
| Jun 17, 2025 | Simplified console / "protection packs" (~80% fewer config steps); Shield network security director (preview) |
| Jun 11, 2025 | Anti-DDoS managed rule group (`AWSManagedRulesAntiDDoSRuleSet`) GA; resource-level DDoS protection for ALB |
| Jun 5, 2025 | ASN match statements + ASN aggregation for rate-based rules |
| Mar 4, 2025 | JA4 fingerprint matching |
| Jan 2025 | Top Insights visualizations in console |

**AWS WAF Classic end-of-life:** planned per-Region milestones in AWS Health dashboard (global date unconfirmed — see §21).  
**Security Automations for AWS WAF solution:** retiring December 2026.

---

## 21. Unverified Items

The following items could not be confirmed from official primary source pages accessed on 2026-08-26. Do not use as authoritative until re-verified:

1. **Targeted Bot Control per-million tier rate beyond the free allotment** — base $10/month subscription and first 1M/month free are confirmed; the specific per-million rate in upper tiers requires re-verification on the live pricing page (https://aws.amazon.com/waf/pricing/).
2. **Challenge per-response price** — the specific per-Challenge-response pricing figure was not clearly stated on the pages fetched; CAPTCHA ($0.40/thousand) is confirmed.
3. **AWS WAF Classic global end-of-life date** — AWS directs customers to per-Region milestones in their AWS Health dashboard; no single calendar date was documented.
4. **Managed rule group staging workflow specifics** beyond version pinning and Count-mode testing — see https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-testing.html.
5. **CloudWatch metric retention period** — "two weeks" appeared in a search snippet but was not confirmed on the official metrics page; governed by standard CloudWatch retention (15 months for 1-minute metrics by default in CloudWatch).
6. **Exact `x-amzn-waf-` prefix** for custom request headers inserted by AWS WAF — consistent with AWS naming conventions but reconfirm on customizing-the-incoming-request.html if load-bearing.
7. **Firewall Manager "first rule groups / last rule groups" ordering terminology** — exact wording not captured verbatim; review https://docs.aws.amazon.com/waf/latest/developerguide/create-policy.html for precise terms.

---

## Source Bibliography

| # | Source | Type | Date accessed | Currency |
|---|--------|------|---------------|----------|
| 1 | [AWS WAF Developer Guide — How AWS WAF works](https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-resources.html) | Official docs | 2026-08-26 | Current |
| 2 | [Web ACL overview](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl.html) | Official docs | 2026-08-26 | Current |
| 3 | [Rule actions](https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-action.html) | Official docs | 2026-08-26 | Current |
| 4 | [Rule groups](https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-groups.html) | Official docs | 2026-08-26 | Current |
| 5 | [AWS WAF capacity units](https://docs.aws.amazon.com/waf/latest/developerguide/aws-waf-capacity-units.html) | Official docs | 2026-08-26 | Current |
| 6 | [Rate-based rules](https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based.html) | Official docs | 2026-08-26 | Current |
| 7 | [AWS WAF labels](https://docs.aws.amazon.com/waf/latest/developerguide/waf-labels.html) | Official docs | 2026-08-26 | Current |
| 8 | [Dynamic label interpolation](https://docs.aws.amazon.com/waf/latest/developerguide/waf-dynamic-label-interpolation.html) | Official docs | 2026-08-26 | Current |
| 9 | [AWS Managed Rules list](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-list.html) | Official docs | 2026-08-26 | Current |
| 10 | [Baseline rule groups](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-baseline.html) | Official docs | 2026-08-26 | Current |
| 11 | [IP reputation rule groups](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-ip-rep.html) | Official docs | 2026-08-26 | Current |
| 12 | [Bot Control managed rule group](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html) | Official docs | 2026-08-26 | Current |
| 13 | [AWS Managed Rules changelog](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-changelog.html) | Official docs | 2026-08-26 | Current |
| 14 | [ATP managed rule group](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-atp.html) | Official docs | 2026-08-26 | Current |
| 15 | [ACFP managed rule group](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-acfp.html) | Official docs | 2026-08-26 | Current |
| 16 | [CAPTCHA and Challenge](https://docs.aws.amazon.com/waf/latest/developerguide/waf-captcha-and-challenge.html) | Official docs | 2026-08-26 | Current |
| 17 | [Associating with AWS resources](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-associating-aws-resource.html) | Official docs | 2026-08-26 | Current |
| 18 | [Shield Advanced capabilities](https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html) | Official docs | 2026-08-26 | Current |
| 19 | [Firewall Manager WAF policies](https://docs.aws.amazon.com/waf/latest/developerguide/waf-policies.html) | Official docs | 2026-08-26 | Current |
| 20 | [Logging destinations](https://docs.aws.amazon.com/waf/latest/developerguide/logging-destinations.html) | Official docs | 2026-08-26 | Current |
| 21 | [Logging fields](https://docs.aws.amazon.com/waf/latest/developerguide/logging-fields.html) | Official docs | 2026-08-26 | Current |
| 22 | [CloudWatch metrics](https://docs.aws.amazon.com/waf/latest/developerguide/waf-metrics.html) | Official docs | 2026-08-26 | Current |
| 23 | [WAF quotas](https://docs.aws.amazon.com/waf/latest/developerguide/limits.html) | Official docs | 2026-08-26 | Current |
| 24 | [AWS WAF best practices](https://docs.aws.amazon.com/waf/latest/developerguide/best-practices.html) | Official docs | 2026-08-26 | Current |
| 25 | [AWS WAF doc history](https://docs.aws.amazon.com/waf/latest/developerguide/doc-history.html) | Official docs | 2026-08-26 | Current |
| 26 | [AWS WAF pricing](https://aws.amazon.com/waf/pricing/) | Official pricing | 2026-08-26 | Current |
| 27 | [AI traffic monetization](https://docs.aws.amazon.com/waf/latest/developerguide/waf-ai-traffic-monetization.html) | Official docs | 2026-08-26 | Current |
| 28 | [Bedrock AgentCore Gateway WAF (What's New 2026-06-29)](https://aws.amazon.com/about-aws/whats-new/2026/06/aws-waf-amazon-bedrock-agentcore/) | Official What's New | 2026-08-26 | Current (2026) |
| 29 | [Anti-DDoS AMR migration blog](https://aws.amazon.com/blogs/security/aws-shield-advanced-is-embracing-the-aws-waf-anti-ddos-managed-rule-group-what-changes-and-how-to-prepare/) | Official security blog | 2026-08-26 | Current (2025-2026) |
| 30 | [Security Automations for AWS WAF](https://docs.aws.amazon.com/solutions/latest/security-automations-for-aws-waf/solution-overview.html) | Official solution docs | 2026-08-26 | Current |
| 31 | [Amazon Security Lake — AWS WAF source](https://docs.aws.amazon.com/security-lake/latest/userguide/aws-waf.html) | Official docs | 2026-08-26 | Current |
| 32 | [Amazon Athena — WAF logs](https://docs.aws.amazon.com/athena/latest/ug/waf-logs.html) | Official docs | 2026-08-26 | Current |

---

*Generated by agents-factory framework-researcher pipeline. All source URLs link to official AWS documentation or AWS official sources accessed 2026-08-26. Items marked [unverified] in §21 require re-verification before use.*

---

## §7 — Research Iteration Changelog

| Iteration | Item | Action | Resolution | Source added |
|-----------|------|--------|------------|--------------|
| 1 | WCU limit "1,500 max" misconception appearing in community sources | Targeted verification against limits.html and capacity-units.html | Resolved: 1,500 WCU is the pricing boundary (included in base price); hard maximum per web ACL is 5,000 WCU. Misconception flagged in Glossary and Anti-Patterns. | Source #5 + #23 |
| 2 | AWS Amplify scope exception (listed as Regional resource but requires CLOUDFRONT scope) | Verified against how-aws-waf-works-resources.html | Resolved: Amplify is a documented exception — must use CLOUDFRONT-scope web ACL in us-east-1 despite being a regional service. Flagged in Scope section and Anti-Patterns. | Source #1 |
| 3 | Targeted Bot Control per-million tier rate | WebSearch + pricing page review | Unresolved: base $10/month subscription and first 1M/month free confirmed; upper-tier per-million rate not confirmed from a single authoritative page. Marked unverified in §21. | Source #26 (partial) |
| 4 | AWS WAF Classic global end-of-life date | Targeted search of doc-history and health dashboard guidance | Unresolved: AWS provides per-Region milestones in the AWS Health dashboard only; no global date published. Marked unverified in §21. | Source #25 |
| 5 | WBA scope (CloudFront-only vs regional) across Bot Control versions | Verified v4.0 vs v6.0 changelog entries | Resolved: WBA was CloudFront-only in v4.0 (Nov 2025); expanded to all regional WAF in v6.0 (May 2026). Documented in Bot Control version table and Glossary. | Source #13 |

**Unverified / irresolvable items:** Targeted Bot Control per-million tier rate (§21 item 1); Challenge per-response price (§21 item 2); WAF Classic global EOL date (§21 item 3); managed rule group staging workflow specifics (§21 item 4); CloudWatch metric retention period (§21 item 5).

> ⚠️ **Migration Note (applies throughout):** AWS WAF Classic (WAFv1) is in a planned end-of-life process with per-Region sunset milestones in the AWS Health dashboard. All new designs must use AWS WAFv2. The Security Automations for AWS WAF CloudFormation solution retires December 2026.
