# AWS Well-Architected Framework — Security Pillar
# Research Knowledge Base

**Target Edition**: AWS WAF 2025 (latest published Security Pillar whitepaper revision: **November 6, 2024**)
**Research Date**: 2026-07-31
**Primary Audience**: Cloud Architects and Tech Leads
**Official Source**: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html

> ⚠️ **Version note**: The "AWS WAF 2025" edition requested maps to the **currently published** Security Pillar whitepaper, whose latest revision date is **November 6, 2024**. This is the current stable edition as of 2026-07-31 (no newer whitepaper revision has superseded it), so it is accepted under Version Absolutism. Because the revision date is > 12 months old, individual claims carry a `⚠️ Source dated` note where relevant. AWS re:Invent Dec 2025 introduced operational changes to some referenced services (notably AWS Security Hub); these are flagged inline.

---

## Executive Summary

The Security Pillar of the AWS Well-Architected Framework provides prescriptive guidance for designing, delivering, and maintaining secure AWS workloads. It is organized around **seven focus areas** — Security Foundations, Identity and Access Management, Detection, Infrastructure Protection, Data Protection, Incident Response, and Application Security — and is assessed through **eleven best-practice questions (SEC 1–SEC 11)**. The pillar is grounded in **seven design principles**: strong identity foundation, traceability, security at all layers, automated security best practices, protecting data in transit and at rest, keeping people away from data, and preparing for security events. The **November 6, 2024** revision refreshed 43 Security best practices across nine questions, with the most significant changes to SEC03 (Permissions management — expanded ABAC guidance), SEC02 (identity federation and secrets management), SEC04 (AWS CloudTrail Lake replacing self-managed SIEM recommendations), and SEC08/SEC09 (S3 Object Lock, Glacier Vault Lock, and mTLS/private certificates). The central 2025 theme is **automation and centralization**: eliminate long-term static credentials, centralize identity via AWS IAM Identity Center, centralize findings via AWS Security Hub, and automate detection-to-remediation loops.

---

## Glossary

| Term | Official Definition (source: Security Pillar whitepaper, Nov 6 2024) |
|------|----------------------------------------------------------------------|
| **Security Pillar** | The pillar describing how to use cloud technologies to protect data, systems, and assets and improve security posture. Composed of seven areas. |
| **Defense in depth** | Applying multiple security controls across all layers (edge, VPC, load balancing, instance/compute, OS, application, code). |
| **Least privilege** | Granting only the permissions required to perform a task, scoped to specific actions, resources, and conditions. |
| **Separation of duties** | Enforcing appropriate authorization for each interaction with AWS resources so no single identity holds excessive control. |
| **Traceability** | Real-time monitoring, alerting, and auditing of actions and changes, integrated with automated investigation/response. |
| **Trust boundary** | A defined edge (network or account boundary) across which trust assumptions change; a core infrastructure-protection concept. |
| **AWS Organizations** | Account management service to centrally govern multiple AWS accounts, apply Service Control Policies (SCPs), and consolidate. |
| **Service Control Policy (SCP)** | An organization policy that sets the maximum available permissions (guardrails) for accounts in an AWS Organization. |
| **AWS IAM Identity Center** | Centralized workforce identity and access service (successor to AWS SSO) using permission sets and SCIM provisioning. |
| **Permission boundary** | An advanced IAM feature that sets the maximum permissions an identity-based policy can grant to an IAM role or user. |
| **ABAC (Attribute-Based Access Control)** | Authorization based on tags/attributes rather than static role assignments; emphasized in the Nov 2024 SEC03 revision. |
| **Amazon GuardDuty** | Threat-detection service that continuously monitors for unexpected, unauthorized, or malicious activity in AWS accounts. |
| **AWS Security Hub** | Cloud security posture management service that aggregates, normalizes, and prioritizes security findings across services. |
| **AWS KMS** | Managed service to create and control cryptographic keys used to protect data at rest and in transit. |

---

## Framework Pillars
### The 7 Security Pillar Focus Areas (AWS WAF 2025 / Nov 6 2024 revision)

The pillar defines security in the cloud as composed of **seven areas**, assessed via **SEC 1–SEC 11** best-practice questions.

**Design principles (all areas):** (1) Implement a strong identity foundation; (2) Maintain traceability; (3) Apply security at all layers; (4) Automate security best practices; (5) Protect data in transit and at rest; (6) Keep people away from data; (7) Prepare for security events.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/security.html (accessed 2026-07-31)

