# P2 — Inventory, go/no-go and design (2026-10-28)

Design source: approved plan (`C:\Users\r.dos.santos.mendes\.claude\plans\quero-poder-programar-aws-transient-karp.md`).
Versions: `P1_version_gate.md`.

## Go/no-go — research units

| Unit | Need | Official docs | Skill name | Package | Worker | Scope boundary | Overlap | Go? |
|---|---|---|---|---|---|---|---|---|
| U1 | Quarkus on Lambda runtime | quarkus.io/guides/aws-lambda ; docs.aws.amazon.com/lambda (runtimes, SnapStart) | `developing-quarkus-amazon-lambda-v3-40` | quarkus-aws | researching-technical-frameworks | plain handlers, packaging, JVM/native/SnapStart, `quarkus-amazon-lambda-xray` mention only | `architecting-lambda-serverless-patterns` (generic, links) | GO (pilot) |
| U2 | HTTP on Lambda | quarkus.io/guides/aws-lambda-http | `developing-quarkus-amazon-lambda-http-v3-40` | quarkus-aws | idem | API GW REST/HTTP event mapping, Quarkus REST on Lambda | `developing-quarkus-rest-v3-40` (REST basics) | GO |
| U3 | Cognito authN/authZ | quarkus.io guides aws-lambda-http (security), security-oidc-bearer-token, security-authorize-web-endpoints | `securing-quarkus-lambda-cognito-v3-40` | quarkus-aws | idem | authorizer claims → SecurityIdentity, JWT, roles/permissions, tenant | `securing-aws-cognito` (AWS side) | GO |
| U4 | DynamoDB + S3 | docs.quarkiverse.io/quarkus-amazon-services (3.23.0) | `integrating-quarkus-amazon-data-v3-40` | quarkus-aws | idem | client config, enhanced client, presigned URLs, Dev Services | `designing-dynamodb-nosql`, `architecting-aws-s3-storage` | GO |
| U5 | SQS/SNS/EventBridge + SSM/Secrets | idem | `integrating-quarkus-amazon-messaging-v3-40` | quarkus-aws | idem | clients, SQS-triggered Lambda, config sources | `architecting-aws-sqs-messaging`, `securing-aws-secrets-certificates` | GO |
| U6 | Lambda testing | quarkus.io/guides/aws-lambda (mock event server), Quarkiverse Dev Services | `testing-quarkus-amazon-lambda-v3-40` | quarkus-aws | idem | `@QuarkusTest` on Lambda, mock event server, LocalStack | `developing-quarkus-junit-v3-40` | GO |
| U7 | Stripe on Quarkus | stripe.com/docs (webhooks, idempotency) + Quarkus guides | `integrating-stripe-quarkus-v3-40` | quarkus-aws-saas | idem | CDI producer, Secrets, raw body on Lambda, idempotency | stripe-java v34 skills (API facts) | GO |
| U8 | LangChain4j on Quarkus | docs.quarkiverse.io/quarkus-langchain4j | `integrating-quarkus-langchain4j-v1-15` | quarkus-aws-saas | idem | AiServices, OpenAI/Anthropic/Bedrock | langchain4j 1.22.0 skills | **G1 decision** (no stable for 3.40) |
| U9 | OpenSpec SDD | github.com/Fission-AI/OpenSpec (v1.15.0) | `specifying-changes-with-openspec-v1-15` | handoff-core | idem | layout, deltas, CLI, Claude Code commands | — | GO (+ G1 decision on overlap) |
| U10 | Clean code Quarkus | refactoring sources + Quarkus CDI guide | `refactoring-quarkus-java` | quarkus-core | artifact-author from `refactoring-oci-java` + Quarkus facts (light research) | behavior-preserving refactor | `refactoring-oci-java` (pattern) | GO |
| U11 | Logging | quarkus.io/guides/logging, aws lambda logging (advanced controls) | `logging-quarkus-lambda-v3-40` | quarkus-aws | idem | JSON logs, MDC, levels, no PII | `monitoring-cloudwatch-observability` | GO |
| U12 | Tracing | quarkus.io/guides/aws-lambda (xray), opentelemetry guide, ADOT | `tracing-quarkus-lambda-v3-40` | quarkus-aws | idem | X-Ray vs OTel, SDK tracing, native | `tracing-aws-xray` | GO |
| U13 | Metrics | quarkus.io/guides/telemetry-micrometer, CloudWatch EMF, Powertools v2 | `monitoring-quarkus-lambda-v3-40` | quarkus-aws | idem | Micrometer vs EMF, tenant dimensions, Powertools+Quarkus compat | `implementing-lambda-powertools-java` (v2.10.0) | GO |
| D1 | Lambda deploy procedure | docs.aws.amazon.com/lambda (versions, aliases, SnapStart activate) | `deploying-aws-lambda` | aws-lambda | idem | artifact → plan → apply (ask) → smoke → rollback | `provisioning-aws-lambda-v6` (HCL) | GO |
| D2 | Lambda debug procedure | docs.aws.amazon.com/lambda (troubleshooting), API GW errors | `debugging-aws-lambda` | aws-lambda | idem | 502/503/504, timeout, AccessDenied, throttling, cold start | `debugging-deployed-functions` (OCI pattern) | GO |
| V1 | Live observability validation | AWS CLI reference (logs, cloudwatch, xray) | `validating-aws-observability` | aws-observability | idem + scripts by artifact-author | read-only checks, alarm test ask-first | `validating-oci-observability` (pattern) | GO |

Not researched (no new facts): `observing-quarkus-lambda` (umbrella), `structuring-quarkus-lambda-projects`, orchestrator, handoff skills/profiles, agents, rules — authored from the units above and the plan.

Declared coverage (no gap): CloudWatch dashboards/SLOs/Application Signals → `monitoring-cloudwatch-observability`; Lambda aliases/SnapStart HCL → `provisioning-aws-lambda-v6`; CDN/Route 53/ACM/WAF → existing skills.

Open verification for P5: APM `hooks:` support in apm 0.35.0 (no package in the repo uses it yet). If unsupported → the hook ships as a documented snippet the user pastes after confirmation.

## Package design (from plan §4.1, §4.2, §6)

quarkus-core · camel-quarkus-skills (♻️) · quarkus-aws · aws-lambda · aws-observability · handoff-core · quarkus-aws-saas · oci-core (♻️ profile) · stripe-java (♻️ 1 line, G1).
Root `apm.yml`: add only `quarkus-aws-saas`; verify transitive resolution with `apm audit --ci` at P8.
