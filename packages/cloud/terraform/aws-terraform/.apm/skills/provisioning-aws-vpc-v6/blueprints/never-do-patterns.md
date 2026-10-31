# Never-Do Patterns — provisioning-aws-vpc-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-14), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| Inline `route` blocks mixed with `aws_route` | [never-do-networking](./never-do-networking.md#1-mixing-inline-route-blocks-with-aws_route) |
| NAT gateway ID in `gateway_id` (permanent diff) | [never-do-networking](./never-do-networking.md#2-nat-gateway-id-in-gateway_id) |
| `secondary_allocation_ids` with `aws_nat_gateway_eip_association` | [never-do-networking](./never-do-networking.md#3-combining-secondary_allocation_ids-with-aws_nat_gateway_eip_association) |
| Same route table in endpoint `route_table_ids` and an association | [never-do-networking](./never-do-networking.md#4-same-route-table-in-endpoint-route_table_ids-and-association) |
| Mixing inline SG rules, `aws_security_group_rule` and per-direction rules | [never-do-security](./never-do-security.md#1-mixing-security-group-rule-mechanisms) |
| Inline NACL rules mixed with `aws_network_acl_rule` | [never-do-security](./never-do-security.md#2-mixing-inline-nacl-rules-with-aws_network_acl_rule) |
| Same subnet in NACL `subnet_ids` and an association | [never-do-security](./never-do-security.md#3-same-subnet-in-nacl-subnet_ids-and-association) |
| SSH/RDP open to 0.0.0.0/0 or ::/0 (EC2.13/14/53/54) | [never-do-security](./never-do-security.md#4-opening-ssh-or-rdp-from-00000) |
| `aws_eip` with `vpc = true` (removed in 6.0) | [never-do-provider-migration](./never-do-provider-migration.md#1-aws_eip-with-vpc--true) |
| `aws_flow_log` with `log_group_name` (removed in 6.0) | [never-do-provider-migration](./never-do-provider-migration.md#2-aws_flow_log-with-log_group_name) |
| S3 backend with `dynamodb_table` (deprecated) | [never-do-provider-migration](./never-do-provider-migration.md#3-s3-backend-with-dynamodb_table) |
| Pinning withdrawn provider 6.57.0 | [never-do-provider-migration](./never-do-provider-migration.md#4-pinning-version-6570) |
