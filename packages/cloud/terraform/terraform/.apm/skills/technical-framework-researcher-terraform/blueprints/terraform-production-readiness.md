# Terraform Production Readiness

## Production Readiness

### Performance
- **RDS**: Multi-AZ deployment adds 5-10ms latency, replicate to read replicas for read-heavy
- **S3**: 3,500 PUT/COPY/POST/DELETE per second per partition key, use random prefixes for high throughput
- **DynamoDB**: On-demand vs. provisioned capacity trade-off

### Scalability
- **EC2**: Auto-scaling group max 50 instances per IAM role by default (request increase)
- **RDS**: Max 40 vCPU, 384GB RAM for largest instance types
- **State file**: Terraform scales to ~10,000 resources per state file

### Monitoring & Alerting
```hcl
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "prod-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
}
```

### Security Checklist
- [ ] All secrets stored in Secrets Manager/Parameter Store
- [ ] State file encryption enabled (S3 + KMS)
- [ ] State file access restricted to service accounts
- [ ] All resources tagged for compliance
- [ ] Security groups follow least-privilege (no 0.0.0.0/0)
- [ ] VPC endpoints for AWS services (no internet egress)
- [ ] CloudTrail logging enabled for audit
- [ ] Secrets Manager rotation enabled
- [ ] RDS encryption enabled (at-rest + in-transit)

### Disaster Recovery Runbook
```bash
# 1. State corruption recovery
aws s3api get-object \
  --bucket my-tf-state \
  --key prod/terraform.tfstate.backup \
  terraform.tfstate.backup

terraform state pull > terraform.tfstate.corrupted
cp terraform.tfstate.backup terraform.tfstate
terraform state push terraform.tfstate

# 2. Compare current state vs. real infrastructure
terraform refresh  # Update state from AWS

# 3. Selective recovery of resource
terraform import aws_instance.web i-0123abcd4567ef89
```

---
