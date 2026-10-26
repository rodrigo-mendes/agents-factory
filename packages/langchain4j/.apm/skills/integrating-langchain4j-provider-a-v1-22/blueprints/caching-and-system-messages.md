# Prompt Caching and System Messages

Back to [SKILL.md](../SKILL.md). langchain4j-anthropic 1.22.0, research date 2026-10-26.

Sources: https://github.com/langchain4j/langchain4j/releases/tag/1.22.0 (release notes), https://docs.langchain4j.dev/integrations/language-models/anthropic (unversioned), `AnthropicChatModel.java` at tag 1.22.0 (https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java).

## Prompt caching

Caching is off by default. In 1.22.0, `cacheAutomatically` and `cacheTtl` (`"5m"` or `"1h"`) are new (PR 6598). `cache_control` goes only on the last tool (PR 6515) and only on the last system message (PR 6070).

Limits from the docs page (medium confidence, see M3): at most 4 cache breakpoints per request; prompts below a model-specific minimum (512 to 4,096 tokens) are not cached. Token usage reports cache-creation and cache-read counts.

### Choosing a mode

| Option | Best when | Sacrifices |
|---|---|---|
| `cacheSystemMessages(true)` / `cacheTools(true)` | fixed system prompt or tool set reused across independent calls | needs a stable prefix |
| `cacheAutomatically(true)` | growing multi-turn conversations | a poor fit when the start of the conversation changes |
| `cacheTtl("1h")` | infrequent but repeated traffic | higher cache-write cost |

```java
// stable system prompt, repeated traffic; langchain4j-anthropic 1.22.0
ChatModel model = AnthropicChatModel.builder()
        .apiKey(System.getenv("ANTHROPIC_API_KEY"))
        .modelName("claude-sonnet-5-5")
        .maxTokens(4096)
        .cacheSystemMessages(true)
        .cacheTtl("1h")                 // default is 5m
        .build();
```

```java
// growing conversation
AnthropicChatModel.builder()
        .modelName("claude-sonnet-5-5")
        .maxTokens(4096)
        .cacheAutomatically(true)
        .build();
```

Mix the modes only after reading the breakpoint limit above. Cache read price is a fraction of base input price (Anthropic pricing page, not read in full); monitor the cache-read token counts instead of assuming savings.

## System messages

By default (`midConversationSystemMessages` is `false`), every `SystemMessage` goes to the top-level `system` field of the request, whatever its position in the list (read at tag 1.22.0).

```java
// langchain4j-anthropic 1.22.0
ChatRequest request = ChatRequest.builder()
        .messages(SystemMessage.from("You answer in one sentence."), UserMessage.from(userInput))
        .build();
```

Keep end-user text out of the `SystemMessage` and pass it as a `UserMessage`, as in the core skill.

### Mid-conversation system messages

`midConversationSystemMessages(true)` sends later system messages inline in the conversation. Per https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages (fetched 2026-10-26):

- Supported on Fable 5.1, Mythos 5.1, Fable 5, Mythos 5, Opus 5.5, Opus 5, Sonnet 5.5, Haiku 5.5 and Opus 4.8; no beta header needed.
- Not available on Claude Sonnet 5.
- Opus 4.7 rejects it with a 400 error (medium confidence, search summary, see M4).
- Placement rules from the LangChain4j docs page (medium confidence, see M6): the system message must follow a user turn, cannot sit between a tool_use and its tool_result, and cannot repeat consecutively. Invalid placement returns a 400.

```java
// only on a supported model, only when system messages arrive mid-conversation
AnthropicChatModel.builder()
        .modelName("claude-sonnet-5-5")
        .maxTokens(4096)
        .midConversationSystemMessages(true)
        .build();
```
