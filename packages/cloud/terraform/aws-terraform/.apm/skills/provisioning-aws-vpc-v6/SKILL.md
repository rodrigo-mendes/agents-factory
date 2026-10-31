---
name: provisioning-aws-vpc-v6
description: "VPC Terraform (aws 6.x): VPC, subnets, IGW, NAT, route tables, security groups, NACLs, endpoints, flow logs. Use when writing HCL for VPC networking. Not for Route 53, CloudFront, ACM, Transit Gateway."
---

# Provisioning AWS VPC with Terraform — hashicorp/aws 6.x

> Version lock: every claim applies to **hashicorp/aws 6.x** (reference 6.69.0) + **Terraform ~> 1.16** only.
> Research date **2026-10-14**. Claims tagged (unverified) or (medium confidence) were not fully confirmed
> against an official page.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Terraform CLI | **1.16.6** — current stable; 1.17.0-rc2 exists, do not target | https://releases.hashicorp.com/terraform/ |
| hashicorp/aws | **6.69.0** — current; 6.70.0 "Unreleased" | https://github.com/hashicorp/terraform-provider-aws/releases |
| aws v7 | Not released — v7 planned; upgrade guide lists removals | https://releases.hashicorp.com/terraform-provider-aws/ |
| 6.57.0 | **Withdrawn** from GitHub and Registry — never pin | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |
| Provider constraint | `~> 6.69` (root modules); `>= 6.0` (reusable modules) | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| CLI constraint | `~> 1.16` | https://developer.hashicorp.com/terraform/language/terraform |

**Version-lifetime risk** (details in [unverified-and-risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)):
- 1.17.0-rc2 exists; do not target it. Re-verify when starting new work.
- 6.57.0 is permanently withdrawn; any pinned constraint that includes it will fail init.
- v7 is planned; breaking changes documented in the v6 upgrade guide already mention v7 removals.

