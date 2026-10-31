# Never-Do — Networking (Routes, NAT, Endpoints)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 1. Mixing Inline Route Blocks with aws_route

Inline `route` blocks and `aws_route` resources on the same route table "will overwrite rules".

```hcl
# WRONG — inline block and aws_route on the same table
resource "aws_route_table" "bad" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}
resource "aws_route" "also_bad" {    # WRONG — conflicts with inline block
  route_table_id            = aws_route_table.bad.id
  destination_cidr_block    = "10.1.0.0/16"
  vpc_peering_connection_id = "pcx-xxx"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route_table.html.markdown

# CORRECT — no inline blocks; all routes via aws_route
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
}
resource "aws_route" "public_igw" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}
```

## 2. NAT Gateway ID in gateway_id

Setting `gateway_id` to a NAT gateway ID causes a permanent diff. Only IGW/VGW IDs belong there.

```hcl
# WRONG — permanent diff in every plan
resource "aws_route" "bad" {
  route_table_id         = aws_route_table.private["eu-west-1a"].id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_nat_gateway.zonal["eu-west-1a"].id   # WRONG
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route.html.markdown

# CORRECT
resource "aws_route" "private_nat" {
  route_table_id         = aws_route_table.private["eu-west-1a"].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.zonal["eu-west-1a"].id
}
```

## 3. Combining secondary_allocation_ids with aws_nat_gateway_eip_association

Using both mechanisms causes a perpetual diff — `aws_nat_gateway_eip_association` overwrites the
associations managed by `secondary_allocation_ids`.

```hcl
# WRONG — perpetual diff
resource "aws_nat_gateway" "bad" {
  allocation_id            = aws_eip.primary.id
  subnet_id                = aws_subnet.public["eu-west-1a"].id
  secondary_allocation_ids = [aws_eip.secondary.id]   # WRONG — conflicts below
}
resource "aws_nat_gateway_eip_association" "bad" {
  allocation_id  = aws_eip.secondary.id
  nat_gateway_id = aws_nat_gateway.bad.id
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/nat_gateway.html.markdown

# CORRECT — use aws_nat_gateway_eip_association alone for secondary EIPs
resource "aws_nat_gateway_eip_association" "secondary" {
  allocation_id  = aws_eip.secondary.id
  nat_gateway_id = aws_nat_gateway.zonal["eu-west-1a"].id
}
```

## 4. Same Route Table in Endpoint route_table_ids and Association

Gateway endpoint route tables listed in both `route_table_ids` and
`aws_vpc_endpoint_route_table_association` conflict.

```hcl
# WRONG — same route table in both places
resource "aws_vpc_endpoint" "bad" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.eu-west-1.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private["eu-west-1a"].id]   # WRONG
}
resource "aws_vpc_endpoint_route_table_association" "bad" {
  vpc_endpoint_id = aws_vpc_endpoint.bad.id
  route_table_id  = aws_route_table.private["eu-west-1a"].id       # WRONG
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/vpc_endpoint.html.markdown

# CORRECT — route_table_ids on the endpoint only
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.eu-west-1.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [for rt in aws_route_table.private : rt.id]
}
```
