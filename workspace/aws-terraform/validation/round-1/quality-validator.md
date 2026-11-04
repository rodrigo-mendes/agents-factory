# Quality Validation Report — provisioning-aws-vpc-v6

**Validator:** quality-validator (pilot P3, hybrid knowledge skill)
**Artifact:** `packages/aws-terraform/.apm/skills/provisioning-aws-vpc-v6/` (SKILL.md + 11 blueprints)
**Research source:** `workspace/aws-terraform/research_AWS_VPC_tf-aws-v6.md` (2026-10-14)
**Validation date:** 2026-10-14
**Rubric:** `hybrid-format-checklist.md`, `tag-notation-and-registers.md`, `evidence-rule.md`, `skill-frontmatter.md`
**Reference:** `packages/stripe-java/.apm/skills/developing-stripe-java-core-v34/` (accepted)

---

## Executive Summary

| Severity | Count | Blocking? |
|----------|-------|-----------|
| HIGH     | 0     | —         |
| MEDIUM   | 2     | No        |
| LOW      | 2     | No        |

**Overall verdict: PASS with minor corrections.** No wrong facts, no broken HCL, no format blockers.
The skill is ready for use pending the two MEDIUM fixes.

---

## 1. Hybrid Format Checklist — Item-by-Item

### 1.1 Frontmatter

| Check | Result | Notes |
|-------|--------|-------|
| Only `name` + `description` (no action-command fields) | ✅ | Lines 2-3; no `context`, `agent`, `disable-model-invocation` |
| `description` is quoted | ✅ | Double-quoted |
| `description` < 300 chars | ✅ | 276 chars |
| `description` contains "Use when" | ✅ | "Use when writing Terraform for VPC networking" |
| `name` matches folder name | ✅ | Both `provisioning-aws-vpc-v6` |
| Version suffix format `-vMAJOR-MINOR` | ⚠️ | Uses `-v6` (major only); see **F-M1** |

### 1.2 SKILL.md Structure and Length

| Check | Result | Notes |
|-------|--------|-------|
| SKILL.md 100-200 lines | ✅ | 147 lines |
| Version Context table with Source column | ✅ | Lines 14-21; all rows carry full URLs |
| Quick Navigation section | ✅ | Lines 32-44; all blueprint links present |
| ✅ Always Do section | ✅ | Lines 48-72 |
| ⚠️ Ask First section | ✅ | Lines 74-83 |
| 🚫 Never Do section | ✅ | Lines 84-99 |
| Quick Reference section | ✅ | Lines 101-119 |
| No absolute paths | ✅ | All links are relative or HTTPS |
| No `.github/` references | ✅ | None found |
| No relative dates ("2 weeks ago") | ✅ | All dates are absolute (2026-10-14) |
| No BOM | ✅ | Not detected |

### 1.3 Blueprint File Inventory

| Blueprint | Present | Lines | <= 160 |
|-----------|---------|-------|--------|
| `always-do-patterns.md` | ✅ | 18 | ✅ |
| `never-do-patterns.md` | ✅ | 20 | ✅ |
| `always-do-foundation.md` | ✅ | 82 | ✅ |
| `always-do-gateways-routing.md` | ✅ | 105 | ✅ |
| `always-do-security.md` | ✅ | 87 | ✅ |
| `always-do-observability-testing.md` | ✅ | 113 | ✅ |
| `never-do-networking.md` | ✅ | 109 | ✅ |
| `never-do-security.md` | ✅ | 116 | ✅ |
| `never-do-provider-migration.md` | ✅ | 100 | ✅ |
| `unverified-and-risks.md` | ✅ | 82 | ✅ |
| `evaluation-scenarios.md` | ✅ | 111 | ✅ |

All 11 blueprints present; all within the 160-line limit.

### 1.4 Evaluation Scenarios

| Check | Result | Notes |
|-------|--------|-------|
| >= 3 scenarios | ✅ | 4 scenarios |
| Canonical scenario | ✅ | Scenario 1: Multi-AZ VPC with Zonal NAT |
| Edge case scenario | ✅ | Scenario 2: Regional NAT Constraints |
| Misuse rejection scenario | ✅ | Scenario 3: Mixing SG Rule Mechanisms |
| Anti-pattern trap scenario | ✅ | Scenario 4: Removed Arguments |
| JSON format with `success_criteria` | ✅ | All 4 |
| `must_pass` array present | ✅ | All 4 |
| `must_not` array present | ✅ | All 4 |
| Deterministic and judgeable | ✅ | Criteria are specific and verifiable |

