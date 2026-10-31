# Research: Quarkus AWS Lambda HTTP (`quarkus-amazon-lambda-http`, `quarkus-amazon-lambda-rest`) on Quarkus 3.40 LTS (3.40.1.1)

Unit U2 of the quarkus-aws-saas family. Future skill: `developing-quarkus-amazon-lambda-http-v3-40` (package `quarkus-aws`).
Source item: "Quarkus HTTP APIs on Lambda behind API Gateway".
Family facts applied as given: `workspace/quarkus-aws-saas/_family_facts_v3.40.md`, `workspace/_family_facts_v3.40.md`.
Family rules applied as given: `workspace/quarkus-aws-saas/_family_rules_v3.40.md`, `workspace/_family_rules_v3.40.md`.
Not repeated here (owned by U1, `workspace/quarkus-aws-saas/research_Quarkus_AmazonLambda_v3.40.md`): plain handlers, `QuarkusStreamHandler` contract, packaging basics, JVM vs native vs SnapStart, runtime identifiers, memory/timeout configuration of the function itself.

All pages were read on **2026-10-28** through the WebFetch tool. The tool limits verbatim quotes from some pages to short fragments (about 125 characters), so quoted text below is fragmentary; anything not in quotes is a paraphrase by the tool or by this researcher. Pages read only in part, or read through summarisation, are listed as coverage limits (L-ids) in Research Gaps.

Scope approval: relayed by the caller from `workspace/quarkus-aws-saas/PIPELINE_STATE.md#approvals` (user, 2026-10-28: "Approve, start pilot U1"; "Fix pilot, then fan-out (Recommended)"). Recorded here as a relay, not as an approval by this agent.

---

## Metadata

```yaml
Full_Name: Quarkus AWS Lambda HTTP extensions - io.quarkus:quarkus-amazon-lambda-http (API Gateway HTTP API) and io.quarkus:quarkus-amazon-lambda-rest (API Gateway REST API)
Target_Version: Quarkus 3.40 LTS, patch 3.40.1.1 (extensions and archetypes 3.40.1.1)
Release_Date: Quarkus 3.40 released 2026-09-30; 3.40.1.1 released 2026-10-19 (family fact, https://quarkus.io/releases)
Support_Status: LTS, community-maintained until 2027-09-30 (family fact). Both extensions are marked "preview" in the 3.40 guide.
Primary_Docs: https://quarkus.io/version/3.40/guides/aws-lambda-http
Secondary_Docs: https://quarkus.io/version/3.40/guides/all-config ; https://quarkus.io/version/3.40/guides/security-cors ; https://quarkus.io/version/3.40/guides/funqy-aws-lambda-http ; https://quarkus.io/version/3.40/guides/rest (partial)
Registry: https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-http/3.40.1.1/quarkus-amazon-lambda-http-3.40.1.1.pom ; https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-rest/3.40.1.1/quarkus-amazon-lambda-rest-3.40.1.1.pom
Source_At_Tag: https://github.com/quarkusio/quarkus/tree/3.40.1.1/extensions/amazon-lambda-http ; .../amazon-lambda-rest (read through raw.githubusercontent.com, files listed in Source Bibliography)
Platform_Docs: API Gateway developer guide (HTTP API payload format, REST Lambda proxy, comparison, quotas, CORS, binary media) ; Lambda developer guide (quotas, runtimes)
Official_Repo: https://github.com/quarkusio/quarkus
Research_Date: 2026-10-28
Domain_Complexity: Standard
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 5
Unverified_Count: 11
Irresolvable_Count: 0
Research_Quality_Score: 88%   # ~95 sourced claims; 11 unverified; 0 irresolvable -> (95-11)/95
Execution_Notes: >
  Caller constraints honoured: no sub-agents (P2.parallel skipped, pages fetched directly), no plan mode
  (scope approval relayed by the caller), file written directly instead of via research-synthesizer.
  Evidence rule (family rule 5): versioned quarkus.io/version/3.40 pages, Maven Central POMs and source at
  tag 3.40.1.1 count as High; AWS developer-guide pages are current official platform pages (High).
```

---

## Executive Summary

Quarkus 3.40.1.1 ships two extensions that run a Quarkus HTTP application as one AWS Lambda function behind Amazon API Gateway. The 3.40 guide says: "Quarkus has a different extension for each Gateway API." "The HTTP Gateway API is implemented within the `quarkus-amazon-lambda-http` extension." "The REST Gateway API is implemented within the `quarkus-amazon-lambda-rest` extension." (https://quarkus.io/version/3.40/guides/aws-lambda-http, read 2026-10-28). The supported frameworks are "Quarkus REST (our Jakarta REST implementation), Undertow (servlet), Reactive Routes" and Funqy HTTP (linked to its own guide), and "You should only use a single HTTP framework together with the AWS Lambda extension to avoid unexpected conflicts and errors." The guide marks the technology as preview: "In _preview_, backward compatibility and presence in the ecosystem is not guaranteed." At tag 3.40.1.1 the HTTP extension's handler is `LambdaHttpHandler implements RequestHandler<APIGatewayV2HTTPEvent, APIGatewayV2HTTPResponse>`, which matches the API Gateway payload format 2.0. The REST extension's handler implements `RequestHandler<AwsProxyRequest, AwsProxyResponse>`, which matches the REST API Lambda proxy (1.0-style) event. Each handler turns the event into a Netty request for the Vert.x HTTP layer and turns the response back into an event (source at tag 3.40.1.1, read 2026-10-28).

For 3.40 nothing changed that needs manual work. The Quarkus 3.40 migration guide says "Quarkus 3.40 LTS is the direct continuation of 3.39 so we don't expect any changes requiring manual intervention in 3.40" and has no Lambda item (https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40, last edited 2026-10-01). The 3.40 configuration reference lists the security keys `quarkus.lambda-http.enable-security` (default `false`), `map-cognito-to-roles` (default `true`), `cognito-role-claim` (default `cognito:groups`) and `cognito-claim-matcher` (default `[^\[\] \t]+`), plus the shared mock-event-server keys (https://quarkus.io/version/3.40/guides/all-config). This research found two pitfalls that the guide does not mention. First, the REST extension's generated `sam.native.yaml` at tag 3.40.1.1 declares `Runtime: provided`. AWS deprecated that runtime on Jan 8, 2024 and has blocked creating functions with it since Feb 8, 2024. The HTTP extension's template uses `provided.al2023` instead. Second, the guide says the REST extension "forces a binary (base 64) encoding of all HTTP response messages", but the 3.40.1.1 REST handler base64-encodes only non-text content types. This conflict is reported as G1 and is not resolved here.

The three critical patterns: (1) pick the extension that matches the gateway type (`-http` ↔ HTTP API / `APIGatewayV2HTTPEvent`, `-rest` ↔ REST API / `AwsProxyRequest`), use one HTTP framework, and inject only the raw-event types documented for that extension; (2) for a REST API, configure the API's binary media types as `*/*`, as the guide and the generated templates require; (3) set `quarkus.lambda-http.enable-security=true` when the application needs the authorizer's identity as a `java.security.Principal`, because the default is `false`. Cognito, JWT and roles in depth belong to U3. Domain complexity is **Standard**: two extensions, two event formats, binary/CORS/timeout cross-cutting concerns with the gateway, and a thin security bridge. There are no encryption or compliance surfaces in this unit.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (versioned official Quarkus page, Maven Central POM, Quarkus source at tag 3.40.1.1, or current AWS developer-guide page, read 2026-10-28) | 🟡 Medium (inference, paraphrase-only evidence, or partly read page) | 🔴 Low (unverified; verify before use)
> Family evidence rule applied (family rules 5 and 6): a single versioned official source is enough for High. Always Do and Never Do hold High claims only; medium/unverified items are in Conditional Patterns or Research Gaps.

### ✅ Mandatory Patterns

**A1. Use the extension that matches the API Gateway type: `quarkus-amazon-lambda-http` for an HTTP API, `quarkus-amazon-lambda-rest` for a REST API**
> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda-http guide (2026-10-28) + Maven Central POMs 3.40.1.1 (2026-10-28) + source at tag 3.40.1.1 (2026-10-28)]
- Why: "Quarkus has a different extension for each Gateway API." The REST POM description is "Build an API Gateway REST API with Lambda integration". The HTTP handler is typed `RequestHandler<APIGatewayV2HTTPEvent, APIGatewayV2HTTPResponse>` and the REST handler is typed `RequestHandler<AwsProxyRequest, AwsProxyResponse>`, so each extension only understands its own gateway's event.
- Code (coordinates from Maven Central; the guide itself shows no dependency XML, it only says the POM needs the matching extension):
  ```xml
  <!-- Quarkus 3.40.1.1 - API Gateway HTTP API (payload format 2.0 event type APIGatewayV2HTTPEvent) -->
  <dependency>
    <groupId>io.quarkus</groupId>
    <artifactId>quarkus-amazon-lambda-http</artifactId>
  </dependency>
  <!-- OR, for an API Gateway REST API (AwsProxyRequest event type) -->
  <dependency>
    <groupId>io.quarkus</groupId>
    <artifactId>quarkus-amazon-lambda-rest</artifactId>
  </dependency>
  ```
- Archetypes (verbatim from the guide):
  ```bash
  # Representative — adapt to your environment (Quarkus 3.40.1.1)
  mvn archetype:generate \
         -DarchetypeGroupId=io.quarkus \
         -DarchetypeArtifactId=quarkus-amazon-lambda-http-archetype \
         -DarchetypeVersion=3.40.1.1
  mvn archetype:generate \
         -DarchetypeGroupId=io.quarkus \
         -DarchetypeArtifactId=quarkus-amazon-lambda-rest-archetype \
         -DarchetypeVersion=3.40.1.1
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-http/3.40.1.1/quarkus-amazon-lambda-http-3.40.1.1.pom (2026-10-28); https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-rest/3.40.1.1/quarkus-amazon-lambda-rest-3.40.1.1.pom (2026-10-28)

**A2. Deploy exactly one HTTP framework per Lambda application**
> Confidence: 🟢 High
- Why: "You should only use a single HTTP framework together with the AWS Lambda extension to avoid unexpected conflicts and errors." The guide calls the `quarkus-rest`, `quarkus-reactive-routes` and `quarkus-undertow` dependencies in the generated project optional and says "Pick which HTTP framework(s) you want to use", so remove the ones you do not use.
- Code:
  ```xml
  <!-- Quarkus 3.40.1.1: keep ONE of quarkus-rest | quarkus-reactive-routes | quarkus-undertow -->
  <dependency>
    <groupId>io.quarkus</groupId>
    <artifactId>quarkus-rest</artifactId>
  </dependency>
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28)

