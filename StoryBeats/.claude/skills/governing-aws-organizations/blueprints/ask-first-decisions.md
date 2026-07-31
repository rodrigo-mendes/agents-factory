# Ask-First Decisions — AWS Organizations Governance (2024-2025)

Source: AWS Organizations User Guide + Organizing Your AWS Environment whitepaper (April 30, 2025). All sources accessed 2026-07-31.

---

## AF-1 — SCP strategy: Deny-list vs Allow-list

**Decision**: Should SCP guardrails use a deny-list or an allow-list strategy?

| Option | AWS mechanism | Optimizes | Sacrifices | Best When |
|--------|---------------|-----------|------------|-----------|
| **Deny list** (default) | Keep `FullAWSAccess` + add explicit Deny statements | Simplicity, low lockout risk, new services allowed by default | Broad Allow may permit unintended service access | Most orgs; the AWS default and recommended starting point |
| **Allow list** | Remove/replace `FullAWSAccess`; explicitly Allow a service subset at EVERY level | Tight service allowlisting; new services blocked unless allowed | High lockout risk; Allow must exist at root → OU → account or all access is denied | Highly regulated orgs needing an explicit service whitelist |

**Key mechanic**: "For a permission to be allowed... there must be an explicit Allow statement at every level from the root through each OU... including the target account." Any single Deny anywhere in the path wins. Missing an Allow at the root blocks ALL member access.

**Question to ask the architect**: "Do you need an explicit whitelist of permitted services (allow-list), or is denying a known-bad set sufficient (deny-list)? If allow-list, are you prepared to maintain Allow statements at every hierarchy level and test in a Policy Staging OU first?"

Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_evaluation.html

---

## AF-2 — AWS Control Tower vs. self-managed (DIY) landing zone

**Decision**: Adopt AWS Control Tower or build a custom landing zone directly on AWS Organizations?

| Option | AWS mechanism | Optimizes | Sacrifices | Best When |
|--------|---------------|-----------|------------|-----------|
| **AWS Control Tower** | Orchestrates Organizations + Service Catalog + Identity Center | Speed (landing zone < 1 hr), prescriptive controls, drift detection, Account Factory | Some rigidity; opinionated OU/account model; regional/feature constraints | Teams wanting managed governance and standardized account vending |
| **DIY on Organizations** | Organizations + CloudFormation StackSets / IaC + custom SCPs | Full customization, no Control Tower constraints | You build/own controls, drift detection, and vending; higher effort | Advanced platform teams with requirements Control Tower cannot meet |

**Key mechanic**: "AWS Control Tower orchestration extends the capabilities of AWS Organizations." You can extend Control Tower by working directly in Organizations, then register existing orgs/enroll accounts. Control Tower itself has no additional charge beyond the AWS resources it deploys (Config, CloudTrail, S3, etc.).

**Question to ask the architect**: "Do you want AWS-managed, prescriptive governance with built-in Account Factory and drift detection (Control Tower), or full control over a custom landing zone (DIY)? Do any requirements conflict with Control Tower's opinionated model?"

Source: https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html

---

## AF-3 — OU hierarchy: flat vs. deep; functional vs. environment vs. workload

**Decision**: How should OUs be structured and how deep should the hierarchy go?

| Option | AWS mechanism | Optimizes | Sacrifices | Best When |
|--------|---------------|-----------|------------|-----------|
| **Functional OUs** (AWS-recommended) | Security, Infrastructure, Workloads, Sandbox OUs | Clear control boundaries, aligns to Control Tower | Requires mapping teams onto functions | Default enterprise pattern |
| **Environment nested under Workloads** | Workloads OU → Prod / Non-Prod nested OUs | Different SCP guardrails per environment | Extra nesting level; more policy attach points | Distinct prod vs non-prod controls are required |
| **Deep hierarchy** (up to 5 levels) | Nested OUs per workload/team | Fine-grained inherited controls | Complexity; harder to reason about effective policy | Large orgs with many distinct isolation tiers |

**Key mechanic**: "Your hierarchy can be five levels deep (including root and lowest accounts)." Nesting "enables smaller units of management"; child OUs inherit parent policies plus their own. Max 2,000 OUs per org.

