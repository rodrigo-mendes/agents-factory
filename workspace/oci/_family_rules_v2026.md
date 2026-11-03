# OCI Family Rules — v2026

Shared policies for OCI agent packages. Derived from the `oci-functions-java` package
instructions (17 rule files) and the 6 architecture skills of `oci-architecture`. Cite sources;
`unverified` = no recorded source URL. Rule IDs (`OCI-Rnn`) are stable: never renumber, only append.

ID ranges: `OCI-R01`–`OCI-R33` = functions/Java rules; `OCI-R34`–`OCI-R115` = architecture rules.

---

## Three-Tier Rules (✅ Always / ⚠️ Ask-First / 🚫 Never)

### Cold-Start Initialization

| ID | Tier | Rule | Rationale |
|----|------|------|-----------|
| OCI-R01 | ✅ | Wrap ALL `configure()` body in `try/catch`; store exception in `initError` field | Without it, any init exception crashes the container (502) with no diagnostic info |
| OCI-R02 | ✅ | Check `initError != null` at the top of every handler before processing | Returns 500 with details instead of a silent crash on the next warm invocation |
| OCI-R03 | ✅ | Cache SDK clients (`StreamClient`, `ObjectStorageClient`, etc.) in instance fields during `configure()` | Prevents re-initialization on every invocation (hot function model) |
| OCI-R04 | 🚫 | Initialize SDK clients inside the handler method | Creates a new client per invocation → latency + OOM risk |
| OCI-R05 | 🚫 | Let `configure()` throw any exception uncaught | Container crash → 502 with no logs on cold start |

### Dockerfile & Deployment

| ID | Tier | Rule | Rationale |
|----|------|------|-----------|
| OCI-R06 | ✅ | Always include `CMD ["<package>.<Class>::<method>"]` in Dockerfile | Missing CMD → container immediately exits → HTTP 502 with zero logs |
| OCI-R07 | ✅ | Ensure `cmd:` in `func.yaml` matches `CMD` in Dockerfile exactly | Mismatch causes initialization failure |
| OCI-R08 | ✅ | Add `oci-java-sdk-common-httpclient-jersey` to `pom.xml` when ANY OCI SDK module is used | Missing causes "No http provider available" crash at runtime, not at compile time |
| OCI-R09 | 🚫 | Hardcode OCI credentials or tokens in `func.yaml` config values | Security violation; use Vault OCID references instead |
| OCI-R10 | 🚫 | Reuse a Docker image tag (version bump is mandatory per deploy) | OCIR may cache the old layer; Terraform detects no change |

### SDK Timeout Budget

| ID | Tier | Rule | Rationale |
|----|------|------|-----------|
| OCI-R11 | ✅ | Set SDK `connectionTimeoutMillis` ≤ 5,000 ms | Cold start already consumes ~15s; fast-fail prevents platform kill |
| OCI-R12 | ✅ | Set SDK `readTimeoutMillis` ≤ 30,000 ms (stay below function timeout) | SDK default 60,000 ms == function timeout = invocation killed with no cleanup |
| OCI-R13 | ⚠️ | Increase `timeout_in_seconds` in func.yaml for compute-heavy functions | Ask: is the timeout increase feasible? Does it affect cost? Max is 300s. |
| OCI-R14 | 🚫 | Use SDK default timeouts when function timeout is ≤ 60s | SDK default (60s) equals the function timeout; can cause mid-PutMessages kills |

### Object Storage

| ID | Tier | Rule | Rationale |
|----|------|------|-----------|
| OCI-R15 | ✅ | Always close `GetObjectResponse.getInputStream()` in a `finally` block | Unclosed streams leak connections and cause OOM over repeated invocations |
| OCI-R16 | ✅ | Fetch the Object Storage namespace once in `configure()`, not per request | Namespace call is an API call; unnecessary per-invocation cost |
| OCI-R17 | 🚫 | Buffer entire object into memory with `byte[]` or `String` for large objects | OOM risk when object > function memory limit; use streaming read |

### Streaming (OCI)

