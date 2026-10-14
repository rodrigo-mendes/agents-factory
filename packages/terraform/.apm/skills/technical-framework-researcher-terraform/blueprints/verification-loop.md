# Verification Loop — technical-framework-researcher-terraform

## Gap-Filling Loop (repeat up to `MAX_ITERATIONS` times, skip when `depth=quick`)

1. Run the checklist below.
2. List every item that fails or is incomplete — these are **gaps**.
3. If gaps exist and iterations remain: research the missing items, fill them in the output, decrement iteration counter, repeat from step 1.
4. If no gaps remain or `MAX_ITERATIONS` is reached: proceed to output.

## Checklist

Before finalizing research, confirm:
1. All HCL code examples are syntactically valid (run `terraform validate`)
2. All `.tf` files format-checked (`terraform fmt`)
3. All security anti-patterns include ❌ wrong / ✅ correct HCL side-by-side
4. All links tested (no 404s, actual documents)
5. `{{TERRAFORM_VERSION}}` and `{{PROVIDER_VERSION}}` explicitly confirmed in examples
6. tfsec scan shows no critical findings on example code
7. CLI command blocks carry `# Representative — adapt to your environment`
8. Integration examples use variables, not hardcoded values
9. Research Iteration Changelog present with at least one iteration row (skip when depth=quick)

```bash
# Confirm mandatory output sections are present
grep -E "^## (Executive Summary|Architectural Guardrails)" \
  research_Terraform_*.md
# Expected: both top-level section headers appear

# Confirm Architectural Guardrails subsections are present
grep -E "^### (✅ Mandatory Patterns|⚠️ Conditional Patterns|🚫 Forbidden Patterns)" \
  research_Terraform_*.md
# Expected: all 3 subsection headers appear

# Confirm every Forbidden Pattern has a correct alternative
grep -c "✅ Correct\|# ✅" research_Terraform_*.md
# Expected: count equals or exceeds the number of Forbidden Pattern entries

# Confirm version string appears throughout (not only in header)
grep -c "{{TERRAFORM_VERSION}}\|v1\.[0-9]" research_Terraform_*.md
# Expected: multiple matches distributed across sections
```
