# Roles and skills per work-order

Back to [SKILL.md](../SKILL.md). The orchestrator lists in each work-order's `## Skills` only what
the task needs; an agent loads those and nothing else (a needed skill that is not listed becomes a
question, outcome `needs-input`). Skill names below are the installed names (checked against the
package folders on 2026-10-28; the Vercel names come from the upstream repositories installed by `vercel-frontend`).

## Solution-architect work-order (`solution-architect`, Opus; review by `solution-architecture-reviewer`)

E2a and E4. The aws-skills the question needs (e.g. `architecting-aws-saas-multitenant`, `designing-dynamodb-nosql`,
`designing-aws-api-gateway-serverless`, `architecting-lambda-serverless-patterns`) plus the specs and ADRs. For the AI parts
`integrating-quarkus-langchain4j-v1-15` as knowledge only after the user's yes to D1. It never lists infrastructure skills (accounts, network, modules).

## Infrastructure-architect work-order (`aws-infrastructure-architect`, Opus; review by `aws-architect-reviewer`)

E2c and E4. Only the skills the change needs: `applying-aws-serverless-well-architected-lens`, `architecting-aws-saas-multitenant`,
`designing-aws-api-gateway-serverless`, `delivering-cloudfront-cdn`, `securing-aws-waf-web-acls`, `securing-aws-iam-serverless`,
`securing-aws-secrets-certificates`, `designing-dynamodb-nosql`, `federating-github-actions-aws-oidc`,
`limiting-blast-radius-github-actions-deploys`, `managing-aws-costs`. Its observability section is reviewed by `aws-observability` mode A.

## Designer work-order (`ui-ux-designer`; review by `ui-design-reviewer`)

E2b and E3b. `web-design-guidelines`, `building-components` (tokens, accessibility, composable APIs) and any other Vercel skill the
work-order names. Static export is a constraint: no screen may need a server render.

## Code work-order (`quarkus-lambda-integrator`, role `code`)

| Task type | Skills to list |
|---|---|
| Any code task, I4/I5 | `refactoring-quarkus-java` (always) |
| Lambda handler, event function, packaging, JVM/native/SnapStart | `developing-quarkus-amazon-lambda-v3-40` |
| REST endpoint behind API Gateway | `developing-quarkus-amazon-lambda-http-v3-40`, `developing-quarkus-rest-v3-40` |
| Authenticated or role-based endpoint | `securing-quarkus-lambda-cognito-v3-40` |
| DynamoDB or S3 access | `integrating-quarkus-amazon-data-v3-40` |
| SQS / SNS / EventBridge consumer or producer, SSM/Secrets config | `integrating-quarkus-amazon-messaging-v3-40` |
| Tests (every code task) | `testing-quarkus-amazon-lambda-v3-40`, `developing-quarkus-junit-v3-40` |
| CDI wiring | `developing-quarkus-arc-v3-40` |
| Logging / tracing / metrics in code | `logging-quarkus-lambda-v3-40`, `tracing-quarkus-lambda-v3-40`, `monitoring-quarkus-lambda-v3-40`, or the umbrella `observing-quarkus-lambda` |
| New project layout | `structuring-quarkus-lambda-projects` |

## AI work-order (`quarkus-lambda-integrator`, role `ai`; review `langchain4j-reviewer` -> `quarkus-code-reviewer`)

Same Quarkus skills as a code task plus `integrating-quarkus-langchain4j-v1-15` (locked to the 1.15.0.CR1 pre-release; list it only after
the user's yes to its Ask First D1, recorded under `## Approvals` as `gate=D1-langchain4j` (verbatim words) and written in the work-order's
settles line as `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)`). AI runs only in the Lambdas; there is no chat in the front end.

## Stripe work-order (`stripe-integrator`, review by `stripe-advisor` -> `quarkus-code-reviewer`)

`integrating-stripe-quarkus-v3-40` (+ the Stripe Java skills the work-order names), plus the same
Quarkus skills as a code task for the endpoint (`developing-quarkus-amazon-lambda-http-v3-40`,
`securing-quarkus-lambda-cognito-v3-40` when the route is authenticated). The raw webhook body must
stay intact for the signature (see the Stripe skill). Review order: `stripe-advisor` first;
`quarkus-code-reviewer` only after the advisor's review is `approved` (hold: the second review work-order is written
`pending` before `board.py` runs, the task's work-orders go `done` after the second `approved`). Every review record of the task carries
`role: stripe`. Each `changes-requested` is one `review_rounds` round, so a project may raise `limits.review_rounds` for Stripe tasks
in `openspec/handoff-profile.yaml`.

