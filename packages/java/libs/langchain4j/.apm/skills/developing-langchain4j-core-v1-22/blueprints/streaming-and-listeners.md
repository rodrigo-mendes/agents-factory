# Streaming, Listeners and Async

Back to [SKILL.md](../SKILL.md). LangChain4j 1.22.0, research date 2026-10-26.

## Streaming handler

Abstract methods: `onCompleteResponse(ChatResponse)` and `onError(Throwable)`. Defaults (no-op): `onPartialResponse`, `onPartialThinking`, `onPartialToolCall`, `onCompleteToolCall`, `onUnmappedRawEvent`. Source at tag 1.22.0: https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/chat/response/StreamingChatResponseHandler.java

```java
// LangChain4j 1.22.0; `streamingModel` is a StreamingChatModel built by a provider module;
// `chatRequest` is built as in always-do-patterns #3
CompletableFuture<ChatResponse> future = new CompletableFuture<>();
streamingModel.chat(chatRequest, new StreamingChatResponseHandler() {
    @Override public void onPartialResponse(String partial) { System.out.print(partial); }
    @Override public void onCompleteResponse(ChatResponse r) { future.complete(r); }
    @Override public void onError(Throwable t) { future.completeExceptionally(t); }
});
ChatResponse full = future.join();
```

Javadoc `@since` markers: `onPartialThinking`, `onPartialToolCall`, `onCompleteToolCall` 1.2.0; context overloads 1.8.0; `onUnmappedRawEvent` 1.17.0 (same source).

## Streaming and retries

Streaming models do not retry: `AnthropicStreamingChatModel` has no `maxRetries` and no retry call, and OpenAI streaming has no `maxRetries` option (medium confidence). Handle a failed stream in `onError` and decide in your code whether to start a new request.

## Cancelling a stream

`PartialResponseContext.streamingHandle().cancel()` closes the connection; no callbacks follow (medium confidence). Source: https://docs.langchain4j.dev/tutorials/response-streaming

## ChatModelListener (observability)

Source: https://docs.langchain4j.dev/tutorials/observability (medium confidence; unversioned page).

- Listeners run synchronously in list order, once per call; retries do not re-fire them (medium confidence).
- A listener exception is logged at WARN and the other listeners still run (medium confidence).
- For streaming, listener `onResponse` fires before the handler's `onCompleteResponse`; listener `onError` fires before the handler's `onError` (medium confidence).
- `onRequest`, `onResponse` and `onError` run on different threads for streaming; use `ctx.attributes()` to carry values (medium confidence).
- Callbacks run on the I/O thread: offload slow work (medium confidence).

```java
// Shape only; method and context names from the observability docs (medium confidence)
public void onResponse(ChatModelResponseContext c) {
    executor.submit(() -> store.save(c.chatResponse()));   // not on the I/O thread
}
```

## Async and reactive options

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `ChatModel.chat` (blocking) | simplicity | one thread per call | batch and back-office work |
| `ChatModel.chatAsync` returning `CompletableFuture` (`@Experimental`) | non-blocking | API stability | async services |
| `StreamingChatModel` with handler | time to first token | callback complexity | token streaming to a UI |
| Reactive `Flow.Publisher<ChatModelStreamingEvent>` (experimental) | backpressure-aware integration | stability; overflow if demand is below `Long.MAX_VALUE` (medium confidence) | reactive stacks |

All except blocking and the handler are Ask First (experimental APIs; see SKILL.md Ask First). Kotlin: `chatAsync(ChatRequest)` resolves to the Java member returning `CompletableFuture`; call `.await()` or pass a coroutine context. The version that introduced this is (unverified).
