# Ask-First Decisions — AWS Route 53 DNS (2026)

Seven decision matrices from SKILL.md. Confirm with the user before designing.
Source research: `workspace/docs/research_cloud_AWS_Route53_Networking_2026.md`. Official sources accessed 2026-08-31.

---

## D1 — Route 53 vs Global Accelerator

Ask: "Do you need sub-second failover without TTL delay AND static IPs?" Both yes -> Global Accelerator; otherwise Route 53 + ARC + low TTLs.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Route 53 routing | Geo/latency/weighted/geoproximity/failover semantics; cost | TTL caching extends effective RTO; no static IPs | Web apps, DNS-based traffic management |
| Global Accelerator | Anycast IPs, non-DNS routing, no TTL sensitivity | Simpler traffic policy (traffic dial); higher baseline cost | Non-HTTP TCP/UDP, fixed-IP allowlisting, true sub-second failover |

Cost: alias queries to AWS resources free; latency/geo queries $0.60-$0.80/M.
Source: [DR options whitepaper](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) (2026-08-31)

---

## D2 — Active-active vs active-passive

Ask the documented RTO/RPO first. RTO < 15 min -> active-active or warm standby + ARC; 15-60 min -> pilot light + ARC; hours -> backup-and-restore.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Active-active (Latency/Weighted/Geolocation + health checks) | Near-zero RTO for infra failure, utilisation, latency | Highest cost; data-consistency complexity | Global high-traffic apps, RPO near zero |
| Warm standby (Failover + health checks + ARC) | Cost; simpler data model | RTO minutes; standby capacity risk on spikes | Regulated apps with RTO in minutes |
| Pilot light (Failover + health checks + ARC) | Lowest standby cost | RTO tens of minutes; RPO tied to replication lag | RTO tolerance 15-60 min |

Source: [DNS failover types](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-types.html) (2026-08-31)

---

## D3 — DNS Firewall deny-list vs allow-list

Ask: "Is the set of external domains bounded and well known?" Yes -> allow-list. No -> deny-list with Managed lists, tighten later.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Deny-list (block known-bad) | Simplicity, developer productivity | Unlisted domains allowed by default | General-purpose VPCs, broad internet needs |
| Allow-list (block all but trusted) | Strictest posture, exfiltration prevention | High operational overhead | PCI/HIPAA, defined external access |

Pricing is per rule-group association per VPC-hour, not per query.
Source: [DNS Firewall domain lists](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall-domain-lists.html) (2026-08-31)

---

## D4 — Routing policy selection

Ask the goal: lowest latency, geographic compliance, gradual rollout, DR failover, or proximity control. Complex multi-region: Latency alias -> Weighted -> health-checked resources.

| Policy | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Simple | Simplicity, lowest cost | No per-value health checks | Single endpoint, dev/test |
| Weighted | Gradual shifting | Weight management | Blue/green, canary, standby (weight 0) |
| Latency | User latency | $0.60/M; based on resolver location | Multi-Region web apps |
| Failover | Clear primary/secondary | Active-passive only | DR |
| Geolocation | Compliance, localisation | Needs default record; $0.70/M | Data residency |
| IP-based | CIDR-specific routing | Public zones only | ISP / enterprise network endpoints |
| Multivalue | Client-side balancing (up to 8 healthy) | Not a load balancer | Small sets of equivalent endpoints |
| Geoproximity | Proximity with bias | Needs Traffic Flow; limited to 30 records | Shifting traffic between Regions |

Cost: Weighted/Failover/Multivalue/IP-based $0.40/M; Latency $0.60/M; Geolocation/Geoproximity $0.70/M.
Source: [Routing policy](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html) (2026-08-31)

---

## D5 — DR tier (cost vs RTO/RPO)

| Tier | Services | RTO | RPO | Cost |
|---|---|---|---|---|
| Backup and restore | Route 53 record update post-recovery, S3, CloudFormation | Hours | Hours-days | Lowest |
| Pilot light | Failover + ARC, Aurora Global / DynamoDB global tables | Tens of minutes | Minutes to near-zero | Low-medium |
| Warm standby | Failover + ARC, Auto Scaling, Aurora Global | Minutes | Near-zero | Medium |
| Active/active | Latency/Weighted + health checks + ARC | Near-zero (infra failure) | Near-zero | Highest (about 2x) |

Ask the RTO/RPO, map it to a tier, and validate cost against business value.
Source: [DR options whitepaper](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) (2026-08-31)

---

## D6 — DNSSEC adoption

Ask: "Is DNSSEC mandated (FedRAMP, DoD, financial regulation) or does the domain handle credentials/financial data?" If yes, enable it with alarms and the us-east-1 KMS key in place first.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Enable | Response integrity; cache-poisoning protection | KSK rotation and DS management; max 1-week TTL; KMS cost; no multi-vendor name servers | High-security / compliance domains |
| Do not enable | Simplicity; multi-vendor name servers OK | No DNS integrity protection | General web apps |

KMS: $0.03 per 10,000 signature requests.
Source: [DNSSEC configuration](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html) (2026-08-31)

---

## D7 — Global Resolver vs VPC Resolver

Ask: "Do external clients already have stable DX/VPN connectivity to AWS?" Yes -> VPC Resolver endpoints. No (remote, mobile, branch) -> Global Resolver.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Global Resolver (GA 2026-03-09) | Internet-reachable, DoH/DoT, no VPN, token auth, threat protection | Charges after 30-day trial; less operating history | Remote workers, branches, DoH/DoT requirement |
| VPC Resolver + inbound/outbound endpoints | Established; fits DX/VPN | Needs connectivity; more on-premises setup | Servers already on DX/VPN |

Cost: endpoints $0.125/ENI/hour + $0.40/M queries; cheaper at high volume with existing connectivity.
Source: [Global Resolver GA](https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-route-53-global-resolver) (2026-08-31)
