# langchain4j

APM package for **LangChain4j 1.22.0** (GitHub release 2026-10-08, Maven Central 2026-10-07,
latest stable at research date 2026-10-26): chat and streaming in plain Java with OpenAI and
Anthropic.

## Contents

| Kind | Name | Role |
|---|---|---|
| Skill | `developing-langchain4j-core-v1-22` | `ChatModel`/`StreamingChatModel` API, streaming and listeners, errors and retry, testing |
| Skill | `integrating-langchain4j-openai-v1-22` | OpenAI builders, GPT-6 and reasoning parameters |
| Skill | `integrating-langchain4j-provider-a-v1-22` | Anthropic builders, thinking and effort, caching and system messages |
| Agent | `langchain4j-integrator` | Non-interactive executor for a closed LangChain4j chat/streaming requirement |
| Rule | `langchain4j-code-standards` | Java sources that import `dev.langchain4j` |
| Rule | `langchain4j-project-config` | `pom.xml`: BOM import, versionless provider modules, JDK 17 |

## Scope

In scope: `ChatModel` and `StreamingChatModel` in plain Java, with the `langchain4j-open-ai` and
`langchain4j-anthropic` modules (both stable 1.22.0).

Out of scope (the skills say so and route nothing): AiServices, `@Tool`, chat memory, RAG,
structured output, Spring and Quarkus integration, other providers, and the beta
`langchain4j-open-ai-official` module (Ask-First only, never the default).

## Why `provider-a`

The Anthropic skill is named `integrating-langchain4j-provider-a-v1-22` because skill and agent
names must not contain the reserved words `anthropic` or `claude`. The provider name appears only
in its description and body.

## How to use

- Skills are knowledge skills: they auto-invoke when a request matches their description.
- The agent `langchain4j-integrator` has no `/command`; it is spawned through the Agent tool by the
  caller with a closed requirement.
- The two rules are path-scoped. The code rule uses `**/src/main/java/**` and `**/src/test/java/**`
  globs and applies only when the file imports `dev.langchain4j`; the config rule matches
  `**/pom.xml` and applies only to projects using LangChain4j.
- After editing the package sources, regenerate with `apm install --target claude` and commit
  both the sources and the regenerated `.claude/`.

## Provenance

- Research: `workspace/langchain4j/research_*_v1.22.0.md` and the gaps file
  `research_LangChain4j_gaps_v1.22.0.md`.
- Family facts: `workspace/langchain4j/_family_facts_v1.22.md` (F1-F10, dated 2026-10-26).
- Family rules: `workspace/langchain4j/_family_rules_v1.22.md` (18 rules).
- Approval: package, scoped rules and README approved 2026-10-26; recorded in
  `workspace/langchain4j/PIPELINE_STATE.md#approvals`.

## Known unverified items (summary)

Each skill carries a register in `blueprints/unverified-and-risks.md`; tags `(unverified)` and
`(medium confidence)` are preserved in skill bodies and rules.

- Core: retry class of `InvalidRequestException` and `ContentFilteredException`; streaming test
  doubles; the hand-written `ChatModel` double (no official 1.22.0 testing recipe; LLM-judge test
  utilities landed after 1.22.0); streaming retry (`AnthropicStreamingChatModel` does not retry,
  OpenAI streaming has no `maxRetries`, medium confidence).
- OpenAI: effort values and default effort, `max_tokens` rejection on GPT-6, other `gpt-6.*`
  variants, Azure and OpenAI-compatible endpoints beyond DeepSeek, `streamingBufferSize` default,
  thread-sharing of one model instance.
- Anthropic: request-time validation, which effort levels each model accepts, API ID strings of
  some models, log output of request details.
