# Unverified Register, Risks and Bibliography

Research date 2026-10-26. Back to [SKILL.md](../SKILL.md). This register lists **6 unverified items (U1-U6), 0 irresolvable items, 9 medium-confidence items (M1-M9), 3 coverage limits (L1-L3)**. A later source read (2026-10-26) resolved the adaptive thinking literal, the effort mechanism, the missing build-time `modelName` check, the streaming retry behavior and `midConversationSystemMessages` model support; it left the request-time `modelName` check and the `InvalidRequestException` hierarchy open.

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
| request-time validation is (unverified) / (unverified), see U1 | SKILL.md Notes; always-do-patterns.md | U1 |
| The retry class of `InvalidRequestException` is (unverified) | SKILL.md Notes | U2 |
| their API ID strings were not collected (unverified), see U3 | always-do-patterns.md | U3 |
| (unverified as an official practice) | SKILL.md Notes | U4 |
| (log output unverified) | SKILL.md Quick Reference | U5 |
| which levels each model accepts is (unverified), see U6 / availability per model is (unverified) | SKILL.md Ask First; thinking-and-effort.md | U6 |
| the streaming model does not retry (medium confidence) / has no `maxRetries` (medium confidence) | SKILL.md Ask First; always-do-patterns.md; builder-options.md | M1 |
| recent models may return empty thinking (medium confidence) / (medium confidence, docs page unversioned, see M2) | SKILL.md Ask First; thinking-and-effort.md | M2 |
| model-specific minimum prompt size (medium confidence) / Limits from the docs page (medium confidence, see M3) | SKILL.md Ask First; caching-and-system-messages.md | M3 |
| Opus 4.7 rejects it with a 400 error (medium confidence, search summary, see M4) | caching-and-system-messages.md | M4 |
| `low`, `medium`, `high`, `xhigh`, `max` exist (medium confidence) / (medium confidence, effort page read through a search summary) | SKILL.md Ask First; thinking-and-effort.md | M5 |
| Placement rules are (medium confidence) / (medium confidence, see M6) | SKILL.md Ask First; caching-and-system-messages.md | M6 |
| (medium confidence for options not seen in source) / (docs page, medium confidence) / Builder method `maxOutputTokens` ... (medium confidence) | builder-options.md | M7 |
| (medium confidence, inference from the unmasked body logging at tag 1.22.0) | thinking-and-effort.md | M8 |
| `.beta(...)` values change over time (medium confidence) | SKILL.md Ask First | M9 |
| assumed to match 1.22.0 (medium confidence) | SKILL.md Version-lifetime risk | L1 |
| only `AnthropicChatModel` and `AnthropicStreamingChatModel` were read | builder-options.md (sources line) | L2 |
| effort page read through a search summary / thinking page served under another path | thinking-and-effort.md | L3 |

## Version-lifetime risk

- langchain4j-anthropic 1.22.0 was released on GitHub 2026-10-08 and published to Maven Central 2026-10-07 (researched 2026-10-26), so docs may still change (High, https://github.com/langchain4j/langchain4j/releases/tag/1.22.0).
- No successor release and no end-of-support date for 1.22.0 were recorded at research time; plan upgrades by bumping the BOM and re-running tests (medium confidence, absence of evidence).
- Claude retirement is not sooner than 2027-09-22 (Opus 5.5), 2027-09-28 (Sonnet 5.5) and 2027-10-07 (Haiku 5.5); no date was recorded for Fable 5.1 (High, https://platform.claude.com/docs/en/about-claude/models/overview).
- Model IDs and effort availability are provider catalog data and change independently of LangChain4j; re-read the models overview before pinning an ID.
- The Anthropic docs page of LangChain4j is unversioned; content read on 2026-10-26 is assumed to match 1.22.0 (see L1).

## Unverified items

- U1. Whether a missing or blank `modelName` is rejected at request time (no build-time check exists in either constructor; the request-time path was not read).
- U2. Whether `InvalidRequestException`, and so `ContentFilteredException`, extends `NonRetriableException` (same open item as U7 in the core skill).
- U3. API ID strings of the legacy Claude models (Fable 5, Opus 5, Opus 4.8, 4.7, 4.6, 4.5, Sonnet 5, Sonnet 4.6, Haiku 4.5).
- U4. A hand-written `ChatModel` double or a local HTTP stub on `baseUrl` as an officially recommended test practice; no Anthropic-specific testing recipe was found.
- U5. Log output of the representative command `mvn -q dependency:tree -Dincludes=dev.langchain4j`.
- U6. Which effort levels each Claude 5.x model accepts.

## Irresolvable items

None.

## Medium-confidence items

- M1. The streaming model has no `maxRetries` and no retry call (source read at tag 1.22.0; the claim is kept at medium confidence for the whole family).
- M2. When `thinkingDisplay` is unset, recent models may return empty thinking (LangChain4j docs page, unversioned).
- M3. Prompt caching limits: at most 4 breakpoints per request and a model-specific minimum prompt of 512 to 4,096 tokens (docs page, unversioned).
- M4. Opus 4.7 rejects `midConversationSystemMessages` with a 400 error (search-result summary of the Anthropic page).
- M5. Effort levels `low`, `medium`, `high`, `xhigh`, `max` (effort page via search summary).
- M6. Placement rules for mid-conversation system messages (LangChain4j docs page, unversioned).
- M7. Builder option groups, per-request `AnthropicChatRequestParameters` and cache-count usage reporting (LangChain4j docs page, unversioned).
- M8. Reasoning text can carry prompt content and should be kept out of production logs (inference).
- M9. Beta header values change over time (docs page, unversioned).

## Coverage limits

- L1. `docs.langchain4j.dev` pages (get-started, Anthropic integration) are unversioned and track the current release; they were read on 2026-10-26 and assumed to match 1.22.0. Source files were read at tag 1.22.0.
- L2. Only `AnthropicChatModel`, `AnthropicStreamingChatModel`, the two module poms and the core exception and retry sources were read; the HTTP client and request-mapping classes of the module were not opened.
- L3. The Anthropic thinking and effort pages were reached through a path alias or a search summary; the quoted statements are taken from those results.

## Source Bibliography

All fetched 2026-10-26. No community sources were used.

- https://docs.langchain4j.dev/integrations/language-models/anthropic
- https://docs.langchain4j.dev/get-started
- https://github.com/langchain4j/langchain4j/releases/tag/1.22.0 (published 2026-10-08)
- https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicChatModel.java
- https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-anthropic/src/main/java/dev/langchain4j/model/anthropic/AnthropicStreamingChatModel.java
- https://github.com/langchain4j/langchain4j/blob/1.22.0/langchain4j-anthropic/pom.xml
- https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-http-client/src/main/java/dev/langchain4j/http/client/log/HttpRequestLogger.java
- https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/ExceptionMapper.java
- https://raw.githubusercontent.com/langchain4j/langchain4j/1.22.0/langchain4j-core/src/main/java/dev/langchain4j/internal/RetryUtils.java
- https://repo1.maven.org/maven2/dev/langchain4j/langchain4j-anthropic/ (1.22.0 at 2026-10-07)
- https://platform.claude.com/docs/en/about-claude/models/overview
- https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost
- https://platform.claude.com/docs/en/build-with-claude/effort (search summary only)
- https://platform.claude.com/docs/en/build-with-claude/mid-conversation-system-messages
