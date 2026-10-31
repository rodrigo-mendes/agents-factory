# Research Scope §5–6 — CI/CD & Testing

## 5. CI/CD Pipelines for Terraform

### 5.1 Pipeline Architecture
Research CI/CD patterns for:
- Plan on PR / Apply on merge
- Manual approval gates
- Environment promotion (dev → staging → prod)
- Drift detection scheduled runs
- Automated formatting and validation checks

**Format**:
```
Stage: [Name]
Trigger: [PR | merge | schedule | manual]
Commands:
  [Exact terraform commands]
Artifacts: [Plan files, state snapshots]
Approval: [Automated | Manual | Policy-based]
Example:
  [Pipeline YAML/config snippet for {{TOOLING_PREFERENCES}}]
Source: [Link]
```

### 5.2 Pipeline Security
Research security patterns:
- Credential management in CI/CD (OIDC, short-lived tokens)
- Plan file security (contains sensitive data)
- State file access control in CI/CD
- PR-based plan output (sanitized)
- Branch protection rules for Terraform repos
- Audit logging for applies

**Format**:
```
Concern: [Security risk]
Mitigation: [Pattern]
Implementation:
  [Code/config example]
Source: [Link]
```

### 5.3 Tooling Comparison
Research and compare CI/CD tooling for Terraform:
- GitHub Actions (native workflows)
- GitLab CI
- Terraform Cloud / Enterprise (VCS-driven)
- Atlantis (self-hosted PR automation)
- Spacelift (managed Terraform CI/CD)
- env0, Scalr, digger

**Format**:
```
Tool: [Name]
Model: [SaaS | Self-hosted | Hybrid]
Key Features: [List]
Limitations: [List]
Best For: [Team size, project scale]
Cost: [Free tier | Pricing model]
Source: [Link]
```

---

## 6. Testing Strategy

### 6.1 Testing Pyramid for Terraform
Research the layered testing approach:
- **Static Analysis** (tier 1): `terraform fmt`, `terraform validate`, tflint
- **Policy-as-Code** (tier 2): OPA/Conftest, Sentinel, Checkov, tfsec/Trivy
- **Unit Testing** (tier 3): `terraform test` (native, v{{TERRAFORM_VERSION}}), mock providers
- **Integration Testing** (tier 4): terratest, real infrastructure deployment + validation
- **End-to-end Testing** (tier 5): Full stack deployment + functional verification

**Format per tier**:
```
Tier: [Number + Name]
Tools: [List with versions]
What It Validates: [Scope]
Speed: [Seconds | Minutes | Hours]
Cost: [Free | Cloud resources consumed]
Example:
  [Test code/config]
CI/CD Stage: [Where in pipeline]
Source: [Link]
```

### 6.2 Native Terraform Test Framework
Research `terraform test` (v{{TERRAFORM_VERSION}}):
- Test file structure (`.tftest.hcl`)
- `run` blocks and assertions
- Mock providers and overrides
- Variables in tests
- Plan-only vs. apply tests
- Test organization patterns

**Format**:
```
Feature: [Name]
Syntax:
  [HCL example]
When: [Use case]
Limitations: [What it can't test]
Source: [Link]
```

### 6.3 Policy-as-Code
Research governance enforcement:
- OPA/Rego with Conftest (plan JSON validation)
- HashiCorp Sentinel (Terraform Cloud/Enterprise)
- Checkov / Bridgecrew
- tfsec / Trivy IaC scanning
- Custom validation rules

**Format**:
```
Tool: [Name]
Policy Language: [Rego | Sentinel | YAML | Python]
Enforcement Point: [Pre-plan | Post-plan | Pre-apply]
Example Policy:
  [Rule requiring encryption, tagging, etc.]
Integration:
  [CI/CD config snippet]
Source: [Link]
```

---
