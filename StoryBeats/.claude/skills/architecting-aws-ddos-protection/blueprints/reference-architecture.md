# Reference Architecture — Canonical DDoS-Resilient AWS Architecture

> Source: AWS DDoS Resiliency Best Practices (AWS WAF Dev Guide) + Well-Architected Security Pillar SEC05.
> Context: Production internet-facing web/API workload requiring L3/L4 + L7 DDoS resilience, centralized
> governance, and cost protection across a multi-account AWS Organizations estate.
> All sources accessed 2026-07-31.

---

## Request Path (edge-fronted, private origin)

```
Internet
  |
  v
Amazon Route 53
  (health-checked failover/latency routing → CloudFront)
  (health checks feed Shield Advanced health-based detection → proactive engagement)
  |
  v
Amazon CloudFront distribution
  + AWS WAF web ACL (managed rules + Layer 7 Anti-DDoS group + rate-based rules)
  [Shield Advanced applied to CloudFront ARN]
  (edge absorption: global PoPs absorb volumetric L3/L4 and filter L7 before it reaches origin)
  |
  v
Application Load Balancer (regional, private VPC)
  + AWS WAF web ACL (regional managed rules + rate-based rules)
  [Shield Advanced applied to ALB ARN]
  (security group: ingress ONLY from CloudFront managed prefix list)
  |
  v
Amazon EC2 / Amazon ECS tasks
  (private subnets — no public IPs; no direct internet exposure)
```

---

## Services Composition

| Layer | Service | Purpose | Notes |
|-------|---------|---------|-------|
| DNS / global routing | Amazon Route 53 (health checks) | Resilient DNS + failover; feeds health-based detection | Health checks required for SRT proactive engagement |
| Edge / CDN | Amazon CloudFront + AWS WAF | Absorb volumetric attacks at global edge; L7 filtering + rate-based rules | Lowest DTO rate ($0.025/GB) under Shield Advanced |
| Regional entry | Application Load Balancer + AWS WAF | Regional L7 routing + filtering | Keep origin private; restrict SG to CloudFront path |
| Compute origin | Amazon EC2 / Amazon ECS (private subnets) | Application origin | No public IPs; SG allows ALB/CloudFront ingress only |
| DDoS protection | AWS Shield Advanced (on CloudFront, Route 53, ALB, Global Accelerator, EIPs) | L3/L4 auto-mitigation + opt-in L7 automatic mitigation | Explicitly protect every public resource |
| Governance | AWS Firewall Manager (Shield Advanced policy) | Org-wide auto-protection + WAF rule deployment | No extra charge for Shield policies; requires Organizations |
| Expert response | Shield Response Team (SRT) + proactive engagement | Expert mitigation during attacks | Requires SRT IAM role + Business/Enterprise Support + health checks |
| Visibility | Amazon CloudWatch + AWS Security Hub + Amazon SNS | Real-time DDoS metrics, findings, alerting | Firewall Manager routes findings to Security Hub/SNS |

---

## Attack-Time Behavior

| Attack type | What AWS does | What you configured |
|-------------|---------------|---------------------|
| L3/L4 volumetric (UDP flood, SYN flood) | AWS auto-mitigates at the network edge (Shield Standard + Advanced) | No additional config required |
| L3/L4 on EC2 EIP | Shield Advanced deploys your VPC NACLs to the AWS network border | NACLs already in place on the VPC |
| L7 request flood (HTTP GET) | Shield Advanced alarms; automatic mitigation fires (if enabled in "block" mode) | Automatic application layer DDoS mitigation enabled; WAF rate-based rules configured |
| L7 sophisticated attack | SRT proactively contacts you (proactive engagement); builds custom WAF rules | Health-based detection enabled; SRT access role configured; contacts current |

---

## Scaling Path (multi-account)

1. Subscribe Shield Advanced at the payer account (covers the entire consolidated-billing family).
2. Designate a Firewall Manager admin account (org security account).
3. Create a Firewall Manager Shield Advanced policy scoped to the org or specific OUs.
4. New accounts and new internet-facing resources are auto-protected without manual steps.
5. Use Shield Advanced protection groups to detect cross-resource attacks on multi-resource applications.

---

## Cost Baseline (directional — re-verify at contracting time)

| Item | Cost | Notes |
|------|------|-------|
| Shield Advanced subscription | $3,000/month (1-year commitment) | Covers entire consolidated-billing family |
| WAF standard fees (covered) | Included | Up to 1,500 WCUs / default body size / 50 billion requests/month per protected resource |
| Automatic L7 mitigation WCUs | 150 WCUs (from covered 1,500 budget) | Deducted from the WAF covered ceiling |
| CloudFront DTO (Shield Advanced) | $0.025/GB | Lower than ALB/EC2 DTO |
| ALB / EC2 / Global Accelerator DTO | $0.050/GB | Standard Shield Advanced DTO rate |
| WAF beyond 1,500 WCUs | Standard WAF pricing | Bot Control, CAPTCHA, large-body inspection extra |
| DDoS cost protection | Service credits (request after attack) | Offsets attack-driven DTO/scaling spikes on protected resources |

> Source: AWS Shield Pricing page + AWS WAF Pricing page (accessed 2026-07-31). Re-verify before contracting.

---

## Alternative: Non-HTTP Workload (TCP/UDP gaming / real-time)

For non-cacheable, non-HTTP(S) services (e.g., gaming, real-time communication) that cannot sit behind CloudFront:

```
Internet
  |
  v
AWS Global Accelerator (standard accelerator)
  [Shield Advanced applied to the accelerator ARN]
  |
  v
Network Load Balancer (regional)
  (Elastic IP or NLB — protect the EIP with Shield Advanced)
  |
  v
EC2 / ECS (private subnet)
```

**Notes**:
- DTO rate: $0.050/GB (Global Accelerator/ELB, not CloudFront's $0.025/GB)
- AWS WAF applies only to HTTP(S) resources; pair with app-level rate limiting for non-HTTP protocols
- Health-based detection via Route 53 health checks still applies for Global Accelerator endpoints

---

## Source Bibliography

- AWS DDoS Resiliency Best Practices (edge services) — https://docs.aws.amazon.com/waf/latest/developerguide/ddos-edge-services.html
- Well-Architected Security Pillar — Protecting networks (SEC05) — https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html
- Shield Advanced capabilities and options — https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html
- AWS Shield Pricing — https://aws.amazon.com/shield/pricing/
- AWS WAF Pricing — https://aws.amazon.com/waf/pricing/
