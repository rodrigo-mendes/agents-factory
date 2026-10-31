# Errors and Retry

Back to [SKILL.md](../SKILL.md). LangChain4j 1.22.0, research date 2026-10-26. Sources read at tag 1.22.0 under `https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/`: `internal/ExceptionMapper.java`, `internal/RetryUtils.java`, `exception/*.java`.

## Status mapping (`DefaultExceptionMapper`, root cause `HttpException`)

| Trigger | Exception | Retried by `RetryUtils` |
|---|---|---|
| HTTP 5xx | `InternalServerException` | yes (RetriableException) |
| HTTP 401, 403 | `AuthenticationException` | no (NonRetriableException) |
| HTTP 404 | `ModelNotFoundException` | no (NonRetriableException) |
| HTTP 408 | `TimeoutException` | yes (RetriableException) |
| HTTP 429 | `RateLimitException` | yes (RetriableException) |
| other 4xx | `InvalidRequestException` | retry class (unverified), see U7; treat as not retried until confirmed |
| `UnresolvedAddressException` | `UnresolvedModelServerException` | no (NonRetriableException) |

`ContentFilteredException` extends `InvalidRequestException`, so its retry class is also (unverified), see U7. Base class: `LangChain4jException extends RuntimeException`. The package and base class of `RetriableException` and `NonRetriableException` are (unverified), see U13; the code below uses only the concrete classes. Only HTTP 408 maps to `TimeoutException`; other client-side timeouts fall through to generic mapping.

## Default retry policy

Source: https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/RetryUtils.java

`withRetryMappingExceptions(action, maxRetries)` maps exceptions through `ExceptionMapper.DEFAULT`, then applies `DEFAULT_RETRY_POLICY`: maxRetries 2 (up to 3 executions), base delay 500 ms, backoff exponent 1.5, jitter 0.2. The 1000 ms value is only the `Builder` field default and is overridden. `NonRetriableException` is rethrown at once. Async retries use `CompletableFuture.delayedExecutor` and never retry `CancellationException` (async helpers since 1.20.0).

Whether every provider exposes `maxRetries` or timeout builder options, and whether every provider applies this policy, is (unverified) here; see the provider sibling skills.

## Classify and branch

```java
// LangChain4j 1.22.0
try {
    ChatResponse r = model.chat(request);
} catch (RateLimitException | dev.langchain4j.exception.TimeoutException e) {
    // retriable: the model already retried per its policy; back off or degrade
} catch (InternalServerException e) {
    // retriable (HTTP 5xx): already retried by the model; back off or degrade
} catch (AuthenticationException | ModelNotFoundException e) {
    // non-retriable: fix credentials or the model name, do not retry
} catch (LangChain4jException e) {
    // final fallback for every other class, including InvalidRequestException and
    // ContentFilteredException, whose retry classification is (unverified), see U7
}
```

Scope: the branching above covers only the classes read at 1.22.0 (see L2).

`dev.langchain4j.exception.TimeoutException` is written fully qualified to avoid a clash with `java.util.concurrent.TimeoutException`.

## Rules for callers

- Do not wrap `model.chat` in your own retry loop for non-retriable classes (see [never-do](./never-do-patterns.md#1-retrying-nonretriableexception)).
- Do not add retry around a streaming call expecting model-level retry: streaming does not retry (medium confidence).
- Keep the total of your own retries plus model retries within your caller's timeout budget.
