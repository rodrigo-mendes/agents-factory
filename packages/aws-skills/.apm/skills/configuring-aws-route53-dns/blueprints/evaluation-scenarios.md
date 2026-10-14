# Evaluation Scenarios — configuring-aws-route53-dns

Six test scenarios for `/evaluating-skill-scenarios configuring-aws-route53-dns`.
Covers canonical use, edge cases, anti-pattern traps, and DR decision quality.

---

## Scenario 1 — Canonical: Zone Apex + www Pointing to CloudFront

```json
{
  "skills": ["configuring-aws-route53-dns"],
  "query": "I have a domain example.com registered in Route 53. I created a CloudFront distribution with example.com and www.example.com as alternate domain names. How do I create the DNS records correctly?",
  "expected_behavior": [
    "Instructs to create Alias A record (not CNAME) at zone apex (example.com) pointing to the CloudFront distribution DNS name",
    "Instructs to create Alias A record for www.example.com pointing to the same CloudFront distribution",
    "Advises to create Alias AAAA records (both apex and www) when IPv6 is enabled on the CloudFront distribution",
    "Mentions that ACM DNS validation CNAME record must remain permanently in the zone for certificate auto-renewal",
    "States that alias queries to CloudFront are free and TTL is managed by Route 53",
    "Does NOT suggest using CNAME at zone apex"
  ]
}
```

---

## Scenario 2 — Canonical: Multi-Region Active-Passive DR with ARC

```json
{
  "skills": ["configuring-aws-route53-dns"],
  "query": "I need to set up DNS-based failover for my web application across us-east-1 (primary) and us-west-2 (secondary). RTO requirement is under 5 minutes. How should I configure Route 53 and what is the correct failover mechanism?",
  "expected_behavior": [
    "Recommends Route 53 Failover routing policy (not Weighted or Simple) for Primary/Secondary designation",
    "Instructs to set TTL to 60-120 seconds on failover records (NOT default higher values)",
    "Explicitly recommends ARC Routing Controls (data plane) as the failover execution mechanism — NOT ChangeResourceRecordSets",
    "Explains that ChangeResourceRecordSets routes through us-east-1 control plane, which may be impaired during a regional failure",
    "Instructs to configure ARC safety rules (assertion rules) to prevent fail-open scenarios",
    "Advises to store ARC cluster endpoint IPs and DR IAM credentials offline before any outage",
    "Recommends Aurora Global Database for near-zero RPO data replication alongside DNS failover",
    "Mentions that Evaluate Target Health = Yes on alias records is sufficient for AWS targets (ALB/CloudFront) instead of a separate health check"
  ]
}
```

---

## Scenario 3 — Canonical: Hybrid DNS for On-Premises Resolution of Private Hosted Zones

```json
{
  "skills": ["configuring-aws-route53-dns"],
  "query": "Our on-premises servers need to resolve DNS names from a Route 53 private hosted zone (internal.example.com). The VPC is connected to on-premises via AWS Direct Connect. What do I need to configure?",
  "expected_behavior": [
    "Instructs to create a Route 53 inbound Resolver endpoint in the VPC with at least 2 ENIs (one per AZ for high availability)",
    "Instructs to configure the on-premises DNS server (BIND/Windows DNS/Unbound) to forward queries for internal.example.com to the inbound endpoint IP addresses",
    "States that the private hosted zone must be explicitly associated with the VPC — this is NOT automatic",
    "Mentions security group on inbound endpoint ENIs must permit UDP/TCP port 53 from on-premises CIDR",
    "Mentions Route 53 Profiles as the scaling option when managing 10+ VPCs or multiple accounts",
    "Does NOT suggest using Global Resolver as the solution when DX connectivity already exists"
  ]
}
```

---

## Scenario 4 — Edge Case: DNSSEC Setup Sequence and KMS Requirements

```json
{
  "skills": ["configuring-aws-route53-dns"],
  "query": "I want to enable DNSSEC signing for my public hosted zone. The hosted zone is in eu-west-1. What are the steps and what do I need to watch out for?",
  "expected_behavior": [
    "States that the KMS key MUST be in us-east-1 regardless of where the hosted zone was created — this is a common setup failure",
    "States that the KMS key MUST be asymmetric, ECC_NIST_P256 algorithm",
    "Instructs to create CloudWatch alarms BEFORE enabling DNSSEC: DNSSECInternalFailure >= 1 and DNSSECKeySigningKeysNeedingAction >= 1, both in us-east-1",
    "Describes the three-step sequence: (1) prepare zone (lower TTLs, enable query logging), (2) enable DNSSEC signing via API, (3) add DS record to parent zone to establish chain of trust",
    "Warns that DNSSEC enforces a maximum TTL of 1 week on all records in the zone",
    "Warns that multi-vendor name server configurations are incompatible with DNSSEC signing",
    "Does NOT allow proceeding without first configuring CloudWatch alarms"
  ]
}
```

---

## Scenario 5 — Anti-Pattern Trap: CNAME at Zone Apex

```json
{
  "skills": ["configuring-aws-route53-dns"],
  "query": "I want to point my root domain example.com to my ALB. I tried creating a CNAME record for example.com pointing to my ALB DNS name but it didn't work. Can I use CNAME flattening like Cloudflare does?",
  "expected_behavior": [
    "Explains that CNAME at zone apex is prohibited by DNS protocol (RFC 1034) — zone apex must have NS and SOA records, which cannot coexist with CNAME at the same name",
    "States that Route 53 returns an error when CNAME at zone apex is attempted",
    "Recommends Route 53 Alias A record (and AAAA for IPv6) at zone apex pointing to the ALB as the correct solution",
    "Explains that Alias records solve the same problem as CNAME flattening but are superior: free for AWS targets, auto-track ALB IP changes, no TTL mismatch",
    "Does NOT recommend workarounds like 'www redirect to apex' as the primary solution",
    "Does NOT suggest attempting CNAME via raw API calls"
  ]
}
```

---

## Scenario 6 — Anti-Pattern Trap: Using Control Plane API for DR Failover

```json
{
  "skills": ["configuring-aws-route53-dns"],
  "query": "Our DR runbook currently calls aws route53 change-resource-record-sets to switch traffic from the primary region to the secondary when a CloudWatch alarm fires. Is this a reliable DR approach?",
  "expected_behavior": [
    "Identifies this as a CRITICAL anti-pattern per AWS Well-Architected REL11-BP04",
    "Explains that ChangeResourceRecordSets is a Route 53 control plane API routed through us-east-1 — the exact region most likely to be impaired during a large-scale incident triggering DR",
    "Recommends replacing the runbook with ARC Routing Controls: pre-configure routing controls, associate with Route 53 health checks, execute failover via aws route53-recovery-cluster update-routing-control-state (ARC data plane — 5 Regional cluster endpoints)",
    "States that ARC Routing Controls operate independently of the Route 53 control plane and are usable even during us-east-1 impairments",
    "Instructs to configure ARC safety rules (assertion rules) to prevent accidental fail-open scenarios",
    "Advises to store ARC cluster endpoint IPs and DR IAM credentials offline",
    "Does NOT validate or suggest improvements to the change-resource-record-sets approach — marks it as unsuitable for DR"
  ]
}
```
