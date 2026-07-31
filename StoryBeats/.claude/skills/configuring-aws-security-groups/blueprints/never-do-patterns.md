# Never-Do Patterns — AWS VPC Security Groups (2025)

Source: AWS VPC User Guide + Well-Architected Security Pillar. All accessed 2026-07-31.

Every entry includes a side-by-side `❌ Wrong / ✅ Correct` using exact AWS service/resource names.

---

## N1 — Exposing SSH/RDP to the entire internet

**Why prohibited**: `0.0.0.0/0` on port 22 or 3389 "enables anyone to access your instances from
any IP address" — the single most common EC2 compromise vector. Internet-wide brute-force scanners
probe these ports continuously.

```text
❌ Wrong  (EC2 instance security group inbound rule)
   Type: SSH   Protocol: TCP   Port: 22   Source: 0.0.0.0/0

✅ Correct — option 1: restrict to a specific CIDR
   Type: SSH   Protocol: TCP   Port: 22   Source: 203.0.113.0/24  (corporate egress range)

✅ Correct — option 2: use a managed prefix list for admin IP ranges
   Type: SSH   Protocol: TCP   Port: 22   Source: pl-0abc123456def789

✅ Correct — option 3 (preferred): eliminate inbound SSH entirely
   # Use AWS Systems Manager Session Manager instead.
   # Requires: SSM Agent on the instance + IAM role with ssm:StartSession permission.
   # No inbound security group rule needed; no open port 22.
```

**Impact**: Internet-wide brute-force; unauthorized access to the EC2 instance; credential
exfiltration; ransomware deployment.

**Source**: [Control traffic using security groups — Best practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html) — accessed 2026-07-31.

---

## N2 — CIDR-based rules for intra-VPC tier-to-tier traffic

**Why prohibited**: Hard-coding the VPC CIDR or subnet CIDR as the source for tier-to-tier traffic
over-exposes the downstream tier to every IP in the range. A compromised host anywhere in the CIDR
can reach the database. AWS's canonical pattern references the *peer security group*, not a CIDR.

```text
❌ Wrong  (Amazon RDS PostgreSQL security group inbound rule)
   Type: PostgreSQL   Protocol: TCP   Port: 5432   Source: 10.0.0.0/16   (entire VPC CIDR)

✅ Correct
   Type: PostgreSQL   Protocol: TCP   Port: 5432   Source: sg-app-tier   (app-tier security group only)
```

**Impact**: Any compromised host in the VPC CIDR can reach the RDS instance; violates least
privilege (Well-Architected SEC05-BP02); SG referencing cannot be cleanly implemented later
without a rule change.

**Source**: [Security group rules — Security group referencing (example)](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html) — accessed 2026-07-31.

---

## N3 — Referencing a peer instance's security group for middlebox-routed traffic

**Why prohibited**: When traffic between two instances is routed through a middlebox appliance
(firewall, IDS/IPS, custom NAT), the network path is no longer instance-to-instance. AWS:
"If you reference the security group of the other instance as the source, this does not allow
traffic to flow between the instances." The failure is silent — the rule looks correct but
the traffic is dropped.

```text
❌ Wrong  (instance-A security group, traffic routed via a firewall appliance)
   Inbound   Source: sg-instance-b        (will NOT permit the middlebox-routed flow)

✅ Correct
   Inbound   Source: 10.0.2.0/24          (CIDR of the subnet containing instance B)
   # Or:
   Inbound   Source: 10.0.2.45/32         (private IP of instance B)
```

**Impact**: Silent connectivity failure; extremely difficult to diagnose because the security
group rule appears valid when inspected. Can block traffic from a newly introduced firewall
appliance in an existing working architecture.

**Source**: [Security group rules — Security group referencing (limitation)](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html) — accessed 2026-07-31.

---

## N4 — Relying on security groups to filter Route 53 Resolver DNS or EC2 Instance Metadata (IMDS)

