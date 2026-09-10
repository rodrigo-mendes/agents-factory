# Evaluation Scenarios — securing-aws-waf-web-acls

Skill under test: `securing-aws-waf-web-acls`
Research date: 2026-08-26
Currency threshold: 2027-08-26

---

## Scenario 1 — Canonical: Standard internet-facing web application

```json
{
  "skills": ["securing-aws-waf-web-acls"],
  "query": "Design an AWS WAF configuration for a production web app with a login page and public marketing pages, served through CloudFront and ALB. Include bot control and fraud prevention.",
  "expected_behavior": [
    "Creates two web ACLs: CLOUDFRONT-scope (us-east-1) for CloudFront and REGIONAL-scope for ALB",
    "Baseline rule groups: CRS (700 WCU) + Known Bad Inputs (200) + IP Reputation (25) on both",
    "Bot Control Common on CloudFront tier; Bot Control Targeted + ATP (scope-down to /login) on ALB tier",
    "All managed rule groups deployed in Count mode first with 24-72h observation window",
    "WCU budget calculated and confirmed below 5,000 hard cap",
    "Logging configured to aws-waf-logs-* destination on both web ACLs",
    "CloudWatch alarms on BlockedRequests spikes"
  ]
}
```

---

## Scenario 2 — Edge: API under credential stuffing from residential proxies

```json
{
  "skills": ["securing-aws-waf-web-acls"],
  "query": "Our /api/auth endpoint is being attacked by credential stuffing using residential proxies that rotate IPs every few requests. Standard IP-based rate limiting is not catching it. What AWS WAF configuration is needed?",
  "expected_behavior": [
    "Recommends Bot Control Targeted (not Common) for ML-based coordinated-activity detection",
    "Adds ATP managed rule group scoped to /api/auth URI path",
    "Adds JA4 fingerprint as a rate-based rule aggregation key (survives IP rotation)",
    "Notes that ML rules require 24-hour baseline establishment period before firing",
    "Notes JA4 fingerprints are logged only when a JA4 match statement is used",
    "Notes JA4/JA3 logging is only available for CloudFront and ALB resource types",
    "Calculates WCU impact: Bot Control (50) + ATP (50) + rate-based key (+30) = additional 130 WCU"
  ]
}
```

---

## Scenario 3 — Edge: AWS Amplify app protection

```json
{
  "skills": ["securing-aws-waf-web-acls"],
  "query": "I need to add WAF protection to our AWS Amplify app. I created a REGIONAL web ACL in ap-southeast-1 but the association is failing. What is wrong?",
  "expected_behavior": [
    "Identifies the error: Amplify requires a CLOUDFRONT-scope web ACL, not REGIONAL",
    "States Amplify is documented as a Regional resource but is an exception requiring CLOUDFRONT scope",
    "Instructs to create a new CLOUDFRONT-scope web ACL in us-east-1",
    "Does NOT suggest using the existing REGIONAL web ACL for Amplify",
    "Provides AWS CLI or IaC correction using us-east-1 region and CLOUDFRONT scope"
  ]
}
```

---

## Scenario 4 — Edge: AI bot management for content publisher

```json
{
  "skills": ["securing-aws-waf-web-acls"],
  "query": "We are a content publisher. We want to allow verified AI agents like ClaudeBot to crawl our site, block unverified AI scrapers, and optionally charge AI agents for API access. What AWS WAF features cover this in 2026?",
  "expected_behavior": [
    "Recommends Bot Control Targeted v6.0+ with Web Bot Authentication (WBA) enabled",
    "Explains WBA cryptographically verifies AI agent identity; verified bots get bot:web_bot_auth:verified label",
    "Explains WBA-verified bots are auto-allowlisted in CategoryAI and not matched by TGT_TokenAbsent",
    "For charging AI agents: recommends Monetize action (CloudFront-only) on rules matching bot:category:ai",
    "Clarifies Monetize is CloudFront-only and cannot be used in REGIONAL web ACLs",
    "Clarifies Monetize is NOT the same as WBA: WBA verifies identity; Monetize charges for access",
    "Distinguishes Bot Control v6.0 (May 2026, all regional) from v4.0 (Nov 2025, CloudFront-only for WBA)"
  ]
}
```

---

## Scenario 5 — Misuse trap: Deploying directly to Block

```json
{
  "skills": ["securing-aws-waf-web-acls"],
  "query": "We want to add AWSManagedRulesCommonRuleSet to our production web ACL with action BLOCK immediately. Our security team says Count mode is not needed because it is an AWS managed rule.",
  "expected_behavior": [
    "Rejects the approach and explains the risk explicitly",
    "States AWS WAF applies rules to ALL matching production traffic immediately upon deployment",
    "Explains that even AWS Managed Rules can generate false positives for specific application patterns",
    "Mandates Count mode with 24-72h observation window and sampled request review before Block",
    "References the AWS WAF best practices doc requirement for Count-mode validation",
    "Does NOT accommodate the request to skip Count mode as a shortcut"
  ]
}
```

---

## Scenario 6 — Misuse trap: ATP and ACFP on Cognito user pool

```json
{
  "skills": ["securing-aws-waf-web-acls"],
  "query": "I want to protect our Amazon Cognito user pool from credential stuffing. Can I add the AWSManagedRulesATPRuleSet to the web ACL that is associated with our Cognito user pool?",
  "expected_behavior": [
    "States clearly that ATP (AWSManagedRulesATPRuleSet) and ACFP cannot be used with Cognito user pool web ACL associations",
    "States the AssociateWebACL call will fail if the web ACL contains ATP or ACFP",
    "Provides the correct architecture: separate web ACL without ATP/ACFP for the Cognito user pool",
    "Recommends protecting the login/registration endpoint at ALB or API Gateway layer where ATP/ACFP is permitted",
    "Provides permissible rules for the Cognito web ACL: CRS + Known Bad Inputs + IP reputation + rate-based",
    "Does NOT suggest workarounds that involve using ATP on the Cognito web ACL"
  ]
}
```
