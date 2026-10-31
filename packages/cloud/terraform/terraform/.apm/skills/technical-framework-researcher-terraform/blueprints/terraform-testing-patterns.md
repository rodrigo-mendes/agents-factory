# Terraform Quality Control & Testing

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
