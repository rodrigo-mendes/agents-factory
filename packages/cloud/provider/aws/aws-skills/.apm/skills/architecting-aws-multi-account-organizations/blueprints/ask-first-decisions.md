# Ask First Decisions — architecting-aws-multi-account-organizations

Source: research base `research_cloud_AWS_Organization_Architecture_Multi_Account_Strategy_2026.md`
(AWS Organizations 2026; research date 2026-08-26; all sources accessed 2026-08-26).

---

## AF-1 — OU Structure Design

**Ask**: "Does the dev environment require meaningfully different SCPs than test?" Yes → separate Dev OU + Test OU. No → single NonProd OU (less SCP maintenance).

| OU Category | OU | Purpose | When Needed |
|---|---|---|---|
| Foundational | Security | Log Archive + Audit/Security Tooling | Always (even though optional in CT v4.0) |
| Foundational | Infrastructure | Network, Shared Services, Backup | Always for enterprise |
| Application | Workloads (Prod/NonProd) | Business workload accounts | Always |
| Experimental | Sandbox | Isolated exploration, no prod connectivity | When developers need it |
| Procedural | Exceptions | Non-standard policy deviations | Minimally, when unavoidable |
| Procedural | Suspended | Accounts held before closure | Always |
| Procedural | Policy Staging | Test SCP/tag policy changes before rollout | Strongly recommended |
| Procedural | Transitional | Landing zone for onboarded accounts | When migrating existing accounts |
| Advanced | Deployments | CI/CD pipeline accounts | When CI/CD needs isolation |
| Advanced | Business Continuity | DR / air-gapped accounts | Regulated/critical workloads |
| Advanced | Individual Business Users | BU self-managed accounts | When BUs need direct access |

**Principles** (Whitepaper, April 30, 2025): organize by function, not org chart; attach SCPs to OUs (account-level only for exceptions); max 5 nesting levels — use depth only when the benefit is clear; start small.
**Cost**: No direct billing difference — affects operational complexity and audit scope.
**Source**: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html (accessed 2026-08-26)

---

## AF-2 — Multi-Account Networking Topology

**Ask**: "Is centralized traffic inspection (firewall, IDS/IPS) required?" Yes → Transit Gateway with an Inspection VPC. "Is IPv4 address space constrained?" Yes → evaluate VPC Sharing. Default: Transit Gateway hub-spoke for > 5 VPCs or any hybrid connectivity.

| Option | Services | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Hub-spoke | Transit Gateway + RAM | Central routing; single on-prem attachment | Per-GB transit cost; route table complexity | > 5 VPCs; hybrid; central inspection |
| VPC Sharing | VPC + RAM | Fewer VPCs; no same-AZ transfer charges | Reduced isolation; shared subnet space | Same security posture; IPv4 scarcity |
| VPC Peering | VPC Peering | Simple; no same-AZ per-GB charge | N² connections; no transitive routing | < 5 VPCs, stable topology |
| PrivateLink | Endpoint services | Per-service isolation | Cost per endpoint; latency | Exposing specific services cross-account |

**Cost profile** (as stated in research): TGW $0.05/attachment-hour + $0.02/GB; PrivateLink $0.01/hour per endpoint + $0.01/GB. Pricing page not cited — (unverified); confirm before quoting.
**Lock-in**: TGW and PrivateLink have no direct equivalents elsewhere — migration means re-architecting connectivity.
**Source**: https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/transit-gateway.html (accessed 2026-08-26); https://docs.aws.amazon.com/whitepapers/latest/building-scalable-secure-multi-vpc-network-infrastructure/amazon-vpc-sharing.html (accessed 2026-08-26)

---

## AF-3 — Landing Zone: Control Tower vs DIY vs Control Tower + LZA

**Ask**: "GovCloud, Secret or Top Secret regions, or DoD compliance?" Yes → LZA required. "Need IaC customization beyond Control Tower v4.0?" Yes → evaluate LZA on top of Control Tower. Default → Control Tower.

| Option | Effort | Flexibility | Compliance | Best When |
|---|---|---|---|---|
| Control Tower | Low; managed | Moderate (v4.0 = high) | Built-in controls catalog | Standard enterprise |
| DIY Organizations | High; manual | Maximum | Manual | Non-standard patterns |
| Control Tower + LZA | Medium; IaC-driven | Very high | Extended + custom | Regulated / sovereign; classified partitions |

**Notes**:
- LZA is complementary to Control Tower, not a replacement (vends accounts via Account Factory).
- Control Tower v4.0 (November 17, 2025): Security OU optional; Config, CloudTrail, Security Roles, Backup integrations individually selectable; mandatory controls no longer applied by default — enable those your compliance profile needs.
- Scaling path: < 50 accounts Control Tower + manual Account Factory; 50–500 add AFT; > 500 add LZA.
- DoD IL4/IL5 specifics: (unverified) — check https://docs.aws.amazon.com/prescriptive-guidance/latest/secure-architecture-dod/lza-overview.html.
- AFT unsupported regions (Spain, Zurich, Tel Aviv, UAE, Hyderabad): (unverified) — check https://docs.aws.amazon.com/controltower/latest/userguide/aft-resources.html.

**Cost**: Control Tower has no additional charge (pay for Config, CloudTrail, etc.); LZA ~$430/month idle baseline in us-east-1 (per research).
**Source**: https://docs.aws.amazon.com/solutions/latest/landing-zone-accelerator-on-aws/solution-overview.html (accessed 2026-08-26); https://docs.aws.amazon.com/controltower/latest/userguide/2025-all.html (2025 release notes); https://docs.aws.amazon.com/controltower/latest/controlreference/control-behavior.html (accessed 2026-08-26)

---

## AF-4 — RI and Savings Plans Discount Sharing

**Ask**: "Chargeback (BU charged exact costs) or showback (BU sees costs, central IT pays)?" Chargeback → Restricted Group Sharing. Showback → Organization-wide sharing.

| Mode | Behavior | Optimizes | Sacrifices | Best When |
|---|---|---|---|---|
| Organization-wide | Owner first, remainder org-wide | Total org savings | BU accountability | Centralized FinOps |
| Prioritized Group | Owner → defined groups → rest of org | BU-prioritized savings | More setup | Multiple BUs with own RI budgets |
| Restricted Group | Owner → group only, no spillover | BU isolation | Possible unused capacity | Strict chargeback |

**Note**: Sharing settings finalize at 23:59:59 UTC on the last day of each month. Disabling sharing can raise the bill if RIs bought for shared use go unused.
**Source**: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/ri-turn-off.html (accessed 2026-08-26)
