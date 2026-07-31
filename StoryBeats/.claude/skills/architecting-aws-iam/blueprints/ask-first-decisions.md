# Ask First Decisions — AWS IAM (pinned 2026-07-31)

4 architectural crossroads that require context before prescribing a pattern.
Degree of freedom: **High** — multiple valid approaches; ask before deciding.

---

## 1. Human access model: IAM Identity Center vs direct SAML/OIDC vs IAM users

**Ask before prescribing**: "Which external IdP is authoritative (Entra ID / Okta / Ping), and is this a single-account or multi-account AWS Organizations estate?"

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| IAM Identity Center + external IdP | IAM Identity Center, STS | Central multi-account access, permission sets, MFA enforcement, access reviews | Additional setup layer; another AWS service to operate | Multi-account AWS Organizations (recommended default) |
| Direct SAML/OIDC federation into IAM roles | IAM SAML/OIDC providers, STS | Simplicity for small scope; no Identity Center dependency | No central permission-set model; per-account IdP config | 1–2 accounts, existing mature IdP, minimal footprint |
| IAM users with passwords/access keys | IAM | Compatibility with tools that cannot federate | Long-term credentials to rotate and potentially leak | Only the documented exception list (CodeCommit, Keyspaces, third-party client/plugin that cannot use federation) |

**Cost profile**: IAM and IAM Identity Center have no per-user charge. Access Analyzer unused/internal analyzers are billed per role or resource analyzed per analyzer per month.

**Lock-in assessment**: Identity Center permission sets are AWS-specific syntax, but sit behind a standard SAML/OIDC IdP that remains portable.

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-users-federation-idp (accessed 2026-07-31)

---

## 2. Delegation model: permissions boundaries vs central role creation

**Ask before prescribing**: "Must developers self-serve IAM role creation, or can a central platform team own all role provisioning?"

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Delegate role creation with a required permissions boundary | IAM permissions boundaries, SCP enforcement | Developer velocity; no central bottleneck | Boundary policy must be designed and enforced via SCP | Many teams needing self-service roles; large org |
| Central platform team creates all roles via IaC pipeline | IAM, Terraform/CloudFormation pipeline | Tight control; uniform security review | Central bottleneck; slower delivery | Small org or high-compliance environment with strict change control |

**How permissions boundaries work**:
- A managed policy attached to a user/role that caps the maximum permissions an identity-based policy can grant to that entity
- Does not grant permissions — the intersection of the boundary and the identity policy determines effective permissions
- Paired with an SCP that denies creating roles without the boundary (`iam:CreateRole` denied if `iam:PermissionsBoundary` not set)

**Cost profile**: No direct cost difference. Operational cost differs: bottleneck overhead (central) vs governance tooling overhead (self-service).

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-permissions-boundaries (accessed 2026-07-31)

---

## 3. Authorization model at scale: RBAC vs ABAC

**Ask before prescribing**: "Is there a governed tagging standard already enforced via SCP or tag policies? Will tagging be audited?"

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| RBAC — one policy per job function or team | IAM managed policies | Explicit and auditable; simple mental model; no tagging dependency | Policy sprawl as teams and resources multiply | Stable, small set of access patterns; tagging not governed |
| ABAC — tag-matching condition policies | IAM condition keys (`aws:PrincipalTag`, `aws:ResourceTag`) | Scales without editing policies as resources grow; multi-tenant project isolation | Requires disciplined governed tagging; missing tags become access gaps | Many teams/projects/tenants with an enforced tagging standard |

**ABAC risk**: Without an enforced tagging standard (via SCP / AWS Organizations tag policies), ABAC becomes an access-control gap where missing or incorrect tags silently deny or grant access. Default to RBAC if tagging governance is not in place.

**ABAC example condition** (a workload can access only resources tagged with its own project tag):
```json
"Condition": {
  "StringEquals": {
    "aws:PrincipalTag/Project": "${aws:ResourceTag/Project}"
  }
}
```

**Cost profile**: No direct IAM cost difference.

**Source**: https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html (accessed 2026-07-31)

---

## 4. Emergency break-glass access design (SEC03-BP03)

**Ask before prescribing**: "What is the recovery path if IAM Identity Center or the external IdP becomes unavailable? Is there an existing runbook for this scenario?"

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Break-glass IAM role with strong monitoring | IAM role, CloudTrail, EventBridge, SNS, GuardDuty | Controlled recovery during IdP/Identity Center outage; auditable; bounded blast radius | Must be tightly guarded; credentials stored securely (e.g., Secrets Manager with restricted access) | All production orgs — required baseline |
| Relying on root user as the only break-glass | Root user | No extra setup | Root has unrestricted access; bypasses most guardrails; high blast radius; slower for most tasks | Never — root is the wrong tool for routine break-glass |

**Break-glass role design**:
- One role per account (or a cross-account break-glass role in a dedicated account) with AdministratorAccess scoped minimally
- Credentials stored in Secrets Manager with strict access controls and access logging
- Every use triggers an immediate CloudTrail alert via EventBridge → SNS to the security team
- GuardDuty: `PrivilegeEscalation:IAMUser/AnomalousBehavior` and `Policy:IAMUser/RootCredentialUsage` are additional signals

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_permissions_emergency_process.html (accessed 2026-07-31)
