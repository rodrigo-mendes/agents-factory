# Reference Architecture — AWS Organizations Enterprise Landing Zone (2024-2025)

Source: AWS Organizations User Guide + Organizing Your AWS Environment whitepaper (April 30, 2025). All sources accessed 2026-07-31.

---

## Enterprise Landing Zone Topology (Control Tower-aligned)

**Context**: Enterprise multi-account governance with centralized security and billing.

| Layer | Account / OU | Purpose |
|-------|-------------|---------|
| Root | Management account | Org owner + payer; org-admin tasks ONLY; no workloads; org CloudTrail owner |
| Security OU | Log Archive account | Central, access-restricted S3 for org CloudTrail + Config logs; tamper-resistant |
| Security OU | Audit / Security Tooling account | Delegated admin for GuardDuty, Security Hub, Config aggregator, IAM Access Analyzer |
| Infrastructure OU | Network account | Centralized networking: Transit Gateway, shared VPCs, DNS, egress |
| Infrastructure OU | Shared Services account | Directory, CI/CD shared tooling, golden AMIs |
| Workloads OU (Prod nested) | Per-workload prod accounts | Production workloads; stricter SCP/RCP guardrails |
| Workloads OU (Non-Prod nested) | Per-workload dev/test accounts | Non-production; relaxed guardrails, cost caps |
| Sandbox OU | Sandbox accounts | Experimentation; limited production access |
| Policy Staging OU | Staging/test accounts | Validate new SCPs/policies before broad rollout |

**Architect customization decisions**: AF-1 (SCP strategy), AF-2 (Control Tower vs DIY), AF-3 (OU depth), AF-4 (account count/quota), AF-5 (vending mechanism).

**Scaling path**:
1. **Early adoption**: Few accounts, manual vending, basic OUs (Security, Workloads, Sandbox)
2. **Foundation stage**: Automated account vending (Account Factory), Cloud Center of Excellence, cost management
3. **Enterprise scale**: Thousands of accounts; org quota adjustable up to 50,000

Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html

---

## Policy Evaluation Model

Effective permission for a principal in a member account:

```
Effective Permission =
  SCP (principal guardrail from org)
  ∩ RCP (resource guardrail from org)
  ∩ IAM identity-based policy (grants)
  ∩ IAM resource-based policy (if applicable)
```

- Neither SCP nor RCP ever grants permissions — they only restrict
- Any explicit Deny anywhere in the chain wins over any Allow
- The management account is EXEMPT from SCP restrictions (not from RCPs for resources it hosts)
- `RCPFullAWSAccess` is auto-attached and cannot be detached; counts toward the 5-RCP-per-entity hard limit

---

## Cross-Provider Service Equivalence

> AWS column is fully source-verified (2026-07-31). Non-AWS columns are conceptual mappings — verify against each provider's current documentation before relying on parity. Governance semantics differ (e.g., SCP intersection differs from Azure Policy effects).

| Concept | AWS | Azure | GCP | OCI |
|---------|-----|-------|-----|-----|
| Top governance root | Organization root (management account) | Root Management Group / Tenant (Entra ID) | Organization node | Tenancy (root compartment) |
| Account grouping | Organizational Unit (OU) | Management Group | Folder | Compartment (nestable) |
| Isolation + billing unit | AWS account | Subscription | Project | Compartment / Tenancy |
| Max nesting depth | 5 levels | 6 levels | 10 levels | 6 levels |
| Principal guardrail | SCP | Azure Policy (deny) + Deny assignments | Org Policy constraints | IAM Policies |
| Resource guardrail | RCP | Azure Policy restrictions / Deny assignments | VPC Service Controls | IAM + conditions |
| Config enforcement | Declarative policies | Azure Policy (modify/deployIfNotExists) | Org Policy constraints | Cloud Guard + Policies |
| Tag governance | Tag policies | Azure Policy tag rules | Org Policy label constraints | Tag defaults |
| Backup governance | Backup policies (AWS Backup) | Azure Backup + Policy | Backup for GKE / Backup DR | OCI Backup policies |
| Workforce access | IAM Identity Center (org instance) | Microsoft Entra ID + PIM | Cloud Identity / Workforce IdF | OCI IAM / Identity Domains |
| Landing zone | AWS Control Tower | Azure Landing Zones (CAF) | Cloud Foundation Toolkit | OCI Landing Zone |
| Account vending | Account Factory / AFT | Subscription vending | Project Factory | Compartment automation |
| Org-wide audit log | CloudTrail organization trail | Azure Monitor / Activity Log to Log Analytics | Cloud Audit Logs (org sink) | OCI Audit + Logging |
| Threat detection | GuardDuty (delegated admin) | Defender for Cloud | Security Command Center | OCI Cloud Guard |
| Security posture | Security Hub (central config + delegated admin) | Defender for Cloud secure score | Security Command Center | OCI Cloud Guard / Security Zones |
| Consolidated billing | Consolidated billing (payer account) | Microsoft Customer Agreement billing | Cloud Billing account | OCI consolidated billing |

---

## Key Quotas (AWS Organizations 2024-2025)

> Re-verify against the live [Quotas page](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html) before design commitments. Organizations is a global service hosted in `us-east-1`; request increases there.

| Item | Default / Hard Limit | Adjustable |
|------|---------------------|-----------|
| Max accounts per org | 10 default; up to 50,000 based on qualification | Yes (mgmt acct only) |
| Roots per org | 1 | No |
| OUs per org | 2,000 | — |
| OU nesting depth | 5 levels under root | No (hard) |
| SCPs per org | 10,000 | — |
| SCPs attached per entity (root/OU/account) | 10 (minimum 1 when SCPs enabled) | No (hard) |
| SCP max document size | 10,240 characters | No |
| RCPs per org | 2,000 | — |
| RCPs attached per entity | 5 (`RCPFullAWSAccess` counts) | No (hard) |
| RCP max document size | 5,120 characters | No |
| Declarative policy max size | 10,000 characters | No |
| Declarative policies per org | 1,000; 10 per entity | No |
| Tag / Backup policy max size | 10,000 characters | No |
| Tag / Backup policies per org | 1,000 each | — |
| Concurrent account creation | 5 in progress at a time | No |
| Invitation attempts per 24h | 20 or org account max, whichever greater | — |
| Tags per root/OU/account | 50 | — |
| IAM Identity Center accounts | 7,000 | Yes |
| GuardDuty members per delegated admin (per Region) | 50,000 | — |

Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html
