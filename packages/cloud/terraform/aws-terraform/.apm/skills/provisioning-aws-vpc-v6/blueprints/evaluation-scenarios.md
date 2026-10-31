# Evaluation Scenarios — provisioning-aws-vpc-v6

Four scenarios required for a hybrid knowledge skill (canonical, edge, misuse rejection, anti-pattern trap).
Each scenario uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Multi-AZ VPC with Zonal NAT

```json
{
  "skills": ["provisioning-aws-vpc-v6"],
  "query": "Generate Terraform for a 3-AZ VPC with public and private subnets, an internet gateway, one NAT gateway per AZ, and route tables. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69 (or >=6.0)",
      "Uses use_lockfile = true in the S3 backend; does not include dynamodb_table",
      "Sets domain = \"vpc\" on every aws_eip (not vpc = true)",
      "Uses availability_mode = \"zonal\" (or omits it, as it is the default) for NAT gateways",
      "Uses nat_gateway_id on aws_route for the NAT route (not gateway_id)",
      "Does not mix inline route blocks in aws_route_table with aws_route resources",
      "Adds depends_on the IGW for NAT gateways and EIPs",
      "Locks down the default SG with aws_default_security_group (no rules) for EC2.2",
      "Uses aws_vpc_security_group_ingress_rule and aws_vpc_security_group_egress_rule (not aws_security_group_rule)",
      "Adds an explicit egress rule on security groups"
    ],
    "must_not": [
      "Use aws_eip with vpc = true",
      "Use dynamodb_table in the S3 backend",
      "Mix inline route blocks with aws_route resources",
      "Put NAT gateway ID in gateway_id on aws_route",
      "Open port 22 or 3389 from 0.0.0.0/0"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Regional NAT Constraints

```json
{
  "skills": ["provisioning-aws-vpc-v6"],
  "query": "I want to use a single regional NAT gateway instead of one per AZ. What are the constraints and how do I configure it in Terraform?",
  "success_criteria": {
    "must_pass": [
      "States that availability_mode = \"regional\" requires vpc_id (not subnet_id or allocation_id)",
      "States that connectivity_type must be \"public\" for regional NAT (private not supported)",
      "States that regional NAT is not available in constrained AZs",
      "States that expanding to a new AZ can take up to 60 minutes",
      "States that a single nat_gateway_id is used in all private route tables",
      "Notes the tradeoff: cross-AZ traffic may incur data transfer costs vs zonal HA"
    ],
    "must_not": [
      "Set subnet_id or allocation_id on a regional NAT gateway",
      "Claim regional NAT supports private connectivity_type",
      "Claim regional NAT is available in all AZs without qualification"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Mixing SG Rule Mechanisms

```json
{
  "skills": ["provisioning-aws-vpc-v6"],
  "query": "Can I use aws_security_group_rule together with aws_vpc_security_group_ingress_rule on the same security group in aws provider 6.x?",
  "success_criteria": {
    "must_pass": [
      "Explicitly rejects mixing aws_security_group_rule with aws_vpc_security_group_ingress_rule/egress_rule on the same SG",
      "States that mixing mechanisms causes rule conflicts, perpetual differences, and rules being overwritten",
      "States that aws_security_group_rule is discouraged (\"Avoid\") — not deprecated",
      "Recommends using only aws_vpc_security_group_ingress_rule and aws_vpc_security_group_egress_rule"
    ],
    "must_not": [
      "State that aws_security_group_rule is deprecated (the word deprecated does not appear in 6.x docs)",
      "Silently permit mixing the mechanisms",
      "Recommend aws_security_group_rule as the preferred approach"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Removed Arguments and Deprecated Backend Option

```json
{
  "skills": ["provisioning-aws-vpc-v6"],
  "query": "Review this Terraform snippet: aws_eip with vpc = true, aws_flow_log with log_group_name, and S3 backend with dynamodb_table. Is this correct for hashicorp/aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Rejects aws_eip vpc = true as removed in 6.0; provides domain = \"vpc\" as the replacement",
      "Rejects aws_flow_log log_group_name as removed in 6.0; provides log_destination (ARN) + log_destination_type = \"cloud-watch-logs\" as the replacement",
      "Rejects S3 backend dynamodb_table as deprecated; provides use_lockfile = true as the replacement",
      "Cites the version-6-upgrade guide or S3 backend docs as authority for each rejection"
    ],
    "must_not": [
      "Accept aws_eip vpc = true as valid for 6.x",
      "Accept aws_flow_log log_group_name as valid for 6.x",
      "Accept dynamodb_table without noting its deprecated status"
    ]
  }
}
```