### 1. Security Foundations — SEC 1
**Definition**: Foundational account/organization operating practices that influence all other areas.
**Question SEC 1**: *How do you securely operate your workload?*
**Key AWS services**: AWS Organizations, Service Control Policies (SCPs), AWS Control Tower, AWS Security Hub, AWS Systems Manager.
**Assessment focus**: multi-account governance, SCP guardrails, staying current with threats, automating control testing in pipelines, threat modeling, and evaluating new security services.
Source: https://docs.aws.amazon.com/config/latest/developerguide/operational-best-practices-for-wa-Security-Pillar.html (accessed 2026-07-31)

### 2. Identity and Access Management — SEC 2 & SEC 3
**Definition**: Managing human and machine identities and their permissions. Two sub-areas: **Identity management** and **Permissions management**.
**Question SEC 2**: *How do you manage identities for people and machines?*
**Question SEC 3**: *How do you manage permissions for people and machines?*
**Key AWS services**: AWS IAM Identity Center, IAM roles, IAM permission boundaries, IAM Access Analyzer, AWS Secrets Manager, AWS Organizations SCPs.
**2024 revision note**: All SEC03 best practices revised; expanded **ABAC** guidance. SEC02 refined identity federation and secrets management.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html (accessed 2026-07-31)

### 3. Detection — SEC 4
**Definition**: Detection of unexpected/unwanted configuration changes and unexpected behavior across the delivery lifecycle and at runtime.
**Question SEC 4**: *How do you detect and investigate security events?*
**Best practices**:
- SEC04-BP01 Configure service and application logging
- SEC04-BP02 Capture logs, findings, and metrics in standardized locations
- SEC04-BP03 Correlate and enrich security alerts
- SEC04-BP04 Initiate remediation for non-compliant resources
**Key AWS services**: Amazon GuardDuty, AWS CloudTrail (+ CloudTrail Lake), AWS Config, Amazon Detective, Amazon Security Lake, AWS Security Hub, Amazon CloudWatch.
**2024 revision note**: AWS CloudTrail Lake replaced self-managed OpenSearch SIEM recommendations.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html (accessed 2026-07-31)

### 4. Infrastructure Protection — SEC 5 & SEC 6
**Definition**: Defense-in-depth control methodologies protecting systems and services from unauthorized access and vulnerabilities. Two sub-areas: **Protecting networks** and **Protecting compute**.
**Question SEC 5**: *How do you protect your network resources?*
**Question SEC 6**: *How do you protect your compute resources?*
**Key AWS services**: Amazon VPC, security groups, network ACLs, AWS Network Firewall, AWS WAF, AWS Shield Advanced, Amazon Inspector, AWS Systems Manager Patch Manager.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html (accessed 2026-07-31)

### 5. Data Protection — SEC 7, SEC 8 & SEC 9
**Definition**: Data classification and protection at rest and in transit. Three sub-areas: **Data classification**, **Protecting data at rest**, **Protecting data in transit**.
**Question SEC 7**: *How do you classify your data?*
**Question SEC 8**: *How do you protect your data at rest?*
**Question SEC 9**: *How do you protect your data in transit?*
**Key AWS services**: AWS KMS, Amazon Macie, AWS Certificate Manager (ACM), Amazon S3 (SSE-KMS, Object Lock), Amazon EBS encryption, AWS S3 Glacier Vault Lock.
**2024 revision note**: SEC08 expanded guidance on S3 Object Lock and S3 Glacier Vault Lock; SEC09 added mTLS and private-certificate recommendations.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/data-protection.html (accessed 2026-07-31)

### 6. Incident Response — SEC 10
**Definition**: Mechanisms to respond to and mitigate the impact of security incidents; preparation, operations, and post-incident activity.
**Question SEC 10**: *How do you anticipate, respond to, and recover from incidents?*
**Sub-topics**: Aspects of AWS incident response, Design goals of cloud response, Preparation, Operations, Post-incident activity.
**Key AWS services**: AWS Security Hub, Amazon EventBridge, AWS Systems Manager Automation (runbooks), AWS Backup, AWS CloudFormation (clean-room/forensic accounts).
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/incident-response.html (accessed 2026-07-31)

### 7. Application Security — SEC 11
**Definition**: How you design, build, and test the security properties of workloads across the SDLC — organization/culture, security *of* the pipeline, security *in* the pipeline, and dependency management.
**Question SEC 11**: *How do you incorporate and validate the security properties of applications throughout the design, development, and deployment lifecycle?*
**Best practices**:
- SEC11-BP01 Train for application security
- SEC11-BP02 Automate testing throughout the development and release lifecycle
- SEC11-BP03 Perform regular penetration testing
- SEC11-BP04 Conduct code reviews
- SEC11-BP05 Centralize services for packages and dependencies
- SEC11-BP06 Deploy software programmatically
- SEC11-BP07 Regularly assess security properties of the pipelines
- SEC11-BP08 Build a program that embeds security ownership in workload teams
**Key AWS services**: Amazon Inspector, Amazon CodeGuru Security, AWS Secrets Manager, AWS WAF, AWS CodeArtifact, AWS Signer.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/application-security.html (accessed 2026-07-31)

