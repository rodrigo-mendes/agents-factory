# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). langchain4j-open-ai 1.22.0, research date 2026-10-26. Every row has a High-confidence alternative.

## 1. Choosing a model from `OpenAiChatModelName`

Sources: https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatModelName.java ; https://developers.openai.com/api/docs/models/all (both read 2026-10-26).

The 1.22.0 enum ends at `GPT_5_1` and contains none of the `gpt-6*` IDs. On 2026-10-26 the catalog marked as Shut down: `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo`, `o1`, `o3-mini`, `o4-mini`, `gpt-4.1-nano`. It marked as Deprecated: `gpt-4o`, `gpt-4o-mini`, `gpt-4.1`, `gpt-4.1-mini`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `gpt-5.1`, `o3`. The error a shut-down ID produces (404 or 400) is (unverified).

```java
// 🚫 WRONG: O4_MINI is Shut down in the catalog
OpenAiChatModel.builder().apiKey(key).modelName(OpenAiChatModelName.O4_MINI).build();
```

```java
// ✅ CORRECT: string ID copied from the catalog
OpenAiChatModel.builder().apiKey(key).modelName("gpt-6-astra").build();
```

## 2. Hardcoding the API key

Source: https://docs.langchain4j.dev/integrations/language-models/open-ai (the official sample reads the key from the environment).

```java
// 🚫 WRONG: the key leaks through version control and logs
OpenAiChatModel.builder().apiKey("sk-proj-...").modelName("gpt-6-astra").build();
```

```java
// ✅ CORRECT
OpenAiChatModel.builder().apiKey(System.getenv("OPENAI_API_KEY")).modelName("gpt-6-astra").build();
```

## 3. Request and response logging in production

Source: https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-http-client/src/main/java/dev/langchain4j/http/client/log/HttpRequestLogger.java

Secret headers are masked (first 5 and last 2 characters of values with 7 or more characters), but the body, which holds prompts, completions and personal data, is logged unmasked at INFO through SLF4J. Both options default to `false`.

```java
// 🚫 WRONG in production
OpenAiChatModel.builder().apiKey(key).modelName("gpt-6-astra").logRequests(true).logResponses(true).build();
```

```java
// ✅ CORRECT: off by default; switch on only through an explicit local flag
OpenAiChatModel.builder().apiKey(key).modelName("gpt-6-astra")
        .logRequests(Boolean.getBoolean("llm.debug"))
        .logResponses(Boolean.getBoolean("llm.debug"))
        .build();
```

## 4. Sampling parameters on GPT-6 with reasoning effort

Source: https://developers.openai.com/api/docs/guides/latest-model (read 2026-10-26): "When reasoning effort is not `none`, remove `temperature`, `top_p`, and `top_logprobs`."

```java
// 🚫 WRONG: temperature sent while reasoning effort is not none
OpenAiChatModel.builder().apiKey(key).modelName("gpt-6-astra")
        .reasoningEffort("low").temperature(0.2).build();
```

```java
// ✅ CORRECT: omit sampling parameters
OpenAiChatModel.builder().apiKey(key).modelName("gpt-6-astra")
        .reasoningEffort("low").maxCompletionTokens(1000).build();
```

If sampling control is required, set effort `none` instead (see [GPT-6 rules](./gpt-6-and-reasoning.md#sampling-parameters)).
