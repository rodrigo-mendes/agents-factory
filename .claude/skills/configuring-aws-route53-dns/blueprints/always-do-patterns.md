# Always-Do Patterns — AWS Route 53 DNS (2026)

Full detail for the 6 mandatory patterns summarised in SKILL.md.
Source research: `workspace/docs/research_cloud_AWS_Route53_Networking_2026.md`. Official sources accessed 2026-08-31.

---

## M1 — Alias records (not CNAME) for AWS targets, including the zone apex

**Pillar**: Reliability (REL02-BP01), Cost Optimization

- Alias records are free for AWS targets, track IP changes automatically, and are the only record type valid at the apex. CNAME at the apex violates RFC 1034 and Route 53 returns an error.
- Create A, and AAAA when IPv6 is enabled. For ALBs the console auto-prepends `dualstack.`.
- Set `Evaluate Target Health = Yes` to inherit target health.
- A simple alias allows one target; use weighted/latency for several.

```bash
aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID --query "ResourceRecordSets[?AliasTarget]"
# Expected: AliasTarget present, EvaluateTargetHealth set as intended
dig example.com   # Expected: A answer, not a CNAME chain
```

Source: [Alias vs non-alias](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resource-record-sets-choosing-alias-non-alias.html) (2026-08-31)

---

## M2 — Associate health checks with routing-policy records

**Pillar**: Reliability (REL02-BP01, REL11-BP04)

- Health checks do not reroute anything on their own; attach them to Failover / Weighted / Latency / Geolocation / Multivalue records via `HealthCheckId`. Unassociated checks cost $0.50-$0.75/month each with no routing effect.
- AWS targets via alias: `Evaluate Target Health = Yes` (no separate check needed).
- Non-AWS endpoints: HTTP/HTTPS/TCP endpoint check.
- Interval 30 s standard; 10 s Fast (extra charge). Failure threshold 1-10, default 3.
- Calculated checks aggregate up to 255 children.

```bash
aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID --query "ResourceRecordSets[?HealthCheckId]"
aws route53 get-health-check-status --health-check-id HEALTH_CHECK_ID
```

Source: [DNS failover configuring](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-configuring.html) (2026-08-31)

---

## M3 — Create DNSSEC CloudWatch alarms BEFORE enabling signing

**Pillar**: Security (SEC04, SEC08-SEC09)

- KSK problems silently break validation for the whole zone; validating resolvers return SERVFAIL.
- Namespace `AWS/Route53`, query in us-east-1 (published every 4 hours):
  - `DNSSECInternalFailure` >= 1
  - `DNSSECKeySigningKeysNeedingAction` >= 1
  - optional: `DNSSECKeySigningKeyMaxNeedingActionAge` > 0; `DNSSECKeySigningKeyAge`
- KMS key: asymmetric, ECC_NIST_P256, **us-east-1**. Key policy grants `dnssec-route53.amazonaws.com` `kms:DescribeKey`, `kms:GetPublicKey`, `kms:Sign`, `kms:CreateGrant`; add confused-deputy protection.
- Enable in three steps: (1) prepare zone (lower TTLs, enable query logging); (2) enable signing; (3) add the DS record to the parent zone.

```bash
aws cloudwatch describe-alarms --alarm-name-prefix DNSSEC --region us-east-1
aws --region us-east-1 route53 get-dnssec --hosted-zone-id ZONE_ID
aws --region us-east-1 route53 list-key-signing-keys --hosted-zone-id ZONE_ID
```

Source: [Monitoring hosted zones with CloudWatch](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/monitoring-hosted-zones-with-cloudwatch.html) (2026-08-31)

---

## M4 — DNS Firewall on every VPC with sensitive workloads

**Pillar**: Security (SEC05, SEC10)

- DNS tunneling bypasses network egress controls. DNS Firewall filters outbound VPC queries (block/allow/alert).
- Baseline with AWS Managed domain lists (Foundational Rules); add custom lists.
- Enable DNS Firewall Advanced (GA 2024-11) for DGA / tunneling / Dictionary-DGA detection; confidence threshold High reduces false positives; findings go to Security Hub.
- Enforce org-wide with AWS Firewall Manager; share rule groups via AWS RAM.
- Maximum 5 rule groups per VPC per account per Region (non-adjustable).
- False positive: find the blocking rule in VPC Resolver logs, add an ALLOW rule with a lower priority number.

```bash
aws route53resolver list-firewall-rule-group-associations --region REGION
```

Source: [DNS Firewall rule groups](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall-rule-groups.html) (2026-08-31)

---

## M5 — Query logging for public zones and VPC Resolver

**Pillar**: Security (SEC04), Operational Excellence

- Public zone logs: CloudWatch Logs group **must be in us-east-1**; one stream per edge location per zone; no Route 53 charge (CloudWatch charges apply).
- VPC Resolver logs only unique (non-cached) queries. One destination per config: CloudWatch Logs (real-time), S3 + Athena (long-term, cheaper), Kinesis Data Firehose (SIEM).
- Global Resolver logs use OCSF v1.2.0 (S3, CloudWatch Logs).
- Limits: 20 query log configs per Region; 100 VPC associations per config.

```bash
aws route53 list-query-logging-configs --hosted-zone-id ZONE_ID
aws route53resolver list-resolver-query-log-configs --region REGION
```

Source: [Query logging](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/query-logs.html) (2026-08-31)

---

## M6 — ARC routing controls (data plane) for DR failover

**Pillar**: Reliability (REL11-BP04)

- `ChangeResourceRecordSets` is a control-plane API routed through us-east-1, the Region likeliest to be impaired in a DR event. REL11-BP04: do not rely on the control plane for recovery.
- ARC routing controls run on 5 Regional cluster endpoints (data plane).
- Steps: create a routing control per endpoint/Region pair; associate each with a Route 53 health check (acts as on/off switch, not a monitor); attach to Failover records; add safety rules (assertion: at least one control stays ON; gating: master switch); automate with ARC Region switch plans.
- Store cluster endpoint IPs and DR IAM credentials offline (physical safe or virtual vault).
- Avoid weighted-record changes as the DR mechanism.

```bash
aws route53-recovery-control-config list-routing-controls --control-panel-arn ARN
aws route53-recovery-cluster get-routing-control-state --routing-control-arn ARN
aws route53-recovery-cluster update-routing-control-state --routing-control-arn ARN --routing-control-state Off
```

Source: [ARC developer guide](https://docs.aws.amazon.com/r53recovery/latest/dg/what-is-route53-recovery.html) (2026-08-31)
