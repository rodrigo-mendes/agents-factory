# Ask First Decision Points — OCI Networking Architecture

## Decision Point 1: Network Security Model — NSGs vs Security Lists vs Network Firewall

| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| NSGs Only | Granularity, micro-segmentation, low cost (free) | Centralized rule visibility | Simple-to-medium architectures with few tiers |
| Security Lists + NSGs | Defense in depth, compliance layers | Complexity, risk of conflicting rules (UNION logic) | Compliance mandates explicit security layers |
| Network Firewall + NSGs | IDS/IPS, L7 inspection, URL filtering, threat intel | Cost (~$580/month + $0.01/GB), added latency | Compliance requires IDS/IPS for inter-VCN traffic |
| WAF + NSGs | L7 HTTP protection, DDoS L7, OWASP Top 10 | Does not inspect non-HTTP traffic | APIs exposed to internet via API Gateway |

**Agent Behavior**:
"Before choosing the security model, ask the user:
'Does inter-VCN/subnet traffic require L7 inspection (IDS/IPS) for compliance, or do NSGs with micro-segmentation meet your security requirements?'"

**Decision Factors**:
- Regulatory requirements (CIS Benchmark, SOC2, PCI-DSS)
- Budget ($0 for NSGs vs ~$580/month for Network Firewall)
- Traffic inspection depth needed (L3-L4 vs L7)

**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/networksecuritygroups.htm

---

## Decision Point 2: Multi-VCN Topology — Single VCN vs Hub-Spoke vs Mesh

| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| Single VCN | Simplicity, no inter-VCN cost | Isolation (blast radius), scalability (subnet limits) | Small projects, single-team, dev/staging |
| Hub-Spoke via DRG v2 | Isolation, centralized security/egress, scalability | Routing complexity, minimal hop latency (~0.1ms) | Enterprise multi-workload, shared services, compliance |
| Mesh (full peering) | Direct communication, lowest latency | No central inspection point, governance difficulty | Microservices with high inter-service communication |
| Hub-Spoke + Network Firewall | Centralized L7 inspection of all traffic | High cost (~$600/month + data), added latency | Regulation requires IDS/IPS on all inter-workload traffic |

**Agent Behavior**:
"Before designing the VCN topology, ask the user:
'How many workloads/teams need network isolation from each other, and is centralized traffic inspection (IPS/IDS) required?'"

**Decision Factors**:
- Number of isolated workloads (1 = single VCN, 3+ = hub-spoke)
- Compliance requirements for centralized inspection
- DRG is free; Network Firewall is ~$600/month

**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/managingDRGs.htm

---

## Decision Point 3: On-Premises Connectivity — FastConnect vs Site-to-Site VPN

| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| FastConnect (Dedicated) | Bandwidth (1G-100G), latency (<2ms), SLA 99.95% | Port cost ($0.30-$0.80/hr), provisioning lead time | Production with high traffic and latency requirements |
| Site-to-Site VPN | Cost (free IPSec tunnels), quick setup | Bandwidth (~1.25 Gbps/tunnel), variable latency | Dev/staging, FastConnect backup, low-traffic |
| FastConnect + VPN (Redundancy) | Maximum resilience, automatic failover | Combined cost, routing complexity | Mission-critical production with strict SLA |

**Agent Behavior**:
"Before configuring on-premises connectivity, ask:
'What is the monthly traffic volume on-premises↔OCI, and what is the maximum acceptable latency for critical transactions?'"

**Decision Factors**:
- Traffic volume (GB/month)
- Latency requirement (<2ms = FastConnect, best-effort = VPN)
- FastConnect: zero data transfer charges (only port cost)

**Source**: https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/fastconnect.htm

---

## Decision Point 4: Load Balancing — Flexible LB vs Network LB vs API Gateway

| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| API Gateway | Rate limiting, auth (JWT/OAuth2), request transforms | No WebSocket long-lived (max 120s timeout) | REST/HTTP APIs for Functions backend |
| Flexible Load Balancer (L7) | SSL termination, path-based routing, WAF integration | Bandwidth cost ($0.006/Mbps/hr) | Web apps with multiple backends, SSL offload |
| Network Load Balancer (L4) | Ultra-low latency, source IP preservation, high throughput | No L7 features (no path routing, no SSL offload) | TCP/UDP workloads, database connectivity |
| API Gateway + LB | Custom domain, WAF + API management combined | Complexity, double-hop latency | Production with custom domain + WAF + API management |

**Agent Behavior**:
"Before choosing the load balancing approach, ask:
'Is this workload HTTP/REST APIs (API Gateway), generic TCP/UDP (NLB), or do you need rate limiting and auth at the network layer?'"

**Source**: https://docs.oracle.com/en-us/iaas/Content/Balance/home.htm
