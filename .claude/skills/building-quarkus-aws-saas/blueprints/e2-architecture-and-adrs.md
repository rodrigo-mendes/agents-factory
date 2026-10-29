# E2 - Technical architecture spec and ADRs

Back to [SKILL.md](../SKILL.md). One architecture spec per project, evolving; changes touch it via an architecture delta + ADR.

## Where

| File | Role |
|---|---|
| `openspec/specs/architecture/spec.md` | components, AWS services, tenancy, security, data model, integrations, NFR targets, observability, IaC layout, code conventions |
| `openspec/specs/architecture/adr/NNN-<title>.md` | one ADR per expensive-to-change decision (template: `coordinating-quarkus-aws-handoffs/assets/adr.template.md`) |
| `openspec/changes/<id>/specs/architecture/spec.md` | architecture **delta** when a later change alters architecture |

Path names are the profile's (`spec.architecture`, `spec.adr_dir`); read them from the profile, do not hardcode.

## Authoring (orchestrator, from B5-B7)

Write the spec yourself from the interview answers. Fill each section only with decisions the user confirmed or that follow from a
loaded skill; mark gaps as questions, never as defaults. For every AWS or Quarkus statement cite the skill that owns it
([knowledge map](knowledge-map.md)); no skill -> `(unverified)`.

Required sections: components view (SPA + CDN, API, Lambdas, data, events); AWS services chosen; tenancy model (pool / silo / bridge);
security (authN, authZ, secrets); data model with tenant owner; integrations (Stripe, LLM provider); **measurable NFR targets
(number + unit)**; observability (SLOs, mandatory log fields incl. `requestId` and `tenantId`, retention, trace sampling,
alarm list with thresholds, dashboards); IaC layout; code conventions.

The observability section is reviewed by `aws-observability` before acceptance (brief in [worker briefs](worker-briefs.md#aws-observability)).

## ADR triggers (one ADR each)

- every B7 constraint; every AWS service choice (e.g. DynamoDB vs Aurora per `designing-dynamodb-nosql`);
- tenancy model and security model (`architecting-aws-saas-multitenant`, `securing-aws-cognito`);
- **API Gateway type: HTTP API vs REST API.** Facts to cite from the family facts: X-Ray tracing and AWS WAF attach to REST API only; JWT authorizer is HTTP API only; with `quarkus-amazon-lambda-http` (HTTP API) a trace starts at the Lambda segment. The Quarkus extension is chosen per API type (`-http` HTTP API payload 2.0, `-rest` REST API; both "preview" per the guide);
- **Runtime: JVM + SnapStart vs native.** SnapStart does not support OS-only runtimes (so not Quarkus native); Quarkus native pairs with `provided.al2023` (inference, medium confidence); decided from the cold-start NFR;
- **Tracing: X-Ray SDK vs OpenTelemetry.** AWS X-Ray SDKs and Daemon are in maintenance mode since 2026-02-25 (security fixes only); AWS recommends OpenTelemetry. Never an unqualified default: ask and record;
- **Metrics: Micrometer vs CloudWatch EMF** (no Quarkiverse CloudWatch Micrometer registry exists); logging library (Powertools Java logging inside Quarkus is (unverified));
- Cognito integration option (Lambda HTTP security vs in-function OIDC), HTTP client for AWS SDK clients, payload strategy above SQS 1 MiB, each external provider (Stripe, LLM), each trade-off between NFR targets.

Each ADR: status `proposed -> accepted` (an accepted ADR is never edited, only `superseded by NNN`), context linking `R*`, decision in one sentence, **>= 2 alternatives**
with rejection reason citing a skill, consequences (positive, negative, what becomes forbidden = reviewer check in I7), sources (skills/pages; none -> `(unverified)`).
Numbering sequential, never reused.

## Acceptance (E2 accepted)

Verifier: `aws-architect` (brief) **and** `check_records.py` (ADR fields) **and** the user.

1. Every NFR target has number + unit.
2. Every relevant decision has a complete ADR (>= 2 alternatives, consequences, sources).
3. Tenancy and security models are defined.
4. No HIGH finding open from `aws-architect`.
5. The user approves (verbatim in `## Approvals`, `gate=E2`).

Save `aws-architect`'s inline answer as `verify-E2.md` (`from: aws-architect`, `saved-by: building-quarkus-aws-saas`, `outcome: pass|fail`, sections Criteria and Evidence).
On `fail`: fix, re-run; this is not a counted loop but ask the user after 2 failed attempts at the same finding. The user approving does not replace the verifier.

## Later changes

If the change adds a service or alters tenancy/security/runtime: write the architecture delta (OpenSpec delta format via the openspec skill) plus a new ADR (superseding if needed), run the same acceptance. Otherwise skip E2 and cite the ADRs in E4.
