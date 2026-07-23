# Terraform CLI — Executable Verification

## 8. Executable Verification (Terraform-Specific CLI)
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
