# Builder Options and Defaults

Back to [SKILL.md](../SKILL.md). langchain4j-anthropic 1.22.0, research date 2026-10-26.

Sources: https://docs.langchain4j.dev/integrations/language-models/anthropic (option list, unversioned, medium confidence for options not seen in source) and, at tag 1.22.0, https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java and https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicStreamingChatModel.java.

## Defaults read from source

| Option | Default | Notes |
|---|---|---|
| `baseUrl` | `https://api.anthropic.com/v1/` | change only for a proxy or gateway |
| `version` | `2023-06-01` | sent as the `anthropic-version` header |
| `maxTokens` | 1024 when neither builder nor `defaultRequestParameters` sets `maxOutputTokens` | set explicitly |
| `maxRetries` | 2 (blocking model) | the streaming model has no `maxRetries` (medium confidence) |
| `timeout` | none in the model class | set a `Duration` |
| `returnThinking` | false | |
| `sendThinking` | true | earlier thinking is sent back on follow-up requests |
| `midConversationSystemMessages` | false | see [caching and system messages](./caching-and-system-messages.md#system-messages) |

## Option groups (docs page)

- Transport: `httpClientBuilder`, `baseUrl`, `apiKey`, `version`, `beta`, `timeout`, `maxRetries` (blocking only), `logRequests`, `logResponses`, `listeners`.
- Sampling and size: `modelName`, `temperature`, `topP`, `topK`, `maxTokens`, `stopSequences`.
- Tools (names only, tools are out of scope): `toolSpecifications`, `toolChoice`, `toolChoiceName`, `disableParallelToolUse`, `serverTools`, `returnServerToolResults`, `toolMetadataKeysToSend`.
- Caching: `cacheSystemMessages`, `cacheTools`, `cacheAutomatically`, `cacheTtl`, `returnCacheDiagnostics`.
- Thinking: `thinkingType`, `thinkingBudgetTokens`, `thinkingDisplay`, `returnThinking`, `sendThinking`.
- Other: `midConversationSystemMessages`, `defaultRequestParameters`, `userId`, `customParameters`.

`previousMessageId` is per-request only. Per-request overrides go through `AnthropicChatRequestParameters`; any option a request leaves unset falls back to the builder value (docs page, medium confidence).

## Per-request parameters

Parameter merging (`overrideWith`, `defaultedBy`) is generic: see `developing-langchain4j-core-v1-22`.

```java
// langchain4j-anthropic 1.22.0
ChatRequest request = ChatRequest.builder()
        .messages(UserMessage.from("Explain adaptive thinking in two lines."))
        .parameters(AnthropicChatRequestParameters.builder().maxOutputTokens(2048).build())
        .build();
ChatResponse response = model.chat(request);
```

Builder method `maxOutputTokens` on the Anthropic request parameters is taken from the docs page (medium confidence).

## Usage

`response.metadata().tokenUsage()` carries token counts; for Anthropic it also reports cache-creation and cache-read counts when caching is on (docs page, medium confidence).
