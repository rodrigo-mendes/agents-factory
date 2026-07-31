# Guide: Researching Technologies

How to use the research prompts to build validated knowledge bases.

---

## When to Use

- Need to learn a new technology for the project
- Want to create a skill based on verified information
- Need to document patterns for a specific version

## Step by Step

### 1. Choose the right researcher

| Domain | Prompt |
|---------|--------|
| Framework/lib (FastAPI, Redis, Spring) | `researching-technical-frameworks` |
| Cloud service + Terraform | `technical-framework-researcher-terraform` |
| Terraform practices (org, CI/CD, test) | `terraform-engineering-best-practices-researcher` |
| Architecture methodology (C4, DDD) | `architecture-methodology-researcher` |
| Cloud framework (WAF, CAF) | `cloud-architecture-researcher` |
| Business domain (Finance, Legal) | `business-domain-researcher` |
| Requirements framework (Scrum, SAFe) | `requirements-methodology-researcher` |

### 2. Run the prompt

```
/researching-technical-frameworks
```

### 3. Provide the inputs

The prompt will ask for:
- **Technology**: Exact name (e.g., "FastAPI")
- **Version**: Specific version (e.g., "0.100")
- **Context**: Integration partners, use case

> ⚠️ **Version Absolutism**: Always provide the specific version. "FastAPI" is not sufficient — it must be "FastAPI v0.100".

### 4. Review the output

The research document will have:
- Validated official patterns
- Sample code (from official docs, not fabricated)
- Breaking changes vs previous versions
- Tested integrations

### 5. Compile into an operational artifact

After research, transform into skill or instruction:

| Research type | Compiler |
|-----------------|----------|
| Generic technology | `/skill-creator` |
| Cloud service + Terraform | `/skill-creator` |
| Terraform practices (org, CI/CD, tests) | `/terraform-instructions-compiler` |
| Architecture methodology | `/architecture-approaches-skill-generator` |
| Requirements methodology | `/methodologies-skill-generator` |

---

## Tips

- **Don't skip compilation**: The research document is not the final artifact — it needs to be structured in three-tier to be useful to agents
- **Validate after compiling**: Use `/skill-best-practices-validator` on the result
- **One version at a time**: If you need multiple versions, do separate research sessions

## Common Pitfalls

| Pitfall | Solution |
|-----------|---------|
| Researching without a specific version | Always provide the exact version |
| Using research output as a skill directly | Pass through the compiler first |
| Mixing information from different versions | Separate into distinct research sessions |
| Not validating the result | Run validator after compiling |

## Full Flow

See: [Knowledge Base Flow](../fluxos/fluxo-base-conhecimento.md)
