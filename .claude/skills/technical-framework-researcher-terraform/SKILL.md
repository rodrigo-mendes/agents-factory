---
name: technical-framework-researcher-terraform
description: Researches a Terraform provider/module for a pinned Terraform and provider version into a hallucination-proof IaC knowledge base. Use when researching Terraform/IaC for a skill.
context: fork
agent: framework-researcher
disable-model-invocation: true
---
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

## Quick Navigation

- **[Terraform CLI Commands](./blueprints/terraform-cli-commands.md)** — init/fmt/validate/tfsec/plan/apply/state/destroy with expected outputs
- **[Output Template](./blueprints/terraform-output-template.md)** — Full research document structure
- **[State Patterns](./blueprints/terraform-state-patterns.md)** — Local vs remote (S3+DynamoDB), encryption, isolation
- **[Module Patterns](./blueprints/terraform-module-patterns.md)** — Standard layout, composition, versioning
- **[Integration Example](./blueprints/terraform-integration-example.md)** — Cross-service integration examples
- **[Testing Patterns](./blueprints/terraform-testing-patterns.md)** — fmt/validate/tfsec/terratest examples
- **[Production Readiness](./blueprints/terraform-production-readiness.md)** — DR, cost, monitoring, upgrade strategy
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 4 scenarios: canonical research, edge case, misuse, anti-pattern trap
- **[External Resources](#external-resources)** — Registry, provider docs, and tooling this skill relies on

---

# Role & Mission

Senior Infrastructure Engineer & AI Safety Architect building a hallucination-proof IaC knowledge base for `{{CLOUD_PROVIDER}} {{SERVICE_NAME}}` using Terraform v`{{TERRAFORM_VERSION}}` with `{{PROVIDER_VERSION}}`, enabling autonomous agent operation with infrastructure safety guarantees.

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

## 2. Domain Complexity Assessment

Before extracting patterns, assess the domain's inherent complexity:

| Tier | Description | Expected Always Do | Expected Ask First | Expected Never Do | Indicators |
|------|-------------|--------------------|--------------------|-------------------|------------|
| **Foundational** | Single-resource wrapper, basic config | 3-4 | 2-3 | 2-3 | Single resource type, limited config surface |
| **Standard** | Multi-resource integration, moderate config | 5-6 | 3-4 | 4-5 | Cross-resource dependencies, security considerations |
| **Complex** | Security-critical, stateful, multi-layer | 7-9 | 4-6 | 5-7 | IAM, encryption, state management, compliance |

**Quality rule**: Include every pattern the domain requires. Never pad to reach a count; never omit to fit under a cap. The ranges above are guidelines — let the domain's actual complexity drive the final count.

## 3. Three-Tier Operational Guardrails

### ✅ Always Do: Mandatory Patterns
Identify all non-negotiable infrastructure standards — include as many as the domain demands:
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
Identify all valid patterns with infrastructure tradeoffs — include every decision point the domain presents:
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
Identify all anti-patterns, vulnerabilities, and state-corruption risks — include every anti-pattern discovered:
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
```
Anti-Pattern: [What NOT to do]
Why: [Security/state-consistency/compliance reason]
❌ Wrong:
  # DON'T — [reason]
  [bad HCL]
✅ Correct:
  # DO — [reason]
  [correct HCL with explanations]

Impact: [state corruption | security breach | unmanaged drift | data loss]
Severity: [CRITICAL | HIGH | MEDIUM]
Source: [Registry security advisory link]
```

> Every Never Do entry **must** include a side-by-side ❌ wrong HCL / ✅ correct HCL example.
> For non-HCL anti-patterns (e.g., workflow anti-patterns like manual apply without plan),
> use concrete command-line or CI config examples rather than prose-only prohibitions.

## 4. State Management (Critical for IaC)
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

## 5. Module Architecture (if `USE_MODULES: yes`)
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

## 6. Provider Configuration & Credentials
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

## 7. Ecosystem Interoperability
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

## 8. Executable Verification (Terraform CLI)

Valide o IaC com o ciclo `init → fmt → validate → tfsec/checkov → plan → apply → state → destroy`.
Comandos completos com saídas esperadas em [Terraform CLI Commands](./blueprints/terraform-cli-commands.md).

> All CLI command blocks in the research output MUST carry the annotation
> `# Representative — adapt to your environment` so consumers know they are illustrative, not
> guaranteed-tested against their specific provider version and credentials.
## 9. Configuration Validation & Type Safety
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

## 10. Drift Detection & Reconciliation
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

## 11. Secrets & Sensitive Data Management
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

## 12. Testing & Validation Frameworks
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

## 13. Production Considerations
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

O documento de saída segue um template com **Metadata**, **Executive Summary** e **Architectural Guardrails** (✅/⚠️/🚫) com exemplos de código. Template completo e exemplos em [Output Template](./blueprints/terraform-output-template.md).
## State Management (patterns)

Local (dev) vs. remoto de produção (S3 + DynamoDB, versioning, encryption) e tratamento de state sensível. Exemplos em [State Patterns](./blueprints/terraform-state-patterns.md).
## Module Architecture (se `USE_MODULES: yes`)

Estrutura padrão de módulo, definição (variables/outputs) e composição no root. Exemplos em [Module Patterns](./blueprints/terraform-module-patterns.md).
## Integration Patterns

Exemplo de integração Terraform ↔ parceiros (ex.: VPC): resource types, data sources, issues e fontes. Em [Integration Example](./blueprints/terraform-integration-example.md).
## Quality Control & Testing

Comandos de verificação (fmt/validate/tfsec/tflint/plan/state) e testes com Terratest (Go). Em [Testing Patterns](./blueprints/terraform-testing-patterns.md).
## Production Readiness

Performance, escalabilidade, monitoramento/alertas, checklist de segurança e runbook de disaster recovery. Em [Production Readiness](./blueprints/terraform-production-readiness.md).

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
3. All security anti-patterns include ❌ wrong / ✅ correct HCL side-by-side
4. All links tested (no 404s, actual documents)
5. `{{TERRAFORM_VERSION}}` and `{{PROVIDER_VERSION}}` explicitly confirmed in examples
6. tfsec scan shows no critical findings on example code
7. CLI command blocks carry `# Representative — adapt to your environment`
8. Integration examples use variables, not hardcoded values

---

## External Resources

### Terraform Registry & Core Documentation

- [Terraform Registry — AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)
- [Terraform Registry — Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest)
- [Terraform Registry — Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest)
- [Terraform Registry — OCI Provider](https://registry.terraform.io/providers/oracle/oci/latest)
- [Terraform Language Documentation (HCL)](https://developer.hashicorp.com/terraform/language)
- [Terraform CLI Documentation](https://developer.hashicorp.com/terraform/cli)
- [Terraform Best Practices Guide](https://developer.hashicorp.com/terraform/cloud-adopt/best-practices)

### Security & Static Analysis Tools

- [tfsec — Terraform security scanner](https://github.com/aquasecurity/tfsec)
- [Checkov — Policy-as-code validator](https://www.checkov.io/)
- [tflint — Terraform linter](https://github.com/terraform-linters/tflint)

### Testing

- [Terratest — Go testing framework for IaC](https://terratest.gruntwork.io/)
- [Terraform test — native test framework](https://developer.hashicorp.com/terraform/language/tests)

### Provider Source Repositories

- [hashicorp/terraform-provider-aws (GitHub issues)](https://github.com/hashicorp/terraform-provider-aws/issues)
- [hashicorp/terraform-provider-google (GitHub issues)](https://github.com/hashicorp/terraform-provider-google/issues)
- [hashicorp/terraform-provider-azurerm (GitHub issues)](https://github.com/hashicorp/terraform-provider-azurerm/issues)

### Meta-Skills

- [authoring-agent-skills SKILL.md](../authoring-agent-skills/SKILL.md) — Three-tier pattern conventions
- [researching-technical-frameworks SKILL.md](../researching-technical-frameworks/SKILL.md) — Anti-hallucination methodology
