# quarkus-langchain4j

LangChain4j on Quarkus 3.40 Lambda through `quarkus-langchain4j` **1.15.0.CR1** (a pre-release), with
its dedicated reviewer.

## Package Contents

```
packages/quarkus-langchain4j/
├── apm.yml                                            <- deps: factory-core, quarkus-aws
└── .apm/
    ├── skills/integrating-quarkus-langchain4j-v1-15/  <- version-locked knowledge skill (+ blueprints/)
    └── agents/langchain4j-reviewer.agent.md           <- tools: Read, Grep, Glob; model: sonnet
```

| Asset | Does |
|---|---|
| skill `integrating-quarkus-langchain4j-v1-15` | OpenAI, Anthropic and Bedrock through `@RegisterAiService`: BOM pin, explicit model and timeouts, `@Timeout` below the gateway limit, keys in Secrets Manager/SSM, no streaming behind the gateway, `@InjectMock` tests. Ask First D1 (pre-release) must be settled before use |
| agent `langchain4j-reviewer` | Read-only review of AI code against the skill's Always-Do and Never-Do (N1-N6) and the ADRs; `review-NN` with `role: ai`, returned inline. Runs before `quarkus-code-reviewer` |

The skill moved here from `aws-saas-serverless-quarkus-react-nextjs` (name unchanged, so references
by name still resolve). Out of scope: chat or streaming to the browser, RAG, vector stores, MCP and
plain LangChain4j 1.22 (see `packages/langchain4j`).

Depends on: factory-core, quarkus-aws.
