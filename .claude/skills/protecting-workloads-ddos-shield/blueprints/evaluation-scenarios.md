# Evaluation Scenarios — protecting-workloads-ddos-shield

Skill under test: `protecting-workloads-ddos-shield`
Research date: 2026-08-26
Currency threshold: 2027-08-26

---

## Scenario 1 — Canonical: Design DDoS protection for a new internet-facing web app

```json
{
  "skills": ["protecting-workloads-ddos-shield"],
  "query": "We are launching a business-critical e-commerce platform on AWS. It needs DDoS protection. What is the recommended architecture?",
  "expected_behavior": [
    "Recommends edge-terminated architecture: Route 53 → CloudFront (Shield Advanced) → WAF web ACL with AWSManagedRulesAntiDDoSRuleSet → ALB (Shield Advanced) → private origins",
    "Specifies attaching a WAF web ACL with the Anti-DDoS AMR (Challenge action for browser clients) to the CloudFront distribution",
    "Recommends enabling Route 53 health-based detection and SRT proactive engagement",
    "Recommends enforcing enrollment via Firewall Manager Shield Advanced policy scoped to the OU",
    "States Shield Advanced cost ($3,000/month per payer account, 1-year commitment) and requirement for Business/Enterprise Support for SRT",
    "Does NOT reference legacy L7AM as a go-forward option"
  ]
}
```

---

## Scenario 2 — Canonical: Validate Anti-DDoS AMR WAF action for an API endpoint

```json
{
  "skills": ["protecting-workloads-ddos-shield"],
  "query": "Our CloudFront distribution serves a REST API (programmatic clients only, no browsers). We are configuring the Anti-DDoS AMR. Which action should we use — Challenge, Block, or Count?",
  "expected_behavior": [
    "Identifies that Challenge is designed for browser clients using silent JS verification; programmatic/API clients cannot complete it and will be rejected",
    "Recommends Block action for API endpoints where Challenge is infeasible",
    "Recommends validating in Count mode during the evaluation window (through 2026-09-30) before enforcing Block",
    "Mentions tuning sensitivity (Low/Medium/High) to minimize false positives for the specific traffic profile",
    "Does NOT recommend Challenge as the default for API-only workloads"
  ]
}
```

---

## Scenario 3 — Migration: Existing Shield Advanced subscriber using legacy L7AM

```json
{
  "skills": ["protecting-workloads-ddos-shield"],
  "query": "We have Shield Advanced with L7 Automatic Mitigation enabled on our ALBs. It works fine. Do we need to do anything?",
  "expected_behavior": [
    "States clearly that legacy L7AM retires 2027-01-01 — migration is mandatory, not optional",
    "Explains the auto-upgrade timeline: eligible web ACLs auto-upgraded 2026-10-01; free evaluation period through 2026-09-30",
    "Recommends proactive migration for tier-1 workloads: add AWSManagedRulesAntiDDoSRuleSet in Count mode now, validate, then switch to Challenge/Block before October",
    "Explains the benefits of migrating early: seconds-scale mitigation vs minutes, Challenge action, 50 WCUs vs 150 WCUs",
    "Provides the verification step: confirm IaC no longer references ddos-automatic-app-layer-response",
    "Does NOT suggest staying on L7AM or that migration is optional"
  ]
}
```

---

## Scenario 4 — Anti-Pattern Trap: Shield Advanced subscribed but resources not enrolled

```json
{
  "skills": ["protecting-workloads-ddos-shield"],
  "query": "We subscribed to Shield Advanced. Are our resources automatically protected?",
  "expected_behavior": [
    "Corrects the assumption: Shield Advanced does NOT auto-protect any resources — enrollment is opt-in per resource",
    "Identifies the risk: paying $3,000/month with gaps in coverage; unprotected resources get no L7 mitigation and no cost protection",
    "Recommends using Firewall Manager Shield Advanced policy scoped to the OU to auto-enroll new and existing resources",
    "Provides detection command: aws shield list-protections to compare enrolled count against actual internet-facing resource count",
    "Does NOT confirm that subscription alone equals protection"
  ]
}
```

---

## Scenario 5 — Edge Case: Proactive engagement not triggering as expected

```json
{
  "skills": ["protecting-workloads-ddos-shield"],
  "query": "We enabled proactive engagement on Shield Advanced but the SRT never contacted us during a recent attack. What went wrong?",
  "expected_behavior": [
    "Identifies the most likely cause: no Route 53 health check associated with the protected resource — health-based detection is a hard prerequisite for proactive engagement",
    "Explains that proactive engagement triggers when a Route 53 health check associated with a protected resource becomes unhealthy during a Shield-detected event",
    "Provides verification steps: Shield console → protected resource → Health check associated = yes; aws shield describe-emergency-contact-settings",
    "Notes that SRT also requires Business or Enterprise Support plan — confirms this was in place",
    "Does NOT suggest that proactive engagement works without health-based detection"
  ]
}
```

---

## Scenario 6 — Misuse: Conflating Shield Advanced with AWS WAF

```json
{
  "skills": ["protecting-workloads-ddos-shield"],
  "query": "We use AWS WAF with custom rules. Do we still need Shield Advanced for DDoS protection?",
  "expected_behavior": [
    "Explains the distinction: AWS WAF is the delivery mechanism for L7 rules including DDoS; Shield Advanced orchestrates, funds, and enhances L7 mitigation but is not a substitute for WAF",
    "States that the Anti-DDoS AMR (AWSManagedRulesAntiDDoSRuleSet) is a WAF managed rule group — you need Shield Advanced to access it",
    "Notes that without Shield Advanced, WAF request costs are unprotected from DDoS-driven bill spikes (no cost protection credits)",
    "Frames the decision: WAF alone provides L7 rule enforcement; Shield Advanced adds L7 automatic DDoS mitigation via AMR, SRT, cost protection, visibility, and Firewall Manager",
    "Does NOT conflate WAF and Shield Advanced as alternatives"
  ]
}
```
