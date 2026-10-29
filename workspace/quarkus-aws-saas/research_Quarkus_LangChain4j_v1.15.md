# Research: Quarkiverse quarkus-langchain4j 1.15.0.CR1 (pre-release) on Quarkus 3.40 LTS inside AWS Lambda

Unit U8 of the quarkus-aws-saas family. Future skill: `integrating-quarkus-langchain4j-v1-15` (package `quarkus-aws-saas`). Source item: framework.
Approval: the user approved U8 locked to 1.15.0.CR1 on 2026-10-28 (verbatim: "1.15.0.CR1, flagged (Recommended)"), recorded in `workspace/quarkus-aws-saas/PIPELINE_STATE.md#approvals`; relayed by the orchestrator, not a new approval.
Family facts applied as given: `workspace/quarkus-aws-saas/_family_facts_v3.40.md` (cited FF<n> = line number of the fact row, e.g. FF18 = quarkus-langchain4j version row). Family rules applied as given: `workspace/quarkus-aws-saas/_family_rules_v3.40.md` (cited R<n>; R3, R5, R6, R7, R9-R13 in particular).

> **PRE-RELEASE CONTEXT (applies to every claim in this file).** The target is **1.15.0.CR1**, a GitHub "Pre-release" (released 03 Oct, year not shown on the release block; Central `lastUpdated` of the provider artifacts is 2026-10-15) [S2][S5]. **No 1.15.0 final exists on Maven Central** as of 2026-10-28; the newer `2.0.0.Beta1` is the Quarkus 4 line and is out of scope (R1) [S5]. The latest stable, 1.14.2, is built on Quarkus 3.33.3.1 / LangChain4j 1.20.2 and cannot be used with Quarkus 3.40 [S4] (FF18). CR behaviour may change before 1.15.0 final. Re-verify every default against the final tag before you rely on it.

