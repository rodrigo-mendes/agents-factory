# Integration Patterns — architecting-aws-vpc-networking

VPC integration patterns for the most common AWS service combinations in a production three-tier
workload. All patterns verified against Amazon VPC User Guide, 2026-07-31.

---

## VPC ↔ EC2 / ECS (Compute Tier)

**Placement**: Private app subnets per AZ. Route `0.0.0.0/0` to same-AZ NAT gateway.

**Security group pattern**:
```
alb-sg:  inbound HTTPS 443 from 0.0.0.0/0
app-sg:  inbound <app-port> from alb-sg      (ALB targets app instances)
         outbound 443 to 0.0.0.0/0            (for external API calls via NAT)
         outbound <db-port> to db-sg           (to data tier)
```

**ECS with Fargate** (attach a task ENI to the same subnets):
- Task definition must include the VPC subnet IDs and the app security group.
- For private tasks, the subnet must have NAT gateway egress (or all required endpoints).
- Add interface endpoints for ECR (`ecr.api`, `ecr.dkr`), Secrets Manager, and CloudWatch Logs
  if tasks run in isolated subnets.

**Common problem**: ECS Fargate task fails to pull image from ECR.
**Solution**: Confirm interface endpoints exist for `com.amazonaws.<region>.ecr.dkr` and
`com.amazonaws.<region>.ecr.api`; confirm the endpoint SG allows HTTPS 443 from the task SG.

---

## VPC ↔ RDS / ElastiCache (Data Tier)

**Placement**: Isolated subnets — route table has only `local` + VPC endpoint routes; no default
route to IGW or NAT.

**Security group pattern**:
```
db-sg:
  inbound  TCP 5432 (PostgreSQL) / 3306 (MySQL) / 6379 (Redis) from app-sg only
  outbound (none required; stateful SG auto-allows responses)
```

**RDS subnet group** — must span ≥2 AZs:
```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name prod-db-subnet-group \
  --db-subnet-group-description "Isolated subnets for RDS Multi-AZ" \
  --subnet-ids subnet-data-1a subnet-data-1b subnet-data-1c
```

**RDS Multi-AZ** — enables synchronous standby in a second AZ. Automatic failover typically
completes in 60–120 seconds. The endpoint DNS name stays the same post-failover.

**Common problem**: Application in app subnet cannot connect to RDS.
**Solution**: (1) Confirm db-sg allows ingress from app-sg on the correct port. (2) Confirm both
are in the same VPC. (3) Confirm the RDS instance is NOT set to Publicly Accessible.

---

## VPC ↔ S3 / DynamoDB (Gateway Endpoints — Free)

Gateway endpoints add a route-table entry directing S3/DynamoDB traffic over the AWS network
without traversing NAT or IGW. No ENI is created; no hourly charge.

```bash
# Create S3 gateway endpoint and add to all private + isolated route tables
aws ec2 create-vpc-endpoint \
  --vpc-id <vpc-id> \
  --service-name com.amazonaws.<region>.s3 \
  --route-table-ids \
    rtb-private-1a rtb-private-1b rtb-private-1c \
    rtb-isolated-1a rtb-isolated-1b rtb-isolated-1c

# Create DynamoDB gateway endpoint similarly
aws ec2 create-vpc-endpoint \
  --vpc-id <vpc-id> \
  --service-name com.amazonaws.<region>.dynamodb \
  --route-table-ids \
    rtb-private-1a rtb-private-1b rtb-private-1c \
    rtb-isolated-1a rtb-isolated-1b rtb-isolated-1c
```

**Bucket policy (restrict access to VPC endpoint)**:
```json
{
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:*",
  "Resource": ["arn:aws:s3:::my-bucket", "arn:aws:s3:::my-bucket/*"],
  "Condition": {
    "StringNotEquals": {
      "aws:SourceVpce": "vpce-xxxx"
    }
  }
}
```

**Cost impact**: Removing S3/DynamoDB traffic from NAT gateway eliminates NAT data-processing
charges for that traffic, which can be significant at high throughput.