| ID | Tier | Rule | Rationale |
|----|------|------|-----------|
| OCI-R18 | ✅ | Always inspect `PutMessagesResultEntry.getError()` after `putMessages()` | HTTP 200 from the API does NOT mean all messages were delivered |
| OCI-R19 | ✅ | Use `event_type` as the Streaming message key | Ensures ordering within an event type and enables partitioned consumption |
| OCI-R20 | 🚫 | Manually Base64-encode message values before passing to SDK | The SDK handles Base64 wire encoding; double-encoding corrupts the payload |
| OCI-R21 | 🚫 | Assume HTTP 200 from PutMessages guarantees delivery | Per-message error entries must be inspected individually |

### Security

| ID | Tier | Rule | Rationale |
|----|------|------|-----------|
| OCI-R22 | ✅ | Use `ResourcePrincipalAuthenticationDetailsProvider` in deployed functions | Provides short-lived credentials; no secret rotation required |
| OCI-R23 | ✅ | Reference Vault secrets by OCID in func.yaml / app config; decode in code | Secrets never appear in plaintext config |
| OCI-R24 | 🚫 | Use API key auth in deployed functions | API keys require rotation and cannot be automatically scoped |
| OCI-R25 | 🚫 | Log secret values or credentials | Visible in OCI Logging; security violation |

### Testing

| ID | Tier | Rule | Rationale |
|----|------|------|-----------|
| OCI-R26 | ✅ | Use `FnTestingRule` (JUnit 4) or `FnTestingRuleJUnit5` for handler tests | Simulates the FDK runtime lifecycle; constructor and configure() are both called |
| OCI-R27 | ✅ | Provide a package-private constructor for test injection of mocks | Avoids ResourcePrincipal calls in unit tests |
| OCI-R28 | ⚠️ | Use Mockito for SDK client mocks vs. in-memory fakes | Ask: does the test require behavioral verification or just stub responses? |
| OCI-R29 | 🚫 | Call real OCI services in unit tests | Creates test environment coupling and secrets exposure |

### Code Structure

| ID | Tier | Rule | Rationale |
|----|------|------|-----------|
| OCI-R30 | ✅ | Keep handler class < 200 lines; extract to sub-packages by responsibility | God classes become unmaintainable; see `refactoring-oci-java` skill |
| OCI-R31 | ✅ | Call `MDC.clear()` in the handler's `finally` block | Prevents MDC context leakage between warm invocations |
| OCI-R32 | ✅ | Return structured JSON error responses with `status`, `erro`, `detalhe`, `elapsed_ms` fields | Enables `oci-debugger` to auto-match known patterns without log access |
| OCI-R33 | 🚫 | Mix business logic, SDK calls, and HTTP response building in the handler method | Single Responsibility; extract to service/client/factory layers |

---

## Architecture Rules

Derived ONLY from the Always Do / Never Do / Ask First rows of the 6 skills in
`packages/oci-architecture/.apm/skills/`. No facts beyond those skills. Where several skills state
the same rule, it is one row listing every source skill. No `(unverified)` or
`(medium confidence)` tags are present in the 6 skills at the time of writing; if a skill adds one,
carry it onto the row.

Skills: `architecting-oci-serverless`, `designing-oci-api-gateway`, `designing-oci-networking`,
`designing-oci-object-storage`, `designing-oci-vault-security`, `designing-oci-event-driven-pubsub`.

### Architecture — Always Do

