# Always-Do Patterns — provisioning-aws-vpc-v6

Index of the always-do blueprints, split by topic. Each pattern has complete HCL and cites its
official source (fetched 2026-10-14).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and S3 backend with `use_lockfile` | [always-do-foundation](./always-do-foundation.md#1-terraform-block-and-s3-backend) |
| 2 | VPC and public/private subnets across AZs (`for_each`) | [always-do-foundation](./always-do-foundation.md#2-vpc-and-publicprivate-subnets) |
| 3 | IGW and one zonal NAT per AZ (EIP `domain = "vpc"`, `depends_on`) | [always-do-gateways-routing](./always-do-gateways-routing.md#3-igw-and-zonal-nat-per-az) |
| 4 | Regional NAT alternative (`availability_mode = "regional"`) | [always-do-gateways-routing](./always-do-gateways-routing.md#4-regional-nat-alternative) |
| 5 | Route tables with separate `aws_route` and associations | [always-do-gateways-routing](./always-do-gateways-routing.md#5-route-tables-and-separate-routes) |
| 6 | Security groups with per-direction rule resources and explicit egress | [always-do-security](./always-do-security.md#6-security-groups) |
| 7 | Default security group locked down (Security Hub EC2.2) | [always-do-security](./always-do-security.md#7-default-sg-lockdown) |
| 8 | Gateway (S3/DynamoDB) and interface endpoints | [always-do-security](./always-do-security.md#8-gateway-and-interface-endpoints) |
| 9 | Flow logs with `log_destination` and a scoped IAM role | [always-do-observability-testing](./always-do-observability-testing.md#9-flow-logs) |
| 10 | `terraform test` with `mock_provider` and CI commands | [always-do-observability-testing](./always-do-observability-testing.md#10-terraform-test-and-ci) |