---

## Mandatory Patterns
### ✅ Always-Do

**Pattern: Enforce MFA and lock away the AWS account root user**
Why: Design principle "Implement a strong identity foundation." The root user has unrestricted access that cannot be constrained by IAM policies; SEC 1 requires securing it. (SEC01/SEC02)
Provider Service: AWS account root user, AWS IAM, hardware MFA (FIDO2/WebAuthn).
Architecture Decision:
  Enable hardware MFA on the root user, delete root access keys, and never use root for routine tasks. Perform daily operations through federated roles.
Verification:
  Security Hub FSBP controls **[IAM.6]** hardware MFA for root, **[IAM.4]** no root access keys, **[IAM.9]** root MFA. AWS Config rules `root-account-hardware-mfa-enabled`, `iam-root-access-key-check`.
  CLI: `aws iam get-account-summary --query 'SummaryMap.AccountMFAEnabled'`
Trade-offs: Minimal cost; small operational friction managing a hardware key; drastically reduces account-takeover blast radius.
Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html (accessed 2026-07-31)

---

**Pattern: Centralize workforce identity with AWS IAM Identity Center; eliminate long-term IAM users for humans**
Why: Strong identity foundation + "eliminate reliance on long-term static credentials." SEC02 (Nov 2024 revision) refines identity federation. (SEC02)
Provider Service: AWS IAM Identity Center (permission sets, SCIM provisioning), external IdP (Okta/Entra ID).
Architecture Decision:
  Federate an external IdP via SCIM/SAML, assign access through permission sets mapped to short-lived role sessions. No standing IAM users for human access.
Verification:
  Security Hub FSBP **[IAM.2]** users have no attached policies; Config `iam-user-unused-credentials-check`, `access-keys-rotated`.
  CLI: `aws sso-admin list-instances` and `aws iam list-users` (expect near-zero human users).
Trade-offs: Requires IdP integration effort; removes credential-rotation burden and enables centralized deprovisioning.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html (accessed 2026-07-31)

---

**Pattern: Apply organization-wide guardrails with AWS Organizations SCPs**
Why: SEC 1 secure-operations; establishes account boundaries as the outermost trust boundary and enforces preventive controls that IAM alone cannot. (SEC01/SEC03)
Provider Service: AWS Organizations, Service Control Policies, AWS Control Tower.
Architecture Decision:
  Group accounts into OUs; attach SCPs denying region opt-out, root-user actions, and disabling of security services (GuardDuty/Config/CloudTrail). Baseline via Control Tower.
Verification:
  Config `account-part-of-organizations`. CLI: `aws organizations list-policies --filter SERVICE_CONTROL_POLICY`.
Trade-offs: SCPs can cause hard-to-diagnose "access denied" if overly broad; test in a sandbox OU first. Zero direct cost.
Source: https://docs.aws.amazon.com/config/latest/developerguide/operational-best-practices-for-wa-Security-Pillar.html (accessed 2026-07-31)

---

**Pattern: Enable multi-Region, organization-wide detection (GuardDuty + Security Hub + CloudTrail + Config)**
Why: Design principle "Maintain traceability." SEC04-BP01/BP02 require standardized logging and centralized findings. (SEC04)
Provider Service: Amazon GuardDuty (delegated admin), AWS Security Hub, AWS CloudTrail (org trail + CloudTrail Lake), AWS Config aggregator.
Architecture Decision:
  Delegate a dedicated security/audit account as administrator for GuardDuty, Security Hub, and Config; create an organization CloudTrail with a multi-Region trail logging management + S3 data events.
Verification:
  Config `guardduty-enabled-centralized`, `securityhub-enabled`, `multi-region-cloudtrail-enabled`, `cloudtrail-security-trail-enabled`.
  CLI: `aws guardduty list-detectors`, `aws securityhub get-enabled-standards`.
Trade-offs: GuardDuty and CloudTrail data-event costs scale with activity/volume; centralization simplifies audit and cross-account correlation.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html (accessed 2026-07-31)

---

**Pattern: Encrypt all data at rest with AWS KMS customer-managed keys**
Why: Design principle "Protect data in transit and at rest." SEC08 (Nov 2024 revision expanded) mandates encryption at rest. (SEC08)
Provider Service: AWS KMS (CMK), Amazon S3 SSE-KMS + S3 Object Lock, Amazon EBS default encryption.
Architecture Decision:
  Enable EBS encryption-by-default per Region; set S3 default encryption to SSE-KMS; use KMS key policies + grants for least-privilege key usage; enable Object Lock for immutable/WORM data.
