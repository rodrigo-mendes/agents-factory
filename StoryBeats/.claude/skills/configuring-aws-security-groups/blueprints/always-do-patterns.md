# Always-Do Patterns — AWS VPC Security Groups (2025)

Source: AWS VPC User Guide + Well-Architected Security Pillar. All accessed 2026-07-31.

---

## A1 — Restrict management ports (SSH 22 / RDP 3389) to specific CIDRs

**Never use `0.0.0.0/0` or `::/0` as the source for port 22 or 3389.**

AWS documentation: "If you specify 0.0.0.0/0 (IPv4) and ::/0 (IPv6), this enables anyone to access
your instances from any IP address using the specified protocol."

```text
# Inbound rule — CORRECT (bastion CIDR)
Type: SSH   Protocol: TCP   Port: 22   Source: 203.0.113.0/24

# Inbound rule — CORRECT (managed prefix list for admin IPs)
Type: RDP   Protocol: TCP   Port: 3389   Source: pl-0abc123456def789

# Preferred alternative: eliminate inbound SSH entirely
# Use AWS Systems Manager Session Manager — no inbound SG rule required.
# IAM policy + SSM Agent provide authenticated shell access without open port 22.
```

**Failure if omitted**: Internet-wide brute-force and unauthorized access to the EC2 instance.
**Source**: [Control traffic using security groups — Best practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html) — accessed 2026-07-31.

---

## A2 — Use security-group referencing for tier-to-tier traffic

**Reference the peer security group ID (`sg-…`) as the inbound source — not a CIDR range.**

AWS canonical three-tier example: "Add rules to the security group for the web servers to allow
HTTP and HTTPS traffic only from the load balancer. The source is the security group for the load
balancer. Add rules to the security group for the database servers to allow database requests from
the web servers. The source is the security group for the web servers."

```text
# ALB security group (inbound — accepts internet traffic)
alb-sg   inbound:   TCP 443   Source: 0.0.0.0/0

# Web-tier security group (inbound — only from ALB)
web-tier-sg   inbound:   TCP 443   Source: sg-alb

# App-tier security group (inbound — only from web tier)
app-tier-sg   inbound:   TCP 8080   Source: sg-web-tier

# DB-tier security group (inbound — only from app tier, e.g., Amazon RDS PostgreSQL)
db-tier-sg   inbound:   TCP 5432   Source: sg-app-tier
```

**Why mandatory**: Ties access to group *membership*, not IP addresses. Survives instance
replacement, Auto Scaling events, and Elastic IP reassignment without rule updates.
**Source**: [Security group rules — Security group referencing](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html) — accessed 2026-07-31.

---

## A3 — Create the minimum number of groups, one per functional role

**One security group per functional layer.** Do not combine roles in a single catch-all group.

```text
# Correct: four functional groups for a three-tier web application
alb-sg       → internet-facing load balancer
web-tier-sg  → EC2 web servers (or ECS/EKS containers)
app-tier-sg  → EC2 application servers
db-tier-sg   → Amazon RDS / ElastiCache data tier

# Incorrect: single catch-all group
all-in-one-sg  → allows all ports from all directions
```

**Why mandatory**: AWS: "Use each security group to manage access to resources that have similar
functions and security requirements." Fewer groups reduce error risk; one-per-function makes rule
intent auditable.
**Source**: [Control traffic using security groups — Best practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html) — accessed 2026-07-31.

---

## A4 — Never open large port ranges

**Every rule must specify a single port (or a narrow named protocol). No wide ranges.**

```text
# Correct: single exact port
db-tier-sg   inbound:   TCP 5432   Source: sg-app-tier   # PostgreSQL only

# Correct: named protocol
alb-sg       inbound:   TCP 443    Source: 0.0.0.0/0     # HTTPS only

# Incorrect: open port range
web-tier-sg  inbound:   TCP 0-65535   Source: sg-alb     # too broad — avoid
```