**Question to ask the architect**: "Do prod and non-prod (or per-workload teams) need materially different guardrails? If not, prefer a shallow functional structure. Never mirror the corporate org chart rigidly — organize by the controls accounts need in common."

Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html

---

## AF-4 — Number of accounts and account granularity

**Decision**: How many accounts, and at what granularity (per-workload, per-environment, per-team)?

| Option | AWS mechanism | Optimizes | Sacrifices | Best When |
|--------|---------------|-----------|------------|-----------|
| **Account per workload + environment** (AWS-recommended) | Multiple member accounts | Strong isolation, clean cost mapping, blast-radius control | More accounts to automate/govern | The AWS-recommended default |
| **Fewer, larger shared accounts** | Shared accounts | Less account sprawl | Weaker isolation, muddied cost attribution | Very small footprints / early experimentation only |

**Key mechanic**: "The optimal number of AWS accounts... can range from a few to thousands." "AWS charges are based on resource usage, not the number of accounts." Default org quota = 10 accounts; adjustable up to 50,000 based on qualification. Concurrent creation limit = 5 in progress at a time.

**Cross-provider note**: Account granularity maps conceptually to GCP Projects and Azure Subscriptions as the equivalent isolation/billing unit.

**Question to ask the architect**: "What isolation and cost-attribution granularity do you need? Default to one account per workload per environment and automate provisioning via Account Factory. Do you need a quota increase beyond the default 10 accounts?"

Source: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html ; https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html

---

## AF-5 — Account vending: Control Tower Account Factory vs. Organizations API/IaC

**Decision**: How to provision and enroll new accounts at scale?

| Option | AWS mechanism | Optimizes | Sacrifices | Best When |
|--------|---------------|-----------|------------|-----------|
| **Control Tower Account Factory** | Service Catalog product wrapping account creation | Self-service, governed, applies controls automatically | Tied to Control Tower's model | Standardized enterprise vending |
| **Account Factory for Terraform (AFT)** | GitOps pipeline over Account Factory | IaC-driven vending, customizations via pipelines | Additional pipeline to run; more complexity | Terraform-centric platform teams |
| **Organizations CreateAccount API / StackSets** | Direct API + CloudFormation StackSets | Maximum control, no Control Tower dependency | You build governance/enrollment | DIY landing zones |

**Key mechanic**: Account Factory "helps automate the account provisioning workflow" and is "built as an abstraction on top of provisioned products in AWS Service Catalog... automates the process of applying controls and policies." Org quota: create max 5 accounts concurrently.

**Question to ask the architect**: "Do you want managed self-service vending (Account Factory), a Terraform GitOps pipeline (AFT), or full-custom API/StackSets vending? Which integrates with your existing IaC and approval workflows?"

Source: https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html

---

## AF-6 — SCP vs RCP vs declarative policies: which guardrail for which need

**Decision**: Which policy type enforces a given control — SCP, RCP, or a declarative policy?

| Option | AWS mechanism | Targets | Optimizes | Best When |
|--------|---------------|---------|-----------|-----------|
| **SCP** | Principal-centric permission guardrail | IAM users + roles in member accounts | Caps what identities may DO | Restricting member-account principals |
| **RCP** | Resource-centric permission guardrail | Resources in member accounts | Enforces data perimeter (who may access your resources) | e.g., only org identities may access your S3 buckets |
| **Declarative policy** | Service configuration enforcement | Service settings org-wide | Durable config baselines that survive new APIs | Enforcing service settings: block public AMIs, S3 config, IMDSv2 |

**Key mechanic**: Effective permissions = intersection of SCP ∩ RCP ∩ IAM identity-based ∩ resource-based policies. SCPs and RCPs never grant — only restrict. `RCPFullAWSAccess` is auto-attached to root/OUs/accounts and cannot be detached (counts toward the 5-RCP-per-entity hard limit).

**Combine for defense-in-depth**:
- SCP: "member-account principals may not create public S3 buckets" (principal side)
- RCP: "only identities within the org may access our S3 buckets" (resource side)
- Declarative policy: "S3 block-public-access is always ON org-wide" (service config side)

**Question to ask the architect**: "Is the control about what identities can DO (SCP), what can touch your RESOURCES (RCP), or how a SERVICE is CONFIGURED (declarative policy)? Combine them for defense-in-depth."

Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html
