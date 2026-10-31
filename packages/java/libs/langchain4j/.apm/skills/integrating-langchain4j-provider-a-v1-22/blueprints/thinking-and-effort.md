# Adaptive Thinking and Effort

Back to [SKILL.md](../SKILL.md). langchain4j-anthropic 1.22.0 on Claude 5.x, research date 2026-10-26.

Sources: https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost, https://platform.claude.com/docs/en/about-claude/models/overview, https://docs.langchain4j.dev/integrations/language-models/anthropic and `AnthropicChatModel.java` at tag 1.22.0 (https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java).

## Adaptive thinking

Claude Fable 5.1, Opus 5.5, Sonnet 5.5 and Haiku 5.5 use adaptive thinking. The API shape is `"thinking": {"type": "adaptive"}`. In LangChain4j, `thinkingType` is a plain `String`, and the thinking object is built only when the type or budget is set.

```java
// langchain4j-anthropic 1.22.0
ChatModel model = AnthropicChatModel.builder()
        .apiKey(System.getenv("ANTHROPIC_API_KEY"))
        .modelName("claude-opus-5-5")
        .maxTokens(8192)
        .thinkingType("adaptive")
        .thinkingDisplay("summarized")   // optional, see below
        .returnThinking(true)            // optional, default false
        .build();
```

Manual `thinkingType("enabled")` with `thinkingBudgetTokens(...)` is deprecated on Opus 4.6 and Sonnet 4.6 and not accepted on later models; see [never-do](./never-do-patterns.md#1-manual-budget-thinking-on-claude-5x).

## Effort

There is no `effort` builder method. Effort is a top-level request field, `"output_config": {"effort": "..."}`, not inside `thinking`. Pass it through `customParameters`:

```java
// langchain4j-anthropic 1.22.0
AnthropicChatModel.builder()
        .modelName("claude-sonnet-5-5")
        .thinkingType("adaptive")
        .customParameters(Map.of("output_config", Map.of("effort", "medium")))
        .build();
```

Levels named by Anthropic are `low`, `medium`, `high`, `xhigh`, `max` (medium confidence, effort page read through a search summary); which levels each model accepts is (unverified), see U6. Defaults from the models overview: high on Fable 5.1 and Sonnet 5.5, medium on Opus 5.5 and Haiku 5.5.

## Showing the reasoning

| Option | Effect | Default |
|---|---|---|
| `thinkingDisplay("summarized")` or `("omitted")` | controls whether reasoning text is returned | model-dependent when unset |
| `returnThinking(true)` | puts the reasoning in `AiMessage.thinking()` | false |
| `sendThinking` | sends earlier thinking back on follow-up requests | true |

When `thinkingDisplay` is unset, recent models may return empty thinking, so `AiMessage.thinking()` stays empty and the streaming `onPartialThinking` callback is not called (medium confidence, docs page unversioned, see M2). For streaming, `onPartialThinking` is a default no-op method of the handler; its contract is in `developing-langchain4j-core-v1-22`.

```java
// show reasoning summaries while streaming
AnthropicStreamingChatModel.builder()
        .apiKey(System.getenv("ANTHROPIC_API_KEY"))
        .modelName("claude-sonnet-5-5")
        .maxTokens(8192)
        .thinkingType("adaptive")
        .thinkingDisplay("summarized")
        .returnThinking(true)
        .build();
// handler: override onPartialThinking(PartialThinking t) to display it
```

## Do not

- Do not set `thinkingBudgetTokens` on Claude 5.x.
- Do not log the reasoning text in production: it can carry prompt content (medium confidence, inference from the unmasked body logging at tag 1.22.0).
