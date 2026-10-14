# Research Scope §3–4 — Environments & State at Scale

## 3. Environment Management Strategy

### 3.1 Environment Isolation Patterns
Research and compare:
- **Workspaces**: Single codebase, Terraform workspace per environment
- **Directory-per-environment**: Separate directories with shared modules
- **Branch-per-environment**: Git branches mapping to environments (anti-pattern?)
- **Terragrunt**: DRY wrapper with `terragrunt.hcl` hierarchy
- **Terraform Stacks** (if available in v{{TERRAFORM_VERSION}})
- **Terraform Cloud/Enterprise workspaces**: Remote workspace-per-environment

**Format**:
```
Strategy: [Name]
How: [Mechanism for isolation]
State Isolation: [How state is separated]
Configuration DRY-ness: [How much duplication]
Blast Radius: [Scope of a failed apply]
CI/CD Integration: [How pipelines trigger per environment]
Team Scale: [solo | small | medium | large]
Example:
  [Directory structure + key config files]
Pitfalls: [Known problems at scale]
Source: [Link]
```

### 3.2 Variable Management Across Environments
Research patterns for:
- `.tfvars` files per environment
- Environment-specific variable files hierarchy
- Variable precedence and override strategy
- Secrets injection (env vars, vault, CI/CD secrets)
- Common vs. environment-specific variables separation

**Format**:
```
Pattern: [Name]
Files:
  [Which files, naming convention]
Precedence:
  [Order of variable resolution]
Example:
  [terraform apply command with -var-file flags]
Secret Handling: [How secrets differ from regular vars]
Source: [Link]
```

---

## 4. State Management at Scale

### 4.1 Backend Strategy
Research backend options and selection criteria:
- Local backend (solo dev only)
- S3/GCS/Azure Blob + locking (DynamoDB, GCS native, Azure Blob lease)
- Terraform Cloud/Enterprise
- OCI Object Storage
- Backend migration patterns
- Cross-account/cross-project state access

**Format**:
```
Backend: [Type]
Locking: [Mechanism]
Encryption: [At rest + in transit]
Access Control: [IAM/RBAC pattern]
When: [Team size + project scale]
Code:
  [Complete backend configuration]
Source: [Link]
```

### 4.2 State Isolation & Segmentation
Research state partitioning strategies:
- State per environment
- State per component/layer
- State per service/domain
- State per region
- Cross-state references (`terraform_remote_state` vs. data sources)
- State granularity tradeoffs (monolithic vs. micro-states)

**Format**:
```
Strategy: [Name]
Granularity: [Monolithic | Per-Layer | Per-Service | Per-Component]
Blast Radius: [What a bad apply can destroy]
Dependency Management: [How cross-state refs work]
Example:
  [State key structure]
Tradeoffs:
  | Aspect | Coarse-grained | Fine-grained |
  |--------|----------------|--------------|
Source: [Link]
```

### 4.3 State Operations & Recovery
Research operational procedures:
- State backup and disaster recovery
- State corruption recovery
- `terraform state mv`, `rm`, `import` patterns
- `terraform import` blocks (v{{TERRAFORM_VERSION}} declarative import)
- Moved blocks for refactoring (`moved {}`)
- State refresh and drift reconciliation
- Removing resources from state safely

**Format**:
```
Operation: [Name]
When: [Scenario]
Command:
  [Exact CLI with flags]
Safety Check: [Pre-operation validation]
Rollback: [Recovery if operation fails]
Source: [Link]
```

---
