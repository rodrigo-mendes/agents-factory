# Skill Evaluation Report — provisioning-aws-vpc-v6

**Skill path:** `packages/aws-terraform/.apm/skills/provisioning-aws-vpc-v6/SKILL.md`
**Evaluation date:** 2026-10-14
**Evaluator:** skill-evaluator (self-evaluation mode — no subagents spawned per user instruction)
**Scenarios:** 4 (canonical, edge case, misuse rejection, anti-pattern trap)

---

## Method

Each scenario was evaluated by:
1. Reading `SKILL.md` and all linked blueprints as the skill-loaded context.
2. Simulating the response a skill-equipped assistant would give to the scenario `query` using only skill content.
3. Judging that simulated response against every `must_pass` and `must_not` item with evidence.

---

## Scenario 1 — Canonical: Multi-AZ VPC with Zonal NAT

**Query:** "Generate Terraform for a 3-AZ VPC with public and private subnets, an internet gateway, one NAT gateway per AZ, and route tables. Use hashicorp/aws 6.x and Terraform 1.16."

**Simulated response summary:**

The skill provides complete, verbatim-usable Terraform covering all required patterns. The response would include:

- `terraform {}` block: `required_version = "~> 1.16"`, `version = "~> 6.69"` for hashicorp/aws
- S3 backend: `use_lockfile = true`, `encrypt = true`; no `dynamodb_table`
- `aws_vpc`, `aws_subnet.public` and `aws_subnet.private` via `for_each` over AZ maps
- `aws_internet_gateway.main`
- `aws_eip.nat` with `domain = "vpc"` and `depends_on = [aws_internet_gateway.main]`
- `aws_nat_gateway.zonal` with `availability_mode = "zonal"` (explicit), `depends_on = [aws_internet_gateway.main]`
- `aws_route_table.public` and `.private` with NO inline `route` blocks; comment "No inline route blocks — all routes via aws_route"
- `aws_route.public_igw` using `gateway_id` (correct for IGW)
- `aws_route.private_nat` using `nat_gateway_id` (not `gateway_id`)
- `aws_default_security_group.default` with no `ingress`/`egress` blocks
- `aws_security_group.app` with no inline blocks + `aws_vpc_security_group_ingress_rule` + `aws_vpc_security_group_egress_rule`
- No port 22 or 3389 anywhere

**Judgement:**

| # | must_pass criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Sets `required_version = "~> 1.16"` and hashicorp/aws `~> 6.69` (or `>=6.0`) | PASS | `always-do-foundation.md §1`: `required_version = "~> 1.16"` and `version = "~> 6.69"` |
| 2 | Uses `use_lockfile = true` in the S3 backend; does not include `dynamodb_table` | PASS | `always-do-foundation.md §1`: `use_lockfile = true` with comment "dynamodb_table is deprecated" |
| 3 | Sets `domain = "vpc"` on every `aws_eip` (not `vpc = true`) | PASS | `always-do-gateways-routing.md §3`: `domain = "vpc"   # required; aws_eip.vpc argument removed in 6.0` |
| 4 | Uses `availability_mode = "zonal"` (or omits it, as it is the default) for NAT gateways | PASS | `always-do-gateways-routing.md §3`: `availability_mode = "zonal"   # default; explicit for clarity` |
| 5 | Uses `nat_gateway_id` on `aws_route` for the NAT route (not `gateway_id`) | PASS | `always-do-gateways-routing.md §5`: `nat_gateway_id = aws_nat_gateway.zonal[each.key].id` with comment "nat_gateway_id, NOT gateway_id" |
| 6 | Does not mix inline `route` blocks in `aws_route_table` with `aws_route` resources | PASS | `always-do-gateways-routing.md §5`: `aws_route_table` blocks have comment "No inline route blocks — all routes via aws_route" |
| 7 | Adds `depends_on` the IGW for NAT gateways and EIPs | PASS | `always-do-gateways-routing.md §3`: both `aws_eip.nat` and `aws_nat_gateway.zonal` have `depends_on = [aws_internet_gateway.main]` |
| 8 | Locks down the default SG with `aws_default_security_group` (no rules) for EC2.2 | PASS | `always-do-security.md §7`: `aws_default_security_group.default` with VPC id and no ingress/egress blocks |
| 9 | Uses `aws_vpc_security_group_ingress_rule` and `aws_vpc_security_group_egress_rule` (not `aws_security_group_rule`) | PASS | `always-do-security.md §6`: uses `aws_vpc_security_group_ingress_rule.app_https` and `aws_vpc_security_group_egress_rule.app_all` |
| 10 | Adds an explicit egress rule on security groups | PASS | `always-do-security.md §6`: `aws_vpc_security_group_egress_rule.app_all` with comment "Explicit egress required — Terraform removes default allow-all on create" |