---

## 2. Fact Fidelity — 30 Claims Sampled

All claims compared against `research_AWS_VPC_tf-aws-v6.md` (2026-10-14).

| # | Claim (file: line) | Research reference | Verdict |
|---|--------------------|--------------------|---------|
| C1 | Terraform CLI 1.16.6 current stable (SKILL.md: 16) | Research §1: "1.16.6 (released 2026-10-14)" | ✅ |
| C2 | 1.17.0-rc2 exists — do not target (SKILL.md: 16) | Research §1: "1.17.0-rc2 exists — do not target" | ✅ |
| C3 | hashicorp/aws 6.69.0 current (SKILL.md: 17) | Research §1: "6.69.0 (released 2026-10-14), latest" | ✅ |
| C4 | 6.70.0 "Unreleased" (SKILL.md: 17) | Research §1: "6.70.0 'Unreleased'" | ✅ |
| C5 | 6.57.0 withdrawn from GitHub and Registry (SKILL.md: 19) | Research §1: "6.57.0 pulled from GitHub and the Registry" | ✅ |
| C6 | v7 planned; upgrade guide lists removals (SKILL.md: 18) | Research §1: "Not released... Upgrade guide mentions 'removed in v7.0.0'" | ✅ |
| C7 | Provider constraint `~> 6.69` root; `>= 6.0` reusable (SKILL.md: 20) | Research §1: "root modules should use `~>`... reusable modules should set only a minimum (`>=`)" | ✅ |
| C8 | `use_lockfile = true` — `dynamodb_table` deprecated (SKILL.md: 52) | Research §7: "`dynamodb_table` is deprecated ('will be removed in a future minor version')" | ✅ |
| C9 | `domain = "vpc"` required — `vpc` arg removed in 6.0 (SKILL.md: 54) | Research §3: "`aws_eip`: `vpc` argument removed → use `domain = 'vpc'`" | ✅ |
| C10 | `aws_security_group_rule` discouraged, NOT deprecated (SKILL.md: 57) | Research §5: "discouraged ('Avoid'), NOT deprecated — the word 'deprecated' does not appear" | ✅ |
| C11 | `aws_vpc_security_group_ingress_rule`/`egress_rule` current best practice (SKILL.md: 56-58) | Research §5: "documented 'current best practice', one CIDR per rule" | ✅ |
| C12 | Terraform removes AWS default allow-all egress on create (SKILL.md: 59-60) | Research §5: "Terraform removes the AWS default allow-all egress on create" | ✅ |
| C13 | Security Hub EC2.2 — default SG must allow no traffic (SKILL.md: 61-62) | Research §5: "EC2.2 (High) default SG must allow no traffic" | ✅ |
| C14 | Security Hub EC2.6 checks REJECT traffic (SKILL.md: 63-64) | Research §5: "EC2.6 (Medium) VPC flow logs enabled (checks REJECT)" | ✅ |
| C15 | `log_group_name` removed in 6.0 (SKILL.md: 66) | Research §3: "`aws_flow_log`: `log_group_name` removed → use `log_destination`" | ✅ |
| C16 | `availability_mode = "zonal"` default; `subnet_id` + `allocation_id` required (SKILL.md Quick Ref: 112) | Research §4: "`availability_mode` default `'zonal'`... Zonal: `subnet_id` required; `allocation_id` required when `connectivity_type = 'public'`" | ✅ |
| C17 | Regional NAT: `vpc_id` required; no `subnet_id`/`allocation_id`; public only (SKILL.md Quick Ref: 113) | Research §4: "Regional: `vpc_id` required; `subnet_id`/`allocation_id` must NOT be set; `connectivity_type` must be `public`" | ✅ |
| C18 | Gateway endpoints: S3 and DynamoDB only; no charge (SKILL.md: 117) | Research §6: "Gateway endpoints: S3 and DynamoDB only; no charge" | ✅ |
| C19 | Flow log IAM trust: `vpc-flow-logs.amazonaws.com` + SourceAccount/SourceArn (SKILL.md: 118) | Research §6: "trust `vpc-flow-logs.amazonaws.com`; add `aws:SourceAccount` + `aws:SourceArn`" | ✅ |
| C20 | CI pipeline: `init -backend=false`, `validate -json`, `plan -detailed-exitcode -input=false -out=tfplan` (SKILL.md: 119) | Research §7: "init -backend=false... -json... -detailed-exitcode... -input=false" | ✅ |
| C21 | `aws_default_security_group` immediately removes all rules (always-do-security.md: 40) | Research §5: "adopts the default SG and immediately removes all rules" | ✅ |
| C22 | Regional NAT not available in constrained AZs; up to 60 min to expand to new AZ (always-do-gateways.md: 43-44) | Research §4 (AWS guidance): "not in constrained AZs... up to 60 min to expand to a new AZ" | ✅ |
| C23 | `ip_protocol = "-1"` — do not set `from_port`/`to_port` (always-do-security.md: 32) | Research §5: "with `ip_protocol = '-1'` do not set `from_port`/`to_port`" | ✅ |
| C24 | `aws_vpc_block_public_access_options` — deleting sets mode to `off`; account+region scope (SKILL.md Ask First: 81) | Research §5: "deleting sets `off`... account+region scope" | ✅ |
| C25 | Mixing inline route blocks with aws_route "will overwrite rules" (never-do-networking.md: 8) | Research §4: "'conflict of rule settings and will overwrite rules'" | ✅ |
| C26 | NAT ID in `gateway_id` causes permanent diff; only IGW/VGW in `gateway_id` (never-do-networking.md: 38-39) | Research §4: "Putting a NAT ID in `gateway_id` causes a permanent diff — use `nat_gateway_id` (only IGW/VGW IDs belong in `gateway_id`)" | ✅ |
| C27 | Security Hub EC2.13/14/53/54 — no SSH/RDP from 0.0.0.0/0 or ::/0 (never-do-security.md: 97-98) | Research §5: "EC2.13 / EC2.14 (High) no 0.0.0.0/0 or ::/0 to 22 / 3389. EC2.53 / EC2.54 (High) no 0.0.0.0/0 / ::/0 to 22/3389" | ✅ |
| C28 | `aws_vpc_ipam` `tier` default `advanced` (`free`|`advanced`) (not in SKILL.md; research §6 only) | Not carried into skill — correctly scoped out | ✅ |
| C29 | `depends_on` IGW documented requirement for NAT/EIP (always-do-gateways.md: 10-11) | Research §4: "Public NAT: explicit `depends_on` on the IGW" and §4 aws_internet_gateway: "Docs recommend instances/EIPs `depends_on` the IGW" | ✅ |
| C30 | `aws_network_acl_rule` uses `rule_number` and `rule_action` (never-do-security.md: 65-67) | Research §5: "`aws_network_acl_rule`: `network_acl_id`, `rule_number`, `protocol`, `rule_action`" | ✅ |

