# Terraform Research — Output Template

# Output Format

Save as `research_{{CLOUD_PROVIDER}}_{{SERVICE_NAME}}_{{PROVIDER_VERSION}}.md`:

## Metadata
```yaml
Full_Name: "Terraform {{CLOUD_PROVIDER}} Provider - {{SERVICE_NAME}}"
Cloud_Provider: "{{CLOUD_PROVIDER}}"
Target_Service: "{{SERVICE_NAME}}"
Terraform_Version: "{{TERRAFORM_VERSION}}"
Provider_Version: "{{PROVIDER_VERSION}}"
Provider_Registry_URL: "https://registry.terraform.io/providers/hashicorp/[provider]"
Release_Date: "[Date]"
Support_Status: "[Active | Deprecated | EOL]"
Last_Updated: "[Date]"
Research_Date: "[Today's date]"
Domain_Complexity: "[Foundational/Standard/Complex]"
```

## Executive Summary
[2-3 paragraphs]
- What {{SERVICE_NAME}} does in {{CLOUD_PROVIDER}}
- Key Terraform provider capabilities and constraints
- Version-specific changes and critical breaking changes
- Infrastructure safety guardrails for this service
- Domain complexity tier and why

## Architectural Guardrails

### ✅ Mandatory Patterns

#### Pattern: Terraform Configuration Block
- Why: Ensures reproducibility and defines version contracts
- Code: 
```hcl
terraform {
  required_version = ">= {{TERRAFORM_VERSION}}"
  required_providers {
    {{CLOUD_PROVIDER}} = {
      source  = "hashicorp/{{CLOUD_PROVIDER}}"
      version = "{{PROVIDER_VERSION}}"
    }
  }
  backend "s3" {
    bucket         = "my-tf-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```
- Source: [Registry Terraform Block Docs](https://registry.terraform.io/providers/hashicorp/[provider]/latest/docs)

#### Pattern: Provider Configuration with Security
- Why: Credentials managed safely, no hardcoding
- Code:
```hcl
provider "{{CLOUD_PROVIDER}}" {
  region = var.aws_region

  assume_role {
    role_arn = "arn:aws:iam::ACCOUNT:role/TerraformRole"
  }

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = var.owner
    }
  }
}
```
- Source: [Provider Configuration Docs]

#### Pattern: Variable Validation & Type Safety
- Why: Prevents invalid configurations at plan time, before apply
- Code:
```hcl
variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  default     = "t3.medium"

  validation {
    condition     = contains(["t3.micro", "t3.small", "t3.medium", "m5.large"], var.instance_type)
    error_message = "Instance type must be approved: t3.micro, t3.small, t3.medium, m5.large"
  }
}
```
- Source: [Input Variable Validation](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)

---

### ⚠️ Conditional Patterns

#### Decision: Local vs. Remote Backend

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Local** | Simplicity, offline use | Sharing, locking, history, safety | Solo dev, learning, no shared infra |
| **S3 + DynamoDB** | Team sharing, locking, audit | Complexity, AWS dependency | Team dev, production, compliance |
| **Terraform Cloud** | SaaS ease, VCS hooks, state versioning | Cost, vendor lock-in, external dependency | Enterprise, distributed teams |

- Agent: "Ask user: How many team members? Is this production infrastructure?"
- Source: [Backend Configuration Docs](https://developer.hashicorp.com/terraform/language/settings/backends/configuration)

#### Decision: Count vs. For_Each vs. Dynamic Blocks

| Option | Best For | Pitfall |
|--------|----------|---------|
| **count** | Conditional resources (0 or 1) | Reordering breaks state |
| **for_each** | Multiple resources, stable keys | Complex maps, nested loops |
| **dynamic blocks** | Variable nested blocks | Hard to read, debug |

- When: Count for optional resources (conditional flags), for_each for multiple instances (list/map iteration), dynamic for nested structures
- Source: [Meta-Arguments docs](https://developer.hashicorp.com/terraform/language/meta-arguments/count)

---

### 🚫 Forbidden Patterns

#### Anti-Pattern: Hardcoded Credentials
```hcl
# DON'T
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  region     = "us-east-1"
}
```
- Why: Credentials exposed in code, version control history, team access logs
- Instead:
```hcl
# DO - Use environment variables or IAM role
provider "aws" {
  region = var.aws_region
  # Credentials from AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY env vars
  # or from EC2/ECS/Lambda IAM role automatically
}
```
- Impact: **CRITICAL** - Full AWS account compromise
- Source: [AWS Security Best Practices](https://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html)

#### Anti-Pattern: Publicly Accessible S3 Bucket
```hcl
# DON'T
resource "aws_s3_bucket" "website" {
  bucket = "my-public-website"
}

resource "aws_s3_bucket_public_access_block" "website" {
  bucket = aws_s3_bucket.website.id

  block_public_acls       = false  # DON'T
  block_public_policy     = false  # DON'T
  ignore_public_acls      = false  # DON'T
  restrict_public_buckets = false  # DON'T
}
```
- Why: Unintended data exposure, data breach risk
- Instead:
```hcl
# DO - Explicitly control access
resource "aws_s3_bucket_public_access_block" "website" {
  bucket = aws_s3_bucket.website.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "website" {
  bucket = aws_s3_bucket.website.id
  policy = data.aws_iam_policy_document.website_policy.json
}
```
- Impact: **CRITICAL** - Unintended public data exposure
- Source: [S3 Block Public Access](https://docs.aws.amazon.com/s3/latest/userguide/access-control-block-public-access.html)

#### Anti-Pattern: Missing State File Encryption
```hcl
# DON'T
backend "s3" {
  bucket = "my-tf-state"
  key    = "terraform.tfstate"
  region = "us-east-1"
  # No encrypt = true
}
```
- Why: State file contains all resource details including secrets, unencrypted at rest
- Instead:
```hcl
# DO
backend "s3" {
  bucket         = "my-tf-state"
  key            = "prod/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true  # Enable server-side encryption
  dynamodb_table = "terraform-locks"  # Enable state locking
}
```
- Impact: **CRITICAL** - Complete infrastructure and secrets exposure
- Source: [Terraform State Security](https://developer.hashicorp.com/terraform/language/state/sensitive-data)

#### Anti-Pattern: Security Group 0.0.0.0/0
```hcl
# DON'T
resource "aws_security_group_rule" "ssh" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]  # DON'T - World access
  security_group_id = aws_security_group.app.id
}
```
- Why: Exposes SSH to entire internet, path for unauthorized access
- Instead:
```hcl
# DO - Restrict to known IPs/bastion
resource "aws_security_group_rule" "ssh" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = [var.bastion_cidr]  # e.g., "203.0.113.0/32"
  security_group_id = aws_security_group.app.id
  description       = "SSH from bastion only"
}
```
- Impact: **CRITICAL** - Unauthorized access, brute force attacks
- Source: [AWS VPC Security Groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)

#### Anti-Pattern: No Tags on Resources
```hcl
# DON'T
resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
  # No tags
}
```
- Why: Unable to track costs, ownership, compliance, automation
- Instead:
```hcl
# DO - Enforce tags with default_tags
provider "aws" {
  default_tags {
    tags = {
      Environment = var.environment
      Owner       = var.owner
      CostCenter  = var.cost_center
      ManagedBy   = "terraform"
    }
  }
}

resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"

  tags = merge(
    var.tags,
    { Name = "app-server-${var.environment}" }
  )
}
```
- Impact: **HIGH** - Cost blindness, compliance gaps, resource orphaning
- Source: [Resource Tagging Strategy](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)

---
