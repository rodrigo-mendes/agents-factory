# Terraform Integration Example

## Integration Patterns: Terraform ↔ {{INTEGRATION_PARTNERS_LIST}}

[For each partner service, include:]

### Integration: Terraform ↔ VPC
- Pattern: VPC as foundational network layer
- Resource: `aws_vpc`, `aws_subnet`, `aws_security_group`
- Data Source: `data.aws_vpc`, `data.aws_security_group`
- Example:
```hcl
module "vpc" {
  source = "./modules/vpc"
  
  cidr            = "10.0.0.0/16"
  enable_dns      = true
  enable_nat      = true
  
  tags = var.tags
}

module "rds" {
  source = "./modules/rds"
  
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  depends_on = [module.vpc]
}
```
- Issues: RDS requires multi-AZ subnets, NAT gateway cost implications
- Source: [AWS VPC Docs](https://docs.aws.amazon.com/vpc/)

---
