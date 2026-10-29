# Package brief — quarkus-aws-saas

Approved plan: `C:\Users\r.dos.santos.mendes\.claude\plans\quero-poder-programar-aws-transient-karp.md` (2026-10-28).
This build produces several APM packages; `quarkus-aws-saas` is the slug of the run and of the composition package.

```yaml
slug: quarkus-aws-saas
language: en                        # artifact language (plan discussed in pt-BR)
frameworks:
  - Quarkus 3.40                    # LTS line, same as existing developing-quarkus-*-v3-40
  - Quarkiverse quarkus-amazon-services <version compatible with Quarkus 3.40>   # P1
  - Quarkiverse quarkus-langchain4j <version compatible with Quarkus 3.40>       # P1
  - OpenSpec <current stable>                                                    # P1 (maturity/licence gate)
  - stripe-java 34.x                # existing skills, reused
needs:
  - write AWS Lambdas with Quarkus (JVM, native, SnapStart) behind API Gateway
  - Cognito authN/authZ in Quarkus, multi-tenant
  - DynamoDB, S3, SQS, SNS, EventBridge, SSM/Secrets Manager from Quarkus
  - test Quarkus Lambdas offline
  - Stripe payments inside Quarkus on Lambda
  - LangChain4j on Quarkus with OpenAI, Anthropic and Amazon Bedrock
  - observability (logs, metrics, X-Ray traces, alarms, dashboards) in code and infra, with live validation
  - deploy and debug Lambdas (runtime-agnostic)
  - continuous, bidirectional SDD (OpenSpec) with generic handoff + spec sync
  - clean code / refactoring for Quarkus
  - frontend delivery: map existing CDN skills (no new research)
legacy_source: packages/oci-core/.apm/skills/coordinating-oci-handoffs (generic part extracted); packages/camel-quarkus-skills (3 Quarkus skills moved to quarkus-core)
deliverables: [skills, agent, rules, readme, structure-skill, orchestrator-skill]
agent_kind: executor
packages: [quarkus-core, quarkus-aws, aws-lambda, aws-observability, handoff-core, quarkus-aws-saas]
modified_packages: [camel-quarkus-skills, camel-quarkus-integrator (links only), oci-core, stripe-java (1 line, G1)]
out_of_scope: [Quarkus 4, SAM, CDK, Amplify, browser auth SDK, Camel on Lambda, ECS, RAG/vector stores]
research_worker: researching-technical-frameworks
rounds: 3
```
