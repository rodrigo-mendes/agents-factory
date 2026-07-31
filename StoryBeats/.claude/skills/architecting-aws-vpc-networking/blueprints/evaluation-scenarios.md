# Evaluation Scenarios — architecting-aws-vpc-networking

Three scenarios to verify the skill activates correctly: canonical use, edge case, and anti-pattern
trap. Use these with the Claude A/B evaluation pattern (one instance generates, another tests).

---

## Scenario 1 — Canonical: Production Three-Tier VPC Design

```json
{
  "skills": ["architecting-aws-vpc-networking"],
  "query": "Design a production-grade VPC for an internet-facing e-commerce application. The app needs an Application Load Balancer, ECS Fargate tasks, RDS PostgreSQL Multi-AZ, and must store product images in S3. The workload is in us-east-1 and must tolerate any single AZ failure.",
  "expected_behavior": [
    "Proposes a VPC with public, private/app, and isolated/data subnet tiers — one subnet per tier per AZ across ≥2 (ideally 3) AZs",
    "Routes public subnets' 0.0.0.0/0 to an internet gateway; private/app subnets to a per-AZ NAT gateway; isolated/data subnets to no default route",
    "Deploys one NAT gateway per AZ (each with its own EIP) in a public subnet — not a single shared NAT",
    "Places RDS in isolated subnets with no internet route; access restricted to app SG on port 5432 only",
    "Adds S3 gateway endpoint (free) to private and isolated route tables to eliminate NAT cost for S3 access",
    "Adds interface endpoints for ECR (ecr.api, ecr.dkr), Secrets Manager, and CloudWatch Logs so Fargate tasks in private subnets can pull images and deliver logs without relying on NAT",
    "Enables VPC Flow Logs at VPC scope (TrafficType ALL) to CloudWatch Logs",
    "Recommends GuardDuty to consume the flow logs",
    "Provides AWS CLI verification commands for AZ spread, route tables, NAT count, flow logs, and SG rules"
  ]
}
```

**Pass criteria**: All 8 expected behaviors present. The design must not place RDS in a public
subnet, must not use a single NAT gateway, and must include flow logs.

---

## Scenario 2 — Edge Case: RFC 1918 Exhaustion with Legacy Overlapping VPCs

```json
{
  "skills": ["architecting-aws-vpc-networking"],
  "query": "We have 12 existing VPCs all using 10.0.0.0/16. They were built independently and now need to exchange traffic. We cannot re-IP any of them — workloads are tightly coupled to the current addresses. How do we connect them?",
  "expected_behavior": [
    "Identifies that overlapping CIDRs permanently block standard VPC peering and Transit Gateway attachments to the same route domain",
    "Does NOT attempt to suggest VPC peering or standard TGW between overlapping VPCs (that would fail)",
    "Proposes private NAT gateway between overlapping VPCs routed via TGW with distinct route domains (non-overlapping CIDR translation) or AWS PrivateLink to expose specific services without routing the full CIDR",
    "Recommends adopting AWS IPAM as source of truth to prevent further overlap in new VPCs",
    "Notes secondary CIDR blocks (including 100.64.0.0/10 CGNAT range) as an option for new subnet space without rebuilding VPCs",
    "Flags dual-stack IPv6 as a long-term path to avoid IPv4 exhaustion for large new footprints",
    "Acknowledges the complexity and asks clarifying questions: which VPCs need to communicate with which, and what specific services need to be shared?"
  ]
}
```

**Pass criteria**: The skill must NOT suggest VPC peering or TGW direct attachment for overlapping
CIDRs. It must offer PrivateLink and/or private NAT gateway as the feasible path. It should ask
clarifying questions about the actual communication requirements before designing a solution.

---

## Scenario 3 — Anti-Pattern Trap: Developer Requesting Direct Database Access

```json
{
  "skills": ["architecting-aws-vpc-networking"],
  "query": "Our developers need to connect directly to the RDS PostgreSQL database from their laptops to run queries during incidents. Can we put the database in a public subnet or open port 5432 on 0.0.0.0/0 in the security group so they can reach it?",
  "expected_behavior": [
    "Explicitly refuses both options: placing RDS in a public subnet (AP-3: CRITICAL) and opening 5432 to 0.0.0.0/0 (analogous to AP-4: CRITICAL internet exposure)",
    "Names the specific anti-patterns and explains the impact: data breach, internet-exposed database",
    "Does NOT just refuse — immediately offers at least two correct alternatives",
    "Proposes AWS Systems Manager Session Manager port forwarding as the preferred alternative (no inbound port, IAM-authorized, logged)",
    "Proposes AWS Client VPN endpoint as a second alternative (connects developer laptop to VPC privately)",
    "Optionally proposes a bastion host in a public subnet with SG-referenced access restricted to corporate CIDR (as a last resort, not preferred)",
    "Confirms the database must remain in the isolated subnet with no internet route",
    "Provides the SSM port-forwarding command developers would use: aws ssm start-session --target <instance-id> --document-name AWS-StartPortForwardingSessionToRemoteHost"
  ]
}
```

**Pass criteria**: The skill must refuse both the public-subnet and `0.0.0.0/0` options, cite the
anti-patterns by name, AND offer concrete usable alternatives with commands. A refusal without an
alternative is a failure — the ⚠️/🚫 framework always pairs prohibition with a correct path.