| ID | Tier | Rule | Source skill |
|----|------|------|--------------|
| OCI-R34 | ✅ | All client traffic enters through API Gateway (`ORACLE_FUNCTIONS_BACKEND` routes to function OCIDs; `/health` as `STOCK_RESPONSE_BACKEND` + ANONYMOUS); function invoke endpoints are never exposed | architecting-oci-serverless, designing-oci-api-gateway |
| OCI-R35 | ✅ | Functions Application in a private subnet (`prohibit_public_ip_on_vnic = true`) with NSGs; API Gateway in a separate public subnet; backend tiers private, internet-facing tiers public | architecting-oci-serverless, designing-oci-networking |
| OCI-R36 | ✅ | Functions authenticate via Dynamic Group + IAM policies with Resource Principal; no credentials in code, env vars, or function config | architecting-oci-serverless |
| OCI-R37 | ✅ | Segregate compartments (e.g. Network, Security, Serverless-Dev/Staging/Prod) to limit blast radius | architecting-oci-serverless |
| OCI-R38 | ✅ | Set explicit `memory_in_mbs` and `timeout_in_seconds` (never leave the 300s default) and pin the image (`image_digest`, full OCIR path) | architecting-oci-serverless |
| OCI-R39 | ✅ | TLS 1.2+ in transit (do not disable gateway TLS); custom domains use OCI Certificates Service with auto-renewal; mTLS for B2B/financial APIs | architecting-oci-serverless, designing-oci-api-gateway |
| OCI-R40 | ✅ | Enable tracing on the Functions Application (`trace_config.is_enabled = true`, APM domain OCID) and access + execution logs on every API Gateway deployment; configure alarms (function errors, gateway 5xx, duration vs timeout) | architecting-oci-serverless, designing-oci-api-gateway |
| OCI-R41 | ✅ | Tag all serverless resources (`Environment`, `Project`, `Team`, `CostCenter`, `ManagedBy`); defined tags (e.g. DataClassification, CostCenter) on buckets | architecting-oci-serverless, designing-oci-object-storage |
| OCI-R42 | ✅ | Three IAM configurations for gateway→function invocation: Dynamic Group (`ApiGateway`, PascalCase) + `use fn-invocation`; `Allow service FaaS to use virtual-network-family`; `Allow service FaaS to read repos in tenancy` | designing-oci-api-gateway, architecting-oci-serverless |
| OCI-R43 | ✅ | Restrictive NSGs: gateway NSG ingress TCP 443 only; functions NSG ingress only from gateway subnet/NSG; functions egress TCP 443 to Service CIDR (+ NAT only if external APIs are needed) | designing-oci-api-gateway, designing-oci-networking, architecting-oci-serverless |
| OCI-R44 | ✅ | CORS with explicit origins, methods, headers; `is_allow_credentials_enabled = true` only with explicit origins | designing-oci-api-gateway |
| OCI-R45 | ✅ | Every VCN with private subnets has a Service Gateway (route `Service CIDR → Service Gateway`) for OCI service access | designing-oci-networking, designing-oci-object-storage |
| OCI-R46 | ✅ | Use NSGs (not Security Lists) as the primary micro-segmentation mechanism, one rule resource per rule | designing-oci-networking |
| OCI-R47 | ✅ | Private subnets that need internet egress use a NAT Gateway, never an Internet Gateway | designing-oci-networking |
| OCI-R48 | ✅ | Enable VCN Flow Logs on subnets with sensitive traffic | designing-oci-networking |
| OCI-R49 | ✅ | Customer-managed keys (CMEK, `kms_key_id`; AES-256, auto-rotation, HSM for production) for data at rest, mandatory for regulated data | designing-oci-vault-security, designing-oci-object-storage |
| OCI-R50 | ✅ | Retrieve secrets from OCI Vault at runtime via Resource Principal; function config holds only non-sensitive values (OCIDs, bucket names, URLs) | designing-oci-vault-security, architecting-oci-serverless |
| OCI-R51 | ✅ | Configure automated secret rotation (`rotation_config`) and `SECRET_EXPIRY_RULE` on production secrets | designing-oci-vault-security |
| OCI-R52 | ✅ | Least-privilege Vault IAM: admins `manage`; workload dynamic groups only `use keys` and `read secret-bundles`, never `manage` | designing-oci-vault-security |
| OCI-R53 | ✅ | Separate keys per purpose (storage, secrets, signing) with distinct rotation intervals | designing-oci-vault-security |
| OCI-R54 | ✅ | Cache secrets in function memory with TTL-based invalidation instead of fetching per invocation | designing-oci-vault-security |
| OCI-R55 | ✅ | Declare `access_type = "NoPublicAccess"` explicitly on every bucket | designing-oci-object-storage |
| OCI-R56 | ✅ | Add a lifecycle policy with an ABORT rule for incomplete multipart uploads (and DELETE on previous versions for versioned buckets) | designing-oci-object-storage |
| OCI-R57 | ✅ | Use `object_events_enabled = true` + OCI Events for processing pipelines; design consumers for at-least-once delivery | designing-oci-object-storage |
| OCI-R58 | ✅ | Use a PUBLIC stream pool (no `private_endpoint_settings`) whenever Service Connector Hub is the stream source | designing-oci-event-driven-pubsub |
| OCI-R59 | ✅ | Publish a standard message envelope (`event_id`, `event_type`, `payload`; recommended `correlation_id`, `timestamp`) | designing-oci-event-driven-pubsub |
| OCI-R60 | ✅ | Use `event_type` as the partition key for ordering within an event type | designing-oci-event-driven-pubsub |
| OCI-R61 | ✅ | Make consumers idempotent (dedupe by `event_id`; SCH delivery is at-least-once) | designing-oci-event-driven-pubsub |
| OCI-R62 | ✅ | One Service Connector per consumer (a connector has exactly one target; each keeps its own cursor) | designing-oci-event-driven-pubsub |
| OCI-R63 | ✅ | SCH-target functions: `timeout = 300` and `memory >= 1024` MB (not applicable to API-Gateway-invoked producers) | designing-oci-event-driven-pubsub |
| OCI-R64 | ✅ | Monitor `ErrorsAtSource` and `ErrorsAtTarget` separately; both must be 0 for a healthy fan-out | designing-oci-event-driven-pubsub |

