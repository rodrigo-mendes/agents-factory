## Metadata
```yaml
Full_Name: "AWS Well-Architected Framework — Security Pillar"
Cloud_Provider: "AWS"
Architecture_Domain: "Well-Architected Framework — Security Pillar"
Target_Edition: "November 6, 2024 (current stable)"
Architecture_Context: "Multi-account production workloads on AWS"
Official_Source_URL: "https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-08-27"
Currency_Threshold: "2027-08-27"
```

## Executive Summary

The AWS Well-Architected Framework Security Pillar defines the ability to protect data, systems, and assets while leveraging cloud technologies to improve an organization's security posture. It is one of the six pillars of the AWS Well-Architected Framework and serves as the canonical reference for security architecture decisions on AWS. The pillar organizes guidance into seven best-practice areas: Security foundations, Identity and access management, Detection, Infrastructure protection, Data protection, Incident response, and Application security. Each area is expressed as a set of best-practice questions (SEC-BP IDs) with risk-rated findings that map directly to architecture decisions.

The November 6, 2024 edition is the current stable version (verified against the official document's stated publication date on 2026-08-27). Sources are flagged as older than 12 months relative to the research date but are retained per Version Absolutism — the edition has not been superseded by a newer stable release. There are no retired services in this edition; the principal additions over prior releases are the formalization of Resource Control Policies (RCPs) alongside Service Control Policies (SCPs) for restricting resource-level access from external principals, and the expanded guidance on EKS Pod Identity for workload credential assignment.

The three most critical guardrails for multi-account production workloads on AWS are: (1) isolate workloads into separate accounts under AWS Organizations to limit blast radius (SEC01-BP01); (2) eliminate long-term static credentials for both human users and workloads — use IAM Identity Center with federated identity for humans and IAM roles for machines (SEC02-BP04 / SEC03 series); and (3) enable organization-wide continuous detection via CloudTrail org trail, GuardDuty, Security Hub, and AWS Config before any workload goes to production (SEC04 series).

## Framework Pillars

> Target Edition: **AWS Well-Architected Security Pillar — November 6, 2024 (current stable as of 2026-08-27)**. No 2025/2026 edition has superseded this release. Per Version Absolutism, all guidance below is pinned to this edition.

### Security Design Principles (7)

The Security Pillar defines seven design principles. These are the evaluative lens for every Always-Do / Never-Do decision in this document.

| # | Principle | Definition (per Nov 6, 2024 edition) |
|---|-----------|--------------------------------------|
| 1 | **Implement a strong identity foundation** | Apply least privilege and separation of duties with appropriate authorization for each interaction; centralize identity management; eliminate reliance on long-term static credentials. |
| 2 | **Maintain traceability** | Monitor, alert, and audit actions and changes in real time; integrate log and metric collection with systems to automatically investigate and act. |
| 3 | **Apply security at all layers** | Defense in depth with multiple controls at every layer — network edge, VPC, load balancing, every instance/compute service, OS, application, and code. |
| 4 | **Automate security best practices** | Software-based security mechanisms defined and managed as code in version-controlled templates to scale securely and cost-effectively. |
| 5 | **Protect data in transit and at rest** | Classify data by sensitivity; apply encryption, tokenization, and access control appropriately. |
| 6 | **Keep people away from data** | Use mechanisms and tools to reduce/eliminate direct access or manual processing, reducing mishandling and human error. |
| 7 | **Prepare for security events** | Have incident management and investigation policy/processes aligned to org requirements; run response simulations; use automation to speed detection, investigation, and recovery. |

Source: Security foundations — Design principles, https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/security.html (accessed 2026-08-27) [✓✓ Triangulated | Security Pillar security.html + Well-Architected Framework welcome.html]

### Best-Practice Areas (7)

Security in the cloud is composed of seven areas, each expressed as risk-rated SEC-BP questions.

| Area | SEC IDs | Focus | Primary AWS Services |
|------|---------|-------|----------------------|
| **Security foundations** | SEC01 | Account/OU separation, guardrails, governance | AWS Organizations, Control Tower, SCPs, RCPs |
| **Identity and access management** | SEC02–SEC03 | Human + machine identities, permissions management | IAM Identity Center, IAM roles, STS, IAM Access Analyzer |
| **Detection** | SEC04 | Logging, threat detection, finding correlation, automated response | CloudTrail, GuardDuty, Security Hub, AWS Config |
| **Infrastructure protection** | SEC05–SEC06 | Protecting networks and compute (defense in depth) | VPC, Security Groups, Network Firewall, AWS WAF, Shield, Systems Manager |
| **Data protection** | SEC07–SEC09 | Classification, encryption at rest and in transit | KMS, S3, EBS, RDS, ACM, Macie |
| **Incident response** | SEC10 | Preparation, containment, forensics, simulation | Security Hub, Detective, Systems Manager, CloudTrail |
| **Application security** | SEC11 | Secure SDLC, pipeline security, dependency management | Inspector, CodeGuru, CodePipeline, Amazon Q Developer |

> Assessment questions per area are risk-rated (High / Medium risk). Use the AWS Well-Architected Tool with the Security Pillar lens to score each SEC-BP against a workload.

Source: Security foundations — Definition, https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/security.html (accessed 2026-08-27)

## Cloud Architecture Glossary

```
Term: Service Control Policy (SCP)
Definition: An AWS Organizations policy type that caps the maximum available permissions for all principals (IAM users and roles) in member accounts. SCPs do not grant permissions — they set guardrails. Effective permissions are the intersection of SCPs and identity-based/resource-based policies.
Provider Docs Section: AWS Organizations — Service Control Policies; Security Pillar SEC01-BP01
Architect Usage: Attach SCPs to OUs to enforce org-wide guardrails (e.g., deny disabling CloudTrail, restrict to approved regions). Never rely on SCPs to grant access.
Common Confusion: SCPs are confused with IAM permission boundaries. SCPs apply to entire accounts/OUs; permission boundaries apply to individual IAM principals within one account.
```

```
Term: Resource Control Policy (RCP)
Definition: An AWS Organizations policy type introduced in 2024 that restricts which principals (including external AWS accounts and services) can access resources in member accounts, regardless of the resource's own policy. RCPs enforce a maximum permission boundary on resource access.
Provider Docs Section: AWS Organizations — Resource Control Policies; Security Pillar SEC01-BP01
Architect Usage: Use RCPs to prevent resource data exfiltration by external accounts (e.g., deny S3 GetObject unless the principal is in your organization). Combine with SCPs for layered defense.
Common Confusion: RCPs are confused with S3 bucket policies or VPC endpoint policies. RCPs apply org-wide to all resources of supported types; bucket policies apply per bucket.
```

```
Term: IAM Identity Center (formerly AWS SSO)
Definition: The AWS service that centralizes workforce identity management and provides federated single sign-on to multiple AWS accounts and applications. It integrates with external identity providers (SAML/OIDC) or uses a native identity store, and vends short-lived STS credentials via permission sets.
Provider Docs Section: AWS IAM Identity Center User Guide; Security Pillar SEC02-BP04
Architect Usage: Route all human access through IAM Identity Center permission sets mapped to IAM roles. Never provision per-user IAM users with permanent credentials.
Common Confusion: Confused with Amazon Cognito (customer identity) or IAM federation via `AssumeRoleWithSAML` directly. IAM Identity Center is the recommended centralized workforce-identity plane.
```

```
Term: Permission Set (IAM Identity Center)
Definition: A named collection of IAM policies (AWS managed, customer managed, or inline) defined in IAM Identity Center that is provisioned as an IAM role into assigned accounts. Users authenticate once and then assume the role corresponding to their assigned permission set.
Provider Docs Section: IAM Identity Center — Permission Sets
Architect Usage: Design permission sets per job function at least-privilege; one permission set may be assigned to multiple accounts. Avoid creating monolithic admin permission sets.
Common Confusion: Confused with IAM roles directly. Permission sets are blueprints provisioned by IAM Identity Center as IAM roles; they are not IAM roles themselves until provisioned.
```

```
Term: IAM Roles Anywhere
Definition: An AWS service that allows workloads running outside AWS (on-premises, other clouds) to obtain temporary AWS credentials using X.509 certificates issued by a trusted certificate authority registered as a Trust Anchor.
Provider Docs Section: IAM Roles Anywhere User Guide; Security Pillar SEC03 series
Architect Usage: Use for on-premises CI/CD pipelines, external automation, or hybrid workloads that need AWS API access without long-term IAM access keys.
Common Confusion: Confused with OIDC-based federation (e.g., GitHub Actions OIDC). Roles Anywhere uses X.509 PKI; OIDC federation uses JWT tokens. Both eliminate long-term keys.
```

```
Term: EKS Pod Identity
Definition: An AWS EKS feature that associates IAM roles with Kubernetes service accounts at the pod level, using an EKS-managed agent to vend short-lived STS credentials to pods. It supersedes the older IRSA (IAM Roles for Service Accounts) pattern in new deployments.
Provider Docs Section: Amazon EKS User Guide — Pod Identity; Security Pillar SEC03 series
Architect Usage: Assign one least-privilege IAM role per Kubernetes workload via Pod Identity. Avoids node-level IAM roles with overly broad permissions shared across all pods.
Common Confusion: Confused with EC2 instance profiles (node-level) or IRSA (annotation-based). Pod Identity is the newer, simpler mechanism requiring the EKS Pod Identity Agent add-on.
```

```
Term: AWS Control Tower
Definition: An AWS service that provides a pre-configured landing zone (multi-account structure, baseline SCPs, centralized logging, and guardrails) and an Account Factory for vending new accounts with baseline controls already applied.
Provider Docs Section: AWS Control Tower User Guide; Security Pillar SEC01-BP01
Architect Usage: Use Control Tower for new organizations wanting an opinionated, governed starting point. Evaluate DIY Organizations + SCPs only when compliance or customization requirements exceed Control Tower's constraints.
Common Confusion: Confused with AWS Organizations. Control Tower uses Organizations as its underlying mechanism but adds an opinionated OU structure, mandatory guardrails, and Account Factory on top.
```

```
Term: AWS Security Hub
Definition: A cloud security posture management (CSPM) service that aggregates, normalizes, and prioritizes security findings from AWS services (GuardDuty, Config, IAM Access Analyzer, Inspector, Macie) and third-party integrations. It evaluates resources against security standards (AWS Foundational Security Best Practices, CIS AWS Foundations, PCI-DSS).
Provider Docs Section: AWS Security Hub User Guide; Security Pillar SEC04-BP03
Architect Usage: Enable Security Hub org-wide with a designated administrator account. Use the AWS Foundational Security Best Practices standard as the baseline; review the security score continuously.
Common Confusion: Confused with Amazon GuardDuty. GuardDuty is a threat-detection service (anomaly/ML-based); Security Hub is an aggregation and compliance posture layer that ingests GuardDuty findings alongside others.
```

```
Term: AWS Config
Definition: A service that continuously records AWS resource configurations and evaluates them against desired-state rules (managed rules or custom Lambda rules). It provides a configuration history and compliance timeline.
Provider Docs Section: AWS Config Developer Guide; Security Pillar SEC04-BP01
Architect Usage: Enable Config with a Config aggregator in the management/security account to get an org-wide configuration view. Use managed rules to detect encryption, logging, and access control drift.
Common Confusion: Confused with AWS CloudTrail. CloudTrail records API calls (who did what, when); Config records the resulting resource state (what a resource looks like and how it changed over time).
```

```
Term: Amazon GuardDuty
Definition: A managed threat-detection service that continuously analyzes AWS CloudTrail management events, CloudTrail S3 data events, VPC Flow Logs, DNS logs, EKS audit logs, and other sources using ML models and threat-intelligence feeds to identify malicious or unauthorized behavior.
Provider Docs Section: Amazon GuardDuty User Guide; Security Pillar SEC04-BP01
Architect Usage: Enable GuardDuty at the organization level with a designated administrator account. Do not disable it per-account; use suppression rules for known-safe findings rather than disabling the service.
Common Confusion: Confused with AWS Security Hub (aggregation layer) or AWS WAF (application-layer protection). GuardDuty is passive threat detection; it does not block traffic or API calls.
```

```
Term: IAM Access Analyzer
Definition: An AWS service that uses automated reasoning to identify resources shared with external principals (external access analyzer) and IAM policies that grant more access than was used (unused-access analyzer). It also validates IAM policies against 100+ policy checks before deployment.
Provider Docs Section: IAM Access Analyzer User Guide; Security Pillar SEC02/SEC03 series
Architect Usage: Enable in every account + org-level analyzer. Use policy-generation mode on existing roles (fed from CloudTrail) to produce least-privilege policies. Integrate policy validation into CI/CD.
Common Confusion: Confused with IAM policy simulator. Simulator tests a specific principal + action + resource; Access Analyzer reasons across all principals and surfaces unintended access automatically.
```

```
Term: Organizational Trail (CloudTrail)
Definition: A CloudTrail trail configured from the management account that automatically applies to all current and future member accounts in the AWS Organization, writing logs to a centralized S3 bucket in a log-archive account.
Provider Docs Section: AWS CloudTrail User Guide — Organizational Trails; Security Pillar SEC04-BP01
Architect Usage: Create one organizational trail as the authoritative API audit log. Member accounts must not be allowed to disable it (enforce via SCP).
Common Confusion: Confused with per-account trails. Per-account trails miss accounts created after the trail was configured; organizational trails are the correct pattern for full org coverage.
```

## Architecture Guardrails

### Mandatory Patterns

**SEC-AD-1 — Separate workloads via multi-account structure**
- Pillar Alignment: Security foundations (SEC01-BP01)
- Why: AWS accounts are a hard isolation boundary for security, billing, and access. Placing unrelated workloads in one account widens the blast radius of any compromise. Risk if not established: High.
- AWS Services: AWS Organizations, AWS Control Tower (landing zone + Account Factory), SCPs, RCPs, AWS Config, CloudFormation StackSets
- Architecture Decision: Design an OU hierarchy aligned to data sensitivity, workload type, and environment (e.g., Security OU, Workload OU per team, Sandbox OU). Apply SCP guardrails at the OU level so all accounts beneath inherit them. Use Control Tower Account Factory to vend new accounts with baseline controls already applied. Apply RCPs to restrict resource access from external principals org-wide.
- Verification: `aws organizations list-accounts` / `aws organizations list-policies --filter SERVICE_CONTROL_POLICY`; Control Tower mandatory-controls dashboard; AWS Config aggregator compliance view; Security Hub AWS Foundational Security Best Practices score.
- Trade-offs: More accounts increases governance overhead; requires centralized tooling (Control Tower or DIY pipeline) and cross-account IAM role design from day one.
- Source: SEC01-BP01 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_securely_operate_multi_accounts.html

**SEC-AD-2 — Federated human access with temporary credentials via IAM Identity Center**
- Pillar Alignment: Identity and access management (SEC02-BP04)
- Why: Human users with permanent IAM access keys or per-user IAM console passwords violate "Implement a strong identity foundation." Temporary STS credentials expire automatically, reducing the window of exposure from leaked credentials.
- AWS Services: AWS IAM Identity Center, external IdP (SAML/OIDC), AWS STS, IAM roles
- Architecture Decision: Route all human access through IAM Identity Center. Connect to corporate IdP (Okta, Entra ID) or use the native identity store. Define permission sets per job function (least privilege). Users authenticate once and receive short-lived STS credentials for the assigned permission set in target accounts. No per-user IAM users with permanent access keys.
- Verification: IAM Credential Report (`aws iam generate-credential-report` then `aws iam get-credential-report`) — confirm no active human access keys. CloudTrail `AssumeRole` / `AssumeRoleWithSAML` events confirm federated flow is in use.
- Trade-offs: Requires IdP integration and IAM Identity Center configuration. Some legacy CLI tooling may need updated credential helpers. Documented exceptions required for service accounts that cannot use federation.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html [✓✓ Triangulated | IAM best practices + Security Pillar SEC02 identity page]

**SEC-AD-3 — Workloads use IAM roles (not embedded keys)**
- Pillar Alignment: Identity and access management (SEC03 series)
- Why: Embedding IAM access keys in application code or configuration files creates persistent secrets that are difficult to rotate and easily leaked via source control or deployment artifacts. IAM roles vend short-lived credentials automatically via instance metadata or container credential endpoints.
- AWS Services: IAM roles, EC2 instance profiles, Lambda execution roles, ECS task roles, EKS Pod Identity, IAM Roles Anywhere (X.509 for external workloads)
- Architecture Decision: Attach a least-privilege IAM role to each compute resource at launch time. The AWS SDK auto-discovers credentials via the credential provider chain — no key management code required. For Kubernetes workloads, use EKS Pod Identity (one role per service account). For on-premises or external workloads, use IAM Roles Anywhere with X.509 certificates.
- Verification: IAM Access Analyzer unused-access findings; IAM credential report (confirm no embedded keys); `aws iam get-instance-profile` for EC2; EKS Pod Identity add-on status in the cluster.
- Trade-offs: External and on-premises workloads require IAM Roles Anywhere setup including a Private CA or trusted third-party CA. Migration from embedded keys requires application changes.
- Source: IAM best practices + Security Pillar permissions management [✓✓ Triangulated]

**SEC-AD-4 — Phishing-resistant MFA for all IAM/root users**
- Pillar Alignment: Identity and access management (SEC02 / Design Principle 1)
- Why: Phishing attacks targeting TOTP codes circumvent software MFA. FIDO2/WebAuthn passkeys and hardware security keys are phishing-resistant because authentication is bound to the origin domain.
- AWS Services: IAM MFA, FIDO2 passkeys / hardware security keys (YubiKey etc.), IAM Identity Center MFA enforcement
- Architecture Decision: Enforce phishing-resistant MFA (passkeys or security keys) for all human access — both IAM users (if any remain) and IAM Identity Center users. Enable MFA on the root user of every account. Block root user API access keys entirely.
- Verification: IAM credential report `mfa_active` column; AWS Config managed rules `mfa-enabled-for-iam-console-access` and `root-account-mfa-enabled`; Security Hub finding for root MFA.
- Trade-offs: Hardware token management and recovery processes are operationally complex at scale. Lost authenticator recovery must be documented and tested before incidents occur.
- Source: IAM best practices + Security Pillar design principle 1 [✓✓ Triangulated]

**SEC-AD-5 — Encryption at rest with AWS KMS**
- Pillar Alignment: Data protection (SEC08-BP01 / SEC08-BP02)
- Why: "Protect data in transit and at rest" requires classifying data by sensitivity and encrypting accordingly. Unencrypted snapshots or volumes expose data if media is mishandled.
- AWS Services: AWS KMS, Amazon S3 (default encryption), Amazon EBS (encryption), Amazon RDS (encryption), Amazon Macie
- Architecture Decision: Classify data assets by sensitivity (public / internal / confidential / restricted). Enable encryption at rest for all sensitive stores using KMS customer-managed keys (CMKs) for regulated/confidential data. Manage keys centrally (SEC08-BP01). Audit all key use via CloudTrail → CloudWatch Logs Insights. Use Macie to discover unclassified sensitive data in S3.
- Verification: AWS Config rules `encrypted-volumes`, `s3-bucket-server-side-encryption-enabled`, `rds-storage-encrypted`; KMS CloudTrail events for key usage; Macie findings dashboard.
- Trade-offs: KMS API request costs and per-region throttling limits require capacity planning. CMK lifecycle (rotation, cross-account grants, key policy management) adds operational overhead versus AWS-managed keys.
- Source: SEC08-BP01/02 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html [✓✓ Triangulated]

**SEC-AD-6 — Continuous detection: logging + threat detection**
- Pillar Alignment: Detection (SEC04-BP01 through SEC04-BP04)
- Why: "Maintain traceability" requires real-time monitoring, alerting, and audit. Without continuous detection, breaches go undetected and forensic investigation is impossible.
- AWS Services: AWS CloudTrail (organizational trail), Amazon GuardDuty (org-wide), AWS Security Hub, AWS Config, Amazon CloudWatch
- Architecture Decision: SEC04-BP01 — configure CloudTrail organizational trail to centralized S3 in Log Archive account (management events + S3 data events for sensitive buckets). SEC04-BP02 — centralize logs. SEC04-BP03 — correlate and enrich via Security Hub standards. SEC04-BP04 — automate remediation using EventBridge rules → Lambda or SSM Automation for common findings.
- Verification: `aws cloudtrail describe-trails` (confirm `IsOrganizationTrail: true`); GuardDuty console — organization-wide enabled status; Security Hub standards compliance score; Config recorder and delivery channel status.
- Trade-offs: Log storage, GuardDuty, and Security Hub generate ongoing costs that scale with account/resource count. Alert-volume tuning is required to avoid alert fatigue; start with High/Critical severity only.
- Source: SEC04 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html [✓✓ Triangulated]

**SEC-AD-7 — Defense-in-depth infrastructure protection (network + compute)**
- Pillar Alignment: Infrastructure protection (SEC05 protecting networks / SEC06 protecting compute)
- Why: "Apply security at all layers" requires controls at the network edge, VPC, load balancer, instance, OS, and application. A single perimeter control is insufficient — trust boundaries must be enforced at every layer.
- AWS Services: Amazon VPC (private subnets, NACLs, Security Groups), AWS Network Firewall, AWS WAF, AWS Shield (Standard/Advanced), VPC endpoints/PrivateLink, AWS Systems Manager (Patch Manager, Session Manager, Fleet Manager), Amazon Inspector
- Architecture Decision: SEC05 — create layered network trust boundaries: workloads in private subnets, controlled ingress via ALB + AWS WAF, egress via NAT Gateway or VPC endpoints, and Security Groups as the primary stateful control (NACLs as coarse secondary). Front internet-facing endpoints with AWS WAF (managed rule groups) and Shield for DDoS. SEC06 — reduce compute attack surface: automated patching via Systems Manager Patch Manager, no SSH/RDP (use Session Manager), immutable AMIs from a hardened pipeline, and continuous vulnerability scanning via Amazon Inspector.
- Verification: `aws ec2 describe-security-groups` (no 0.0.0.0/0 on management ports); AWS Config rules `restricted-ssh`, `vpc-sg-open-only-to-authorized-ports`; Inspector coverage report; Systems Manager patch compliance dashboard; WAF WebACL association on ALB/CloudFront.
- Trade-offs: Layered controls add configuration complexity and can introduce connectivity troubleshooting overhead. Network Firewall and Shield Advanced carry meaningful cost — reserve Shield Advanced for high-value internet-facing workloads.
- Source: SEC05/SEC06 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html

**SEC-AD-8 — Secure the software delivery lifecycle (application security)**
- Pillar Alignment: Application security (SEC11-BP01 through SEC11-BP08)
- Why: "Automate security best practices" applied to the SDLC: the cost and complexity of resolving defects is lowest early in the lifecycle. Threat modeling in design and automated testing in the pipeline prevent vulnerabilities from reaching production.
- AWS Services: Amazon Inspector (SCA/CVE), Amazon CodeGuru / Amazon Q Developer (code review), AWS CodePipeline / CodeBuild (programmatic deployment), AWS CodeArtifact (centralized dependencies), AWS Signer (artifact signing)
- Architecture Decision: SEC11 covers four areas — organization & culture, security *of* the pipeline, security *in* the pipeline, and dependency management. Train builders (SEC11-BP01); automate SAST/SCA/secret-scanning throughout the lifecycle (SEC11-BP02); perform regular penetration testing (SEC11-BP03); conduct code reviews (SEC11-BP04); centralize packages/dependencies via CodeArtifact (SEC11-BP05); deploy software programmatically only — no manual production changes (SEC11-BP06); regularly assess pipeline security properties (SEC11-BP07); embed security ownership in workload teams (SEC11-BP08).
- Verification: Inspector findings in Security Hub; CodePipeline stage with a mandatory security-scan action; CodeArtifact as the only configured package source; branch-protection + required-review settings; evidence of threat models per workload.
- Trade-offs: Mature AppSec automation requires investment in pipeline engineering and developer enablement. Gating deploys on scan results can slow delivery until false positives are tuned.
- Source: SEC11 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/application-security.html

### Architectural Decisions

**Decision A — Multi-account governance model**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Managed landing zone | AWS Control Tower | Speed, built-in guardrails, Account Factory automation | Flexibility / customization ceiling | New or standard orgs wanting a fast best-practice baseline |
  | DIY org + policies | AWS Organizations + SCPs/RCPs | Full control over OU design and policy logic | Build and maintenance effort | Highly specific governance requirements or existing landing zone |

- Cost Profile: Control Tower has no additional service charge beyond the underlying AWS services it manages; DIY incurs engineering time cost.
- Lock-in Assessment: Both options use AWS Organizations as the underlying primitive; migration between them is possible but requires careful SCP/guardrail reconciliation.
- Architect Instruction: "Ask whether the organization has existing governance tooling or a landing zone already deployed before recommending Control Tower — retrofitting Control Tower onto a mature DIY org is high-effort."
- Source: SEC01-BP01 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_securely_operate_multi_accounts.html

**Decision B — Identity source for IAM Identity Center**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Native identity store | IAM Identity Center identity store | Simplicity, no external IdP dependency | Enterprise directory integration / user lifecycle automation | Small or greenfield organization with no corporate IdP |
  | External IdP federation | IAM Identity Center + Okta / Microsoft Entra ID | Single source of truth, existing user lifecycle management | Integration setup and ongoing IdP maintenance | Existing enterprise workforce directory |

- Cost Profile: IAM Identity Center has no additional charge; cost is the IdP license (external IdP option).
- Lock-in Assessment: External IdP federation is portable — switching to a different IdP requires only reconfiguring the SAML/OIDC connection, not re-provisioning AWS users.
- Architect Instruction: "Ask whether a corporate identity provider (Okta, Entra ID, Ping) already exists for the organization before recommending the native identity store."
- Source: IAM best practices + SEC02-BP04

**Decision C — Encryption key ownership**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | AWS-managed keys | AWS KMS AWS-managed | Zero key administration overhead | Granular key policy control; cross-account grants | Low compliance sensitivity; no regulatory key-custody mandate |
  | Customer-managed keys (CMK) | AWS KMS CMK | Granular key policy, audit, rotation control | Key lifecycle admin overhead | Regulated data (PCI, HIPAA, FedRAMP) or cross-account access |
  | Imported key material / external key store | AWS KMS external key store | Full key custody outside AWS | Highest operational burden; availability dependency on external HSM | Strict key-custody mandates requiring off-AWS storage |

- Cost Profile: AWS-managed keys have no per-key charge (API calls billed); CMKs incur a per-key monthly charge plus API call charges; external key stores add HSM infrastructure cost.
- Lock-in Assessment: CMKs are AWS-regional; data encrypted under a CMK cannot be decrypted outside that region without cross-region key replication configuration.
- Architect Instruction: "Ask the data classification for each data store before recommending key type — only regulated or restricted data requires CMKs."
- Source: SEC08-BP01 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html

### Anti-Patterns

**SEC-ND-1 — Long-term static access keys for humans**
- Risk Level: CRITICAL
- Why: Violates "Implement a strong identity foundation." Leaked long-term keys provide persistent unauthorized access with no automatic expiry. Human access keys in version control or CI secrets are a leading cause of cloud breaches.
- ❌ Wrong: An IAM user `deploy-admin` with a permanent access key pair stored in a developer's `~/.aws/credentials` and copied into a CI secret.
- ✅ Correct: IAM Identity Center federated sign-in → STS temporary credentials via assumed IAM roles. Keys expire automatically (1–12 hours); no rotation required. For CI, use GitHub Actions OIDC → IAM role.
- Detection: IAM credential report `access_key_1_active=true` on human user entries; IAM Access Analyzer unused-access findings for active keys not used in 90+ days.
- Impact: Data breach; persistent unauthorized access post-credential exposure.
- Source: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

**SEC-ND-2 — Root user for daily operations / no root MFA**
- Risk Level: CRITICAL
- Why: Root user credentials cannot be restricted by SCPs — compromise equals total account takeover. Root access keys amplify the risk by enabling programmatic full-access without console login.
- ❌ Wrong: Root user with an active access key used by a nightly backup script, no MFA enabled.
- ✅ Correct: Lock root credentials in a vault; enable phishing-resistant MFA on root; delete root access keys; run the backup script under a least-privilege IAM role. Operate exclusively via IAM Identity Center roles for all daily tasks.
- Detection: AWS Config rules `root-account-mfa-enabled`, `iam-root-access-key-check`; CloudTrail events for `userIdentity.type: Root`; Security Hub finding for root MFA absence.
- Impact: Total account takeover; all resources and data in the account fully exposed.
- Source: IAM best practices https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

**SEC-ND-3 — Multiple unrelated workloads in one account**
- Risk Level: CRITICAL
- Why: Violates SEC01-BP01 multi-account isolation principle. One compromised workload (e.g., a development app) can access production data if they share an account. Risk classification: High.
- ❌ Wrong: `prod-api`, `dev-api`, and `analytics` all deployed in a single AWS account `123456789012`, sharing IAM roles and VPCs.
- ✅ Correct: Separate accounts per workload/environment under dedicated OUs (Prod OU, Non-Prod OU). Apply SCP guardrails at the OU level so isolation is structural, not policy-only.
- Detection: AWS Organizations account/OU review; Config aggregator tagging compliance; absence of environment-specific accounts.
- Impact: Wide blast radius — compromise of one workload exposes all co-resident workloads.
- Source: SEC01-BP01 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_securely_operate_multi_accounts.html

**SEC-ND-4 — Overly broad ("*") permissions**
- Risk Level: HIGH
- Why: Violates least-privilege principle (Design Principle 1). Wildcard actions or resources allow privilege escalation and lateral movement if the identity's credentials are compromised.
- ❌ Wrong: An IAM policy with `{"Effect":"Allow","Action":"*","Resource":"*"}` attached to an application role.
- ✅ Correct: IAM Access Analyzer policy generation from CloudTrail activity to produce observed-usage-based least-privilege policies scoped to specific actions and resource ARNs. IAM Access Analyzer policy validation (100+ checks) integrated into CI/CD pipelines.
- Detection: IAM Access Analyzer policy validation findings; unused-access findings for permissions granted but never used in 90 days.
- Impact: Privilege escalation; lateral movement across services and accounts.
- Source: IAM best practices https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

**SEC-ND-5 — No logging / broken traceability**
- Risk Level: CRITICAL
- Why: Violates "Maintain traceability." Without an audit trail, breaches are undetected, forensic investigation is impossible, and compliance requirements (SOC2, ISO 27001, PCI-DSS) cannot be demonstrated.
- ❌ Wrong: CloudTrail disabled in member accounts, or a per-account trail that misses newly created accounts; no GuardDuty.
- ✅ Correct: Organizational CloudTrail trail → centralized S3 in Log Archive account (Object Lock); GuardDuty org-wide; Security Hub + AWS Config; SEC04-BP02 centralized log store pattern. Deny disabling CloudTrail via SCP.
- Detection: `aws cloudtrail describe-trails` — confirm `IsOrganizationTrail: true` and delivery to Log Archive S3; GuardDuty and Security Hub console enabled status; Config recorder running.
- Impact: Undetected breach; forensic investigation impossible; compliance audit failure.
- Source: SEC04 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html

**SEC-ND-6 — Unencrypted data at rest / unmonitored key use**
- Risk Level: HIGH
- Why: Violates "Protect data in transit and at rest." Unencrypted EBS snapshots, S3 objects, or RDS instances expose data if media or snapshots are accessed outside their intended context.
- ❌ Wrong: An S3 bucket with default encryption disabled and an unencrypted RDS instance holding customer PII.
- ✅ Correct: Enforce KMS encryption on all sensitive stores (S3 default encryption, EBS encryption-by-default, RDS storage encryption). Audit key use via CloudTrail + CloudWatch Logs Insights. Use Macie to discover unclassified sensitive data in S3.
- Detection: AWS Config rules `encrypted-volumes`, `s3-bucket-server-side-encryption-enabled`, `rds-storage-encrypted`; Macie findings for sensitive data in unclassified buckets.
- Impact: Data exposure on media, snapshot, or object theft; compliance violation (HIPAA, PCI-DSS, GDPR).
- Source: SEC08 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html

**SEC-ND-7 — Public internet exposure without WAF/DDoS protection**
- Risk Level: HIGH
- Why: Violates "Apply security at all layers" (SEC05 infrastructure protection). An internet-facing API or web app without edge protection is exposed to L7 attacks (SQLi, XSS, bot abuse) and volumetric DDoS.
- ❌ Wrong: An ALB directly exposed to `0.0.0.0/0` on port 443 with no AWS WAF WebACL and no Shield, backing a production API.
- ✅ Correct: Front the ALB (or CloudFront) with an AWS WAF WebACL using AWS Managed Rules (Core rule set, SQLi, IP reputation, rate-based rules); enable AWS Shield (Advanced for high-value targets). Terminate at CloudFront to reduce origin exposure.
- Detection: Check WebACL association on ALB/CloudFront (`aws wafv2 list-resources-for-web-acl`); AWS Config rule for WAF association; Shield protection status.
- Impact: Service outage (DDoS), data breach (L7 injection), cost overrun (bot/scraper traffic).
- Source: SEC05 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html

**SEC-ND-8 — Security groups open to 0.0.0.0/0 on management ports**
- Risk Level: HIGH
- Why: Violates SEC05 (protecting networks) and SEC06 (protecting compute). Exposing SSH (22) or RDP (3389) to the internet invites brute-force and exploitation of unpatched instances.
- ❌ Wrong: A Security Group with inbound rule `tcp/22` from `0.0.0.0/0` on production EC2 instances.
- ✅ Correct: Remove all inbound rules on management ports; use AWS Systems Manager Session Manager for shell access (no open ports, full CloudTrail audit). If direct access is unavoidable, restrict to a bastion in a private subnet reachable only via Session Manager or VPN.
- Detection: AWS Config rules `restricted-ssh`, `restricted-common-ports`; `aws ec2 describe-security-groups` for `0.0.0.0/0` on ports 22/3389; Security Hub FSBP finding `EC2.13`/`EC2.14`.
- Impact: Instance compromise; lateral movement; cryptomining or ransomware deployment.
- Source: SEC05/SEC06 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html

## Cloud-Native Design Patterns

**Centralized Log Archive with Immutable Retention**
- Category: Security / Compliance
- Problem: Individual account CloudTrail logs can be deleted or modified by account-level admin users, destroying the forensic trail.
- Solution on AWS: Create a dedicated Log Archive account in the Security OU. Organizational CloudTrail trail delivers logs to an S3 bucket in the Log Archive account with Object Lock (WORM) enabled. Member accounts have no write or delete access to the bucket. Log Archive account has no workloads — access is tightly restricted to the security operations team.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Integrity | Logs immutable — cannot be deleted by compromised member account admin | Bucket and Object Lock configuration complexity |
  | Coverage | Organizational trail auto-covers future accounts | Single trail → single S3 destination becomes a high-value target (harden bucket policy) |
  | Cost | Centralized storage enables lifecycle policies for archival to S3 Glacier | Storage cost grows linearly with account/API volume |

- Source: SEC04-BP02 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html

**Automated Remediation Pipeline for Security Findings**
- Category: Security / Automation
- Problem: Manual remediation of Security Hub and GuardDuty findings introduces response latency, increases exposure windows, and does not scale across many accounts.
- Solution on AWS: Security Hub findings → EventBridge rule (filter by severity + finding type) → Lambda function or SSM Automation runbook → remediation action (e.g., revoke overly permissive security group rule, quarantine IAM key, isolate EC2 instance). Audit remediation actions via CloudTrail.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Speed | Automated response in seconds vs hours | Risk of false-positive remediation disrupting legitimate workloads — requires tuning |
  | Coverage | Scales across org without proportional staffing | Cross-account Lambda/SSM role design complexity |
  | Auditability | All remediation actions recorded in CloudTrail | Lambda code must be version-controlled and tested |

- Source: SEC04-BP04 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html

## Security Architecture

**Identity and Access Management**
- AWS Services: AWS IAM, AWS IAM Identity Center, AWS STS, AWS Organizations (SCPs + RCPs)
- Architecture: Centralize identity in IAM Identity Center connected to corporate IdP → federated SSO to AWS accounts → STS vends temporary credentials scoped to least-privilege permission sets (IAM roles). SCPs attached at OU level cap the maximum permissions available to all principals in member accounts — no SCP exception can exceed the SCP boundary. RCPs restrict which external principals can access resources in member accounts, blocking data exfiltration paths even if a member account's resource policy is misconfigured.
- Compliance Alignment: Well-Architected SEC01/SEC02/SEC03; CIS AWS Foundations Benchmark
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html

**Infrastructure Protection (Network + Compute)**
- AWS Services: Amazon VPC (private subnets, NACLs, Security Groups), AWS Network Firewall, AWS WAF, AWS Shield, VPC endpoints/PrivateLink, AWS Systems Manager (Patch Manager, Session Manager), Amazon Inspector
- Architecture: Establish layered trust boundaries (network and account). Internet ingress terminates at CloudFront + AWS WAF, then ALB in a public subnet; application and data tiers live in private subnets with egress via NAT Gateway or VPC endpoints. Security Groups are the primary stateful control; NACLs provide coarse subnet-level defense. Shield protects against DDoS. Compute is hardened via immutable AMIs, automated patching (Patch Manager), no inbound management ports (Session Manager for access), and continuous CVE scanning (Inspector).
- Compliance Alignment: Well-Architected SEC05/SEC06; CIS AWS Foundations Benchmark; PCI-DSS network segmentation requirements
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html

**Data Protection**
- AWS Services: AWS KMS, Amazon S3 (default encryption + versioning + Object Lock), Amazon EBS (encryption), Amazon RDS (encryption), Amazon Macie, AWS Certificate Manager (TLS)
- Architecture: Classify data assets by sensitivity → enable KMS encryption at rest for all stores containing internal/confidential/restricted data (CMKs for regulated data, AWS-managed for lower tiers) → enforce TLS in transit using ACM certificates and policy conditions (`aws:SecureTransport: true`) → audit all KMS key use via CloudTrail → run Macie scans on S3 to detect unclassified sensitive data (PII, credentials).
- Compliance Alignment: Well-Architected SEC07/SEC08/SEC09; PCI-DSS encryption requirements; HIPAA encryption safeguards; GDPR pseudonymization/encryption requirements
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/data-protection.html

**Application Security**
- AWS Services: Amazon Inspector, Amazon CodeGuru / Amazon Q Developer, AWS CodePipeline / CodeBuild, AWS CodeArtifact, AWS Signer
- Architecture: Embed security across the SDLC per SEC11's four areas (organization & culture, security *of* the pipeline, security *in* the pipeline, dependency management). Threat model in design; run SAST/SCA/secret-scanning as mandatory pipeline stages; centralize dependencies in CodeArtifact; deploy only programmatically (no manual production changes); sign artifacts with AWS Signer; scan running workloads and images continuously with Inspector; embed security ownership in workload teams.
- Compliance Alignment: Well-Architected SEC11; SOC 2 CC8 (change management); ISO 27001 A.14 (secure development)
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/application-security.html

**Threat Detection**
- AWS Services: Amazon GuardDuty, AWS Security Hub, AWS Config, AWS CloudTrail, Amazon CloudWatch
- Architecture: GuardDuty (ML-based threat detection across CloudTrail, VPC Flow Logs, DNS, EKS audit logs) + Security Hub (finding aggregation and standards compliance scoring) + AWS Config (resource configuration compliance) + CloudTrail (API audit trail) → all findings and logs centralized to Log Archive account → EventBridge rules filter High/Critical findings → SNS alerts to security team → Lambda or SSM Automation for automated remediation of known-safe-to-automate findings.
- Compliance Alignment: Well-Architected SEC04; SOC 2 CC7 (monitoring); ISO 27001 A.12.4 (logging and monitoring)
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html

## Operational Patterns

**Security Posture Review Cadence**
- RTO/RPO (if applicable): Not applicable (posture review, not a recovery pattern)
- AWS Services: AWS Security Hub, AWS Config, IAM Access Analyzer, Amazon GuardDuty
- Cost Profile: Medium — Security Hub, Config rules, and GuardDuty are per-account per-region charges; cost scales with resource density.
- Automation: Automate Security Hub standards scoring dashboards (weekly digest via EventBridge Scheduler → Lambda → SNS/email). Automate Config rule evaluation on resource change events. Manually review IAM Access Analyzer unused-access findings monthly — remediation decisions require human judgment (which access to revoke).
- Source: SEC04 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html

**Incident Response Preparation**
- RTO/RPO (if applicable): Defined per workload classification; Well-Architected SEC10 recommends pre-defined RTO targets per incident severity.
- AWS Services: AWS Security Hub, Amazon GuardDuty, AWS CloudTrail, Amazon Detective, AWS Systems Manager (Automation runbooks), AWS Lambda
- Cost Profile: Low baseline (runbooks and Detective are pay-per-use); High during active incidents (Detective analysis cost spikes on large investigation graphs).
- Automation: Pre-build SSM Automation runbooks for common containment actions (isolate EC2, revoke IAM key, restrict S3 bucket). Run simulations (GameDays) before incidents occur — SEC10-BP06. Store runbooks in version control; test quarterly.
- Source: SEC10 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/incident-response.html

## Reference Architectures

**Multi-Account Production Workload — Security Baseline**
- Context: Multi-account production workloads on AWS with human and machine identities
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Governance | AWS Control Tower | Landing zone, Account Factory, mandatory guardrails |
  | Governance | AWS Organizations (SCPs + RCPs) | Permission guardrails and resource access restrictions |
  | Identity | IAM Identity Center + external IdP | Federated SSO, temporary credentials for humans |
  | Identity | IAM roles (EC2/Lambda/ECS/EKS Pod Identity) | Workload credentials — no embedded keys |
  | Network | Amazon VPC + Security Groups + AWS WAF + Shield | Layered network defense-in-depth |
  | Compute | Systems Manager (Patch/Session Manager) + Inspector | Hardened, patched, keyless compute access |
  | Detection | CloudTrail organizational trail | API audit log → Log Archive S3 (Object Lock) |
  | Detection | Amazon GuardDuty (org-wide) | ML threat detection |
  | Detection | AWS Security Hub (org-wide) | Finding aggregation, standards scoring |
  | Detection | AWS Config (org aggregator) | Configuration compliance |
  | Data Protection | AWS KMS CMKs | Encryption at rest for regulated data |
  | Data Protection | Amazon Macie | Sensitive data discovery in S3 |
  | Data Protection | AWS Certificate Manager | TLS in transit |
  | AppSec | CodePipeline + Inspector + CodeArtifact | Secure SDLC and dependency management |
  | Response | EventBridge + Lambda/SSM Automation | Automated remediation for High/Critical findings |

- Key Decisions: External IdP vs native IAM Identity Center identity store; CMK vs AWS-managed keys per data classification tier; Control Tower vs DIY Organizations governance model.
- Scaling Path: Start with Control Tower + IAM Identity Center + GuardDuty + CloudTrail (day-one baseline). Add Security Hub standards, Macie, WAF, and automated remediation pipelines as the team matures. Introduce Amazon Detective for deep-dive investigation capability at scale.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/

## Service Equivalence Map

> Included as a decision aid for architects evaluating security-service equivalents across providers. Equivalence does NOT mean feature parity — validate against each provider's current documentation before decisions.

| Security Capability (AWS focus) | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|---|---|---|---|---|
| **Org guardrails** | Organizations SCPs / RCPs | Organization Policies | Management Groups / Azure Policy | Compartment Policies / Security Zones |
| **Landing zone** | Control Tower | Cloud Foundation Toolkit | Azure Landing Zones (CAF) | OCI Landing Zones |
| **Workforce identity / SSO** | IAM Identity Center | Cloud Identity / Workforce Identity | Microsoft Entra ID | IAM Identity Domains |
| **Workload identity** | IAM roles / EKS Pod Identity / Roles Anywhere | Workload Identity Federation | Managed Identities | Instance Principals / Dynamic Groups |
| **Least-privilege analysis** | IAM Access Analyzer | IAM Recommender / Policy Analyzer | Entra Permissions Management | (partial) IAM Policy tooling |
| **Key management** | AWS KMS | Cloud KMS | Key Vault | OCI Vault / Key Management |
| **Secrets management** | Secrets Manager | Secret Manager | Key Vault | OCI Vault |
| **Sensitive-data discovery** | Amazon Macie | Sensitive Data Protection (DLP) | Microsoft Purview | Data Safe |
| **Threat detection** | Amazon GuardDuty | Security Command Center (Threat) | Microsoft Defender for Cloud | Cloud Guard |
| **Posture management (CSPM)** | AWS Security Hub | Security Command Center | Defender for Cloud | Cloud Guard |
| **Config/compliance recording** | AWS Config | Cloud Asset Inventory | Azure Policy / Resource Graph | Cloud Guard / OCI Audit |
| **API audit log** | AWS CloudTrail | Cloud Audit Logs | Azure Activity Log / Monitor | OCI Audit |
| **Web application firewall** | AWS WAF | Cloud Armor | Azure WAF | OCI WAF |
| **DDoS protection** | AWS Shield | Cloud Armor | Azure DDoS Protection | OCI DDoS Protection |
| **Network firewall** | AWS Network Firewall | Cloud NGFW / Firewall | Azure Firewall | Network Firewall |
| **Vulnerability/CVE scanning** | Amazon Inspector | Artifact Analysis / SCC | Defender for Cloud (vuln) | Vulnerability Scanning Service |
| **Private connectivity** | PrivateLink / VPC endpoints | Private Service Connect | Private Link | Service Gateway / Private Endpoints |
| **Keyless shell access** | SSM Session Manager | IAP for TCP | Azure Bastion | OCI Bastion |

> **⚠️ Important**: Service equivalence does NOT mean feature parity. Each service has unique capabilities, limits, pricing models, and regional availability. Always validate against the current provider documentation before architectural decisions.

## Provider Differentiators

**AWS Organizations SCPs + RCPs — Layered Policy Enforcement**: AWS provides both identity-side guardrails (SCPs, which cap what principals can do) and resource-side guardrails (RCPs, which restrict who can access resources). This dual-layer enforcement is unique in its depth and is directly native to the AWS Organizations primitive — no third-party tooling required for org-wide enforcement.

**IAM Access Analyzer — Automated Reasoning for Permissions**: Uses formal automated reasoning (Zelkova) to prove whether a policy can allow access, not just simulate it. Policy validation with 100+ checks and unused-access analysis provide proactive posture hardening that goes beyond generic CSPM rule matching.

**GuardDuty — Purpose-Built Threat Detection at Scale**: GuardDuty ingests multiple native AWS data sources (CloudTrail, VPC Flow Logs, DNS, EKS audit logs, S3 data events, RDS activity) without requiring log export or agent deployment, reducing operational friction versus SIEM-based detection that requires log pipeline management.

## Scenario Coverage

**Standard Case**: Multi-account workload with human and machine identities
- Approach: Control Tower landing zone → IAM Identity Center (federated to corporate IdP) → permission sets mapped to least-privilege IAM roles per job function → IAM roles per compute workload (EC2 instance profile / Lambda execution role / EKS Pod Identity) → GuardDuty + Security Hub org-wide → CloudTrail organizational trail to Log Archive S3 (Object Lock) → KMS CMK encryption for confidential/restricted data → Macie for sensitive-data discovery → AWS WAF + Shield on internet-facing endpoints.
- Key Decisions: External IdP vs native IAM Identity Center identity store; CMK vs AWS-managed keys per data classification; Control Tower vs DIY Organizations governance model.

**Edge Case**: External or on-premises workloads needing AWS access without long-term keys
- Approach: IAM Roles Anywhere with X.509 certificates from a Private CA (AWS Private CA or trusted third-party CA). Register the CA as a Trust Anchor in IAM Roles Anywhere. Workloads use the Roles Anywhere credential helper to exchange X.509 certificates for STS temporary credentials scoped to a least-privilege IAM role. No embedded access keys required.

**Anti-Pattern Case**: Request to use root credentials for automation or embed IAM access keys in application code
- Clarification: Ask why IAM roles cannot be used for the compute resource. If the workload is on-premises or external, ask whether IAM Roles Anywhere (X.509 PKI) or Secrets Manager with automatic rotation is feasible before considering any long-term key exception. If the request is for root credentials specifically, always refuse — document root as reserved for break-glass account-level tasks only and escalate to the security team for review.

## Source Bibliography

All sources are official AWS documentation. The Security Pillar whitepaper's stated publication date is **November 6, 2024** — flagged as >12 months old relative to the research date (2026-08-27) but retained per Version Absolutism as the current stable edition (verified 2026-08-27; no newer edition published).

| # | Source | URL | Accessed | Currency |
|---|--------|-----|----------|----------|
| 1 | Security Pillar — Welcome (publication date verification) | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html | 2026-08-27 | Nov 6, 2024 — ⚠️ >12mo, current stable |
| 2 | Well-Architected Framework — Welcome (six pillars) | https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html | 2026-08-27 | current stable |
| 3 | Security foundations — Design principles + 7 areas | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/security.html | 2026-08-27 | Nov 6, 2024 — ⚠️ >12mo |
| 4 | SEC01 — Operate workloads securely (multi-account) | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_securely_operate_multi_accounts.html | 2026-08-27 | Nov 6, 2024 — ⚠️ >12mo |
| 5 | Identity and access management | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html | 2026-08-27 | Nov 6, 2024 — ⚠️ >12mo |
| 6 | Detection (SEC04) | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html | 2026-08-27 | Nov 6, 2024 — ⚠️ >12mo |
| 7 | Infrastructure protection (SEC05/SEC06) | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/infrastructure-protection.html | 2026-08-27 | Nov 6, 2024 — ⚠️ >12mo |
| 8 | Data protection (SEC07–SEC09) | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/data-protection.html | 2026-08-27 | Nov 6, 2024 — ⚠️ >12mo |
| 9 | Protecting data at rest (SEC08) | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html | 2026-08-27 | Nov 6, 2024 — ⚠️ >12mo |
| 10 | Incident response (SEC10) | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/incident-response.html | 2026-08-27 | Nov 6, 2024 — ⚠️ >12mo |
| 11 | Application security (SEC11) | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/application-security.html | 2026-08-27 | Nov 6, 2024 — ⚠️ >12mo |
| 12 | IAM — Security best practices | https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html | 2026-08-27 | current stable |

## Research Iteration Changelog

| Iteration | Date | Action | Result |
|-----------|------|--------|--------|
| Baseline | (prior run) | Initial research document — metadata, glossary, guardrails, detection/IAM/data-protection coverage | Complete but missing 3 mandatory sections + 2 best-practice areas |
| 1 | 2026-08-27 | Verified current edition against official welcome.html; confirmed Nov 6, 2024 is still current stable (no 2026 edition) | Version pin confirmed |
| 2 | 2026-08-27 | Fetched design principles + 7 best-practice areas (security.html); added **Framework Pillars** section | Gap resolved |
| 3 | 2026-08-27 | Fetched infrastructure-protection.html + application-security.html; added SEC-AD-7 (network/compute), SEC-AD-8 (AppSec), SEC-ND-7/8 anti-patterns, and Infrastructure Protection + Application Security architecture sections | Coverage gap resolved (5 of 7 → 7 of 7 areas) |
| 4 | 2026-08-27 | Added **Service Equivalence Map** (security-capability cross-provider) and **Source Bibliography** | Mandatory-section gaps resolved |
| 5 | 2026-08-27 | Triangulation pass: tagged design principles + SEC02/SEC08/SEC04 patterns with [✓✓ Triangulated] | No unresolved/unverified items remain |

> **Status:** 0 unverified items remaining. All 7 best-practice areas covered. All 6 mandatory output sections present (Framework Pillars, Mandatory Patterns, Architectural Decisions, Anti-Patterns, Service Equivalence Map, Source Bibliography).
