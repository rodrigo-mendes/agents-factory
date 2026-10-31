# Evaluation Scenarios: integrating-quarkus-langchain4j-v1-15

Six scenarios, covering the four required types. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (pre-release and conflicting defaults)](#scenario-2-edge-case-pre-release-and-conflicting-defaults)
- [Scenario 3: Misuse Rejection (RAG, Quarkus 4, plain Java)](#scenario-3-misuse-rejection-rag-quarkus-4-plain-java)
- [Scenario 4: Anti-Pattern Trap (streaming and a long timeout behind API Gateway)](#scenario-4-anti-pattern-trap-streaming-and-a-long-timeout-behind-api-gateway)
- [Scenario 5: Anti-Pattern Trap (API key in application.properties)](#scenario-5-anti-pattern-trap-api-key-in-applicationproperties)
- [Scenario 6: Anti-Pattern Trap (real provider in tests)](#scenario-6-anti-pattern-trap-real-provider-in-tests)

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-bedrock-ai-service-on-rest-api
skills: ["integrating-quarkus-langchain4j-v1-15"]
query: "Add an AI service that answers support questions with Amazon Bedrock to my Quarkus 3.40 Lambda behind an API Gateway REST API."
must_pass:
  - "Imports quarkus-langchain4j-bom 1.15.0.CR1 and adds quarkus-langchain4j-bedrock plus quarkus-smallrye-fault-tolerance, without explicit dev.langchain4j versions (BOM coverage of every artifact is unverified, U1)"
  - "Configures no credentials and no region for Bedrock because the Lambda execution role and the SDK default chain apply, and sets the model id explicitly"
  - "Puts @Timeout below 29 s on the AI service method and sets explicit provider timeouts, noting that the timeout values are a design choice (medium confidence, M1)"
  - "Returns String from the resource method instead of Multi, because the HTTP handler buffers the response; for the REST extension this is (medium confidence, M4)"
  - "Leaves the AI service at its default RequestScoped scope and leaves log-requests and tracing include-prompt off"
  - "Asks before choosing the Bedrock model id or inference profile and names the two IAM actions without inventing resource ARNs (unverified, U4)"
must_not:
  - "Writes static AWS credentials or an access key for Bedrock"
  - "Writes SAM or CDK templates instead of deferring IaC to provisioning-aws-*-v6"
  - "Sets @Timeout to 60 s"
```

---

## Scenario 2: Edge Case (pre-release and conflicting defaults)

**Type**: Conflicting sources

```yaml
id: 2
name: edge-prerelease-and-default-model
skills: ["integrating-quarkus-langchain4j-v1-15"]
query: "Is quarkus-langchain4j 1.15.0 final out, and which default model does the Anthropic extension use so I can skip configuring it?"
must_pass:
  - "States that 1.15.0.CR1 is a pre-release, that no 1.15.0 final exists on Maven Central as of 2026-10-28, and that adoption is an Ask First item (D1) with a re-check trigger when the final ships"
  - "States that 1.14.2 is built on Quarkus 3.33.3.1 and 2.0.0.Beta1 is the Quarkus 4 line (medium confidence, I4), so neither fits Quarkus 3.40"
  - "Cites both statements for the Anthropic model: code default claude-3-haiku-20240307 and the tag docs sentence 'latest available Claude model' (C2), and advises setting the model explicitly"
  - "Mentions that the dev docs run ahead of the tag and that the tag wins"
must_not:
  - "Claims a 1.15.0 final exists or recommends 1.14.2 on Quarkus 3.40"
  - "Picks one default model silently without citing the other source"
```

---

## Scenario 3: Misuse Rejection (RAG, Quarkus 4, plain Java)

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-rag-quarkus4-plain-java
skills: ["integrating-quarkus-langchain4j-v1-15"]
query: "Add RAG with a vector store and an MCP tool server to my Quarkus 4 app, and also show me a plain-Java LangChain4j chat call without Quarkus."
must_pass:
  - "Says RAG, vector and embedding stores and MCP are out of scope for this skill and does not write them"
  - "Says Quarkus 4 content is rejected because the skill is locked to Quarkus 3.40 and that 2.0.0.Beta1 is the Quarkus 4 line (medium confidence, I4)"
  - "Points the plain-Java request to developing-langchain4j-core-v1-22 by name and does not restate it"
  - "Offers only what is in scope: AI services with OpenAI, Anthropic or Bedrock on Quarkus 3.40 Lambda"
must_not:
  - "Writes RAG, embedding store or MCP configuration"
  - "Uses Quarkus 4 or 2.0.0.Beta1 coordinates"
```

---

## Scenario 4: Anti-Pattern Trap (streaming and a long timeout behind API Gateway)

**Type**: Tempting shortcut

```yaml
id: 4
name: trap-streaming-and-60s-timeout-behind-gateway
skills: ["integrating-quarkus-langchain4j-v1-15"]
query: "Stream the model answer token by token to the browser with Multi<String> over SSE through API Gateway, and use the guide's @Timeout of 60 seconds."
must_pass:
  - "Rejects incremental delivery: the 3.40.1.1 HTTP handler buffers until LastHttpContent, an HTTP API has no response streaming and Lambda streams natively only on Node.js managed runtimes"
  - "Proposes a blocking String or POJO return bounded by @Timeout"
  - "Rejects 60 s because the guide's value is an example and the gateway limit is 29 s for a REST API and 30 s for an HTTP API"
  - "Tags the REST-extension buffering as (medium confidence, M4) and the response-streaming output format as (unverified, U3), and treats streaming on a REST API as an Ask First item (D10)"
must_not:
  - "Writes a Multi<String> or SERVER_SENT_EVENTS endpoint behind API Gateway"
  - "Keeps a @Timeout or provider timeout above the gateway limit"
```

---

## Scenario 5: Anti-Pattern Trap (API key in application.properties)

**Type**: Tempting shortcut

```yaml
id: 5
name: trap-openai-key-in-properties
skills: ["integrating-quarkus-langchain4j-v1-15"]
query: "Put quarkus.langchain4j.openai.api-key=sk-live-... in application.properties, or in a Lambda environment variable, so it just works."
must_pass:
  - "Rejects both placements: AWS recommends Secrets Manager instead of environment variables for API keys and the extension says never to embed keys in source code (family rule 5)"
  - "Offers the delivery mechanism as an Ask First item (D3): Secrets Manager config source or a ModelAuthProvider bean, tagging the config-source timing as (unverified, U2)"
  - "Notes that Bedrock needs no API key because it uses the Lambda role"
must_not:
  - "Writes a literal key or an api-key line in application.properties"
  - "States as fact that the Secrets Manager config source resolves quarkus.langchain4j keys in time"
```

---

## Scenario 6: Anti-Pattern Trap (real provider in tests)

**Type**: Tempting shortcut

```yaml
id: 6
name: trap-real-provider-in-tests
skills: ["integrating-quarkus-langchain4j-v1-15"]
query: "Write the integration test so it calls the real OpenAI endpoint with the key from the CI environment."
must_pass:
  - "Rejects real provider calls in tests and offers @InjectMock on the AI service or WireMock with the provider base-url overridden"
  - "Uses a placeholder key such as test-key under the %test profile"
  - "Says WireMock guide coverage is OpenAI Chat Completions only and that HTTP-level mocking of Anthropic and Bedrock is not documented (unverified, U9), so the AI service is mocked there"
must_not:
  - "Reads OPENAI_API_KEY into a test profile property"
  - "Uses quarkus-test-amazon-lambda, which was removed in Quarkus 3.31"
```
