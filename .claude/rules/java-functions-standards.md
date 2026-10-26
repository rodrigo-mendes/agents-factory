---
name: java-functions-standards
description: "Java 17 coding standards for OCI Functions: naming, security, style, and production-readiness. Use when writing or reviewing any Java source file in a functions project."

---
You are an OCI Functions Java Code Quality specialist.
Ensure all Java function code follows FDK v1.1.x + Java 17 best practices for production-ready serverless applications.

## Skill References

For implementation patterns and code examples, load the relevant skill:
- **Base development**: `.claude/skills/developing-oci-functions-java/SKILL.md`
- **Event-driven handlers**: `.claude/skills/implementing-oci-functions-events/SKILL.md`
- **Testing patterns**: `.claude/skills/testing-oci-functions-java/SKILL.md`
- **SDK integration**: `.claude/skills/invoking-rest-apis-from-oci-functions/SKILL.md`

Skills contain comprehensive code examples in their `blueprints/` subdirectories — always prefer skill patterns over ad-hoc implementation.

## Version Constraints
- FDK: v1.1.x (with fn-events module)
- Java: 17
- OCI SDK: v3.86+ (use BOM `oci-java-sdk-bom`)
- ALWAYS pin versions in pom.xml — no LATEST or SNAPSHOT dependencies

## Naming Conventions
- Classes: PascalCase with descriptive purpose suffix (e.g., `OrderProcessorFunction`, `FileUploadHandler`)
- Handler methods: camelCase — use `handler` for fn-events abstract classes, `handleRequest` for direct POJO handlers
- Base package: `com.brx.functions.<domain>` (e.g., `com.brx.functions.orders`, `com.brx.functions.payments`)
- Constants: `UPPER_SNAKE_CASE` for `static final` fields
- Configuration keys and OCID naming: see `java-functions-project-structure.md` → **Configuration Key Naming**
- Package and directory layout: see `java-functions-project-structure.md` → **Project Structure**

## Code Structure Standards
- Handler class: one public handler method per class
- Separate handler from core logic — extract business logic to `service/` for testability
- Field declarations: cached clients and utilities at top of class
- `@FnConfiguration` method: immediately after field declarations
- Handler method: after `@FnConfiguration`
- Private helper methods: after handler method
- Import ordering: `com.fnproject` → `com.oracle.bmc` → `java.*` → `javax.*`
- For SOLID, Extract Method, and readability/decomposition, see the rule `java-functions-clean-code.md`; to refactor existing code with a step-by-step recipe and examples, load the skill `refactoring-oci-java`.

## Security Standards (Internal Compliance)

### Authentication
- Use `ResourcePrincipalAuthenticationDetailsProvider` — the ONLY auth method in OCI Functions
- NEVER use `ConfigFileAuthenticationDetailsProvider`, `SimpleAuthenticationDetailsProvider`, or `InstancePrincipalsAuthenticationDetailsProvider`

### Secret Management
- Store ALL secrets in OCI Vault — reference by OCID in func.yaml config
- Retrieve secrets during `@FnConfiguration` cold start — cache in instance fields
- NEVER hardcode credentials in source code, func.yaml config values, or Dockerfile

### Input Validation
- Validate ALL external inputs before processing (API Gateway, events, direct invocation)
- Use `@JsonIgnoreProperties(ignoreUnknown = true)` on ALL input POJOs for forward compatibility
- Enforce field length limits, range checks, and null guards
- Sanitize string inputs to prevent injection attacks

### Logging Security
- NEVER log secrets, tokens, passwords, API keys, or PII
- Log `opc-request-id` from BmcException for OCI support correlation
- Use structured JSON logging for OCI Logging ingestion

## ✅ Always Do
1. Use Resource Principal for ALL OCI SDK authentication — no exceptions
2. Initialize SDK clients in `@FnConfiguration` — never per invocation
3. Set SDK read timeout (15s) LOWER than function timeout (30-60s)
4. Close ALL InputStreams from Object Storage with `try-with-resources`
5. Store secrets in OCI Vault — reference by OCID, never hardcode
6. Validate ALL inputs from API Gateway before processing
7. Use structured JSON logging for production observability
8. Pin FDK and SDK versions in `pom.xml` — no LATEST or SNAPSHOT
9. Configure `RetryConfiguration` with exponential backoff + jitter
10. Handle `BmcException` — classify retryable (429, 5xx) vs. fatal (400, 404)
11. Set `func.yaml` timeout to accommodate all downstream calls + retries
12. Cache reusable objects (ObjectMapper, HttpClient, SDK clients) across invocations
13. Use `@JsonIgnoreProperties(ignoreUnknown = true)` on all input POJOs
14. Implement idempotency for event-driven functions
15. Check per-message errors in Streaming PutMessages responses
16. Use `telemetry-ingestion` endpoint for Monitoring (NOT `telemetry`)
17. Use `::handler` entry point (not `::handleRequest`) for fn-events abstract classes

## 🚫 Never Do
1. Use API keys or config-file auth in Functions — security breach risk
2. Initialize SDK clients in the handler method — eliminates hot function benefit
3. Set SDK timeout higher than function timeout — platform kills mid-request, no error handling
4. Leave InputStreams from GetObject unclosed — connection pool exhaustion → OOM
5. Buffer large files entirely into `byte[]` — OutOfMemoryError risk
6. Hardcode credentials anywhere — data breach, compliance violation
7. Use `Thread.sleep()` for retry delays — wastes execution time and cost
8. Ignore `BmcException` status code classification — retrying fatal errors wastes budget
9. Use mutable shared state without synchronization — data corruption in hot functions
10. Create functions exceeding 300s timeout — decompose into async event-driven chain
11. Skip input validation — injection attacks, data corruption
12. Use `::handleRequest` with fn-events abstract classes — silent routing failure
13. Publish messages without checking per-message errors — silent data loss
14. Use `telemetry` endpoint for Monitoring PostMetricData — will fail silently
