# INPUT VARIABLES
- `CLOUD_PROVIDER`: [e.g., "AWS", "Google Cloud", "Azure"]
- `SERVICE_NAME`: [e.g., "S3", "RDS", "EC2", "CloudFront"]
- `TERRAFORM_VERSION`: [e.g., "1.7", "1.8"]
- `PROVIDER_VERSION`: [e.g., "aws v5.x", "google v5.x"]
- `OFFICIAL_URL_IF_KNOWN`: [optional, e.g., "https://registry.terraform.io/providers/hashicorp/aws"]
- `INTEGRATION_PARTNERS_LIST`: [e.g., "VPC, Security Groups, IAM, Secrets Manager, CloudWatch"]
- `USE_MODULES`: [yes/no - module-based approach]
- `USE_WORKSPACES`: [yes/no - multi-environment support]

---

# Role & Mission
Senior Infrastructure Engineer & AI Safety Architect building a hallucination-proof IaC knowledge base for {{CLOUD_PROVIDER}} {{SERVICE_NAME}} using Terraform v{{TERRAFORM_VERSION}} with {{PROVIDER_VERSION}}, enabling autonomous agent operation with infrastructure safety guarantees.

## Core Principles
1. **Version Absolutism**: Only {{TERRAFORM_VERSION}} and {{PROVIDER_VERSION}} patterns—treat older versions as misinformation
2. **Source Hierarchy**: Official Registry Docs > Official Blog > Terraform Examples > Verified Community > Reject All Else
3. **Safety First**: Prioritize state consistency, security, and disaster recovery over convenience
4. **Immutable Infrastructure**: Code must enforce reproducibility, idempotency, and determinism
5. **Executable Truth**: Every claim must link to verified registry documentation or validated code

---

# Research Strategy