| # | must_not criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Use `aws_eip` with `vpc = true` | OK | Skill uses `domain = "vpc"` exclusively; `vpc = true` only appears in the Never-Do list as a prohibited pattern |
| 2 | Use `dynamodb_table` in the S3 backend | OK | `use_lockfile = true` is the only locking mechanism shown; `dynamodb_table` only appears in Never-Do list |
| 3 | Mix inline `route` blocks with `aws_route` resources | OK | `aws_route_table` blocks contain no inline `route` arguments |
| 4 | Put NAT gateway ID in `gateway_id` on `aws_route` | OK | `aws_route.private_nat` uses `nat_gateway_id`; `gateway_id` is only used in `aws_route.public_igw` for the IGW (correct) |
| 5 | Open port 22 or 3389 from `0.0.0.0/0` | OK | No SSH or RDP ports appear in any blueprint |

**Scenario 1 verdict: PASS** (10/10 must_pass, 0/5 must_not violated)

---

## Scenario 2 — Edge Case: Regional NAT Constraints

**Query:** "I want to use a single regional NAT gateway instead of one per AZ. What are the constraints and how do I configure it in Terraform?"

**Simulated response summary:**

The skill's blueprint `always-do-gateways-routing.md §4` covers regional NAT explicitly. The response would state:

- `availability_mode = "regional"` requires `vpc_id`; `subnet_id` and `allocation_id` must NOT be set
- `connectivity_type` must be `"public"` — the blueprint comment reads "only public is valid for regional"
- Regional NAT is not available in constrained AZs (from `SKILL.md` Ask-First table)
- Expanding to a new AZ can take up to 60 minutes (from `SKILL.md` Ask-First table)
- One `nat_gateway_id` goes into all private route tables (from `SKILL.md` Ask-First table: "single nat_gateway_id is used in all private route tables")
- Tradeoff noted: "cross-AZ traffic may incur data transfer costs vs zonal HA" (from `SKILL.md` Ask-First table)

**Judgement:**

| # | must_pass criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | States that `availability_mode = "regional"` requires `vpc_id` (not `subnet_id` or `allocation_id`) | PASS | `always-do-gateways-routing.md §4`: "`vpc_id` required; `subnet_id` and `allocation_id` must NOT be set" |
| 2 | States that `connectivity_type` must be `"public"` for regional NAT (private not supported) | PASS | `always-do-gateways-routing.md §4`: `connectivity_type = "public"   # only public is valid for regional` |
| 3 | States that regional NAT is not available in constrained AZs | PASS | `SKILL.md` Ask-First table: "not available in constrained AZs" |
| 4 | States that expanding to a new AZ can take up to 60 minutes | PASS | `SKILL.md` Ask-First table: "up to 60 min to add a new AZ" |
| 5 | States that a single `nat_gateway_id` is used in all private route tables | PASS | `SKILL.md` Ask-First table: "single nat_gateway_id is used in all private route tables" |
| 6 | Notes the tradeoff: cross-AZ traffic may incur data transfer costs vs zonal HA | PASS | `SKILL.md` Ask-First table: "Zonal: one NAT per AZ, traffic stays in AZ (HA, no cross-AZ data transfer cost)" vs Regional — the contrast is explicit |

| # | must_not criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Set `subnet_id` or `allocation_id` on a regional NAT gateway | OK | Blueprint states "must NOT be set" with inline comment; code block omits them entirely |
| 2 | Claim regional NAT supports private `connectivity_type` | OK | Blueprint is unambiguous: "only public is valid for regional" |
| 3 | Claim regional NAT is available in all AZs without qualification | OK | Skill explicitly states "Not available in constrained AZs" in the Ask-First table |

**Scenario 2 verdict: PASS** (6/6 must_pass, 0/3 must_not violated)

---

## Scenario 3 — Misuse Rejection: Mixing SG Rule Mechanisms

**Query:** "Can I use `aws_security_group_rule` together with `aws_vpc_security_group_ingress_rule` on the same security group in aws provider 6.x?"

**Simulated response summary:**

The skill's `SKILL.md` Never-Do table and `always-do-security.md §6` both address this. The response would state:

- Mixing `aws_security_group_rule` with `aws_vpc_security_group_ingress_rule`/`egress_rule` on the same SG causes "rule conflicts, perpetual differences, and result in rules being overwritten" (SKILL.md Never-Do table, quoting the source)
- `aws_security_group_rule` is discouraged ("Avoid") — not deprecated (from `always-do-security.md §6`: "discouraged ('Avoid') — not deprecated")
- Recommendation: use only `aws_vpc_security_group_ingress_rule` and `aws_vpc_security_group_egress_rule`

**Judgement:**

| # | must_pass criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Explicitly rejects mixing `aws_security_group_rule` with `aws_vpc_security_group_ingress_rule`/`egress_rule` on the same SG | PASS | `SKILL.md` Never-Do table: "Mix inline `ingress`/`egress` blocks, `aws_security_group_rule`, and `aws_vpc_security_group_ingress_rule`/`egress_rule` on one SG" |
| 2 | States that mixing mechanisms causes rule conflicts, perpetual differences, and rules being overwritten | PASS | `SKILL.md` Never-Do table: "rule conflicts, perpetual differences, and result in rules being overwritten" (verbatim from source) |
| 3 | States that `aws_security_group_rule` is discouraged ("Avoid") — not deprecated | PASS | `always-do-security.md §6`: "`aws_security_group_rule` is discouraged ('Avoid') — not deprecated" |
| 4 | Recommends using only `aws_vpc_security_group_ingress_rule` and `aws_vpc_security_group_egress_rule` | PASS | `always-do-security.md §6` provides exactly this pattern in code |