Verification:
  Security Hub FSBP **[EC2.7]** EBS default encryption, **[S3.4]/[S3.17]** S3 encryption. CLI: `aws ec2 get-ebs-encryption-by-default`.
Trade-offs: KMS request costs + minor latency on crypto operations; strong regulatory-compliance and blast-radius benefits.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/data-protection.html (accessed 2026-07-31)

---

**Pattern: Enforce encryption in transit (TLS 1.2+ / mTLS) with AWS Certificate Manager**
Why: SEC09 (Nov 2024 revision added mTLS/private certs). Protects data in transit end-to-end. (SEC09)
Provider Service: AWS Certificate Manager (public + ACM Private CA), Elastic Load Balancing, Amazon CloudFront, Amazon API Gateway (mTLS).
Architecture Decision:
  Terminate TLS 1.2+ at ELB/CloudFront using ACM certs; enforce HTTPS-only via redirects and S3 bucket policies with `aws:SecureTransport`; use mTLS for service-to-service trust where required.
Verification:
  Security Hub FSBP **[ELB.1]** HTTP→HTTPS redirect, **[S3.5]** SSL-only requests. CLI: `aws acm list-certificates`.
Trade-offs: Certificate lifecycle management (ACM auto-renews public certs); negligible latency; eliminates plaintext exposure.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/data-protection.html (accessed 2026-07-31)

---

**Pattern: Automate detection-to-remediation loops (Security Hub → EventBridge → Systems Manager Automation)**
Why: Design principles "Automate security best practices" + "Prepare for security events." SEC04-BP04 and SEC10. (SEC04/SEC10)
Provider Service: AWS Security Hub, Amazon EventBridge, AWS Systems Manager Automation runbooks, AWS Lambda.
Architecture Decision:
  Route Security Hub findings and Config non-compliance events through EventBridge rules to SSM Automation documents (e.g., auto-revoke public S3 access, isolate a compromised EC2 instance) with human-approval gates for high-impact actions.
Verification:
  Config `cloudwatch-alarm-action-check`. CLI: `aws events list-rules`, `aws ssm list-documents --filters Key=DocumentType,Values=Automation`.
Trade-offs: Automation carries risk of over-aggressive remediation; gate destructive actions with approvals. Reduces MTTR significantly.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/incident-response.html (accessed 2026-07-31)

---

## Architectural Decisions
### ⚠️ Ask-First

**Decision: How to manage human access to AWS at scale**
Options:
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| IAM Identity Center + external IdP | AWS IAM Identity Center + Okta/Entra ID | Central deprovisioning, SSO UX | IdP dependency | Enterprise with existing IdP |
| IAM Identity Center identity store | AWS IAM Identity Center (built-in) | No external IdP needed | Fewer advanced IdP features | Smaller orgs, no IdP |
| IAM roles + SAML federation | AWS IAM + SAML | Fine-grained control | More manual role mapping | Legacy/edge integration needs |

Ask The Architect: "Do you have an existing corporate IdP (Entra ID/Okta) to federate, or should IAM Identity Center be the identity source of truth?"
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html (accessed 2026-07-31)

---

**Decision: Network perimeter protection depth**
Options:
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Security groups + NACLs only | Amazon VPC native | Lowest cost/complexity | No L7/IPS inspection | Simple internal workloads |
| + AWS WAF on ALB/CloudFront/API GW | AWS WAF | L7 protection (OWASP) | Rule tuning effort | Public web apps/APIs |
| + AWS Network Firewall | AWS Network Firewall | Stateful L3-L7 egress/IPS | Cost + throughput planning | Regulated/egress-controlled VPCs |
| + AWS Shield Advanced | AWS Shield Advanced | DDoS cost protection + DRT | $3k/mo subscription | Internet-facing critical apps |

Ask The Architect: "What is the workload exposure (internet-facing vs internal) and regulatory requirement for egress inspection and DDoS protection?"
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html (accessed 2026-07-31)

---

**Decision: KMS key ownership and rotation model**
Options:
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| AWS-managed keys | AWS KMS (aws/service) | Zero management | No key policy control, no cross-account | Low-sensitivity data |
| Customer-managed keys (CMK) | AWS KMS CMK | Key policy control, auto-rotation, audit | Management overhead | Regulated/sensitive data |
| Imported key material / CloudHSM | AWS KMS + AWS CloudHSM | Full key custody (BYOK/HYOK) | Highest complexity/cost | Strict key-custody mandates |

Ask The Architect: "Do compliance requirements demand customer control over key material and rotation, or is AWS-managed sufficient?"
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/data-protection.html (accessed 2026-07-31)

