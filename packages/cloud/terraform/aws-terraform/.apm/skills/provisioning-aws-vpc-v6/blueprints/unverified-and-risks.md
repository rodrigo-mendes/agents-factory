# Unverified Claims and Risks — hashicorp/aws 6.x VPC

Research date 2026-10-14. See SKILL.md for inline source URLs per claim.

## Version-lifetime risk

- **hashicorp/aws 6.x is the current stable major** as of 2026-10-14 (reference 6.69.0). Re-verify when
  starting new work or after 30 days. Source: https://github.com/hashicorp/terraform-provider-aws/releases
- **Terraform 1.16.6** is the current stable CLI. **1.17.0-rc2** exists — do not target it.
  Source: https://releases.hashicorp.com/terraform/
- **6.57.0 is permanently withdrawn** from GitHub and the Registry. Any constraint resolving to it
  fails `terraform init`.
- **v7 is planned** — upgrade guide already documents items "removed in v7.0.0". When v7 ships,
  create a new skill `provisioning-aws-vpc-v7`.
- **aws 6.0.0 release year** is (medium confidence) 2025 — GitHub page showed "18 Jun" without year (M1).

## Unverified Items

| Tag | Item | Status |
|---|---|---|
| U1 | `aws_eip` `domain` default when omitted — not stated in docs | (unverified) — always set `domain = "vpc"` explicitly |
| U2 | `aws_main_route_table_association` import — no import section documented | (unverified) — import behavior not confirmed |
| U3 | `aws_flow_log` `traffic_type` requirement for Transit Gateway targets — not stated | (unverified) — always set `traffic_type` for eni/regional NAT/subnet/vpc targets |
| U4 | `terraform validate` exit codes — not documented on the validate command page | (unverified) — use `-json` output fields for programmatic checks |
| U5 | Interface endpoint pricing — not fetched during research | (unverified) — check https://aws.amazon.com/privatelink/pricing/ |
| U6 | Terraform support/EOL windows — official page redirects to IBM portal; only third-party trackers seen | (unverified) |

## Medium-Confidence Items

| Tag | Item | Status |
|---|---|---|
| M1 | aws 6.0.0 release year — page shows "18 Jun" without year; read as 2025 | (medium confidence) — breaking changes confirmed via upgrade guide |
| M2 | Verbatim wording of provider warnings — WebFetch paraphrases; substance confirmed on raw markdown | (medium confidence) — use raw markdown source URLs to verify exact wording |

## Coverage Limits

| Tag | Item |
|---|---|
| L1 | CHANGELOG 6.53.0–6.55.0 checked with strict name filter; 6.54.0 only partly visible |
| L2 | Registry pages JS-only; raw `main` branch used — may run slightly ahead of 6.69.0 |
| L3 | Per-resource `region` attribute confirmed by enhanced-region-support guide, not by each resource page |

## Tag to Register Mapping

| Tag text | Where | Register id |
|---|---|---|
| (unverified) | always-do-security.md §8 Gateway and Interface Endpoints — interface endpoint pricing | U5 |
| (medium confidence) | Version-lifetime risk section above — 6.0.0 release year | M1 |
| (medium confidence) | Version-lifetime risk section above — verbatim warning wording | M2 |

## Source Bibliography

All fetched 2026-10-14. Numbers match the original research bibliography.

1. https://releases.hashicorp.com/terraform/ — Terraform 1.16.6 stable; 1.17.0-rc2 pre-release
2. https://raw.githubusercontent.com/hashicorp/terraform/v1.16/CHANGELOG.md — 1.16.x change list
3. https://github.com/hashicorp/terraform-provider-aws/releases — 6.69.0 current; 6.0.0 release label
4. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md — 6.57.0 withdrawn; VPC changes 6.48–6.69
5. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown — aws_eip vpc removed; flow_log log_group_name removed
6. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown — per-resource region behavior
7–21. Resource docs (aws_vpc, aws_subnet, aws_internet_gateway, aws_eip, aws_nat_gateway, aws_nat_gateway_eip_association, aws_route_table, aws_route, aws_route_table_association, aws_egress_only_internet_gateway, aws_security_group, aws_vpc_security_group_ingress_rule, aws_vpc_security_group_egress_rule, aws_security_group_rule, aws_vpc_security_group_rules_exclusive) — pattern at: `https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/<name>.html.markdown`
22. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/default_security_group.html.markdown — adopts default SG, removes all rules
23. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/network_acl.html.markdown — NACL inline/resource conflict; subnet_ids conflict
24. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_endpoint.html.markdown — route_table_ids + association conflict; endpoint types
25. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/flow_log.html.markdown — log_destination; iam_role_arn; destination_options
26. https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_block_public_access_options.html.markdown — account+region scope
27. https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html — zonal NAT guidance; EIP limits
28. https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html — regional NAT constraints; 60 min AZ expansion
29. https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-iam-role.html — IAM trust; SourceAccount/SourceArn conditions
30. https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-limitations.html — immutable config; not-captured traffic
31. https://docs.aws.amazon.com/securityhub/latest/userguide/ec2-controls.html — EC2.2/6/13/14/19/53/54
32. https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html — S3+DynamoDB only; no charge
33. https://developer.hashicorp.com/terraform/language/expressions/version-constraints — ~> semantics
34. https://developer.hashicorp.com/terraform/language/terraform — required_version; constants only
35. https://developer.hashicorp.com/terraform/language/backend/s3 — use_lockfile; dynamodb_table deprecated
36. https://developer.hashicorp.com/terraform/language/files/dependency-lock — commit lock file; cross-platform hashes
37. https://developer.hashicorp.com/terraform/cli/commands/validate — -json output; requires init
38. https://developer.hashicorp.com/terraform/cli/commands/plan — -detailed-exitcode (0/1/2); -out; -input=false
39. https://developer.hashicorp.com/terraform/language/tests — .tftest.hcl; run blocks; assert; mock_provider
40. https://developer.hashicorp.com/terraform/cli/commands/test — -filter; -json; -junit-xml; -verbose
41. https://developer.hashicorp.com/terraform/language/tests/mocking — mock_provider; mock_resource; override_resource
