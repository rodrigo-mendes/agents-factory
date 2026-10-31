# Never-Do Patterns — AWS Route 53 DNS (2026)

Six anti-patterns from SKILL.md with wrong / correct / detection.
Source research: `workspace/docs/research_cloud_AWS_Route53_Networking_2026.md`. Official sources accessed 2026-08-31.

---

## A1 — CNAME at the zone apex (CRITICAL)

The apex must hold NS and SOA records; a CNAME cannot coexist with them (RFC 1034). Route 53 returns an error.

- ❌

```
example.com. CNAME d1234.cloudfront.net.
```

- ✅ Alias A (and AAAA) at the apex:

```
example.com. A    ALIAS d1234.cloudfront.net
example.com. AAAA ALIAS d1234.cloudfront.net
```

- Detect: `aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID --query "ResourceRecordSets[?Name=='example.com.' && Type=='CNAME']"` must be empty.

Source: [Alias vs non-alias](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html) (2026-08-31)

---

## A2 — ChangeResourceRecordSets as the DR failover mechanism (CRITICAL)

It is a control-plane API routed through us-east-1, unavailable in exactly the event that triggers DR (REL11-BP04).

- ❌ Runbook or Lambda calling `aws route53 change-resource-record-sets`; weighted-record flips (100/0 to 0/100) as failover.
- ✅ Pre-built ARC routing controls with health-check switches; failover via the data plane:

```bash
aws route53-recovery-cluster update-routing-control-state --routing-control-arn ARN --routing-control-state Off
```

  ARC Region switch plans add safety rules; keep cluster endpoint IPs and DR credentials offline.
- Detect: grep DR runbooks for `change-resource-record-sets` / `route53 change-*`; confirm routing controls exist for each critical endpoint.

Source: [ARC developer guide](https://docs.aws.amazon.com/r53recovery/latest/dg/what-is-route53-recovery.html) (2026-08-31)

---

## A3 — High TTL on failover-capable records (HIGH)

Clients keep a failed endpoint until their cached TTL expires; 3600 s means up to an hour beyond detection.

- ❌ Failover records with TTL 300-3600.
- ✅ TTL 60-120 s on health-check-associated records; pre-lower TTLs at least 2x the current value before planned DR tests; for sub-TTL failover use Global Accelerator. Some resolvers may cache beyond TTL (unverified: explicit AWS caveat).
- Detect: `aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID --query "ResourceRecordSets[?HealthCheckId && TTL > '120']"`

Source: [DNS failover types](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-types.html) (2026-08-31)

---

## A4 — Expecting private zone names to resolve outside associated VPCs (HIGH)

PHZs answer only queries from explicitly associated VPCs. Others get the public record or NXDOMAIN, so a PHZ is not a security boundary.

- ❌ On-premises hosts querying a PHZ name with no inbound endpoint or forwarding rule.
- ✅ Associate the PHZ with every VPC that needs it; for on-premises use inbound Resolver endpoints (2+ ENIs) and forwarding rules to their IPs; cross-account via Route 53 Profiles or AWS RAM.
- Detect: `aws route53 get-hosted-zone --id ZONE_ID` (VPCs list); `aws route53 list-vpc-association-authorizations --hosted-zone-id ZONE_ID`.

Source: [Private hosted zones](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-private.html) (2026-08-31)

---

## A5 — Multi-vendor name servers with DNSSEC (HIGH)

Inconsistent signed answers across providers cause SERVFAIL for validating resolvers, making the zone unreachable.

- ❌ Enabling signing while the registrar also delegates to another provider (for example Cloudflare, Azure DNS).
- ✅ Sign only zones served exclusively by Route 53 name servers (`*.awsdns-*.com/net/org/co.uk`). If multi-vendor DNS is required, do not enable DNSSEC.
- Detect: check NS records at the registrar before enabling.

Source: [DNSSEC configuration](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html) (2026-08-31)

---

## A6 — Health check domain name equals the health-checked record (MEDIUM)

Creates a circular dependency; Route 53 may use a stale or cached IP.

- ❌ Health check domain `api.example.com` for the failover record `api.example.com`.
- ✅ Use the real endpoint DNS name or IP in the health check; for ALB/CloudFront use alias records with `Evaluate Target Health = Yes`; for EC2 specify the instance IP.
- Detect: compare health check domain names with the record names they are attached to.

Source: [Health check values](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/health-checks-creating-values.html) (2026-08-31)