---

**Decision: Detection & investigation data aggregation strategy**
Options:
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Security Hub central findings | AWS Security Hub | Normalized posture view | Not a full log lake | Posture management focus |
| CloudTrail Lake | AWS CloudTrail Lake | Managed SQL over events | Event scope limited to trails | Audit/investigation queries |
| Amazon Security Lake (OCSF) | Amazon Security Lake | Open-schema lake, 3rd-party feeds | Setup + storage cost | Multi-source SIEM/analytics |
| Amazon Detective | Amazon Detective | Graph-based investigation | Investigation-only | Root-cause deep dives |

Ask The Architect: "Is the priority posture management, investigation, or building a multi-source security data lake for analytics/SIEM?"
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html (accessed 2026-07-31)

---

**Decision: Multi-account structure and guardrail baseline**
Options:
| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| AWS Control Tower landing zone | AWS Control Tower + Organizations | Fast, opinionated baseline | Less customization | Greenfield/standard needs |
| Custom Organizations + SCPs | AWS Organizations | Full flexibility | Build/maintain yourself | Complex existing estates |
| Single account, IAM boundaries | AWS IAM permission boundaries | Simplicity | Weak blast-radius isolation | Very small workloads only |

Ask The Architect: "Do you need a prescriptive landing zone (Control Tower) or a bespoke Organizations design for existing accounts?"
Source: https://docs.aws.amazon.com/config/latest/developerguide/operational-best-practices-for-wa-Security-Pillar.html (accessed 2026-07-31)

---

## Anti-Patterns
### 🚫 Never-Do

**Anti-Pattern: Using the AWS account root user for daily operations / creating root access keys**
Why: Violates "strong identity foundation"; root cannot be constrained by IAM policies. (SEC01/SEC02)
Risk Level: CRITICAL
Blast Radius: Entire AWS account (billing, IAM, all resources).
❌ Wrong: `aws iam create-access-key` while signed in as root; using root credentials in CI/CD.
✅ Correct: Delete root access keys; enable hardware MFA on root; operate via AWS IAM Identity Center permission sets / IAM roles with short-lived sessions.
Detection: Security Hub FSBP **[IAM.4]**, **[IAM.9]**, **[IAM.6]**; AWS Config `iam-root-access-key-check`, `root-account-mfa-enabled`.
Impact: Full account takeover / data breach.
Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html (accessed 2026-07-31)

---

**Anti-Pattern: Attaching wildcard `Action: "*"` / `Resource: "*"` admin policies to identities**
Why: Violates least privilege (SEC03). Nov 2024 SEC03 revision emphasizes scoped/ABAC permissions.
Risk Level: CRITICAL
Blast Radius: All resources reachable by the identity.
❌ Wrong: IAM policy `{"Effect":"Allow","Action":"*","Resource":"*"}` attached to an application role.
✅ Correct: Scope to specific actions/resources/conditions; use IAM permission boundaries and IAM Access Analyzer to generate least-privilege policies from CloudTrail activity.
Detection: Config `iam-policy-no-statements-with-admin-access`, `iam-policy-no-statements-with-full-access`; Security Hub FSBP **[IAM.1]**.
Impact: Privilege escalation / lateral movement.
Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started-reduce-permissions.html (accessed 2026-07-31)

---

**Anti-Pattern: Long-lived IAM user access keys embedded in code/CI instead of roles**
Why: Violates "eliminate long-term static credentials" (SEC02).
Risk Level: HIGH
Blast Radius: Any resource the key can access; keys leak via source control.
❌ Wrong: `AWS_ACCESS_KEY_ID=AKIA...` hardcoded in a repo or Lambda env var.
✅ Correct: Use IAM roles for EC2/Lambda/ECS (instance profiles, task roles) and OIDC federation for CI/CD; store any unavoidable secrets in AWS Secrets Manager with rotation.
Detection: Config `access-keys-rotated`, `codebuild-project-envvar-awscred-check`, `secretsmanager-rotation-enabled-check`; Security Hub FSBP **[IAM.3]**.
Impact: Credential compromise / data breach.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html (accessed 2026-07-31)

---

**Anti-Pattern: S3 buckets with public read/write and Block Public Access disabled**
Why: Violates permissions management (SEC03) and data protection (SEC08).
Risk Level: CRITICAL
Blast Radius: All objects in the bucket; potential mass data exfiltration.
❌ Wrong: Bucket ACL `public-read`; account-level S3 Block Public Access turned off.
✅ Correct: Enable S3 Block Public Access at account + bucket level; use bucket policies with least privilege and `aws:SecureTransport`; access via presigned URLs or CloudFront OAC.
Detection: Config `s3-bucket-public-read-prohibited`, `s3-bucket-public-write-prohibited`, `s3-account-level-public-access-blocks-periodic`; Security Hub FSBP **[S3.1]/[S3.2]/[S3.3]/[S3.8]**.
Impact: Data breach / compliance violation.
Source: https://docs.aws.amazon.com/config/latest/developerguide/operational-best-practices-for-wa-Security-Pillar.html (accessed 2026-07-31)