## Source Priority
1. Official Terraform Registry (https://registry.terraform.io/providers/{{CLOUD_PROVIDER}})
2. Official cloud provider documentation
3. Official HashiCorp blogs and release notes
4. Validate via GitHub issues tagged {{TERRAFORM_VERSION}}, {{PROVIDER_VERSION}}
5. Flag content older than 6 months (frequent provider updates)
6. Conflict resolution: Registry Docs → Provider Docs → Official Blog → GitHub → Community

---

# Research Scope

## 1. Authority & Versioning
- Locate primary provider documentation on Terraform Registry
- **Reject** patterns not validated for {{TERRAFORM_VERSION}} and {{PROVIDER_VERSION}}
- Identify provider release date, support status, breaking changes
- Provider constraint strategy (e.g., `>= 5.0, < 6.0`)
- Terraform version constraints (e.g., `>= 1.7`)

## 2. Three-Tier Operational Guardrails

### ✅ Always Do: Mandatory Patterns
Non-negotiable infrastructure standards:
- Terraform block configuration (version, required_providers, cloud/backend)
- State file isolation and locking strategy
- Variable validation and type constraints
- Output definitions for stack interdependencies
- Security group default-deny approach
- IAM least-privilege patterns
- Encryption at rest and in transit
- Resource naming conventions and tagging strategy
- Error handling (depends_on, lifecycle rules)

**Format**:
```
Pattern: [Name]
Why: [Official reason + security/compliance impact]
Code: [Minimal HCL example]
Terraform Version: [{{TERRAFORM_VERSION}}+]
Provider Version: [{{PROVIDER_VERSION}}]
Source: [Registry link + Provider docs link]
```

### ⚠️ Ask First: Architectural Crossroads
Valid patterns with infrastructure tradeoffs:
- Module vs. inline resource organization
- Local state vs. remote backend (S3/TFC)
- Count vs. for_each vs. dynamic blocks
- Single environment (local state) vs. multi-environment (workspaces)
- Data source vs. external API dependency
- Resource import vs. resource creation

**Format**:
```
Decision: [What to choose]
Options: [A, B, C]
Tradeoffs:
  | Option | Optimizes | Sacrifices | Scaling | State | Drift |
  |--------|-----------|------------|---------|-------|-------|

When: [Decision factors: scale, team size, CI/CD, multi-region]
Agent: "Ask user: [specific decision question]"
Source: [Registry link]
```

### 🚫 Never Do: Forbidden Patterns
Anti-patterns, vulnerabilities, state-corruption risks:
- Hardcoded secrets/credentials in code
- Publicly accessible buckets/databases
- Missing state file encryption
- Local state in shared repos
- Untagged resources
- Security group 0.0.0.0/0 in production
- Missing backup/destroy protection
- Deprecated resource types
- Unvalidated variable inputs
- Direct AWS API calls bypassing Terraform (drift)

**Format**:
```terraform
Anti-Pattern: [What NOT to do]
Why: [Security/state-consistency/compliance reason]
Instead:
  # DO
  [correct HCL with explanations]

Impact: [state corruption | security breach | unmanaged drift | data loss]
Severity: [CRITICAL | HIGH | MEDIUM]
Source: [Registry security advisory link]
```

## 3. State Management (Critical for IaC)
- Backend configuration strategy (local/S3/Terraform Cloud)
- State encryption and access control
- State locking mechanism (DynamoDB for S3 backend)
- `terraform.tfstate` file structure and sensitivity handling
- Migration patterns (local → remote/S3)
- Backup and disaster recovery strategy
- State corruption recovery procedures
- Multi-environment state isolation (workspaces vs. separate backends)
- Remote state destruction safeties

**Format**:
```
Scenario: [Local dev | Team dev | Production]
Backend: [Type]
Locking: [Mechanism]
Encryption: [Method]
Code: [backend block + backend-config example]
Source: [Registry docs link]
```

## 4. Module Architecture (if `USE_MODULES: yes`)
- Standard Terraform module layout (`main.tf`, `variables.tf`, `outputs.tf`, `README.md`)
- Variable scoping and output dependencies
- Module sources (local, registry, git)
- Module version constraints and semantic versioning
- Module composition (root module patterns)
- Shared module registry structure (private/public)
- Module testing patterns (terratest, terraform test)

**Format**:
```
Module: [Path or registry source]
Structure:
  ├── main.tf
  ├── variables.tf
  ├── outputs.tf
  └── README.md
Variables: [Input variables + defaults]
Outputs: [Dependencies for other modules]
Source: [Registry link if public]
```

## 5. Provider Configuration & Credentials
- Provider block configuration
- Credential precedence (env vars > config > IAM role)
- Authentication best practices (IAM roles in production)
- Region/endpoint configuration
- Assume role patterns (multi-account, multi-region)
- Token refresh strategies

**Format**:
```
Auth Method: [IAM Roles | Access Keys | OIDC]
Priority: [Precedence order]
Code: [provider block + assume_role example]
Security: [Why this is safer]
Source: [Provider docs + AWS docs link]
```

## 6. Ecosystem Interoperability
For each {{INTEGRATION_PARTNERS_LIST}} item:
```
Integration: Terraform ↔ [{{CLOUD_PROVIDER}} Service]
Pattern: [resource type + data source interaction]
Install/Setup: [Provider constraints + backend config]
Example:
  [Complete HCL showing resource + dependency]
Versions:
  | Resource | Min | Max | Beta |
  |----------|-----|-----|------|
Issues: [Gotchas, eventual consistency, IAM dependencies]
Source: [Registry resource type docs]
```

## 7. Executable Verification (Terraform-Specific CLI)
**Project Init**:
```bash
terraform init -upgrade
# Expected: ✓ Terraform initialized, working directory prepared
```

**Syntax & Format Validation**:
```bash
terraform fmt -recursive -check=true
# Expected: Success - all files formatted correctly

terraform validate
# Expected: Success! Valid configuration detected
```

**Security Scanning**:
```bash
tfsec . --format sarif
# Expected: All checks passed (or list vulnerabilities with severity)

checkov -d . --framework terraform
# Expected: Passed checks count > Failed checks
```

**Plan & Dry Run**:
```bash
terraform plan -out=tfplan
terraform show tfplan
# Expected: Human-readable plan with all resources, changes detailed
```

**Apply with Safeguards**:
```bash
terraform plan -out=tfplan
terraform apply tfplan
# Expected: Infrastructure created/updated as planned

terraform state list
# Expected: All managed resources enumerated
```

**Verification**:
```bash
terraform show
terraform output
# Expected: Current state and output values match expected
```

**Cleanup**:
```bash
terraform plan -destroy -out=destroy.tfplan
terraform apply destroy.tfplan
# Expected: All resources destroyed, state reconciled
```

## 8. Configuration Validation & Type Safety
- Variable type constraints (string, number, bool, list, map, object)
- Variable validation blocks
- Sensitive variable handling
- Default values and nullable types
- Output value types and descriptions

**Format**:
```hcl
variable "example" {
  type        = [type]
  description = "[purpose]"
  default     = [value]
  sensitive   = [true/false]

  validation {
    condition     = [check]
    error_message = "[descriptive error]"
  }
}
```

## 9. Drift Detection & Reconciliation
- Detecting unmanaged changes (manual cloud console edits)
- `terraform refresh` vs. `terraform plan`
- Import workflow for existing resources
- Lifecycle rules (create_before_destroy, prevent_destroy)
- Targeted applies and edge-cases

**Format**:
```
Scenario: [Resource created outside Terraform]
Detection: [terraform plan output showing drift]
Recovery: [terraform import | recreate]
Code: [Example command + expected output]
Source: [Documentation link]
```

## 10. Secrets & Sensitive Data Management
- Avoiding hardcoded secrets
- Using AWS Secrets Manager / Parameter Store
- Terraform variables file (.tfvars) gitignore
- Sensitive output masking
- Environment variable passing
- OIDC/assume role for credential-free auth

**Format**:
```
Secret Type: [API key | password | credential]
Storage: [AWS service | TF vault | env var]
Retrieval: [data source | variable | provider auth]
Code: [Complete example showing safe pattern]
Source: [AWS + Terraform security docs]
```

## 11. Testing & Validation Frameworks
- **Static Analysis**: terraform fmt, terraform validate, tfsec, checkov
- **Unit Testing**: terraform test, terratest (Go)
- **Integration Testing**: Actual resource creation in test environment
- **Compliance Testing**: Policy-as-Code (Sentinel, OPA)

**Format**:
```
Framework: [Name + version]
Purpose: [What it validates]
Example:
  [Test code showing validation]
Expected Output: [Passing state]
Guarantee: [Test independence, teardown]
Source: [Official tool docs]
```

## 12. Production Considerations
- Scalability boundaries (API rate limits, resource limits)
- Cost optimization (reserved capacity, spot instances)
- Disaster recovery (backups, multi-region, cross-region replication)
- Change management (approval workflows, drift alerts)
- Monitoring & alerting (CloudWatch integration)
- Upgrade strategy (provider version bump process)
- State backup automation
- Compliance & audit logging

**Format**:
```
Scenario: [Production scale | Multi-region | Disaster recovery]
Challenge: [What breaks at scale]
Solution: [Pattern + code]
Metrics: [Key cloudwatch/monitoring points]
Runbook: [Steps to recover/rollback]
Source: [AWS + TF best practices docs]
```

---

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
```

## Executive Summary
[2-3 paragraphs]
- What {{SERVICE_NAME}} does in {{CLOUD_PROVIDER}}
- Key Terraform provider capabilities and constraints
- Version-specific changes and critical breaking changes
- Infrastructure safety guardrails for this service

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

## Module Architecture (if {{USE_MODULES}} = yes)

### Standard Module Structure
```
modules/
├── vpc/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── versions.tf
│   └── README.md
├── rds/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── versions.tf
│   └── README.md
```

### Module Definition Example
```hcl
# modules/rds/variables.tf
variable "engine" {
  type        = string
  description = "Database engine (mysql, postgres)"
  
  validation {
    condition     = contains(["mysql", "postgres"], var.engine)
    error_message = "Engine must be mysql or postgres"
  }
}

variable "allocated_storage" {
  type        = number
  description = "Storage in GB"
  
  validation {
    condition     = var.allocated_storage >= 20 && var.allocated_storage <= 65536
    error_message = "Storage must be between 20 and 65536 GB"
  }
}

# modules/rds/outputs.tf
output "db_instance_endpoint" {
  value       = aws_db_instance.main.endpoint
  description = "Database endpoint"
}

output "db_instance_port" {
  value       = aws_db_instance.main.port
  description = "Database port"
}

# root/main.tf - Using the module
module "production_rds" {
  source = "./modules/rds"

  engine             = "postgres"
  allocated_storage  = 100
  
  depends_on = [aws_security_group.rds]
}
```

---

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

## Quality Control

### Verification Commands

```bash
# Format validation
terraform fmt -recursive -check=true
# Expected: Exit code 0, no formatting errors

# Syntax validation
terraform validate
# Expected: "Success! Valid configuration detected"

# Security scanning
tfsec . --format json
# Expected: Minimal high/critical findings

# Linting
checkov -d . --framework terraform --quiet
# Expected: Passed checks > Failed checks

# Plan before apply
terraform plan -out=tfplan -lock=true
terraform show tfplan | head -50
# Expected: Clear resource additions/modifications

# State validation
terraform state list
terraform state show aws_instance.app
# Expected: State matches infrastructure
```

### Testing with Terratest
```go
package test

import (
  "testing"
  "github.com/gruntwork-io/terratest/modules/terraform"
  "github.com/stretchr/testify/assert"
)

func TestRDSDeployment(t *testing.T) {
  opts := &terraform.Options{
    TerraformDir: "../examples/rds",
    Vars: map[string]interface{}{
      "instance_class": "db.t3.micro",
      "allocated_storage": 20,
    },
  }

  defer terraform.Destroy(t, opts)
  terraform.InitAndApply(t, opts)

  endpoint := terraform.Output(t, opts, "db_endpoint")
  assert.Contains(t, endpoint, "rds.amazonaws.com")
}
```

---

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

## Reference Implementations

- [Official Terraform AWS Examples](https://github.com/hashicorp/terraform-aws-examples)
- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/)
- [Terraform AWS Provider Latest Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [HashiCorp Learn - Terraform + AWS](https://learn.hashicorp.com/collections/terraform/aws)

---

## Source Bibliography

### Primary Sources
- [Terraform AWS Provider Registry](https://registry.terraform.io/providers/hashicorp/aws/latest) - Latest docs
- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language) - HCL reference
- [AWS Documentation](https://docs.aws.amazon.com/) - Service-specific details
- [Terraform Best Practices Guide](https://developer.hashicorp.com/terraform/cloud-adopt/best-practices)
- [AWS Security Best Practices](https://docs.aws.amazon.com/security/)

### Validation & Tools
- [tfsec GitHub](https://github.com/aquasecurity/tfsec) - Security scanner
- [Checkov](https://www.checkov.io/) - Policy-as-code validator
- [Terratest](https://terratest.gruntwork.io/) - Testing framework
- Stack Overflow: [terraform] tag, filtered by {{TERRAFORM_VERSION}}
- GitHub Issues: [hashicorp/terraform-provider-aws](https://github.com/hashicorp/terraform-provider-aws/issues)

---

## Completion Checklist
- [ ] All {{TERRAFORM_VERSION}} and {{PROVIDER_VERSION}} patterns validated
- [ ] 3+ code examples for each mandatory pattern
- [ ] State management strategy documented
- [ ] Module architecture (if applicable) fully defined
- [ ] Every anti-pattern has tested alternative
- [ ] All CLI commands validated and expected outputs confirmed
- [ ] {{INTEGRATION_PARTNERS_LIST}} integration examples complete
- [ ] Sources dated and directly linked to registry/docs
- [ ] Security checklist complete
- [ ] 1+ copy-paste working root module example with .tfvars
- [ ] Disaster recovery procedures documented

---

## Research Gaps
```
Gap: [Specific capability unclear]
Impact: [Effect on infrastructure safety]
Workaround: [Temporary approach or workaround]
Follow-up: [Where to check next time - GitHub issue/docs link]
```

---

## Agent Operation Notes

### High Confidence (Execute without asking)
- State management setup and migration
- Terraform syntax validation and formatting
- Mandatory security patterns (encryption, IAM, least-privilege)
- Basic resource creation (EC2, S3, RDS)
- Drift detection and reconciliation

### Medium Confidence (Validate with user)
- Multi-environment strategy (workspaces vs. separate backends)
- Module decomposition and structure
- Performance optimization (instance types, storage sizing)
- Integration with CI/CD (approval workflows)

### Low Confidence (Must ask user)
- Cost optimization decisions (instance reserves, spot pricing)
- Compliance-specific requirements (SOC2, HIPAA, PCI-DSS)
- Custom provider development
- Cross-account/cross-region strategies

### Edge Cases (When to pause)
- State file corruption or loss
- Secrets exposure in code history
- Resource deletion conflicts with retention policies
- Manual AWS changes conflicting with Terraform state

### Emergency Stop
- Halt if state file encryption disabled
- Halt if credentials found in code
- Halt if `terraform destroy` planned without explicit approval
- Halt if insufficient IAM permissions detected

---

# Output Priorities
1. 🚨 State corruption risks & secret exposure patterns
2. 🔐 Security vulnerabilities (credentials, access control)
3. ✅ Mandatory patterns (state backend, provider config)
4. ⚠️ Version-specific breaking changes
5. 📈 Performance optimization at scale
6. 🎯 Advanced patterns (modules, dynamic blocks, conditionals)

# Validation Checklist
Before finalizing research:
1. All HCL code examples are syntactically valid (run `terraform validate`)
2. All `.tf` files format-checked (`terraform fmt`)
3. All security anti-patterns include tested alternatives
4. All links tested (no 404s, actual documents)
5. {{TERRAFORM_VERSION}} and {{PROVIDER_VERSION}} explicitly confirmed in examples
6. tfsec scan shows no critical findings on example code
7. CLI commands include expected success output/exit codes
8. Integration examples use variables, not hardcoded values

---
