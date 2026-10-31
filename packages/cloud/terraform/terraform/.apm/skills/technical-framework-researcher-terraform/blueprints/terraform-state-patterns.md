# Terraform State Management Patterns

## State Management Deep Dive

### Local Development State
```hcl
# Use local state only for development/learning
# File: main.tf
terraform {
  required_version = ">= 1.7"
}
```
- Risk: Single point of failure, no sharing, no locking
- When: Solo development, learning, temporary environments

### Production Remote State (S3 + DynamoDB)
```hcl
# Setup DynamoDB for locking (run once)
resource "aws_dynamodb_table" "terraform_locks" {
  name           = "terraform-locks"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name      = "terraform-locks"
    ManagedBy = "terraform"
  }
}

# Backend configuration
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "prod/rds/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

# S3 bucket security hardening
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
```
- Benefit: Team access, state locking prevents conflicts, version history
- Safeguard: State file contains secrets, restrict S3/DynamoDB access to service accounts only

### State File Sensitivity Handling
```hcl
# Data sources containing secrets
data "aws_secretsmanager_secret" "db_password" {
  name = "prod/rds/master-password"
}

# Mark outputs as sensitive
output "database_password" {
  value       = data.aws_secretsmanager_secret.db_password.arn
  sensitive   = true
  description = "ARN of database password secret"
}

# Terraform will mask this value in logs and plan output
```

---
