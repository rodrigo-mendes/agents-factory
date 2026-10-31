# Testing with a ChatModel Test Double

Back to [SKILL.md](../SKILL.md). LangChain4j 1.22.0, research date 2026-10-26.

## What is known

- No official ChatModel testing recipe was found for 1.22.0 (medium confidence, absence of evidence).
- The official AI Services tutorial says an AI Service is an interface and can be mocked (unverified: taken from a search snippet, page not read); AI Services are out of scope here.
- `dev.langchain4j:langchain4j-test:1.22.0-beta32` contains only `dev/langchain4j/test/guardrail` at tag 1.22.0. The LLM-judge and `ChatRequestAssert` utilities were merged after 1.22.0 and are not part of this version (medium confidence).
- The provider poms use `ai-mocks-openai-jvm` and `ai-mocks-anthropic-jvm` as their own test dependencies; that is how the project tests itself, not guidance for users.

## Hand-written double (unverified)

`ChatModel` has no abstract methods; every method is `default` and implementors override `doChat(ChatRequest)` (source at 1.22.0: https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/chat/ChatModel.java). Using that as a test double is derived from the source and is (unverified) as an officially recommended practice.

```java
// LangChain4j 1.22.0 (unverified as official practice)
ChatModel fake = new ChatModel() {
    @Override public ChatResponse doChat(ChatRequest req) {
        return ChatResponse.builder()
            .aiMessage(AiMessage.from("stubbed"))
            .tokenUsage(new TokenUsage(1, 1))      // (unverified) builder field names and constructor
            .finishReason(FinishReason.STOP)
            .build();
    }
};
assertEquals("stubbed", fake.chat("hi"));
```

- Default `listeners()` being empty is (unverified).
- Run `mvn -q test` after writing the double; a compile error on `ChatResponse.builder()` means the field names differ and must be read from the 1.22.0 source.

## Mockito alternative (medium confidence, derived from source, no official recipe)

`mock(ChatModel.class)` works mechanically, but `chat(String)` is a default method that delegates; stub the overload your code under test actually calls.

## Streaming double

No streaming double was researched: (unverified). Implement a `StreamingChatModel` subclass only after reading its source at tag 1.22.0.
