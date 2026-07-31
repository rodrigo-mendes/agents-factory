# Evaluation Scenarios — configuring-aws-security-groups

Use these scenarios to verify that an agent consuming the `configuring-aws-security-groups` skill
produces correct, well-sourced, and pattern-compliant outputs.

---

## Scenario 1 — Canonical: Three-tier web application security group design

```json
{
  "skills": ["configuring-aws-security-groups"],
  "query": "Design the security groups for a three-tier web application on AWS: an Application Load Balancer (public-facing), EC2 web servers in a private subnet, and an Amazon RDS PostgreSQL database in an isolated subnet. The application serves HTTPS traffic. A developer asked to allow all inbound traffic on all ports to simplify development.",
  "expected_behavior": [
    "Creates four distinct security groups: alb-sg, web-tier-sg, app-tier-sg (or equivalent), db-tier-sg",
    "ALB security group allows inbound TCP 443 from 0.0.0.0/0",
    "Web-tier security group allows inbound TCP 443 from sg-alb (SG referencing, not CIDR)",
    "DB-tier security group allows inbound TCP 5432 from sg-web-tier (SG referencing)",
    "Names follow <function>-sg convention (not sg-<function>)",
    "Explicitly rejects the 'allow all traffic' request; explains least-privilege (A3, A4)",
    "Recommends enabling VPC Flow Logs (A7)",
    "Recommends NACL defense-in-depth layer for production subnets (A6)"
  ]
}
```

**Pass criteria**: The agent uses SG referencing for all tier-to-tier rules (A2), refuses to allow
all-ports traffic (A4), and names groups correctly (not starting with `sg-`) (N6).

---

## Scenario 2 — Edge case: Middlebox-routed traffic between instances

```json
{
  "skills": ["configuring-aws-security-groups"],
  "query": "We have two EC2 instances (instance-A in subnet 10.0.1.0/24 and instance-B in subnet 10.0.2.0/24) that need to communicate on TCP 8080. All traffic between subnets is routed through a third-party firewall appliance. A colleague suggested adding the security group of instance-B as the inbound source on instance-A's security group. Is this correct?",
  "expected_behavior": [
    "Correctly identifies this as a middlebox-routed topology",
    "States that SG referencing will NOT work in this case (N3)",
    "Explains why: traffic traverses a firewall appliance, so the source IP seen by instance-A is the appliance's IP, not instance-B's SG membership",
    "Recommends using the subnet CIDR of instance-B (10.0.2.0/24) or the private IP of instance-B as the inbound source",
    "Does NOT suggest using sg-instance-b as the source",
    "Links the decision to Ask-First decision C3 (SG referencing vs. CIDR)"
  ]
}
```

**Pass criteria**: The agent catches the middlebox caveat from N3, rejects SG referencing as the
source, and recommends the CIDR alternative with an explanation.

---

## Scenario 3 — Misuse trap: Deny rule and stateless mental model

```json
{
  "skills": ["configuring-aws-security-groups"],
  "query": "I need to block all traffic from the IP range 198.51.100.0/24 to our web servers. I also want to add an outbound rule to allow TCP 1024-65535 so that the responses to inbound HTTPS requests can leave the instance. Please create the security group rules.",
  "expected_behavior": [
    "Rejects the 'block IP range via security group' request; explains security groups are allow-only and cannot express deny rules (N5)",
    "Directs to Network ACL as the correct tool for explicit deny (C1)",
    "Provides the correct NACL rule: inbound DENY TCP source 198.51.100.0/24 at a lower rule number than the allow rule",
    "Rejects the outbound TCP 1024-65535 rule as unnecessary; explains statefulness (N5)",
    "Clarifies that return traffic for allowed inbound HTTPS is automatically permitted without an explicit egress rule",
    "Does not create the redundant outbound ephemeral-return rule"
  ]
}
```

**Pass criteria**: The agent demonstrates knowledge of statefulness (return traffic auto-allowed),
explains that deny rules belong in NACLs not SGs, and does not produce the unnecessary egress rule.

---

## Scenario 4 — Anti-pattern trap: Security group naming

```json
{
  "skills": ["configuring-aws-security-groups"],
  "query": "Generate the Terraform code to create a security group named 'sg-web-tier' for the web servers.",
  "expected_behavior": [
    "Flags that the name 'sg-web-tier' starts with the reserved 'sg-' prefix (N6)",
    "Explains the API will reject CreateSecurityGroup with this name",
    "Proposes a compliant name such as 'web-tier-sg' or 'web-sg'",
    "Produces Terraform code using the corrected name (e.g., name = 'web-tier-sg')",
    "Mentions the uniqueness-within-VPC constraint"
  ]
}
```

**Pass criteria**: The agent catches the naming violation (N6) before generating code, proposes
a compliant alternative, and produces IaC with the corrected name.
