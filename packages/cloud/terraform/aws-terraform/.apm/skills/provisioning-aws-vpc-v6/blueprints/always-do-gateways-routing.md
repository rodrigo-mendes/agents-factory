# Always-Do — Gateways and Routing (IGW, NAT, Route Tables)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.
Assumes `aws_vpc.main`, `aws_subnet.public`, `aws_subnet.private`, `local.public_subnets`,
`local.private_subnets` from [always-do-foundation.md](./always-do-foundation.md).

## 3. IGW and Zonal NAT per AZ

`domain = "vpc"` is required on every EIP — the `vpc` argument was removed in 6.0.
Both EIPs and NAT gateways must `depends_on` the IGW.

```hcl
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "main" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/internet_gateway.html.markdown

resource "aws_eip" "nat" {
  for_each   = local.public_subnets
  domain     = "vpc"   # required; aws_eip.vpc argument removed in 6.0
  depends_on = [aws_internet_gateway.main]
  tags       = { Name = "nat-${each.key}" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/eip.html.markdown

resource "aws_nat_gateway" "zonal" {
  for_each          = local.public_subnets
  allocation_id     = aws_eip.nat[each.key].id
  subnet_id         = aws_subnet.public[each.key].id
  connectivity_type = "public"
  availability_mode = "zonal"   # default; explicit for clarity
  depends_on        = [aws_internet_gateway.main]
  tags              = { Name = "nat-${each.key}" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/nat_gateway.html.markdown
# Source: https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html
```

## 4. Regional NAT Alternative

`vpc_id` required; `subnet_id` and `allocation_id` must NOT be set; `connectivity_type` must be
`"public"`. One NAT ID goes in all private route tables. Not available in constrained AZs; up to
60 min to expand to a new AZ.

```hcl
resource "aws_nat_gateway" "regional" {
  availability_mode = "regional"
  vpc_id            = aws_vpc.main.id
  connectivity_type = "public"   # only public is valid for regional
  # subnet_id and allocation_id MUST NOT be set for regional mode
  depends_on = [aws_internet_gateway.main]
  tags       = { Name = "nat-regional" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/nat_gateway.html.markdown
# Source: https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html
```

## 5. Route Tables and Separate Routes

Never mix inline `route` blocks in `aws_route_table` with `aws_route` resources.
Use `nat_gateway_id` for NAT routes — `gateway_id` is for IGW/VGW only.

```hcl
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "public" }
  # No inline route blocks — all routes via aws_route
}

resource "aws_route" "public_igw" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
  # gateway_id is correct for IGW/VGW; NAT uses nat_gateway_id
}

resource "aws_route_table_association" "public" {
  for_each       = local.public_subnets
  subnet_id      = aws_subnet.public[each.key].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  for_each = local.private_subnets
  vpc_id   = aws_vpc.main.id
  tags     = { Name = "private-${each.key}" }
}

resource "aws_route" "private_nat" {
  for_each               = local.private_subnets
  route_table_id         = aws_route_table.private[each.key].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.zonal[each.key].id
  # nat_gateway_id, NOT gateway_id — NAT ID in gateway_id causes permanent diff
}

resource "aws_route_table_association" "private" {
  for_each       = local.private_subnets
  subnet_id      = aws_subnet.private[each.key].id
  route_table_id = aws_route_table.private[each.key].id
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route_table.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route.html.markdown
```