---

## VPC ↔ Transit Gateway (Multi-VPC Hub)

Each VPC attaches to TGW once. TGW route tables define which attachments can reach which
(segmentation between prod/dev/shared-services).

```bash
# Create TGW attachment for a VPC
aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id tgw-xxxx \
  --vpc-id <vpc-id> \
  --subnet-ids subnet-app-1a subnet-app-1b  # one subnet per AZ used
```

**Route table segmentation example**:
```
TGW route table "prod" propagates: vpc-prod, vpc-shared-services
TGW route table "dev"  propagates: vpc-dev,  vpc-shared-services
# prod and dev cannot route to each other — segmented
```

**Centralized egress pattern**: Route `0.0.0.0/0` in spoke VPC private route tables to TGW
instead of a per-VPC NAT gateway. TGW forwards to an inspection/egress VPC containing a NAT
gateway and/or AWS Network Firewall. Spoke VPCs need no NAT gateway of their own.

**Common problem**: Spoke VPC cannot reach shared-services VPC after TGW attachment.
**Solution**: (1) Confirm the spoke's route table has a route for the shared-services CIDR → TGW.
(2) Confirm the TGW route table for the spoke attachment propagates or has a static route for the
shared-services VPC. (3) Confirm CIDRs are non-overlapping.

---

## VPC ↔ GuardDuty / CloudWatch Logs (Observability)

**VPC Flow Logs → CloudWatch Logs → GuardDuty** (GuardDuty auto-ingests flow logs when enabled).

```bash
# 1. Create IAM role for flow log delivery
aws iam create-role --role-name VPCFlowLogsRole \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"vpc-flow-logs.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

# Attach policy allowing logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents, logs:DescribeLogGroups

# 2. Create flow log at VPC scope
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids <vpc-id> \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /vpc/flowlogs/<vpc-id> \
  --deliver-logs-permission-arn arn:aws:iam::<account>:role/VPCFlowLogsRole

# 3. Enable GuardDuty (auto-consumes flow logs, DNS logs, CloudTrail)
aws guardduty create-detector --enable
```

**Interface endpoints for isolated subnets** — allows CloudWatch Logs agent to deliver without NAT:
```bash
aws ec2 create-vpc-endpoint \
  --vpc-endpoint-type Interface \
  --vpc-id <vpc-id> \
  --service-name com.amazonaws.<region>.logs \
  --subnet-ids subnet-data-1a subnet-data-1b \
  --security-group-ids sg-endpoint  # allow HTTPS 443 from data-tier SG
```

**NAT gateway CloudWatch metrics** (for egress cost monitoring):
- `BytesOutToDestination` — data leaving VPC via NAT
- `BytesOutToSource` — responses returning via NAT
- Set alarm: if `BytesOutToDestination` exceeds baseline by >50%, investigate for data exfiltration
  or runaway process.

---

## VPC ↔ AWS Systems Manager Session Manager (Bastion-Free Access)

SSM Session Manager provides shell access to EC2 instances without opening inbound ports.
Requires interface endpoints when instances are in private/isolated subnets without NAT.

**Required endpoints for SSM (in the subnet with no NAT)**:
```
com.amazonaws.<region>.ssm
com.amazonaws.<region>.ssmmessages
com.amazonaws.<region>.ec2messages
```

```bash
for svc in ssm ssmmessages ec2messages; do
  aws ec2 create-vpc-endpoint \
    --vpc-endpoint-type Interface \
    --vpc-id <vpc-id> \
    --service-name com.amazonaws.<region>.${svc} \
    --subnet-ids subnet-app-1a subnet-app-1b \
    --security-group-ids sg-endpoint
done
```

**Instance IAM role**: attach `AmazonSSMManagedInstanceCore` managed policy.

**Result**: Developers use `aws ssm start-session --target <instance-id>` — no SSH port open,
full IAM authorization, session logged to CloudWatch Logs/S3.