**A3. Inject the raw AWS event and Lambda context only through the types documented for your extension**
> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda-http guide "Injectable AWS Context Variables" (2026-10-28) + source at tag 3.40.1.1 `setContextObject(...)` calls (2026-10-28)]
- Why: with Quarkus REST, the HTTP extension exposes `com.amazonaws.services.lambda.runtime.Context`, `APIGatewayV2HTTPEvent` and `APIGatewayV2HTTPEvent.RequestContext`. The REST extension exposes `Context`, `io.quarkus.amazon.lambda.http.model.AwsProxyRequestContext` and `io.quarkus.amazon.lambda.http.model.AwsProxyRequest`. In both 3.40.1.1 handlers these are exactly the objects stored per request with `quarkusHeaders.setContextObject(<Class>.class, ...)`.
- Code (method shapes from the guide; the guide's snippet does not import `@Path`/`@GET`; return bodies are illustrative (medium confidence)):
  ```java
  // Quarkus 3.40.1.1 - quarkus-amazon-lambda-http + quarkus-rest (HTTP API, payload 2.0)
  import jakarta.ws.rs.GET;
  import jakarta.ws.rs.Path;
  import jakarta.ws.rs.core.Context;
  import com.amazonaws.services.lambda.runtime.events.APIGatewayV2HTTPEvent;

  @Path("/myresource")
  public class MyResource {
      @GET @Path("ctx")
      public String ctx(@Context com.amazonaws.services.lambda.runtime.Context ctx) { return ctx.getAwsRequestId(); }

      @GET @Path("event")
      public String event(@Context APIGatewayV2HTTPEvent event) { return event.getRawPath(); }

      @GET @Path("requestContext")
      public String requestContext(@Context APIGatewayV2HTTPEvent.RequestContext req) { return req.getRequestId(); }
  }
  ```
  ```java
  // Quarkus 3.40.1.1 - quarkus-amazon-lambda-rest + quarkus-rest (REST API)
  import jakarta.ws.rs.core.Context;
  import io.quarkus.amazon.lambda.http.model.AwsProxyRequest;
  import io.quarkus.amazon.lambda.http.model.AwsProxyRequestContext;
  // methods from the guide: reqContext(@Context AwsProxyRequestContext req), req(@Context AwsProxyRequest req)
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java (2026-10-28); https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java (2026-10-28)

**A4. REST API: configure the API's binary media types as `*/*`**
> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda-http guide (2026-10-28) + generated REST `sam.jvm.yaml`/`sam.native.yaml` at tag 3.40.1.1 (2026-10-28) + AWS lambda-proxy-binary-media (2026-10-28)]
- Why: the guide says the REST API "assumes that HTTP response bodies are text unless you explicitly tell it" "which media types are binary through configuration", and that "the `sam.yaml` file must configure the API Gateway to assume all media types are binary". AWS says that to return binary media from a Lambda proxy integration you must base64-encode the response and "configure your API's binary media types". AWS also says API Gateway "uses the first `Accept` header from clients to determine if a response should return binary media" and recommends `*/*` when you cannot control that header. The REST templates at tag 3.40.1.1 carry `BinaryMediaTypes: - "*/*"`. The Terraform side belongs to `provisioning-aws-api-gateway-v6` (family rule 4).
- Code (artifact contract value, as in the generated template):
  ```yaml
  # Generated by quarkus-amazon-lambda-rest 3.40.1.1 (target/sam.jvm.yaml) - reference value only
  Globals:
    Api:
      EndpointConfiguration: REGIONAL
      BinaryMediaTypes:
        - "*/*"
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/deployment/src/main/resources/http/sam.jvm.yaml (2026-10-28); https://docs.aws.amazon.com/apigateway/latest/developerguide/lambda-proxy-binary-media.html (2026-10-28)

**A5. Set `quarkus.lambda-http.enable-security=true` when the application needs the authorizer identity**
> Confidence: 🟢 High | [✓✓ Triangulated | all-config 3.40 (2026-10-28) + aws-lambda-http guide (2026-10-28) + deployment processor at tag 3.40.1.1 (2026-10-28)]
- Why: the key's default is `false` (env `QUARKUS_LAMBDA_HTTP_ENABLE_SECURITY`). In the 3.40.1.1 deployment processor, `setupSecurity` returns early unless `config.enableSecurity()` is true. Only when it is true does it register `LambdaHttpAuthenticationMechanism` and `DefaultLambdaIdentityProvider`. The full security model is in the one-paragraph summary under C8 and in U3.
- Code:
  ```properties
  # src/main/resources/application.properties (Quarkus 3.40.1.1)
  quarkus.lambda-http.enable-security=true
  ```
- Source: https://quarkus.io/version/3.40/guides/all-config (2026-10-28, chars 0-100,000); https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/deployment/src/main/java/io/quarkus/amazon/lambda/http/deployment/AmazonLambdaHttpProcessor.java (2026-10-28)

**A6. Develop against the mock event server; POST raw API Gateway events to `/_lambda_` for complex cases**
> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda-http guide (2026-10-28) + all-config 3.40 (2026-10-28) + family fact row 14]
- Why: "In dev and test mode, Quarkus will start a mock AWS Lambda event server that will convert HTTP requests" into API Gateway events. To simulate more complex events, POST raw API Gateway JSON to `/_lambda_` (paraphrase). "The mock event server is also started for `@QuarkusIntegrationTest` tests, so it will work with native binaries too." Keys: `quarkus.lambda.mock-event-server.enabled` (default `true`), `quarkus.lambda.mock-event-server.dev-port` (default `8080`), `quarkus.lambda.mock-event-server.test-port` (default `8081`). In-depth testing belongs to U6.
- Code:
  ```bash
  # Representative — adapt to your environment (Quarkus 3.40.1.1)
  ./mvnw quarkus:dev
  curl -s http://localhost:8080/hello             # converted by the mock server into an API Gateway event
  # raw event (HTTP API extension): POST an APIGatewayV2HTTPEvent JSON body to http://localhost:8080/_lambda_
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://quarkus.io/version/3.40/guides/all-config (2026-10-28)

**A7. Treat `target/sam.jvm.yaml` / `target/sam.native.yaml` as reference output; provision with the Terraform skills**
> Confidence: 🟢 High (artifact facts) + family rule 4 (policy)
- Why: the build writes `function.zip` ("lambda deployment file"), `sam.jvm.yaml` ("sam cli deployment script") and `sam.native.yaml` ("sam cli deployment script for native") to `target/` (Maven) or `build/` (Gradle). Family rule 4 says IaC goes through `provisioning-aws-lambda-v6` and `provisioning-aws-api-gateway-v6`, never SAM. The templates are still the authoritative source for the values the extension expects (handler, runtime, binary media types, native env var; see the artifact contract table in Implementation Blueprint).
- Code:
  ```bash
  # Representative — adapt to your environment (Quarkus 3.40.1.1)
  ./mvnw install            # -> target/function.zip, target/sam.jvm.yaml, target/sam.native.yaml
  ./mvnw install -Dnative   # native build; see U1 for native prerequisites
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28)

