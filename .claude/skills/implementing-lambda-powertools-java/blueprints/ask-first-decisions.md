# Ask-First Decisions — Lambda Powertools for Java v2.10.0

Four decision matrices from SKILL.md. Confirm with the user before generating code.
Source research: `workspace/docs/research_cloud_AWS_LambdaPowertools_Java_2026.md`. Official sources accessed 2026-09-01.

---

## D1 — Annotation API (AspectJ CTW) vs Functional API

Ask: "Does the runtime use GraalVM native image, Kotlin, or heavy Lombok? Or is it a standard Maven/Gradle Java 11+ project?"

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `@Logging` / `@Tracing` / `@FlushMetrics` (AspectJ compile-time weaving) | Ergonomics, declarative config | Build complexity; incompatible with GraalVM native, Kotlin/Lombok toolchains | Standard Java 11+ project, no GraalVM |
| Functional API (v2.7.0+, no AspectJ) | GraalVM native compatibility, simpler build, Kotlin/Lombok support | Slightly more verbose handler code | GraalVM, Kotlin, Lombok, constrained CI |

- No runtime cost difference; AspectJ weaving adds build time.
- Both APIs are Powertools-specific; the functional API is easier to wrap in an abstraction layer.
- AspectJ plugin must be `dev.aspectj:aspectj-maven-plugin:1.14` (not `org.codehaus.mojo`). `aspectjrt` by JDK: 11-17 -> 1.9.20.1+, 21 -> 1.9.21+, 25 -> 1.9.25+.

Source: [Powertools for Java](https://docs.aws.amazon.com/powertools/java/latest/) (2026-09-01)

---

## D2 — Log4j2 backend vs Logback backend

Ask: "Does the project already depend on Log4j2 or Logback?" Never add both (class-loading conflicts).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `powertools-logging-log4j` (JsonTemplateLayout) | Performance, ECS layout support, mature ecosystem | Larger footprint | Already on Log4j2, or ECS compatibility needed |
| `powertools-logging-logback` (LambdaJsonEncoder) | Familiarity for Spring-lineage teams, smaller footprint | Slightly less template flexibility | Already on Logback / Spring Boot conventions |

- Cost is negligible and identical (both free; same CloudWatch Logs cost).
- Switching changes only the Maven/Gradle dependency and `log4j2.xml` / `logback.xml`; no business-logic change.

Source: [Powertools Logging](https://docs.aws.amazon.com/powertools/java/2.8.0/core/logging/) (2026-09-01)

---

## D3 — SSM Parameter Store vs Secrets Manager for credentials

Ask: "Does the credential require automated rotation?" Yes -> Secrets Manager.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| SSM Parameter Store SecureString (`powertools-parameters-ssm`) | Cost (free standard tier, up to 10,000 params), hierarchical paths, `GetParametersByPath` | Not designed for rotation; no native cross-account support | Config and non-rotated credentials, cost-sensitive |
| Secrets Manager (`powertools-parameters-secrets`) | Automatic rotation, cross-account support, audit trail | $0.40/secret/month + $0.05 per 10K API calls | DB credentials, API keys needing rotation |

- Both are AWS-proprietary; Powertools abstracts the API but ARN/path naming is AWS-specific.
- TTL guidance from SKILL.md: credentials 5-30 s, config 30-60 s.

Source: [Powertools Parameters](https://docs.aws.amazon.com/powertools/java/latest/utilities/parameters/) (2026-09-01)

---

## D4 — Idempotency table: On-Demand vs Provisioned

Ask: "What is the expected peak requests-per-second of the mutating endpoint?"

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| PAY_PER_REQUEST (On-Demand) | Simplicity, no capacity planning, absorbs spikes | Higher per-request cost at sustained high throughput | Variable or unpredictable traffic |
| Provisioned + Auto Scaling | Lower cost at sustained high throughput | Capacity planning; throttling risk on spikes | High, predictable throughput |

- Cost: 2 WCU on the first call; 1 WCU + 1 RCU on an idempotent retry. Max stored response 400 KB (DynamoDB item limit).
- DynamoDB is the only persistence layer documented in the research for v2 idempotency. Redis support: (unverified).
- Confidence in this decision in the research file is Medium (single source).

Source: [Powertools Idempotency](https://docs.aws.amazon.com/powertools/java/latest/utilities/idempotency/) (2026-09-01)
