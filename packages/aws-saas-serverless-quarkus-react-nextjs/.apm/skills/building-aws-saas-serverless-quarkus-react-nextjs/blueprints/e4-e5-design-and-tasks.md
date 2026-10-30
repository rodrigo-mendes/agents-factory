# E4 designs and E5 tasks

Back to [SKILL.md](../SKILL.md). Precondition: E2 (a, b, c), E3 and, for UI changes, E3b accepted (verifies `pass` + user approvals recorded).
The manager writes no design: `solution-architect` and `aws-infrastructure-architect` (both opus) author, different reviewers verify. Layout of the files: rule `openspec-project-layout` (package `openspec-core`).

## E4 - Designs of the change

```
openspec/changes/<id>/
├── design.md          index of the designs + overall traceability (the official OpenSpec file, used as an index)
├── design/            one file per flow (factory convention)
│   ├── list-items.md
│   └── classify-item.md
└── infra-design.md    infrastructure of the change
```

Authors and reviewers: `solution-architect` writes `design.md` and `design/<flow>.md`; `solution-architecture-reviewer` reviews **one design per work-order** (so a rejected design does not block the others) and the index; `aws-infrastructure-architect` writes `infra-design.md`; `aws-architect-reviewer` reviews it. The two authors run in parallel (different files).
Work-orders: `wo-NN-solution-architect.md` (+ one `wo-NN-solution-reviewer` per design and one for the index), `wo-NN-infrastructure-architect.md` (+ one review). Each carries Functionality and Diagram (the flow it designs).

### When to split into several designs (the architect decides, `design.md` lists all)

| Split | Example |
|---|---|
| Flows with their own sequence | "list items" (synchronous) and "classify with AI" (asynchronous, SQS) |
| Different functionalities in one change | `items` and `billing` |
| Parts that go to parallel tasks | a screen and an event consumer |
| **Do not split** | only because the document grew; one flow = one design |

Rules: every `R*` of the change is **owned by exactly one** design (it may be cited in others); contracts stay in `architecture/contracts/` and designs point to them; every E5 work-order cites the design it came from.

### Each design (`design/<flow>.md`) - 11 sections

| # | Section | Content |
|---|---|---|
| 1 | Scope | what is in and out |
| 2 | Traceability | R* -> screen -> front component -> endpoint/event -> Lambda -> table/queue -> ADR |
| 3 | Sequences | one ASCII diagram per main scenario |
| 4 | Contracts used or changed | links to `contracts/*.md`; changes marked as deltas |
| 5 | Data model | keys (PK/SK), indexes, sample item, who writes, who reads |
| 6 | Errors | HTTP code / error event per failure, and what the front shows |
| 7 | Logical security | claims used, per-route authorization, tenant isolation |
| 8 | Times and limits | gateway, Lambda, LLM and third-party timeouts (sum fits the budget) |
| 9 | AI | provider, model, prompt location, fallback, cost |
| 10 | Build order | contract -> back -> front -> infra -> observability -> CI/CD |
| 11 | Risks and `(unverified)` | inherited from the skills |

`infra-design.md` sections: new or changed resources per environment, IAM per Lambda, new secrets, new alarms, Terraform modules touched, effect on the pipeline (new job, new GitHub environment), extra cost.
An architecture or infrastructure delta needed by a design returns to [E2](e2-architecture-and-adrs.md) (delta + new ADR in the right folder, re-verified).

### Acceptance E4 (verifiers: reviewers, not me)