### ⚠️ Conditional Patterns

**C1. HTTP API or REST API**
> Confidence: 🟢 High (feature matrix) | decision is the user's
- Options: A) HTTP API + `quarkus-amazon-lambda-http`; B) REST API + `quarkus-amazon-lambda-rest`.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | HTTP API | price ("designed with minimal features so that they can be offered at a lower price"), native JWT authorizer, automatic deployments, Cloud Map private integration | no edge-optimized/private endpoints, no AWS WAF, no API keys/usage plans/per-client throttling, no caching, no request validation, no request-body transformation, no X-Ray tracing at the gateway, no execution logs, no response streaming; integration timeout fixed at 30 s | public regional API with Cognito/JWT and no API-management needs |
  | REST API | API keys, per-client throttling, request validation, AWS WAF, private endpoints, caching, X-Ray at the gateway, resource policies | higher price; binary media types must be `*/*` (A4); no native JWT authorizer (Lambda authorizer instead) | needs any REST-only feature |

- Agent: "Ask the user: do you need API keys / usage plans, AWS WAF, private endpoints, caching, request validation or resource policies? If yes, REST API; if not, HTTP API."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html (2026-10-28) (the guide links this page); https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html (2026-10-28)

**C2. Which HTTP framework on Lambda**
> Confidence: 🟢 High (supported list) / 🟡 Medium (selection criteria)
- Options: Quarkus REST (`quarkus-rest`), Reactive Routes (`quarkus-reactive-routes`), Undertow servlet (`quarkus-undertow`), Funqy HTTP (`quarkus-funqy-http` + `quarkus-amazon-lambda-http`, per its own preview guide, which says it "requires you to use AWS API Gateway" without naming HTTP or REST API).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Quarkus REST | `@Context` injection of the raw event is documented only for it | — | default for new JAX-RS APIs (sibling `developing-quarkus-rest-v3-40`) |
  | Reactive Routes | lightweight Vert.x routes | raw-event access not documented (M4) | very small route sets |
  | Undertow | servlet portability (the HTTP POM description reads "Allow applications written for a servlet container to run in AWS Lambda") | raw-event access not documented (M4) | porting servlet code |
  | Funqy HTTP | function-style API | separate preview guide; gateway type not stated (M7) | Funqy codebases |

- Agent: "Ask which framework; default proposal Quarkus REST (medium confidence) because the guide documents raw-event injection only for it."
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://quarkus.io/version/3.40/guides/funqy-aws-lambda-http (2026-10-28)

**C3. Where to handle CORS**
> Confidence: 🟡 Medium (the Quarkus Lambda guide does not mention CORS)
- Options: A) HTTP API CORS configuration on the gateway; B) Quarkus CORS filter (`quarkus.http.cors.enabled`, default `false`; origins have no default, and "When not specified, CORS is not permitted, and only same-origin requests are allowed"); C) for a REST API with Lambda proxy, return the headers from the application ("you must add `Access-Control-Allow-Origin:domain-name` to the output `headers`").
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A (HTTP API gateway CORS) | preflight answered by API Gateway "even if there isn't an OPTIONS route"; one place to configure | "API Gateway ignores CORS headers returned from your backend integration"; with `$default` route + authorizer you need an unauthorized `OPTIONS /{proxy+}` route | HTTP API |
  | B (Quarkus filter) | same config locally and deployed | whether the filter runs for Lambda-dispatched requests is (unverified) (U1); ignored behind an HTTP API that has CORS configured | REST API, or HTTP API without gateway CORS |
  | C (headers from code) | explicit | hand-written; error responses must carry headers too | REST API without B |

- Agent: "Ask which gateway and whether gateway CORS is already defined in `provisioning-aws-api-gateway-v6`; never configure A and B for the same HTTP API (B is ignored)."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-cors.html (2026-10-28); https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html (2026-10-28); https://quarkus.io/version/3.40/guides/security-cors (2026-10-28)

**C4. Timeout budget (Lambda timeout vs API Gateway integration timeout)**
> Confidence: 🟢 High (numbers) / 🟡 Medium (the budgeting rule itself)
- Facts: HTTP API "Maximum integration timeout | 30 seconds | No". REST API Regional/private "50 milliseconds - 29 seconds", raisable ("You can raise the integration timeout to greater than 29 seconds, but this might require a reduction in your Region-level throttle quota"); edge-optimized not raisable. Lambda function timeout max 900 s. The generated templates set `Timeout: 15`. The 3.40.1.1 handlers wait on the response future with no timeout of their own (`handler.getFuture().get()`).
- Options: A) keep the Lambda timeout below the gateway integration timeout (medium confidence: derived rule); B) REST Regional with a raised quota; C) move long work off the synchronous path (out of scope: U5).
- Agent: "Ask the expected p99 latency; propose Lambda timeout < gateway timeout. What the client sees when the gateway times out first is (unverified) (U7)."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html (2026-10-28); https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html (2026-10-28); source files in A3 (2026-10-28)

