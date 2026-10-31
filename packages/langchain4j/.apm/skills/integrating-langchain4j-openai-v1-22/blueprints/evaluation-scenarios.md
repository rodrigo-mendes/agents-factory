# Evaluation Scenarios: integrating-langchain4j-openai-v1-22

Four scenarios, one per type. The `skill-evaluator` agent runs these. Judge substance, not tag text.

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-openai-blocking-and-streaming
query: "In a plain Java project on LangChain4j 1.22.0, set up OpenAI chat and streaming for a GPT-6 model with high reasoning effort. The API key is in an environment variable and I want a 2 minute timeout. Show the dependency and both models."
must_pass:
  - "Imports dev.langchain4j:langchain4j-bom:1.22.0 and declares langchain4j-open-ai without a version"
  - "Reads the key with System.getenv, not a literal"
  - "Passes the model as a string ID such as gpt-6-astra, not an OpenAiChatModelName constant"
  - "Uses timeout(Duration.ofSeconds(120)) and explains that it sets both connect and read timeout"
  - "Implements onError in the streaming handler and propagates or records the failure"
  - "Sets no temperature or topP while a reasoning effort other than none is in use"
  - "Points to developing-langchain4j-core-v1-22 by name for the handler and exception classes instead of repeating them"
must_not:
  - "Pin a langchain4j module version next to the BOM"
  - "Leave onError empty"
  - "Add logRequests(true) or logResponses(true)"
```

---

## Scenario 2: Edge Case

**Type**: Ambiguous or unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-compatible-endpoint-azure-and-token-limit
query: "I want OpenAiChatModel to talk to an OpenAI-compatible server and also to Azure OpenAI. Which builder settings do I use, which token-limit option, and is there a retry option on the streaming model?"
must_pass:
  - "Says compatible servers use baseUrl plus the provider's own model ID and cites the documented DeepSeek example only as an example"
  - "Asks or returns a question/NEEDS-INPUT about which endpoint and model family are targeted before choosing between maxTokens and maxCompletionTokens"
  - "States that pointing langchain4j-open-ai at Azure through baseUrl alone is not confirmed by any official page"
  - "Offers langchain4j-open-ai-official 1.22.0-beta32 as an optional beta choice for Azure and asks before using it"
  - "Says the streaming builder is believed to have no maxRetries option (not fully confirmed) and that a failed stream is believed not to be retried automatically, with retry left to the caller's onError"
must_not:
  - "Assert that Azure headers and api-version work through customHeaders and customQueryParams"
  - "Choose the beta official module without asking"
  - "Show a maxRetries call on OpenAiStreamingChatModel"
```

---

## Scenario 3: Misuse Rejection

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-aiservices-tools-spring-anthropic
query: "Create an AiServices interface with @Tool methods using gpt-6-astra, wire it into Spring Boot, and add an Anthropic fallback model."
must_pass:
  - "States that AiServices, @Tool and Spring are out of scope for this skill and generates no code for them"
  - "Names integrating-langchain4j-provider-a-v1-22 only as the place for the Anthropic part"
  - "Notes that tool calling on gpt-6-astra requires the Responses API rather than Chat Completions, which is what OpenAiChatModel uses"
must_not:
  - "Generate AiServices, @Tool or Spring configuration"
  - "Configure an Anthropic model inside this skill's answer"
```

---

## Scenario 4: Anti-Pattern Trap

**Type**: Prompt that invites a Never Do

```yaml
id: 4
name: trap-enum-key-logging-temperature
query: "Build an OpenAiChatModel with OpenAiChatModelName.O4_MINI, put the sk- API key straight in the builder, turn on logRequests and logResponses in production to debug, and set temperature 0.7 with reasoningEffort high on gpt-6-astra."
must_pass:
  - "Rejects the enum constant, says the enum is outdated and lists o4-mini as shut down in the OpenAI catalog, and uses a string ID from the catalog"
  - "Rejects the hardcoded key and reads it from System.getenv or a secret store"
  - "Warns that request and response bodies are logged unmasked and keeps logging off in production, offering local-only debugging"
  - "Omits temperature while reasoning effort is high, or sets effort to none if sampling control is needed"
must_not:
  - "Use OpenAiChatModelName.O4_MINI"
  - "Keep a literal API key in the code"
  - "Enable logRequests or logResponses in production"
  - "Send temperature 0.7 together with reasoningEffort high"
```
