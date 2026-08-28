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
Research_Depth: "[quick/standard/deep/exhaustive]"
Max_Iterations: "[N]"
Research_Quality_Score: "[N%]"
# Research_Quality_Score = (total_claims - unverified - irresolvable) / total_claims * 100
Gap_Loop_Ran: "[true/false]"
Iterations_Used: "[N of MAX_ITERATIONS]"
Triangulated_Count: "[N]"
Unverified_Count: "[N]"
Irresolvable_Count: "[N]"
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

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns
[Consolidated list with code examples]

### ⚠️ Conditional Patterns
[Decision matrices for architectural crossroads]

### 🚫 Forbidden Patterns
[Anti-patterns with alternatives and severity]

## Reference Implementations
- [Official HashiCorp examples with URLs]
- [Community reference architectures (Cloud Posse, Gruntwork)]
- [Book recommendations with edition/chapter references]

## Source Bibliography
**Primary**: [Official docs, HashiCorp Learn, Registry with URLs and dates]
**Books**: [Title, Author, Edition, relevant chapters]
**Community**: [GitHub repos, blog posts with star counts and dates]
**All Deep-Links**: [Complete organized list]

## Research Iteration Changelog

> Mandatory when `RESEARCH_DEPTH` is `standard`, `deep`, or `exhaustive`. Omit for `quick`.

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | [Section name] | [Claim or pattern] | Added / Resolved / Updated | [URL] (DATE) |
| 2 | [Section name] | [Claim or pattern] | ⚠️ IRRESOLVABLE — [one-line rationale] | — |

> Add one row per gap-loop resolution. Rows are appended in order; do not reorder.
> `IRRESOLVABLE` rows remain in the table permanently as an audit trail.

## Completion Checklist
- [ ] All 9 research scope areas addressed
- [ ] 3+ code examples for mandatory patterns
- [ ] Every anti-pattern has a safe alternative with ❌/✅ side-by-side
- [ ] Directory structure examples are complete and copy-pasteable
- [ ] Module examples include variables.tf, outputs.tf, main.tf
- [ ] CI/CD pipeline examples match {{TOOLING_PREFERENCES}}
- [ ] Testing examples use v{{TERRAFORM_VERSION}} features
- [ ] Sources dated and linked
- [ ] Recommendations calibrated for {{TEAM_SIZE}} and {{PROJECT_SCALE}}

## Research Gaps
```
Gap: [What's missing or uncertain]
Impact: [Effect on recommendations]
Workaround: [Temporary guidance]
Follow-up: [Where to verify]
```

## Agent Operation Notes
- **High Confidence**: [Patterns that can be applied without asking — official best practices]
- **Medium Confidence**: [Patterns that should be validated — community-adopted but not officially blessed]
- **Low Confidence**: [Patterns that must ask user — organizational, compliance, or preference-dependent]
- **Scale Sensitivity**: [Patterns that change based on team size / project scale]
- **Emergency Stop**: [When to halt — state corruption risk, security exposure, compliance violation]
