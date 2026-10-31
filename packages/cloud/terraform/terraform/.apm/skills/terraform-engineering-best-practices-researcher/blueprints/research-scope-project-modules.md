# Research Scope §1–2 — Project Organization & Module Design

## 1. Project Organization & Directory Structure

### 1.1 Repository Strategy
Research and compare repository organization patterns:
- **Monorepo**: All infrastructure in one repository
- **Polyrepo**: One repository per service/stack/environment
- **Hybrid**: Shared modules repo + per-service deployment repos

**Format**:
```
Strategy: [Monorepo | Polyrepo | Hybrid]
When: [Team size, project scale, deployment cadence]
Structure:
  [Directory tree example]
Advantages: [List]
Disadvantages: [List]
Scaling Limit: [When this pattern breaks]
Migration Path: [How to evolve from this to the next pattern]
Source: [Link]
```

### 1.2 Directory Layout Patterns
Research standard directory structures for:
- **Flat layout**: Single directory per environment
- **Layered layout**: Separated by infrastructure layer (networking, compute, data)
- **Domain-driven layout**: Separated by business domain/service
- **Component-based layout**: Separated by logical component with explicit dependencies

**Format for each**:
```
Layout: [Name]
Scale: [solo → enterprise suitability]
Example:
  [Complete directory tree with file names]
Dependency Flow: [How components reference each other]
State Isolation: [How state files are separated]
Source: [Link]
```

### 1.3 File Organization Within a Module/Stack
Research the standard file conventions:
- `main.tf` — primary resources
- `variables.tf` — input variables
- `outputs.tf` — output values
- `providers.tf` — provider configuration
- `versions.tf` / `terraform.tf` — version constraints
- `locals.tf` — local values
- `data.tf` — data sources
- `backend.tf` — backend configuration
- When to split `main.tf` by resource type (e.g., `network.tf`, `compute.tf`, `iam.tf`)

**Format**:
```
Convention: [File naming rule]
Why: [Readability | Tooling compatibility | Team conventions]
When to Split: [Threshold — e.g., >200 lines, >10 resources]
Source: [Link]
```

---

## 2. Module Design & Architecture

### 2.1 Module Types
Research and classify module patterns:
- **Resource modules**: Thin wrappers around 1-3 resources (e.g., `terraform-aws-vpc`)
- **Infrastructure modules**: Compose multiple resource modules (e.g., networking stack)
- **Composition/root modules**: Environment-specific configurations calling infrastructure modules
- **Utility modules**: Data transformations, naming conventions, tagging

**Format**:
```
Type: [Resource | Infrastructure | Composition | Utility]
Purpose: [What it encapsulates]
Scope: [What it should NOT include]
Example:
  [Module structure + main.tf excerpt]
Anti-pattern: [Common mistake with this type]
Source: [Link]
```

### 2.2 Module Interface Design
Research best practices for:
- Variable naming conventions (prefix strategy, required vs. optional)
- Variable validation blocks (type constraints, regex, custom conditions)
- Output design (what to expose, naming, descriptions)
- Sensitive variable handling
- Default values philosophy (safe defaults vs. explicit configuration)
- `nullable` attribute usage (v{{TERRAFORM_VERSION}}+)

**Format**:
```
Practice: [Name]
Why: [Rationale]
Code:
  [HCL example]
Anti-pattern:
  [What NOT to do]
Source: [Link]
```

### 2.3 Module Composition Patterns
Research how modules call other modules:
- Flat composition (root calls all modules at same level)
- Nested composition (modules call sub-modules)
- Facade pattern (wrapper module simplifying complex module)
- Dependency injection (passing outputs between modules)
- Data source vs. remote state for cross-module references

**Format**:
```
Pattern: [Name]
Diagram:
  [ASCII dependency graph]
When: [Scale/complexity threshold]
Tradeoffs:
  | Aspect | Benefit | Cost |
  |--------|---------|------|
Code:
  [Example showing pattern]
Source: [Link]
```

### 2.4 Module Versioning & Distribution
Research strategies for:
- Semantic versioning for modules
- Module sources (local path, Git, Terraform Registry, S3/GCS)
- Version constraints (`~>`, `>=`, exact pinning)
- Private module registry (Terraform Cloud, Artifactory, GitLab)
- Module release workflow (tagging, changelog, breaking change policy)

**Format**:
```
Source Type: [Local | Git | Registry | S3]
Version Constraint: [Pattern + rationale]
When: [Team size, module maturity]
Example:
  module "vpc" {
    source  = "[source]"
    version = "[constraint]"
  }
Source: [Link]
```

---