**Why mandatory**: AWS: "Do not open large port ranges. Ensure that access through each port is
restricted to the sources or destinations that require it." Wide ranges violate least-privilege
(SEC05-BP02) and create an unauditable attack surface.
**Source**: [Control traffic using security groups — Best practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html) — accessed 2026-07-31.

---

## A5 — Restrict SG create/modify to specific IAM principals

**Use IAM policies and SCPs to control who can create, modify, or delete security groups.**

```json
{
  "Effect": "Deny",
  "Action": [
    "ec2:CreateSecurityGroup",
    "ec2:AuthorizeSecurityGroupIngress",
    "ec2:AuthorizeSecurityGroupEgress",
    "ec2:RevokeSecurityGroupIngress",
    "ec2:RevokeSecurityGroupEgress",
    "ec2:DeleteSecurityGroup"
  ],
  "Resource": "*",
  "Condition": {
    "StringNotEquals": {
      "aws:PrincipalTag/Role": ["NetworkAdmin", "SecurityAdmin"]
    }
  }
}
```

**Why mandatory**: Aligns with Well-Architected SEC05-BP04 (automate network protection). Prevents
unauthorized rule changes and enforces change control via IaC pipelines.
**Additional guidance**: Create a separate security group (or network interface) for management
traffic so a distinct IAM policy can govern change control on that group independently.
**Source**: [Control traffic using security groups — Best practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html); [SEC05-BP04](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html) — accessed 2026-07-31.

---

## A6 — Add NACLs as a defense-in-depth layer for production subnets

**For every production subnet, create a NACL with rules that mirror the security group intent.**

```text
# Production subnet NACL (inbound) — mirrors SG intent at subnet level
Rule 100   Allow   TCP 443   Source: 0.0.0.0/0      # HTTPS
Rule 200   Allow   TCP 1024-65535   Source: 0.0.0.0/0   # ephemeral return ports (NACLs are stateless)
Rule 32766 Deny    All       Source: 0.0.0.0/0       # implicit deny

# Production subnet NACL (outbound)
Rule 100   Allow   TCP 1024-65535   Dest: 0.0.0.0/0  # ephemeral return
Rule 200   Allow   TCP 443          Dest: 0.0.0.0/0  # outbound HTTPS
Rule 32766 Deny    All              Dest: 0.0.0.0/0  # implicit deny
```

**Why mandatory**: AWS: "Consider creating network ACLs with rules similar to your security groups,
to add an additional layer of security." NACLs provide subnet-wide protection if an instance is
launched without the correct security group — a fail-safe against misconfiguration.
**Note**: NACLs are stateless — you must explicitly allow both inbound and outbound ephemeral ports.
**Source**: [Control traffic using security groups — Best practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html); [Infrastructure security in Amazon VPC](https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html) — accessed 2026-07-31.

---

## A7 — Enable VPC Flow Logs

**Every production VPC must have flow logs enabled before workloads go live.**

```bash
# Create VPC Flow Logs to CloudWatch Logs
aws ec2 create-flow-logs \
  --resource-ids vpc-0abc123456def7890 \
  --resource-type VPC \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /vpc/flow-logs \
  --deliver-logs-permission-arn arn:aws:iam::123456789012:role/FlowLogsRole
# Expected: FlowLogId returned, no Unsuccessful entries
```

**Verify**:
```bash
aws ec2 describe-flow-logs \
  --filter "Name=resource-id,Values=vpc-0abc123456def7890" \
  --query 'FlowLogs[*].{Status:FlowLogStatus,Dest:LogDestination}' \
  --output table
# Expected: Status=ACTIVE
```

**Why mandatory**: AWS: Flow logs "can help you diagnose overly restrictive or overly permissive
security group and network ACL rules." Without flow logs, rule validation is guesswork.
**Source**: [Ensure internetwork traffic privacy in Amazon VPC — Flow logs](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Security.html) — accessed 2026-07-31.
