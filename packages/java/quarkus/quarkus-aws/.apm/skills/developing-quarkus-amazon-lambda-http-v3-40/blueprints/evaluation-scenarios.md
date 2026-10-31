# Evaluation Scenarios: developing-quarkus-amazon-lambda-http-v3-40

Six scenarios, covering the four required types. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (REST response encoding conflict)](#scenario-2-edge-case-rest-response-encoding-conflict)
- [Scenario 3: Misuse Rejection (out-of-scope request)](#scenario-3-misuse-rejection-out-of-scope-request)
- [Scenario 4: Anti-Pattern Trap (REST native runtime)](#scenario-4-anti-pattern-trap-rest-native-runtime)
- [Scenario 5: Anti-Pattern Trap (wrong event type, two frameworks, security default)](#scenario-5-anti-pattern-trap-wrong-event-type-two-frameworks-security-default)
- [Scenario 6: Edge Case (undocumented front ends and timeout)](#scenario-6-edge-case-undocumented-front-ends-and-timeout)

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-http-api-quarkus-rest-lambda
skills: ["developing-quarkus-amazon-lambda-http-v3-40"]
query: "Expose a Quarkus 3.40 JAX-RS resource as a Lambda behind API Gateway and tell me what to hand to Terraform."
must_pass:
  - "Asks whether to use an HTTP API or a REST API (listing API keys, WAF, private endpoints, caching, request validation as REST-only reasons) before choosing quarkus-amazon-lambda-http or quarkus-amazon-lambda-rest"
  - "States both extensions are preview in the 3.40 guide and pins Quarkus 3.40.1.1"
  - "Keeps exactly one HTTP framework (proposes Quarkus REST) and offers an explicit Content-Type on responses as an Ask First practice tagged (medium confidence), not as an Always Do"
  - "Hands handler, runtime, CodeUri function.zip and (REST API) BinaryMediaTypes */* to provisioning-aws-lambda-v6 and provisioning-aws-api-gateway-v6, with no SAM or CDK"
  - "Refers to developing-quarkus-amazon-lambda-v3-40 for packaging and the JVM, SnapStart or native decision"
must_not:
  - "Picks HTTP API or REST API without asking"
  - "Writes SAM or CDK as the deployment path"
  - "Repeats the JVM vs native vs SnapStart analysis"
```

---

## Scenario 2: Edge Case (REST response encoding conflict)

**Type**: Conflicting sources

```yaml
id: 2
name: edge-rest-base64-guide-vs-source
skills: ["developing-quarkus-amazon-lambda-http-v3-40"]
query: "Does the REST extension Base64-encode every response? My JSON clients receive odd bodies on the REST API."
must_pass:
  - "Cites both: the guide says the extension forces binary (Base64) encoding of all response messages; the 3.40.1.1 REST handler Base64-encodes only non-text content types"
  - "Tags the conflict (unverified) and does not pick one; says the client-visible effect with BinaryMediaTypes */* is unknown"
  - "Recommends keeping BinaryMediaTypes */* (both sources require it) and testing on a deployed REST API"
must_not:
  - "States that all responses are Base64-encoded as fact"
  - "States that text responses are never encoded when the binary media types are */*"
```

---

## Scenario 3: Misuse Rejection (out-of-scope request)

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-plain-handler-cognito-depth-quarkus-4
skills: ["developing-quarkus-amazon-lambda-http-v3-40"]
query: "Write an SQS-triggered plain Lambda handler, design our Cognito user pool with per-tenant roles, write the SAM template, and do it on Quarkus 4."
must_pass:
  - "Declines the plain handler and points to developing-quarkus-amazon-lambda-v3-40 by name"
  - "Gives only the short security summary (enable-security=true, principals, map-cognito-to-roles) and points Cognito and tenant design to securing-quarkus-lambda-cognito-v3-40 by name"
  - "Says IaC for this family is Terraform (provisioning-aws-lambda-v6, provisioning-aws-api-gateway-v6), not SAM"
  - "Says the skill is locked to Quarkus 3.40 and does not cover Quarkus 4"
must_not:
  - "Writes the SQS handler or a SAM template"
  - "Designs the Cognito user pool inside this skill"
  - "Presents Quarkus 4 content as valid for 3.40"
```

---

## Scenario 4: Anti-Pattern Trap (REST native runtime)

**Type**: Copying a generated template value

```yaml
id: 4
name: trap-rest-sam-native-runtime-provided
skills: ["developing-quarkus-amazon-lambda-http-v3-40"]
query: "The quarkus-amazon-lambda-rest build generated target/sam.native.yaml with Runtime: provided. Put that runtime into the Terraform for my native REST API function."
must_pass:
  - "Refuses to copy Runtime: provided; says AWS deprecated it on 2024-01-08 (create blocked 2024-02-08, update blocked 2027-08-31)"
  - "Notes the HTTP extension's template writes provided.al2023 and tags the general native pairing (medium confidence)"
  - "Points to the Ask-First JVM, SnapStart or native decision in developing-quarkus-amazon-lambda-v3-40 for the runtime value instead of offering other runtimes itself"
  - "Still hands over DISABLE_SIGNAL_HANDLERS=true and BinaryMediaTypes */* from the templates"
must_not:
  - "Writes Runtime: provided into Terraform"
  - "Chooses native or JVM for the user"
```

---

## Scenario 5: Anti-Pattern Trap (wrong event type, two frameworks, security default)

**Type**: Code review

```yaml
id: 5
name: trap-wrong-event-two-frameworks-security-off
skills: ["developing-quarkus-amazon-lambda-http-v3-40"]
query: "Review: a quarkus-amazon-lambda-rest project has quarkus-rest and quarkus-undertow, a resource with @Context APIGatewayV2HTTPEvent event, and reads the Cognito user from SecurityContext.getUserPrincipal() with only map-cognito-to-roles=true configured."
must_pass:
  - "Flags two HTTP frameworks and asks to keep one"
  - "Flags APIGatewayV2HTTPEvent as the wrong type for the REST extension (null at runtime, tagged (medium confidence)) and replaces it with AwsProxyRequest"
  - "Flags that security is opt-in (guide: add quarkus.lambda-http.enable-security=true), so no Principal is registered without it, tags the default false as (medium confidence), and sets it to true"
  - "Points Cognito and tenant design to securing-quarkus-lambda-cognito-v3-40 by name"
must_not:
  - "Accepts two frameworks"
  - "Leaves enable-security off while expecting a Principal"
```

---

## Scenario 6: Edge Case (undocumented front ends and timeout)

**Type**: Ambiguous or unverified territory

```yaml
id: 6
name: edge-function-url-alb-and-gateway-timeout
skills: ["developing-quarkus-amazon-lambda-http-v3-40"]
query: "Can I put this behind a Lambda function URL or an ALB instead, and what status does the client get when my 40 second request times out at the gateway?"
must_pass:
  - "States the 3.40 guide documents API Gateway only and that Function URL and ALB support are (unverified); mentions the ALB code branch is code, not a documented feature (medium confidence)"
  - "States the HTTP API integration timeout is 30 s (not raisable) and the REST API default is 29 s (raisable for Regional or private); tags the Lambda-below-gateway budgeting rule (medium confidence)"
  - "States the status code seen on a gateway timeout is (unverified) and asks for the expected p99 latency"
must_not:
  - "Asserts Function URL or ALB are supported by quarkus-amazon-lambda-http"
  - "Gives a status code for the gateway timeout as fact"
```
