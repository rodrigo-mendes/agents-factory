# Research Scope §7–9 — Code Quality, Advanced Patterns & Governance

## 7. Code Quality & Standards

### 7.1 Naming Conventions
Research naming patterns for:
- Resources (snake_case, descriptive names)
- Variables (prefix conventions, required vs. optional)
- Outputs (consistent naming for cross-module refs)
- Modules (terraform-{provider}-{name} for registry)
- Files (when to split, naming rules)
- Tags/labels (organizational tagging strategy)

**Format**:
```
Element: [Resource | Variable | Output | Module | Tag]
Convention: [Pattern with examples]
Why: [Readability | Tooling | Compliance]
Example:
  [HCL showing convention applied]
Source: [Link]
```

### 7.2 DRY Patterns
Research code reuse mechanisms:
- `locals` for computed values
- `for_each` vs. `count` (when to use which)
- Dynamic blocks (when appropriate, when over-engineered)
- Module reuse across environments
- Terragrunt DRY patterns (if applicable)
- Variable defaults as shared configuration
- `templatefile()` for generated configurations

**Format**:
```
Pattern: [Name]
Mechanism: [HCL construct]
When: [Use case]
When NOT: [Anti-pattern threshold]
Example:
  [Before (repetitive) → After (DRY)]
Source: [Link]
```

### 7.3 Code Review Checklist
Research what to verify in Terraform PRs:
- Plan output review (additions, changes, destructions)
- State impact analysis
- Security implications (public access, IAM changes)
- Cost impact estimation
- Naming and tagging compliance
- Module version pinning
- Backend configuration changes

**Format**:
```
Check: [Name]
Why: [Risk if missed]
How: [What to look for in PR / plan]
Automation: [Can it be automated? How?]
Source: [Link]
```

---

## 8. Advanced Patterns (for {{PROJECT_SCALE}} = platform-team or enterprise)

### 8.1 Multi-Account / Multi-Subscription Strategy
- Provider aliases for cross-account resources
- Assume role / service principal patterns
- Shared services account pattern
- Landing zone provisioning

### 8.2 Terraform at Scale
- Execution time optimization (parallelism, targeted applies)
- API rate limiting mitigation
- Large state file management
- Team workflows with concurrent changes
- Terraform Cloud/Enterprise workspace organization

### 8.3 Refactoring Patterns
- `moved {}` blocks for resource renaming
- `import {}` blocks for adopting existing resources
- State surgery with `terraform state mv`
- Module extraction (monolith → modules)
- Provider migration patterns

### 8.4 Dependency Management
- Inter-stack dependencies (remote state, data sources, SSM/Vault)
- Deployment ordering and orchestration
- Circular dependency detection and resolution
- Cross-region and cross-account dependencies

**Format for each 8.x section**:
```
Pattern: [Name]
Scale: [When needed — team size, resource count]
Implementation:
  [HCL / CLI example]
Risks: [What can go wrong]
Mitigation: [Safety measures]
Source: [Link]
```

---

## 9. Governance & Compliance

### 9.1 Change Control
- Required approvals for production changes
- Plan artifact retention
- Apply audit trail
- Rollback procedures and blast radius assessment
- Emergency change process

### 9.2 Compliance-as-Code
- Tagging enforcement policies
- Encryption-at-rest enforcement
- Network access control validation
- Least-privilege IAM validation
- Cost budget guardrails
- Region restriction enforcement

### 9.3 Documentation Standards
- Module README.md with terraform-docs
- Architecture Decision Records (ADRs) for IaC choices
- Runbooks for common operations
- Onboarding documentation for new team members

**Format**:
```
Practice: [Name]
Why: [Compliance | Operational | Team scaling]
Implementation:
  [Tool / process / config]
Automation: [How to enforce automatically]
Source: [Link]
```

---
