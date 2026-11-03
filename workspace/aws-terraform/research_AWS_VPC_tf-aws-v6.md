# Research — AWS VPC with Terraform 1.16.x + hashicorp/aws 6.x

> Research date: **2026-10-14**. Status: **COMPLETE** (pilot unit `vpc`, Frente 5).
> Synthesized by the orchestrator from 1 researcher + 4 section investigators (core, security,
> endpoints/flow logs/IPv6/IPAM, Terraform testing) plus an orchestrator version re-check.
> Registry pages (registry.terraform.io) render JS-only; the upstream raw markdown in
> `hashicorp/terraform-provider-aws` (`main`) is used as the authoritative source for resource docs.
> Coverage reference only (not a source): `workspace/terraform/research_AWS_VPC_aws-v6.x.md` (6.47.0, Terraform 1.7 — EOL).

## 1. Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Terraform CLI | **1.16.6** (released 2026-10-14); 1.16.0 released 2026-08-26 | https://releases.hashicorp.com/terraform/ ; https://raw.githubusercontent.com/hashicorp/terraform/v1.16/CHANGELOG.md |
| Terraform pre-release | 1.17.0-rc2 exists — do not target | https://releases.hashicorp.com/terraform/ |
| Previous line | 1.15.9 (2026-08-19) — superseded by 1.16 | https://github.com/hashicorp/terraform/blob/v1.15/CHANGELOG.md |
| hashicorp/aws | **6.69.0** (released 2026-10-14), latest; 6.70.0 "Unreleased" | https://github.com/hashicorp/terraform-provider-aws/releases ; https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md ; https://registry.terraform.io/v1/providers/hashicorp/aws/versions ; https://releases.hashicorp.com/terraform-provider-aws/ |
| aws v7 | Not released (no stable, no pre-release). Upgrade guide mentions items "removed in v7.0.0" → v7 planned | https://releases.hashicorp.com/terraform-provider-aws/ ; https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown |
| aws 6.0.0 release | "18 Jun" on the release page, year read as 2025 (medium confidence) | https://github.com/hashicorp/terraform-provider-aws/releases/tag/v6.0.0 |
| Withdrawn | **6.57.0 pulled** from GitHub and the Registry — never pin it | https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md |