### Architecture — Never Do

| ID | Tier | Rule | Source skill |
|----|------|------|--------------|
| OCI-R65 | 🚫 | Hardcode credentials in application code or function config (use Vault + Resource Principal; store only OCIDs) | architecting-oci-serverless, designing-oci-vault-security |
| OCI-R66 | 🚫 | Place Functions in a public subnet | architecting-oci-serverless |
| OCI-R67 | 🚫 | Wildcard IAM policies (`manage all-resources`, `manage keys in tenancy`, `manage object-family in tenancy`) for functions, dynamic groups, or developers | architecting-oci-serverless, designing-oci-vault-security, designing-oci-object-storage |
| OCI-R68 | 🚫 | Leave function timeout unconfigured (runs up to the 300s platform maximum) | architecting-oci-serverless |
| OCI-R69 | 🚫 | Deploy an API Gateway deployment without `rate_limiting` (`rate_key = CLIENT_IP` is the minimum baseline) | architecting-oci-serverless, designing-oci-api-gateway |
| OCI-R70 | 🚫 | Disable logging or tracing in production | architecting-oci-serverless, designing-oci-api-gateway |
| OCI-R71 | 🚫 | Put all resources in a single compartment | architecting-oci-serverless |
| OCI-R72 | 🚫 | Design SCH → Function targets without cold-start-ceiling awareness (JVM pre-main gap ~55-62 s vs SCH sync deadline ~30-60 s); mitigations: timeout 300s + memory 1024 MB, provisioned concurrency (multiples of 10), GraalVM native image, async decouple | architecting-oci-serverless, designing-oci-event-driven-pubsub |
| OCI-R73 | 🚫 | Expose Functions without an API Gateway in front | designing-oci-api-gateway |
| OCI-R74 | 🚫 | Wildcard CORS origins (`*`) combined with `is_allow_credentials_enabled = true` | designing-oci-api-gateway |
| OCI-R75 | 🚫 | Single monolithic deployment with all routes (flag deployments with more than 20 routes; one deployment per bounded context) | designing-oci-api-gateway |
| OCI-R76 | 🚫 | Hardcoded backend IPs in `HTTP_BACKEND` routes (use `ORACLE_FUNCTIONS_BACKEND` or DNS-based discovery) | designing-oci-api-gateway |
| OCI-R77 | 🚫 | Security List with `0.0.0.0/0` ingress on all ports/protocols | designing-oci-networking |
| OCI-R78 | 🚫 | Route a private subnet to an Internet Gateway | designing-oci-networking |
| OCI-R79 | 🚫 | Omit the Service Gateway (OCI service traffic would traverse NAT/internet) | designing-oci-networking |
| OCI-R80 | 🚫 | NSG with unrestricted egress (all protocols to `0.0.0.0/0`) | designing-oci-networking |
| OCI-R81 | 🚫 | VCN with insufficient or overlapping CIDR blocks (`/16` for production; verify non-overlap with on-premises and other VCNs) | designing-oci-networking |
| OCI-R82 | 🚫 | Pre-Authenticated Requests with excessive scope or far-future expiry (minimum scope: single object, read-only, short expiry; retain `par_id`) | designing-oci-object-storage |
| OCI-R83 | 🚫 | Versioned bucket without a lifecycle rule on previous object versions | designing-oci-object-storage |
| OCI-R84 | 🚫 | Use Object Storage as session state or a message queue (use OCI Cache / Queue / Streaming / Vault as appropriate) | designing-oci-object-storage |
| OCI-R85 | 🚫 | Public bucket (`access_type = "ObjectRead"`) for non-public data (private bucket + CDN origin for public delivery) | designing-oci-object-storage |
| OCI-R86 | 🚫 | Oracle-managed (default) keys for regulated data | designing-oci-vault-security |
| OCI-R87 | 🚫 | A single encryption key for all purposes | designing-oci-vault-security |
| OCI-R88 | 🚫 | Secrets without expiration or rotation configured | designing-oci-vault-security |
| OCI-R89 | 🚫 | Private-endpoint-only stream pool with SCH as source (SCH runs outside the VCN; `private_endpoint_settings` is immutable, replace the pool) | designing-oci-event-driven-pubsub |
| OCI-R90 | 🚫 | One SCH connector routed to multiple functions (one target per connector) | designing-oci-event-driven-pubsub |
| OCI-R91 | 🚫 | Rely on HTTP headers for trace propagation across the stream boundary (embed trace context in the message envelope) | designing-oci-event-driven-pubsub |
| OCI-R92 | 🚫 | Grant only `fn-invocation` to SCH for a Functions target (both `use fn-function` and `use fn-invocation` are required) | designing-oci-event-driven-pubsub |