**Version lock:** this skill locks to the **6.x major line** (suffix `-v6`), reference 6.69.0.
A new major is a new skill.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- Foundation patterns: [terraform block + backend, VPC + subnets](./blueprints/always-do-foundation.md)
- Gateway/routing patterns: [IGW, NAT, route tables](./blueprints/always-do-gateways-routing.md)
- Security patterns: [SGs, default SG, endpoints](./blueprints/always-do-security.md)
- Observability/testing: [flow logs, terraform test, CI](./blueprints/always-do-observability-testing.md)
- Never-do networking: [routes, NAT, endpoints](./blueprints/never-do-networking.md)
- Never-do security: [SG/NACL rules, SSH/RDP](./blueprints/never-do-security.md)
- Never-do provider/migration: [removed args, deprecated backend, withdrawn version](./blueprints/never-do-provider-migration.md)
- [Unverified claims and risks](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Use `~> 6.69` (root) or `>= 6.0` (module) and `~> 1.16` for the CLI constraint** in every `terraform {}` block.
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend).
- **Use `use_lockfile = true` on the S3 backend** — `dynamodb_table` is deprecated and will be removed.
  See [foundation §1](./blueprints/always-do-foundation.md#1-terraform-block-and-s3-backend).
- **Set `domain = "vpc"` on every `aws_eip`** — the `vpc` argument was removed in 6.0.
  See [gateways §3](./blueprints/always-do-gateways-routing.md#3-igw-and-zonal-nat-per-az).
- **Use `aws_vpc_security_group_ingress_rule` / `aws_vpc_security_group_egress_rule`** — the
  current documented best practice, one CIDR per rule. `aws_security_group_rule` is discouraged, not deprecated.
  See [security §6](./blueprints/always-do-security.md#6-security-groups).
- **Add explicit egress on every `aws_security_group`** — Terraform removes the AWS default allow-all
  egress on create. See [security §6](./blueprints/always-do-security.md#6-security-groups).
- **Lock down the default SG with `aws_default_security_group` (no rules)** — satisfies Security Hub EC2.2.
  See [security §7](./blueprints/always-do-security.md#7-default-sg-lockdown).
- **Enable flow logs** on every VPC (Security Hub EC2.6 checks REJECT traffic).
  See [observability §9](./blueprints/always-do-observability-testing.md#9-flow-logs).
- **Use `log_destination` (log group ARN) + `log_destination_type = "cloud-watch-logs"`** for flow
  logs — `log_group_name` was removed in 6.0. See [observability §9](./blueprints/always-do-observability-testing.md#9-flow-logs).
- **Separate `aws_route` resources; never mix with inline `route` blocks** in the same route table.
  See [gateways §5](./blueprints/always-do-gateways-routing.md#5-route-tables-and-separate-routes).
- **Add `depends_on` the IGW for NAT gateways and EIPs** — documented requirement.
  See [gateways §3](./blueprints/always-do-gateways-routing.md#3-igw-and-zonal-nat-per-az).
- **Run `terraform test` with `mock_provider "aws"` and `command = plan`** for CI-safe unit tests.
  See [observability §10](./blueprints/always-do-observability-testing.md#10-terraform-test-and-ci).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Zonal vs regional NAT | Zonal: one NAT per AZ, traffic stays in AZ (HA, no cross-AZ data transfer cost); Regional: single NAT ID in all route tables, expands automatically, public only, up to 60 min to add a new AZ, not available in constrained AZs. ([source](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html)) | "Should NAT be zonal (one per AZ, resilient) or regional (simpler routing, automatic expansion)?" |
| Flow log destination | CloudWatch: real-time, query with Logs Insights, IAM role required; S3: parquet format with `destination_options`, cheaper long-term retention, no IAM role. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/flow_log.html.markdown)) | "Should flow logs go to CloudWatch (real-time queries) or S3 (parquet, cheaper)?" |
| IPv6 / dual-stack | `assign_generated_ipv6_cidr_block` on VPC (/56 Amazon), `ipv6_cidr_block` (/64) on subnets, `aws_egress_only_internet_gateway` for outbound-only IPv6. Conflicts with `ipv6_ipam_pool_id`. | "Does this VPC need IPv6 or dual-stack? If yes, confirm IPAM or Amazon-assigned /56." |
| VPC Block Public Access | `aws_vpc_block_public_access_options` sets `internet_gateway_block_mode` — applies **account-wide + region-wide**; deleting the resource sets mode to `off`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_block_public_access_options.html.markdown)) | "Should VPC Block Public Access be enabled? Confirm the account-level blast radius is acceptable." |
| Adopting default SG / NACL | `aws_default_security_group` immediately removes all existing rules on adopt. `aws_default_network_acl` removes all rules first; subnets cannot be removed, only reassigned. | "Will adopting the default SG or NACL disrupt existing workloads in this account?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Mix inline `route` blocks in `aws_route_table` with separate `aws_route` resources — "will overwrite rules". ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route_table.html.markdown)) | Use only `aws_route` resources; set `route = []` in `aws_route_table` or omit `route` |
| Mix inline `ingress`/`egress` blocks, `aws_security_group_rule`, and `aws_vpc_security_group_ingress_rule`/`egress_rule` on one SG — "rule conflicts, perpetual differences, and result in rules being overwritten". `aws_security_group_rule` is discouraged, not deprecated. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/security_group_rule.html.markdown)) | Use only `aws_vpc_security_group_ingress_rule` + `aws_vpc_security_group_egress_rule` |
| Mix inline `rule` blocks in `aws_network_acl` with `aws_network_acl_rule` resources. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/network_acl.html.markdown)) | Use only `aws_network_acl_rule` resources with `aws_network_acl` |
| Put the same subnet in `aws_network_acl.subnet_ids` and a separate `aws_network_acl_association`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/network_acl.html.markdown)) | Use one mechanism per subnet |
| Combine `secondary_allocation_ids` with `aws_nat_gateway_eip_association` — perpetual diff. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/nat_gateway.html.markdown)) | Use `aws_nat_gateway_eip_association` alone for secondary EIPs |
| Set `gateway_id` on `aws_route` to a NAT gateway ID — permanent diff. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route.html.markdown)) | Use `nat_gateway_id` for NAT; only IGW/VGW IDs belong in `gateway_id` |
| List the same route table in `aws_vpc_endpoint.route_table_ids` and `aws_vpc_endpoint_route_table_association`. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_endpoint.html.markdown)) | Use one mechanism per route table |
| `aws_eip { vpc = true }` — `vpc` argument removed in 6.0. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | `aws_eip { domain = "vpc" }` |
| `aws_flow_log { log_group_name = … }` — removed in 6.0. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown)) | `log_destination` (ARN) + `log_destination_type = "cloud-watch-logs"` |
| S3 backend with `dynamodb_table` — deprecated, will be removed. ([source](https://developer.hashicorp.com/terraform/language/backend/s3)) | `use_lockfile = true` for native S3 locking |
| Pin `version = "6.57.0"` — withdrawn from GitHub and the Registry. ([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md)) | `~> 6.69` or any non-withdrawn patch |
| Open port 22 or 3389 from `0.0.0.0/0` or `::/0` — violates Security Hub EC2.13/EC2.14/EC2.53/EC2.54. ([source](https://docs.aws.amazon.com/securityhub/latest/userguide/ec2-controls.html)) | Restrict SSH/RDP to specific CIDR ranges |

## Quick Reference

Sources fetched 2026-10-14.

| Aspect | Value | Source |
|---|---|---|
| Provider constraint (root) | `~> 6.69` | https://developer.hashicorp.com/terraform/language/expressions/version-constraints |
| CLI constraint | `~> 1.16` | https://developer.hashicorp.com/terraform/language/terraform |
| S3 locking | `use_lockfile = true` (S3 native; `dynamodb_table` deprecated) | https://developer.hashicorp.com/terraform/language/backend/s3 |
| EIP in VPC | `domain = "vpc"` (not `vpc = true` — removed 6.0) | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown |
| Flow log CW destination | `log_destination` (ARN) + `log_destination_type = "cloud-watch-logs"` | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown |
| Zonal NAT default | `availability_mode = "zonal"` (default); `subnet_id` + `allocation_id` required | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/nat_gateway.html.markdown |
| Regional NAT | `availability_mode = "regional"`; `vpc_id` required; no `subnet_id`/`allocation_id`; public only | https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html |
| SG egress default | Terraform removes AWS default allow-all egress on create | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/security_group.html.markdown |
| Security Hub EC2.2 | Default SG must allow no traffic | https://docs.aws.amazon.com/securityhub/latest/userguide/ec2-controls.html |
| Security Hub EC2.6 | VPC flow logs enabled (checks REJECT) | https://docs.aws.amazon.com/securityhub/latest/userguide/ec2-controls.html |
| Gateway endpoints | S3 and DynamoDB only; no charge | https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html |
| Flow log IAM trust | `vpc-flow-logs.amazonaws.com` + SourceAccount/SourceArn conditions | https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-iam-role.html |
| `terraform test` CI | `init -backend=false`, `validate -json`, `plan -detailed-exitcode -input=false -out=tfplan` | https://developer.hashicorp.com/terraform/cli/commands/plan |

## 5.x → 6.x Migration (VPC)

Breaking changes in 6.0.0 that affect VPC work
([source](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown), 2026-10-14):

- **`aws_eip`**: `vpc` argument removed → `domain = "vpc"`.
- **`aws_flow_log`**: `log_group_name` removed → `log_destination` (ARN) + `log_destination_type = "cloud-watch-logs"`.
- No breaking changes for `aws_vpc*`, `aws_subnet`, `aws_security_group*`, `aws_network_acl*`, `aws_route*`.

Upgrade path: move to latest 5.x, get a clean plan, set `~> 6.0`, run `terraform init -upgrade`.
6.48.0 → 6.69.0 contains no VPC-scope breaking changes.

## External Resources

All fetched 2026-10-14.

- Provider releases: https://github.com/hashicorp/terraform-provider-aws/releases
- CHANGELOG: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
- Version 6 upgrade guide: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
- AWS VPC User Guide — NAT gateways: https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html
- AWS VPC User Guide — Regional NAT: https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html
- AWS VPC User Guide — Flow log IAM role: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-iam-role.html
- Security Hub EC2 controls: https://docs.aws.amazon.com/securityhub/latest/userguide/ec2-controls.html
- Terraform S3 backend: https://developer.hashicorp.com/terraform/language/backend/s3
- Terraform test: https://developer.hashicorp.com/terraform/language/tests
- Full bibliography: [unverified-and-risks](./blueprints/unverified-and-risks.md#source-bibliography)