**Result: 0 hallucinations, 0 contradictions across 30 sampled claims.**

---

## 3. HCL Correctness

### 3.1 Argument Name Verification

| Argument | Resource | Expected (from research) | Found in HCL | Verdict |
|----------|----------|--------------------------|--------------|---------|
| `availability_mode` | `aws_nat_gateway` | `"zonal"` \| `"regional"` | `"zonal"` (always-do-gateways §3), `"regional"` (§4) | ✅ |
| `ip_protocol` | `aws_vpc_security_group_ingress_rule` | required field | `"tcp"`, `"-1"` used correctly | ✅ |
| `cidr_ipv4` | `aws_vpc_security_group_ingress_rule` | exactly one of `cidr_ipv4`\|`cidr_ipv6`\|`prefix_list_id`\|`referenced_security_group_id` | `cidr_ipv4` used | ✅ |
| `log_destination` | `aws_flow_log` | ARN (not name) | `aws_cloudwatch_log_group.flow_logs.arn` | ✅ |
| `log_destination_type` | `aws_flow_log` | `"cloud-watch-logs"` | `"cloud-watch-logs"` | ✅ |
| `use_lockfile` | S3 backend | `true` | `use_lockfile = true` | ✅ |
| `domain` | `aws_eip` | `"vpc"` | `domain = "vpc"` | ✅ |
| `rule_number` | `aws_network_acl_rule` | `rule_number` (not `rule_no`) | `rule_number = 100` (correct block); `rule_no` only in WRONG block for `aws_network_acl` inline | ✅ |
| `rule_action` | `aws_network_acl_rule` | `rule_action` (not `action`) | `rule_action = "allow"` in correct block; `action` only in WRONG inline block | ✅ |
| `vpc_id` | `aws_nat_gateway` (regional) | required for regional | `vpc_id = aws_vpc.main.id` | ✅ |

