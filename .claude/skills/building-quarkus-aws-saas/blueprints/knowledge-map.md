# Knowledge map by waves (real skill names)

Back to [SKILL.md](../SKILL.md). Each wave depends on the previous one. Use the map to (a) decide which skills a work-order lists and (b) tell the user what is covered.
Status column = state at authoring (2026-10-28, from `packages/*/.apm/skills/`); **re-verify with `ls .claude/skills/` at preflight**. If a listed skill is absent at run time, stop that area and tell the user.

## Wave 0 - Process

| Topic | Skill | Status |
|---|---|---|
| Handoff protocol, scripts, templates | `coordinating-agent-handoffs` | exists |
| Quarkus/AWS handoff profile (`assets/handoff-profile.yaml`, templates) | `coordinating-quarkus-aws-handoffs` | exists |
| OpenSpec format and CLI (v1.15) | `specifying-changes-with-openspec-v1-15` | exists |
| Spec sync command | `syncing-spec-from-code` | exists |
| Clean code and refactoring (I4/I5) | `refactoring-quarkus-java` | exists (in `quarkus-core`) |

## Wave 1 - Lambda base, HTTP API, tests

| Topic | Skill | Status |
|---|---|---|
| Quarkus on Lambda (`quarkus-amazon-lambda`, `function.zip`, JVM vs native, SnapStart) | `developing-quarkus-amazon-lambda-v3-40` | exists |
| Project layout | `structuring-quarkus-lambda-projects` | exists |
| HTTP behind API Gateway (`-http` / `-rest`) | `developing-quarkus-amazon-lambda-http-v3-40` | exists |
| Tests (mock event server, no `quarkus-test-amazon-lambda` from 3.31) | `testing-quarkus-amazon-lambda-v3-40`, `developing-quarkus-junit-v3-40` | exists |
| Lambda patterns / API Gateway design | `architecting-lambda-serverless-patterns`, `designing-aws-api-gateway-serverless` | exists (aws-skills) |
| Base Quarkus | `developing-quarkus-arc-v3-40`, `developing-quarkus-rest-v3-40` | exists |

## Wave 2 - Identity

| Topic | Skill | Status |
|---|---|---|
| Cognito, claims -> identity, roles, tenant per user | `securing-quarkus-lambda-cognito-v3-40` | exists |
| Cognito service, IAM for serverless | `securing-aws-cognito`, `securing-aws-iam-serverless` | exists |

## Wave 3 - Data and events

| Topic | Skill | Status |
|---|---|---|
| DynamoDB / S3 clients (Quarkiverse), tenant isolation | `integrating-quarkus-amazon-data-v3-40`, `designing-dynamodb-nosql`, `architecting-aws-s3-storage` | exists |
| SQS / SNS / EventBridge, config sources (SSM, Secrets Manager) | `integrating-quarkus-amazon-messaging-v3-40`, `architecting-aws-sqs-messaging`, `architecting-aws-sns-pubsub`, `architecting-eventbridge-eda`, `securing-aws-secrets-certificates` | exists |

## Wave 4 - Frontend

SPA on S3 + CloudFront, DNS, certificates, WAF: `delivering-cloudfront-cdn`, `architecting-aws-s3-storage`, `configuring-aws-route53-dns`, `securing-aws-waf-web-acls` (exist; WAF attaches to REST API, not HTTP API).
No new skill: the frontend app itself and browser auth SDKs are out of scope.

## Wave 5 - Business

| Topic | Skill | Status |
|---|---|---|
| Stripe inside Quarkus/Lambda (CDI client, secrets, webhook, idempotency) | `integrating-stripe-quarkus-v3-40` (+ stripe-java 34: `developing-stripe-java-core-v34`, `processing-stripe-payments-v34`, `handling-stripe-webhooks-v34`, `managing-stripe-subscriptions-v34`) | exists (+ stripe-java) |
| AI with LangChain4j on Quarkus (OpenAI, Anthropic, Bedrock) | `integrating-quarkus-langchain4j-v1-15` (quarkus-langchain4j 1.15.0.CR1, a **pre-release**: only it targets Quarkus 3.40; latest stable 1.14.2 does not) | exists (quarkus-aws-saas), pre-release-locked |

When the user asks for AI/LLM features: say plainly that the skill exists but is locked to a pre-release (defaults may change before 1.15.0 final), that plain-Java LangChain4j (`developing-langchain4j-core-v1-22`, package `langchain4j`) is a different scope and is not wired into this team, and ask (Ask First, skill D1) whether a pre-release is acceptable. On yes, list the skill in the code work-order; on no, offer to record the requirement as blocked or to research it later. Never write LangChain4j code from memory; RAG, vector stores and MCP stay out of scope.

## Wave 6 - Operation

| Topic | Skill | Status |
|---|---|---|
| Terraform per service | `provisioning-aws-<service>-v6` (e.g. `-lambda-`, `-api-gateway-`, `-cognito-`, `-dynamodb-`, `-s3-`, `-sqs-`, `-iam-`, `-secrets-manager-`, `-kms-`, `-cloudfront-`, `-route53-`, `-acm-`, `-waf-`, `-cloudwatch-`, `-xray-`, `-vpc-`) | exists (aws-terraform) |
| Multi-tenant SaaS, cost | `architecting-aws-saas-multitenant`, `managing-aws-costs`, `optimizing-aws-costs`, `applying-aws-serverless-well-architected-lens` | exists |
| Deploy procedure | `deploying-aws-lambda` | exists |
| Diagnosis | `debugging-aws-lambda` | exists |

## Wave 7 - Observability

| Pillar | Code (integrator) | Infra / validation |
|---|---|---|
| Logs | `logging-quarkus-lambda-v3-40` | `provisioning-aws-cloudwatch-v6`, `monitoring-cloudwatch-observability` |
| Traces | `tracing-quarkus-lambda-v3-40`, `tracing-aws-xray` | `provisioning-aws-xray-v6` |
| Metrics | `monitoring-quarkus-lambda-v3-40`, `implementing-lambda-powertools-java` (locked to Powertools 2.10.0: outside this family's scope) | `provisioning-aws-cloudwatch-v6` |
| Umbrella (3 pillars in code) | `observing-quarkus-lambda` | exists |
| Live validation (5 pillars, read-only) | n/a | `validating-aws-observability` (scripts `check-logs/metrics/traces/alarms/dashboards`), command `observe-aws-workload`: both exist |
| Dashboards / SLOs / Application Signals | coverage not confirmed: declare the gap in E2 if no skill covers it | `aws-observability` agent: exists (Modes A/B/C, see [worker briefs](worker-briefs.md#aws-observability)) |

## Selection rule

List in a work-order **only** the skills the task needs (one per need); an agent treats an unlisted skill as a question. Loading everything costs context and violates the agents' own rules.

## Out of scope (say so, do not improvise)

Quarkus 4, SAM and CDK, Amplify, browser auth SDKs, Camel on Lambda, ECS/Fargate, RAG and vector stores, MCP and agent frameworks.