---

**Anti-Pattern: Security groups allowing 0.0.0.0/0 to sensitive ports (22/3389/databases)**
Why: Violates "apply security at all layers" and network protection (SEC05).
Risk Level: HIGH
Blast Radius: Any instance associated with the security group.
❌ Wrong: Inbound rule `0.0.0.0/0 : 22` (SSH open to the internet).
✅ Correct: Restrict SSH/RDP to known CIDRs or use AWS Systems Manager Session Manager (no open inbound ports); front web ports with ALB + AWS WAF.
Detection: Config `restricted-ssh`, `vpc-sg-open-only-to-authorized-ports`; Security Hub FSBP **[EC2.13]/[EC2.14]/[EC2.19]**.
Impact: Unauthorized access / lateral movement.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html (accessed 2026-07-31)

---

**Anti-Pattern: Disabling or not centralizing CloudTrail / running single-Region trails only**
Why: Violates "maintain traceability" (SEC04-BP01/BP02).
Risk Level: HIGH
Blast Radius: Loss of audit trail across the organization; blind spots in other Regions.
❌ Wrong: A single-Region trail in one account; no organization trail; log bucket writable by the same account.
✅ Correct: Organization-wide multi-Region CloudTrail delivering to a dedicated, access-restricted log-archive account with log-file validation and SSE-KMS.
Detection: Config `multi-region-cloudtrail-enabled`, `cloudtrail-security-trail-enabled`, `cloud-trail-cloud-watch-logs-enabled`; Security Hub FSBP **[CloudTrail.1]/[CloudTrail.2]**.
Impact: Undetected breach / failed audits.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html (accessed 2026-07-31)

---

**Anti-Pattern: Not enabling Amazon GuardDuty (no threat detection)**
Why: Violates detection of unexpected behavior (SEC04).
Risk Level: HIGH
Blast Radius: Organization-wide undetected threats (crypto-mining, credential exfiltration, malicious API calls).
❌ Wrong: GuardDuty disabled; relying only on manual CloudTrail review.
✅ Correct: Enable GuardDuty across all accounts/Regions via delegated administrator; route findings to Security Hub + EventBridge automation.
Detection: Config `guardduty-enabled-centralized`; Security Hub FSBP **[GuardDuty.1]**.
Impact: Prolonged undetected compromise.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html (accessed 2026-07-31)

---

**Anti-Pattern: Unencrypted EBS volumes / RDS / S3 (no at-rest encryption)**
Why: Violates "protect data at rest" (SEC08).
Risk Level: HIGH
Blast Radius: All data on the storage resource and its snapshots.
❌ Wrong: Launching EBS volumes and RDS instances with encryption disabled; snapshots inherit plaintext.
✅ Correct: Enable EBS encryption-by-default per Region; enable RDS storage encryption at creation; S3 default SSE-KMS — all with AWS KMS CMKs.
Detection: Config `encrypted-volumes`, `rds-storage-encrypted`, `s3-bucket-server-side-encryption-enabled`; Security Hub FSBP **[EC2.7]/[RDS.3]/[S3.4]**.
Impact: Data breach / compliance violation.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/data-protection.html (accessed 2026-07-31)

---

**Anti-Pattern: Public RDS/Redshift/EBS snapshots and public-access database instances**
Why: Violates permissions and data protection (SEC03/SEC05/SEC08).
Risk Level: CRITICAL
Blast Radius: Entire database contents exposed to the internet.
❌ Wrong: `PubliclyAccessible: true` on an RDS instance; a public RDS snapshot.
✅ Correct: Place databases in private subnets, `PubliclyAccessible: false`, access via bastion/Session Manager or VPC-internal apps; keep snapshots private.
Detection: Config `rds-instance-public-access-check`, `rds-snapshots-public-prohibited`, `redshift-cluster-public-access-check`, `ebs-snapshot-public-restorable-check`; Security Hub FSBP **[RDS.2]/[Redshift.1]**.
Impact: Mass data breach.
Source: https://docs.aws.amazon.com/config/latest/developerguide/operational-best-practices-for-wa-Security-Pillar.html (accessed 2026-07-31)

---

