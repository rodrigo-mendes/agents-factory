# Always-Do — Zones, Records, Routing Policies, Health Checks

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 1. Terraform block and providers

Route 53 resources never take `region` per the AWS provider region guide
(https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown).
The `us_east_1` alias is needed only for us-east-1-pinned dependencies (query-log log group, DNSSEC
KMS key). A regional resource may instead set `region = "us-east-1"` without an alias (medium
confidence: inferred from Enhanced Region Support; the provider docs' own examples use an alias).
All HCL below is a fragment with example values (names, IPs, TTLs, retention).

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.69" }
  }
  backend "s3" {
    bucket       = "my-tf-state"
    key          = "route53/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true   # dynamodb_table is deprecated
  }
}
provider "aws" { region = var.region }
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_query_log.html.markdown
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
```

## 2. Public and private zones

A zone with at least one `vpc` block is private and needs at least one VPC association at all times.
Prefer in-line `vpc` blocks; use `aws_route53_zone_association` only for explicit association ordering.
Do not mix the two for the same zone.

```hcl
resource "aws_route53_zone" "public" {
  name = "example.com"
  tags = { Environment = "prod" }
}

resource "aws_route53_zone" "private" {
  name = "internal.example.com"
  vpc {
    vpc_id = aws_vpc.main.id
  }
}

# Subdomain delegation: NS record in the parent zone + the subdomain zone
resource "aws_route53_zone" "sub" {
  name = "dev.example.com"
}
resource "aws_route53_record" "sub_ns" {
  zone_id = aws_route53_zone.public.zone_id
  name    = "dev.example.com"
  type    = "NS"
  ttl     = 3600
  records = aws_route53_zone.sub.name_servers
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_zone.html.markdown
```

## 3. Records and alias records

Non-alias records need `ttl` + `records`. Alias records need `alias { name, zone_id,
evaluate_target_health }` and omit `ttl`/`records`. Prefer alias over CNAME for AWS targets.

```hcl
resource "aws_route53_record" "mx" {
  zone_id = aws_route53_zone.public.zone_id
  name    = "example.com"
  type    = "MX"
  ttl     = 3600
  records = ["10 mail.example.com"]
}

resource "aws_route53_record" "www" {
  zone_id = aws_route53_zone.public.zone_id
  name    = "www.example.com"
  type    = "A"
  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# TXT value > 255 chars (e.g. DKIM): insert \"\" inside the string to split it
resource "aws_route53_record" "dkim" {
  zone_id = aws_route53_zone.public.zone_id
  name    = "selector._domainkey.example.com"
  type    = "TXT"
  ttl     = 3600
  records = ["first-part\"\"second-part"]
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown
# Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-dns.html
```

## 4. Routing policies and health checks

Every routing policy needs `set_identifier`; policies conflict with each other. For failover use a
short TTL (60-120 s). Always define a default record for geolocation (`country = "*"`),
geoproximity and latency policies.

```hcl
resource "aws_route53_health_check" "primary" {
  type = "HTTPS"
  fqdn = "primary.example.com"
  tags = { Name = "primary" }   # Security Hub Route53.1 requires tags
}

resource "aws_route53_record" "app_primary" {
  zone_id         = aws_route53_zone.public.zone_id
  name            = "app.example.com"
  type            = "A"
  ttl             = 60
  records         = ["192.0.2.10"]
  set_identifier  = "primary"
  health_check_id = aws_route53_health_check.primary.id
  failover_routing_policy { type = "PRIMARY" }
}

resource "aws_route53_record" "app_secondary" {
  zone_id        = aws_route53_zone.public.zone_id
  name           = "app.example.com"
  type           = "A"
  ttl            = 60
  records        = ["192.0.2.20"]
  set_identifier = "secondary"
  failover_routing_policy { type = "SECONDARY" }
}

# Geolocation: country = "*" is the default record
resource "aws_route53_record" "geo_default" {
  zone_id        = aws_route53_zone.public.zone_id
  name           = "geo.example.com"
  type           = "A"
  ttl            = 60
  records        = ["192.0.2.30"]
  set_identifier = "default"
  geolocation_routing_policy { country = "*" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_health_check.html.markdown
# Source: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-dns.html
```

Disabled health checks are always treated as healthy; use `invert_healthcheck` to stop routing.