### Architecture — Ask First

Each row is a decision the request must settle before the design is final. Options and trade-offs
live in the source skill's Ask First blueprint.

| ID | Tier | Rule (decision to settle) | Source skill |
|----|------|---------------------------|--------------|
| OCI-R93 | ⚠️ | Compute shape: GENERIC_X86 vs GENERIC_ARM vs GENERIC_X86_ARM (native x86-only libraries?) | architecting-oci-serverless |
| OCI-R94 | ⚠️ | Cold-start mitigation: on-demand vs provisioned concurrency vs scheduled warm-up (P99 latency SLA?) | architecting-oci-serverless |
| OCI-R95 | ⚠️ | Invocation pattern: synchronous vs detached (does the operation fit the gateway timeout?) | architecting-oci-serverless |
| OCI-R96 | ⚠️ | Authentication: JWT vs custom authorizer vs token introspection vs mTLS vs usage plan vs anonymous (identity provider and token format?) | designing-oci-api-gateway, architecting-oci-serverless |
| OCI-R97 | ⚠️ | API Gateway endpoint type: PUBLIC vs PRIVATE (external or internal consumers?) | designing-oci-api-gateway, architecting-oci-serverless |
| OCI-R98 | ⚠️ | Function subnet egress: private + NAT Gateway vs private + Service Gateway only (external third-party APIs needed?) | architecting-oci-serverless |
| OCI-R99 | ⚠️ | Rate-limiting strategy: CLIENT_IP vs usage plans + API keys vs custom authorizer per tenant | designing-oci-api-gateway |
| OCI-R100 | ⚠️ | Network security model: NSGs only vs Security Lists + NSGs vs Network Firewall vs WAF (L7 inspection or compliance need?) | designing-oci-networking |
| OCI-R101 | ⚠️ | VCN topology: single VCN vs hub-spoke (DRG v2) vs mesh vs hub-spoke + Network Firewall | designing-oci-networking |
| OCI-R102 | ⚠️ | On-premises connectivity: FastConnect vs Site-to-Site VPN vs both (traffic volume, latency) | designing-oci-networking |
| OCI-R103 | ⚠️ | Load balancing: API Gateway vs Flexible LB vs Network LB vs API Gateway + LB | designing-oci-networking |
| OCI-R104 | ⚠️ | Storage tier strategy (immutable after bucket creation): Standard, auto-tiering, lifecycle → IA/Archive, Archive | designing-oci-object-storage |
| OCI-R105 | ⚠️ | Data protection: versioning vs retention rules (WORM; locked rules cannot be shortened) vs cross-region replication vs combined | designing-oci-object-storage |
| OCI-R106 | ⚠️ | Access pattern: dynamic group/instance principal vs user policy vs PAR vs CDN over private bucket vs public bucket (who needs access?) | designing-oci-object-storage |
| OCI-R107 | ⚠️ | Vault type: Default vs Virtual Private vs dedicated KMS vs external KMS (compliance, key count, cross-region replication?) | designing-oci-vault-security |
| OCI-R108 | ⚠️ | Key protection mode (IMMUTABLE after creation): HSM vs software vs external | designing-oci-vault-security |
| OCI-R109 | ⚠️ | Secret storage: Vault secrets vs function config variables (would exposure cause a security incident?) | designing-oci-vault-security |
| OCI-R110 | ⚠️ | Key algorithm: AES-256 default; ask only for signing or key wrapping (RSA, ECDSA P-256/P-384) | designing-oci-vault-security |
| OCI-R111 | ⚠️ | Consumer variant: REST (02a) vs database (02b) vs event chain (02c) vs custom | designing-oci-event-driven-pubsub |
| OCI-R112 | ⚠️ | Stream pool type (immutable): PUBLIC vs PRIVATE (is SCH the only reader or do in-VCN Kafka clients also read?) | designing-oci-event-driven-pubsub |
| OCI-R113 | ⚠️ | SCH cold-start mitigation: timeout 300s + memory 1024 MB vs provisioned concurrency vs GraalVM native vs async decouple | designing-oci-event-driven-pubsub |
| OCI-R114 | ⚠️ | SCH cursor strategy: `LATEST` vs `TRIM_HORIZON` (replay on reactivation requires full idempotency) | designing-oci-event-driven-pubsub |
| OCI-R115 | ⚠️ | Fan-out topology: N SCH connectors vs stream hub vs in-VCN Kafka consumer group | designing-oci-event-driven-pubsub |

