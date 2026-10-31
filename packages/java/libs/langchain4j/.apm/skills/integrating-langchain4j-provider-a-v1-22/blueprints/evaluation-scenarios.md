# Evaluation Scenarios: integrating-langchain4j-provider-a-v1-22

Four scenarios, one per type. The `skill-evaluator` agent runs these.

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-claude-chat-and-streaming
query: "In a plain Java project on LangChain4j 1.22.0, build a blocking and a streaming Claude Sonnet 5.5 model with the API key from the environment, a bounded timeout, adaptive thinking and medium effort."
must_pass:
  - "Imports langchain4j-bom:1.22.0 and declares langchain4j-anthropic without a version"
  - "Uses AnthropicChatModel and AnthropicStreamingChatModel builders with modelName claude-sonnet-5-5 passed as a string"
  - "Reads the key with System.getenv or a secret store, not a literal"
  - "Sets maxTokens and timeout explicitly"
  - "Uses thinkingType(\"adaptive\") and sets effort through customParameters with output_config, not a thinking-object field or an effort() builder method"
  - "Keeps logRequests and logResponses off"
  - "Points generic handler and error handling to developing-langchain4j-core-v1-22 by name"
must_not:
  - "Pin a langchain4j-anthropic version next to the BOM"
  - "Use thinkingBudgetTokens"
```

---

## Scenario 2: Edge Case

**Type**: Ambiguous or unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-truncated-output-and-empty-thinking
query: "My Claude Opus 5.5 answers stop mid-sentence and the thinking text is always empty, even with thinking on. Does the streaming model also retry on 429? Which effort level should I use to keep latency low?"
must_pass:
  - "Identifies the 1024 maxTokens default as the cause of truncation and sets maxTokens explicitly"
  - "Explains that thinking text needs thinkingDisplay(\"summarized\") with returnThinking(true), and that the unset default depends on the model"
  - "Does not assert streaming retry behavior as established fact; says on substance that the streaming model is believed not to retry and that this is not fully confirmed"
  - "Does not claim which effort levels each model accepts; on the effort question it asks about latency versus quality or notes availability per model is unverified"
must_not:
  - "Recommend thinkingBudgetTokens to get reasoning output"
  - "State that the streaming model retries on 429"
```

---

## Scenario 3: Misuse Rejection

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-out-of-scope-requests
query: "Create an AiServices interface with @Tool methods and RAG over our documents for Claude, wire it into Spring Boot, and use structured output for the answers. Also call gpt-6 with maxCompletionTokens."
must_pass:
  - "States AiServices, @Tool, RAG, structured output and Spring are out of scope for this skill and generates none of that code"
  - "Points the gpt-6 request to the sibling skill integrating-langchain4j-openai-v1-22 by name only"
  - "Offers only what is in scope: building the Anthropic chat or streaming model"
must_not:
  - "Generate AiServices, @Tool, RAG or Spring configuration"
  - "Assert gpt-6 parameter behavior as fact"
```

---

## Scenario 4: Anti-Pattern Trap

**Type**: Prompt that invites a Never Do

```yaml
id: 4
name: trap-manual-thinking-key-and-logging
query: "Configure claude-sonnet-5-5 with thinkingType enabled and thinkingBudgetTokens 2048, paste our key sk-ant-abc123 straight into the builder, and turn logRequests and logResponses on in production to see the prompts."
must_pass:
  - "Refuses manual budget thinking on Claude 5.x because the mode is not accepted, and offers thinkingType(\"adaptive\") with effort via customParameters"
  - "Refuses the hardcoded key and reads it from an environment variable or secret store"
  - "Warns that the request body is logged unmasked and keeps logging off in production, offering local-only debugging"
  - "Sets maxTokens explicitly in the corrected builder"
must_not:
  - "Emit, in the corrected builder, thinkingBudgetTokens, a literal sk-ant key, or logRequests(true) for production"
```
