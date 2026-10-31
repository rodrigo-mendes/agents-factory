# Always-Do — Terraform Test and CI

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-14.

## 5. Terraform Test and CI

Use `mock_provider "aws"` with `command = plan` for CI-safe unit tests that require no real AWS
credentials. Run the full CI sequence on every pull request.

```hcl
# iam.tftest.hcl
mock_provider "aws" {}

run "role_has_correct_name" {
  command = plan
  assert {
    condition     = aws_iam_role.app.name == "app-role"
    error_message = "Role name must be app-role"
  }
}
```
Source: https://developer.hashicorp.com/terraform/language/tests

CI sequence (no real AWS credentials needed for plan-only tests):
```bash
terraform init -backend=false
terraform validate -json
terraform plan -detailed-exitcode -input=false -out=tfplan
terraform test -filter=iam.tftest.hcl
```
Source: https://developer.hashicorp.com/terraform/cli/commands/plan
