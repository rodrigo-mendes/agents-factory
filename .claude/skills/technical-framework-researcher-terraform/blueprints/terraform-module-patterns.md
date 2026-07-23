# Terraform Module Architecture

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
