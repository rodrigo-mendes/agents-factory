# quarkus-aws-saas

Composition for building a **SaaS on Quarkus 3.40 + AWS** with continuous, bidirectional
spec-driven development (OpenSpec format + CLI, our own agents).

| Kind | Names |
|---|---|
| inline orchestrator | `/building-quarkus-aws-saas` — E1 interview → E2 architecture spec + ADRs → E3 functional spec → E4 design → E5 tasks → E6 implementation cycle I0–I9 with independent review → E7 deploy + observability → E8 reverse sync → E9 archive gate |
| handoff profile | `coordinating-quarkus-aws-handoffs` (roles, limits with 3-level precedence, next-step rules, templates) |
| skill | `integrating-stripe-quarkus-v3-40` (stripe-java 34.0.0 on Quarkus Lambda: raw body + signature header, SQS hand-off, dedupe, idempotency, tenant mapping) |
| skill | `integrating-quarkus-langchain4j-v1-15` (quarkus-langchain4j 1.15.0.CR1, a pre-release, on Quarkus 3.40 Lambda: AI services with OpenAI, Anthropic and Bedrock, time budget, secrets, tests) |

Team (agents from this and other packages): aws-architect, quarkus-lambda-integrator,
quarkus-code-reviewer, stripe-integrator, stripe-advisor, aws-terraform-engineer, aws-lambda-deployer,
aws-observability, aws-lambda-debugger, spec-synchronizer. Only the orchestrator talks to the user.

LangChain4j on Quarkus: no stable quarkus-langchain4j exists for Quarkus 3.40 as of 2026-10-28, so the skill is locked to the 1.15.0.CR1 pre-release (user-approved 2026-10-28).

Optional GitHub Projects mirror: with `tracker.kind: github-projects` (off by default) the orchestrator mirrors
the change, tasks, ADRs, escalations and spec-deltas to a GitHub Project and can take gate answers from issue
comments validated by a GitHub Actions workflow (package openspec-github). Git stays canonical.

Depends on: factory-core, quarkus-aws, aws-lambda, aws-observability, handoff-core, aws-architect,
terraform, stripe-java, openspec-github.
