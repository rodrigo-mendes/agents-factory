# Always-Do — Security (Security Groups, Default SG, Endpoints)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 6. Security Groups

Use `aws_vpc_security_group_ingress_rule` + `aws_vpc_security_group_egress_rule` (current best
practice, one CIDR per rule). `aws_security_group_rule` is discouraged ("Avoid") — not deprecated.
Terraform removes the AWS default allow-all egress on create — add an explicit egress rule.

```hcl
resource "aws_security_group" "app" {
  name        = "app"
  description = "Application tier"
  vpc_id      = aws_vpc.main.id
  # No inline ingress/egress blocks — use per-direction rule resources
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/security_group.html.markdown

resource "aws_vpc_security_group_ingress_rule" "app_https" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = "10.0.0.0/8"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

# Explicit egress required — Terraform removes default allow-all on create
resource "aws_vpc_security_group_egress_rule" "app_all" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"   # all protocols; do not set from_port/to_port with -1
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_security_group_ingress_rule.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_security_group_egress_rule.html.markdown
```

## 7. Default SG Lockdown

`aws_default_security_group` adopts the VPC default SG and immediately removes all rules.
Satisfies Security Hub EC2.2 (High): "default security group must allow no traffic".

```hcl
resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.main.id
  # Omitting ingress/egress → deny all traffic (no rules)
  tags = { Name = "default-no-traffic" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/default_security_group.html.markdown
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/ec2-controls.html (EC2.2)
```

## 8. Gateway and Interface Endpoints

Gateway endpoints (S3, DynamoDB) are free. Never list the same route table in both
`route_table_ids` and `aws_vpc_endpoint_route_table_association`.

```hcl
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.eu-west-1.s3"
  vpc_endpoint_type = "Gateway"   # default
  route_table_ids   = [for rt in aws_route_table.private : rt.id]
  # Never combine route_table_ids with aws_vpc_endpoint_route_table_association for the same tables
}

resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.eu-west-1.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [for rt in aws_route_table.private : rt.id]
}

resource "aws_vpc_endpoint" "ssm" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.eu-west-1.ssm"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [for s in aws_subnet.private : s.id]
  security_group_ids  = [aws_security_group.app.id]
  private_dns_enabled = true   # default false
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_endpoint.html.markdown
# Source: https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html
```

Interface endpoint pricing: (unverified) — not fetched; check https://aws.amazon.com/privatelink/pricing/.
