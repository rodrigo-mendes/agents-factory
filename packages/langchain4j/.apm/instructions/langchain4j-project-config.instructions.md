---
name: langchain4j-project-config
description: "LangChain4j 1.22.0 Maven configuration: langchain4j-bom import, provider modules without version, JDK 17 minimum, no beta open-ai-official by default. Use when editing pom.xml of a project that uses LangChain4j."
applyTo: "**/pom.xml"
---

# LangChain4j project configuration (1.22.0)

Targets LangChain4j 1.22.0 (chat and streaming, plain Java). Exact coordinates, versions and
builder options are in the skills; refer there instead of restating them. Tags `(unverified)` /
`(medium confidence)` in a skill apply here too.

Activation: `pom.xml` matches in any Maven project. Apply this rule **only when the POM declares
or should declare a `dev.langchain4j` dependency**; otherwise ignore it.

## Skills

- `developing-langchain4j-core-v1-22`: core dependencies, JDK baseline, version context.
- `integrating-langchain4j-openai-v1-22`: `langchain4j-open-ai` module.
- `integrating-langchain4j-provider-a-v1-22`: `langchain4j-anthropic` module.

## Always

- Import `dev.langchain4j:langchain4j-bom:1.22.0` in `dependencyManagement` (type `pom`, scope
  `import`) (`developing-langchain4j-core-v1-22`).
- Declare provider modules (`langchain4j-open-ai`, `langchain4j-anthropic`) without a `<version>`;
  the BOM manages them.
- Set the compiler release to JDK 17 or higher: 17 is the minimum supported JDK.
- Verify with `./mvnw clean compile` and `test` (or `mvn` when there is no wrapper).

## Ask First

- `langchain4j-open-ai-official` (beta, `1.22.0-beta32`): add it only when the user asks for it
  (`integrating-langchain4j-openai-v1-22`).
- Modules outside chat and streaming (AiServices, RAG, memory, Spring/Quarkus starters): out of
  scope of these skills; say so and do not configure them from memory.
- New dependencies beyond the requirement.

## Never

- Put a `<version>` on a provider module while the BOM is imported.
- Mix a different LangChain4j version with the 1.22.0 BOM.
- Target a JDK below 17.
- Choose `langchain4j-open-ai-official` by default.
- Put API keys in the POM or in committed properties: use environment variables or a secret store.
