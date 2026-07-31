# Evaluation Scenarios — architecting-aws-ddos-protection

> 6 test cases covering canonical use, edge cases, and misuse/anti-pattern traps.
> Use with `/evaluating-skill-scenarios architecting-aws-ddos-protection`.

---

## Scenario 1 — Canonical: Multi-account production estate Shield Advanced design

```json
{
  "skills": ["architecting-aws-ddos-protection"],
  "query": "We have a multi-account AWS Organizations estate with 8 production accounts running revenue-bearing e-commerce workloads behind CloudFront and ALBs. Design our DDoS protection architecture.",
  "expected_behavior": [
    "Recommends Shield Advanced (not Standard) — business-critical justification",
    "Prescribes Firewall Manager Shield Advanced policy from the org security account for org-wide auto-protection",
    "Specifies WAF web ACL on both CloudFront (CLOUDFRONT scope, us-east-1) and regional ALBs",
    "Includes health-based detection via Route 53 health checks as a prerequisite for proactive engagement",
    "Prescribes SRT IAM role with AWSShieldDRTAccessPolicy trusting drt.shield.amazonaws.com",
    "Mentions Business or Enterprise Support plan requirement for SRT",
    "References $3,000/month subscription cost covering the entire consolidated-billing family",
    "States that Firewall Manager Shield policies are included at no extra charge"
  ]
}
```

---

## Scenario 2 — Canonical: Shield Advanced onboarding checklist for a single account

```json
{
  "skills": ["architecting-aws-ddos-protection"],
  "query": "We just subscribed to Shield Advanced for a single AWS account running a payments API behind an ALB. Walk me through the onboarding steps we must complete before go-live.",
  "expected_behavior": [
    "Identifies all internet-facing resources that need explicit protection (ALB ARN, Route 53 zone, any EIPs)",
    "Prescribes attaching AWS WAF web ACL with managed rules + rate-based rules to the ALB",
    "Prescribes creating Route 53 health check and associating it with the Shield Advanced protection",
    "Prescribes creating the SRT IAM role (AWSShieldDRTAccessPolicy, drt.shield.amazonaws.com trust)",
    "Prescribes enabling proactive engagement with 24x7 contacts",
    "Provides AWS CLI verification commands (describe-subscription, list-protections, describe-drt-access)",
    "Flags support plan requirement: Business or Enterprise Support for SRT"
  ]
}
```

---

## Scenario 3 — Edge case: Non-HTTP workload (gaming / real-time TCP)

```json
{
  "skills": ["architecting-aws-ddos-protection"],
  "query": "We run a real-time multiplayer gaming backend using UDP over port 7000. It sits behind a Network Load Balancer with an Elastic IP. Can we use Shield Advanced? How does WAF apply?",
  "expected_behavior": [
    "Confirms Shield Advanced CAN protect EC2 Elastic IPs and NLBs (listed as protectable resource types)",
    "Clarifies AWS WAF does NOT apply to UDP/non-HTTP(S) traffic — WAF is HTTP(S)-only",
    "Recommends AWS Global Accelerator standard accelerator as an edge front for the NLB (also protectable with Shield Advanced)",
    "Notes DTO rate is $0.050/GB (not CloudFront's $0.025/GB) for this topology",
    "Still prescribes health-based detection via Route 53 health checks and SRT pre-configuration",
    "Recommends app-level rate limiting as substitute for WAF L7 rules on non-HTTP protocols"
  ]
}
```

---

## Scenario 4 — Edge case: Automatic L7 mitigation enabled but not blocking attacks

```json
{
  "skills": ["architecting-aws-ddos-protection"],
  "query": "We enabled automatic application layer DDoS mitigation on our Shield Advanced protected CloudFront distribution, but during a test flood it didn't seem to block anything. What should we check?",
  "expected_behavior": [
    "Identifies that automatic L7 mitigation defaults to 'count' mode — must be set to 'block' to actively drop traffic",
    "Notes that the automatic mitigation adds a 150-WCU rule group to the WAF web ACL",
    "Checks that a WAF web ACL is actually attached to the CloudFront distribution",
    "Verifies the WAF web ACL has sufficient WCU budget (at least 150 WCUs available for the mitigation rule group)",
    "Provides verification steps: Shield console Protection -> Layer 7 DDoS mitigation; wafv2 get-web-acl to inspect rules",
    "Does NOT suggest disabling Shield or removing WAF as a fix"
  ]
}
```

---

## Scenario 5 — Misuse trap: Team requests launching with Shield Standard to save costs

```json
{
  "skills": ["architecting-aws-ddos-protection"],
  "query": "Our finance team says Shield Advanced is $3,000/month and we should just use Shield Standard for our new checkout service to save costs. Is that acceptable?",
  "expected_behavior": [
    "Explicitly states Shield Standard has NO layer-7 protection — HTTP/HTTPS floods pass through",
    "States Shield Standard has no SRT, no proactive engagement, no DDoS cost protection, no health-based detection",
    "Identifies checkout/payments as business-critical, revenue-bearing — recommends Shield Advanced",
    "Notes that Shield Advanced subscription covers the entire consolidated-billing family, amortizing the $3,000/month cost across accounts",
    "Notes WAF standard fees are covered (up to 1,500 WCUs), partially offsetting the subscription cost",
    "Mentions DDoS cost protection as a financial risk mitigation that Standard lacks",
    "Does NOT recommend Standard for this workload"
  ]
}
```

---

## Scenario 6 — Anti-pattern trap: EC2 with public IP for a quick launch

```json
{
  "skills": ["architecting-aws-ddos-protection"],
  "query": "A developer wants to expose an EC2 instance with a public IP temporarily for a product launch next week. They say they'll add CloudFront later. Is this okay with Shield Advanced protecting the EIP?",
  "expected_behavior": [
    "Refuses direct EC2 public IP exposure even with Shield Advanced on the EIP — no L7 protection, no WAF at the edge",
    "Flags 'temporarily' as a CRITICAL risk pattern: temporary becomes permanent",
    "Prescribes adding CloudFront + WAF BEFORE launch, not after",
    "States origin must be private (no public IP on the EC2 instance) — restrict security group to ALB/CloudFront path only",
    "Does NOT accept the 'protect EIP with Shield Advanced' as sufficient for a web application",
    "Provides the correct architecture: CloudFront + WAF -> ALB + WAF -> EC2 in private subnet",
    "References SEC05-BP01 (Create network layers) as the violated best practice"
  ]
}
```