### 3.2 Removed / Deprecated Arguments

| Argument | Status | Appears in WRONG block | Appears in correct examples | Verdict |
|----------|--------|----------------------|-----------------------------|---------|
| `aws_eip.vpc` | Removed in 6.0 | ✅ yes (never-do-provider-migration §1) | No | ✅ |
| `aws_flow_log.log_group_name` | Removed in 6.0 | ✅ yes (never-do-provider-migration §2) | No | ✅ |
| `backend.dynamodb_table` | Deprecated | ✅ yes (never-do-provider-migration §3) | No | ✅ |
| `aws_security_group_rule` | Discouraged | ✅ yes (never-do-security §1 WRONG block) | No | ✅ |

### 3.3 .tftest.hcl Structure

| Check | Expected (research §7) | Found | Verdict |
|-------|------------------------|-------|---------|
| File location | `tests/*.tftest.hcl` | `tests/vpc.tftest.hcl` (comment) | ✅ |
| `mock_provider` block | Top-level | `mock_provider "aws" {}` | ✅ |
| `run` block | `run "name" { command = plan; assert {...} }` | Three run blocks with `command = plan` | ✅ |
| `assert` structure | `condition`, `error_message` | Both fields present | ✅ |
| `variables` block | Top-level or in `run` | Top-level `variables { vpc_cidr = ... }` | ✅ |

### 3.4 Source Attribution Inconsistency

`never-do-networking.md` line 47 cites `route_table.html.markdown` as the source for the "NAT ID in `gateway_id` causes permanent diff" anti-pattern. SKILL.md line 93 correctly cites `route.html.markdown` (the `aws_route` resource docs). Research §4 documents this under `aws_route`. The blueprint source citation is wrong.

See **F-L1**.

---

## 4. Tag and Register Consistency

### 4.1 Confidence Tags in Skill and Blueprints

| Tag found | File | Line | Register ID | In mapping table? |
|-----------|------|------|-------------|-------------------|
| `(unverified)` | always-do-security.md | 86 | U5 | ✅ yes |

No other inline confidence tags `(unverified)` or `(medium confidence)` appear in SKILL.md or any blueprint. U1–U4, U6, M1, M2 live only in `unverified-and-risks.md` as register entries, not as inline tags in the skill body. This is correct — register entries document research-level uncertainty; only claims promoted into the skill body need inline tags.

### 4.2 Tag to Register Mapping Accuracy

| Mapping row | `Tag text` | `Where` in mapping | Actual location | Verdict |
|-------------|------------|---------------------|-----------------|---------|
| U5 | `(unverified)` | "SKILL.md §8 note + always-do-security.md §8" | `always-do-security.md` line 86 only; SKILL.md has no §8 | ⚠️ F-M2 |
| M1 | `(medium confidence)` | Version-lifetime risk section | Correct — `unverified-and-risks.md` version-lifetime risk | ✅ |
| M2 | `(medium confidence)` | Version-lifetime risk section | Correct — `unverified-and-risks.md` version-lifetime risk | ✅ |

### 4.3 Bold / Bracket Tag Check

`never-do-security.md` line 9 uses `**discouraged**` (bold). This bold is emphasis on the word "discouraged" as a factual distinction from "deprecated" — it is not a confidence tag. The tag notation policy prohibits bold for confidence tags only. This usage is acceptable.

No `[unverified]` bracket tags found anywhere. ✅

### 4.4 Register Sections Check

`unverified-and-risks.md` sections present: Version-lifetime risk ✅, Unverified Items (U1–U6) ✅, Medium-Confidence Items (M1–M2) ✅, Coverage Limits (L1–L3) ✅, Tag to Register Mapping ✅, Source Bibliography ✅.

ID format: U1/U2.../U6, M1/M2, L1/L2/L3 — all correct, no `U-1` or `MC1` variants. ✅

---

## 5. Evaluation Scenarios

| Scenario | Type | JSON | `success_criteria` | `must_pass` | `must_not` | Deterministic |
|----------|------|------|--------------------|-------------|------------|---------------|
| 1 — Multi-AZ VPC with Zonal NAT | Canonical | ✅ | ✅ | 10 items | 5 items | ✅ |
| 2 — Regional NAT Constraints | Edge case | ✅ | ✅ | 6 items | 3 items | ✅ |
| 3 — Mixing SG Rule Mechanisms | Misuse rejection | ✅ | ✅ | 4 items | 3 items | ✅ |
| 4 — Removed Args + Deprecated Backend | Anti-pattern trap | ✅ | ✅ | 4 items | 3 items | ✅ |

