# OCI Family Facts — v2026

Shared domain facts for OCI-platform agent packages. Derived from the `oci-functions-java`
package (FDK v1.1.x, OCI Java SDK v3.86.x, observed in `workspace/poc-oci-serverless`).
Facts marked `unverified` have no recorded source URL — validate before citing.

---

## Runtime Platform

| Fact | Value | Source |
|------|-------|--------|
| FDK Java target version | v1.0.186 (baseline) / v1.1.x (latest) | https://github.com/fnproject/fdk-java/releases (2024-Q4) |
| Java runtime | Java 17 (Amazon Corretto), Java 11 minimum | https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsfdksupportedruntimes.htm |
| Docker build image | `fnproject/fn-java-fdk-build:jdk17-latest` | https://hub.docker.com/r/fnproject/fn-java-fdk-build |
| Docker run image | `fnproject/fn-java-fdk:jre17-latest` | https://hub.docker.com/r/fnproject/fn-java-fdk |
| Function max timeout | 300 seconds | https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingfunctions.htm |
| Default timeout (func.yaml) | 60 seconds | Observed in `services/*/func.yaml` (poc-oci-serverless) |
| Cold start budget | ~15 seconds reserved from total timeout | `unverified` (observed pattern in project, no OCI doc confirms exact value) |
| fn-events module | Added in FDK v1.1.x (APIGatewayFunction, ConnectorHubFunction) | https://github.com/fnproject/fdk-java/blob/master/fn-events/README.md |

## OCI Java SDK

| Fact | Value | Source |
|------|-------|--------|
| SDK target version | v3.36+ (baseline) / v3.86.1 (latest at authoring) | https://github.com/oracle/oci-java-sdk/releases |
| BOM artifact | `oci-java-sdk-bom` | https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/javasdkgettingstarted.htm |
| HTTP provider (MANDATORY) | `oci-java-sdk-common-httpclient-jersey` — required when any SDK module is used; missing causes runtime crash (not compile error) | https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/javasdkgettingstarted.htm |
| Auth for Functions | `ResourcePrincipalAuthenticationDetailsProvider` | https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingoci.htm |
| SDK default read timeout | 60,000 ms (= function default timeout) | `unverified` (observed in SDK source; can cause timeout with no cleanup) |
| Recommended SDK timeouts | connect: 5,000 ms; read: ≤30,000 ms (stay below function timeout) | Observed pattern in `workspace/poc-oci-serverless` services |

## Streaming (OCI)

| Fact | Value | Source |
|------|-------|--------|
| SDK module | `oci-java-sdk-streaming` | https://docs.oracle.com/en-us/iaas/api/#/en/streaming/20180418/ |
| Event envelope | `DomainEvent` (brx-fn-obs-commons) — key = event_type, value = UTF-8 JSON | Observed in `libs/obs-commons/DomainEvent.java` (poc-oci-serverless) |
| Wire encoding | SDK handles base64 automatically; never Base64-encode manually | https://docs.oracle.com/en-us/iaas/Content/Streaming/Tasks/streaming-put-messages.htm |
| PutMessages HTTP 200 trap | HTTP 200 does NOT guarantee per-message delivery — inspect `PutMessagesResultEntry.getError()` | https://docs.oracle.com/en-us/iaas/api/#/en/streaming/20180418/Stream/PutMessages |
| Partition key | Use `event_type` as message key for ordering within event type | Observed pattern in `services/func-event-producer` (poc-oci-serverless) |

## Object Storage

| Fact | Value | Source |
|------|-------|--------|
| SDK module | `oci-java-sdk-objectstorage` | https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/ |
| Namespace fetch | Required before PutObject; retrieve once in `configure()` and cache | Observed in `services/func-api-facade/OciServiceClient.java` |
| Stream management | Always close `GetObjectResponse.getInputStream()` in a finally block | https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/javasdkexamples.htm |
| OOM risk | Never buffer entire object in memory with unbounded byte arrays | `unverified` (pattern inferred from stream management best practices) |

## Vault / Secrets

| Fact | Value | Source |
|------|-------|--------|
| SDK module | `oci-java-sdk-secrets` | https://docs.oracle.com/en-us/iaas/api/#/en/secretretrieval/ |
| Content encoding | Base64 in `Base64SecretBundleContentDetails`; decode with `java.util.Base64.getDecoder()` | https://docs.oracle.com/en-us/iaas/api/#/en/secretretrieval/20190301/SecretBundle |
| IAM requirement | Dynamic group must include function compartment; policy: `allow dynamic-group <dg> to read secret-bundles in compartment <c>` | https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingdynamicgroups.htm |
| Lifecycle state | Secret must be in ACTIVE state; PENDING/DELETING causes retrieval failure | https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Tasks/managingsecrets.htm |

## Deployment

| Fact | Value | Source |
|------|-------|--------|
| Dockerfile CMD (MANDATORY) | Without CMD instruction, container exits immediately → HTTP 502 with no logs | Observed repeatedly in `workspace/poc-oci-serverless` postmortems |
| CMD must match func.yaml | `CMD ["<package>.<Class>::<method>"]` must match `cmd:` in func.yaml | https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingfunctions.htm |
| Terraform deploy pattern | Update image in `terraform.tfvars`; `terraform plan` must show exactly 1 change before apply | Observed in `infra/environments/dev/` (poc-oci-serverless) |
| OCIR region prefix | Image URI format: `<region>.ocir.io/<namespace>/<repo>/<name>:<tag>` | https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryoverview.htm |
| No credentials in func.yaml | Store sensitive values in Vault, reference via OCID in app config | https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionssecretsmanagement.htm |

## API Gateway Integration (FDK fn-events)

| Fact | Value | Source |
|------|-------|--------|
| API Gateway function base class | `APIGatewayFunction<I, O>` (FDK v1.1.x fn-events module) | https://github.com/fnproject/fdk-java/tree/master/fn-events |
| Service Connector Hub (SCH) consumer | `ConnectorHubFunction<StreamingData<T>>` | https://github.com/fnproject/fdk-java/tree/master/fn-events |
| @FnConfiguration | Must be `configure(RuntimeContext)` with `@Override` when extending fn-events classes | `unverified` (observed in poc-oci-serverless; FDK docs are sparse on this constraint) |

## Observability (APM / OCI Monitoring)

| Fact | Value | Source |
|------|-------|--------|
| APM tracing endpoint pattern | `/opentelemetry/private/v1/traces` (NOT `/observations/private`) | `unverified` (observed as a postmortem gotcha in poc-oci-serverless; no direct OCI doc URL captured) |
| Custom metrics namespace | Must use `telemetry-ingestion` endpoint for OCI Monitoring (not standard Monitoring endpoint) | `unverified` (observed pattern; no doc URL captured) |
| W3C trace propagation | Inject `traceparent`/`tracestate` inside event envelope for cross-service distributed traces | https://www.w3.org/TR/trace-context/ |
| MDC cleanup | Always call `MDC.clear()` in `finally` block to prevent context leakage between warm invocations | `unverified` (standard SLF4J best practice; inferred from code pattern) |

---

## Package Provenance

- Source PoC: `workspace/poc-oci-serverless` (read-only; authored by Rodrigo dos Santos Mendes)
- Migrated to package: `packages/oci-functions-java/.apm/`
- Facts last updated: 2026-10-14
- Unverified count: **8 facts** (marked above)
