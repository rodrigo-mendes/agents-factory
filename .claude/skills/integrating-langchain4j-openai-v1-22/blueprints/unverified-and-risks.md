# Unverified Register, Risks and Bibliography

Research date 2026-10-26. Back to [SKILL.md](../SKILL.md). This register lists **14 unverified items (U1-U14), 0 irresolvable items, 6 medium-confidence items (M1-M6), 3 coverage limits (L1-L3)**. The earlier question whether `gpt-6.*` models run on Chat Completions was resolved by a later source read for Astra, Luna and Terra (Sol only through a summary, see M2) and is no longer open.

## Contents

- [Tag to register mapping](#tag-to-register-mapping)
- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Source Bibliography](#source-bibliography)

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) / (medium confidence) in the version-lock note | SKILL.md header | generic note, see the lists below |
| (medium confidence, absence of evidence) | SKILL.md Version-lifetime risk; Version-lifetime risk below | none (version-lifetime note, not a register item) |
| Streaming has no `maxRetries`, no retry (medium confidence) | SKILL.md Ask First and Quick Reference; always-do-patterns.md section 3; builder-options.md | M1 |
| `maxTokens` for compatible servers; max_tokens deprecation wording (medium confidence) | SKILL.md Ask First; builder-options.md; gpt-6-and-reasoning.md | M3 |
| OpenAI-compatible behavior beyond DeepSeek is (unverified) | SKILL.md Ask First; builder-options.md | U12 |
| Docs-page claims on compatible endpoints (medium confidence) | builder-options.md; gpt-6-and-reasoning.md (`returnThinking`) | M5 |
| Official-SDK module claims (medium confidence) | SKILL.md Ask First; builder-options.md | M6 |
| BOM management of the official module is (unverified) | SKILL.md Ask First; builder-options.md | U11 |
| Azure deployment and credential options (unverified) | builder-options.md | U10 |
| Azure through `baseUrl` alone is (unverified) | SKILL.md Ask First; builder-options.md | U9 |
| Tools on Sol and Luna with effort none (medium confidence) | SKILL.md Notes; gpt-6-and-reasoning.md | M2 |
| gpt-6.1-sol Chat Completions via summary (medium confidence) | gpt-6-and-reasoning.md | M2 |
| Other `gpt-6.*` variants (unverified) | gpt-6-and-reasoning.md | U13 |
| Effort values and default effort (unverified) | SKILL.md Notes; gpt-6-and-reasoning.md | U5, U6 |
| Exception type for a rejected parameter (unverified) | gpt-6-and-reasoning.md | U14 |
| `max_tokens` rejected on GPT-6 (unverified) | gpt-6-and-reasoning.md | U4 |
| 60 s too short for long outputs (unverified) | SKILL.md Notes; always-do-patterns.md section 4 | U7 |
| `streamingBufferSize` default (unverified) | SKILL.md Ask First; builder-options.md | U8 |
| Sharing one instance across threads (unverified) | SKILL.md Notes; always-do-patterns.md section 2 | U3 |
| Module-side modelName validation (unverified) | always-do-patterns.md section 2 | U1 |
| Error from a shut-down model ID (unverified) | never-do-patterns.md section 1 | U2 |
| Inherited parameters builder methods (medium confidence) | always-do-patterns.md section 6 | M4 |
| docs pages assumed to match 1.22.0 | SKILL.md Version-lifetime risk | L1 |
| OpenAI pages unversioned; Terra model page not opened | gpt-6-and-reasoning.md | L2 |
| only named classes read | register only | L3 |

## Version-lifetime risk