## Front-end work-order (`nextjs-frontend-integrator`, role `frontend`; review `nextjs-code-reviewer` -> `ui-design-reviewer`)

The Vercel skills that work with a static export, only the ones the screen needs: `react-best-practices`, `composition-patterns`,
`building-components`, `web-design-guidelines`, `next-dev-loop` (and `next-bundle-optimizer` when the work-order names it).
`ai-elements` is not used (no chat in the front end); skills that need a server or the Vercel platform stay out. Inputs: wireframe, design system, contract.
Build line: `pnpm install --frozen-lockfile && lint && test && build` on Node 26 (same as `building-nextjs-github-actions-v16-4`).
Both reviews carry `role: frontend`; the visual review compares the code with the wireframe and the design system in both themes.

## Terraform work-order (`aws-terraform-engineer`, role `infra`; review by `terraform-code-reviewer`)

The work-order carries the engineer's closed requirement (services, root vs module, region/account scope,
naming and tags, state backend or "no backend", mocked test wanted); it runs offline checks only and never
plans or applies (the pipeline plans and applies; the bootstrap is applied once by the user, `gate=bootstrap-apply`). One `provisioning-aws-<service>-v6` per
service in the task. Names present in the repo:
`lambda`, `api-gateway`, `iam`, `dynamodb`, `s3`, `cognito`, `sqs`, `sns`, `eventbridge`, `kms`,
`secrets-manager`, `parameter-store`, `vpc`, `waf`, `cloudfront`, `acm`, `route53`, `step-functions`,
`ses`, `shield`, `cloudtrail`, `cost-management`, `organizations`, `sam`, `cloudwatch`, `xray`
(each `provisioning-aws-<name>-v6`). Hosting of the front end (S3 bucket, CloudFront with OAC, WAF, ACM, Route53) and the bootstrap
(GitHub OIDC provider, roles `<env>-deploy` and `<env>-pr`, state bucket with lock) are infra tasks. Log groups, alarms, dashboards and X-Ray groups belong
to the observability work-order, not to Terraform tasks. Review records carry `role: infra`.

## CI/CD work-order (`cicd-pipeline-engineer`, role `cicd`; review by `cicd-pipeline-reviewer`)

`composing-github-actions-pipelines`, `building-java-github-actions`, `building-nextjs-github-actions-v16-4`,
`automating-terraform-github-actions-v1-17`, `federating-github-actions-aws-oidc`, `limiting-blast-radius-github-actions-deploys`,
`securing-supply-chain-github-actions` (the ones the pipeline needs). Closed requirement: GitHub plan and visibility, targets, environments, repo layout.
Review records carry `role: cicd`.

## Review work-order (variants)

Table in [wo-review](../assets/wo-review.template.md): reviewer per task type, `role:` of the review record, and who gets `changes-requested`.
Always: the skills the authoring work-order listed (their Never-Do items are the review criteria) + the accepted ADRs of the **three** folders
(`architecture`, `design`, `infrastructure`); a violation of any of them is HIGH. Back end and AI: `refactoring-quarkus-java` checklist.
The review work-order's Constraints carry the authoring work-order's settles line copied verbatim (e.g.
`D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)` when `integrating-quarkus-langchain4j-v1-15` is listed).

## Observability work-order (`aws-observability`)

`validating-aws-observability`, `provisioning-aws-cloudwatch-v6`, `provisioning-aws-xray-v6`,
`monitoring-cloudwatch-observability` and `tracing-aws-xray` (aws-skills); the observability section
of `infrastructure/spec.md` is the input. Mode B (Terraform) is reviewed by `terraform-code-reviewer` (`role: observability`). Mode C starts from the
`smoke_start_epoch` of the CD pipeline record. The alarm firing test only with the user's approval.

## Debug / verify work-orders

- `aws-lambda-debugger`: `debugging-aws-lambda` (the debugger never invokes the function); mode B adds `validating-aws-observability`
  (read-only scripts only). When the runtime is Quarkus list `logging-quarkus-lambda-v3-40`, `tracing-quarkus-lambda-v3-40`,
  `developing-quarkus-amazon-lambda-v3-40` so it can read logs, traces and handler settings.
- `static-site-verifier`: the work-order names the site URL, the sha256 of `out/` from the pipeline record and the checks of its agent definition (read-only).
- `spec-synchronizer`: `coordinating-agent-handoffs`, `specifying-changes-with-openspec-v1-15`.

## Rule of thumb

List the smallest set; the reviewer's Never-Do checklist is exactly the union of listed skills, so
an unlisted skill is an unreviewed risk. Every listed skill keeps its `(unverified)` /
`(medium confidence)` tags in the agent's result.
