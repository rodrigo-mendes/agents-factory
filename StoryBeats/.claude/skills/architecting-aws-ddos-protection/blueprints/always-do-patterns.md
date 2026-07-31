# Always Do Patterns — AWS Shield DDoS Architecture

> Source: AWS WAF Developer Guide + Well-Architected Security Pillar SEC05. All sources accessed 2026-07-31.

---

## Pattern 1: Enable Shield Advanced on every internet-facing resource

**Why**: Shield Advanced "doesn't automatically protect your resources" — protection applies only to resources you explicitly specify. Any unprotected public resource creates a gap in the DDoS perimeter. (SEC05-BP03)

**Protectable resource types**:
- Amazon CloudFront distributions
- Amazon Route 53 hosted zones
- AWS Global Accelerator standard accelerators
- Amazon EC2 Elastic IP addresses (protects attached instances/NLBs)
- Application Load Balancers
- Classic Load Balancers

**Architecture decision**: Inventory every internet-facing resource; add each to Shield Advanced via console/API or enforce via a Firewall Manager Shield Advanced policy so new resources are auto-covered.

**Verification**:
```bash
aws shield list-protections --query 'Protections[*].{Name:Name,Resource:ResourceArn}'
# Every public resource ARN must appear in the output
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-protected-resources.html

---

## Pattern 2: Subscribe to Shield Advanced before an attack (proactive, not reactive)

**Why**: Shield Advanced is a subscription with a 1-year commitment. SRT access, proactive engagement, custom mitigations, and health-based detection all require pre-configuration. You cannot obtain the Advanced posture mid-attack. (SEC05-BP03/BP04)

**Architecture decision**: Subscribe at the organization payer account level; one subscription covers all accounts in the consolidated-billing family. Enroll critical accounts; configure SRT access and proactive engagement as part of onboarding.

**Verification**:
```bash
aws shield describe-subscription
# Expected: "SubscriptionState": "ACTIVE" with valid StartTime and EndTime
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary.html

---

## Pattern 3: Attach AWS WAF to every L7 entry point

**Why**: "Shield Advanced uses AWS WAF web ACLs, rules, and rule groups as part of its application layer protections." Shield's network-layer protection does NOT stop HTTP/HTTPS request floods. Your Shield Advanced subscription covers standard AWS WAF fees up to 1,500 WCUs per protected resource. (SEC05-BP03)

**Architecture decision**: Attach an AWS WAF web ACL to every L7 entry point (CloudFront distribution and regional ALB). Include AWS Managed Rules + the Layer 7 Anti-DDoS Amazon Managed Rule group (included with Shield Advanced) + rate-based rules.

**Verification**:
```bash
# CloudFront (must be us-east-1 for CLOUDFRONT scope)
aws wafv2 list-web-acls --scope CLOUDFRONT --region us-east-1

# Regional ALB
aws wafv2 list-web-acls --scope REGIONAL --region <region>
aws wafv2 list-resources-for-web-acl --web-acl-arn <arn> --resource-type APPLICATION_LOAD_BALANCER --region <region>
# Expected: ALB ARN listed as associated resource
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html

---

## Pattern 4: Enable health-based detection via Route 53 health checks

**Why**: "Using health checks with Shield Advanced helps prevent false positives and provides faster detection and mitigation when a protected resource is unhealthy." Hard prerequisite: "Shield Advanced proactive engagement is available only for resources that have health-based detection enabled." (SEC05-BP03)

**Scope**: All protected resource types except Route 53 hosted zones.

**Architecture decision**: Create a Route 53 health check per critical resource and associate it in Shield Advanced during onboarding.

**Verification**:
```bash
aws shield describe-protection --protection-id <ID> --query 'Protection.HealthCheckIds'
# Expected: non-empty array — e.g., ["abc12345-..."]
# Empty array means proactive engagement is non-functional for this resource
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html

---

## Pattern 5: Pre-configure SRT access (IAM role + support plan)

**Why**: The SRT can only act on your behalf if you grant permissions before an event. The role trusts service principal `drt.shield.amazonaws.com` and must have `AWSShieldDRTAccessPolicy` attached. SRT use also requires a Business or Enterprise Support plan. (SEC05-BP03)

**Architecture decision**: During Shield Advanced onboarding, use "Create a new role for the SRT" (or attach `AWSShieldDRTAccessPolicy` to an existing role trusting `drt.shield.amazonaws.com`). Confirm the account is on Business/Enterprise Support.

