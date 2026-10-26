# Never-Do — Zones, Records, Exclusive Ownership

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 1. Mixing inline vpc blocks with aws_route53_zone_association

Mixing in-line `vpc` blocks and `aws_route53_zone_association` for the same zone ID causes "a
perpetual difference in plan output". Workaround if unavoidable: `lifecycle { ignore_changes = [vpc] }`.

```hcl
# WRONG — both mechanisms on one zone
resource "aws_route53_zone" "bad" {
  name = "internal.example.com"
  vpc { vpc_id = aws_vpc.a.id }
}
resource "aws_route53_zone_association" "bad" {
  zone_id = aws_route53_zone.bad.zone_id
  vpc_id  = aws_vpc.b.id
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_zone.html.markdown

# CORRECT — in-line vpc blocks only
resource "aws_route53_zone" "good" {
  name = "internal.example.com"
  vpc { vpc_id = aws_vpc.a.id }
  vpc { vpc_id = aws_vpc.b.id }
}
```

## 2. Alias record with ttl or records

`alias` conflicts with `ttl` and `records`; set exactly one of `records` or `alias`.

```hcl
# WRONG
resource "aws_route53_record" "bad" {
  zone_id = aws_route53_zone.public.zone_id
  name    = "www.example.com"
  type    = "A"
  ttl     = 300                      # WRONG — conflicts with alias
  records = ["192.0.2.1"]            # WRONG — conflicts with alias
  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown

# CORRECT — alias block only
resource "aws_route53_record" "good" {
  zone_id = aws_route53_zone.public.zone_id
  name    = "www.example.com"
  type    = "A"
  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}
```

## 3. Routing policies without set_identifier or combined

`set_identifier` is required with any routing policy, and each routing policy conflicts with every
other one.

```hcl
# WRONG — no set_identifier, two policies on one record
resource "aws_route53_record" "bad" {
  zone_id = aws_route53_zone.public.zone_id
  name    = "app.example.com"
  type    = "A"
  ttl     = 60
  records = ["192.0.2.10"]
  weighted_routing_policy { weight = 10 }
  latency_routing_policy { region = "eu-west-1" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown

# CORRECT — one policy plus set_identifier
resource "aws_route53_record" "good" {
  zone_id        = aws_route53_zone.public.zone_id
  name           = "app.example.com"
  type           = "A"
  ttl            = 60
  records        = ["192.0.2.10"]
  set_identifier = "weighted-a"
  weighted_routing_policy { weight = 10 }
}
```

## 4. Partial aws_route53_records_exclusive

It takes exclusive ownership of a zone's record sets, including removal of record sets not explicitly
configured. The default NS/SOA records created with the zone "should not be included"; adding them
causes persistent drift because the read operation ignores writing them to state. To avoid drift,
every `aws_route53_record` managed alongside needs an equivalent `resource_record_set` block. It
reconciles only on apply and does not prevent out-of-band creation; destroying it does not delete
records. Schema: `zone_id` required; `resource_record_set` optional and repeatable with required
`name` and `type`, exactly one of `resource_records` (blocks with required `value`) or
`alias_target`, and `ttl` required for non-alias.

```hcl
# WRONG — includes the default NS record and has no equivalent for aws_route53_record.www
resource "aws_route53_records_exclusive" "bad" {
  zone_id = aws_route53_zone.public.zone_id
  resource_record_set {
    name = "example.com"
    type = "NS"                 # WRONG — default NS/SOA must not be included
    ttl  = 172800
    resource_records { value = "ns-1.example.net." }
  }
}
resource "aws_route53_record" "www" {   # no matching resource_record_set -> drift
  zone_id = aws_route53_zone.public.zone_id
  name    = "www.example.com"
  type    = "A"
  ttl     = 300
  records = ["192.0.2.1"]
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_records_exclusive.html.markdown

# CORRECT — no NS/SOA; each managed record has an equivalent resource_record_set
resource "aws_route53_records_exclusive" "good" {
  zone_id = aws_route53_zone.public.zone_id
  resource_record_set {
    name = "www.example.com"
    type = "A"
    ttl  = 300
    resource_records { value = "192.0.2.1" }
  }
}
```

Alternative: manage records with `aws_route53_record` alone.

## 5. Batch reads in drift-sensitive pipelines

`TF_AWS_ROUTE53_RECORD_BATCH_READS=true` (6.67.0, experimental) caches each zone's record set on first
read; out-of-band changes after caching "will not be detected", with no backward-compatibility
guarantee.

```bash
# WRONG — drift-sensitive CI
TF_AWS_ROUTE53_RECORD_BATCH_READS=true terraform plan -detailed-exitcode
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/route53_record.html.markdown

# CORRECT — leave the variable unset
terraform plan -detailed-exitcode
```
