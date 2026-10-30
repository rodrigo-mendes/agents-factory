# E2 - Solution, design and infrastructure (3 fronts)

Back to [SKILL.md](../SKILL.md). One spec per area, evolving; a later change touches it through a delta + ADR. I (the manager) write none of it: each front has an author agent and a different reviewer agent.
The tree and the rules of who writes what live in the rule `openspec-project-layout` (package `openspec-core`; factory convention, not official OpenSpec).

## Where (three areas, three ADR folders)

| Area | Files | Author | Reviewer |
|---|---|---|---|
| Solution (E2a) | `openspec/specs/architecture/spec.md`, `architecture/contracts/*.md`, `architecture/adr/NNN-*.md` | `solution-architect` (opus) | `solution-architecture-reviewer` |
| Design (E2b) | `openspec/specs/design/design-system.md`, `design/adr/NNN-*.md` (wireframes and navigation come in [E3b](e3b-ui-design.md)) | `ui-ux-designer` | `ui-design-reviewer` |
| Infrastructure (E2c) | `openspec/specs/infrastructure/spec.md`, `infrastructure/adr/NNN-*.md` | `aws-infrastructure-architect` (opus) | `aws-architect-reviewer` |
| Later-change deltas | `openspec/changes/<id>/specs/<area>/spec.md` | same as the area | same as the area |

ADR numbering is **per folder** (each starts at 001). Cite an ADR by path: `architecture/adr/003`, `design/adr/002`, `infrastructure/adr/001`. Template: `coordinating-quarkus-aws-handoffs/assets/adr.template.md` (field `area`: architecture | design | infrastructure). An accepted ADR is never edited, only `superseded by NNN`. Violation of an ADR of any folder is HIGH for every code reviewer.
Path names are the profile's (`spec.architecture`, `spec.adr_dir` = `architecture/adr`, informational); work-orders list all three ADR folders.

```
E1 verified
   |-- E2a solution-architect  -> solution-architecture-reviewer -> verify-E2a --+
   |-- E2b ui-ux-designer      -> ui-design-reviewer             -> verify-E2b --+   (E2a and E2b may run in parallel)
   +--  after E2a: E2c aws-infrastructure-architect (+ aws-observability Mode A)
                   -> aws-architect-reviewer -> verify-E2c
all three pass -> I show the 3 fronts -> the user approves E2 -> every ADR (3 folders) becomes accepted
```