**Verification**:
```bash
aws shield describe-drt-access
# Expected: non-empty "RoleArn" field

# Verify IAM role trust policy
aws iam get-role --role-name <ShieldDRTAccessRole> --query 'Role.AssumeRolePolicyDocument'
# Expected: Principal contains "drt.shield.amazonaws.com"

# Verify managed policy
aws iam list-attached-role-policies --role-name <ShieldDRTAccessRole>
# Expected: AWSShieldDRTAccessPolicy listed
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/authorize-srt.html

---

## Pattern 6: Enable SRT proactive engagement with current 24x7 contacts

**Why**: With proactive engagement, "the SRT can proactively contact you… triages the DDoS event and creates AWS WAF mitigations." This shortens time-to-mitigation for large L7 attacks. Requires health-based detection. (SEC05-BP04)

**Architecture decision**: Enable proactive engagement during onboarding. Provide primary and secondary contact details (email, phone, time zone). Keep contacts current — outdated contacts defeat proactive engagement.

**Verification**:
```bash
aws shield describe-emergency-contact-settings
# Expected: "EmergencyContactList" with at least one entry containing EmailAddress and PhoneNumber

aws shield describe-subscription --query 'Subscription.ProactiveEngagementStatus'
# Expected: "ENABLED"
# "PENDING" means health-based detection has not been set up yet
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-responding.html

---

## Pattern 7: Rely on DDoS cost protection — protect all resources and request credits

**Why**: "Shield Advanced offers some cost protection against spikes in your AWS bill that might result from a DDoS attack against your protected resources… including coverage for spikes in Shield Advanced data transfer out (DTO) usage fees." Coverage applies to protected resources only and is delivered as service credits (not automatic refunds).

**Architecture decision**: Protect every internet-facing resource with Shield Advanced (so all are credit-eligible). After an attack that drove a DTO/scaling cost spike, file a credit request via AWS Support.

**Verification**:
```bash
# Before any spike: confirm all public resources are protected
aws shield list-protections --query 'Protections[*].ResourceArn'

# After a spike: open an AWS Support case requesting a Shield Advanced service credit
# (no CLI; requires AWS Support console or API)
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html

---

## Pattern 8: Centralize visibility via Firewall Manager + CloudWatch + Security Hub

**Why**: Shield Advanced provides advanced real-time metrics and reports. Firewall Manager can centralize monitoring across accounts using SNS/Security Hub and auto-applies Shield/WAF protections org-wide at no additional charge for Advanced customers. (SEC05-BP04)

**Architecture decision**: Deploy a Firewall Manager Shield Advanced policy from the org security account; route findings to Security Hub and CloudWatch dashboards/alarms for DDoS metrics (`DDoSDetected`, attack volume).

**Verification**:
```bash
aws fms list-policies
# Expected: at least one Shield Advanced policy

# CloudWatch: verify DDoS alarm exists
aws cloudwatch describe-alarms --alarm-names "DDoSDetected-<resource>"
# Expected: alarm configured on DDoSDetected metric

# Security Hub: verify Firewall Manager integration
aws securityhub describe-hub
# Expected: Security Hub enabled; Firewall Manager findings appear in findings list
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-summary-capabilities.html

---

## Pattern 9: Add AWS WAF rate-based rules as layered defense

**Why**: AWS DDoS resiliency best practices recommend rate-based rules to limit requests from individual source IPs. Shield Advanced automatic app-layer mitigation itself enforces AWS WAF rate limiting on known DDoS sources. (SEC05-BP03/BP04)

**Architecture decision**: Add rate-based rules with thresholds tuned to your normal traffic profile. Start in "count" mode to observe, then switch to "block" once thresholds are calibrated.

**Verification**:
```bash
aws wafv2 get-web-acl --name <acl-name> --scope <CLOUDFRONT|REGIONAL> --id <acl-id> --region <region> \
  --query 'WebACL.Rules[?Type==`RATE_BASED`]'
# Expected: at least one RateBasedStatement rule present

# Check sampled requests to validate threshold is triggering appropriately
aws wafv2 get-sampled-requests --web-acl-arn <arn> --rule-metric-name <rate-rule-metric> \
  --scope <scope> --time-window Start=<iso-start>,End=<iso-end> --max-items 100
```

**Source**: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-edge-services.html
