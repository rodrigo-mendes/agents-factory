# Never-Do — Limits and Provider (WCU, rate limit, backend, withdrawn version)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 8. Treating 1,500 WCU as the maximum

The hard maximum is 5,000 WCU per web ACL and per rule group. More than 1,500 WCU in a web ACL incurs
extra cost; it is a pricing threshold, not a limit. Do not hard-code WCU numbers for managed rule groups
(Coverage Limit L1). The exact AWS error name on WCU overflow is (unverified).

```hcl
# WRONG
variable "rule_group_capacity" {
  type = number
  validation {
    condition     = var.rule_group_capacity <= 1500   # WRONG — 1,500 is not the maximum
    error_message = "Max 1500 WCU."
  }
}
# Source: https://docs.aws.amazon.com/waf/latest/developerguide/limits.html

# CORRECT
variable "rule_group_capacity" {
  type = number
  validation {
    condition     = var.rule_group_capacity <= 5000
    error_message = "Hard max is 5,000 WCU per rule group."
  }
}
```

## 9. Rate limit minimum of 100

The AWS minimum for a rate-based rule is 10.

```hcl
# WRONG
variable "rate_limit" {
  type = number
  validation {
    condition     = var.rate_limit >= 100   # WRONG
    error_message = "Rate limit must be at least 100."
  }
}
# Source: https://docs.aws.amazon.com/waf/latest/developerguide/limits.html

# CORRECT
variable "rate_limit" {
  type = number
  validation {
    condition     = var.rate_limit >= 10
    error_message = "AWS WAF rate-based rule limit minimum is 10."
  }
}
```

## 10. Deprecated backend, withdrawn version and backend-region claim

`dynamodb_table` is deprecated in the S3 backend; 6.57.0 was withdrawn from GitHub and the Registry. The
claim that the state backend must be in us-east-1 for CloudFront-scope WAF has no official source
(unverified).

```hcl
# WRONG
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.57.0"   # WRONG — withdrawn
    }
  }
  backend "s3" {
    bucket         = "example-tfstate"
    key            = "waf/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "locks"   # WRONG — deprecated
  }
}
# Source: https://developer.hashicorp.com/terraform/language/backend/s3
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md

# CORRECT
#   version      = "~> 6.69"
#   use_lockfile = true
```