**Why prohibited**: AWS explicitly documents that security groups *cannot* block DNS requests to
or from the Route 53 Resolver (the VPC+2 IP address). Network ACLs share the same limitation for
the Instance Metadata Service (IMDS) at `169.254.169.254`. Writing SG rules for these endpoints
creates a false sense of security — the traffic passes regardless.

```text
❌ Wrong  (attempting to block DNS exfiltration with a security group egress rule)
   Egress   Protocol: UDP   Port: 53   Dest: 0.0.0.0/0
   # Security groups have NO deny semantics, and cannot
   # block Route 53 Resolver or IMDS traffic in any case.

✅ Correct — DNS filtering
   # Use Route 53 Resolver DNS Firewall to filter/block DNS queries.
   # AWS Firewall Manager can centrally manage DNS Firewall policies.

✅ Correct — IMDS protection
   # Disable IMDSv1 and require IMDSv2 at the EC2 instance level:
   aws ec2 modify-instance-metadata-options \
     --instance-id i-0abc123456def7890 \
     --http-tokens required \
     --http-endpoint enabled
```

**Impact**: DNS-based command-and-control / exfiltration and IMDS credential theft remain
possible even with the rule in place. Security posture is worse than expected.

**Source**: [Security group rules — Limitation (Route 53 Resolver)](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html); [Network ACLs — Limitations (IMDS)](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html) — accessed 2026-07-31.

---

## N5 — Adding redundant return-traffic egress rules or expecting a deny effect

**Why prohibited**: Security groups are stateful — "if a security group allows inbound traffic to
an EC2 instance, responses are automatically allowed regardless of outbound security group rules."
Adding explicit return-traffic egress rules is harmless noise, but it signals a stateless mental
model. More dangerously: writing a rule intended as a *deny* has no effect — security groups
cannot deny traffic. The intended block never takes effect.

```text
❌ Wrong  (treating SG as stateless, like a NACL)
   Inbound    Allow   TCP 443   Source: 0.0.0.0/0
   Outbound   Allow   TCP 1024-65535   Dest: 0.0.0.0/0    ← unnecessary ephemeral return rule
   Inbound    Deny    TCP 22   Source: 198.51.100.0/24    ← deny has NO effect in a SG

✅ Correct
   Inbound    Allow   TCP 443   Source: sg-alb             ← return traffic auto-allowed (stateful)

   # To deny a specific source CIDR, use a Network ACL rule (stateless, subnet level):
   # NACL inbound rule #90   DENY   TCP 22   Source: 198.51.100.0/24
```

**Impact**: Over-broad egress rules (noise) that complicate audits; a nonexistent "deny" that
never blocks the intended traffic, leaving a security gap that appears closed.

**Source**: [Compare security groups and network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html); [Security group rules — "You can specify allow rules, but not deny rules"](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html) — accessed 2026-07-31.

---

## N6 — Naming a security group with the reserved `sg-` prefix

**Why prohibited**: AWS reserves the `sg-` prefix for security group *resource IDs*
(e.g., `sg-0abc1234567890abc`). The API explicitly rejects names starting with `sg-`:
"A security group name can't start with `sg-`." Names must also be unique within the VPC and
≤ 255 characters.

```text
❌ Wrong
   Name: sg-web-tier           ← rejected — collides with the reserved resource-ID prefix

✅ Correct
   Name: web-tier-sg           ← descriptive, ≤ 255 chars, unique within VPC
   Name: alb-sg                ← short, purpose-clear
   Name: db-tier-sg            ← consistent with function-sg convention
```

**Impact**: `CreateSecurityGroup` API call fails; Terraform `aws_security_group` resource reports
an error at `apply` time; CloudFormation stack creation fails with a validation error.

**IaC pattern to avoid**:
```hcl
# Terraform — WRONG
resource "aws_security_group" "web" {
  name = "sg-${var.environment}-web"   # fails: starts with sg-
}

# Terraform — CORRECT
resource "aws_security_group" "web" {
  name = "${var.environment}-web-sg"   # passes: follows <env>-<function>-sg convention
}
```

**Source**: [Control traffic using security groups — Security group basics](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html) — accessed 2026-07-31.
