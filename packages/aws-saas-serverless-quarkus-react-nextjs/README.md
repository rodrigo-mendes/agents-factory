# aws-saas-serverless-quarkus-react-nextjs

Composition for building a **SaaS on Quarkus 3.40 + AWS Lambda with a Next.js/React static front end** (S3 + CloudFront),
with continuous spec-driven development (OpenSpec format + CLI, our own agents) and deploy by GitHub Actions.
Renamed from `quarkus-aws-saas`.

| Kind | Names |
|---|---|
| inline orchestrator (project manager) | `/building-aws-saas-serverless-quarkus-react-nextjs`: E1 interview, E2a solution / E2b design / E2c infrastructure, E3 functional spec, E3b wireframes, E4 technical designs, E5 tasks, E6 implementation with independent review, E7 PR + CI + merge + CD + verification, E8 reverse sync, E9 archive gate |
| handoff profile | `coordinating-quarkus-aws-handoffs` (20 roles, limits, next-step rules, templates) |
| skill | `integrating-stripe-quarkus-v3-40` |

The orchestrator only coordinates: it talks to the user, writes the functional spec and the task list, records approvals and
runs the handoff scripts. It never designs, codes or deploys. Models: planning in the session model; `solution-architect` and
`aws-infrastructure-architect` with `opus`; every other agent with `sonnet` (explicit in each launch).

## Team (who creates, who reviews)

| Deliverable | Author | Independent reviewer |
|---|---|---|
| Functional spec, task list | orchestrator | `spec-synchronizer` |
| Solution architecture, designs (E2a, E4) | `solution-architect` | `solution-architecture-reviewer` |
| Design system, wireframes (E2b, E3b) | `ui-ux-designer` | `ui-design-reviewer` |
| Infrastructure design (E2c, E4) | `aws-infrastructure-architect` | `aws-architect-reviewer` |
| Back end | `quarkus-lambda-integrator` | `quarkus-code-reviewer` |
| AI in Lambdas | `quarkus-lambda-integrator` | `langchain4j-reviewer` then `quarkus-code-reviewer` |
| Stripe | `stripe-integrator` | `stripe-advisor` then `quarkus-code-reviewer` |
| Front end | `nextjs-frontend-integrator` | `nextjs-code-reviewer` then `ui-design-reviewer` |
| Terraform (infra, observability) | `aws-terraform-engineer`, `aws-observability` | `terraform-code-reviewer` |
| Workflows | `cicd-pipeline-engineer` | `cicd-pipeline-reviewer` |
| Deploy and publish | GitHub Actions `cd-*` after the user's merge | `aws-lambda-debugger`, `static-site-verifier` |

Agents never push, open or merge PRs, trigger workflows or run `terraform apply`; they read the pipeline results (`gh pr checks`, `gh run view`).

## Depends on

factory-core, quarkus-aws, quarkus-langchain4j, aws-lambda, aws-observability, handoff-core, aws-architect, terraform, stripe-java,
openspec-github, solution-architecture, ui-design, nextjs-frontend, vercel-frontend, github-actions-cicd.

Optional GitHub Projects mirror: with `tracker.kind: github-projects` (off by default) the orchestrator mirrors the change to a
GitHub Project (package openspec-github). Git stays canonical. LangChain4j on Quarkus is pinned to the 1.15.0.CR1 pre-release
(Ask First; user-approved 2026-10-28). Details of the process: the orchestrator `SKILL.md` and its `blueprints/`.