Work-orders: `wo-NN-solution-architect.md`, `wo-NN-designer.md`, `wo-NN-infrastructure-architect.md` (each `task: spec`); the reviewers get `wo-NN-solution-reviewer.md`, `wo-NN-design-reviewer.md` and `wo-NN-infrastructure-reviewer.md` (a verify, not a code review). Every launch uses the model of the [Model split](../SKILL.md#protocols) (opus for the two architects, sonnet for the rest).

## E2a - Solution architecture

The author writes from the playback (B2-B7, B12) and loaded skills; the manager cites, never decides. Required in `architecture/spec.md`: components (web app, API, Lambdas, data, events, AI); tenancy model; security logic (authN, authZ per route, secrets use); data model with tenant owner; integrations (Stripe, LLM provider); **measurable NFR targets (number + unit)**; observability needs (SLOs, mandatory log fields `requestId` and `tenantId`); code conventions. Contracts: one file per endpoint group and per event (method, input, output, errors, who calls; fields, producer, consumer).
For every AWS or Quarkus statement it cites the skill that owns it; no skill -> `(unverified)`. An open decision without an answer -> `needs-input` (I ask the user, then relaunch).

ADR triggers: every B7 constraint; tenancy and security models; **API Gateway type HTTP vs REST** (X-Ray and WAF attach to REST API only; JWT authorizer is HTTP API only); **runtime JVM + SnapStart vs native**; **tracing X-Ray SDK vs OpenTelemetry** (X-Ray SDK/Daemon in maintenance since 2026-02-25, never an unqualified default); metrics Micrometer vs CloudWatch EMF; Cognito integration option; payload strategy above SQS 1 MiB; **LLM provider** (and the D1 pre-release choice); **static export** (no SSR); each trade-off between NFR targets.
Each ADR: status `proposed`, context linking `R*` or B-blocks, decision in one sentence, **>= 2 alternatives** with rejection reason citing a skill, consequences (what becomes forbidden = reviewer check), sources (none -> `(unverified)`).

## E2b - Design system

`ui-ux-designer` writes `design/design-system.md` (colors light/dark with computed contrast, typography, spacing, radii, shadows, base components with states normal/hover/focus/disabled/error, accessibility rules) and `design/adr/` (component base, style/token strategy, theming, accessibility level, languages, layout/density), from B9-B11 and the skills `building-components`, `web-design-guidelines`, `composition-patterns`. A design decision that weighs on architecture (bundle size, i18n routes) is cited by the `solution-architect` in `architecture/spec.md`. In E6 the first front task is tokens + base components.

## E2c - Infrastructure design (`infrastructure/spec.md`, 12 sections)

Starts after `verify-E2a` is `pass` (uses the components and contracts). `aws-observability` Mode A reviews section 8 (brief in [worker briefs](worker-briefs.md#aws-observability)).

| # | Section | Content |
|---|---|---|
| 1 | Environments and accounts | dev, prod (others); one account per environment or not; region |
| 2 | Component -> AWS service map | each E2a component with service, size/limit, why |
| 3 | Network | VPC or not (Lambda outside a VPC by default), endpoints, egress to LLM/Stripe |
| 4 | Edge | API Gateway (type, throttling), CloudFront + OAC, WAF, Route53, ACM |
| 5 | Identity and access | Cognito, Lambda roles (least privilege), GitHub OIDC roles per environment |
| 6 | Secrets and keys | Secrets Manager/SSM, KMS, rotation |
| 7 | Data | DynamoDB (capacity mode, PITR), S3, retention |
| 8 | Observability | log groups and retention, alarms, X-Ray, dashboards |
| 9 | Terraform | module layout, one state per environment and component, S3 backend with lock |
| 10 | CI/CD | GitHub environments, role per environment, who releases prod (from B8: GitHub plan) |
| 11 | Cost | estimate per environment and what weighs most |
| 12 | Risks and `(unverified)` | inherited from the skills |

Skills the architect loads (only those the change needs): see Wave 6 of the [knowledge map](knowledge-map.md). ADRs in `infrastructure/adr/` (accounts, state backend, GitHub OIDC roles, CloudFront/OAC/WAF, ...). It never changes components or contracts: a needed change returns as a question to me.

## Acceptance (E2 accepted)

Verifiers: the three reviewers **and** `check_records.py` (ADR fields) **and** the user.

1. `verify-E2a`, `verify-E2b`, `verify-E2c` are `pass`, each saved verbatim from the reviewer's inline answer (`saved-by`, `outcome: pass|fail`, sections Criteria and Evidence).
2. Every NFR target has number + unit; every relevant decision has a complete ADR in its folder (>= 2 alternatives, consequences, sources).
3. Tenancy, security and the section 10 CI/CD plan are defined.
4. No HIGH finding open.
5. If the change has AI: the user answered D1 (`gate=D1-langchain4j`).
6. The user approves E2 as one gate (verbatim, `gate=E2`); only then I set every ADR `accepted`. The user approving does not replace the reviewers.

On `fail`: return the findings to the author in a new work-order, re-run the reviewer; ask the user after 2 failed attempts at the same finding (not a counted loop; the counted ones are in the profile).

## Later changes

If the change adds a service, alters tenancy/security/runtime, the design system or the infrastructure: the matching author writes a delta (OpenSpec delta format via the openspec skill) plus a new ADR (superseding if needed), the matching reviewer verifies; only the fronts with a delta re-enter E2. Otherwise skip E2 and cite the ADRs in E4.