**C5. Payload size and binary bodies**
> Confidence: 🟢 High (limits) / 🟡 Medium (effective ceiling, M3)
- Facts: API Gateway payload size 10 MB (HTTP and REST, not increasable). Lambda synchronous invocation payload "6 MB each for request and response". Lambda "1 MB for the total combined size of request line and header values". HTTP API "Total combined size of request line and header values | 10240 bytes". REST API total header size 20480 bytes (8000 bytes for a private API). The HTTP handler base64-decodes request bodies when `isBase64Encoded` is true, and base64-encodes responses whose `Content-Type` is not text (`isText`: starts with `text`, contains `json`, `yaml`, or `xml` except `openxmlformats`; a missing `Content-Type` counts as binary). The guide says binary responses are base64-encoded when deployed: "This is different from the behavior using `quarkus:dev`, which will return the raw bytes."
- Options: A) inline binary within the 6 MB Lambda limit, remembering the base64 overhead (medium confidence, M3); B) presigned S3 URLs for large files (U4).
- Agent: "Ask the maximum request/response size; above a few MB propose S3 presigned URLs (U4). Always set an explicit `Content-Type` on responses, because a missing one is base64-encoded as binary."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html (2026-10-28); https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html (2026-10-28); https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); HTTP `LambdaHttpHandler.java` at tag 3.40.1.1 (2026-10-28)

**C6. HTTP API payload format version and custom-domain base paths**
> Confidence: 🟡 Medium (inference from two High sources)
- Facts: AWS: when an integration is created "by using the AWS CLI, CloudFormation, or an SDK, you must specify a `payloadFormatVersion`. The supported values are `1.0` and `2.0`." The 3.40.1.1 HTTP handler deserialises `APIGatewayV2HTTPEvent`, reads the method from `requestContext.http.method`, and throws `IllegalStateException` if it is missing. A 1.0 payload carries `requestContext.httpMethod` instead. AWS also says: "If you use an API mapping to connect your stage to a custom domain name, `rawPath` won't provide the API mapping value. Use format `1.0` and `path` to access the API mapping". The HTTP handler builds the request URI from `rawPath` (+ `rawQueryString`).
- Options: A) payload format 2.0 with `quarkus-amazon-lambda-http`, and design routes without relying on the API-mapping prefix; B) a REST API with `quarkus-amazon-lambda-rest` when the mapping prefix must be visible.
- Agent: "Propose `payloadFormatVersion = 2.0` for every HTTP API integration that targets a quarkus-amazon-lambda-http function (medium confidence: the guide does not state it). Ask whether a custom-domain API mapping with a path is planned."
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html (2026-10-28); HTTP `LambdaHttpHandler.java` at tag 3.40.1.1 (2026-10-28)

**C7. Lambda function URLs or Application Load Balancer instead of API Gateway**
> Confidence: 🔴 Low (not covered by the 3.40 guide)
- Facts: the 3.40 guide does not mention Function URLs or ALB. The 3.40.1.1 REST handler has a `RequestSource.ALB` branch (detected when `requestContext.elb` is non-null). It appends query values unencoded for ALB and sets `statusDescription` only for ALB. This is code, not a documented feature (U6). Function URL support is (unverified) (U5).
- Agent: "Ask before proposing Function URLs or ALB; the skill must state that the Quarkus 3.40 guide documents API Gateway only."
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); REST `LambdaHttpHandler.java` and `AwsProxyRequest.java` at tag 3.40.1.1 (2026-10-28)

**C8. Identity from the authorizer: built-in principals or a custom `LambdaIdentityProvider` (summary; depth in U3)**
> Confidence: 🟢 High (facts) | decision belongs to U3
- One-paragraph summary of what the extension does: with `quarkus.lambda-http.enable-security=true` (default `false`), Quarkus reads the authorizer data that API Gateway put in the event and registers a `java.security.Principal`. HTTP API: Cognito JWT → `io.quarkus.amazon.lambda.http.CognitoPrincipal` (name from `requestContext.authorizer.jwt.claims.cognito:username`), IAM → `IAMPrincipal` (`requestContext.authorizer.iam.userId`), Lambda authorizer → `CustomPrincipal` (`requestContext.authorizer.lambda.principalId`). REST API: `requestContext.authorizer.claims.cognito:username`, `requestContext.identity.user`, `requestContext.authorizer.principalId` respectively. Cognito groups are mapped to roles: `map-cognito-to-roles` default `true`, `cognito-role-claim` default `cognito:groups`, `cognito-claim-matcher` default `[^\[\] \t]+`. Alternatively, an `@ApplicationScoped` bean implementing `io.quarkus.amazon.lambda.http.LambdaIdentityProvider` overrides `SecurityIdentity authenticate(APIGatewayV2HTTPEvent event)` (HTTP) or `authenticate(AwsProxyRequest event)` (REST). For `sam local`, the environment variable `QUARKUS_AWS_LAMBDA_FORCE_USER_NAME` hardcodes a principal name. Tenant isolation (family rule 6) and Cognito/JWT design are U3.
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://quarkus.io/version/3.40/guides/all-config (2026-10-28)

**C9. Native image CPU target for Lambda**
> Confidence: 🟢 High (guide statement) | JVM vs native itself is U1/C1 (family rule 3)
- Facts: "AL2023 x86-64 binaries are built for the x86-64-v2 revision of the x86-64 architecture." "In Quarkus, the default value of quarkus.native.march is x86-64-v3." "To maximize Lambda compatibility, you can set quarkus.native.march to x86-64-v2."
- Agent: "If native is chosen (U1 Ask-First), ask whether to set `quarkus.native.march=x86-64-v2`."
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28)

### 🚫 Forbidden Patterns

**F1. Adding more than one HTTP framework to a Lambda HTTP application**
> Severity: High
> Confidence: 🟢 High
- Why: "You should only use a single HTTP framework together with the AWS Lambda extension to avoid unexpected conflicts and errors."
- Impact: unexpected conflicts and errors (guide wording; failure mode not specified).
- ❌ Wrong:
  ```xml
  <!-- Quarkus 3.40.1.1 -->
  <dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest</artifactId></dependency>
  <dependency><groupId>io.quarkus</groupId><artifactId>quarkus-undertow</artifactId></dependency>
  <dependency><groupId>io.quarkus</groupId><artifactId>quarkus-reactive-routes</artifactId></dependency>
  ```
- ✅ Correct:
  ```xml
  <!-- Quarkus 3.40.1.1: one framework only -->
  <dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest</artifactId></dependency>
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28)

**F2. Injecting the other gateway's event type**
> Severity: High
> Confidence: 🟢 High
- Why: the HTTP extension stores only `Context`, `APIGatewayV2HTTPEvent` and `APIGatewayV2HTTPEvent.RequestContext`; the REST extension stores only `Context`, `AwsProxyRequestContext` and `AwsProxyRequest`. The 3.40.1.1 HTTP producers return `null` when the class key is absent (`getContextObjects().get(...)` on an empty map).
- Impact: a null event at runtime.
- ❌ Wrong:
  ```java
  // quarkus-amazon-lambda-rest 3.40.1.1 project
  public String event(@Context APIGatewayV2HTTPEvent event) { return event.getRawPath(); }
  ```
- ✅ Correct:
  ```java
  // quarkus-amazon-lambda-rest 3.40.1.1 project
  public String req(@Context io.quarkus.amazon.lambda.http.model.AwsProxyRequest req) { return req.getPath(); }
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/AwsHttpContextProducers.java (2026-10-28)