> **Which docs were read.** docs.quarkiverse.io publishes **only the `dev` docs version** for quarkus-langchain4j. The version selector shows "dev" and lists no other version [S6]. `dev` follows the main branch, so it is newer than the 1.15.0.CR1 tag. I therefore read three layers: (1) `dev` HTML pages [S6-S17]; (2) the **tag-pinned** AsciiDoc sources at `1.15.0.CR1` for OpenAI, Anthropic and AI services [S33-S35]; (3) **tag-pinned Java config/recorder sources** for defaults [S18-S32]. Where `dev` and the tag differ, the **tag wins**, and the difference is listed in the [Contradictions Report](#contradictions-report). Under R13, a claim from a `dev` page (main branch) or a tool summary is High only when a verbatim quote is recorded here; otherwise it is tagged (medium confidence).

All pages were read on **2026-10-28** with WebFetch. The tool returns verbatim quotes of up to about 125 characters; longer passages are paraphrased without quotation marks. Coverage per page (full / partly read with character ranges / 404) is listed in the bibliography. IDs A1-A10, Q1-Q7 and F1-F8 are this document's own Always / Conditional / Forbidden patterns.

Scope. Covered: `@RegisterAiService` in a Quarkus 3.40 Lambda, chat and streaming models for OpenAI, Anthropic and Amazon Bedrock (Bedrock with the Lambda IAM role, no API key), `quarkus.langchain4j.*` keys and their documented defaults, API keys from Secrets Manager/SSM, timeouts against the Lambda and API Gateway limits, retries, what streaming means behind API Gateway, native/SnapStart notes, the `@Tool` boundary, testing without real provider calls, and metrics/tracing hooks. NOT covered: RAG/vector/embedding stores, MCP, agentic frameworks, plain-Java LangChain4j (`developing-langchain4j-core-v1-22` et al.), Quarkus 4, Terraform (deferred to `provisioning-aws-*-v6`, R4).

Order note: the caller requires the file to **end with the Source Bibliography**. The bibliography is therefore the last section, not section 11 of the template. All 15 template headings are present; two extra sections, "Contradictions Report" and "Facts for the family", sit just before the bibliography.

## Contents

- [Metadata](#metadata)
- [Executive Summary](#executive-summary)
- [Architectural Guardrails](#architectural-guardrails): [Mandatory](#-mandatory-patterns), [Conditional](#️-conditional-patterns), [Forbidden](#-forbidden-patterns)
- [Migration Guide](#migration-guide)
- [Implementation Blueprint](#implementation-blueprint)
- [Quality Control](#quality-control)
- [Production Readiness](#production-readiness)
- [Reference Implementations](#reference-implementations)
- [Research Gaps](#research-gaps)
- [Research Iteration Changelog](#research-iteration-changelog)
- [Completion Checklist](#completion-checklist)
- [Agent Operation Notes](#agent-operation-notes)
- [Contradictions Report](#contradictions-report)
- [Facts for the family](#facts-for-the-family)
- [Source Bibliography](#source-bibliography)

---

## Metadata

```yaml
Full_Name: Quarkiverse quarkus-langchain4j (io.quarkiverse.langchain4j) — extensions quarkus-langchain4j-openai, quarkus-langchain4j-anthropic, quarkus-langchain4j-bedrock — used from a Quarkus 3.40 LTS AWS Lambda (quarkus-amazon-lambda / quarkus-amazon-lambda-http / -rest) behind Amazon API Gateway
Target_Version: 1.15.0.CR1 (PRE-RELEASE) — parent POM quarkus.version 3.40.0, langchain4j.version 1.21.0, quarkus-wiremock.version 1.5.1 [S1]
Release_Date: GitHub release block "released this 03 Oct" (year not shown), marked "Pre-release" [S2]; Central lastUpdated 20261015 for openai/anthropic/bedrock metadata [S5]
Support_Status: Candidate release, no 1.15.0 final on Central as of 2026-10-28 [S5]; latest stable 1.14.2 is on Quarkus 3.33.3.1 / LangChain4j 1.20.2 [S4]; 2.0.0.Beta1 = Quarkus 4 line (out of scope, R1) [S5]; Quarkus 3.40 LTS until 2027-09-30 (FF8)
Primary_Docs: https://docs.quarkiverse.io/quarkus-langchain4j/dev/ (only "dev" is published [S6]) + tag-pinned AsciiDoc https://github.com/quarkiverse/quarkus-langchain4j/tree/1.15.0.CR1/docs/modules/ROOT/pages
Official_Repo: https://github.com/quarkiverse/quarkus-langchain4j (tag 1.15.0.CR1)
Research_Date: 2026-10-28
Domain_Complexity: Complex (three providers, secrets, IAM, hard gateway time limits, PII in prompts, multi-tenant memory risk, pre-release target)
Research_Depth: exhaustive (default; no depth argument supplied)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 5 of 5
Triangulated_Count: 7          # A1, A2, A3, A4, A5, A6, A8 have 2+ independent sources
Unverified_Count: 11           # U1-U11 in Research Gaps
Irresolvable_Count: 3          # G1 Bedrock page at tag, G2 OpenAI chat-model.mode declaration/default at tag, G3 1.14.2...1.15.0.CR1 diff
Research_Quality_Score: 85%    # (~95 claims - 11 unverified - 3 irresolvable) / 95; medium-confidence items counted as verified-with-tag
Deviations_from_agent_workflow: "Caller forbade sub-agents, background tasks and plan mode (scope approved by the user 2026-10-28, relayed via PIPELINE_STATE.md#approvals). All pages fetched directly; file written directly instead of via research-synthesizer. No provider or AWS call was executed; no code was compiled. Source Bibliography moved to the end per caller's Done-when."
```

---

## Executive Summary

quarkus-langchain4j turns an annotated interface into a CDI bean that talks to an LLM: `@RegisterAiService` "Marks an interface as an AI Service managed by CDI, creating a bean for interactions with an LLM" [S7]. At tag 1.15.0.CR1, "The resulting CDI bean is {@link jakarta.enterprise.context.RequestScoped} by default" [S26]. Chat memory defaults to "`MessageWindowChatMemory` with 10-message window", and "Memory is request-scoped by default" [S35]. You pick providers by adding one extension each: `quarkus-langchain4j-openai`, `quarkus-langchain4j-anthropic` and `quarkus-langchain4j-bedrock`, all published as 1.15.0.CR1 on Central [S5]. The only change in 1.15.0.CR1 is the platform move: "Upgrade to Quarkus 3.40" and "Bump to Langchain4j 1.21.0 and support `DecisionModel`". The release lists no breaking changes [S2]. 1.14.2 itself was only a security fix (GHSA-8vpj-4r6j-h9qg in the Redis filter mapper) [S3].

Running inside Lambda behind API Gateway adds hard limits the library docs do not discuss:

- **(a) Time budget.**
  - API Gateway allows 50 ms-29 s per integration for REST APIs. Regional and private APIs can be raised beyond 29 s, "but this might require a reduction in your Region-level throttle quota" [S37]. HTTP APIs have a "Maximum integration timeout | 30 seconds | No" [S38].
  - The OpenAI and Anthropic clients fall back to `Duration.ofSeconds(10)` [S20][S23].
  - OpenAI/Anthropic `max-retries` defaults to `1`, which means "exactly one attempt, with retrying disabled", and is deprecated in favour of MicroProfile Fault Tolerance [S18][S22].
  - Bedrock retries through the AWS SDK: `max-retries` is 3 [S27][S31]. Its `api-call-timeout` is documented as `13s`, but the recorder falls back to `Duration.ofSeconds(10)` [S27][S31], a contradiction listed as C3.
- **(b) Streaming is buffered.** The Quarkus 3.40.1.1 HTTP Lambda handler writes every `HttpContent` chunk into a `ByteArrayOutputStream` and completes only on `LastHttpContent` [S46]. HTTP APIs have no response streaming [S39]. Lambda streams natively only "on Node.js managed runtimes" [S41]. A `Multi<String>` AI service therefore gives no time-to-first-byte gain on Lambda. It also loses retries, because the streaming builders apply no `maxRetries` [S20][S23].
- **(c) Credentials.**
  - Bedrock sets a credentials provider only when `credentials-provider` is configured [S31]. Otherwise the AWS SDK's default chain applies [S45]: Lambda's execution-role environment variables [S43], or container credentials under SnapStart (FF33).
  - OpenAI and Anthropic keys default to the literal `dummy`. An unset key fails with `SRCFG00014 ... is required` [S20][S23].
  - AWS recommends "Secrets Manager instead of environment variables to store ... API keys" [S43], while the extension docs suggest the `QUARKUS_LANGCHAIN4J_OPENAI_API_KEY` environment variable [S33]. R5 settles it: keys come from Secrets Manager/SSM.

Three critical patterns:

1. **Budget the call.** Set the provider timeout and retries explicitly so that `attempts x timeout` fits under the API Gateway integration timeout (29/30 s). Bound the AI method with `@Timeout` from `quarkus-smallrye-fault-tolerance` [S12]. See A3.
2. **Return a blocking `String` (or POJO) from AI services on synchronous API Gateway routes**, not `Multi`. See A5 and F3.
3. **Keep secrets out of config.** Bedrock uses no keys at all (the role is enough plus `bedrock:InvokeModel` / `bedrock:InvokeModelWithResponseStream` [S44]). OpenAI/Anthropic keys are resolved from Secrets Manager at init. Prompt/completion tracing and request logging stay off; they are off by default [S25][S24]. See A2, A4, A7, F1, F4.

Domain tier **Complex**: secrets, IAM, three external services, PII in prompts, multi-tenant memory, and a pre-release target.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, or 1 tag-pinned source / verbatim-quoted official page per R13) | 🟡 Medium (1 source, inference, `dev`-only paraphrase, or tool summary without quote) | 🔴 Low (verify before use)

### ✅ Mandatory Patterns

**A1. Pin the whole quarkus-langchain4j line to 1.15.0.CR1 and let it manage LangChain4j (1.21.0)**
> Confidence: 🟢 High | [✓✓ Triangulated | parent POM 1.15.0.CR1 (2026-10-28) + Central metadata (2026-10-28) + release notes 1.15.0.CR1 (2026-10-28)]
- Why:
  - 1.15.0.CR1 is the only quarkus-langchain4j version on Quarkus 3.40: `<quarkus.version>3.40.0</quarkus.version>` and `<langchain4j.version>1.21.0</langchain4j.version>` [S1] (FF18).
  - 1.14.2 uses `<quarkus.version>3.33.3.1</quarkus.version>` [S4].
  - A `quarkus-langchain4j-bom` artifact exists at 1.15.0.CR1 [S5d].
  - The plain-Java skill family is on LangChain4j **1.22.0**. Do not import its version here: that would be a second LangChain4j version in one application (version absolutism).
  - Whether the BOM manages every `dev.langchain4j:*` artifact was not read (U1).
- Code:
  ```xml
  <!-- Quarkus 3.40 LTS + quarkus-langchain4j 1.15.0.CR1 (PRE-RELEASE) -->
  <dependencyManagement>
    <dependencies>
      <!-- quarkus-bom import as in the family (FF9) -->
      <dependency>
        <groupId>io.quarkiverse.langchain4j</groupId>
        <artifactId>quarkus-langchain4j-bom</artifactId>
        <version>1.15.0.CR1</version>
        <type>pom</type>
        <scope>import</scope>
      </dependency>
    </dependencies>
  </dependencyManagement>
  <dependencies>
    <!-- add only the providers this function uses -->
    <dependency><groupId>io.quarkiverse.langchain4j</groupId><artifactId>quarkus-langchain4j-bedrock</artifactId></dependency>
    <!-- <artifactId>quarkus-langchain4j-openai</artifactId> / <artifactId>quarkus-langchain4j-anthropic</artifactId> -->
  </dependencies>
  ```
- Source: [S1] [S4] [S5] [S2] (all 2026-10-28)

**A2. Bedrock on Lambda: no keys, no credentials in properties; the execution role plus the two Bedrock actions**
> Confidence: 🟢 High | [✓✓ Triangulated | BedrockRecorder.java @1.15.0.CR1 + AWS SDK credentials-chain page + Lambda env-var page + Bedrock Converse page (all 2026-10-28)]
- Why:
  - The recorder sets a provider only when configured: `if (credentialsProvider.isPresent()) { awsClientBuilder.credentialsProvider(...) }`. Region follows the same pattern: `if (region.isPresent()) { awsClientBuilder.region(Region.of(region.get())); }` [S31].
  - Doc defaults: "default aws credentials provider chain" and "default aws region provider chain" [S27].
  - The SDK: "create a service client builder but don't specify a credentials provider", and the chain checks environment variables `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_SESSION_TOKEN` and then container credentials (`AWS_CONTAINER_CREDENTIALS_FULL_URI`) [S45].
  - Lambda sets those keys "obtained from the function's execution role" and sets `AWS_REGION` [S43]. Under SnapStart it uses container credentials instead (FF33), and the chain also covers those [S45].
  - The `dev` page says: "The extension uses the AWS SDK default credentials provider chain." and "Do not configure AWS credentials in `application.properties`." [S10]. These are verbatim quotes, so they count as High under R13.
  - IAM: "To call `Converse`, you require permission for the `bedrock:InvokeModel` operation. To call `ConverseStream`, you require permission for the `bedrock:InvokeModelWithResponseStream` operation." [S44]. That LangChain4j's `BedrockChatModel`/`BedrockStreamingChatModel` call Converse/ConverseStream is (medium confidence): the LangChain4j page only says `requestMetadata` is added to "Converse and ConverseStream requests" [S49].
- Code:
  ```properties
  # Quarkus 3.40 + quarkus-langchain4j-bedrock 1.15.0.CR1 — Lambda role, no key
  # no quarkus.langchain4j.bedrock.aws.credentials-provider / region => SDK default chains (role, AWS_REGION)
  quarkus.langchain4j.bedrock.chat-model.model-id=<explicit model or inference-profile id>   # see Q3
  ```
  ```json
  { "Effect": "Allow",
    "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
    "Resource": "<model / inference-profile ARNs — exact ARN forms: U4>" }
  ```
  IAM is written in Terraform by `provisioning-aws-iam-*-v6` (R4). The JSON above shows only the actions.
- Source: [S31] [S27] [S45] [S43] [S44] [S10] (2026-10-28)

**A3. Budget every model call under the API Gateway integration timeout, with explicit timeouts, retries and `@Timeout`**
> Confidence: 🟢 High for each limit and default | [✓✓ Triangulated | REST/HTTP API quota pages + recorder sources @1.15.0.CR1 + fault-tolerance guide (2026-10-28)]; the budget formula is an inference (medium confidence)
- Why:
  - Limits:
    - REST API: "50 milliseconds - 29 seconds for all integration types, including Lambda, Lambda proxy". It can be raised for Regional/private APIs only [S37].
    - HTTP API: "Maximum integration timeout | 30 seconds | No" [S38].
    - Lambda: default timeout "3 seconds", maximum "900 seconds (15 minutes)" [S42].
    - When the function errors, API Gateway returns 500/502 and "does not retry" (FF38).
    - Which status a gateway timeout returns (504) was not re-read here (U8).
  - Provider defaults:
    - OpenAI/Anthropic: `.timeout(openAiConfig.timeout().orElse(Duration.ofSeconds(10)))` and the Anthropic equivalent [S20][S23].
    - `max-retries` default `1`, documented as "1 means exactly one attempt, with retrying disabled." [S18][S22].
    - Bedrock: SDK `max-retries` 3 (`firstOrDefault(3, ...)`), `api-call-timeout` (whole call "including retries"), `client.timeout` (read) `10s`, `client.connect-timeout` `3s` [S27][S29][S31].
  - Recommended mechanism: MicroProfile Fault Tolerance. The deprecation javadoc says "Using the fault tolerance mechanisms built in Langchain4j is not recommended. If possible, use MicroProfile Fault Tolerance instead." [S22]. The guide's example: `@Timeout(value = 60, unit = ChronoUnit.SECONDS)`. That 60 s is **the guide's example** (R11), so on an API Gateway route it must be lowered below 29/30 s [S12].
  - Rule of thumb (medium confidence): `@Timeout` < gateway timeout - Quarkus/Lambda overhead; provider `timeout x attempts` < `@Timeout`; Lambda timeout ≥ gateway timeout, so the function is not killed before the gateway answers.
- Code:
  ```properties
  # Quarkus 3.40 + quarkus-langchain4j 1.15.0.CR1 — example values for a REST API route (29 s)
  quarkus.langchain4j.openai.timeout=20s                 # default 10s (fallback in OpenAiRecorder)
  quarkus.langchain4j.anthropic.timeout=20s              # default 10s (fallback in AnthropicRecorder)
  quarkus.langchain4j.bedrock.client.timeout=20s         # read timeout, doc default 10s
  quarkus.langchain4j.bedrock.aws.api-call-timeout=24s   # set explicitly: doc says 13s, code falls back to 10s (C3)
  quarkus.langchain4j.bedrock.aws.max-retries=1          # doc/code default 3; retries share api-call-timeout
  ```
  ```java
  // Quarkus 3.40 + quarkus-langchain4j 1.15.0.CR1 + quarkus-smallrye-fault-tolerance
  @RegisterAiService
  public interface SupportAssistant {
      @Timeout(value = 25, unit = ChronoUnit.SECONDS)   // below the 29 s REST API limit (guide example used 60 s)
      @Fallback(fallbackMethod = "fallback")
      String answer(@UserMessage String question);
      default String fallback(String question) { return "The assistant is unavailable, try again."; }
  }
  ```
  Whether the property key spellings above are exactly as shown: `openai.timeout` and `anthropic.timeout` derive from the tag-pinned config interfaces [S18][S21]. `bedrock.client.timeout` and `bedrock.aws.api-call-timeout` derive from the `dev` config table [S10] plus the tag-pinned interfaces [S27][S29] (High). Placing a `@Fallback` default method on an AI service interface follows the guide's pattern, but the exact signature is (medium confidence) [S12].
- Source: [S37] [S38] [S42] [S18] [S20] [S22] [S23] [S27] [S29] [S31] [S12] (2026-10-28), FF38

**A4. API keys (OpenAI, Anthropic) come from Secrets Manager/SSM at init, never from properties, code or Lambda environment variables**
> Confidence: 🟢 High for the rule | [✓✓ Triangulated | Lambda env-var page + quarkus-langchain4j security page (verbatim) + R5 + U5 internal research]; the exact config-source mapping for `quarkus.langchain4j.*` keys is (medium confidence)
- Why:
  - Lambda: "we recommend that you use AWS Secrets Manager instead of environment variables to store database credentials and other sensitive information like API keys" [S43].
  - Extension: "Never embed API keys, or other credentials directly in your source code, prompts, or user-controlled inputs." [S16].
  - R5: LLM keys always come from Secrets Manager/SSM.
  - The Quarkiverse Secrets Manager config source maps a property to a secret name (`quarkus.secretsmanager.config.secrets."<property>"=<secret-name>`). It is "loaded once at startup", it is off by default, and it should be mapped explicitly in production [I1, U5 A10/Q1].
  - Applying it to `quarkus.langchain4j.openai.api-key` assumes the key is resolved after the config source is active. The extension pages do not state this (U2). Fallback: a custom `ModelAuthProvider` bean, which can "load tokens or API keys from the database or other sources" [S16]. The recorders look up a `ModelAuthProvider` before the dummy-key check [S23].
- Code:
  ```properties
  # Quarkus 3.40 + quarkus-amazon-secretsmanager (Quarkiverse 3.23.0, FF17) + quarkus-langchain4j-openai 1.15.0.CR1
  quarkus.secretsmanager.config.enabled=true
  quarkus.secretsmanager.config.secrets."quarkus.langchain4j.openai.api-key"=prod/llm/openai-api-key
  quarkus.secretsmanager.config.secrets."quarkus.langchain4j.anthropic.api-key"=prod/llm/anthropic-api-key
  # never: quarkus.langchain4j.openai.api-key=sk-... ; never: Lambda env QUARKUS_LANGCHAIN4J_OPENAI_API_KEY
  ```
- Source: [S43] [S16] [S20] [S23] (2026-10-28), [I1], R5

**A5. On a synchronous API Gateway route, AI service methods return `String`/POJO, not `Multi<String>`**
> Confidence: 🟢 High | [✓✓ Triangulated | LambdaHttpHandler.java @3.40.1.1 (verbatim) + Lambda response-streaming page + HTTP vs REST page (2026-10-28)]; the REST-extension handler is (medium confidence)
- Why:
  - The 3.40.1.1 HTTP handler buffers: `baos = new ByteArrayOutputStream(BUFFER_SIZE);`, `if (msg instanceof LastHttpContent) {`, `responseBuilder.setBody(baos.toString(StandardCharsets.UTF_8));`, `future.complete(responseBuilder);`. The caller blocks on `return handler.getFuture().get();` [S46].
  - AWS: "Lambda supports response streaming on Node.js managed runtimes. For other languages ... use a custom runtime with a custom Runtime API integration" [S41]. HTTP API: "Response streaming | Yes (REST) | No (HTTP)" [S39]. REST API streaming needs `InvokeWithResponseStream` plus a metadata/8-null-byte-delimiter output format [S40]. The Quarkus handler entry point is `QuarkusStreamHandler::handleRequest` (FF11), and no Quarkus page read here documents that format (U3).
  - Streaming models skip retries: `streamingChatModel` "never reads `maxRetries`" (OpenAI), and the Anthropic streaming builder "has no `.maxRetries(...)` call" [S20][S23]. These are tool summaries of tag-pinned code, (medium confidence) per R13; the non-streaming `.maxRetries(openAiConfig.maxRetries())` line is verbatim.
  - The streaming guide itself says "methods returning Multi are considered non-blocking. Do not use blocking code inside streaming pipelines." [S11].
- Code:
  ```java
  // Quarkus 3.40 (quarkus-amazon-lambda-http) + quarkus-langchain4j 1.15.0.CR1 — buffered anyway, so return the whole answer
  @Path("/assist")
  public class AssistResource {
      @Inject SupportAssistant assistant;
      @POST @Consumes(MediaType.TEXT_PLAIN) @Produces(MediaType.TEXT_PLAIN)
      public String assist(String question) { return assistant.answer(question); }
  }
  ```
- Source: [S46] [S41] [S39] [S40] [S20] [S23] [S11] (2026-10-28), FF11

**A6. Set every model name/ID explicitly; do not rely on defaults in a CR**
> Confidence: 🟢 High | [✓✓ Triangulated | tag config sources + tag AsciiDoc + dev docs (2026-10-28)]
- Why: defaults differ between layers.
  - OpenAI `@WithDefault("gpt-4o-mini")` at both 1.15.0.CR1 and 1.14.2 [S19][S36], while the `dev` table shows `gpt-6-luna` [S8] (C1).
  - Anthropic `@WithDefault("claude-3-haiku-20240307")` [S22], while the tag AsciiDoc says "By default, the extension uses the latest available Claude model." [S34] (C2).
  - Bedrock `@ConfigDocDefault("global.amazon.nova-2-lite-v1:0")` on `Optional<String> modelId()`. This is documentation only, with no `@WithDefault` [S28]; the runtime fallback was not traced (U5).
- Code:
  ```properties
  # quarkus-langchain4j 1.15.0.CR1 — explicit model per provider (values are examples)
  quarkus.langchain4j.openai.chat-model.model-name=<chosen OpenAI model>
  quarkus.langchain4j.anthropic.chat-model.model-name=<chosen Claude model>
  quarkus.langchain4j.anthropic.chat-model.max-tokens=1024      # default 1024
  quarkus.langchain4j.bedrock.chat-model.model-id=<chosen model or inference-profile id>
  ```
- Source: [S19] [S22] [S28] [S34] [S36] [S8] (2026-10-28)

**A7. Keep prompt/completion out of spans and logs (the defaults), and keep metric dimensions bounded**
> Confidence: 🟢 High | tag-pinned config sources + verbatim security/observability quotes (2026-10-28) + R7
- Why:
  - `TracingConfig` at the tag has `@WithDefault("false")` on `includePrompt`, `includeCompletion`, `includeToolArguments` and `includeToolResult` [S25].
  - `quarkus.langchain4j.log-requests`/`log-responses` have doc default `false` [S24].
  - Security page: "Avoid logging full prompts and responses unless absolutely necessary for auditing." and "remove any Personally Identifiable Information (PII) or other sensitive details." [S16]. R7: no PII.
  - The `gen_ai.client.token.usage` metric uses a `gen_ai.token.type` dimension [S15]. Adding tenant ids as tags needs an ADR (R7).
- Code:
  ```properties
  # quarkus-langchain4j 1.15.0.CR1 — production profile (explicit = documented defaults)
  quarkus.langchain4j.tracing.include-prompt=false
  quarkus.langchain4j.tracing.include-completion=false
  quarkus.langchain4j.log-requests=false
  quarkus.langchain4j.log-responses=false
  ```
- Source: [S25] [S24] [S16] [S15] (2026-10-28), R7

**A8. Tests never call a real provider: mock the AI service bean, or point the provider at WireMock**
> Confidence: 🟢 High | [✓✓ Triangulated | RegisterAiService.java @tag + Quarkus 3.40 testing guide + model-mocking guide + parent POM wiremock version (2026-10-28)]
- Why:
  - AI service beans are `@RequestScoped` by default [S26]. "By default, the `@InjectMock` annotation can be used for any normal CDI scoped bean", via `quarkus-junit-mockito` [S47].
  - WireMock guide: the extension "starts a local HTTP server as a Dev Service in dev and test mode". Starting it "does not automatically redirect model calls", so `base-url` must be overridden: `%test.quarkus.langchain4j.openai.base-url=http://localhost:${quarkus.wiremock.devservices.port}/v1`. Also, "No internal Quarkus LangChain4j testing modules are required" [S13]. The guide's `quarkus-wiremock` version 1.5.1 matches the parent POM property [S1].
  - The OpenAI dummy-key check applies only with the default base URL [S20], so a WireMock base URL plus a placeholder key starts cleanly.
  - Lambda-level tests use the mock event server with `quarkus-junit` + RestAssured; `quarkus-test-amazon-lambda` was removed in 3.31 (FF23, FF14).
- Code:
  ```java
  // Quarkus 3.40 + quarkus-junit-mockito + quarkus-langchain4j 1.15.0.CR1
  @QuarkusTest
  class AssistResourceTest {
      @InjectMock SupportAssistant assistant;           // @RequestScoped by default => mockable
      @Test void answers() {
          Mockito.when(assistant.answer("hi")).thenReturn("hello");
          given().contentType("text/plain").body("hi").post("/assist")
                 .then().statusCode(200).body(is("hello"));
      }
  }
  ```
- Source: [S26] [S47] [S13] [S1] [S20] (2026-10-28), FF14, FF23

**A9. Keep chat memory per request (the default) on Lambda; persistent memory is a separate, explicit decision**
> Confidence: 🟢 High for the defaults | tag AsciiDoc + tag RegisterAiService.java (2026-10-28); the Lambda consequence is (medium confidence)
- Why:
  - "Memory is request-scoped by default; configure using `chatMemoryProviderSupplier`." and "Default memory provider: `MessageWindowChatMemory` with 10-message window." [S35].
  - The bean is `@RequestScoped` by default, and "If you need to change the scope, simply annotate the class with a CDI scope." [S26].
  - Lambda: the JVM is per execution environment, so in-JVM memory is neither shared across environments nor durable (medium confidence: inference). Memory stores (Redis/MongoDB) are listed in the docs nav [S6] but are out of this unit's research scope.
- Source: [S35] [S26] [S6] (2026-10-28)

**A10. Treat `@Tool` as a boundary: each tool round trip is another model call inside the same time budget**
> Confidence: 🟢 High for the quotes; budget consequence (medium confidence)
- Why:
  - "Tools must be part of a CDI bean and annotated with `@Tool`." Tools are registered with `@ToolBox` or `@RegisterAiService(tools=…)` [S17].
  - `maxSequentialToolInvocations() default 10` is deprecated in favour of `maxToolCallingRoundTrips()` [S26].
  - Fault-tolerance guide: "Use `@Retry` (and `@CircuitBreaker`) carefully when your AI service registers tools." [S12].
  - "Security annotations such as `@RolesAllowed` on a tool method of a CDI bean are enforced" [S17]. Tenant isolation (R6) therefore still applies inside tools.
  - Full `@Tool` design is out of scope for this unit.
- Source: [S17] [S26] [S12] (2026-10-28), R6

### ⚠️ Conditional Patterns

**Q1. Which provider(s) per function, and how to select one when several are on the classpath**
> Confidence: 🟢 High for the syntax quotes; provider names `anthropic`/`bedrock` in `chat-model.provider` (medium confidence)
- Options: (A) exactly one provider extension per function, the simplest: the AI service uses "the default model" [S7]; (B) several providers with named models. "when multiple model providers are present in the application (such as OpenAI, Azure OpenAI, HuggingFace, etc.)" "each model needs to be given a name, which is then referenced by the AI service" [S35]. Tag example: `quarkus.langchain4j.m1.chat-model.provider=openai` [S35], plus `@RegisterAiService(modelName = "m1")` [S26]. Provider-specific keys then take the name, e.g. `quarkus.langchain4j.openai.my-model.chat-model.model-name=…` [S6 models page].
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A one provider | smallest package, fewest secrets/IAM paths | no failover across vendors | one vendor contract per function |
  | B named models | vendor choice / fallback per method | more config, more secrets, larger cold start (unquantified) | routing tasks to different models |

- Agent: "Ask the user which provider(s) each function uses; with Bedrock-only no API key exists at all."
- Source: [S7] [S35] [S26] (2026-10-28)

**Q2. Timeout and retry budget split (values)**
> Confidence: 🟡 Medium (values are design choices; limits are High, see A3)
- Options: (A) single attempt with a long timeout (OpenAI/Anthropic default retries = none [S18][S22]); (B) MicroProfile `@Retry` plus a short per-attempt timeout under `@Timeout` [S12]; (C) asynchronous path: API Gateway → SQS → Lambda (up to 900 s [S42]) with the result stored and fetched later. Messaging belongs to U5.
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A | simple, one bill per call | no recovery from a transient 5xx | short prompts, fast models |
  | B | resilience | each retry eats the 29/30 s budget; tools plus retry repeats side effects [S12] | idempotent, tool-free prompts |
  | C | long generations, no 29/30 s cap | async UX, extra infra | long outputs, batch |

- Agent: "Ask the expected p99 model latency and output length before choosing; if p99 > ~20 s, propose C."
- Source: [S18] [S22] [S12] [S42] [S37] [S38] (2026-10-28)

**Q3. Bedrock model ID vs cross-Region inference profile (`global.` / `us.` prefixes)**
> Confidence: 🟡 Medium
- Options: (A) a plain model ID; (B) an inference-profile ID such as the doc default `global.amazon.nova-2-lite-v1:0` [S28] or the `dev` example `us.anthropic.claude-opus-4-7` [S10].
- Tradeoffs: profiles may route across Regions (data residency), and the IAM `Resource` ARNs differ (U4, not read).
- Agent: "Ask the data-residency constraint and the exact model; then write the matching IAM resources in Terraform."
- Source: [S28] [S10] (2026-10-28)

**Q4. JVM + SnapStart vs native for a LangChain4j Lambda (R3: always an ADR)**
> Confidence: 🟡 Medium
- Options:
  - (A) JVM + SnapStart. Managed Java runtimes only, so not native (FF16). Restore-time limit quotes: FF21. Use `quarkus.snapstart.enabled` (FF22). Credentials under SnapStart: FF33. Secrets loaded at init end up in the snapshot (see [I2] U7 for the same effect with Stripe keys).
  - (B) native on `provided.al2023` (FF13, FF20).
  - No quarkus-langchain4j page read here documents native or SnapStart. LangChain4j's own framework page lists "Ability to compile to a GraalVM native binary" [S48]. The Anthropic runtime module ships a `graalvm` package at the tag [S50]. Both are indirect, so (medium confidence) (U6).
  - Whether the providers' Vert.x/REST-client connections survive a SnapStart restore is (unverified) (U7).
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | A JVM+SnapStart | documented Java runtime, no native build | snapshot holds init state incl. secrets; restore behaviour of HTTP pools unverified | default candidate, subject to ADR |
  | B native | fast cold start, no snapshot | native support of the three providers not documented on the pages read | after a native integration test passes |

- Agent: "Ask for an ADR; do not default either way (R3)."
- Source: [S48] [S50] (2026-10-28), FF13, FF16, FF20-FF22, FF33, [I2]

**Q5. OpenAI API mode: Chat Completions vs Responses**
> Confidence: 🟢 High for the tag statement; `dev` behaviour differs (C4)
- Options: (A) the tag default, quoted as "By default, the chat model targets OpenAI's `/v1/chat/completions` endpoint." [S33]; (B) Responses API, set by "the build-time `mode` property" [S33], needed for models "only exposed through it (for example `gpt-5-pro`, `o1-pro`)" [S33].
- Tradeoffs: on `dev`, `max-retries` "is deprecated and is **not honored** on the Responses API" [S8] (dev only, verbatim). Mode is build-time, so it cannot be switched per environment at runtime [S33].
- Agent: "Ask the model; if it is Responses-only, set mode explicitly and use MicroProfile retries (A3)."
- Source: [S33] [S8] (2026-10-28)

**Q6. Secret loading mechanism**
> Confidence: 🟡 Medium
- Options: (A) the Secrets Manager config source mapped onto `quarkus.langchain4j.<provider>.api-key` (A4; ordering assumption U2); (B) a `ModelAuthProvider` CDI bean that reads the secret through an injected `SecretsManagerClient` [S16][S23]; (C) the AWS Parameters and Secrets Lambda Extension ([I1] U5 Q1).
- Tradeoffs: A loads once at startup (snapshot-frozen under SnapStart, so rotation needs a new version [I1][I2]). B allows a refresh policy but is custom code. C costs an HTTP hop per fetch.
- Agent: "Ask the rotation requirement; pick A when no rotation without redeploy is needed."
- Source: [S16] [S23] (2026-10-28), [I1], [I2]

**Q7. Metrics and tracing export path**
> Confidence: 🟢 High for the extension hooks; the AWS export path belongs to the metrics/tracing units
- Options:
  - Metrics: "Metrics are enabled when `quarkus-micrometer` is part of the application" (`langchain4j.aiservices.timed`, `langchain4j.aiservices.counted`, `gen_ai.client.token.usage`) [S15]. There is no Quarkiverse CloudWatch Micrometer registry (FF39); the export choice is owned by the metrics unit.
  - Traces: "Traces are enabled when `quarkus-opentelemetry` is part of the application"; spans use `langchain4j.aiservices.$interface_name.$method_name` [S15]. X-Ray SDK vs OpenTelemetry is an ADR (FF34).
  - Events: `AiServiceStartedEvent`, `AiServiceCompletedEvent`, `AiServiceErrorEvent`, … correlated by `event.invocationContext().invocationId()`. Also, "The Quarkus-specific auditing features have been deprecated and removed." [S15].
- Agent: "Ask which telemetry backend the family ADR selected before adding exporters."
- Source: [S15] (2026-10-28), FF34, FF39, FF42

### 🚫 Forbidden Patterns

**F1. API key in `application.properties`, source code or a Lambda environment variable**
> Severity: Critical
> Confidence: 🟢 High
- Why: AWS recommends Secrets Manager "instead of environment variables" for API keys [S43]. The extension says "Never embed API keys, or other credentials directly in your source code" [S16]. R5 applies.
- Impact: key leakage via Git, the Lambda console or config dumps; vendor account abuse ("leaking them can lead to unauthorized access and abuse of your account" [S16]).
- ❌ Wrong:
  ```properties
  quarkus.langchain4j.openai.api-key=sk-live-...          # committed
  # or Lambda env QUARKUS_LANGCHAIN4J_OPENAI_API_KEY=sk-live-...
  ```
- ✅ Correct:
  ```properties
  quarkus.secretsmanager.config.enabled=true
  quarkus.secretsmanager.config.secrets."quarkus.langchain4j.openai.api-key"=prod/llm/openai-api-key
  ```
  The config-source mechanism itself is High per U5 [I1]; its ordering with the LangChain4j keys is (medium confidence), and the alternative is in Q6 (R9).
- Source: [S43] [S16] (2026-10-28), [I1], R5

**F2. Static AWS keys (or any credentials) for Bedrock**
> Severity: Critical
> Confidence: 🟢 High
- Why: Lambda already supplies execution-role credentials [S43], and the extension uses the default chain when nothing is configured [S31][S27]. The `dev` docs: "Do not configure AWS credentials in `application.properties`." [S10].
- Impact: long-lived keys outside IAM rotation; breaks SnapStart's container-credential path (FF33).
- ❌ Wrong:
  ```properties
  quarkus.langchain4j.bedrock.aws.credentials-provider=staticKeys   # bean holding AKIA... keys
  ```
- ✅ Correct:
  ```properties
  # nothing: SDK default chain => Lambda execution role; grant bedrock:InvokeModel (+ InvokeModelWithResponseStream) to the role
  ```
- Source: [S43] [S31] [S27] [S10] [S44] (2026-10-28), FF33

**F3. Exposing an SSE / `Multi<String>` AI endpoint through API Gateway + Quarkus Lambda and expecting incremental delivery**
> Severity: High
> Confidence: 🟢 High (HTTP extension, verbatim code); REST extension (medium confidence)
- Why: the handler buffers until `LastHttpContent` [S46]; HTTP API has no response streaming [S39]; the Java managed runtime has no native streaming [S41]; streaming models get no `maxRetries` [S20][S23] (medium confidence, tool summary of tag code).
- Impact: no time-to-first-byte gain; the full generation must still finish within 29/30 s [S37][S38]; transient provider errors are not retried. How a `text/event-stream` body is encoded (text vs base64) depends on the handler's `isText(Content-Type)` check, which is (unverified) for SSE (U9).
- ❌ Wrong:
  ```java
  @POST @Produces(MediaType.SERVER_SENT_EVENTS)
  public Multi<String> stream(String q) { return assistant.respondToQuestion(q); }   // behind API Gateway + Lambda
  ```
- ✅ Correct:
  ```java
  @POST @Produces(MediaType.TEXT_PLAIN)
  public String answer(String q) { return assistant.answer(q); }   // blocking, bounded by @Timeout (A3)
  ```
- Source: [S46] [S39] [S41] [S11] [S37] [S38] (2026-10-28)

**F4. Turning on request/response logging or prompt/completion tracing in production**
> Severity: High
> Confidence: 🟢 High
- Why: the defaults are off [S24][S25]; "Avoid logging full prompts and responses unless absolutely necessary for auditing." [S16]; R7 forbids PII in logs. Whether request logging masks the `Authorization` / `x-api-key` header was not verified (U10), which makes it riskier.
- Impact: PII and possibly credentials in CloudWatch Logs or trace backends.
- ❌ Wrong:
  ```properties
  quarkus.langchain4j.log-requests=true
  quarkus.langchain4j.tracing.include-prompt=true
  ```
- ✅ Correct:
  ```properties
  %dev.quarkus.langchain4j.log-requests=true      # dev profile only
  quarkus.langchain4j.tracing.include-prompt=false # default
  ```
- Source: [S24] [S25] [S16] (2026-10-28), R7

**F5. Provider timeout or `@Timeout` larger than the API Gateway integration timeout**
> Severity: High
> Confidence: 🟢 High (limits); impact detail (medium confidence)
- Why: REST APIs allow up to 29 s (Regional/private raisable with throttle trade-off) and HTTP APIs 30 s with no increase [S37][S38]. The fault-tolerance guide's 60 s value is an example, not a default [S12] (R11).
- Impact: API Gateway answers before the function does; the Lambda keeps running (and billing) until it finishes or hits its own timeout (medium confidence; the exact gateway timeout status was not re-read, U8).
- ❌ Wrong:
  ```java
  @Timeout(value = 60, unit = ChronoUnit.SECONDS)   // copied from the guide, behind a 29 s REST API
  ```
- ✅ Correct:
  ```java
  @Timeout(value = 25, unit = ChronoUnit.SECONDS)   // < 29 s, provider timeout x attempts below this
  ```
- Source: [S37] [S38] [S12] (2026-10-28)

**F6. Mixing LangChain4j versions: overriding `langchain4j.version` to the plain-Java family's 1.22.0**
> Severity: High
> Confidence: 🟡 Medium (the pin is High; the breakage is not verified)
- Why: 1.15.0.CR1 is built and tested against `<langchain4j.version>1.21.0</langchain4j.version>` [S1]; version absolutism means one LangChain4j version per application.
- Impact: binary incompatibilities between the extension and core LangChain4j classes (unverified, U1).
- ❌ Wrong:
  ```xml
  <dependency><groupId>dev.langchain4j</groupId><artifactId>langchain4j</artifactId><version>1.22.0</version></dependency>
  ```
- ✅ Correct:
  ```xml
  <!-- no explicit dev.langchain4j versions; import io.quarkiverse.langchain4j:quarkus-langchain4j-bom:1.15.0.CR1 -->
  ```
- Source: [S1] [S5d] (2026-10-28)

**F7. Making an AI service `@ApplicationScoped`/`@Singleton` with the default chat memory in a multi-tenant function**
> Severity: Critical (R6)
> Confidence: 🟡 Medium (inference from verbatim scope/memory quotes)
- Why: memory "is managed using CDI-scope" when no supplier is set [S7], and the bean scope can be changed by annotation [S26]. An application-wide scope would therefore keep one 10-message window across requests, and in Lambda across tenants served by the same environment (inference). R6: tenant isolation violations are 🚫.
- Impact: one tenant's conversation context leaks into another tenant's prompt.
- ❌ Wrong:
  ```java
  @ApplicationScoped
  @RegisterAiService
  public interface SupportAssistant { String answer(@UserMessage String q); }
  ```
- ✅ Correct:
  ```java
  @RegisterAiService            // @RequestScoped by default: memory lives for one request
  public interface SupportAssistant { String answer(@UserMessage String q); }
  ```
- Source: [S7] [S26] [S35] (2026-10-28), R6

**F8. Real provider calls in unit/integration tests**
> Severity: Medium
> Confidence: 🟢 High
- Why: tests must be deterministic and must not spend vendor quota. WireMock is the documented way to test model HTTP calls "without calling a real model" [S14][S13]. AI services are mockable via `@InjectMock` [S26][S47].
- Impact: flaky tests, cost, keys needed in CI.
- ❌ Wrong:
  ```properties
  %test.quarkus.langchain4j.openai.api-key=${OPENAI_API_KEY}   # real key, real endpoint
  ```
- ✅ Correct:
  ```properties
  %test.quarkus.langchain4j.openai.base-url=http://localhost:${quarkus.wiremock.devservices.port}/v1
  %test.quarkus.langchain4j.openai.api-key=test-key
  ```
- Source: [S13] [S14] [S26] [S47] (2026-10-28)

---

## Migration Guide

> Confidence: 🟢 High for the listed changes | Sources: release 1.15.0.CR1 [S2] (2026-10-28) + release 1.14.2 [S3] (2026-10-28) + parent POMs [S1][S4]

**Breaking Changes (1.14.x → 1.15.0.CR1)**: the release notes list none and have no breaking-changes section [S2]. Listed changes:
- "Upgrade to Quarkus 3.40" (#2901)
- "Bump to Langchain4j 1.21.0 and support `DecisionModel`" (#2909)
- "JitLLM: move onto the JitLLM 1.0.2 facade and rename the extension from gpu-llama3" (#2888). Not used in this scope.
- "Remove the legacy HTTP/SSE transport from the MCP client guide" (#2904). MCP is out of scope.

The full 1.14.2...1.15.0.CR1 diff (24 commits, 337 files) could not be rendered by GitHub, so silent default changes cannot be excluded (G3). The spot-checked defaults are identical at 1.14.2 and 1.15.0.CR1: OpenAI `gpt-4o-mini`; Bedrock `modelId` doc default, `temperature`, `maxTokens` 1024, `topP` [S36].

**Deprecated APIs / keys (at tag 1.15.0.CR1)**:
- `quarkus.langchain4j.openai.max-retries` and `quarkus.langchain4j.anthropic.chat-model.max-retries`: deprecated; use MicroProfile Fault Tolerance [S18][S22].
- OpenAI `proxy-type` / `proxy-host` / `proxy-port`: `@Deprecated(forRemoval = true)`; use `proxy-configuration-name` [S18]. Bedrock proxy keys likewise [S29].
- OpenAI `chat-model.max-tokens`: `@Deprecated`; `max-completion-tokens` exists [S19].
- `@RegisterAiService.maxSequentialToolInvocations` (default 10): deprecated, replaced by `maxToolCallingRoundTrips()` [S26].
- "The Quarkus-specific auditing features have been deprecated and removed." Use the `AiService*Event` CDI events [S15].

**Pre-release → final (1.15.0)**: re-run the defaults check (C1-C4) on the final tag; dev docs already show changes not in the CR (OpenAI `mode` auto-selection, `gpt-6-luna`) [S8].

**Upgrade Steps** (Representative — adapt to your environment):
1. Move the application to Quarkus 3.40 (`quarkus-bom` 3.40.x, FF8, FF9).
2. Set the quarkus-langchain4j BOM/extension version to `1.15.0.CR1` [S5]. Remove any explicit `dev.langchain4j:*` versions (F6).
3. Replace `max-retries` reliance with `quarkus-smallrye-fault-tolerance` annotations sized to the gateway budget (A3).
4. Set model names and IDs explicitly (A6) and OpenAI `mode` explicitly if needed (Q5).
5. `./mvnw verify` with WireMock/mocks (A8); then build `function.zip` (R4, FF10).

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Quarkus | 3.40.0 (parent POM) | 3.40.x LTS (patch 3.40.1.1 pairing not stated, medium confidence) | [S1], FF8 |
| LangChain4j (core) | 1.21.0 | 1.21.0 | managed by the extension [S1]; NOT 1.22.0 (F6) |
| quarkus-wiremock (tests) | 1.5.1 | 1.5.1 | parent POM property and guide [S1][S13] |
| Quarkiverse amazon-services | 3.23.0 | 3.23.x | for Secrets Manager/SSM only (FF17); AWS SDK alignment with `langchain4j-bedrock` (unverified, U11) |
| Lambda Java runtime | java17.al2023 / java21 / java25 | — | FF15; native: `provided.al2023` (FF13) |

---

## Implementation Blueprint

> Confidence: 🟢 High for the extension pieces [✓✓ tag sources + docs]; Lambda wiring per family facts

**Lifecycle** (Quarkus 3.40 + quarkus-langchain4j 1.15.0.CR1 on Lambda):
```text
Init (cold start or SnapStart snapshot):
  Quarkus boots -> Secrets Manager config source loads mapped secrets once [I1]
  -> provider recorders build ChatModel / StreamingChatModel beans (OpenAI/Anthropic: dummy-key check, SRCFG00014 if unset [S20][S23];
     Bedrock: BedrockRuntimeClient / BedrockRuntimeAsyncClient via BedrockSdkHttpClientFactory [S31])
Invoke (API Gateway -> QuarkusStreamHandler::handleRequest, FF11):
  REST resource (worker thread) -> @RequestScoped AI service [S26] -> model call (timeout/attempts, A3)
  -> full response buffered by LambdaHttpHandler -> one API Gateway response [S46]
Freeze/thaw: the environment is reused; request-scoped memory is discarded per request [S35]
```

**Dependencies** (Representative):
```xml
<!-- Quarkus 3.40 LTS; quarkus-langchain4j 1.15.0.CR1 (PRE-RELEASE) -->
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-amazon-lambda-http</artifactId></dependency>            <!-- preview, FF25 -->
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-rest</artifactId></dependency>
<dependency><groupId>io.quarkiverse.langchain4j</groupId><artifactId>quarkus-langchain4j-bedrock</artifactId></dependency>
<dependency><groupId>io.quarkiverse.langchain4j</groupId><artifactId>quarkus-langchain4j-anthropic</artifactId></dependency>   <!-- only if used -->
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-smallrye-fault-tolerance</artifactId></dependency>     <!-- [S12] -->
<dependency><groupId>io.quarkiverse.amazonservices</groupId><artifactId>quarkus-amazon-secretsmanager</artifactId></dependency> <!-- only for API keys, [I1] -->
<!-- tests -->
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-junit</artifactId><scope>test</scope></dependency>
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-junit-mockito</artifactId><scope>test</scope></dependency>
<dependency><groupId>io.quarkiverse.wiremock</groupId><artifactId>quarkus-wiremock</artifactId><version>1.5.1</version><scope>provided</scope></dependency>
<dependency><groupId>io.quarkiverse.wiremock</groupId><artifactId>quarkus-wiremock-test</artifactId><version>1.5.1</version><scope>test</scope></dependency>
```
Bedrock does not need an extra AWS SDK HTTP client artifact. The extension excludes `netty-nio-client`, `url-connection-client` and `apache-client` from `langchain4j-bedrock` and builds its own through `BedrockSdkHttpClientFactory` with a `Supplier<Vertx>` [S32][S31]. That the factory is Vert.x-based is (medium confidence). This differs from the Quarkiverse amazon-services clients, where an HTTP client artifact must be added explicitly (FF28).

**Configuration reference: documented defaults per key (R10, R11)** at tag 1.15.0.CR1 unless noted. "Doc default" = `@ConfigDocDefault`; "runtime" = `@WithDefault` or recorder fallback.

| Key | Default | Source |
|---|---|---|
| `quarkus.langchain4j.timeout` | doc `10s` (no `@WithDefault`); recorders fall back to `Duration.ofSeconds(10)` | [S24] [S20] [S23] |
| `quarkus.langchain4j.log-requests` | doc `false` | [S24] |
| `quarkus.langchain4j.log-responses` | doc `false` | [S24] |
| `quarkus.langchain4j.log-requests-curl` | doc `false` | [S24] |
| `quarkus.langchain4j.temperature` | no documented default | [S24] |
| `quarkus.langchain4j.tracing.include-prompt` | `false` | [S25] |
| `quarkus.langchain4j.tracing.include-completion` | `false` | [S25] |
| `quarkus.langchain4j.tracing.include-tool-arguments` | `false` | [S25] |
| `quarkus.langchain4j.tracing.include-tool-result` | `false` | [S25] |
| `quarkus.langchain4j.openai.api-key` | `dummy` | [S18] |
| `quarkus.langchain4j.openai.base-url` | `https://api.openai.com/v1/` | [S18] |
| `quarkus.langchain4j.openai.timeout` | doc `10s` (`${quarkus.langchain4j.timeout}`) | [S18] |
| `quarkus.langchain4j.openai.max-retries` | `1` (deprecated) | [S18] |
| `quarkus.langchain4j.openai.log-requests` | doc `false` | [S18] |
| `quarkus.langchain4j.openai.log-responses` | doc `false` | [S18] |
| `quarkus.langchain4j.openai.enable-integration` | `true` | [S18] |
| `quarkus.langchain4j.openai.chat-model.model-name` | `gpt-4o-mini` (dev docs: `gpt-6-luna`, C1) | [S19] [S8] |
| `quarkus.langchain4j.openai.chat-model.temperature` | doc "the model's default" | [S19] |
| `quarkus.langchain4j.openai.chat-model.mode` | tag docs: Chat Completions by default, build-time; declaration/default value not located (G2); dev: `auto` | [S33] [S8] |
| `quarkus.langchain4j.anthropic.api-key` | `dummy` | [S21] |
| `quarkus.langchain4j.anthropic.base-url` | `https://api.anthropic.com/v1/` | [S21] |
| `quarkus.langchain4j.anthropic.version` | `2023-06-01` | [S21] |
| `quarkus.langchain4j.anthropic.timeout` | doc `10s` (`${quarkus.langchain4j.timeout}`) | [S21] |
| `quarkus.langchain4j.anthropic.log-requests` | doc `false` | [S21] |
| `quarkus.langchain4j.anthropic.log-responses` | doc `false` | [S21] |
| `quarkus.langchain4j.anthropic.enable-integration` | `true` | [S21] |
| `quarkus.langchain4j.anthropic.chat-model.model-name` | `claude-3-haiku-20240307` (tag AsciiDoc says "latest available", C2) | [S22] [S34] |
| `quarkus.langchain4j.anthropic.chat-model.max-tokens` | `1024` | [S22] |
| `quarkus.langchain4j.anthropic.chat-model.temperature` | doc `0.7` | [S22] |
| `quarkus.langchain4j.anthropic.chat-model.max-retries` | `1` (deprecated) | [S22] |
| `quarkus.langchain4j.bedrock.aws.region` | doc "default aws region provider chain" (not set in code unless configured) | [S27] [S31] |
| `quarkus.langchain4j.bedrock.aws.endpoint-override` | none | [S27] |
| `quarkus.langchain4j.bedrock.aws.credentials-provider` | doc "default aws credentials provider chain" (bean name) | [S27] [S31] |
| `quarkus.langchain4j.bedrock.aws.max-retries` | doc `3`; code `firstOrDefault(3, …)` | [S27] [S31] |
| `quarkus.langchain4j.bedrock.aws.api-call-timeout` | doc `13s`; code falls back to `Duration.ofSeconds(10)` (C3) | [S27] [S31] |
| `quarkus.langchain4j.bedrock.client.connect-timeout` | doc `3s` | [S29] |
| `quarkus.langchain4j.bedrock.client.timeout` | doc `10s` | [S29] |
| `quarkus.langchain4j.bedrock.client.keep-alive-enabled` | doc `true` | [S29] |
| `quarkus.langchain4j.bedrock.log-requests` | doc `false` | [S30] |
| `quarkus.langchain4j.bedrock.log-responses` | doc `false` | [S30] |
| `quarkus.langchain4j.bedrock.log-body` | doc `false` | [S30] |
| `quarkus.langchain4j.bedrock.chat-model.model-id` | doc `global.amazon.nova-2-lite-v1:0` (no `@WithDefault`, U5) | [S28] |
| `quarkus.langchain4j.bedrock.chat-model.temperature` | doc `0.7` | [S28] |
| `quarkus.langchain4j.bedrock.chat-model.max-tokens` | `1024` | [S28] |
| `quarkus.langchain4j.bedrock.chat-model.top-p` | doc `1.0` | [S28] |
| `quarkus.langchain4j.bedrock.chat-model.prompt-caching-ttl` | doc `5m` | [S28] |
| `quarkus.langchain4j.bedrock.enable-integration` | `true` (dev docs table) | [S10] (medium confidence: dev table via tool summary) |

Key spellings for Bedrock (`aws.*`, `client.*`) are taken from the `dev` config table [S10] and match the tag interfaces' method names [S27][S29][S30] (kebab-case mapping). High.

**Integration**: quarkus-langchain4j ↔ Amazon Bedrock on Lambda (Representative):
```java
// Quarkus 3.40 + quarkus-langchain4j-bedrock 1.15.0.CR1 — Bedrock with the Lambda role
@RegisterAiService                                   // @RequestScoped by default [S26]
public interface SupportAssistant {
    @SystemMessage("You answer questions about the customer's own account only.")
    @Timeout(value = 25, unit = ChronoUnit.SECONDS)  // < 29 s REST API (A3)
    String answer(@UserMessage String question);
}
```
```properties
quarkus.langchain4j.bedrock.chat-model.model-id=<explicit id>       # A6, Q3
quarkus.langchain4j.bedrock.client.timeout=20s
quarkus.langchain4j.bedrock.aws.api-call-timeout=24s
quarkus.langchain4j.bedrock.aws.max-retries=1
quarkus.lambda.handler=<only for plain handlers; HTTP extension routes via JAX-RS>   # FF11, U2 research
```

**Integration**: quarkus-langchain4j ↔ OpenAI/Anthropic with Secrets Manager: see A4. The provider names for Q1 multi-provider: `quarkus.langchain4j.m1.chat-model.provider=openai` [S35]. The values `anthropic` and `bedrock` are (medium confidence).

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (Quarkus 3.40, quarkus-langchain4j 1.15.0.CR1)
# Init:     ./mvnw -q dependency:tree -Dincludes=io.quarkiverse.langchain4j,dev.langchain4j
#           Expected: io.quarkiverse.langchain4j:* 1.15.0.CR1 and dev.langchain4j:* 1.21.0 only (A1, F6)
# Config:   grep -nE "api-key=|AKIA|sk-" src/main/resources/application.properties
#           Expected: no match (F1, F2)
# Logging:  grep -nE "log-requests=true|include-prompt=true" src/main/resources/application.properties
#           Expected: no match outside %dev. (F4)
# Timeouts: grep -nE "@Timeout\(value = ([3-9][0-9]|[0-9]{3,})" -r src/main/java
#           Expected: no match on API Gateway routes (F5)
# Test:     ./mvnw verify
#           Expected: BUILD SUCCESS, no outbound call to api.openai.com / api.anthropic.com / bedrock-runtime (A8)
# Package:  ./mvnw package  -> target/function.zip (FF10)
```

**Mocking**:
```java
// Quarkus 3.40 + quarkus-wiremock 1.5.1 + quarkus-langchain4j-openai 1.15.0.CR1 — model HTTP level (pattern from [S13])
// %test.quarkus.langchain4j.openai.base-url=http://localhost:${quarkus.wiremock.devservices.port}/v1
// %test.quarkus.langchain4j.openai.api-key=test-key
// %test.quarkus.langchain4j.openai.chat-model.model-name=gpt-4o-mini
@QuarkusTest
class ModelContractTest {
    @Inject ChatModel model;
    @ConnectWireMock WireMock wiremock;   // annotation name per quarkus-wiremock-test (medium confidence; guide shows wiremock.verifyThat)
    @Test void callsChatCompletions() {
        assertEquals("Hello from WireMock!", model.chat("Hello"));
        wiremock.verifyThat(1, postRequestedFor(urlPathEqualTo("/v1/chat/completions")));
    }
}
```
- The guide covers OpenAI Chat Completions only. For other providers it says "Other HTTP model providers can use the same approach, but need mappings that match their own URLs and response formats." [S13].
- For Bedrock, the HTTP-level equivalent would use `quarkus.langchain4j.bedrock.aws.endpoint-override` [S27] with Converse-shaped stubs; this is not documented (unverified, U9). The documented safe default for Bedrock tests is therefore `@InjectMock` of the AI service (A8).
- No Dev Services for OpenAI/Anthropic/Bedrock were found on the pages read (U9).
- `enable-integration=false` "Set to `false` to disable all requests." [S8]. This is a verbatim `dev` quote; the tag key exists [S18][S21].

---

## Production Readiness

- **Performance**:
  - Model latency dominates and is unbounded by the library, so it must be bounded (A3).
  - Init cost of provider clients and secret fetches is unquantified (U7).
  - Bedrock keep-alive is on by default [S29].
  - Streaming brings no TTFB gain on Lambda (A5).
- **Scalability**: each Lambda environment handles one request at a time (family U1); vendor rate limits are per account/key (not read here). Use Q2-C for long generations.
- **Monitoring**:
  - [ ] `langchain4j.aiservices.timed` / `.counted` and `gen_ai.client.token.usage` with `quarkus-micrometer` [S15]. Export path per FF39 and the metrics unit.
  - [ ] AI-service spans `langchain4j.aiservices.$interface_name.$method_name` with `quarkus-opentelemetry` [S15], with ADR per FF34.
  - [ ] `AiServiceErrorEvent` observer that logs the `invocationId` + `requestId`/`tenantId` (R7), no prompt text [S15].
  - [ ] Optional `gen_ai.client.estimated_cost` "when a `CostEstimator` bean is available" [S15].
- **Error handling**: map provider failures and `@Timeout` to a controlled 5xx/503 body; an uncaught exception becomes a Lambda error and API Gateway answers 502 (FF38). Watch the `@Fallback` behaviour with tools [S12].
- **Security**:
  - [ ] Bedrock: role-only, two actions, least-privilege resources (A2, U4).
  - [ ] OpenAI/Anthropic keys from Secrets Manager/SSM (A4, F1). Rotation under SnapStart needs a new published version ([I2], FF33).
  - [ ] Logging and prompt tracing off; PII removed before sending ("remove any Personally Identifiable Information (PII)" [S16]).
  - [ ] Prompt-injection hygiene: "Clearly separate instructions from user-provided data in your prompts." [S16].
  - [ ] Tenant id from the token, never from the prompt or path (R6); tools enforce `@RolesAllowed` [S17].
  - [ ] AI service stays `@RequestScoped` (F7).

---

## Reference Implementations

- Quarkiverse docs (dev): AI Services, Models, provider pages, streaming, fault tolerance, testing, observability, security [S6-S17]
- Tag-pinned docs sources: https://github.com/quarkiverse/quarkus-langchain4j/tree/1.15.0.CR1/docs/modules/ROOT/pages [S33-S35]
- Tag-pinned provider runtime sources (defaults, recorders) [S18-S32]
- Release notes 1.15.0.CR1 mention "Add a GitHub pull request code reviewer sample" (#2903) [S2]. Not read; it is not Lambda-specific.
- Quarkus 3.40 AWS Lambda HTTP handler source (buffering) [S46]; family research U1/U2 for Lambda packaging and HTTP mapping.

---

## Research Gaps

```
Gap: U1 — whether quarkus-langchain4j-bom 1.15.0.CR1 manages every dev.langchain4j:* artifact, and the effect of overriding to 1.22.0
Impact: F6 rated Medium
Workaround: no explicit dev.langchain4j versions; check mvn dependency:tree
Follow-up: https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-bom/1.15.0.CR1/
§7-ref: open (unverified)

Gap: U2 — config phase of quarkus.langchain4j.<provider>.api-key vs Secrets Manager config source availability
Impact: A4/F1 mapping (medium confidence)
Workaround: ModelAuthProvider bean (Q6-B)
Follow-up: @ConfigRoot phase in LangChain4jOpenAiConfig / LangChain4jAnthropicConfig at tag; integration test
§7-ref: open (unverified)

Gap: U3 — any Quarkus 3.40 support for Lambda response streaming (InvokeWithResponseStream format)
Impact: F3 conclusion for REST APIs
Workaround: buffered String responses (A5)
Follow-up: quarkusio/quarkus tag 3.40.1.1 amazon-lambda* sources; aws-lambda-http guide
§7-ref: open (unverified)

Gap: U4 — IAM Resource ARN forms for Bedrock inference profiles (global./us.)
Impact: A2 policy resources
Workaround: Terraform skill with Bedrock IAM docs at write time
Follow-up: docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-*.html
§7-ref: open (unverified)

Gap: U5 — runtime fallback for Bedrock chat-model.model-id (doc default only)
Impact: A6 already requires explicit id
Workaround: set model-id explicitly
Follow-up: BedrockRecorder.java chat model builder at tag
§7-ref: open (unverified)

Gap: U6 — native-image support statement for the three providers in quarkus-langchain4j docs
Impact: Q4 native option (medium confidence)
Workaround: native integration test before ADR
Follow-up: integration-tests module at tag; docs search "native"
§7-ref: open (unverified)

Gap: U7 — SnapStart restore behaviour of provider HTTP clients (Vert.x / SDK) and init cost
Impact: Q4 option A
Workaround: post-restore smoke test; ADR
Follow-up: Quarkus 3.40 SnapStart guide + quarkus-langchain4j issues
§7-ref: open (unverified)

Gap: U8 — status code API Gateway returns on integration timeout and whether Lambda keeps running
Impact: F5 impact text (medium confidence)
Workaround: keep budgets under the limit
Follow-up: API Gateway Lambda error docs (FF38 page) — re-read for timeout case
§7-ref: open (unverified)

Gap: U9 — Dev Services / HTTP-level mocking for Anthropic and Bedrock; SSE content encoding in LambdaHttpHandler
Impact: QC mocking choices; F3 detail
Workaround: @InjectMock of the AI service
Follow-up: testing-model-mocking guide updates; isText() in LambdaHttpHandler
§7-ref: open (unverified)

Gap: U10 — whether log-requests masks Authorization / x-api-key headers
Impact: F4 severity
Workaround: never enable outside %dev
Follow-up: quarkus-langchain4j core logging filter sources at tag
§7-ref: open (unverified)

Gap: U11 — AWS SDK version alignment between langchain4j-bedrock (via LangChain4j 1.21.0) and Quarkiverse amazon-services 3.23.0 (awssdk 2.55.6, FF17)
Impact: classpath conflicts when Secrets Manager + Bedrock are combined
Workaround: dependency:tree check; one managed awssdk version
Follow-up: langchain4j-bedrock 1.21.0 POM
§7-ref: open (unverified)

Gap: G1 — Bedrock page not found in tag-pinned docs (404 for bedrock-chat-model.adoc, bedrock.adoc, amazon-bedrock.adoc; nav at tag lists no Bedrock entry)
Impact: Bedrock prose claims rest on dev page + tag code
Workaround: tag code used for defaults/behaviour
Follow-up: repo docs tree listing at tag (full "View all files")
§7-ref: Iteration 4 — IRRESOLVABLE

Gap: G2 — declaration and default value of quarkus.langchain4j.openai.chat-model.mode at tag
Impact: Q5 relies on the tag AsciiDoc sentence
Workaround: set mode explicitly when needed
Follow-up: grep "mode" in openai runtime/deployment config at tag
§7-ref: Iteration 3 — IRRESOLVABLE

Gap: G3 — full diff 1.14.2...1.15.0.CR1 ("This comparison is taking too long to generate.")
Impact: silent default changes cannot be excluded
Workaround: spot checks C1, S36
Follow-up: git diff locally
§7-ref: Iteration 5 — IRRESOLVABLE
```

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Guardrails A6 | OpenAI default model: dev table `gpt-6-luna` vs tag | Resolved: tag `@WithDefault("gpt-4o-mini")` (also 1.14.2); recorded C1 | [S19] [S36] (2026-10-28) |
| 1 | Guardrails A3 | Anthropic `max-retries` location | Resolved: `chat-model.max-retries` in ChatModelConfig, default 1, deprecated | [S22] (2026-10-28) |
| 2 | Guardrails A3 | Bedrock `api-call-timeout` default | Contradiction: doc 13s vs code `Duration.ofSeconds(10)`; recorded C3, set explicitly | [S27] [S31] (2026-10-28) |
| 2 | Guardrails A2 | Bedrock credentials when unset | Resolved: no provider set in code → SDK default chain → Lambda role / SnapStart container creds | [S31] [S45] [S43] (2026-10-28) |
| 3 | Conditional Q5 | OpenAI API mode default at tag | Resolved by tag AsciiDoc (Chat Completions, build-time); dev auto-selection recorded C4 | [S33] [S8] (2026-10-28) |
| 3 | Conditional Q5 | `chat-model.mode` declaration/default at tag | ⚠️ IRRESOLVABLE — not in ChatModelConfig.java; location not found within budget | — |
| 4 | Guardrails A5 | Streaming on Quarkus Lambda | Resolved: LambdaHttpHandler buffers until LastHttpContent | [S46] (2026-10-28) |
| 4 | Bibliography | Bedrock tag-pinned docs page | ⚠️ IRRESOLVABLE — three candidate paths 404, nav lists none | — |
| 4 | Guardrails A2 | Converse IAM actions | Resolved (verbatim) | [S44] (2026-10-28) |
| 5 | Conditional Q1 | Multi-provider selection syntax | Resolved: `quarkus.langchain4j.m1.chat-model.provider=openai` at tag | [S35] (2026-10-28) |
| 5 | Migration | 1.14.2→1.15.0.CR1 full diff | ⚠️ IRRESOLVABLE — GitHub compare timed out | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Complex)
- [x] All scope areas cited (AI services, 3 providers, keys/defaults, secrets, timeouts, retries, streaming, native/SnapStart, tools boundary, testing, observability)
- [x] Pattern counts driven by domain needs (10 / 7 / 8)
- [x] Every anti-pattern has alternative (F1-F8 with ❌/✅)
- [x] All CLI commands marked as representative
- [x] Integration examples complete (Bedrock, OpenAI/Anthropic + Secrets Manager, tests)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example (representative; not compiled)
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated or downgraded (A7, A9, A10 single-layer with verbatim tag sources; consequences tagged medium)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in §7 (U-items open/unverified; G1-G3 IRRESOLVABLE)

---

## Agent Operation Notes

- **High Confidence (execute without asking)**:
  - the version lock (A1)
  - Bedrock role-only credentials plus the two IAM actions (A2)
  - the gateway/Lambda limits and provider defaults (A3)
  - no keys in properties/env (A4, F1, F2)
  - buffered responses with `quarkus-amazon-lambda-http` (A5, F3)
  - explicit model ids (A6)
  - logging/tracing off (A7, F4)
  - mocks/WireMock in tests (A8, F8)
  - the default table values tagged High
- **Medium Confidence (validate with user)**:
  - the Secrets Manager config-source mapping onto LangChain4j keys (U2)
  - budget values (Q2)
  - native support (Q4)
  - multi-provider names `anthropic`/`bedrock` (Q1)
  - Vert.x-based Bedrock HTTP client
  - the REST-extension buffering
  - F6 and F7 impact statements
- **Low Confidence (must ask human)**: SnapStart restore behaviour of provider clients (U7); Bedrock inference-profile IAM ARNs (U4); G1-G3.
- **Edge Cases (pause)**: the target is a **CR (pre-release)**, so any default may change at 1.15.0 final; re-verify C1-C4. dev docs run ahead of the tag (C1, C4).
- **Emergency Stop**: not triggered (official sources available). If 1.15.0 final ships with Quarkus ≠ 3.40, re-scope.

---

## Contradictions Report

| ID | Topic | Source A | Source B | Resolution |
|---|---|---|---|---|
| C1 | OpenAI default `chat-model.model-name` | tag 1.15.0.CR1 (and 1.14.2) `@WithDefault("gpt-4o-mini")` [S19][S36] | dev docs table `gpt-6-luna` [S8] (tool summary, no verbatim sentence) | Tag wins for 1.15.0.CR1; always set explicitly (A6) |
| C2 | Anthropic default model | code `@WithDefault("claude-3-haiku-20240307")` [S22] | tag AsciiDoc "By default, the extension uses the latest available Claude model." [S34] | Code is the runtime truth; set explicitly (A6) |
| C3 | Bedrock `aws.api-call-timeout` default | `@ConfigDocDefault("13s")` [S27] (dev table also 13s [S10]) | recorder `builder.apiCallTimeout(firstOrDefault(Duration.ofSeconds(10), modelConfig.aws().apiCallTimeout(), bedrockConfig.aws().apiCallTimeout()));` [S31] | Cite both; set explicitly (A3). Whether that statement is guarded by a condition was not read (medium confidence) |
| C4 | OpenAI API mode default | tag AsciiDoc: "By default, the chat model targets OpenAI's `/v1/chat/completions` endpoint." [S33] | dev: default `auto`, "When not set, the mode is selected automatically:" (responses for the OpenAI base URL) [S8] | Tag wins for 1.15.0.CR1; expect change at final (Q5) |
| C5 | Where to put API keys | extension docs suggest env var `QUARKUS_LANGCHAIN4J_OPENAI_API_KEY` [S33]; security page says "set the `OPENAI_API_KEY` environment variable in your deployment environment" [S16] | AWS: Secrets Manager "instead of environment variables" for API keys [S43]; R5 | R5 + AWS win on Lambda (A4, F1) |

---

## Facts for the family

Facts in this file that other units also use. "FF<n>" = existing row in `_family_facts_v3.40.md`; "new" = candidate row for the orchestrator (this unit does not edit the facts file).

| Fact | Used by | Family-fact row |
|---|---|---|
| API Gateway integration timeout: REST API 50 ms-29 s (Regional/private raisable, "might require a reduction in your Region-level throttle quota"; edge-optimized not raisable); HTTP API "30 seconds", not raisable | U2 HTTP, U7 Stripe (cited as internal [I8] there), debugging/deploy units | **new** (no row; [S37][S38]) |
| Lambda timeout default 3 s, max 900 s | U1, U5, U7, deploy/debug units | **new** (no row; [S42]) |
| Response streaming: REST API yes / HTTP API no; Lambda native streaming only on Node.js managed runtimes; API Gateway streaming needs `InvokeWithResponseStream` plus the delimiter output format | U2 HTTP | extends **FF35** (streaming row not in FF35; [S39][S40][S41]) |
| Quarkus 3.40.1.1 `LambdaHttpHandler` buffers the whole response (`ByteArrayOutputStream` until `LastHttpContent`) | U2 HTTP | **new** ([S46]) |
| AWS: use Secrets Manager instead of Lambda environment variables for API keys | U5, U7 | **new** ([S43]); secret config source itself per U5 research [I1] (no row) |
| SDK default credentials chain (system props → env vars → web identity → profile → container → instance) covers both Lambda role env vars and SnapStart container credentials | U4, U5, U7 | complements **FF33** ([S45]) |
| quarkus-langchain4j 1.15.0.CR1 = Quarkus 3.40.0 / LangChain4j 1.21.0; 1.14.2 = Quarkus 3.33.3.1 / LangChain4j 1.20.2; 2.0.0.Beta1 = Quarkus 4 | U8 only (plus G-level version audits) | confirms/extends **FF18** ([S1][S4][S5]) |
| No Quarkiverse CloudWatch Micrometer registry (applies to `gen_ai.*` metrics) | metrics unit | **FF39** |
| X-Ray SDK maintenance mode → tracing exporter is an ADR | tracing unit | **FF34** |
| API Gateway → Lambda error mapping 500/502, no retries | debug unit, U7 | **FF38** |
| JVM+SnapStart vs native is an ADR | all Lambda units | **R3**, FF13, FF16, FF20-FF22 |
| `quarkus-test-amazon-lambda` removed in 3.31; use the mock event server | testing unit | **FF23**, FF14 |

---

## Source Bibliography

**Primary (all read 2026-10-28):**

| ID | URL | Coverage | Used for |
|---|---|---|---|
| S1 | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-parent/1.15.0.CR1/quarkus-langchain4j-parent-1.15.0.CR1.pom | properties + modules (tool extraction; values verbatim) | quarkus 3.40.0, langchain4j 1.21.0, wiremock 1.5.1 |
| S2 | https://github.com/quarkiverse/quarkus-langchain4j/releases/tag/1.15.0.CR1 | full release block | pre-release flag, changes |
| S3 | https://github.com/quarkiverse/quarkus-langchain4j/releases/tag/1.14.2 | full release block | 1.14.2 changes |
| S4 | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-parent/1.14.2/quarkus-langchain4j-parent-1.14.2.pom | two properties (verbatim) | 1.14.2 = Quarkus 3.33.3.1 / LangChain4j 1.20.2 |
| S5a | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-openai/maven-metadata.xml | latest/release/last 6 versions | versions |
| S5b | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-anthropic/maven-metadata.xml | same | versions |
| S5c | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-bedrock/maven-metadata.xml | same | versions |
| S5d | https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-bom/maven-metadata.xml | relevant entries | BOM exists at 1.15.0.CR1 |
| S6 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/index.html (+ models.html) | nav only / models page tool summary | docs version "dev" only; named model example |
| S7 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/ai-services.html | tool summary with verbatim quotes (page length not measured) | @RegisterAiService, memory, tools |
| S8 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/openai-chat-model.html | two passes, tool summary with short verbatim quotes | dev defaults, mode, max-retries on Responses |
| S9 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/anthropic-chat-model.html | tool summary (length not measured) | dev Anthropic table (superseded by S21/S22) |
| S10 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/bedrock-chat-model.html | **partly read: chars 0-100000 of 119216** | Bedrock credentials quotes, key spellings |
| S11 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/guide-streamed-responses.html | tool summary with verbatim quotes | Multi, SSE, non-blocking |
| S12 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/guide-fault-tolerance.html | tool summary with verbatim excerpts | @Timeout/@Fallback example, tools warning |
| S13 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/testing-model-mocking.html | tool summary with verbatim quotes | WireMock approach |
| S14 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/testing.html | **partly read: chars 0-100000 of 103328** | evaluation framework, WireMock pointer |
| S15 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/observability.html | tool summary with verbatim quotes | metrics, spans, events |
| S16 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/security.html | tool summary with verbatim quotes | secrets, logging, PII, injection |
| S17 | https://docs.quarkiverse.io/quarkus-langchain4j/dev/function-calling.html | tool summary with verbatim quotes | @Tool boundary |
| S18 | https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/model-providers/openai/openai-vanilla/runtime/src/main/java/io/quarkiverse/langchain4j/openai/runtime/config/LangChain4jOpenAiConfig.java | annotations verbatim | OpenAI top-level defaults |
| S19 | …/1.15.0.CR1/model-providers/openai/openai-vanilla/runtime/src/main/java/io/quarkiverse/langchain4j/openai/runtime/config/ChatModelConfig.java | annotations verbatim; 134 lines | model-name, temperature, mode reference |
| S20 | …/1.15.0.CR1/model-providers/openai/openai-vanilla/runtime/src/main/java/io/quarkiverse/langchain4j/openai/runtime/OpenAiRecorder.java | verbatim lines + tool summary | timeout fallback, maxRetries, dummy-key check |
| S21 | …/1.15.0.CR1/model-providers/anthropic/runtime/src/main/java/io/quarkiverse/langchain4j/anthropic/runtime/config/LangChain4jAnthropicConfig.java | annotations verbatim | Anthropic top-level defaults |
| S22 | …/1.15.0.CR1/model-providers/anthropic/runtime/src/main/java/io/quarkiverse/langchain4j/anthropic/runtime/config/ChatModelConfig.java | annotations + javadoc verbatim | model, max-tokens, max-retries |
| S23 | …/1.15.0.CR1/model-providers/anthropic/runtime/src/main/java/io/quarkiverse/langchain4j/anthropic/runtime/AnthropicRecorder.java | verbatim timeout line + tool summary | timeout fallback, streaming without retries, ModelAuthProvider lookup |
| S24 | …/1.15.0.CR1/core/runtime/src/main/java/io/quarkiverse/langchain4j/runtime/config/LangChain4jConfig.java | excerpt verbatim | global keys |
| S25 | …/1.15.0.CR1/core/runtime/src/main/java/io/quarkiverse/langchain4j/runtime/config/TracingConfig.java | verbatim | tracing defaults |
| S26 | …/1.15.0.CR1/core/runtime/src/main/java/io/quarkiverse/langchain4j/RegisterAiService.java | javadoc + attributes verbatim | RequestScoped default, attributes |
| S27 | …/1.15.0.CR1/model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/config/AwsConfig.java | annotations (doc defaults); javadoc paraphrased | region, credentials, retries, api-call-timeout |
| S28 | …/1.15.0.CR1/model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/config/ChatModelConfig.java | annotations verbatim | model-id, temperature, max-tokens, top-p, caching TTL |
| S29 | …/1.15.0.CR1/model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/config/HttpClientConfig.java | doc defaults; javadoc paraphrased | connect/read timeout, keep-alive, proxy deprecations |
| S30 | …/1.15.0.CR1/model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/config/AwsClientConfig.java | verbatim | log-requests/responses/body |
| S31 | …/1.15.0.CR1/model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/BedrockRecorder.java | two passes; verbatim code blocks for credentials, region, apiCallTimeout, retries; rest tool summary | Bedrock runtime behaviour |
| S32 | …/1.15.0.CR1/model-providers/bedrock/runtime/pom.xml | dependency list (tool extraction) | HTTP client exclusions |
| S33 | https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/docs/modules/ROOT/pages/openai-chat-model.adoc | tool summary with verbatim quotes | tag-pinned mode default, env var |
| S34 | …/1.15.0.CR1/docs/modules/ROOT/pages/anthropic-chat-model.adoc | tool summary with verbatim quotes (config include not resolved) | tag-pinned Anthropic prose |
| S35 | …/1.15.0.CR1/docs/modules/ROOT/pages/ai-services.adoc | two passes, verbatim quotes | memory defaults, provider selection |
| S36 | …/1.14.2/model-providers/bedrock/runtime/src/main/java/io/quarkiverse/langchain4j/bedrock/runtime/config/ChatModelConfig.java ; …/1.14.2/model-providers/openai/openai-vanilla/runtime/src/main/java/io/quarkiverse/langchain4j/openai/runtime/config/ChatModelConfig.java | annotations verbatim | 1.14.2 vs CR defaults |
| S37 | https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html | full | REST API 29 s |
| S38 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html | full | HTTP API 30 s |
| S39 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html | full | response streaming REST yes / HTTP no |
| S40 | https://docs.aws.amazon.com/apigateway/latest/developerguide/response-transfer-mode-lambda.html | full | streaming output format |
| S41 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html | full | Node.js-only native streaming |
| S42 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-timeout.html | full | 3 s default, 900 s max |
| S43 | https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html | full | Secrets Manager recommendation, AWS_REGION, role keys |
| S44 | https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html | saved full output, grep of IAM sentence | Converse IAM actions |
| S45 | https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/credentials-chain.html | full | default credentials chain |
| S46 | https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda-http/runtime/src/main/java/io/quarkus/amazon/lambda/http/LambdaHttpHandler.java | verbatim lines via tool | buffered response |
| S47 | https://quarkus.io/version/3.40/guides/getting-started-testing | **partly read: chars 0-100000 of 108160** | @InjectMock scope rule |
| S48 | https://docs.langchain4j.dev/integrations/frameworks/quarkus | one sentence verbatim | native claim (indirect) |
| S49 | https://docs.langchain4j.dev/integrations/language-models/amazon-bedrock | tool summary (page shows langchain4j-bedrock 1.23.0 snippet, not our version) | Converse implication only |
| S50 | https://github.com/quarkiverse/quarkus-langchain4j/tree/1.15.0.CR1/model-providers/anthropic/runtime/src/main/java/io/quarkiverse/langchain4j/anthropic/runtime | directory listing (may be incomplete) | `graalvm` package exists |

**Not available / failed (2026-10-28):**
- 404: `…/1.15.0.CR1/docs/modules/ROOT/pages/bedrock-chat-model.adoc`, `…/bedrock.adoc`, `…/amazon-bedrock.adoc` (G1). The tag `nav.adoc` lists no Bedrock entry.
- Timed out: https://github.com/quarkiverse/quarkus-langchain4j/compare/1.14.2...1.15.0.CR1 (G3)
- Lambda runtime env-var anchor page `configuration-envvars-runtime.html` returned only a title. Superseded by S43, and the tool's "general knowledge" answer was discarded.
- `conversation-inference-call.html`: "moved", superseded by S44.

**Internal (cited, not re-verified here):**
- I1 `workspace/quarkus-aws-saas/research_Quarkus_AmazonMessaging_v3.40.md` (U5: Secrets Manager/SSM config sources A10/Q1, defaults off, load once at startup)
- I2 `workspace/quarkus-aws-saas/research_Stripe_Quarkus_Lambda_v3.40.md` (U7: secrets in the SnapStart snapshot, rotation needs a new version)
- I3 `workspace/quarkus-aws-saas/research_Quarkus_AmazonLambdaHTTP_v3.40.md` (U2: HTTP API feature limits incl. no response streaming)
- Family facts `_family_facts_v3.40.md` rows FF8-FF42 as cited; family rules R1-R15.

**Validation**: WebSearch "quarkus-langchain4j native image support GraalVM docs.quarkiverse.io" (2026-10-28) returned only secondary sources (Devoxx, DevConf, IBM tutorial). None were used as evidence; only the official LangChain4j framework page S48 is cited.