Recommended constraint block (root module):

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }
}
```

- `~>` lets only the rightmost component increment; root modules should use `~>` for both bounds; reusable modules should set only a minimum (`>=`). (https://developer.hashicorp.com/terraform/language/expressions/version-constraints)
- `required_version` constrains the CLI only, must be satisfied across all modules, and the `terraform` block accepts constants only. (https://developer.hashicorp.com/terraform/language/terraform)

## 2. Terraform 1.16 changes relevant to VPC work

From https://raw.githubusercontent.com/hashicorp/terraform/v1.16/CHANGELOG.md (2026-10-14):
- No BREAKING CHANGES section in 1.16.0; one UPGRADE NOTE (`bastion_host_key` now applied by provisioners).
- `import` blocks inside modules are now supported.
- `terraform_data` gains a `store` block that can hold ephemeral and sensitive values across plan and apply.
- Providers can use nested blocks as computed values; planned private data is now stored for providers.
- test: Terraform reports resources left behind when `skip_cleanup` is set; warning when a `-filter` file does not exist.
- Experiments (alpha builds only — do not use): `backend` blocks inside `run`, `skip_cleanup`, `terraform test cleanup`, `-allow-deferral`.
- No 1.16.0 changes to `validate`, the S3 backend or `required_version`.

Carried from 1.15.0 (https://github.com/hashicorp/terraform/blob/v1.15/CHANGELOG.md): variables/locals in module `source`/`version`; `convert` function; `deprecated` attribute on `variable`/`output`; `terraform validate` checks backend type and required attributes; output type constraints; test mock blocks can call functions; S3 backend `AWS_USE_FIPS_ENDPOINT` / `AWS_USE_DUALSTACK_ENDPOINT` accept only `true`/`false` (breaking).

## 3. Provider 6.x changes affecting VPC

6.0.0 breaking changes in VPC scope (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown):
- `aws_eip`: `vpc` argument removed → use `domain = "vpc"`.
- `aws_flow_log`: `log_group_name` removed → use `log_destination` (log group ARN) + `log_destination_type = "cloud-watch-logs"`.
- `aws_instance`: `cpu_core_count`/`cpu_threads_per_core` removed (use `cpu_options`); `user_data` stored cleartext.
- No breaking changes listed for `aws_vpc*`, `aws_subnet`, `aws_security_group*`, `aws_network_acl*`, `aws_route*`.
- Upgrade path: move to latest 5.x, get a clean plan, set `~> 6.0`, run `terraform init -upgrade`. No minimum Terraform version stated.

Per-resource `region` (https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown):
- Every resource accepts optional `region`, defaulting to the provider region.
- Changing `region` forces replacement; removing it does not (prior state value is used).
- Import into a region with `@region` (e.g. `vpc-xxx@eu-west-1`).
- One provider block per region is "not deprecated".
- `aws_vpc_endpoint_service` data source: `region` deprecated in favor of `service_region`.

6.48.0 → 6.69.0, VPC scope (CHANGELOG): no breaking changes.
- 6.48.0 `aws_vpc_ipam_pool_cidr_allocation` tagging (#48084).
- 6.50.0 fix perpetual drift on `aws_route`/`aws_route_table` `gateway_id` with `odb_network_arn` (#48239).
- 6.56.0 `aws_flow_log` `tag_field_specification` (#48913); `aws_subnet` waits for IPAM CIDR release on delete (#46523); `aws_vpc_ipam_pool` cross-account fix (#46483).
- 6.57.0 withdrawn; 6.57.1 `aws_flow_log` list resource + resource identity (#49086); `aws_vpc` data source adds `ipv6_cidr_block_associations`, deprecates `ipv6_association_id`/`ipv6_cidr_block` (#46918).
- 6.61.0 `aws_nat_gateway` in-place update of `secondary_private_ip_address_count` for private NAT (#47477).
- 6.65.0 `aws_network_acl` list resource + identity (#50020).
- 6.67.0 `aws_default_security_group` list resource + identity (#50120).
- 6.68.0 / 6.69.0: Transit Gateway items only.
- Note: 6.53.0–6.55.0 checked with a strict name filter; 6.54.0 only partly visible (coverage limit).

Identity-based import (`identity` block) requires Terraform ≥ 1.12.0 — satisfied by 1.16.

## 4. Core resources

Source for each: `https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/<name>.html.markdown` (2026-10-14).

### aws_vpc
- No required arguments; `cidr_block` explicit or from IPAM (`ipv4_ipam_pool_id` + `ipv4_netmask_length`).
- Defaults: `enable_dns_support = true`, `enable_dns_hostnames = false`, `instance_tenancy = "default"` (`dedicated` costs a per-region fee), `assign_generated_ipv6_cidr_block = false`, `enable_network_address_usage_metrics = false`.
- IPv6: `assign_generated_ipv6_cidr_block` (Amazon /56, conflicts with `ipv6_ipam_pool_id`); `ipv6_netmask_length` 44–60 step 4 (conflicts with `ipv6_cidr_block`).
- On delete, removes GuardDuty-managed endpoints/SGs (tag `GuardDutyManaged=true`); needs `ec2:DescribeVpcEndpoints`, `ec2:DescribeSecurityGroups`, `ec2:DeleteVpcEndpoints`, `ec2:ModifyVpcEndpoint`, `ec2:DeleteSecurityGroup`.
- Import: `vpc-…`; identity import supported.

### aws_subnet
- Required: `vpc_id`. Defaults false: `map_public_ip_on_launch`, `assign_ipv6_address_on_creation`, `ipv6_native`, `enable_dns64`, resource-name DNS A/AAAA on launch.
- `ipv6_cidr_block` must be /64; `ipv6_netmask_length` 44–64 step 4 with `ipv6_ipam_pool_id`.
- For a secondary VPC CIDR, take `vpc_id` from `aws_vpc_ipv4_cidr_block_association` to order correctly.
- Lambda-attached subnets can take up to 45 min to delete (handled by provider ≥ 2.31.0).
- Timeouts: create 10m, delete 20m. Import `subnet-…`.

### aws_internet_gateway
- All optional (`vpc_id`, `tags`, `region`). Docs recommend instances/EIPs `depends_on` the IGW. Import `igw-…`.

### aws_eip
- `domain = "vpc"` for VPC EIPs. Whether `domain` defaults to `"vpc"` when omitted is **not stated** (unverified).
- "EIP may require IGW to exist prior to association. Use `depends_on`."
- Do not associate with `aws_lb`/`aws_nat_gateway` via `network_interface` (AuthFailure) — use the target's `allocation_id`.
- Set `instance` or `network_interface`, not both. Import `eipalloc-…`.

### aws_nat_gateway
- `availability_mode` default `"zonal"`; values `zonal` | `regional`.
- Zonal: `subnet_id` required; `allocation_id` required when `connectivity_type = "public"` (default `public`; also `private`).
- Regional: `vpc_id` required; `subnet_id`/`allocation_id` must NOT be set; `connectivity_type` must be `public`. Optional repeatable `availability_zone_address { allocation_ids, availability_zone | availability_zone_id }` (manual mode); omitting it = automatic mode.
- Adding/removing `availability_zone_address` recreates the regional NAT; moving an allocation between AZs needs two applies.
- Do NOT combine `secondary_allocation_ids` with `aws_nat_gateway_eip_association` (perpetual diff, overwritten associations).
- Public NAT: explicit `depends_on` on the IGW.
- Import `nat-…`.

### aws_nat_gateway_eip_association
- Required `allocation_id`, `nat_gateway_id`. Timeouts create 10m, delete 30m. Import `nat-…,eipalloc-…`.

### aws_route_table / aws_route
- `aws_route_table` requires `vpc_id`; inline `route` omitted = existing routes ignored; `route = []` removes all managed routes.
- **Never mix inline `route` blocks with `aws_route` resources** — "conflict of rule settings and will overwrite rules".
- Putting a NAT ID in `gateway_id` causes a permanent diff — use `nat_gateway_id` (only IGW/VGW IDs belong in `gateway_id`).
- Do not use `propagating_vgws` with `aws_vpn_gateway_route_propagation`.
- `aws_route`: `route_table_id` + one destination (`destination_cidr_block` | `destination_ipv6_cidr_block` | `destination_prefix_list_id`) + one target. For S3 gateway endpoints use `aws_vpc_endpoint_route_table_association`, not `vpc_endpoint_id` + prefix list.
- Import `aws_route`: `rtb-…_10.42.0.0/16`. Timeouts 5m/2m/5m.

### aws_route_table_association / aws_main_route_table_association
- Association: `route_table_id` + one of `subnet_id` | `gateway_id`. Pre-existing association → `Resource.AlreadyAssociated` unless imported. Import `subnet-…/rtb-…`.
- Main association: `route_table_id`, `vpc_id`; on destroy restores `original_route_table_id` (original must still exist). Do not combine with `aws_default_route_table` on the same VPC. **No import section documented** (unverified).

### aws_egress_only_internet_gateway
- Required `vpc_id`. IPv6 outbound-only (blocks inbound-initiated IPv6). Import `eigw-…`.

### AWS guidance — NAT
- Zonal NAT: "create a NAT gateway in each Availability Zone, and configure your routing to ensure that resources use the NAT gateway in the same Availability Zone." 5→100 Gbps, 1M→10M pps, 55,000 simultaneous connections per IP per destination, default 2 EIPs per public NAT, up to 8 IPv4 addresses. (https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html)
- Regional NAT: expands across AZs automatically, no public subnet needed, own route table pre-routed to the IGW, single NAT ID in all route tables, up to 32 IPs per AZ, up to 60 min to expand to a new AZ, no private NAT, not in constrained AZs. (https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html)

## 5. Security controls

Sources: raw resource markdown as in §4; AWS VPC User Guide; Security Hub EC2 controls (all 2026-10-14).

- **Best practice:** `aws_vpc_security_group_ingress_rule` + `aws_vpc_security_group_egress_rule` are the documented "current best practice", one CIDR per rule.
- **`aws_security_group_rule` is discouraged ("Avoid"), NOT deprecated** — the word "deprecated" does not appear. (Corrects the 6.47 reference file.)
- **Never mix** inline `ingress`/`egress`, `aws_security_group_rule`, and per-direction rule resources on one SG: "rule conflicts, perpetual differences, and result in rules being overwritten."
- Per-direction rules: required `security_group_id`, `ip_protocol`; exactly one of `cidr_ipv4` | `cidr_ipv6` | `prefix_list_id` | `referenced_security_group_id`; with `ip_protocol = "-1"` do not set `from_port`/`to_port`.
- `aws_security_group`: Terraform **removes the AWS default allow-all egress** on create — add explicit egress if needed. Removing inline blocks doesn't delete rules (`ingress = []`). `description` defaults to "Managed by Terraform", forces new, has no update API. `name`/`name_prefix`/`vpc_id` force new; SG still attached blocks deletion — use `create_before_destroy` / `replace_triggered_by`. `revoke_rules_on_delete` default false. Timeouts create 10m, delete 15m.
- `aws_vpc_security_group_rules_exclusive`: owns all rules of an SG (`ingress_rule_ids`, `egress_rule_ids` required); removes unlisted rules on apply; destroying it does not revoke rules.
- `aws_default_security_group`: adopts the default SG and **immediately removes all rules**; omitting `egress` = deny all egress; incompatible with `aws_security_group_rule`; removing it from config doesn't destroy the SG.
- `aws_network_acl`: required `vpc_id`; **never mix inline rules with `aws_network_acl_rule`**; never put the same subnet in `subnet_ids` and an association resource. Rule block: `rule_no`, `action`, `protocol`, `from_port`, `to_port`.
- `aws_network_acl_rule`: `network_acl_id`, `rule_number`, `protocol`, `rule_action`; `egress` default false.
- `aws_default_network_acl`: adopts, removes all rules first; empty config denies all; subnets can't be removed, only reassigned (use `ignore_changes = [subnet_ids]` workaround).
- `aws_vpc_block_public_access_options`: `internet_gateway_block_mode` = `block-bidirectional` | `block-ingress` | `off`; account+region scope; deleting sets `off`; timeouts 30m; import by region name.
- `aws_vpc_block_public_access_exclusion`: `internet_gateway_exclusion_mode` = `allow-egress` | `allow-bidirectional`; `vpc_id` or `subnet_id`.
- AWS: SGs are stateful; NACLs stateless, rules 1–32766 lowest-first, number in increments of 10/100; NACLs cannot block Route 53 Resolver (VPC+2) or IMDS; restrict 22/3389 to specific ranges; don't open large port ranges. (https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html ; https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html ; https://docs.aws.amazon.com/vpc/latest/userguide/default-security-group.html)
- Security Hub (https://docs.aws.amazon.com/securityhub/latest/userguide/ec2-controls.html):
  - EC2.2 (High) default SG must allow no traffic — `vpc-default-security-group-closed`.
  - EC2.6 (Medium) VPC flow logs enabled (checks REJECT) — `vpc-flow-logs-enabled`.
  - EC2.13 / EC2.14 (High) no 0.0.0.0/0 or ::/0 to 22 / 3389.
  - EC2.19 (Critical) no unrestricted access to high-risk ports (20-23, 25, 110, 135, 143, 445, 1433-1434, 3000, 3306, 3389, 4333, 5000, 5432, 5500, 5601, 8080, 8088, 8888, 9200, 9300).
  - EC2.53 / EC2.54 (High) no 0.0.0.0/0 / ::/0 to 22/3389 — `vpc-sg-port-restriction-check`.

## 6. Endpoints, flow logs, IPAM

- `aws_vpc_endpoint`: `vpc_id` required; `vpc_endpoint_type` default `Gateway` (`Gateway`, `GatewayLoadBalancer`, `Interface`, `Resource`, `ServiceNetwork`); exactly one of `service_name` | `resource_configuration_arn` | `service_network_arn`. `route_table_ids` (Gateway), `subnet_ids` (Interface/GWLB), `security_group_ids` (Interface; default = VPC default SG), `private_dns_enabled` default false, `policy` default full access, `ip_address_type`, `service_region`, `dns_options`, `subnet_configuration`.
- Gateway endpoints: S3 and DynamoDB only; no charge; AWS-managed prefix-list routes can't be edited; one endpoint route per service per route table. (https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html) Interface endpoint pricing not fetched (unverified).
- **Never** list the same route table in `aws_vpc_endpoint.route_table_ids` and an `aws_vpc_endpoint_route_table_association`.
- `aws_vpc_endpoint_policy`: `vpc_endpoint_id` required, `policy` optional.
- `aws_flow_log`: target one of `vpc_id`, `subnet_id`, `eni_id`, `transit_gateway_id`, `transit_gateway_attachment_id`, `regional_nat_gateway_id`; `traffic_type` (`ACCEPT`|`REJECT`|`ALL`) required for eni/regional NAT/subnet/vpc (TGW requirement not stated — unverified); `log_destination_type` default `cloud-watch-logs` (also `s3`, `kinesis-data-firehose`); `iam_role_arn` required for CloudWatch; `max_aggregation_interval` default 600 (60 for TGW); `destination_options` (`file_format` plain-text|parquet, `hive_compatible_partitions`, `per_hour_partition`); `tag_field_specification`.
- Flow log IAM role: trust `vpc-flow-logs.amazonaws.com`; permissions `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`, `logs:DescribeLogGroups`, `logs:DescribeLogStreams`; add `aws:SourceAccount` + `aws:SourceArn` (`arn:aws:ec2:<region>:<account>:vpc-flow-log/<id>`) conditions. (https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-iam-role.html)
- Flow log limits: configuration immutable (delete + recreate); not captured: Amazon DNS, IMDS 169.254.169.254, Time Sync 169.254.169.123, DHCP, ARP, mirrored source, VPC router reserved IP; Nitro ≤ 1 min aggregation; 250 subscriptions per resource. (https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-limitations.html)
- `aws_vpc_ipam`: `operating_regions` required (must include provider region); `tier` default `advanced` (`free`|`advanced`); `metered_account` default `ipam-owner`; `cascade`.
- `aws_vpc_ipam_pool`: `address_family`, `ipam_scope_id` required; `locale`; `source_ipam_pool_id`; `public_ip_source` default `byoip`; allocation netmask defaults/min/max; `auto_import`.
- `aws_vpc_ipam_pool_cidr`: `ipam_pool_id` required; `cidr` xor `netmask_length`.

## 7. Workflow and testing (Terraform 1.16)

- Lock file `.terraform.lock.hcl`: providers only; commit it; `init` reuses locked version unless `-upgrade`; `terraform providers lock -platform=linux_amd64 …` for cross-platform hashes. (https://developer.hashicorp.com/terraform/language/files/dependency-lock)
- `terraform validate`: syntax + internal consistency, no remote calls; needs `init` (`-backend=false` in CI); `-json` output has `valid`, `error_count`, `warning_count`, `diagnostics`, `format_version "1.0"`. Exit codes not documented (unverified). (https://developer.hashicorp.com/terraform/cli/commands/validate)
- `terraform plan -detailed-exitcode`: 0 no changes, 1 error, 2 changes. `-out=tfplan` (no `.tf` suffix; plan file holds sensitive values in cleartext). `-input=false` for CI. (https://developer.hashicorp.com/terraform/cli/commands/plan)
- `terraform test` (docs show 1.16.x as latest): `.tftest.hcl` in `tests/` by default (`-test-directory`); `run` blocks with `command = apply` (default) or `plan`; `assert { condition, error_message }`; `variables`, `providers`, `expect_failures` (custom conditions only; prefer with `plan`), `module`, `state_key`, `parallel`; resources destroyed in reverse run order; flags `-filter`, `-json`, `-junit-xml` (stable since 1.11), `-verbose`, `-parallelism`. (https://developer.hashicorp.com/terraform/language/tests ; https://developer.hashicorp.com/terraform/cli/commands/test)
- Mocking: `mock_provider` (fake computed values: 0 / false / 8-char string / empty collections), `mock_resource`/`mock_data` defaults, `override_resource`, `override_data`, `override_module`, `override_during`. (https://developer.hashicorp.com/terraform/language/tests/mocking)
- S3 backend: `use_lockfile = true` (default false) writes `<key>.tflock`, needs `s3:GetObject`/`PutObject`/`DeleteObject`; **`dynamodb_table` is deprecated** ("will be removed in a future minor version"); `dynamodb_endpoint` → `endpoints.dynamodb`; both may be set during migration. (https://developer.hashicorp.com/terraform/language/backend/s3) — corrects the 6.47 reference file.

## 8. Unverified / medium-confidence items

- U1 `aws_eip` `domain` default when omitted — not stated; always set `domain = "vpc"`.
- U2 `aws_main_route_table_association` import — no import section documented.
- U3 `aws_flow_log` `traffic_type` requirement for TGW targets — not stated.
- U4 `terraform validate` exit codes — not documented on the command page.
- U5 Interface endpoint pricing — not fetched.
- U6 Terraform support/EOL windows — official support page redirects to IBM portal; only third-party trackers seen.
- M1 aws 6.0.0 release year 2025 (page shows "18 Jun" without year).
- M2 Verbatim warning wording — WebFetch paraphrases; substance confirmed on the raw markdown.
- L1 CHANGELOG 6.53.0–6.55.0 checked with a strict name filter; 6.54.0 only partly visible.
- L2 Registry pages not readable (JS); raw `main` markdown used — may run slightly ahead of 6.69.0.
- L3 `region` introduction in 6.0 confirmed by the enhanced-region-support guide, not by each resource page.

## 9. Security note

- One fetched AWS page (`flow-logs-basics.html`) returned an embedded `system-reminder`-style block that is not AWS documentation; it was disregarded as prompt injection.

## Source Bibliography

All fetched 2026-10-14.

1. https://releases.hashicorp.com/terraform/
2. https://raw.githubusercontent.com/hashicorp/terraform/v1.16/CHANGELOG.md
3. https://github.com/hashicorp/terraform/blob/v1.15/CHANGELOG.md
4. https://github.com/hashicorp/terraform-provider-aws/releases
5. https://github.com/hashicorp/terraform-provider-aws/releases/tag/v6.0.0
6. https://registry.terraform.io/v1/providers/hashicorp/aws/versions
7. https://releases.hashicorp.com/terraform-provider-aws/
8. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
9. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
10. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown
11. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc.html.markdown
12. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/subnet.html.markdown
13. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/internet_gateway.html.markdown
14. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/eip.html.markdown
15. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/nat_gateway.html.markdown
16. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/nat_gateway_eip_association.html.markdown
17. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route_table.html.markdown
18. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route.html.markdown
19. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route_table_association.html.markdown
20. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/main_route_table_association.html.markdown
21. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/egress_only_internet_gateway.html.markdown
22. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/security_group.html.markdown
23. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_security_group_ingress_rule.html.markdown
24. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_security_group_egress_rule.html.markdown
25. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/security_group_rule.html.markdown
26. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_security_group_rules_exclusive.html.markdown
27. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/default_security_group.html.markdown
28. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/network_acl.html.markdown
29. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/network_acl_rule.html.markdown
30. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/default_network_acl.html.markdown
31. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_block_public_access_options.html.markdown
32. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_block_public_access_exclusion.html.markdown
33. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_endpoint.html.markdown
34. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_endpoint_route_table_association.html.markdown
35. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_endpoint_policy.html.markdown
36. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/flow_log.html.markdown
37. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_ipam.html.markdown
38. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_ipam_pool.html.markdown
39. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_ipam_pool_cidr.html.markdown
40. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_encryption_control.html.markdown
41. https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html
42. https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html
43. https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html
44. https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html
45. https://docs.aws.amazon.com/vpc/latest/userguide/default-security-group.html
46. https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html
47. https://docs.aws.amazon.com/securityhub/latest/userguide/ec2-controls.html
48. https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html
49. https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html
50. https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-iam-role.html
51. https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-limitations.html
52. https://developer.hashicorp.com/terraform/language/terraform
53. https://developer.hashicorp.com/terraform/language/expressions/version-constraints
54. https://developer.hashicorp.com/terraform/language/files/dependency-lock
55. https://developer.hashicorp.com/terraform/cli/commands/validate
56. https://developer.hashicorp.com/terraform/cli/commands/plan
57. https://developer.hashicorp.com/terraform/language/tests
58. https://developer.hashicorp.com/terraform/cli/commands/test
59. https://developer.hashicorp.com/terraform/language/tests/mocking
60. https://developer.hashicorp.com/terraform/language/backend/s3
