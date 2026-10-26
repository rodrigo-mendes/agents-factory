# Builder Options and Variants

Back to [SKILL.md](../SKILL.md). langchain4j-open-ai 1.22.0, research date 2026-10-26. Sources: `OpenAiChatModel.java` and `OpenAiStreamingChatModel.java` at tag 1.22.0 (https://github.com/langchain4j/langchain4j/tree/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai).

## OpenAiChatModel builder

| Option | Default | Note |
|---|---|---|
| `baseUrl` | `https://api.openai.com/v1` | change only for compatible endpoints |
| `apiKey` | none | read from the environment |
| `organizationId`, `projectId` | none | optional scoping |
| `modelName(String or OpenAiChatModelName)` | none | use the String overload |
| `timeout(Duration)` | connect 15 s, read 60 s | one call sets both |
| `maxRetries` | 2 | blocking model only |
| `logRequests`, `logResponses` | `false` | keep off in production |
| `logger(org.slf4j.Logger)` | internal logger | SLF4J type |
| `httpClientBuilder` | JDK HTTP client | `langchain4j-http-client-jdk` at runtime |
| `customHeaders(Map or Supplier<Map>)`, `customQueryParams`, `customParameters` | none | extra headers, query and body fields |
| `listeners` | none | listener API: core skill |
| `defaultRequestParameters` | none | see [patterns](./always-do-patterns.md#6-shared-defaults) |
| `temperature`, `topP`, `stop`, `presencePenalty`, `frequencyPenalty` | unset | omit on GPT-6 with effort not `none` |
| `maxTokens`, `maxCompletionTokens` | unset | prefer `maxCompletionTokens` |
| `logitBias`, `seed`, `user`, `store`, `metadata`, `serviceTier` | unset | pass-through request fields |
| `reasoningEffort(String)` | unset | sent verbatim |
| `logprobs`, `topLogprobs`, `parallelToolCalls` | unset | `logprobs` must be removed on GPT-6 with effort not `none` |
| `promptCacheKey`, `promptCacheOptions` | unset | since 1.21.0 |
| `responseFormat`, `supportedCapabilities`, `strictJsonSchema`, `strictTools` | `strict*` false | structured output and tools: out of scope |
| `returnThinking`, `sendThinking(Boolean[, String])` | `false` | field name default `reasoning_content` |
| `useInputImageFormat` | `false` | out of scope |

The default `User-Agent` is `langchain4j-openai`. An empty `choices` array in a response raises `InternalServerException` ("Chat completion failed: no choices returned in response").

## OpenAiStreamingChatModel additions

- `accumulateToolCallId` default `true`; set `false` only for APIs that repeat the full tool-call ID in every chunk (medium confidence).
- `streamingBufferSize` is `@Experimental` since 1.20.0; overflow ends the stream with `IllegalStateException`; the default value is (unverified).
- There is no `maxRetries` (medium confidence). Own retry belongs in `onError`, on retriable exceptions only (core skill).

## OpenAI-compatible endpoints

Source: https://docs.langchain4j.dev/integrations/language-models/open-ai (unversioned page, read 2026-10-26). Claims in this section are (medium confidence).

```java
// langchain4j-open-ai 1.22.0: documented DeepSeek example
ChatModel model = OpenAiChatModel.builder()
        .apiKey(System.getenv("DEEPSEEK_API_KEY"))
        .baseUrl("https://api.deepseek.com/v1")
        .modelName("deepseek-reasoner")
        .returnThinking(true)                 // reasoning_content -> AiMessage.thinking()
        .build();
```

- Set `baseUrl` and the provider's own model ID; the catalog check in SKILL.md applies to OpenAI only.
- `sendThinking(true[, fieldName])` sends thinking back; the default field name is `reasoning_content`.
- `maxTokens` may be the only token limit a compatible server understands (medium confidence); ask which endpoint is targeted before choosing.
- The dedicated "OpenAI-Compatible" docs page was not read, so provider caveats beyond DeepSeek are (unverified).

## Official SDK module

Source: https://docs.langchain4j.dev/integrations/language-models/open-ai-official (beta module page, read 2026-10-26) and https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-open-ai-official/ . Page-sourced claims in this section are (medium confidence).

Ask First only; never the default. `dev.langchain4j:langchain4j-open-ai-official:1.22.0-beta32` wraps the official `openai-java` SDK.

| Aspect | Value |
|---|---|
| Classes | `OpenAiOfficialChatModel`, `OpenAiOfficialStreamingChatModel`, both via `builder()` |
| Azure | `isAzure(true)`; detected automatically when `baseUrl` ends with `openai.azure.com`; with no API key it uses passwordless auth and needs the `azure-identity` dependency |
| GitHub Models | `isGitHubModels(true)` |
| Responses API | documented as experimental on that page |
| Unknown | Azure deployment-name and credential builder options (unverified); whether `langchain4j-bom:1.22.0` manages this artifact's version (unverified) |

Do not expect `OpenAiChatModel` inside the `-official` artifact, and do not declare it as `1.22.0`; the published version is `1.22.0-beta32`. Pointing `langchain4j-open-ai` at Azure through `baseUrl`, `customHeaders` and `customQueryParams` is (unverified): Azure uses an `api-key` header and an `api-version` query parameter, and no official page confirms this route.
