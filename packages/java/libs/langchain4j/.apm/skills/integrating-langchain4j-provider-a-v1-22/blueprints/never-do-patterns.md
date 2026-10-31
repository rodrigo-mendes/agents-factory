# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). langchain4j-anthropic 1.22.0, research date 2026-10-26. Every row has a High-confidence alternative.

## 1. Manual budget thinking on Claude 5.x

Source: https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost and https://platform.claude.com/docs/en/about-claude/models/overview (fetched 2026-10-26): `thinking.type="enabled"` with `budget_tokens` is deprecated on Opus 4.6 and Sonnet 4.6 and not accepted on later models.

```java
// 🚫 WRONG: the API rejects the request on Claude 5.x
AnthropicChatModel.builder()
        .modelName("claude-sonnet-5-5")
        .thinkingType("enabled").thinkingBudgetTokens(2048);
```

```java
// ✅ CORRECT
AnthropicChatModel.builder()
        .modelName("claude-sonnet-5-5")
        .thinkingType("adaptive");
```

## 2. Relying on the 1024 maxTokens default

Source: https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java

```java
// 🚫 WRONG: output is cut off at 1024 tokens (finish reason LENGTH)
AnthropicChatModel.builder().apiKey(key).modelName("claude-sonnet-5-5").build();
```

```java
// ✅ CORRECT
AnthropicChatModel.builder().apiKey(key).modelName("claude-sonnet-5-5").maxTokens(8192).build();
```

## 3. Hardcoding the API key

```java
// 🚫 WRONG
.apiKey("sk-ant-...")
```

```java
// ✅ CORRECT
.apiKey(System.getenv("ANTHROPIC_API_KEY"))
```

## 4. logRequests / logResponses in production

Source: https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-http-client/src/main/java/dev/langchain4j/http/client/log/HttpRequestLogger.java. Secret headers such as `x-api-key` are masked (first 5 and last 2 characters); the body (prompts, personal data) is logged unmasked at INFO through SLF4J.

```java
// 🚫 WRONG in production
.logRequests(true).logResponses(true)
```

```java
// ✅ CORRECT: off in production; on only while debugging locally
.logRequests(false).logResponses(false)
```

## 5. Effort inside the thinking object

Source: https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost. Effort sits at top level in `output_config`, not inside `thinking`. The LangChain4j builder has no `effort` method; `thinkingType` is a plain `String`.

```java
// 🚫 WRONG: there is no effort option on the builder
.thinkingType("adaptive").effort("high")
```

```java
// ✅ CORRECT
.thinkingType("adaptive")
.customParameters(Map.of("output_config", Map.of("effort", "high")))
```

## 6. Legacy or invented model IDs

Source: https://platform.claude.com/docs/en/about-claude/models/overview

```java
// 🚫 WRONG: not in the current or legacy catalog
.modelName("claude-3-5-sonnet-20241022")
```

```java
// ✅ CORRECT
.modelName("claude-sonnet-5-5")
```

## 7. midConversationSystemMessages on Claude Sonnet 5

Source: https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages: "not available on Claude Sonnet 5". The option defaults to `false` (AnthropicChatModel at tag 1.22.0).

```java
// 🚫 WRONG with Claude Sonnet 5
.midConversationSystemMessages(true)
```

```java
// ✅ CORRECT: leave the default false (all system messages go to the top-level system field),
// or use a supported model such as claude-sonnet-5-5
```

## 8. Pinning a module version next to the BOM

Source: https://docs.langchain4j.dev/get-started

```xml
<!-- 🚫 WRONG: bypasses BOM alignment -->
<artifactId>langchain4j-anthropic</artifactId><version>1.22.0</version>
```

```xml
<!-- ✅ CORRECT -->
<artifactId>langchain4j-anthropic</artifactId>
```
