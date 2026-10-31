# Evaluation Scenarios — architecting-aws-multi-account-organizations

Skill version: AWS Organizations 2026 (research date 2026-08-26)

---

## Scenario 1 — Canonical: New Enterprise Landing Zone Design

```json
{
  "skills": ["architecting-aws-multi-account-organizations"],
  "query": "We are starting a brand-new AWS organization for a 200-person company. We expect 20 accounts today and 150 in two years. Walk me through the recommended landing zone architecture including OU structure, security accounts, and access management.",
  "expected_behavior": [
    "Recommends AWS Control Tower as the baseline governance layer (not DIY Organizations) for standard enterprise use case",
    "Specifies foundational accounts: Log Archive, Security Tooling (Audit), Network, Shared Services, Backup in their respective OUs",
    "Specifies foundational OUs: Security OU, Infrastructure OU, Workloads OU (Prod/NonProd), Suspended OU, Policy Staging OU",
    "Recommends IAM Identity Center with an external IdP (Okta, Azure AD) for all human access; zero IAM users in member accounts",
    "Recommends AFT for the scaling path at >50 accounts",
    "Identifies management account as org-management only — no workloads",
    "References Security Tooling delegated admin pattern for GuardDuty, Security Hub, Detective, Config, Macie, Inspector sharing the same account",
    "Does not recommend LZA unless compliance requirements (GovCloud, DoD) are stated"
  ]
}
```

---

## Scenario 2 — Canonical: SCP and RCP Data Perimeter Implementation

```json
{
  "skills": ["architecting-aws-multi-account-organizations"],
  "query": "Our CISO requires a data perimeter preventing external principals from accessing our S3 buckets and KMS keys even if someone misconfigures a bucket policy. What policies do we need and where do we attach them?",
  "expected_behavior": [
    "Identifies RCPs (Resource Control Policies) as the resource-centric guardrail — the correct tool for blocking external principals from accessing org resources",
    "Identifies SCPs as the identity-centric complement (blocking org principals from accessing external resources)",
    "Provides RCP condition using aws:PrincipalOrgID to restrict access to org principals only",
    "Includes exception for AWS service principals using aws:PrincipalIsAWSService condition key",
    "Includes exception for cross-service calls using aws:ViaAWSService condition key",
    "Mentions VPC endpoint policies as the network-centric third axis",
    "States RCPs are attached at the org root for broadest coverage",
    "Does not suggest S3 bucket policies alone are sufficient (they can be misconfigured at account level)",
    "References the five initial RCP-supported services: S3, STS, KMS, SQS, Secrets Manager"
  ]
}
```

---

## Scenario 3 — Edge Case: Migrating an Existing Standalone Account Into the Org

```json
{
  "skills": ["architecting-aws-multi-account-organizations"],
  "query": "We have an existing AWS account with production workloads that we want to bring into our organization. What is the safe migration approach?",
  "expected_behavior": [
    "Recommends using the Transitional OU as the initial landing zone for the migrated account",
    "Advises applying a limited SCP (read-only restrictions) to the Transitional OU while assessing the account's existing resources",
    "Warns not to use the account's existing IAM users for access — use IAM Identity Center permission sets instead",
    "Mentions checking existing resources against Workloads OU SCPs before moving the account to its final OU",
    "Notes the account must be at least 4 days old before it can be closed (if that becomes necessary)",
    "Does not suggest moving directly to the Workloads OU without assessment",
    "Identifies risk of existing IAM users that violate IAM Identity Center-only access SCP"
  ]
}
```

---

## Scenario 4 — Edge Case: Control Tower Drift in an Existing Org

```json
{
  "skills": ["architecting-aws-multi-account-organizations"],
  "query": "Control Tower is showing a drift alert on our Security OU. A team member manually modified an SCP in AWS Organizations. How should we handle this?",
  "expected_behavior": [
    "Warns against manually editing Control Tower-managed SCPs or OUs directly in AWS Organizations — this causes drift",
    "Recommends using the Control Tower console Re-register OU function to reconcile drift, not manual repair via Organizations",
    "Recommends establishing a Policy Staging OU pattern to test SCP changes before applying to production OUs",
    "Notes that SCP changes should go through the Policy Staging OU → review → target OU promotion workflow",
    "Recommends a change management process where all policy changes are documented as change records linked to CloudTrail event IDs",
    "Does not recommend manually undoing the change in Organizations without Control Tower reconciliation"
  ]
}
```

---

## Scenario 5 — Misuse: Anti-Pattern Trap — Single AWS Account for All Environments

```json
{
  "skills": ["architecting-aws-multi-account-organizations"],
  "query": "Our startup wants to use a single AWS account for development, test, and production to keep things simple. Is this okay for now?",
  "expected_behavior": [
    "Flags this as the canonical multi-account anti-pattern and does not validate it as acceptable",
    "Explains that SCPs cannot enforce environment isolation within a single account — IAM policies become the only isolation mechanism",
    "States that a production incident in a single-account model has unlimited blast radius",
    "Recommends the absolute minimum: separate Production and NonProd accounts plus a Sandbox account for experimentation",
    "References the AWS Whitepaper 'Organizing Your AWS Environment Using Multiple Accounts' (April 30, 2025)",
    "If budget is the constraint, recommends mitigations for single-account environments: separate VPCs per environment, strict IAM boundary policies, CloudTrail logging to a separate account",
    "Does not simply approve the single-account approach as a valid starting point without caveats"
  ]
}
```

---

## Evaluation Grading

| Score | Criteria |
|---|---|
| 5 — Excellent | All expected behaviors present; correct AWS service names; correct policy type terminology (Authorization vs Declarative; SCP vs RCP); no deprecated terms ("management policies") |
| 4 — Good | ≥ 80% of expected behaviors; minor terminology imprecision (e.g., missing ViaAWSService exception in RCP scenario) |
| 3 — Acceptable | Core recommendation correct but missing key safeguards (e.g., Scenario 2 correct RCP but missing service-principal exception) |
| 2 — Marginal | Correct intent but wrong mechanism (e.g., recommending bucket policies instead of RCPs for data perimeter) |
| 1 — Failing | Uses deprecated terminology; recommends workloads in management account; validates single-account approach without caveats; conflates SCPs and RCPs |