**Anti-Pattern: No incident response plan / no pre-provisioned access & runbooks**
Why: Violates "prepare for security events" (SEC10). Preparation strongly affects response effectiveness.
Risk Level: HIGH
Blast Radius: Extended outage and uncontained compromise during an incident.
❌ Wrong: Ad-hoc scramble during an incident; responders lack pre-authorized break-glass roles or forensic tooling.
✅ Correct: Pre-provision break-glass IAM roles, forensic/clean-room accounts (via CloudFormation), SSM Automation runbooks, AWS Backup immutable copies; run regular game days.
Detection: Process control — validate via game-day exercises and Well-Architected review of SEC10.
Impact: Prolonged breach / data loss / regulatory penalties.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/incident-response.html (accessed 2026-07-31)

---

**Anti-Pattern: No automated application-security testing in the pipeline**
Why: Violates SEC11-BP02 (automate testing throughout the SDLC).
Risk Level: MEDIUM
Blast Radius: Vulnerabilities shipped to production; vulnerable dependencies.
❌ Wrong: Manual-only security review at release; unscanned third-party dependencies pulled directly from public registries.
✅ Correct: Integrate Amazon Inspector (CI/CD + runtime) and Amazon CodeGuru Security scans in the pipeline; centralize dependencies via AWS CodeArtifact; store secrets in AWS Secrets Manager.
Detection: SEC11 Well-Architected review; Amazon Inspector findings routed to Security Hub.
Impact: Exploitable production vulnerabilities.
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/application-security.html (accessed 2026-07-31)

---

**Anti-Pattern: EC2 instances using IMDSv1 (no metadata token protection)**
Why: Violates permissions management / defense in depth (SEC03/SEC06); IMDSv1 is exploitable via SSRF for credential theft.
Risk Level: HIGH
Blast Radius: The instance role's permissions, stealable via SSRF.
❌ Wrong: Launch template with `HttpTokens: optional` (IMDSv1 allowed).
✅ Correct: Enforce IMDSv2 with `HttpTokens: required` and `HttpPutResponseHopLimit: 1`.
Detection: Config `ec2-imdsv2-check`; Security Hub FSBP **[EC2.8]**.
Impact: Credential theft via SSRF → lateral movement.
Source: https://docs.aws.amazon.com/config/latest/developerguide/operational-best-practices-for-wa-Security-Pillar.html (accessed 2026-07-31)

---

## Service Equivalence Map

Covers the key services across all 7 focus areas.

| Service Class | AWS | GCP | Azure | OCI |
|---------------|-----|-----|-------|-----|
| Identity / SSO (SEC02) | AWS IAM / AWS IAM Identity Center | Cloud IAM / Identity Platform | Microsoft Entra ID (Azure AD) | OCI IAM / Identity Domains |
| Org governance (SEC01) | AWS Organizations + SCPs / AWS Control Tower | Google Cloud Organization / Org Policies | Azure Management Groups / Azure Policy | OCI Compartments / Tenancy Policies |
| Access analysis (SEC03) | AWS IAM Access Analyzer | IAM Recommender / Policy Analyzer | Entra Permissions Management | OCI IAM policy analysis |
| Secrets (SEC02/SEC11) | AWS Secrets Manager | Secret Manager | Azure Key Vault | OCI Vault (Secrets) |
| Threat detection (SEC04) | Amazon GuardDuty | Security Command Center (Threat) | Microsoft Defender for Cloud | OCI Cloud Guard |
| Posture mgmt / findings (SEC01/SEC04) | AWS Security Hub | Security Command Center | Microsoft Defender for Cloud | OCI Cloud Guard |
| Audit logging (SEC04) | AWS CloudTrail / CloudTrail Lake | Cloud Audit Logs | Azure Monitor Activity Log | OCI Audit |
| Config compliance (SEC04) | AWS Config | Config Controller / Asset Inventory | Azure Policy / Resource Graph | OCI Cloud Guard recipes |
| Security data lake (SEC04) | Amazon Security Lake | Chronicle / SecOps | Microsoft Sentinel | OCI Logging Analytics |
| Investigation (SEC04) | Amazon Detective | Security Command Center | Microsoft Sentinel | OCI Cloud Guard |
| Network isolation (SEC05) | Amazon VPC / Security Groups / NACLs | VPC / Firewall Rules | Virtual Network / NSGs | OCI VCN / Security Lists / NSGs |
| Network firewall (SEC05) | AWS Network Firewall | Cloud NGFW | Azure Firewall | OCI Network Firewall |
| WAF (SEC05/SEC11) | AWS WAF | Cloud Armor | Azure WAF (Front Door/App GW) | OCI WAF |
| DDoS protection (SEC05) | AWS Shield Advanced | Cloud Armor (Adaptive Protection) | Azure DDoS Protection | OCI DDoS protection |
| Vulnerability scanning (SEC06/SEC11) | Amazon Inspector | Security Command Center (Vuln) / Artifact Analysis | Defender for Cloud (Vuln) | OCI Vulnerability Scanning |
| Code security (SEC11) | Amazon CodeGuru Security | Cloud Security Scanner / SCC | Defender for DevOps / GitHub Advanced Security | OCI DevOps (scanning) |
| Key management (SEC08) | AWS KMS / AWS CloudHSM | Cloud KMS / Cloud HSM | Azure Key Vault / Managed HSM | OCI Vault / Dedicated KMS |
| Data classification (SEC07) | Amazon Macie | Sensitive Data Protection (DLP) | Microsoft Purview | OCI Data Safe |
| Certificates / TLS (SEC09) | AWS Certificate Manager / ACM Private CA | Certificate Manager / CAS | Azure Key Vault Certificates | OCI Certificates |
| Backup / recovery (SEC10) | AWS Backup | Backup and DR Service | Azure Backup | OCI Backup |
| Event automation (SEC10) | Amazon EventBridge + AWS Systems Manager Automation | Eventarc + Cloud Workflows | Event Grid + Azure Automation | OCI Events + Functions |

