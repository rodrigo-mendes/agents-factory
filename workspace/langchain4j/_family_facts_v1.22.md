# Family facts — langchain4j 1.22.0

Verified by the orchestrator on 2026-10-26. Authors never edit this file.

| ID | Fact | Confidence | Source (URL, page read date) | Used by |
|---|---|---|---|---|
| F1 | Target version: LangChain4j 1.22.0 (GitHub release 2026-10-08; Maven Central 2026-10-07), latest stable | High | https://github.com/langchain4j/langchain4j/releases ; https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-open-ai/maven-metadata.xml (2026-10-26) | all |
| F2 | BOM: `dev.langchain4j:langchain4j-bom:1.22.0`, type pom, scope import; some modules in the BOM still use `1.22.0-beta32` | High | https://docs.langchain4j.dev/get-started (2026-10-26) | all |
| F3 | `langchain4j-open-ai` and `langchain4j-anthropic` are released as 1.22.0 (stable, not beta) | High | Maven Central maven-metadata.xml for both artifacts (2026-10-26) | openai, anthropic |
| F4 | Minimum supported JDK is 17 | High | https://docs.langchain4j.dev/get-started (2026-10-26) | all |
| F5 | HTTP status mapping (core `ExceptionMapper`): 5xx→InternalServerException; 401/403→AuthenticationException; 404→ModelNotFoundException; 408→TimeoutException; 429→RateLimitException; other 4xx→InvalidRequestException; UnresolvedAddressException→UnresolvedModelServerException | High | https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/ExceptionMapper.java (2026-10-26) | all |
| F6 | Default retry policy: maxRetries 2 (up to 3 attempts), delay 500 ms, backoff 1.5, jitter 0.2; `NonRetriableException` subclasses are rethrown immediately | High | https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/RetryUtils.java (2026-10-26) | all |
| F7 | Provider modules declare `langchain4j-core` (compile) transitively | High (from gap research S-ids, pom.xml at tag 1.22.0) | research_LangChain4j_gaps_v1.22.0.md item 6 | all |
| F8 | `logRequests`/`logResponses` mask secret headers (first 5 + last 2 chars) but log the request/response body unmasked (prompts, PII); logger is SLF4J at INFO | High | https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-http-client/src/main/java/dev/langchain4j/http/client/log/HttpRequestLogger.java (re-read by orchestrator 2026-10-26; secret keywords: auth, api-key, token, secret, password, credential, cookie...) | openai, anthropic |
| F9 | Streaming chat models: `AnthropicStreamingChatModel` does not retry; OpenAI streaming has no `maxRetries` option | (medium confidence) | gap research item 5; openai research | core, openai, anthropic |
| F10 | No official ChatModel testing recipe for 1.22.0; `langchain4j-test` test utilities for LLM-judge landed after 1.22.0 | (medium confidence) | gap research item 9 | core |
