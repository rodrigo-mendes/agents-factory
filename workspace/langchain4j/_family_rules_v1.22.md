# Family rules — langchain4j 1.22.0

1. Evidence rule: a claim in Always Do / Never Do needs a versioned official source read in full.
2. Tags are plain parentheses: `(medium confidence)`, `(unverified)`; never bold or brackets.
3. One claim per Always Do bullet; Never Do alternatives are High confidence too.
4. Scope is chat + streaming in plain Java only (ChatModel / StreamingChatModel). AiServices, @Tool, memory, RAG, structured output, Spring/Quarkus are out of scope: say so and route nothing. — decided at intake, reason: user choice "Chat + streaming".
5. Always import `langchain4j-bom:1.22.0` and declare provider modules without a version (F2, F3).
6. Never hardcode API keys; read them from environment variables / secret store. Never enable `logRequests`/`logResponses` in production (F8: body logged unmasked).
7. Model IDs are passed as strings from current official provider catalogs, not the OpenAI model-name enum (outdated, stops at GPT_5_1). — decided after research, reason: enum lists shut-down models.
8. Anthropic on Claude 5.x: use `thinkingType("adaptive")`; manual `thinkingType("enabled")` + `thinkingBudgetTokens` is a Never Do for 5.x. Effort via `customParameters(Map.of("output_config", Map.of("effort", ...)))`.
9. OpenAI reasoning models: omit `temperature`/`top_p` when reasoning effort is not `none`; limit output with `maxCompletionTokens`, not `maxTokens`.
10. `langchain4j-open-ai-official` (1.22.0-beta32) is Ask-First only: never chosen by default. — decided by user: "Opção Ask-First".
11. Async/reactive APIs marked @Experimental are Ask-First.
12. Testing: provide a hand-written ChatModel test double overriding `doChat`, tagged (unverified) per F10.
13. Do not cite workspace ids (F#, rule #) inside skills; cite URLs. — pilot round 1.
14. Cite stable module docs pages, never the beta open-ai-official page, for stable-module claims. — pilot round 2.
15. Error-handling samples end with a `catch (LangChain4jException e)` fallback; InvalidRequestException/ContentFilteredException retry class is (unverified). — pilot round 2.
16. Provider skills own model construction (builders); core takes ChatModel/StreamingChatModel as given and points to the provider sibling. — pilot round 3.
17. Evaluation scenarios: every must_pass is triggerable by the query and judged on substance, not tag text. — pilot round 2.
18. Skill/agent `name` must not contain reserved words `anthropic` or `claude`; provider names appear only in description/body. — fan-out, user chose "integrating-langchain4j-provider-a-v1-22".