All 4 scenarios meet the minimum of 3; all include the four required types (canonical, edge, rejection, trap). Criteria are specific and free of ambiguity. ✅

---

## Findings

### MEDIUM Findings

**F-M1 — Version suffix format deviates from -vMAJOR-MINOR convention**
- File: `SKILL.md` (frontmatter `name`), `always-do-patterns.md` (title), `never-do-patterns.md` (title)
- Line: SKILL.md line 2
- Detail: The hybrid-format-checklist and CLAUDE.md naming conventions specify `-vMAJOR-MINOR` (e.g., `developing-camel-quarkus-core-v3-40`). This skill uses `-v6` (major-only). SKILL.md line 29 documents the intent: "this skill locks to the 6.x major line (suffix -v6), A new major is a new skill." The design is deliberate but contradicts the prescribed format. When the team reviews naming conventions for major-line skills (as opposed to minor-pinned skills), this should be resolved either by updating the convention to allow `-vMAJOR` for major-line locks, or by renaming to `-v6-x` to make the major-line intent explicit.
- Fix: Either (a) rename to `provisioning-aws-vpc-v6-x` to be explicit about major-line tracking, or (b) amend the policy document to canonically allow `-vMAJOR` for provider-major-line skills. Do not do this silently — the name is embedded in scenario 1 `"skills": ["provisioning-aws-vpc-v6"]` and in every blueprint header.

**F-M2 — Tag to Register Mapping "Where" column has incorrect location for (unverified)**
- File: `blueprints/unverified-and-risks.md`
- Line: 47
- Detail: The mapping row for `(unverified)` / U5 says "SKILL.md §8 note + always-do-security.md §8". SKILL.md has no §8 section — it uses plain heading names (Version Context, Blueprints & Guardrails, Quick Reference, etc.). The `(unverified)` tag appears only at `always-do-security.md` line 86 under "§8. Gateway and Interface Endpoints".
- Fix: Change the `Where` value to `always-do-security.md §8 — Gateway and Interface Endpoints (line 86)`.

### LOW Findings

**F-L1 — Incorrect source URL in never-do-networking.md for NAT-in-gateway_id anti-pattern**
- File: `blueprints/never-do-networking.md`
- Line: 47
- Detail: `# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route_table.html.markdown`. The "NAT ID in `gateway_id` permanent diff" anti-pattern is documented in `aws_route` docs (`route.html.markdown`), not `route_table.html.markdown`. SKILL.md line 93 correctly cites `route.html.markdown` for this claim.
- Fix: Replace `route_table.html.markdown` with `route.html.markdown` at line 47 of `never-do-networking.md`.

**F-L2 — Quick Reference table uses abbreviated source descriptions instead of full URLs**
- File: `SKILL.md`
- Lines: 110, 111, 112, 114
- Detail: Four rows in the Quick Reference table use informal descriptions instead of full URLs: "version-6-upgrade guide" (EIP, flow log rows), "aws_nat_gateway docs" (Zonal NAT row), "aws_security_group docs" (SG egress row). The evidence rule states every claim should link to a dated official source. The full URLs are available in the research file and are cited in the blueprints.
- Fix (optional): Replace abbreviated descriptions with full `https://raw.githubusercontent.com/...` URLs, matching the references already used in the corresponding blueprints.

---

## Checklist Sign-Off

| Dimension | Status |
|-----------|--------|
| Hybrid format compliance | ✅ Pass (1 MEDIUM: version suffix) |
| SKILL.md structure and length | ✅ Pass |
| Blueprint inventory (11 files, all <= 160 lines) | ✅ Pass |
| Fact fidelity (30/30 claims confirmed) | ✅ Pass — 0 hallucinations |
| HCL argument correctness | ✅ Pass (1 LOW: source citation mismatch) |
| No deprecated/removed args in correct examples | ✅ Pass |
| .tftest.hcl structure valid | ✅ Pass |
| Tag notation (plain parentheses, no bold/bracket tags) | ✅ Pass |
| Tag to Register Mapping coverage | ⚠️ Pass with caveat (F-M2: "Where" error) |
| Register ID format (U#, M#, L#) | ✅ Pass |
| Evaluation scenarios (>= 3, JSON, must_pass/must_not) | ✅ Pass — 4 scenarios |
