# GPT-6 and Reasoning-Model Rules

Back to [SKILL.md](../SKILL.md). langchain4j-open-ai 1.22.0; OpenAI pages read 2026-10-26. The OpenAI catalog and guides are unversioned and change on OpenAI's schedule.

## Chat Completions support

| Model ID | Chat Completions (`v1/chat/completions`) | Source |
|---|---|---|
| `gpt-6-astra` | listed on the model page | https://developers.openai.com/api/docs/models/gpt-6-astra |
| `gpt-6-luna` | listed on the model page | https://developers.openai.com/api/docs/models/gpt-6-luna |
| `gpt-6.1-sol` | listed on the model page, seen through a search-result summary (medium confidence) | https://developers.openai.com/api/docs/models/gpt-6.1-sol |
| `gpt-6.1-terra` | stated in the guide; the model page was not opened | https://developers.openai.com/api/docs/guides/latest-model |

Other `gpt-6.*` variants were not checked (unverified). Smoke-test a new ID with one `chat("ping")` call before wiring it into production.

Tool calling (out of scope here) per the guide: on Astra, Sol (medium confidence) and Terra it requires the Responses API; Sol (medium confidence) and Luna allow function calling on Chat Completions only with `reasoning_effort: "none"` (medium confidence, because the Sol page was seen only through a summary).

## Sampling parameters

Source: https://developers.openai.com/api/docs/guides/latest-model: "When reasoning effort is not `none`, remove `temperature`, `top_p`, and `top_logprobs`." On Chat Completions `logprobs` must also be removed.

```java
// langchain4j-open-ai 1.22.0: effort not none -> no sampling parameters
OpenAiChatModel reasoning = OpenAiChatModel.builder()
        .apiKey(System.getenv("OPENAI_API_KEY"))
        .modelName("gpt-6-astra")
        .reasoningEffort("low")            // sent verbatim, never validated by the builder
        .maxCompletionTokens(1000)
        .build();

// effort none -> sampling parameters may be set again
OpenAiChatModel sampled = OpenAiChatModel.builder()
        .apiKey(System.getenv("OPENAI_API_KEY"))
        .modelName("gpt-6-astra")
        .reasoningEffort("none")
        .temperature(0.2)
        .build();
```

The builder forwards `reasoningEffort` as given (`OpenAiUtils.java` at 1.22.0), so a wrong value or a forbidden parameter fails at the API, not at build time. Which values each GPT-6 model accepts, whether `none` is accepted by every model, and the default effort when the field is unset are all (unverified); when unsure, omit `temperature` and `topP`. The exception type returned for a rejected parameter is (unverified); other 4xx map to `InvalidRequestException` in the core skill's table.

## Output limit

Source: https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/internal/OpenAiUtils.java

- `maxCompletionTokens(Integer)` is sent as `max_completion_tokens`.
- `maxTokens(Integer)` is sent as `max_tokens`. The builder converts neither into the other.
- OpenAI's API reference describes `max_tokens` as deprecated in favor of `max_completion_tokens` and not compatible with o-series models; `max_completion_tokens` counts visible and reasoning tokens (medium confidence). The reference page returned 404 on a direct fetch and the wording came from a search snippet.
- A GPT-6-specific statement that `max_tokens` is rejected was not found (unverified).

Use `maxCompletionTokens` against api.openai.com. For an OpenAI-compatible server that only understands `max_tokens`, ask first (see [options](./builder-options.md#openai-compatible-endpoints)).

## Reasoning output

`returnThinking(true)` puts `reasoning_content` into `AiMessage.thinking()` and streams it through `onPartialThinking`; the docs present it for DeepSeek, not for OpenAI models (medium confidence). Do not rely on it for GPT-6.