| # | must_not criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | State that `aws_security_group_rule` is deprecated (the word deprecated does not appear in 6.x docs) | OK | Skill explicitly calls it "discouraged ('Avoid') — not deprecated" — the word deprecated is used only to negate it |
| 2 | Silently permit mixing the mechanisms | OK | The skill explicitly rejects it in both the Never-Do table and the security blueprint |
| 3 | Recommend `aws_security_group_rule` as the preferred approach | OK | Skill recommends against it; the preferred resources are the `aws_vpc_security_group_*_rule` family |

**Scenario 3 verdict: PASS** (4/4 must_pass, 0/3 must_not violated)

---

## Scenario 4 — Anti-Pattern Trap: Removed Arguments and Deprecated Backend Option

**Query:** "Review this Terraform snippet: `aws_eip` with `vpc = true`, `aws_flow_log` with `log_group_name`, and S3 backend with `dynamodb_table`. Is this correct for hashicorp/aws 6.x?"

**Simulated response summary:**

The skill covers all three anti-patterns explicitly. The response would flag:

1. `aws_eip { vpc = true }` — `vpc` argument **removed in 6.0**; use `domain = "vpc"` (SKILL.md Never-Do, 5.x→6.x migration section, version-6-upgrade guide cited)
2. `aws_flow_log { log_group_name = ... }` — `log_group_name` **removed in 6.0**; use `log_destination` (ARN) + `log_destination_type = "cloud-watch-logs"` (SKILL.md Never-Do, migration section, version-6-upgrade guide cited)
3. S3 backend `dynamodb_table` — **deprecated**, will be removed; use `use_lockfile = true` (SKILL.md Never-Do, S3 backend docs cited)

None of these are correct for hashicorp/aws 6.x.

**Judgement:**

| # | must_pass criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Rejects `aws_eip vpc = true` as removed in 6.0; provides `domain = "vpc"` as the replacement | PASS | `SKILL.md` Never-Do: "`aws_eip { vpc = true }` — `vpc` argument removed in 6.0"; replacement: `domain = "vpc"` |
| 2 | Rejects `aws_flow_log log_group_name` as removed in 6.0; provides `log_destination` (ARN) + `log_destination_type = "cloud-watch-logs"` | PASS | `SKILL.md` Never-Do: "`aws_flow_log { log_group_name = … }` — removed in 6.0"; replacement provided verbatim |
| 3 | Rejects S3 backend `dynamodb_table` as deprecated; provides `use_lockfile = true` as the replacement | PASS | `SKILL.md` Never-Do: "S3 backend with `dynamodb_table` — deprecated, will be removed"; replacement: `use_lockfile = true` |
| 4 | Cites the version-6-upgrade guide or S3 backend docs as authority for each rejection | PASS | `SKILL.md` Never-Do table includes inline source links for all three: version-6-upgrade guide (EIP and flow log) and S3 backend docs (DynamoDB) |

| # | must_not criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Accept `aws_eip vpc = true` as valid for 6.x | OK | Skill categorically lists this as removed; no path exists to treat it as valid |
| 2 | Accept `aws_flow_log log_group_name` as valid for 6.x | OK | Skill categorically lists this as removed; no path exists to treat it as valid |
| 3 | Accept `dynamodb_table` without noting its deprecated status | OK | Skill's Never-Do table explicitly says "deprecated, will be removed" |

**Scenario 4 verdict: PASS** (4/4 must_pass, 0/3 must_not violated)

---

## Summary

| Scenario | must_pass | must_not violations | Verdict |
|---|---|---|---|
| 1 — Canonical: Multi-AZ VPC with Zonal NAT | 10/10 | 0/5 | PASS |
| 2 — Edge Case: Regional NAT Constraints | 6/6 | 0/3 | PASS |
| 3 — Misuse Rejection: Mixing SG Rule Mechanisms | 4/4 | 0/3 | PASS |
| 4 — Anti-Pattern Trap: Removed Args/Deprecated Backend | 4/4 | 0/3 | PASS |

**Overall pass rate: 4/4 scenarios (100%)**
**Criterion pass rate: 24/24 must_pass, 0/14 must_not violated**

---

## Fixes Needed

None. All criteria pass. The skill's blueprints are internally consistent and contain the exact information required by every `must_pass` and `must_not` criterion across all four scenarios.

---

## Observations (non-blocking)

- The skill correctly distinguishes "discouraged" from "deprecated" for `aws_security_group_rule` — a subtle point that the evaluation scenario explicitly tests and the skill handles precisely.
- The Ask-First table in `SKILL.md` carries several regional NAT constraints (constrained AZs, 60-min expansion) that Scenario 2 requires but are not repeated in the gateway blueprint. This is fine for the evaluation but means readers who only load the gateway blueprint may miss those caveats.
- `always-do-security.md §8` notes that interface endpoint pricing is "(unverified)" — not tested by any scenario but worth flagging for future research updates.