---

## Source Bibliography

### Tier 1 — Official AWS Documentation (Security Pillar whitepaper, current stable rev. Nov 6 2024)
> ⚠️ Whitepaper revision dated 2024-11; it is the current stable edition (no newer revision as of 2026-07-31). Verify currency at each access.
- Welcome / overview — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html (accessed 2026-07-31; publication date Nov 6, 2024)
- Security foundations & design principles — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/security.html (accessed 2026-07-31)
- Identity and access management — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html (accessed 2026-07-31)
- Detection — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html (accessed 2026-07-31)
- Infrastructure protection — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html (accessed 2026-07-31)
- Data protection — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/data-protection.html (accessed 2026-07-31)
- Incident response — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/incident-response.html (accessed 2026-07-31)
- Application security — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/application-security.html (accessed 2026-07-31)

### Tier 1 — Official AWS Documentation (supporting)
- AWS Config — Operational Best Practices for WAF Security Pillar (SEC BP → Config rule mapping) — https://docs.aws.amazon.com/config/latest/developerguide/operational-best-practices-for-wa-Security-Pillar.html (accessed 2026-07-31)
- IAM Security best practices — https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html (accessed 2026-07-31)
- IAM Prepare for least-privilege permissions — https://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started-reduce-permissions.html (accessed 2026-07-31)
- Security Hub — AWS Foundational Security Best Practices (FSBP) standard — https://docs.aws.amazon.com/securityhub/latest/userguide/fsbp-standard.html (accessed 2026-07-31)
- Security Hub CSPM introduction — https://docs.aws.amazon.com/securityhub/latest/userguide/what-is-securityhub.html (accessed 2026-07-31)

### Tier 2 — Official AWS Blog / Whitepapers
> ⚠️ Source dated 2024-11; latest framework guidance-update announcement.
- Announcing updates to the AWS Well-Architected Framework guidance (Nov 6, 2024 — 43 Security BPs revised across SEC02-SEC04, SEC06-SEC11) — https://aws.amazon.com/blogs/architecture/announcing-updates-to-the-aws-well-architected-framework-guidance-3/ (accessed 2026-07-31)
- AWS Security & Identity reference architectures — https://aws.amazon.com/architecture/security-identity-compliance/ (accessed 2026-07-31)

### Currency notes (post-whitepaper developments — verify before relying)
- AWS re:Invent Dec 2025 announced a major AWS Security Hub update (near real-time risk analytics; unified aggregation/correlation across GuardDuty, Inspector, Macie, and Security Hub CSPM; up to 1 year historical trend data). This post-dates the Nov 2024 whitepaper — confirm control IDs/behavior against current Security Hub docs before implementation. (Source: WebSearch summary, 2026-07-31 — treat as unverified until confirmed on docs.aws.amazon.com.)

---

## Research Gaps / Unverified Items
- Exact wording of SEC 6 and SEC 7–SEC 10 question titles was inferred from the standard WAF framework question set and confirmed structurally via the whitepaper topic pages and the AWS Config SEC→rule mapping (SEC-1 through SEC-5 verified directly; SEC-6 through SEC-11 topic structure verified; precise question-title strings for SEC 6/7/8/9/10 should be reconfirmed against https://docs.aws.amazon.com/wellarchitected/latest/framework/ if used verbatim).
- Some Security Hub FSBP control IDs (e.g., IAM.6, EC2.8, S3.5) are standard/stable but should be reconfirmed against the current FSBP standard page, since the Dec 2025 Security Hub update may have renumbered or added controls.