**F3. REST API without binary media types `*/*`**
> Severity: High
> Confidence: 🟢 High
- Why: the guide says the `sam.yaml` "must configure the API Gateway to assume all media types are binary". AWS says the REST API treats bodies as text unless the content type is configured as binary.
- Impact: base64-encoded bodies reach clients undecoded (per the guide's reasoning; exact client symptom not tested).
- ❌ Wrong:
  ```yaml
  # REST API for a quarkus-amazon-lambda-rest 3.40.1.1 function, no binary media types
  Globals:
    Api:
      EndpointConfiguration: REGIONAL
  ```
- ✅ Correct:
  ```yaml
  Globals:
    Api:
      EndpointConfiguration: REGIONAL
      BinaryMediaTypes:
        - "*/*"
  # In Terraform: binary_media_types = ["*/*"] via provisioning-aws-api-gateway-v6 (attribute name per that skill)
  ```
- Source: https://quarkus.io/version/3.40/guides/aws-lambda-http (2026-10-28); https://docs.aws.amazon.com/apigateway/latest/developerguide/lambda-proxy-binary-media.html (2026-10-28)

**F4. Shipping the REST extension's generated native runtime `provided`**
> Severity: High
> Confidence: 🟢 High
- Why: `quarkus-amazon-lambda-rest` 3.40.1.1 generates `sam.native.yaml` with `Runtime: provided`. AWS lists `provided` (Amazon Linux) as deprecated Jan 8, 2024, block function create Feb 8, 2024, block function update Aug 31, 2027. The only supported OS-only runtime is `provided.al2023`, which is the value `quarkus-amazon-lambda-http` 3.40.1.1 writes in its own `sam.native.yaml`.
- Impact: new functions cannot be created on `provided`; existing ones run unpatched and lose updates on Aug 31, 2027.
- ❌ Wrong:
  ```yaml
  # target/sam.native.yaml as generated by quarkus-amazon-lambda-rest 3.40.1.1
  Runtime: provided
  ```
- ✅ Correct:
  ```yaml
  # value to carry into provisioning-aws-lambda-v6 for a native Quarkus 3.40.1.1 function
  Runtime: provided.al2023
  ```
- Note: the family fact (row 13) keeps the general "Quarkus native ↔ `provided.al2023`" pairing at (medium confidence). This entry relies only on the two High facts above. The new source evidence is reported to the orchestrator (G2).
- Source: https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/deployment/src/main/resources/http/sam.native.yaml (2026-10-28); https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/deployment/src/main/resources/http/sam.native.yaml (2026-10-28); https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html (2026-10-28)

**F5. Reading multi-value headers or query parameters from the raw `APIGatewayV2HTTPEvent`**
> Severity: Moderate
> Confidence: 🟢 High
- Why: "Format `2.0` doesn't have `multiValueHeaders` or `multiValueQueryStringParameters` fields. Duplicate headers are combined with commas and included in the `headers` field. Duplicate query strings are combined with commas". The 3.40.1.1 HTTP handler rebuilds the request from `rawPath` + `rawQueryString` and splits header values on commas (except `access-control-request-headers`) before Quarkus REST sees them.
- Impact: hand parsing of `event.getHeaders()` / `getQueryStringParameters()` loses value boundaries.
- ❌ Wrong:
  ```java
  // Quarkus 3.40.1.1, quarkus-amazon-lambda-http
  String[] tags = event.getQueryStringParameters().get("tag").split(",");   // "a,b" is ambiguous
  ```
- ✅ Correct:
  ```java
  // Quarkus 3.40.1.1: let Quarkus REST parse the request rebuilt from rawQueryString
  @GET public String list(@QueryParam("tag") List<String> tags) { return String.join("|", tags); }
  ```
- Source: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html (2026-10-28); HTTP `LambdaHttpHandler.java` at tag 3.40.1.1 (2026-10-28)

**F6. Expecting an authorizer `Principal` without enabling security**
> Severity: High
> Confidence: 🟢 High
- Why: `quarkus.lambda-http.enable-security` defaults to `false`, and the 3.40.1.1 processor registers the authentication mechanism only when it is true.
- Impact: the authorizer identity is not turned into a `Principal`/`SecurityIdentity`.
- ❌ Wrong:
  ```properties
  # application.properties, Quarkus 3.40.1.1 - key omitted (default false)
  quarkus.lambda-http.map-cognito-to-roles=true
  ```
- ✅ Correct:
  ```properties
  quarkus.lambda-http.enable-security=true
  ```
- Source: https://quarkus.io/version/3.40/guides/all-config (2026-10-28); AmazonLambdaHttpProcessor.java at tag 3.40.1.1 (2026-10-28)

---

## Migration Guide

> Confidence: 🟢 High | Sources: https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40 (last edited 2026-10-01, read 2026-10-28) + https://quarkus.io/version/3.40/guides/all-config (2026-10-28)

**Breaking Changes**: none for the Lambda HTTP extensions in 3.40. The 3.40 migration guide has no Lambda, AWS, Funqy or vertx-http item and says "Quarkus 3.40 LTS is the direct continuation of 3.39 so we don't expect any changes requiring manual intervention in 3.40." Changes between 3.33 and 3.39 were not read (U8). Inherited 3.31 changes (`quarkus-junit5` → `quarkus-junit`, `quarkus.https.*` removal) apply as family facts and are not repeated.

**⚠️ Migration Note (template defect, not an API change)**: the REST extension's native SAM template still declares `Runtime: provided` (F4). When moving a REST native function to 3.40, set `provided.al2023` in Terraform.

**Upgrade Steps**:
1. Bump the Quarkus platform BOM to 3.40.1.1 (archetype version `3.40.1.1`).
2. `./mvnw install` and diff `target/sam.jvm.yaml` / `target/sam.native.yaml` against the values in Terraform (handler `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest`, `java21`, native env `DISABLE_SIGNAL_HANDLERS: true`).
3. For a REST API, confirm the binary media types `*/*` (A4).
4. Re-check `quarkus.lambda-http.*` keys against the 3.40 defaults (Quick table in Implementation Blueprint).

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Quarkus | 3.40.1.1 | 3.40.x | version-locked (family rule 1) |
| JDK (build) | 17 | — | guide prerequisites: "JDK 17+ installed with `JAVA_HOME` configured appropriately" |
| Lambda runtime (JVM) | `java21` | — | generated `sam.jvm.yaml`: `Runtime: java21` (runtime choice is U1) |
| Lambda runtime (native) | `provided.al2023` | — | HTTP template value; REST template says `provided` (F4) |
| Maven | 3.9.16 | — | guide prerequisites list "Maven 3.9.16" (paraphrased by the tool) (medium confidence) |
| `com.amazonaws:aws-lambda-java-core` | managed by Quarkus BOM | — | declared in the HTTP POM (not in the REST POM's direct list) |
| `org.eclipse.microprofile.jwt:microprofile-jwt-auth-api` | managed | — | declared in both POMs |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | aws-lambda-http guide + source at tag 3.40.1.1]

**Lifecycle** (what happens per request, from the 3.40.1.1 HTTP handler):
```text
API Gateway HTTP API (payload 2.0)
  -> Lambda invokes io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest   (sam.jvm.yaml)
  -> LambdaHttpHandler.handleRequest(APIGatewayV2HTTPEvent, Context)
       URI      = rawPath [+ "?" + rawQueryString]
       method   = requestContext.http.method   (missing -> IllegalStateException)
       headers  = each value split on ","  (except access-control-request-headers); Host: localhost if absent
       cookies  = joined with "; " into one Cookie header
       body     = Base64-decoded if isBase64Encoded, else UTF-8
       context  = setContextObject(Context / APIGatewayV2HTTPEvent / RequestContext)
  -> Vert.x HTTP router -> Quarkus REST | Reactive Routes | Undertow
  -> APIGatewayV2HTTPResponse
       Set-Cookie -> cookies[] ; other headers -> single-value map, values comma-joined
       body       -> text if Content-Type is text/json/yaml/xml, else Base64 + isBase64Encoded=true
       dispatch exception -> 500 {"message":"Internal Server Error"}
```
REST extension differences (3.40.1.1): path from `path`, query rebuilt from `multiValueQueryStringParameters` (URL-encoded except ALB), headers from `multiValueHeaders`, response headers in `multiValueHeaders`, same text/binary rule (see G1).

**Step 1: project** (A1, A2): generate with the archetype for your gateway; keep one framework.

**Step 2: resource with raw-event access** (A3, Quarkus REST):
```java
// Quarkus 3.40.1.1 - quarkus-amazon-lambda-http + quarkus-rest-jackson (method bodies illustrative (medium confidence))
package org.acme;

import com.amazonaws.services.lambda.runtime.events.APIGatewayV2HTTPEvent;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.Context;
import jakarta.ws.rs.core.MediaType;
import java.util.Map;

@Path("/hello")
public class GreetingResource {

    @GET
    @Produces(MediaType.APPLICATION_JSON)   // explicit Content-Type: a missing one is Base64-encoded as binary (C5)
    public Map<String, String> hello(@Context APIGatewayV2HTTPEvent.RequestContext rc,
                                     @Context com.amazonaws.services.lambda.runtime.Context lambda) {
        return Map.of("apiRequestId", rc.getRequestId(), "lambdaRequestId", lambda.getAwsRequestId());
    }
}
```

**Step 3: configuration** (defaults per key, family rule 10; all from https://quarkus.io/version/3.40/guides/all-config unless stated):

| Key | Env var | Type | Default | Note |
|---|---|---|---|---|
| `quarkus.lambda-http.enable-security` | `QUARKUS_LAMBDA_HTTP_ENABLE_SECURITY` | boolean | `false` | A5 |
| `quarkus.lambda-http.map-cognito-to-roles` | `QUARKUS_LAMBDA_HTTP_MAP_COGNITO_TO_ROLES` | boolean | `true` | U3 |
| `quarkus.lambda-http.cognito-role-claim` | `QUARKUS_LAMBDA_HTTP_COGNITO_ROLE_CLAIM` | string | `cognito:groups` | the guide's example override is `cognito:roles` |
| `quarkus.lambda-http.cognito-claim-matcher` | `QUARKUS_LAMBDA_HTTP_COGNITO_CLAIM_MATCHER` | string | `[^\[\] \t]+` | regex for role values |
| `quarkus.lambda.mock-event-server.enabled` | `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_ENABLED` | boolean | `true` | A6 |
| `quarkus.lambda.mock-event-server.dev-port` | `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_DEV_PORT` | int | `8080` | family fact row 14 |
| `quarkus.lambda.mock-event-server.test-port` | `QUARKUS_LAMBDA_MOCK_EVENT_SERVER_TEST_PORT` | int | `8081` | reference description says "dev mode" (doc typo) |
| `quarkus.http.cors.enabled` | page not recorded | boolean | `false` | https://quarkus.io/version/3.40/guides/security-cors ; effect on Lambda (unverified) (U1) |
| `quarkus.native.march` | page not recorded | string | `x86-64-v3` (as stated by the aws-lambda-http guide) | the guide's suggestion is `x86-64-v2` (C9) |

The same four `quarkus.lambda-http.*` keys appear under both the "Amazon Lambda HTTP" and "Amazon Lambda AWS Gateway REST API" sections of the reference. Whether they are build-time fixed is (unverified) (U10).

**Step 4: build and artifact contract** (A7). Values to carry into `provisioning-aws-lambda-v6` / `provisioning-aws-api-gateway-v6`, read line by line from the 3.40.1.1 templates:

| Template value | HTTP `sam.jvm.yaml` | HTTP `sam.native.yaml` | REST `sam.jvm.yaml` | REST `sam.native.yaml` |
|---|---|---|---|---|
| Handler | `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest` | `not.used.in.provided.runtimei` | same as HTTP JVM | `not.used.in.provided.runtimei` |
| Runtime | `java21` | `provided.al2023` | `java21` | `provided` (F4: use `provided.al2023`) |
| CodeUri | `function.zip` | `function.zip` | `function.zip` | `function.zip` |
| MemorySize (the template's example, not a Quarkus default) | `512` | `128` | `512` | `128` |
| Timeout (the template's example) | `15` | `15` | `15` | `15` |
| Policies | `AWSLambdaBasicExecutionRole` | same | same | same |
| Environment | — | `DISABLE_SIGNAL_HANDLERS: true` | — | `DISABLE_SIGNAL_HANDLERS: true` |
| Event | `Type: HttpApi` | `Type: HttpApi` | `Type: Api`, `Path: /{proxy+}`, `Method: any` | same as REST JVM |
| Globals.Api | `EndpointConfiguration: REGIONAL`, `BinaryMediaTypes: "*/*"` | same | same | same |
| Output URL | `https://${ServerlessHttpApi}.execute-api.${AWS::Region}.amazonaws.com/` | same | `https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/` | same |

All HTTP templates also carry a `Globals: Api:` block. Whether it has any effect on an `HttpApi` event is (unverified) (U11).

**Integration**: Quarkus 3.40 Lambda HTTP ↔ Terraform skills. Hand off the table above. Do not author SAM or CDK (family rule 4).

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (Quarkus 3.40.1.1)
./mvnw quarkus:dev                         # mock event server on :8080 (A6)
curl -i http://localhost:8080/hello        # Expected: 200 and JSON body; binary endpoints return RAW bytes in dev
./mvnw verify                              # @QuarkusTest on the mock server, :8081
./mvnw install                             # Expected: target/function.zip, target/sam.jvm.yaml, target/sam.native.yaml
grep -E "Runtime:|Handler:|BinaryMediaTypes" target/sam.*.yaml
# Expected (REST native): "Runtime: provided" -> replace with provided.al2023 in Terraform (F4)
grep -c "quarkus.lambda-http.enable-security=true" src/main/resources/application.properties
# Expected: 1 when the authorizer identity is needed (A5)
```

**Mocking** (shape from the guide's `AmazonLambdaSimpleTestCase`; full pattern in U6, test framework facts in `developing-quarkus-junit-v3-40`):
```java
// Quarkus 3.40.1.1 - POST a raw APIGatewayV2HTTPEvent to the mock event server (/_lambda_)
// Body shape illustrative (medium confidence); see U6 for the canonical test.
@QuarkusTest
class SecurityTest {
    @Test
    void cognitoUsername() {
        APIGatewayV2HTTPEvent request = new APIGatewayV2HTTPEvent();
        // set requestContext.http.method/path = GET /security/username and authorizer.jwt.claims["cognito:username"]="Bill"
        // given().contentType("application/json").body(request).post("/_lambda_")
        //   .then().statusCode(200)  // response is an APIGatewayV2HTTPResponse JSON; body "Bill"
    }
}
```
Guarantee: the mock server runs inside the test JVM (or next to the native binary for `@QuarkusIntegrationTest`), so no AWS account is needed.

---

## Production Readiness

- **Performance**: each invocation is dispatched through an in-process Netty/Vert.x virtual connection (source). Cold-start behaviour, JVM vs native and SnapStart belong to U1. Native is described as giving "a smaller memory footprint and startup time" (guide).
- **Scalability**: Lambda default concurrency 1,000 per Region versus the API Gateway default throttle of 10,000 rps. AWS warns that "it's possible to have more incoming requests from API Gateway that Lambda can handle" (https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html). Each execution environment serves up to 10 synchronous requests per second.
- **Limits**: payload 10 MB (API Gateway) vs 6 MB (Lambda synchronous). Headers: 10240 bytes (HTTP API), 20480 bytes (REST), 1 MB (Lambda). Integration timeout 30 s (HTTP, fixed) / 29 s (REST, raisable for Regional/private). See C4/C5.
- **Error handling**: an exception escaping the dispatch returns HTTP 500 with `{ "message": "Internal Server Error" }` from both 3.40.1.1 handlers. For REST, AWS returns `502 Bad Gateway` when "the function output is of a different format". A non-numeric `X-Forwarded-Port` header causes `Integer.parseInt` to fail, which yields a 500 (source). The HTTP handler splits every header value on commas, so headers whose values legitimately contain commas (for example HTTP dates) reach the application split (medium confidence, M8).
- **Monitoring**: API Gateway CloudWatch metrics and access logs exist for both API types; execution logs and gateway X-Ray tracing exist only for REST APIs (comparison page). Application logging, metrics and tracing belong to U11 to U13. Native X-Ray needs `quarkus-amazon-lambda-xray` (guide; U1/U12).
- **Security**: identity mapping is off by default (A5, C8). Use gateway CORS for HTTP APIs (C3). Never return stack traces (handler already returns a generic 500 body). Secrets come from Secrets Manager/SSM (family rule 5, U5). The tenant comes from the token (family rule 6, U3).

---

## Reference Implementations

- Quarkus 3.40 Lambda HTTP guide samples (`MyResource` context injection, `CustomSecurityProvider`, `AmazonLambdaSimpleTestCase`): https://quarkus.io/version/3.40/guides/aws-lambda-http
- Archetypes: `io.quarkus:quarkus-amazon-lambda-http-archetype:3.40.1.1`, `io.quarkus:quarkus-amazon-lambda-rest-archetype:3.40.1.1` (guide)
- Extension source at tag 3.40.1.1: https://github.com/quarkusio/quarkus/tree/3.40.1.1/extensions/amazon-lambda-http and https://github.com/quarkusio/quarkus/tree/3.40.1.1/extensions/amazon-lambda-rest (tree pages not fetched; files read via raw URLs, see Bibliography)
- Funqy HTTP on Lambda quickstart directory `funqy-amazon-lambda-http-quickstart` (named by https://quarkus.io/version/3.40/guides/funqy-aws-lambda-http; repository not fetched)
- AWS payload 2.0/1.0 samples: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html
- AWS binary Lambda proxy sample: https://docs.aws.amazon.com/apigateway/latest/developerguide/lambda-proxy-binary-media.html

---

## Source Bibliography

**Primary (versioned Quarkus 3.40 / registry / source at tag)**
| # | URL | Read | Coverage | Used for |
|---|---|---|---|---|
| S1 | https://quarkus.io/version/3.40/guides/aws-lambda-http | 2026-10-28 | 7 passes; tool estimated ~50k chars, no truncation reported; verbatim quotes limited to short fragments (L1) | extensions, frameworks, preview status, archetypes, build files, sam notes, binary, injection, security, mock server, march |
| S2 | https://quarkus.io/version/3.40/guides/all-config | 2026-10-28 | 232,437 chars in 3 windows (0-100k found the keys; 100k-200k and 200k-end no matches) (L2) | `quarkus.lambda-http.*`, mock-server keys, defaults |
| S3 | https://quarkus.io/version/3.40/guides/security-cors | 2026-10-28 | coverage not reported by the tool (L5) | `quarkus.http.cors.*` defaults |
| S4 | https://quarkus.io/version/3.40/guides/funqy-aws-lambda-http | 2026-10-28 | short page, summary | Funqy HTTP + `quarkus-amazon-lambda-http`, preview |
| S5 | https://quarkus.io/version/3.40/guides/rest | 2026-10-28 | 0-100,000 of 167,085 chars (L3) | `quarkus-rest`, `quarkus-rest-jackson`, context objects; no Lambda content |
| S6 | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40 | 2026-10-28 | full (last edited 2026-10-01) | no Lambda changes |
| S7 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-http/3.40.1.1/quarkus-amazon-lambda-http-3.40.1.1.pom | 2026-10-28 | full | name, description, dependencies |
| S8 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-rest/3.40.1.1/quarkus-amazon-lambda-rest-3.40.1.1.pom | 2026-10-28 | full | name, description, dependencies |
| S9 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java | 2026-10-28 | full per tool, summarised (L4) | HTTP request/response mapping |
| S10 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java | 2026-10-28 | summarised (L4) | REST mapping, ALB branch, text/binary rule |
| S11 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/runtime/src/main/java/io/quarkus/amazon/lambda/http/model/AwsProxyRequest.java | 2026-10-28 | summarised (L4) | fields, `RequestSource` |
| S12 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/AwsHttpContextProducers.java | 2026-10-28 | summarised (L4) | `@RequestScoped` producers |
| S13 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/deployment/src/main/java/io/quarkus/amazon/lambda/http/deployment/AmazonLambdaHttpProcessor.java | 2026-10-28 | summarised (L4) | handler build item, security build step |
| S14 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/deployment/src/main/java/io/quarkus/amazon/lambda/http/deployment/AmazonLambdaHttpProcessor.java | 2026-10-28 | summarised (L4) | template generation |
| S15 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/deployment/src/main/resources/http/sam.jvm.yaml | 2026-10-28 | every line quoted | artifact contract |
| S16 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/deployment/src/main/resources/http/sam.native.yaml | 2026-10-28 | every line quoted | `provided.al2023` |
| S17 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/deployment/src/main/resources/http/sam.jvm.yaml | 2026-10-28 | every line quoted | REST contract, `*/*` |
| S18 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/deployment/src/main/resources/http/sam.native.yaml | 2026-10-28 | every line quoted | `Runtime: provided` (F4) |

**Primary (AWS developer guides, current pages)**
| # | URL | Read | Used for |
|---|---|---|---|
| S19 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html | 2026-10-28 | payload 1.0/2.0, response inference, `payloadFormatVersion` requirement, `rawPath` + API mapping |
| S20 | https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html | 2026-10-28 | REST proxy input/output, multi-value merge rule, CORS header, 502 on bad format |
| S21 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html | 2026-10-28 | feature comparison (C1) |
| S22 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html | 2026-10-28 | 30 s timeout, 10 MB, 10240-byte headers |
| S23 | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html | 2026-10-28 | REST 29 s timeout (raisable), 10 MB, header sizes, URL lengths |
| S24 | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html | 2026-10-28 | 6 MB sync payload, 1 MB headers, 900 s timeout, concurrency |
| S25 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-cors.html | 2026-10-28 | HTTP API CORS behaviour |
| S26 | https://docs.aws.amazon.com/apigateway/latest/developerguide/lambda-proxy-binary-media.html | 2026-10-28 | binary media types, `Accept` header |
| S27 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html | 2026-10-28 | `provided` deprecation, `provided.al2023`, `java21` |

**Family facts (orchestrator-verified, applied as given)**: rows 9-14 of `workspace/quarkus-aws-saas/_family_facts_v3.40.md` (https://quarkus.io/releases ; https://quarkus.io/guides/aws-lambda ; https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html).

**Cross-unit reference**: `workspace/quarkus-aws-saas/research_Quarkus_AmazonLambda_v3.40.md` (U1) for handlers, packaging, native, SnapStart.

**Validation (community)**: none used.

---

## Research Gaps

```
Gap G1 (source conflict, not a family fact): REST response encoding.
  Guide: "the Quarkus extension forces a binary (base 64) encoding of all HTTP response messages"
  (https://quarkus.io/version/3.40/guides/aws-lambda-http, 2026-10-28).
  Source at tag 3.40.1.1: REST LambdaHttpHandler sets setBase64Encoded(true) only when Content-Type is not text
  (isText: text*, json, yaml, xml except openxmlformats)
  (https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java).
Impact: what a REST client receives for text responses when BinaryMediaTypes is */* (see U3).
Workaround: keep BinaryMediaTypes */* (both sources require it); do not state "all responses are base64" as fact.
Follow-up: orchestrator / human; test with a deployed REST API.
§7-ref: reported, not resolved by this unit.

Gap G2 (evidence relevant to family fact row 13, NOT a contradiction): native runtime in generated templates.
  Family fact row 13: the guide does not name provided.al2023; pairing native <-> provided.al2023 is (medium confidence)
  (https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html).
  New evidence: quarkus-amazon-lambda-http 3.40.1.1 sam.native.yaml declares "Runtime: provided.al2023"
  (https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/deployment/src/main/resources/http/sam.native.yaml);
  quarkus-amazon-lambda-rest 3.40.1.1 sam.native.yaml declares "Runtime: provided"
  (https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-rest/deployment/src/main/resources/http/sam.native.yaml).
Impact: the orchestrator may decide whether the family fact's medium tag can be raised; this unit keeps it as given.
§7-ref: reported.

U1 (unverified): whether the Quarkus CORS filter (quarkus.http.cors.*) runs for Lambda-dispatched requests.
U2 (unverified): which request content types API Gateway HTTP API delivers with isBase64Encoded=true.
U3 (unverified): client-visible effect of BinaryMediaTypes */* on REST responses the 3.40.1.1 handler sends as text (depends on G1).
U4 (unverified): mechanism behind @Context injection of AwsProxyRequest/AwsProxyRequestContext in the REST extension
    (the REST producer class was not fetched; the injection itself is documented in the guide = High).
U5 (unverified): Lambda function URL events with quarkus-amazon-lambda-http (not documented).
U6 (unverified): ALB as a supported front end (only a RequestSource.ALB code branch exists in the REST handler).
U7 (unverified): status code the client receives when the gateway integration timeout fires before the Lambda returns.
U8 (unverified): Lambda HTTP changes in the Quarkus 3.33-3.39 migration guides (only 3.40 read).
U9 (unverified): which HTTP frameworks the 3.40.1.1 archetypes include by default.
U10 (unverified): whether quarkus.lambda-http.* keys are build-time fixed (lock icon not visible to the tool).
U11 (unverified): whether the Globals.Api block in the HTTP-API SAM templates has any effect on an HttpApi event.

M1 (medium confidence): native Quarkus <-> provided.al2023 pairing (family fact wording; see G2).
M2 (medium confidence): method bodies and illustrative code (resources, test skeleton).
M3 (medium confidence): effective inline payload ceiling = 6 MB (Lambda) below 10 MB (API Gateway), reduced further by base64 overhead.
M4 (medium confidence): @Inject of APIGatewayV2HTTPEvent/Context in Reactive Routes or Undertow, inferred from @RequestScoped
    producers in AwsHttpContextProducers (source), not documented.
M5 (medium confidence): statements the tool paraphrased rather than quoted (archetype /hello example, Maven 3.9.16 prerequisite).
M6 (medium confidence): budgeting rule "Lambda timeout < gateway integration timeout" (derived from two High numbers).
M7 (medium confidence): Funqy HTTP on Lambda implies an HTTP API (it uses quarkus-amazon-lambda-http; its guide only says "API Gateway").
M8 (medium confidence): consequence of comma-splitting for headers whose values contain commas (e.g. HTTP dates); also
    payloadFormatVersion 2.0 requirement for -http (C6) derived from source + AWS page.

L1 (coverage limit): aws-lambda-http 3.40 read in 7 WebFetch passes with a short-quote limit; quotes are fragments, the rest is tool paraphrase.
L2 (coverage limit): all-config read in 3 windows; the tool noted part of the first window was summarised; keys found only in 0-100,000.
L3 (coverage limit): rest guide 3.40 read 0-100,000 of 167,085 characters.
L4 (coverage limit): source files at tag 3.40.1.1 read through tool summarisation (code fragments quoted; SAM templates quoted line by line).
L5 (coverage limit): security-cors 3.40 coverage not reported by the tool.
```

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Implementation Blueprint / F5 | How path, headers, query, cookies, base64 bodies are mapped (guide silent) | Resolved from source at tag 3.40.1.1 (HTTP and REST handlers, AwsProxyRequest) | S9, S10, S11 (2026-10-28) |
| 1 | C5 | Which responses are base64-encoded | Resolved for HTTP (`isText` rule); REST conflict with guide logged as G1 | S9, S10, S1 (2026-10-28) |
| 2 | A7 / Blueprint Step 4 | Content of generated sam.jvm.yaml / sam.native.yaml (guide shows only fragments) | Resolved: 4 templates quoted line by line | S15-S18 (2026-10-28) |
| 2 | F4 | REST native template runtime `provided` | Added; confirmed deprecated Jan 8, 2024 / create blocked Feb 8, 2024 | S18, S27 (2026-10-28) |
| 3 | A3 / F2 | How injected event objects are produced | Resolved for HTTP (`@RequestScoped` producers, null when absent); REST producer left U4 | S12 (2026-10-28) |
| 3 | Research Gaps | U1-U11 | Left (unverified): MAX_ITERATIONS=3 reached; not IRRESOLVABLE, each has a follow-up page or test | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited (http vs rest, frameworks incl. Funqy mention, event mapping, raw event/context injection, CORS, binary media types, build output and SAM templates, dev mode/mock server, security one paragraph (C8), Function URL/ALB (C7: not covered by the guide), HTTP limits)
- [x] Pattern counts driven by domain needs (7 / 9 / 6)
- [x] Every anti-pattern has a High alternative (family rule 9)
- [x] All CLI commands marked as representative
- [x] Integration examples complete within scope (artifact contract table for the Terraform skills, family rule 4)
- [x] Sources dated and linked
- [x] Security documented (C8 summary; depth deferred to U3)
- [x] 1+ copy-paste working example (A1 dependencies/archetypes, A5 property, Step 2 resource)
- [x] Confidence badge applied to every pattern entry
- [x] Always-Do patterns triangulated where two sources exist (A1, A3, A4, A5, A6); A2 and A7 High on a single versioned page per family evidence rule
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced (G1/G2 reported; U-items logged in iteration 3)

---

## Agent Operation Notes

- **High Confidence (execute without asking)**: A1 to A7, F1 to F6, the config-key defaults table, the artifact contract table values, AWS quotas and payload-format facts.
- **Medium Confidence (validate with user)**: M1 to M8; C3 (CORS placement), C4 budgeting rule, C6 payload version 2.0 for `-http`.
- **Low Confidence (must ask human)**: U1 to U11; G1 (REST base64: guide vs source); C7 (Function URL / ALB).
- **Edge Cases (pause)**: both extensions are marked preview in the 3.40 guide ("backward compatibility ... is not guaranteed"); Quarkus 3.40.1.1 is 9 days old but the 3.40 LTS line is 28 days old. No pause.
- **Emergency Stop**: not triggered (official versioned sources available; version is current LTS).
- **Decision rules**: HTTP vs REST API is C1 (Ask First); JVM vs native stays U1 (family rule 3); IaC goes only through `provisioning-aws-lambda-v6` / `provisioning-aws-api-gateway-v6` (family rule 4).
