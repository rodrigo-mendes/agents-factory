# Terraform Engineering — Output Template

# Output Format

Save as `research_Terraform_Engineering_Best_Practices_v{{TERRAFORM_VERSION}}.md`:

## Metadata
```yaml
Title: "Terraform Engineering Best Practices"
Terraform_Version: "{{TERRAFORM_VERSION}}"
Cloud_Provider: "{{CLOUD_PROVIDER}}"
Team_Size: "{{TEAM_SIZE}}"
Project_Scale: "{{PROJECT_SCALE}}"
Environment_Count: "{{ENVIRONMENT_COUNT}}"
Tooling: "{{TOOLING_PREFERENCES}}"
Research_Date: "[Today's date]"
Sources_Count: "[Number of verified sources]"
```

## Executive Summary
[2-3 paragraphs]
- Terraform v{{TERRAFORM_VERSION}} engineering landscape for {{PROJECT_SCALE}} projects
- Key recommendations for {{TEAM_SIZE}} teams on {{CLOUD_PROVIDER}}
- Critical patterns and anti-patterns for the given scale

## Project Organization
[Section 1 findings — repository strategy, directory layout, file conventions]

## Module Architecture
[Section 2 findings — module types, interface design, composition, versioning]

## Environment Strategy
[Section 3 findings — isolation patterns, variable management]

## State Management
[Section 4 findings — backend strategy, isolation, operations]

## CI/CD Pipeline
[Section 5 findings — pipeline architecture, security, tooling]

## Testing Strategy
[Section 6 findings — testing pyramid, native tests, policy-as-code]

## Code Quality & Standards
[Section 7 findings — naming, DRY patterns, code review]

## Advanced Patterns
[Section 8 findings — multi-account, scale, refactoring, dependencies]
*(Include only if {{PROJECT_SCALE}} = platform-team or enterprise)*

## Governance & Compliance
[Section 9 findings — change control, compliance-as-code, documentation]
*(Include only if {{COMPLIANCE_REQUIREMENTS}} specified)*

## Architectural Guardrails
### ✅ Mandatory Patterns
[Consolidated list with code examples]

### ⚠️ Conditional Patterns
[Decision matrices for architectural crossroads]

### 🚫 Forbidden Patterns
[Anti-patterns with alternatives and severity]
