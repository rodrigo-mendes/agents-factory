# Evaluation Scenarios — architecting-aws-security-pillar

These scenarios validate that the skill correctly applies the AWS Well-Architected Framework Security Pillar
(November 6, 2024 edition) to architecture decisions for multi-account production workloads.

---

## Scenario 1 — Canonical: Day-one security baseline for a new AWS organization

```json
{
  "skills": ["architecting-aws-security-pillar"],
  "query": "We are launching a new AWS organization for a SaaS product. We have a dev team of 15, a staging environment, and a production environment. What is the minimum security baseline we need before the first production workload goes live?",
  "expected_behavior": [
    "Recommends AWS Organizations OU hierarchy (Prod OU, Non-Prod OU, Security OU, Sandbox OU) — SEC-AD-1",
    "Specifies CloudTrail organizational trail → Log Archive S3 with Object Lock as a day-one requirement — SEC-AD-6",
    "Specifies GuardDuty org-wide and Security Hub with AWS Foundational Security Best Practices standard — SEC-AD-6",
    "Recommends IAM Identity Center for all human access (not per-user IAM users) — SEC-AD-2",
    "Requires phishing-resistant MFA (FIDO2/hardware key) on root of every account — SEC-AD-4",
    "Recommends AWS Control Tower for new organizations as the fastest path to a best-practice baseline (Decision A)",
    "Provides the seven-item day-one checklist from Quick Reference",
    "Does NOT recommend per-user IAM users with permanent access keys"
  ]
}
```

---

## Scenario 2 — Architectural Decision: Choosing between Control Tower and DIY Organizations

```json
{
  "skills": ["architecting-aws-security-pillar"],
  "query": "Our company has been on AWS for 3 years with 40+ accounts already managed through a homegrown Terraform pipeline that provisions accounts with our own SCP set. Should we migrate to AWS Control Tower?",
  "expected_behavior": [
    "Asks about the existing governance tooling and SCP coverage before making a recommendation — Decision A (Ask First)",
    "Flags that retrofitting Control Tower onto a mature DIY Organizations setup is high-effort",
    "Presents both options (Control Tower vs DIY) with the trade-off matrix from Decision A",
    "Does NOT unilaterally recommend Control Tower without acknowledging the existing DIY setup",
    "Notes that both options use Organizations as the underlying primitive, making future migration possible",
    "Suggests evaluating whether existing compliance/customization requirements exceed Control Tower's constraints"
  ]
}
```

---

## Scenario 3 — Edge Case: External workloads needing AWS access without long-term keys

```json
{
  "skills": ["architecting-aws-security-pillar"],
  "query": "We have an on-premises Jenkins CI/CD server that needs to push Docker images to Amazon ECR and deploy to ECS. How should we give it AWS credentials without embedding access keys in the Jenkins config?",
  "expected_behavior": [
    "Recommends IAM Roles Anywhere with X.509 certificates from a trusted CA — SEC-AD-3 (external workloads)",
    "Explains that the workload exchanges X.509 certificates for STS temporary credentials scoped to a least-privilege IAM role",
    "Mentions the Roles Anywhere credential helper for the SDK credential provider chain",
    "Alternatively mentions GitHub Actions / Jenkins OIDC plugin if the Jenkins version supports OIDC federation",
    "Explicitly rejects embedding IAM access keys in Jenkins configuration — SEC-ND-1",
    "Specifies the IAM role must be least-privilege (ECR push + ECS deploy actions only, scoped to specific resource ARNs)"
  ]
}
```

---

## Scenario 4 — Anti-Pattern Trap: Request to use root credentials for automation

```json
{
  "skills": ["architecting-aws-security-pillar"],
  "query": "Our ops team wants to create a root access key on the management account to run a nightly AWS Organizations compliance report. Can you help me set this up?",
  "expected_behavior": [
    "Refuses to provide guidance for creating or using root access keys for automation — SEC-ND-2 (CRITICAL)",
    "Explains that root user credentials cannot be restricted by SCPs and compromise equals total account takeover",
    "Proposes a correct alternative: create a least-privilege IAM role in the management account with read-only Organizations permissions (organizations:List*, organizations:Describe*) and run the compliance report under that role",
    "Recommends running the role via IAM Identity Center permission set so the ops team gets temporary credentials",
    "Instructs to lock root credentials in a secrets vault, enable FIDO2 MFA on root, and delete any existing root access keys",
    "Does NOT provide any instructions for creating root access keys"
  ]
}
```

---

## Scenario 5 — Data Classification: Choosing encryption key type

```json
{
  "skills": ["architecting-aws-security-pillar"],
  "query": "We store three types of data in S3: (1) publicly available product documentation, (2) internal employee HR records, (3) PCI-DSS scoped cardholder data. What encryption key strategy should we use?",
  "expected_behavior": [
    "Asks or acknowledges the data classification for each tier before recommending key type — Decision C (Ask First) — but here classification is provided, so proceeds to recommend",
    "Public documentation: AWS-managed keys or no custom key management required (low sensitivity)",
    "HR records (internal/confidential): recommends KMS CMK with CloudTrail key-use auditing",
    "PCI-DSS cardholder data (regulated/restricted): mandates KMS CMK with explicit key policy, considers whether external key store is needed based on PCI key-custody requirements",
    "Recommends Amazon Macie to discover unclassified sensitive data across S3 — SEC-AD-5",
    "Does NOT recommend a single key type for all three tiers"
  ]
}
```

---

## Scenario 6 — Detection Gap: Security group open to the internet

```json
{
  "skills": ["architecting-aws-security-pillar"],
  "query": "During an audit I found that 12 EC2 instances in our production VPC have a security group with port 22 open to 0.0.0.0/0. How do I remediate this and prevent recurrence?",
  "expected_behavior": [
    "Identifies this as SEC-ND-8 anti-pattern (HIGH risk) — security groups open to 0.0.0.0/0 on management ports",
    "Immediate remediation: remove the inbound rule for tcp/22 from 0.0.0.0/0 on the offending security groups",
    "Replacement access mechanism: configure Systems Manager Session Manager for shell access (no open ports required) — SEC-AD-7",
    "Preventive controls: AWS Config managed rules restricted-ssh and vpc-sg-open-only-to-authorized-ports; Security Hub FSBP findings EC2.13/EC2.14",
    "Provides the Verification Loop command: aws ec2 describe-security-groups filtered on port 22 / 0.0.0.0/0",
    "Optionally mentions EventBridge rule to auto-remediate future violations via Lambda or SSM Automation — SEC-AD-6 automated remediation pattern",
    "Does NOT suggest restricting to a specific CIDR range as the primary fix (Session Manager is the correct replacement)"
  ]
}
```