- langchain4j-open-ai 1.22.0 was released on GitHub 2026-10-08 and published to Maven Central 2026-10-07 (researched 2026-10-26), so docs may still change (High, https://github.com/langchain4j/langchain4j/releases/tag/1.22.0).
- No successor release and no end-of-support date were recorded at research time (medium confidence, absence of evidence); plan upgrades by bumping the BOM and re-running tests.
- The OpenAI model catalog changes on OpenAI's schedule. Statuses listed in [never-do patterns](./never-do-patterns.md#1-choosing-a-model-from-openaichatmodelname) were read on 2026-10-26; re-check IDs before pinning (High, https://developers.openai.com/api/docs/models/all).
- `langchain4j-open-ai-official` is published as `1.22.0-beta32`; beta modules may change shape between releases (High, https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-open-ai-official/).
- The docs site is unversioned (see L1).

## Unverified items

- U1. Whether the module validates a missing `modelName` before sending the request (no build-time check exists).
- U2. The HTTP status OpenAI returns for a shut-down model ID (404 or 400).
- U3. Whether one built `OpenAiChatModel` or `OpenAiStreamingChatModel` can be shared across threads.
- U4. A GPT-6-specific statement that `max_tokens` is rejected (only generic o-series wording was found).
- U5. The default reasoning effort of GPT-6 models when `reasoningEffort` is unset.
- U6. Which `reasoningEffort` values each GPT-6 model accepts, including `none`.
- U7. Whether the 60 s default read timeout is too short for long reasoning outputs.
- U8. The default value of `streamingBufferSize`.
- U9. Whether `langchain4j-open-ai` reaches Azure OpenAI through `baseUrl`, `customHeaders` and `customQueryParams`.
- U10. Azure deployment-name and credential builder options of `langchain4j-open-ai-official`.
- U11. Whether `langchain4j-bom:1.22.0` manages the version of `langchain4j-open-ai-official`.
- U12. Provider caveats for OpenAI-compatible servers beyond the DeepSeek example (the dedicated docs page was not read).
- U13. Chat Completions support of `gpt-6.*` variants other than Astra, Luna, Sol and Terra.
- U14. The exception type LangChain4j raises when OpenAI rejects a parameter (likely `InvalidRequestException` for other 4xx; the HTTP status is not confirmed).

## Irresolvable items

None.

## Medium-confidence items

- M1. The OpenAI streaming builder has no `maxRetries` and streaming does not retry (the model source was read once and not re-read; not fully confirmed).
- M2. `gpt-6.1-sol` listing Chat Completions and the Sol and Luna function-calling rule come from a search-result summary and the guide.
- M3. `max_tokens` deprecation and o-series incompatibility come from a search snippet of the API reference (direct fetch returned 404); compatible servers may accept only `max_tokens`.
- M4. `OpenAiChatRequestParameters` builder methods inherited from the common parameters builder were not seen directly; per-request override is implied by `overrideWith`.
- M5. Compatible-endpoint claims (DeepSeek example, `returnThinking`, `sendThinking`, `accumulateToolCallId`) come from the unversioned OpenAI docs page.
- M6. Official-SDK module claims (Azure detection, GitHub Models, Responses API) come from the beta module docs page.

## Coverage limits

- L1. `docs.langchain4j.dev` pages are unversioned and track the current release; they were read on 2026-10-26 and assumed to match 1.22.0. Source files were read at tag 1.22.0.
- L2. The OpenAI catalog and guides are unversioned pages read on 2026-10-26; the `gpt-6.1-terra` model page was not opened (the guide covers it).
- L3. Only the OpenAI module classes named in [builder options](./builder-options.md) were read; `langchain4j-examples` at 1.22.0 was not opened.

## Source Bibliography

All fetched 2026-10-26. No community sources were used. Source base: `https://github.com/langchain4j/langchain4j/blob/1.22.0/`.

- https://docs.langchain4j.dev/integrations/language-models/open-ai
- https://docs.langchain4j.dev/integrations/language-models/open-ai-official
- https://docs.langchain4j.dev/get-started
- https://github.com/langchain4j/langchain4j/releases/tag/1.22.0 (published 2026-10-08)
- https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-open-ai/maven-metadata.xml
- https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-open-ai-official/
- Source base + `langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatModel.java`
- Source base + `langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiStreamingChatModel.java`
- Source base + `langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatModelName.java`
- Source base + `langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/OpenAiChatRequestParameters.java`
- Source base + `langchain4j-open-ai/src/main/java/dev/langchain4j/model/openai/internal/OpenAiUtils.java`
- Source base + `langchain4j-open-ai/pom.xml`
- Source base + `langchain4j-core/src/main/java/dev/langchain4j/internal/RetryUtils.java`
- Source base + `langchain4j-core/src/main/java/dev/langchain4j/model/chat/response/StreamingChatResponseHandler.java`
- Source base + `langchain4j-http-client/src/main/java/dev/langchain4j/http/client/log/HttpRequestLogger.java`
- https://developers.openai.com/api/docs/models/all
- https://developers.openai.com/api/docs/models/gpt-6-astra
- https://developers.openai.com/api/docs/models/gpt-6-luna
- https://developers.openai.com/api/docs/models/gpt-6.1-sol (through a search-result summary)
- https://developers.openai.com/api/docs/guides/latest-model
- https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create (search snippet only; direct fetch returned 404)
