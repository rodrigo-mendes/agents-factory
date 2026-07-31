# Never Do Patterns — AWS Shield DDoS Architecture

> Source: AWS WAF Developer Guide + Well-Architected Security Pillar SEC05. All sources accessed 2026-07-31.
> Each anti-pattern includes: risk level, blast radius, wrong architecture, correct alternative, and detection commands.

---

## Anti-Pattern 1: Expose EC2 instances directly to the internet without edge/ALB + WAF + Shield

**Risk level**: CRITICAL
**Blast radius**: Full application — the exposed instance can be saturated (L3/L4) or flooded (L7), causing complete outage. No cost protection applies.
**SEC05 violation**: BP01 (Create network layers), BP02 (Control traffic flow)

### Wrong
```
# EC2 instance with a public IP, serving HTTP(S) directly
# No CloudFront, no ALB, no AWS WAF, no Shield Advanced protection on the instance IP

Internet --[public IP]--> EC2 instance (port 80/443 open to 0.0.0.0/0)
```

### Correct
```
Internet
  --> Route 53 (health-checked)
  --> CloudFront distribution + AWS WAF web ACL          [Shield Advanced applied]
  --> Application Load Balancer + AWS WAF web ACL        [Shield Advanced applied]
  --> EC2 / ECS in private subnet
      (security group: allow ingress ONLY from ALB/CloudFront prefix list)

# Shield Advanced must also be applied to:
# - the CloudFront distribution ARN
# - the ALB ARN (or its Elastic IP if using NLB)
# - the Route 53 hosted zone ARN
```

**Detection**:
```bash
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].{ID:InstanceId,PublicIP:PublicIpAddress}' | grep -v null
# Any instance with a PublicIpAddress serving application traffic is a CRITICAL risk

aws shield list-protections
# Absence of the EC2 EIP/ALB ARN confirms no Shield coverage
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-edge-services.html

---

## Anti-Pattern 2: Rely on Shield Standard alone for business-critical or regulated workloads

**Risk level**: HIGH
**Blast radius**: Revenue and availability of the critical application during an L7 flood or sophisticated attack — with no SRT, no expert mitigation, and no cost protection.
**SEC05 violation**: BP03 (Implement inspection-based protection)

### Wrong
```
# Payments checkout API, no Shield Advanced, no WAF
# Only default Shield Standard (L3/L4 automatic, no L7)

Internet --> ALB (public) --> EC2 application
# Shield Standard is "on" but provides: no L7, no SRT, no proactive engagement, no cost protection
```

### Correct
```
# Subscribe Shield Advanced at the payer account
aws shield subscribe

# Protect the ALB
aws shield create-protection --name "PaymentsALB" --resource-arn <alb-arn>

# Attach WAF with managed rules + rate-based rules
aws wafv2 associate-web-acl --web-acl-arn <acl-arn> --resource-arn <alb-arn> --region <region>

# Enable SRT access, health-based detection, proactive engagement (see always-do-patterns.md)
```

**Detection**:
```bash
aws shield describe-subscription
# Missing or "SubscriptionState": "INACTIVE" on a business-critical account = HIGH risk

aws wafv2 list-resources-for-web-acl --web-acl-arn <arn>
# Absence of critical endpoint ARN = L7 gap
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-overview.html

---

## Anti-Pattern 3: Skip health-based detection (no Route 53 health checks on protected resources)

**Risk level**: HIGH
**Blast radius**: Proactive engagement is silently non-functional; detection is slower and more prone to false positives for the affected resource.
**SEC05 violation**: BP03

### Wrong
```
# ALB protected by Shield Advanced — but no Route 53 health check associated
aws shield create-protection --name "MyALB" --resource-arn <alb-arn>
# No associate-health-check call made
# Result: describe-protection shows empty HealthCheckIds
# Result: proactive engagement = silently disabled for this resource
```

### Correct
```bash
# 1. Create the Route 53 health check
aws route53 create-health-check --caller-reference "$(date +%s)" \
  --health-check-config Type=HTTPS,FullyQualifiedDomainName=api.example.com,Port=443,ResourcePath=/health

# 2. Associate it with the Shield Advanced protection
aws shield associate-health-check \
  --protection-id <protection-id> \
  --health-check-arn arn:aws:route53:::healthcheck/<health-check-id>

# Verify
aws shield describe-protection --protection-id <protection-id> --query 'Protection.HealthCheckIds'
# Expected: non-empty array
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html

---

## Anti-Pattern 4: Skip SRT pre-configuration before an attack

**Risk level**: HIGH
**Blast radius**: Extended outage during an active attack — SRT cannot access WAF logs/APIs to build mitigations, wasting the most critical response minutes.
**SEC05 violation**: BP03

### Wrong
```
# Shield Advanced subscribed, but during setup:
# "Do not grant the SRT access to my account" was selected
# Account is on Developer support plan (SRT requires Business or Enterprise)

