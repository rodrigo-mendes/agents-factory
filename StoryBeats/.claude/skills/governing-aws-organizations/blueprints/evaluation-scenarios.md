# Evaluation Scenarios — governing-aws-organizations

Skill: `governing-aws-organizations`
Version tested against: AWS Organizations 2024-2025 (all-features mode)
Created: 2026-07-31

---

## Scenario 1 — Canonical: Standard enterprise landing zone design

```json
{
  "skills": ["governing-aws-organizations"],
  "query": "Design a multi-account landing zone for a 200-person company moving to AWS. They need strong security controls, centralized logging, and the ability to onboard new application teams quickly.",
  "expected_behavior": [
    "Recommends AWS Control Tower as the managed landing zone (AF-2), not a DIY approach",
    "Specifies the core OU structure: Security (Log Archive + Audit), Infrastructure, Workloads (Prod/NonProd nested), Sandbox",
    "Calls out that the management account must remain empty of workloads (AD-2, NP-1)",
    "Requires all-features mode enabled (AD-1)",
    "Specifies an organization CloudTrail trail to the Log Archive account (AD-5)",
    "Delegates GuardDuty, Security Hub, and Config to the Audit account — not the management account (AD-6, NP-7)",
    "Recommends IAM Identity Center organization instance for workforce access (AD-8)",
    "Recommends Account Factory for account vending (AF-5)",
    "Recommends the deny-list SCP strategy as the starting point (AF-1)",
    "Includes root-level SCP blocking LeaveOrganization/CloseAccount (AD-4, NP-4)"
  ]
}
```

---

## Scenario 2 — Edge: Regulated org needing explicit service whitelist

```json
{
  "skills": ["governing-aws-organizations"],
  "query": "A financial services firm needs to ensure that only a specific set of AWS services are usable by any member account — no service should be reachable unless explicitly permitted. How do we implement this?",
  "expected_behavior": [
    "Identifies this as the allow-list SCP strategy (AF-1) — not the default deny-list",
    "Warns that removing FullAWSAccess at root without replacements causes org-wide lockout (NP-2)",
    "Explains that Allow statements must exist at EVERY hierarchy level: root → OU → account",
    "Recommends creating a Policy Staging OU to validate allow-list SCPs before broad rollout (NP-3, AD-9)",
    "Recommends combining SCP (principal guardrail) + RCP (resource perimeter) + declarative policies for defense-in-depth (AF-6)",
    "Notes the 10-SCP-per-entity hard limit and the need to design policy documents within the 10,240 character size limit",
    "Does NOT suggest using RCPFullAWSAccess removal — explains it cannot be detached"
  ]
}
```

---

## Scenario 3 — Misuse / anti-pattern trap: "Just run it in the management account for now"

```json
{
  "skills": ["governing-aws-organizations"],
  "query": "We only have the management account set up so far. Can we just deploy our first application there while we figure out the org structure?",
  "expected_behavior": [
    "Refuses to validate the approach and clearly flags NP-1 (CRITICAL anti-pattern)",
    "Explains that SCPs do not restrict any principal in the management account — the application would be completely un-guardrailed",
    "States the management account should contain only org-admin resources, not workloads",
    "Provides the correct alternative: create a member account under a Workloads OU for the application",
    "Does NOT offer a compromise like 'as a temporary measure it is fine' — this is a hard Never-Do",
    "Offers to guide the architect through the account creation and OU setup steps instead"
  ]
}
```

---

## Scenario 4 — Edge: Policy staging before root attachment

```json
{
  "skills": ["governing-aws-organizations"],
  "query": "We have a new SCP that denies all use of EC2 instance types larger than xlarge. We want to roll it out across all 300 accounts. What is the right process?",
  "expected_behavior": [
    "Flags the risk of attaching untested SCPs directly to the root (NP-3 — HIGH risk, affects all 300 accounts simultaneously)",
    "Recommends creating or using a Policy Staging OU with representative test accounts (AD-9)",
    "Recommends validating the SCP against IAM service-last-accessed data and CloudTrail usage before broad rollout",
    "Suggests gradual rollout: Policy Staging OU → one Workloads sub-OU → all non-prod OUs → root/all OUs",
    "Notes the SCP 10,240 character size limit and 10-per-entity attach limit to watch for at scale",
    "Recommends monitoring CloudTrail for AttachPolicy events targeting the root as a detection control"
  ]
}
```

---

## Scenario 5 — Canonical: GuardDuty centralization across org

```json
{
  "skills": ["governing-aws-organizations"],
  "query": "We want to enable GuardDuty across all our 50 AWS accounts, with a central place to view all findings. What is the correct architecture?",
  "expected_behavior": [
    "Requires all-features mode enabled in Organizations (AD-1)",
    "Designates a dedicated Audit/Security Tooling member account as the GuardDuty delegated administrator — not the management account (AD-6, NP-7)",
    "Specifies that GuardDuty is a Regional service — delegated admin must be configured in each Region separately",
    "Sets GuardDuty auto-enable to ALL (not NEW) to cover existing + future accounts",
    "Notes the 50,000-member-per-Region limit (not a concern at 50 accounts but good to state)",
    "Provides the verification command: aws guardduty list-organization-admin-accounts",
    "Recommends the same Audit account as delegated admin for Security Hub for consolidated findings (AD-6)"
  ]
}
```