1. `verify-E4-<flow>.md` pass for each design (`from: solution-architecture-reviewer`); `verify-E4-infra.md` pass (`from: aws-architect-reviewer`).
2. `verify-E4-index.md` pass: coverage - every `R*` of the change is owned by one design; each design listed in `design.md`.
3. Every architecture change has delta + ADR. `fail` -> new work-order to the author (not edit the verifier's record), re-run only the failed one.
Shown to the user, not blocking.

## E5 - Tasks (`tasks.md` + one work-order per task)

Each task row: ID (`T1`), requirements covered, design it came from, component, owner role, dependencies, skills the work-order must list.
Size rule: a task fits one I0-I9 cycle (one endpoint or event consumer, one screen, one Terraform module set, one observability set, one pipeline).
Order: contract -> back (and AI) -> front -> infra -> observability -> CI/CD. **First change of the project: task T0 = bootstrap** (GitHub OIDC provider, roles `<env>-deploy` and `<env>-pr`, state bucket with lock; written by `aws-terraform-engineer`, reviewed by `terraform-code-reviewer`; the **user applies it once** with the commands in `result-NN-infra`, `gate=bootstrap-apply`; no agent applies) before the CI/CD task. The CI/CD task writes the workflows and returns the list "user-must-add" (branch protection, required check `ci-gate`, GitHub environments, variables with role ARNs).
Keep OpenSpec's own checkbox convention in `tasks.md` (IDs live in the task text, U2).

### Choosing owner and skills

| Task type (role) | Owner | Skills the work-order lists (see [knowledge map](knowledge-map.md)) |
|---|---|---|
| Lambda handler / HTTP endpoint (`code`) | `quarkus-lambda-integrator` | `developing-quarkus-amazon-lambda-http-v3-40` (+ `developing-quarkus-rest-v3-40`; HTTP or REST variant per the API ADR), `testing-quarkus-amazon-lambda-v3-40`, `developing-quarkus-junit-v3-40`, `refactoring-quarkus-java`, `structuring-quarkus-lambda-projects` |
| Cognito-secured resource | same | + `securing-quarkus-lambda-cognito-v3-40` |
| DynamoDB / S3 access | same | + `integrating-quarkus-amazon-data-v3-40` |
| SQS / SNS / EventBridge consumer | same | + `integrating-quarkus-amazon-messaging-v3-40` |
| Instrumentation in code | same | + `logging-`, `tracing-`, `monitoring-quarkus-lambda-v3-40` (or umbrella `observing-quarkus-lambda`) |
| AI in a Lambda (`ai`) | `quarkus-lambda-integrator` | + `integrating-quarkus-langchain4j-v1-15`; create only after the yes to D1 (`gate=D1-langchain4j`); settles line `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)` |
| Stripe (`stripe`) | `stripe-integrator` | + `integrating-stripe-quarkus-v3-40`, stripe-java 34 skills |
| Front end (`frontend`) | `nextjs-frontend-integrator` | the IN Vercel skills (`react-best-practices`, `composition-patterns`, `building-components`, `web-design-guidelines`, `next-dev-loop`, ...); first front task = tokens + base components |
| Terraform incl. bootstrap and site hosting (`infra`) | `aws-terraform-engineer` | matching `provisioning-aws-<service>-v6` |
| CloudWatch / X-Ray / dashboards / alarms (`observability`, Mode B) | `aws-observability` | `validating-aws-observability`, `provisioning-aws-cloudwatch-v6`, `provisioning-aws-xray-v6`, `monitoring-cloudwatch-observability` |
| Workflows (`cicd`) | `cicd-pipeline-engineer` | `composing-github-actions-pipelines`, plus the stack skills (Java, Next.js, Terraform, OIDC, blast radius, supply chain) |

### Work-order per task

Write `wo-NN-<role>.md` from the profile template (`coordinating-quarkus-aws-handoffs/assets/wo-*.template.md`): required sections **Functionality** (what the user gains, 2-4 sentences), **Diagram** (sequence or flow from the design the task came from; the wireframe cut for a front task), Skills, Requirements (with scenarios), Applicable ADRs (from the 3 folders), Constraints (`limits`, `coverage_min`), Acceptance criteria. Frontmatter: `kind: work-order`, `status: pending`, `from: building-aws-saas-serverless-quarkus-react-nextjs`, `to: <agent>`, `change`, `task`, `requirements`, `createdAt` real UTC (`date -u +%Y-%m-%dT%H:%M:%SZ`). Then `check_records.py`.

### Acceptance E5

1. `spec-synchronizer` reviews `tasks.md` and the work-orders: every `R*` has a task; every task cites `R*`; every work-order has Functionality and Diagram; dependencies have no cycle and respect the order; saved as `verify-E5.md` (must be `pass`). I also list `R*` ids against `requirements:` myself (the board does not read `tasks.md`, L3).
2. `board.py` runs without error and shows all tasks `pending`.
3. The user approves the task list (verbatim, `gate=E5`) before the first launch.

### E5 drift baseline (after the approval, before the first work-order)

`detect_drift.py` exits 1 until a `lastSyncedSha` exists, and only `board.py --sync-sha` sets it. Right after the task-list approval and **before the first work-order** run:

```
python <scripts>/board.py <handoff-dir> --profile <profile> --sync-sha $(git rev-parse HEAD)   # valid in Git Bash and in PowerShell
```

Record it under `## Approvals` as `gate=E5-baseline` (`subject=<sha>`; the baseline hides no drift because no code of this change exists yet). Later `--sync-sha` calls happen only after an accepted delta ([E8](e8-reverse-sync.md)).

Independent tasks may run in parallel (<= 4, disjoint files); dependent ones in order.