# During an attack: SRT cannot help — no IAM role, no log access, wrong support plan
```

### Correct
```bash
# 1. Ensure Business or Enterprise Support plan is active (verify in AWS Support console)

# 2. Create the SRT IAM role (via console "Configure AWS SRT support" OR CLI)
aws iam create-role --role-name ShieldDRTAccessRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Principal": {"Service": "drt.shield.amazonaws.com"}, "Action": "sts:AssumeRole"}]
  }'
aws iam attach-role-policy --role-name ShieldDRTAccessRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSShieldDRTAccessPolicy

# 3. Grant the role to Shield
aws shield associate-drt-role --role-arn arn:aws:iam::<account-id>:role/ShieldDRTAccessRole

# Verify
aws shield describe-drt-access
# Expected: non-empty RoleArn
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/authorize-srt.html

---

## Anti-Pattern 5: Ignore DDoS cost protection (unprotected resources or unclaimed credits)

**Risk level**: MEDIUM
**Blast radius**: Finance — unbounded attack-driven bill spike (DTO + scaling) with no reimbursement path.

### Wrong
```
# Internet-facing resources left outside Shield Advanced

aws shield list-protections
# Public CloudFront distribution ARN and ALB ARN are NOT in the output

# Attack-driven DTO spike on unprotected resources → fully billable, no credit eligibility
# Or: attack occurred on a protected resource but no credit was ever requested
```

### Correct
```bash
# 1. Protect all public resources before any spike
aws shield create-protection --name "MyCloudFront" --resource-arn <cloudfront-arn>
aws shield create-protection --name "MyALB" --resource-arn <alb-arn>

# 2. After an attack-driven cost spike: open an AWS Support case
# Request a Shield Advanced service credit citing the attack event ID
# (Use AWS Support console or the AWS Support API — no dedicated Shield credit CLI)

# Monitor for anomalies with Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=<start>,End=<end> \
  --granularity DAILY \
  --metrics "UnblendedCost" \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["AWS Data Transfer"]}}'
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html

---

## Anti-Pattern 6: Use Shield without AWS WAF for HTTP/HTTPS endpoints (layer-7 gap)

**Risk level**: HIGH
**Blast radius**: Any HTTP/HTTPS endpoint — vulnerable to web request floods despite Shield being active.
**SEC05 violation**: BP03

### Wrong
```
# CloudFront distribution with Shield Advanced — but no WAF web ACL attached
# Shield "on" → only L3/L4 protection at the network edge
# HTTP GET flood hits the origin unfiltered

aws shield list-protections
# CloudFront ARN is protected

aws wafv2 list-resources-for-web-acl --web-acl-arn <any-arn>
# CloudFront distribution ARN is NOT associated with any web ACL
# Result: L7 floods pass through Shield to the origin
```

### Correct
```bash
# Attach WAF web ACL to the CloudFront distribution
aws wafv2 associate-web-acl \
  --web-acl-arn arn:aws:wafv2:us-east-1:<account-id>:global/webacl/<name>/<id> \
  --resource-arn arn:aws:cloudfront::<account-id>:distribution/<dist-id>

# Enable automatic application layer DDoS mitigation (start in count, then block)
# (Via Shield console: Protection -> Layer 7 DDoS mitigation -> Enable -> Count -> Block)

# Verify WAF is associated
aws wafv2 list-resources-for-web-acl \
  --web-acl-arn arn:aws:wafv2:us-east-1:<account-id>:global/webacl/<name>/<id> \
  --resource-type CLOUDFRONT --region us-east-1
# Expected: CloudFront distribution ARN present
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-responding.html

---

## Anti-Pattern 7: Single-region deployment with no Route 53 failover or edge front

**Risk level**: MEDIUM
**Blast radius**: The whole application if the single regional entry point is saturated — no failover, no edge absorption.
**SEC05 violation**: BP01 (Create network layers), BP02 (Control traffic flow)

### Wrong
```
# Single Route 53 A-record pointing to a single-region ALB
# No health-check-based failover, no CloudFront, no Global Accelerator

Route 53 A record --> ALB (us-east-1 only)
# Attack saturates the ALB → full outage with no failover path
```

### Correct
```
# Front with CloudFront and/or Global Accelerator for edge absorption
# Use Route 53 health-checked failover or latency-based routing across regions
# Protect all entry points with Shield Advanced

Route 53 (failover/latency routing + health checks)
  --> CloudFront distribution [Shield Advanced] + WAF
      --> ALB us-east-1 [Shield Advanced] + WAF --> origin (private)
      --> ALB eu-west-1 [Shield Advanced] + WAF --> origin (private)  [failover target]
```

**Detection**:
```bash
aws route53 list-resource-record-sets --hosted-zone-id <zone-id> \
  --query 'ResourceRecordSets[?Type==`A`].[Name,FailoverType,HealthCheckId]'
# Expected: FailoverType = PRIMARY/SECONDARY and HealthCheckId present
# Simple A-record with no failover or health check = MEDIUM risk for blast-radius
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-edge-services.html
