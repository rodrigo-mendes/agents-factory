# Ask-first decisions

Back to [SKILL.md](../SKILL.md). Research date 2026-10-28. Each decision lists options and tradeoffs; ask the user and wait, do not pick a default. Source ids resolve in the [source bibliography](./source-bibliography.md).

## Contents

- [D1 Adopt a pre-release](#d1-adopt-a-pre-release)
- [D2 Providers per function](#d2-providers-per-function)
- [D3 API key loading mechanism](#d3-api-key-loading-mechanism)
- [D4 Time and retry budget](#d4-time-and-retry-budget)
- [D5 Bedrock model id and IAM](#d5-bedrock-model-id-and-iam)
- [D6 JVM + SnapStart or native](#d6-jvm--snapstart-or-native)
- [D7 OpenAI API mode](#d7-openai-api-mode)
- [D8 AI service scope and chat memory](#d8-ai-service-scope-and-chat-memory)
- [D9 LangChain4j version override](#d9-langchain4j-version-override)
- [D10 Streaming and tools](#d10-streaming-and-tools)

## D1 Adopt a pre-release

1.15.0.CR1 is the only quarkus-langchain4j version built on Quarkus 3.40 [S1][S5]; the stable 1.14.2 needs Quarkus 3.33.3.1 [S4]. The release notes list no breaking changes, but the full 1.14.2 to 1.15.0.CR1 diff could not be rendered, so silent default changes are not excluded (medium confidence, absence of evidence, I3) [S2]. This is the one statement of the pre-release caveat: defaults and keys can change at the final; other files point here.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A adopt 1.15.0.CR1, flagged | works on Quarkus 3.40 LTS today | defaults and keys may change at the final | the product accepts a candidate release |
| B wait for 1.15.0 final | stable artifact | no LLM feature on Quarkus 3.40 until then | LLM calls are not on the critical path |

Re-check trigger: when 1.15.0 final appears on Maven Central, re-run the defaults check (C1 to C4) on its tag; the `dev` docs already differ from the tag, for example the OpenAI mode selection (C4). Ask: "Is a pre-release acceptable here, and who re-runs the defaults check at the final?"

## D2 Providers per function

Option A, one provider extension per function: the AI service uses "the default model" [S7]. Option B, several providers: "each model needs to be given a name, which is then referenced by the AI service" [S35], for example `quarkus.langchain4j.m1.chat-model.provider=openai` with `@RegisterAiService(modelName = "m1")` [S35][S26]. The values `anthropic` and `bedrock` for `chat-model.provider` are (medium confidence, M8).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A one provider | smallest package, fewest secrets and IAM paths | no vendor failover | one vendor contract per function |
| B named models | vendor choice per method | more config and secrets, cold-start cost unquantified | routing tasks to different models |

Ask: "Which provider or providers does each function call? With Bedrock only, no API key exists."

## D3 API key loading mechanism

Family rule 5 (secrets come from Secrets Manager or SSM) fixes the store; the delivery is open.

| Option | Tradeoff |
|---|---|
| A Secrets Manager config source mapped onto the key, for example `quarkus.secretsmanager.config.secrets."quarkus.langchain4j.openai.api-key"=<secret name>` | Loaded once at startup, off by default (medium confidence, M20) [N1]; see `integrating-quarkus-amazon-messaging-v3-40`. That the key is resolved after the config source is active is (unverified, U2) [S20][S23]. |
| B a `ModelAuthProvider` CDI bean reading the secret through an injected Secrets Manager client | It can "load tokens or API keys from the database or other sources" [S16]; the recorders look it up before the dummy-key check [S23]. Custom code. |
| C the AWS Parameters and Secrets Lambda Extension | One HTTP hop per fetch (medium confidence, M20) [N1]. |

With SnapStart, a value loaded at init sits in the snapshot, so rotation needs a new published version (medium confidence, M18) [N2]. Ask: "Must keys rotate without a redeploy? If not, A, after an integration test of the ordering."

## D4 Time and retry budget

Fixed inputs: gateway limits [S37][S38], Lambda timeout [S42], provider defaults [S18][S20][S22][S23][S27][S29][S31]. The split below is a design choice (medium confidence, M1).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A single attempt, long timeout (OpenAI and Anthropic default retries: none) | simplicity | no recovery from a transient 5xx | short prompts, fast models |
| B MicroProfile `@Retry` with a short per-attempt timeout under `@Timeout` [S12] | resilience | each retry spends the 29 s or 30 s budget; the guide says use `@Retry` "carefully when your AI service registers tools" | idempotent, tool-free prompts |
| C asynchronous: API Gateway to SQS to Lambda (up to 900 s [S42]), result stored and fetched later | no gateway cap | asynchronous UX, extra infrastructure (messaging: `integrating-quarkus-amazon-messaging-v3-40`) | long outputs, batch |

A `@Fallback` default method on the AI service interface follows the guide's pattern but its exact signature is (medium confidence, M3). A REST API on a Regional or private endpoint can raise the 29 s limit, which may reduce the Region-level throttle quota [S37]. Ask: "Which gateway type, Lambda timeout, p99 model latency and output length? Above about 20 s p99, consider C."

## D5 Bedrock model id and IAM

Option A: a plain model id. Option B: an inference-profile id such as the documentation default `global.amazon.nova-2-lite-v1:0` [S28] or the `dev` example `us.anthropic.claude-opus-4-7` [S10]. A profile may route across Regions (medium confidence, M12). The role needs "`bedrock:InvokeModel`" for `Converse` and "`bedrock:InvokeModelWithResponseStream`" for `ConverseStream` [S44]; that the Bedrock chat and streaming models call those two operations is (medium confidence, M2) [S49]. The resource ARN forms for profiles are (unverified, U4), and the runtime fallback of `model-id` is (unverified, U5). Ask: "Which exact model, and is cross-Region routing allowed by the data-residency policy?" Then write the matching IAM resources in Terraform (`provisioning-aws-*-v6`).

## D6 JVM + SnapStart or native

Always an ADR (family rule 3): SnapStart supports Java managed runtimes only, not OS-only runtimes ([SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)), so it cannot combine with a native build. No quarkus-langchain4j page read documents native or SnapStart; the LangChain4j framework page lists "Ability to compile to a GraalVM native binary" [S48] and the Anthropic module ships a `graalvm` package [S50], both indirect, so native support of the three providers is (unverified, U6). Whether the providers' Vert.x or SDK connections survive a restore is (unverified, U7). Secrets loaded at init end up in the snapshot (medium confidence, M18) [N2].

| Option | Optimizes | Sacrifices |
|---|---|---|
| A JVM + SnapStart | documented Java runtime, no native build | restore behaviour of HTTP clients unverified; secrets in the snapshot |
| B native on `provided.al2023` | fast cold start, no snapshot | provider native support not documented on the pages read |

Ask: "Is there an ADR for the runtime choice? A post-restore smoke test or a native integration test is required either way."

## D7 OpenAI API mode

Tag docs: "By default, the chat model targets OpenAI's `/v1/chat/completions` endpoint." Responses mode is set by "the build-time `mode` property" and is needed for models "only exposed through it (for example `gpt-5-pro`, `o1-pro`)" [S33]. The `dev` docs say `max-retries` "is deprecated and is **not honored** on the Responses API" [S8] (dev docs, verbatim) and select the mode automatically (C4). The declaration and default of the `mode` key at the tag were not located (medium confidence, absence of evidence, I2). Ask: "Does the chosen model exist only on the Responses API? If yes, set the mode explicitly and use MicroProfile retries."

## D8 AI service scope and chat memory

The bean is `@RequestScoped` by default and memory "is managed using CDI-scope" when no supplier is set [S7][S26]. An application-wide scope would keep one 10-message window across requests, and across tenants served by the same environment (medium confidence, M11); family rule 6 treats tenant isolation violations as never-do. In-JVM memory is not shared across Lambda environments and not durable (medium confidence, M6). Memory stores (Redis, MongoDB) are listed in the docs navigation [S6] but are out of scope. Ask: "Is memory needed across requests, where is it stored, and how is it keyed by the tenant taken from the token?"

## D9 LangChain4j version override

1.15.0.CR1 is built against `langchain4j.version` 1.21.0 [S1]; the plain-Java family uses 1.22.0. Mixing two LangChain4j versions in one application breaks version absolutism, and binary incompatibility is (unverified, U1). AWS SDK alignment between `langchain4j-bedrock` and the Quarkiverse amazon-services 3.23.x clients is (unverified, U11); check `./mvnw dependency:tree`. Ask: "Why must LangChain4j differ from 1.21.0?"

## D10 Streaming and tools

Streaming: with `quarkus-amazon-lambda-rest` the handler buffering is assumed equal to the HTTP one (medium confidence, M4). A REST API supports response streaming through `InvokeWithResponseStream` with a metadata and delimiter output format [S40]; no Quarkus page read documents that format (unverified, U3). Ask: "Is incremental delivery a hard requirement? If yes, the options are outside this skill's evidence."

Tools: "Tools must be part of a CDI bean and annotated with `@Tool`" [S17]; `maxSequentialToolInvocations` (default 10) is deprecated for `maxToolCallingRoundTrips()` [S26]; "Security annotations such as `@RolesAllowed` on a tool method of a CDI bean are enforced" [S17], so tenant isolation still applies inside tools. Each tool round trip is another model call inside the same time budget (medium confidence, M7). Ask: "Which tools, and what is the round-trip cap against the gateway budget?"