---

## Skill Routing Policy

When a request triggers multiple skill domains, load skills in this order:

1. `developing-oci-functions-java` (base — always first)
2. Domain-specific skill (`integrating-oci-functions-objectstorage`, `publishing-events-from-oci-functions`, etc.)
3. `refactoring-oci-java` only when explicitly requested

Never skip the base skill — it carries the initError, CMD, and httpclient-jersey patterns that
prevent the most common deployment failures.

---

## Version Policy

| Policy | Value |
|--------|-------|
| FDK version lock | FDK v1.1.x — do NOT mix with Fn 2.x or GraalVM native patterns |
| SDK version | Always read from existing `services/*/pom.xml`; never hardcode |
| Java version | Java 17 (Amazon Corretto) on OCI Functions; Java 11 is the minimum supported |
| Base images | Use `fnproject/fn-java-fdk-build:jdk17-latest` and `fnproject/fn-java-fdk:jre17-latest` |

---

## Handoff Protocol

All agents write a report to `docs/handoff/<capability>/` before handing off:
- `oci-functions-java` writes `report-java.md`
- `oci-deployer` writes `deploy-report.md`
- `oci-debugger` writes `diagnosis-report.md`
- `oci-serverless-architect` writes work-orders (`stream-a-java.md`, `stream-b-terraform-infra.md`, `stream-c-terraform-integration.md`) and nothing else

Handoff direction:
- Java code complete → `oci-deployer` (if infra exists) or `@oci-terraform` (if infra missing)
- Deploy failure → `oci-debugger` (if auto-fix failed)
- Debug finding → `oci-deployer` (code/config fix) or `@oci-terraform` (infra fix)
- Architecture design approved → `/provision-oci-infra` (infra work-orders) and `/develop-java-function` (Java work-order)

---

## Rules Provenance

- Source (OCI-R01–R33): `packages/oci-functions-java/.apm/instructions/*.instructions.md` (17 rule files)
- Source (OCI-R34–R115): Always Do / Never Do / Ask First blueprints and SKILL.md of the 6 skills in
  `packages/oci-architecture/.apm/skills/` (architecting-oci-serverless, designing-oci-api-gateway,
  designing-oci-networking, designing-oci-object-storage, designing-oci-vault-security,
  designing-oci-event-driven-pubsub). Cross-skill duplicates merged into one row with all sources listed.
- Counts: 33 functions rules + 82 architecture rules (31 Always, 28 Never, 23 Ask First)
- PoC evidence: `workspace/poc-oci-serverless/` (read-only reference)
- Last updated: 2026-10-26
