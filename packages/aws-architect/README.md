# aws-architect

Advisory agent package for AWS architecture design and review.

## What It Does

The `aws-architect` agent reviews, designs, and evaluates AWS architectures by reasoning over
the 40 knowledge skills in the `aws-skills` package. It follows the WAF six pillars (Nov 2024
edition) and returns sourced, version-dated guidance. It produces design recommendations, ADRs,
and implementation roadmaps — no IaC code generation.

## Package Contents

```
packages/aws-architect/
├── apm.yml                             <- Package manifest (deps: aws-skills + factory-core)
├── README.md                           <- This file
└── .apm/
    ├── agents/
    │   └── aws-architect.agent.md      <- Advisory agent (tools: Read, Grep, Glob; model: sonnet)
    ├── instructions/
    │   ├── aws-security-baseline.instructions.md      <- Security guardrails (R01–R06)
    │   └── aws-iac-reliability-cost.instructions.md   <- Reliability/networking/cost guardrails (R07–R12)
    └── skills/
        └── aws-architecture-advisor/
            ├── SKILL.md                <- Action-command skill (routes to aws-architect agent)
            └── blueprints/
                └── evaluation-scenarios.md  <- 4 test scenarios
```

## How to Use

```
/aws-architecture-advisor review my VPC design for WAF Reliability and Security compliance
/aws-architecture-advisor design a serverless event-driven order processing system on AWS
/aws-architecture-advisor assess our multi-account landing zone against WAF Security Pillar
```

## Dependencies

- `../aws-skills` — 40 knowledge skills (WAF pillars, security, networking, serverless, data, observability)
- `../factory-core` — shared agent/skill/rule frontmatter standards

## Shared Knowledge Base

- `workspace/aws/_family_facts_v2026.md` — 20 facts shared across ≥2 skills (1 unverified)
- `workspace/aws/_family_rules_v2026.md` — 13 numbered, testable policy decisions

## Agent Constraints

- **Advisory only** — no IaC code generation, no file editing
- **Non-interactive** — returns questions when context is missing; never assumes
- **Source-bound** — cites only facts from loaded skills; preserves `(unverified)` tags
- **Flat** — no sub-agent spawning, no plan mode
