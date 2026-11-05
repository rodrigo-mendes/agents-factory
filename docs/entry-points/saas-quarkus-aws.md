# SaaS on Quarkus, AWS Lambda and Next.js

`/building-aws-saas-serverless-quarkus-react-nextjs` is a project manager. You use it to build or
change a SaaS end to end: Quarkus 3.40 Lambdas, a Next.js static site on S3 and CloudFront, AI in
Lambdas, and GitHub Actions deployment.

It is an **inline orchestrator**: it runs in your session, asks you questions, and starts a team of
workers. It never designs or writes code itself. Every technical decision comes from a worker and
every step is recorded in a handoff file.

## When to use it

- You are starting or evolving a SaaS change and want the whole path, from interview to merged code.
- You want each step reviewed by a different agent before it moves on.

Use something else when:

- The change is not on Quarkus 3.40, AWS Lambda and Next.js. The orchestrator refuses Quarkus 4,
  Camel, SAM or CDK, ECS and server-side rendering.
- You only need one piece. Call the worker directly or use a more specific command.

## How to start

```
/building-aws-saas-serverless-quarkus-react-nextjs
```

To start from an existing prototype, add the POC arguments:

```
/building-aws-saas-serverless-quarkus-react-nextjs poc.back=poc/api poc.front=poc/web
```

The POC is turned into a spec draft first, through [`/bootstrapping-spec-from-poc`](specs-and-github.md).

## The steps

The work runs in phases E1 to E9. Each phase has an author, an independent verifier and, where it
matters, a gate where you decide.

| Phase | What happens | Your gate |
|---|---|---|
| E1 Interview | The orchestrator interviews you in 12 blocks, at most 10 questions per round. | You confirm each block summary. |
| E2 Architecture | Solution architecture, design system and infrastructure design, each with decision records (ADRs). | You approve E2 once; the ADRs become `accepted`. |
| E3 Functional spec | Requirements with scenarios, as OpenSpec change deltas. | You approve E3. |
| E3b Wireframes | Wireframes and navigation. Skipped when the change has no UI. | You approve E3b. |
| E4 Designs | One technical design per flow, plus an infrastructure design. | Shown to you, not blocking. |
| E5 Tasks | A task list and one work-order per task. | You approve the task list. |
| E6 Implementation | The owner agent builds each task, then a review chain checks it. | Only escalations; you apply the OIDC and state bootstrap once. |
| E7 Pull request and pipeline | You push and open the pull request. CI runs, you merge, CD deploys to dev, and the result is verified. | You merge, and you release to prod. |
| E8 Reverse sync | Drift between code and spec becomes a spec-delta. | You decide each delta. |
| E9 Archive gate | The orchestrator checks that everything is green and drift is zero. | You approve the archive. |

No work-order exists until the architecture, design, infrastructure and functional-spec verifies
pass and your approvals are recorded. The orchestrator never pushes, opens pull requests, merges or
applies Terraform.

### Who writes and who reviews

Each deliverable has a different reviewer, so no agent reviews its own work.

| Deliverable | Author | Reviewer |
|---|---|---|
| Interview, functional spec, task list | the orchestrator | `spec-synchronizer` |
| Solution architecture and designs | `solution-architect` | `solution-architecture-reviewer` |
| Design system and wireframes | `ui-ux-designer` | `ui-design-reviewer` |
| Infrastructure design | `aws-infrastructure-architect` | `aws-architect-reviewer` |
| Back-end code | `quarkus-lambda-integrator` | `quarkus-code-reviewer` |
| Front-end code | `nextjs-frontend-integrator` | `nextjs-code-reviewer`, then `ui-design-reviewer` |
| Terraform | `aws-terraform-engineer`, `aws-observability` | `terraform-code-reviewer` |
| CI/CD workflows | `cicd-pipeline-engineer` | `cicd-pipeline-reviewer` |

Stripe and AI code have extra reviewers; the package README lists them. See also the
[SaaS flow](../flows/saas-spec-driven.md).

## Models

- Planning runs in your session's model.
- Architecture workers (`solution-architect`, `aws-infrastructure-architect`) run on the opus model.
- Every other worker runs on the sonnet model.
- Each deliverable has a different reviewer, so no agent reviews its own work.

## Where the records go

Everything is written under `openspec/changes/<id>/`:

- the specs and designs of the change,
- `handoff/` with one record per work-order, result and review.

Read the records to see what happened. They are the audit trail.

## Limits

- It does not merge pull requests or run production deployments. Those need your approval.
- It does not invent requirements. Anything missing becomes a question.

## Related

- Package: [`aws-saas-serverless-quarkus-react-nextjs`](../../packages/saas/aws-saas-serverless-quarkus-react-nextjs/README.md).
- Layers it uses: [`handoff-core`](../../packages/delivery/protocol/handoff-core/README.md),
  [`quarkus-aws`](../../packages/java/quarkus/quarkus-aws/README.md),
  [`solution-architecture`](../../packages/architecture/solution-architecture/README.md),
  [`ui-design`](../../packages/frontend/react/ui-design/README.md),
  [`nextjs-frontend`](../../packages/frontend/react/nextjs-frontend/README.md),
  [`aws-architect`](../../packages/cloud/provider/aws/aws-architect/README.md),
  [`aws-observability`](../../packages/cloud/provider/aws/aws-observability/README.md),
  [`github-actions-cicd`](../../packages/delivery/github/github-actions-cicd/README.md).
- Spec tools: [specs-and-github](specs-and-github.md).
