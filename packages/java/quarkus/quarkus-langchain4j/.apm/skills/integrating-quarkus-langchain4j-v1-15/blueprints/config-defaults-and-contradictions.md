# Config defaults and contradictions

Back to [SKILL.md](../SKILL.md). Research date 2026-10-28. Source ids resolve in the [source bibliography](./source-bibliography.md). "Doc default" means a `@ConfigDocDefault` value; "runtime" means `@WithDefault` or a recorder fallback. All values are at tag 1.15.0.CR1 unless noted. docs.quarkiverse.io publishes only `dev`, which runs ahead of the tag; where they differ the tag wins (family rule 11: a value that only appears in an example is "the example").

## Contents

- [Global and tracing keys](#global-and-tracing-keys)
- [OpenAI keys](#openai-keys)
- [Anthropic keys](#anthropic-keys)
- [Bedrock keys](#bedrock-keys)
- [Contradictions](#contradictions)

## Global and tracing keys

| Key | Default | Source |
|---|---|---|
| `quarkus.langchain4j.timeout` | doc `10s`, no `@WithDefault`; recorders fall back to `Duration.ofSeconds(10)` | S24, S20, S23 |
| `quarkus.langchain4j.log-requests` | doc `false` | S24 |
| `quarkus.langchain4j.log-responses` | doc `false` | S24 |
| `quarkus.langchain4j.log-requests-curl` | doc `false` | S24 |
| `quarkus.langchain4j.temperature` | no documented default | S24 |
| `quarkus.langchain4j.tracing.include-prompt` | `false` | S25 |
| `quarkus.langchain4j.tracing.include-completion` | `false` | S25 |
| `quarkus.langchain4j.tracing.include-tool-arguments` | `false` | S25 |
| `quarkus.langchain4j.tracing.include-tool-result` | `false` | S25 |

## OpenAI keys

| Key | Default | Source |
|---|---|---|
| `quarkus.langchain4j.openai.api-key` | `dummy` | S18 |
| `quarkus.langchain4j.openai.base-url` | `https://api.openai.com/v1/` | S18 |
| `quarkus.langchain4j.openai.timeout` | doc `10s` (`${quarkus.langchain4j.timeout}`) | S18 |
| `quarkus.langchain4j.openai.max-retries` | `1`, deprecated | S18 |
| `quarkus.langchain4j.openai.log-requests`, `log-responses` | doc `false` | S18 |
| `quarkus.langchain4j.openai.enable-integration` | `true` | S18 |
| `quarkus.langchain4j.openai.chat-model.model-name` | `gpt-4o-mini` (also at 1.14.2) | S19, S36 |
| `quarkus.langchain4j.openai.chat-model.temperature` | doc "the model's default" | S19 |
| `quarkus.langchain4j.openai.chat-model.max-tokens` | `@Deprecated`; `max-completion-tokens` exists | S19 |
| `quarkus.langchain4j.openai.chat-model.mode` | tag docs: Chat Completions, build-time; declaration and default not located (medium confidence, absence of evidence, I2) | S33 |
| `quarkus.langchain4j.openai.proxy-type`, `proxy-host`, `proxy-port` | `@Deprecated(forRemoval = true)`; use `proxy-configuration-name` | S18 |

The dummy-key check (`SRCFG00014 ... is required`) applies only with the default base URL [S20].

## Anthropic keys

| Key | Default | Source |
|---|---|---|
| `quarkus.langchain4j.anthropic.api-key` | `dummy` | S21 |
| `quarkus.langchain4j.anthropic.base-url` | `https://api.anthropic.com/v1/` | S21 |
| `quarkus.langchain4j.anthropic.version` | `2023-06-01` | S21 |
| `quarkus.langchain4j.anthropic.timeout` | doc `10s` (`${quarkus.langchain4j.timeout}`) | S21 |
| `quarkus.langchain4j.anthropic.log-requests`, `log-responses` | doc `false` | S21 |
| `quarkus.langchain4j.anthropic.enable-integration` | `true` | S21 |
| `quarkus.langchain4j.anthropic.chat-model.model-name` | `claude-3-haiku-20240307` | S22 |
| `quarkus.langchain4j.anthropic.chat-model.max-tokens` | `1024` | S22 |
| `quarkus.langchain4j.anthropic.chat-model.temperature` | doc `0.7` | S22 |
| `quarkus.langchain4j.anthropic.chat-model.max-retries` | `1`, deprecated | S22 |

`max-retries` of `1` means "exactly one attempt, with retrying disabled" [S18][S22]. The streaming builders do not read it (medium confidence, M5) [S20][S23].

## Bedrock keys

Key spellings (`aws.*`, `client.*`) come from the `dev` config table [S10] and match the method names of the tag interfaces [S27][S29][S30] (kebab-case mapping). The Bedrock page does not exist at the tag, so prose claims rest on the `dev` page plus tag code (medium confidence, absence of evidence, I1).

| Key | Default | Source |
|---|---|---|
| `quarkus.langchain4j.bedrock.aws.region` | doc "default aws region provider chain"; not set in code unless configured | S27, S31 |
| `quarkus.langchain4j.bedrock.aws.credentials-provider` | doc "default aws credentials provider chain" | S27, S31 |
| `quarkus.langchain4j.bedrock.aws.endpoint-override` | none | S27 |
| `quarkus.langchain4j.bedrock.aws.max-retries` | doc `3`; code `firstOrDefault(3, ...)` | S27, S31 |
| `quarkus.langchain4j.bedrock.aws.api-call-timeout` | doc `13s`; code falls back to `Duration.ofSeconds(10)` (medium confidence, M14; C3) | S27, S31 |
| `quarkus.langchain4j.bedrock.client.connect-timeout` | doc `3s` | S29 |
| `quarkus.langchain4j.bedrock.client.timeout` | doc `10s` (read timeout) | S29 |
| `quarkus.langchain4j.bedrock.client.keep-alive-enabled` | doc `true` | S29 |
| `quarkus.langchain4j.bedrock.log-requests`, `log-responses`, `log-body` | doc `false` | S30 |
| `quarkus.langchain4j.bedrock.chat-model.model-id` | doc `global.amazon.nova-2-lite-v1:0`, no `@WithDefault` (unverified, U5) | S28 |
| `quarkus.langchain4j.bedrock.chat-model.temperature` | doc `0.7` | S28 |
| `quarkus.langchain4j.bedrock.chat-model.max-tokens` | `1024` | S28 |
| `quarkus.langchain4j.bedrock.chat-model.top-p` | doc `1.0` | S28 |
| `quarkus.langchain4j.bedrock.chat-model.prompt-caching-ttl` | doc `5m` | S28 |
| `quarkus.langchain4j.bedrock.enable-integration` | `true` per the `dev` table (medium confidence, M10) | S10 |

`api-call-timeout` covers the whole call "including retries" [S27]. Bedrock proxy keys are deprecated like the OpenAI ones [S29].

## Contradictions

| ID | Topic | Statement A | Statement B | Handling |
|---|---|---|---|---|
| C1 | OpenAI default model | tag `@WithDefault("gpt-4o-mini")`, also at 1.14.2 [S19][S36] | `dev` table shows `gpt-6-luna` (tool summary, no verbatim sentence) (medium confidence, M17) [S8] | The tag wins; set the model explicitly |
| C2 | Anthropic default model | code `@WithDefault("claude-3-haiku-20240307")` [S22] | tag docs "By default, the extension uses the latest available Claude model." [S34] (https://raw.githubusercontent.com/quarkiverse/quarkus-langchain4j/1.15.0.CR1/docs/modules/ROOT/pages/anthropic-chat-model.adoc) | Code is the runtime truth; set the model explicitly |
| C3 | Bedrock `aws.api-call-timeout` | `@ConfigDocDefault("13s")` [S27], also in the `dev` table [S10] | recorder `firstOrDefault(Duration.ofSeconds(10), ...)` [S31]; whether a condition guards that line was not read (medium confidence, M14) | Cite both; set it explicitly |
| C4 | OpenAI API mode | tag docs: "By default, the chat model targets OpenAI's `/v1/chat/completions` endpoint." [S33] | `dev`: default `auto`, "When not set, the mode is selected automatically:" [S8] | The tag wins for the CR; expect a change at the final |
| C5 | Where to put API keys | extension docs suggest the environment variable `QUARKUS_LANGCHAIN4J_OPENAI_API_KEY` [S33] and `OPENAI_API_KEY` [S16] | AWS: Secrets Manager "instead of environment variables" [S43]; family rule 5 | AWS and rule 5 win on Lambda |

Between 1.14.2 and 1.15.0.CR1 the spot-checked defaults are identical: OpenAI `gpt-4o-mini`; Bedrock `modelId` doc default, `temperature`, `maxTokens`, `topP` [S36]. The full diff could not be rendered (medium confidence, absence of evidence, I3).
