# Always-Do Patterns

Back to [SKILL.md](../SKILL.md). LangChain4j 1.22.0, research date 2026-10-26.

## 1. Import the BOM

Source: https://docs.langchain4j.dev/get-started (fetched 2026-10-26).

```xml
<!-- LangChain4j 1.22.0 -->
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>dev.langchain4j</groupId>
      <artifactId>langchain4j-bom</artifactId>
      <version>1.22.0</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>
```

Some modules in the BOM are still published as `1.22.0-beta32`; that is expected and managed by the BOM.

## 2. Declare modules without versions

```xml
<!-- the provider module brings langchain4j-core (compile scope); no <version> -->
<dependencies>
  <dependency>
    <groupId>dev.langchain4j</groupId>
    <artifactId>langchain4j-open-ai</artifactId>
  </dependency>
</dependencies>
```

`langchain4j-open-ai` and `langchain4j-anthropic` are stable 1.22.0 releases. Provider options are in the sibling skills `integrating-langchain4j-openai-v1-22` and `integrating-langchain4j-provider-a-v1-22`.
Core arrives transitively: both provider poms at tag 1.22.0 list `langchain4j-core` and `langchain4j-http-client` in compile scope (https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/pom.xml).

## 3. Blocking call with request and response

```java
// LangChain4j 1.22.0; `model` is a ChatModel built by a provider module
ChatRequest request = ChatRequest.builder()
    .messages(SystemMessage.from("Answer briefly."), UserMessage.from("What is LangChain4j?"))
    .build();
ChatResponse response = model.chat(request);
AiMessage ai = response.aiMessage();
TokenUsage usage = response.metadata().tokenUsage();
FinishReason reason = response.metadata().finishReason();   // STOP | LENGTH | TOOL_EXECUTION | CONTENT_FILTER | OTHER
```

Optional (medium confidence, chat docs page): the builder shortcuts `.temperature(0.2)` and `.maxOutputTokens(300)` can be added before `.build()`.

`chat(request)` delegates to `chat(request, ChatRequestOptions.EMPTY)`, merges default parameters, notifies listeners, calls `doChat`, then reports the response or the error (https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/chat/ChatModel.java).
`TokenUsage` also has `add(TokenUsage)` and `static sum(a, b)`; whether the counts can be null is (unverified).

Message types: `SystemMessage`, `UserMessage`, `AiMessage`, `ToolExecutionResultMessage`. Content types: `TextContent`, `ImageContent`, `AudioContent`, `VideoContent`, `PdfFileContent` (chat docs page, medium confidence).

## 4. Parameter precedence

```java
// overrideWith: the ARGUMENT wins. defaultedBy: the RECEIVER wins (default impl throws UnsupportedOperationException).
ChatRequestParameters merged = modelDefaults.overrideWith(perRequest);
```

Source: https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/model/chat/request/ChatRequestParameters.java

## 5. Read keys from the environment

```java
// Never hardcode keys; official docs sample: https://docs.langchain4j.dev/integrations/language-models/open-ai
String apiKey = System.getenv("LLM_API_KEY");
if (apiKey == null || apiKey.isBlank()) {
    throw new IllegalStateException("LLM_API_KEY is not set");
}
```

The environment variable name is yours; the provider builder that consumes the key is in the provider sibling skills.
