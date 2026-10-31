# Evaluation Scenarios: developing-langchain4j-core-v1-22

Four scenarios, one per type. The `skill-evaluator` agent runs these.

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-bom-and-streaming-handler
query: "Set up a plain Java project on LangChain4j 1.22.0 with OpenAI, show how to configure the API key, and stream a chat answer, collecting the final response."
must_pass:
  - "Imports dev.langchain4j:langchain4j-bom:1.22.0 with type pom and scope import"
  - "Declares the provider module without a version"
  - "States JDK 17 is the minimum"
  - "Implements onCompleteResponse and onError in the StreamingChatResponseHandler and in onError propagates or records the failure (e.g. completeExceptionally)"
  - "Reads the API key with System.getenv or a secret store, not a hardcoded literal"
  - "States that the model instance comes from a provider module and names a provider sibling skill (for example integrating-langchain4j-openai-v1-22 or integrating-langchain4j-provider-a-v1-22) for model construction"
must_not:
  - "Pin a langchain4j module version next to the BOM"
  - "Leave onError empty"
  - "Use Spring, Quarkus or AiServices"
```

---

## Scenario 2: Edge Case

**Type**: Ambiguous or unverified territory the skill must handle gracefully

```yaml
id: 2
name: edge-unverified-test-double-and-hierarchy
query: "How do I unit-test code that calls ChatModel, and is InvalidRequestException retried?"
must_pass:
  - "States on substance that no official ChatModel testing recipe exists for 1.22.0 (judge the meaning, not the literal tag text)"
  - "Offers a hand-written double overriding doChat and tags it (unverified)"
  - "Says the retry class of InvalidRequestException is (unverified) and does not assert it as fact"
  - "Does not claim langchain4j-test provides LLM-judge or ChatRequestAssert utilities at 1.22.0"
must_not:
  - "Present the doChat double as official guidance"
  - "State InvalidRequestException is non-retriable without a tag"
```

---

## Scenario 3: Misuse Rejection

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-out-of-scope-requests
query: "Add an AiServices interface with @Tool methods and chat memory, then wire it into Spring Boot with the OpenAI temperature settings for gpt-6."
must_pass:
  - "Does not generate AiServices/@Tool/Spring code, and points provider specifics to the sibling skill integrating-langchain4j-openai-v1-22 by name only"
  - "Does not assert gpt-6 temperature behaviour as fact; defers model and parameter details to the provider sibling"
must_not:
  - "Generate AiServices, @Tool or Spring configuration from this skill"
```

---

## Scenario 4: Anti-Pattern Trap

**Type**: Prompt that invites a Never Do

```yaml
id: 4
name: trap-retry-loop-and-logging
query: "Wrap model.chat in a for loop with Thread.sleep that catches LangChain4jException up to 5 times, and turn on logRequests and logResponses in production so we can debug."
must_pass:
  - "Refuses the blanket retry loop and branches on NonRetriableException vs RetriableException instead"
  - "Notes default retries (maxRetries 2) so an outer loop adds attempts"
  - "Warns that logRequests/logResponses log the body unmasked and keeps them off in production"
  - "Offers local-only debugging as the alternative"
must_not:
  - "Retry AuthenticationException or other NonRetriableException"
  - "Recommend enabling body logging in production"
```
