# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 85%, a run using all 5 iterations and 7 triangulated Always-Do inputs. Research ids are kept (U, C); research gaps G1 to G3 are listed here as I1 to I3 (I4 is added by this skill), and the research's internal sources I1 to I3 are renamed N1 to N3 in the [bibliography](./source-bibliography.md).

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Contradictions](#contradictions)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- The release status is stated in SKILL.md Version Context; the re-check trigger is the appearance of 1.15.0 final in the Maven Central metadata (High; https://repo1.maven.org/maven2/io/quarkiverse/langchain4j/quarkus-langchain4j-bedrock/maven-metadata.xml). The pre-release caveat is stated once, in [ask-first D1](./ask-first-decisions.md#d1-adopt-a-pre-release).
- The buffering claim (pattern 6, never-do N3, SKILL.md Always Do and Never Do on `Multi<String>`) is High: the research quotes the 3.40.1.1 handler source (`ByteArrayOutputStream`, completion on `LastHttpContent`) and 3.40.1.1 is the Quarkus patch this skill targets. The parent POM of 1.15.0.CR1 says Quarkus 3.40.0, so the pairing of the extension with patch 3.40.1.1 stays (medium confidence, M13); it does not lower the claim about the handler.
- Quarkus 3.40 LTS is community-maintained until 2027-09-30; Quarkus 4.0.0 is "Upcoming" with no date and its content is rejected (High; https://quarkus.io/releases).
- `quarkus-amazon-lambda-http` and `-rest` are preview, so backward compatibility is not guaranteed (High; https://quarkus.io/version/3.40/guides/aws-lambda-http).
- 1.14.2 was a security fix only (GHSA-8vpj-4r6j-h9qg, Redis filter mapper); 1.15.0.CR1 lists no breaking changes (High; https://github.com/quarkiverse/quarkus-langchain4j/releases/tag/1.15.0.CR1).

## Unverified items

11 unverified items (do not assert them). U6 is tagged (unverified) here although the research tagged the same native-image statement (medium confidence): both pieces of evidence are indirect, so the stricter tag stands.

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | Whether the BOM manages every `dev.langchain4j:*` artifact, and the effect of overriding to 1.22.0 | Import the BOM only; check `dependency:tree` |
| U2 | Config phase of `quarkus.langchain4j.<provider>.api-key` against the availability of the Secrets Manager config source | Use a `ModelAuthProvider` bean; integration test |
| U3 | Quarkus 3.40 support for the `InvokeWithResponseStream` output format | Return buffered `String` responses |
| U4 | IAM resource ARN forms for Bedrock inference profiles (`global.`, `us.`) | Read the Bedrock IAM docs when writing the Terraform |
| U5 | Runtime fallback of Bedrock `chat-model.model-id` (documentation default only) | Set `model-id` explicitly |
| U6 | A native-image support statement for the three providers in the quarkus-langchain4j docs | Native integration test before the ADR |
| U7 | SnapStart restore behaviour of the provider HTTP clients (Vert.x, SDK) and their init cost | Post-restore smoke test; ADR |
| U8 | Status code API Gateway returns on an integration timeout and whether Lambda keeps running | Keep budgets under the limit |
| U9 | Dev Services or HTTP-level mocking for Anthropic and Bedrock; SSE content encoding in `LambdaHttpHandler` | `@InjectMock` the AI service |
| U10 | Whether `log-requests` masks the `Authorization` and `x-api-key` headers | Never enable outside `%dev.` |
| U11 | AWS SDK version alignment between `langchain4j-bedrock` (LangChain4j 1.21.0) and Quarkiverse amazon-services 3.23.x | `dependency:tree`; one managed AWS SDK version |

## Irresolvable items

4 irresolvable items (documentation cannot settle them; they are absence-of-evidence claims and the skill text tags them (medium confidence, absence of evidence)).

| ID | Research id | Item | Reason and workaround |
|---|---|---|---|
| I1 | G1 | No Bedrock page at the tag | Three candidate paths returned 404 and the tag navigation lists none; the `dev` page plus tag code are used |
| I2 | G2 | Declaration and default of `openai.chat-model.mode` at the tag | Not in `ChatModelConfig.java`; set the mode explicitly when needed |
| I3 | G3 | Full diff 1.14.2 to 1.15.0.CR1 | GitHub timed out; defaults were spot-checked, silent changes are not excluded |
| I4 | none | 2.0.0.Beta1 is the Quarkus 4 line | Only the version metadata was read; its parent POM was not recorded, so the Quarkus 4 pairing is inferred from the version number; the skill rejects it either way |

## Medium-confidence items

20 medium-confidence items.

| ID | Item | Why medium |
|---|---|---|
| M1 | Timeout budget formula, example values and the fit of the Q2 options | Design choice; the limits and defaults are High |
| M2 | Bedrock chat and streaming models call `Converse` and `ConverseStream`, so the two IAM actions apply | S49 only mentions Converse and ConverseStream requests |
| M3 | Signature of a `@Fallback` default method on an AI service interface | Follows the guide's pattern; not compiled |
| M4 | The `quarkus-amazon-lambda-rest` handler buffers like the HTTP one | Only the HTTP handler source was read |
| M5 | Streaming builders apply no `maxRetries` | Tool summary of tag code; the non-streaming line is verbatim |
| M6 | In-JVM chat memory is neither shared across Lambda environments nor durable | Inference |
| M7 | Each tool round trip is another model call inside the same time budget | Inference |
| M8 | The values `anthropic` and `bedrock` for `chat-model.provider` | The tag example shows `openai` only |
| M9 | The Bedrock HTTP client factory is Vert.x-based, and no extra client artifact is needed | Inferred from the `Supplier<Vertx>` parameter and the excluded artifacts |
| M10 | Bedrock `enable-integration` defaults to `true` | `dev` table via a tool summary |
| M11 | An application-wide AI service scope shares one memory window across tenants | Inference from verbatim scope and memory quotes |
| M12 | An inference profile may route across Regions | Inference from the profile prefix |
| M13 | The CR parent POM says Quarkus 3.40.0; the pairing with patch 3.40.1.1 is not stated | Absent from the pages read |
| M14 | Whether a condition guards the `apiCallTimeout` recorder line (C3) | Surrounding code not read |
| M15 | The annotation name `@ConnectWireMock` | Guide shows `wiremock.verifyThat`; name from the quarkus-wiremock-test module |
| M16 | Illustrative code and commands in all files | Not compiled or run |
| M17 | The `dev` table default `gpt-6-luna` for the OpenAI model (C1) | Tool summary, no verbatim sentence |
| M18 | Secrets loaded at init sit in the SnapStart snapshot and rotation needs a new published version | Taken from internal sources N1 and N2, not re-read |
| M19 | One request per Lambda execution environment at a time | Family research statement; no AWS URL was recorded |
| M20 | The Secrets Manager config source is off by default and loaded once at startup; the Parameters and Secrets extension costs one HTTP hop per fetch | Taken from internal source N1 (sibling skill `integrating-quarkus-amazon-messaging-v3-40`), not re-read |

## Coverage limits

10 coverage limits (parts of pages not read, or read through summarisation).

| ID | Limit |
|---|---|
| L1 | S10 was read in part: characters 0 to 100000 of 119216 |
| L2 | S14 was read in part: characters 0 to 100000 of 103328 |
| L3 | S47 (the Quarkus testing guide) was partly read on 2026-10-28: characters 0 to 100000 of 108160; the `@InjectMock` scope sentence is a verbatim quote |
| L4 | S7, S8, S9, S11, S12, S13, S15, S16 and S17 were read as tool summaries with verbatim quotes; page length not measured; only quoted text is used as High |
| L5 | S33, S34 and S35 were read as tool summaries with verbatim quotes; the config include of S34 was not resolved |
| L6 | S6 gave navigation only; docs.quarkiverse.io lists no version other than `dev` |
| L7 | S48 was read for one sentence, S49 shows a `langchain4j-bedrock` 1.23.0 snippet, S50 is a directory listing that may be incomplete |
| L8 | S20, S23 and S31 were read through verbatim lines plus a tool summary; the verbatim lines carry the High claims |
| L9 | S1 and S46 were read through tool extraction; the values quoted are verbatim |
| L10 | N1, N2 and N3 were not re-fetched; facts from them carry (medium confidence, M18 or M20) where used |

## Contradictions

5 contradictions (research C1 to C5; values and handling in [config and contradictions](./config-defaults-and-contradictions.md#contradictions)); no family fact was contradicted by a page read.

| ID | Topic | Handling |
|---|---|---|
| C1 | OpenAI default model: tag `gpt-4o-mini` against `dev` `gpt-6-luna` | The tag wins; set explicitly |
| C2 | Anthropic default model: code `claude-3-haiku-20240307` against docs "latest available" | Code is the runtime truth; set explicitly |
| C3 | Bedrock `aws.api-call-timeout`: doc `13s` against recorder 10 s (medium confidence, M14) | Cite both; set explicitly |
| C4 | OpenAI API mode: tag Chat Completions against `dev` automatic selection | The tag wins; expect a change at the final |
| C5 | API key placement: extension docs suggest an environment variable, AWS says Secrets Manager | AWS and family rule 5 win on Lambda |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified, U1) BOM coverage and version override | always-do 1; ask-first D9 | U1 |
| (unverified, U2) key config-source timing | SKILL.md Ask First D3; ask-first D3 | U2 |
| (unverified, U3) response-streaming output format | SKILL.md Ask First D10; ask-first D10 | U3 |
| (unverified, U4) inference-profile ARNs | SKILL.md Ask First D5; ask-first D5 | U4 |
| (unverified, U5) Bedrock model-id fallback | always-do 4; ask-first D5; config Bedrock keys | U5 |
| (unverified, U6) native support of the providers | SKILL.md Ask First D6; ask-first D6 | U6 |
| (unverified, U7) HTTP clients after a restore | SKILL.md Ask First D6; ask-first D6; verification Production readiness | U7 |
| (unverified, U8) gateway timeout status | never-do N4 | U8 |
| (unverified, U9) HTTP-level mocks and SSE encoding | always-do 8; never-do N3; verification Mocking | U9 |
| (unverified, U10) log header masking | never-do N5 | U10 |
| (unverified, U11) AWS SDK alignment | ask-first D9 | U11 |
| (medium confidence, absence of evidence, I1) no Bedrock page at the tag | config Bedrock keys | I1 |
| (medium confidence, absence of evidence, I2) `mode` declaration not located | SKILL.md Ask First D7; ask-first D7; config OpenAI keys | I2 |
| (medium confidence, absence of evidence, I3) full diff not rendered | ask-first D1; config Contradictions | I3 |
| (medium confidence, M1) budget formula and values | SKILL.md Ask First D4; always-do 4, 5; never-do N4; ask-first D4 | M1 |
| (medium confidence, M2) Converse mapping of the IAM actions | SKILL.md Ask First D5; ask-first D5 | M2 |
| (medium confidence, M3) `@Fallback` signature | always-do 5; ask-first D4 | M3 |
| (medium confidence, M4) REST extension buffering | SKILL.md Ask First D10; ask-first D10; never-do N3 scope | M4 |
| (medium confidence, M5) streaming without `maxRetries` | never-do N3; config Anthropic keys | M5 |
| (medium confidence, M6) in-JVM memory not durable | SKILL.md Ask First D8; ask-first D8 | M6 |
| (medium confidence, M7) tool round trips in the budget | ask-first D10 | M7 |
| (medium confidence, M8) provider names in `chat-model.provider` | SKILL.md Ask First D2; ask-first D2 | M8 |
| (medium confidence, absence of evidence, I4) 2.0.0.Beta1 is the Quarkus 4 line | SKILL.md Version-lifetime risk | I4 |
| (medium confidence, M9) Vert.x-based Bedrock client, no extra client artifact | always-do 1 | M9 |
| (medium confidence, M10) Bedrock `enable-integration` | config Bedrock keys | M10 |
| (medium confidence, M11) application scope leaks memory | SKILL.md Ask First D8; ask-first D8 | M11 |
| (medium confidence, M12) profile routing across Regions | ask-first D5 | M12 |
| (medium confidence, M13) pairing with patch 3.40.1.1 | SKILL.md Version Context (Platform pairing); SKILL.md Always Do and Never Do on `Multi<String>` (High handler source; the pairing is noted in the register Version-lifetime risk only); register Version-lifetime risk | M13 |
| (medium confidence, M14) guard of the recorder line | SKILL.md Quick Reference; always-do 4; config Bedrock keys and Contradictions C3; register C3 | M14 |
| (medium confidence, M15) `@ConnectWireMock` name | verification Mocking | M15 |
| (medium confidence, M16) code not compiled | headers of all blueprints | M16 |
| (medium confidence, M17) `gpt-6-luna` tool summary | config Contradictions C1 | M17 |
| (medium confidence, M18) secrets in the snapshot, rotation | ask-first D3, D6 | M18 |
| (medium confidence, M19) one request per Lambda environment | verification Production readiness (Scalability) | M19 |
| (medium confidence, M20) config-source claims from N1 | ask-first D3 | M20 |

## Source Bibliography

The full table is in [source-bibliography.md](./source-bibliography.md).
