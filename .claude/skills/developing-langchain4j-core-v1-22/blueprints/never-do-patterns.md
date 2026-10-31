# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). LangChain4j 1.22.0, research date 2026-10-26. Every row has a High-confidence alternative.

## 1. Retrying NonRetriableException

Source: https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/RetryUtils.java

```java
// 🚫 WRONG: wastes latency and quota, masks auth failures
for (int i = 0; i < 5; i++) {
    try { return model.chat(req); }
    catch (LangChain4jException e) { Thread.sleep(1000); }
}
```

```java
// ✅ CORRECT
try {
    return model.chat(req);
} catch (NonRetriableException e) {
    throw e;                       // surface immediately
} catch (RetriableException e) {
    return fallback();             // the model already retried per its policy
} catch (LangChain4jException e) {
    throw e;                       // final fallback: InvalidRequestException / ContentFilteredException retry class is (unverified), see U7
}
```

## 2. Empty onError

Source: https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/chat/response/StreamingChatResponseHandler.java

```java
// 🚫 WRONG: the stream failure is swallowed, the caller waits forever
@Override public void onError(Throwable t) { }
```

```java
// ✅ CORRECT
@Override public void onError(Throwable t) { future.completeExceptionally(t); }
```

## 3. Pinning a provider version next to the BOM

Source: https://docs.langchain4j.dev/get-started

```xml
<!-- 🚫 WRONG: bypasses BOM alignment -->
<dependency>
  <groupId>dev.langchain4j</groupId><artifactId>langchain4j-open-ai</artifactId><version>1.22.0</version>
</dependency>
```

```xml
<!-- ✅ CORRECT: version comes from langchain4j-bom:1.22.0 -->
<dependency>
  <groupId>dev.langchain4j</groupId><artifactId>langchain4j-open-ai</artifactId>
</dependency>
```

## 4. Hardcoding an API key

Source: https://docs.langchain4j.dev/integrations/language-models/open-ai (the official sample reads the key with `System.getenv`).

```java
// 🚫 WRONG
String apiKey = "sk-...";
```

```java
// ✅ CORRECT
String apiKey = System.getenv("LLM_API_KEY");
```

## 5. logRequests / logResponses in production

Source (High, read at tag 1.22.0 on 2026-10-26): https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-http-client/src/main/java/dev/langchain4j/http/client/log/HttpRequestLogger.java. The option lives on provider builders, so details are in the provider sibling skills. Header secrets are masked (first 5 and last 2 characters) but the body, which holds prompts and personal data, is logged unmasked at INFO through SLF4J.

```java
// 🚫 WRONG in production: prompts and PII reach the logs
// builder.logRequests(true).logResponses(true)
```

```java
// ✅ CORRECT: explicitly off in production; enable only while debugging locally
// builder.logRequests(false).logResponses(false)
```

## Medium-confidence cautions (not Never Do)

These stay in Ask First in [SKILL.md](../SKILL.md) because their sources are single unversioned docs pages (medium confidence): blocking inside listeners, thread-locals across streaming callbacks, end-user text in `SystemMessage`. Wrong and right shapes:

```java
// Wrong: MDC.put("start", ...) in onRequest, read in onResponse (streaming runs them on different threads)
// Right: ctx.attributes().put("startNanos", System.nanoTime()) in onRequest; read ctx.attributes() in onResponse
// Wrong: SystemMessage.from("You are helpful. " + userInput)
// Right: List.of(SystemMessage.from("You are helpful."), UserMessage.from(userInput))
```
