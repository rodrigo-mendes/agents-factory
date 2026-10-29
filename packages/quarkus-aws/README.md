# quarkus-aws

**Quarkus 3.40 LTS on AWS Lambda**, reusable outside any one SaaS. Built on `quarkus-core`.

| Kind | Names |
|---|---|
| knowledge skills (version-locked) | `developing-quarkus-amazon-lambda-v3-40`, `developing-quarkus-amazon-lambda-http-v3-40`, `securing-quarkus-lambda-cognito-v3-40`, `integrating-quarkus-amazon-data-v3-40`, `integrating-quarkus-amazon-messaging-v3-40`, `testing-quarkus-amazon-lambda-v3-40`, `logging-quarkus-lambda-v3-40`, `tracing-quarkus-lambda-v3-40`, `monitoring-quarkus-lambda-v3-40` |
| composition skills | `observing-quarkus-lambda` (3-pillar umbrella), `structuring-quarkus-lambda-projects` |
| agents | `quarkus-lambda-integrator` (executor, implementation steps I0–I6, I8, I9), `quarkus-code-reviewer` (read-only, step I7) |
| rules | `quarkus-lambda-code-standards`, `quarkus-lambda-project-config` |

Version facts and provenance: `workspace/quarkus-aws-saas/` (research files, `_family_facts_v3.40.md`).
Key version decisions: Quarkiverse amazon-services 3.23.0; `quarkus-test-amazon-lambda` was removed in
Quarkus 3.31 (tests use `quarkus-junit` + RestAssured); JVM + SnapStart vs native and X-Ray SDK vs
OpenTelemetry are ADR decisions.

Depends on: factory-core, quarkus-core, handoff-core, aws-skills.
