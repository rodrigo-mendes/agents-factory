# Ask First Decisions — architecting-aws-security-pillar

Source: AWS Well-Architected Framework Security Pillar, November 6, 2024 (verified 2026-08-27)

These are architectural crossroads where the correct choice depends on organizational context.
Always gather the indicated information before making a recommendation.

---

## Decision A — Multi-account governance model

**Pillar alignment**: Security foundations (SEC01-BP01)

**Before recommending, ask**:
> "Does the organization have an existing landing zone or AWS account governance pipeline already deployed?"

Retrofitting Control Tower onto a mature DIY Organizations setup is high-effort and requires careful SCP/guardrail reconciliation. If a mature DIY setup exists, evaluate whether its limitations justify migration before recommending Control Tower.

| Option | AWS Services | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| **Managed landing zone** | AWS Control Tower + Account Factory | Speed, built-in guardrails, automated account vending | Flexibility / customization ceiling | New or standard orgs wanting a fast best-practice baseline with no existing tooling |
| **DIY org + policies** | AWS Organizations + SCPs/RCPs + CloudFormation StackSets | Full control over OU design and policy logic | Build and maintenance engineering effort | Highly specific compliance/governance requirements, or mature existing landing zone tooling |

**Cost profile**: Control Tower has no additional service charge beyond the underlying AWS services it manages. DIY incurs engineering time cost proportional to the organization's size.

**Lock-in assessment**: Both options use AWS Organizations as the underlying primitive. Migration between them is possible but requires careful reconciliation of SCPs, guardrails, and account structures. Neither option creates meaningful lock-in at the organization level.

**Architect instruction**: Do not default to Control Tower for organizations that have been on AWS more than 12 months — ask first. For greenfield organizations (≤6 months on AWS), Control Tower is generally the right default.

**Source**: SEC01-BP01 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_securely_operate_multi_accounts.html

---

## Decision B — Identity source for IAM Identity Center

**Pillar alignment**: Identity and access management (SEC02-BP04)

**Before recommending, ask**:
> "Does the organization already have a corporate identity provider (Okta, Microsoft Entra ID, Ping Identity, or similar)?"

If a corporate IdP exists, use it as the authoritative identity source — federate IAM Identity Center to it. Creating a parallel native identity store creates a second source of truth for user lifecycle management (onboarding, offboarding, role changes) that must be kept in sync manually.

| Option | AWS Services | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| **Native identity store** | IAM Identity Center built-in identity store | Simplicity, no external dependency | Enterprise directory integration, user lifecycle automation | Small or greenfield organization with no existing corporate directory |
| **External IdP federation** | IAM Identity Center + Okta / Microsoft Entra ID / Ping | Single source of truth, automatic user lifecycle management, existing MFA policies enforced | Initial integration setup effort; ongoing IdP license cost | Organization with an existing workforce directory and IdP |

**Cost profile**: IAM Identity Center itself has no additional charge. External IdP option incurs IdP licensing cost (already present in most enterprises).

**Lock-in assessment**: Switching from native identity store to an external IdP (or between external IdPs) requires only reconfiguring the SAML/OIDC connection in IAM Identity Center — user provisioning via SCIM is re-run. This is not high lock-in.

**Architect instruction**: If the organization has >20 employees and any existing SaaS with SSO, a corporate IdP almost certainly exists — ask before recommending the native identity store.

**Source**: IAM best practices + SEC02-BP04 [✓✓ Triangulated]

---

## Decision C — Encryption key ownership per data store

**Pillar alignment**: Data protection (SEC08-BP01)

**Before recommending, ask**:
> "What is the data classification (public / internal / confidential / restricted) for this specific data store? Does the organization have a regulatory key-custody mandate (PCI-DSS, HIPAA, FedRAMP)?"

Key management overhead must be proportional to data sensitivity. Do not apply CMKs to low-sensitivity data stores where AWS-managed keys suffice — this adds per-key monthly cost and key lifecycle management overhead without commensurate security benefit.

| Option | AWS Services | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| **AWS-managed keys** | AWS KMS AWS-managed key | Zero key administration overhead | Granular key policy control; cross-account grants | Low compliance sensitivity; no regulatory key-custody mandate; public or internal data |
| **Customer-managed keys (CMK)** | AWS KMS CMK | Granular key policy, audit trail via CloudTrail, rotation control, cross-account grant capability | Per-key monthly charge (~$1/month); key lifecycle management overhead | Regulated data (PCI, HIPAA, FedRAMP) or cross-account access; confidential or restricted data |
| **Imported key material / external key store** | AWS KMS external key store (XKS) | Full key custody outside AWS (HSM remains under customer control) | Highest operational burden; availability dependency on external HSM; highest cost | Strict key-custody mandates requiring proof that keys never leave the customer's physical control |

**Cost profile**:
- AWS-managed keys: no per-key charge; API calls billed at standard KMS rate
- CMKs: ~$1/key/month + API call charges
- External key store: CMK cost + external HSM infrastructure and connectivity cost

**Lock-in assessment**: CMKs are AWS-regional. Data encrypted under a CMK cannot be decrypted outside that region without explicit cross-region key replication (KMS multi-region keys). Plan for multi-region key architecture if DR/failover is required.

**Architect instruction**: Run through data classification before any KMS recommendation. The most common mistake is applying CMKs everywhere "for security" without recognizing the key lifecycle overhead this creates at scale (hundreds of services × multiple regions × key rotation).

**Source**: SEC08-BP01 https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html
