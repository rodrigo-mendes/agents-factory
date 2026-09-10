# Evaluation Scenarios — designing-aws-vpc-networks

Six test cases for `/evaluating-skill-scenarios designing-aws-vpc-networks`.

---

## Scenario 1 — Canonical Use: Three-Tier Production VPC

```json
{
  "skills": ["designing-aws-vpc-networks"],
  "query": "Design a production VPC for a web application with EC2 Auto Scaling backend and RDS database across two Availability Zones in us-east-1.",
  "expected_behavior": [
    "Specifies three subnet tiers per AZ: public (IGW + ALB + NAT GW), private (EC2 Auto Scaling), isolated (RDS Multi-AZ)",
    "Specifies one NAT Gateway per AZ in the public subnet of each AZ, not a shared single NAT GW",
    "Recommends /16–/20 VPC CIDR and /24 minimum per tier per AZ",
    "Includes ALB in public subnets with WAF attached, EC2 in private subnets with no public IP",
    "Adds S3 and DynamoDB Gateway Endpoints in private subnet route tables",
    "Includes VPC Flow Logs enabled at VPC level publishing to S3",
    "References Security Hub EC2.9 to detect any public IPs on app/data tiers"
  ]
}
```

---

## Scenario 2 — Multi-Account Enterprise: When to Choose Transit Gateway

```json
{
  "skills": ["designing-aws-vpc-networks"],
  "query": "We have 8 VPCs across 4 AWS accounts (dev, staging, prod, shared-services) and need transitive routing between them plus Direct Connect to on-premises. Should we use VPC Peering or Transit Gateway?",
  "expected_behavior": [
    "Recommends Transit Gateway — 8 VPCs exceeds the 3-VPC threshold for peering scalability",
    "Explains O(n²) peering mesh problem (28 peering connections for 8 VPCs full mesh)",
    "Recommends TGW in a dedicated Network Services account following hub-and-spoke pattern",
    "Mentions TGW route table segmentation for prod/non-prod isolation",
    "Recommends Direct Connect primary + Site-to-Site VPN as encrypted backup path",
    "Does NOT recommend VPC Peering for this scenario",
    "Mentions TGW per-AZ CloudWatch metrics (Late 2024) for observability"
  ]
}
```

---

## Scenario 3 — Security Decision: Operational Access to Private EC2 Instances

```json
{
  "skills": ["designing-aws-vpc-networks"],
  "query": "Our developers need SSH access to EC2 instances in private subnets. The team proposes opening port 22 in the security group to the corporate IP range 203.0.113.0/24. Is this the right approach?",
  "expected_behavior": [
    "Does NOT recommend opening SSH port 22 in the security group, even to a corporate CIDR",
    "Recommends AWS Systems Manager Session Manager as the preferred alternative (no open ports)",
    "Explains that SSM Session Manager works from private subnets via PrivateLink (ssm, ssmmessages, ec2messages Interface endpoints)",
    "References Security Hub EC2.13 (SSH from 0.0.0.0/0) and the principle of least-privilege",
    "If the team insists on SSH, specifies restricting to a dedicated bastion SG ID (not a CIDR) and monitoring via CloudTrail",
    "Does NOT suggest 0.0.0.0/0 as the source under any circumstances"
  ]
}
```

---

## Scenario 4 — Anti-Pattern Trap: Small CIDR for Cost Saving

```json
{
  "skills": ["designing-aws-vpc-networks"],
  "query": "To save IP space and reduce complexity, our architect wants to use a /26 VPC CIDR (64 IPs) for a new production environment. Is that acceptable?",
  "expected_behavior": [
    "Rejects /26 as too small for a production VPC — flags HIGH risk",
    "Explains that the initial VPC CIDR cannot be changed or deleted (REL02-BP03)",
    "Explains that each subnet reserves 5 IPs (first 4 + last 1), leaving 59 usable in a /26",
    "Lists services blocked by NAU exhaustion: EC2, NLBs, endpoints, Lambda, TGW attachments, NAT GWs",
    "Recommends /16 for most production workloads, minimum /20 for small environments",
    "Recommends AWS IPAM for allocation governance to avoid this issue systematically",
    "Mentions CloudWatch metric NetworkAddressUsage (namespace AWS/EC2) for ongoing monitoring"
  ]
}
```

---

## Scenario 5 — Cost Optimization: High NAT Gateway Data Processing Charges

```json
{
  "skills": ["designing-aws-vpc-networks"],
  "query": "Our monthly AWS bill shows $800/month in NAT Gateway data processing charges. Our application in private subnets frequently reads large files from S3 and queries DynamoDB. How do we reduce this cost?",
  "expected_behavior": [
    "Identifies the root cause: S3 and DynamoDB traffic routing through NAT Gateway incurring $0.045/GB processing charges",
    "Recommends Gateway VPC Endpoints for both S3 and DynamoDB (free, no hourly charge)",
    "Explains that Gateway Endpoints require only a route table entry pointing the S3/DynamoDB prefix list to the endpoint",
    "Confirms traffic stays on the AWS network — no internet traversal",
    "Notes that Gateway endpoints do not support on-premises access (Interface endpoints needed for that case)",
    "Estimates the cost impact based on traffic volume redirected away from NAT GW"
  ]
}
```

---

## Scenario 6 — Edge Case: Compliance Requiring In-Transit Encryption Without Application Changes

```json
{
  "skills": ["designing-aws-vpc-networks"],
  "query": "Our HIPAA auditors require in-transit encryption for all traffic between Fargate tasks and Application Load Balancers. Our engineering team says updating TLS configuration in all application containers is too risky before the audit. Is there an AWS-native solution?",
  "expected_behavior": [
    "Recommends VPC Encryption Controls (GA November 2025, paid from March 2026)",
    "Explains it enforces hardware-based AES-256 in-transit encryption on Fargate, NLB, and ALB paths without application code changes",
    "Recommends starting in Monitor mode (audit — logs unencrypted connections) before switching to Enforce mode",
    "Mentions Declarative Policy via AWS Organizations (available July 6, 2026) for org-wide enforcement without per-account configuration",
    "References HIPAA §164.312(e)(1) transmission security and PCI DSS 4.2 compliance alignment",
    "Combines recommendation with VPC Block Public Access Declarative Policy for a complete preventive control baseline"
  ]
}
```
