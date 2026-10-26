# Evaluation Scenarios — securing-vpc-network-access

Six test cases covering canonical use, edge cases, and anti-pattern traps.

---

## Scenario 1 (Canonical): Three-tier web application SG design

```json
{
  "skills": ["securing-vpc-network-access"],
  "query": "Design the security group rules for a three-tier web application with an ALB, EC2 web tier, and RDS PostgreSQL database in a single VPC.",
  "expected_behavior": [
    "Creates three purpose-built SGs: alb-sg, web-sg, db-sg",
    "ALB-SG allows TCP 443 and 80 inbound from 0.0.0.0/0",
    "Web-SG allows TCP 443/80 inbound from ALB-SG using SG referencing (not a hardcoded VPC CIDR)",
    "DB-SG allows TCP 5432 inbound from Web-SG using SG referencing",
    "Recommends removing or not creating inbound 22/3389 rules; suggests SSM Session Manager for admin access",
    "Recommends custom NACLs per subnet tier as defense-in-depth backstop",
    "Recommends enabling VPC Flow Logs"
  ]
}
```

---

## Scenario 2 (Edge Case): Multi-VPC policy centralization

```json
{
  "skills": ["securing-vpc-network-access"],
  "query": "We have 8 VPCs in the same AWS account and Region all sharing the same network access policy. What is the best approach to manage security groups without duplicating rules across all 8 VPCs?",
  "expected_behavior": [
    "Recommends Security Group VPC Associations (GA Oct 2024) for same-account, same-Region VPCs",
    "Explains that one SG can be associated to multiple VPCs — eliminates per-VPC SG duplication",
    "Notes the constraint: same-Region and same-account only; default SG cannot be associated; cannot associate to a default VPC",
    "Distinguishes from Shared Security Groups — cross-account via RAM + Organizations + shared VPC",
    "Does NOT recommend the classic per-VPC SG approach without first flagging the 2024 alternative"
  ]
}
```

---

## Scenario 3 (Anti-Pattern Trap): Wildcard SG rule request

```json
{
  "skills": ["securing-vpc-network-access"],
  "query": "Our application is not connecting. Just open the security group to allow all traffic from 0.0.0.0/0 on all ports to unblock development.",
  "expected_behavior": [
    "Refuses to generate a wildcard all-traffic SG rule without scoping",
    "Explains that all-traffic 0.0.0.0/0 rules create untracked flows — existing sessions drop immediately on the next rule edit",
    "Asks which specific protocol, port, and source IP/range is actually required",
    "Proposes SG referencing or a scoped CIDR/prefix list as alternatives",
    "Flags the management-port (22/3389) case as CRITICAL risk if included in the wildcard",
    "Mentions AWS Config rule restricted-ssh as a detection mechanism"
  ]
}
```

---

## Scenario 4 (NACL Stateless): Missing ephemeral return rule

```json
{
  "skills": ["securing-vpc-network-access"],
  "query": "I created a custom NACL for my public subnet with: rule 100 ALLOW TCP 443 inbound from 0.0.0.0/0, and the default DENY * rule. HTTPS traffic is broken intermittently. What is wrong?",
  "expected_behavior": [
    "Immediately identifies the missing ephemeral-port outbound rule as the root cause",
    "Explains that NACLs are stateless — return traffic must be explicitly allowed",
    "Prescribes adding: outbound ALLOW TCP 1024-65535 to 0.0.0.0/0 (ephemeral range for return traffic)",
    "Notes that the exact ephemeral range varies by client OS and NAT gateway",
    "Recommends numbering NACL rules in increments of 10 or 100 to allow future inserts without renumbering"
  ]
}
```

---

## Scenario 5 (Nitro v6 Breaking Change): Long-lived connection drops after instance migration

```json
{
  "skills": ["securing-vpc-network-access"],
  "query": "We migrated to new EC2 instance types and now our RDS connection pool drops connections after about 5-6 minutes of idle time. Connections were stable before the migration.",
  "expected_behavior": [
    "Identifies the Nitro v6 TCP established idle timeout change: dropped from 432,000s to 350s on Nitro v6",
    "Explains this is a breaking operational change for long-lived connections including DB connection pools",
    "Recommends setting TcpEstablishedTimeout via instance metadata options at launch-template or instance level",
    "Recommends enabling TCP keepalive at the application or OS level as an alternative",
    "Mentions ENA metric conntrack_allowance_exceeded as a monitoring signal"
  ]
}
```

---

## Scenario 6 (Misuse): Requesting a deny rule on a security group

```json
{
  "skills": ["securing-vpc-network-access"],
  "query": "Add a DENY rule to the web-tier security group to block traffic from a known bad IP address 1.2.3.4.",
  "expected_behavior": [
    "Clarifies that AWS Security Groups are allow-only — they cannot express deny rules",
    "Distinguishes from Azure NSG and GCP firewall rules, which do support deny",
    "Redirects to Network ACL as the correct mechanism for an explicit DENY (per-subnet, stateless, allow+deny)",
    "Provides the correct NACL approach: add a low-numbered deny rule for 1.2.3.4 so it evaluates before the allow rules",
    "Confirms that a NACL is subnet-scoped, not instance-scoped, and asks whether the subnet scope is acceptable"
  ]
}
```
