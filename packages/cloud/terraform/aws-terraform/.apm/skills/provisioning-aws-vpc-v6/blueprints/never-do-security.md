# Never-Do — Security (SG Rules, NACL Rules, SSH/RDP)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. Mixing Security Group Rule Mechanisms

Mixing inline `ingress`/`egress` blocks, `aws_security_group_rule`, and per-direction rule
resources on one SG causes rule conflicts, perpetual differences, and rules being overwritten.
`aws_security_group_rule` is **discouraged** ("Avoid") — not deprecated.

```hcl
# WRONG — three mechanisms on the same SG
resource "aws_security_group" "mixed" {
  vpc_id = aws_vpc.main.id
  ingress {                         # WRONG — inline block
    from_port = 443; to_port = 443; protocol = "tcp"; cidr_blocks = ["10.0.0.0/8"]
  }
}
resource "aws_security_group_rule" "also_wrong" {   # WRONG — discouraged + mixed
  type = "ingress"; security_group_id = aws_security_group.mixed.id
  from_port = 80; to_port = 80; protocol = "tcp"; cidr_blocks = ["10.0.0.0/8"]
}
resource "aws_vpc_security_group_ingress_rule" "conflict" {   # WRONG — third mechanism
  security_group_id = aws_security_group.mixed.id
  cidr_ipv4 = "10.0.0.0/8"; from_port = 8080; to_port = 8080; ip_protocol = "tcp"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/security_group_rule.html.markdown

# CORRECT — one mechanism only: aws_vpc_security_group_ingress_rule / egress_rule
resource "aws_security_group" "app" {
  vpc_id = aws_vpc.main.id; name = "app"; description = "Application tier"
}
resource "aws_vpc_security_group_ingress_rule" "https" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4 = "10.0.0.0/8"; from_port = 443; to_port = 443; ip_protocol = "tcp"
}
resource "aws_vpc_security_group_egress_rule" "all_out" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4 = "0.0.0.0/0"; ip_protocol = "-1"   # all protocols; no from_port/to_port
}
```

## 2. Mixing Inline NACL Rules with aws_network_acl_rule

```hcl
# WRONG — inline rule block mixed with aws_network_acl_rule
resource "aws_network_acl" "bad" {
  vpc_id = aws_vpc.main.id
  ingress {                                    # WRONG — inline block
    rule_no = 100; action = "allow"; protocol = "tcp"
    from_port = 443; to_port = 443; cidr_block = "0.0.0.0/0"
  }
}
resource "aws_network_acl_rule" "bad_rule" {  # WRONG — conflicts with inline block
  network_acl_id = aws_network_acl.bad.id
  rule_number = 200; rule_action = "allow"; protocol = "tcp"
  from_port = 80; to_port = 80; cidr_block = "0.0.0.0/0"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/network_acl.html.markdown

# CORRECT — no inline blocks; all rules via aws_network_acl_rule
resource "aws_network_acl" "private" {
  vpc_id = aws_vpc.main.id
}
resource "aws_network_acl_rule" "allow_https_in" {
  network_acl_id = aws_network_acl.private.id
  rule_number = 100; protocol = "tcp"; rule_action = "allow"
  egress = false; cidr_block = "10.0.0.0/8"; from_port = 443; to_port = 443
}
```

## 3. Same Subnet in NACL subnet_ids and Association

```hcl
# WRONG — same subnet in both places
resource "aws_network_acl" "bad" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = [aws_subnet.private["eu-west-1a"].id]   # WRONG
}
resource "aws_network_acl_association" "bad" {
  network_acl_id = aws_network_acl.bad.id
  subnet_id      = aws_subnet.private["eu-west-1a"].id  # WRONG — duplicates subnet_ids
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/network_acl.html.markdown

# CORRECT — use aws_network_acl_association exclusively
resource "aws_network_acl" "private" { vpc_id = aws_vpc.main.id }
resource "aws_network_acl_association" "private" {
  for_each       = local.private_subnets
  network_acl_id = aws_network_acl.private.id
  subnet_id      = aws_subnet.private[each.key].id
}
```

## 4. Opening SSH or RDP from 0.0.0.0/0

Violates Security Hub EC2.13 (SSH/0.0.0.0/0), EC2.14 (RDP/0.0.0.0/0), EC2.53 (SSH/::/0),
EC2.54 (RDP/::/0) — all rated High.

```hcl
# WRONG — open SSH from the internet
resource "aws_vpc_security_group_ingress_rule" "bad_ssh" {
  security_group_id = aws_security_group.bastion.id
  cidr_ipv4 = "0.0.0.0/0"   # WRONG — EC2.13/EC2.53 violation
  from_port = 22; to_port = 22; ip_protocol = "tcp"
}
# Source: https://docs.aws.amazon.com/securityhub/latest/userguide/ec2-controls.html

# CORRECT — restrict to a specific CIDR
resource "aws_vpc_security_group_ingress_rule" "ssh_vpn" {
  security_group_id = aws_security_group.bastion.id
  cidr_ipv4 = "203.0.113.0/24"   # specific corporate range
  from_port = 22; to_port = 22; ip_protocol = "tcp"
}
```
