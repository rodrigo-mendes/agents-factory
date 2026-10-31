# Evaluation Scenarios: testing-quarkus-amazon-lambda-v3-40

Six scenarios, covering the four required types. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (random port and RestAssured)](#scenario-2-edge-case-random-port-and-restassured)
- [Scenario 3: Misuse Rejection (out-of-scope request)](#scenario-3-misuse-rejection-out-of-scope-request)
- [Scenario 4: Anti-Pattern Trap (removed LambdaClient)](#scenario-4-anti-pattern-trap-removed-lambdaclient)
- [Scenario 5: Anti-Pattern Trap (real AWS in tests)](#scenario-5-anti-pattern-trap-real-aws-in-tests)
- [Scenario 6: Edge Case (secured HTTP Lambda)](#scenario-6-edge-case-secured-http-lambda)

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-plain-handler-test
skills: ["testing-quarkus-amazon-lambda-v3-40"]
query: "Write an offline test for my plain Quarkus 3.40 Lambda that takes a Person JSON and returns a greeting. No AWS account is available."
must_pass:
  - "Uses @QuarkusTest with RestAssured posting the JSON to the mock event server (port 8081 in test mode) and asserts status 200 and the body"
  - "Declares io.quarkus:quarkus-junit and io.rest-assured:rest-assured in test scope"
  - "Tags the reconstructed test code or the Maven dependency form as (medium confidence) where it is not verbatim from the guide"
  - "Mentions that a handler error returns status 500 from the mock event server (medium confidence)"
must_not:
  - "Uses quarkus-test-amazon-lambda or LambdaClient"
  - "Calls real AWS or requires credentials"
```

---

## Scenario 2: Edge Case (random port and RestAssured)

**Type**: Behaviour the documentation does not settle

```yaml
id: 2
name: edge-random-mock-port
skills: ["testing-quarkus-amazon-lambda-v3-40"]
query: "Our CI runs tests in parallel. Set the mock event server to a random port, and confirm RestAssured follows it automatically. Does quarkus.lambda.test-port also work?"
must_pass:
  - "Gives quarkus.lambda.mock-event-server.test-port=0 as the documented way to get a random port"
  - "States that whether RestAssured follows a random or overridden port is (unverified) and asks whether tests run in parallel on shared hosts"
  - "Says quarkus.lambda.test-port exists and is not deprecated but the start-up reads only the mock-event-server names (medium confidence); recommends the mock-event-server names"
must_not:
  - "Guarantees that RestAssured follows the random port"
  - "Recommends quarkus.lambda.test-port"
```

---

## Scenario 3: Misuse Rejection (out-of-scope request)

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-deploy-and-quarkus-4
skills: ["testing-quarkus-amazon-lambda-v3-40"]
query: "Deploy my Quarkus Lambda with sam deploy, design the Cognito pool, and write the tests for Quarkus 4."
must_pass:
  - "Says SAM is optional local emulation only and deployment is Terraform (provisioning-aws-lambda-v6) consuming function.zip"
  - "Points Cognito design to securing-quarkus-lambda-cognito-v3-40 by name"
  - "Says the skill is locked to Quarkus 3.40 and does not cover Quarkus 4"
must_not:
  - "Presents sam deploy or sam.*.yaml as a deployment path"
  - "Invents Cognito pool configuration"
  - "Presents Quarkus 4 or Beta content as valid for 3.40"
```

---

## Scenario 4: Anti-Pattern Trap (removed LambdaClient)

**Type**: Request that uses a removed artifact

```yaml
id: 4
name: trap-lambda-client-after-upgrade
skills: ["testing-quarkus-amazon-lambda-v3-40"]
query: "After upgrading to Quarkus 3.40 my build cannot resolve io.quarkus:quarkus-test-amazon-lambda. Pin 3.30.8 so LambdaClient.invoke keeps working."
must_pass:
  - "Says the module and LambdaClient were removed in 3.31, the last Central version is 3.30.8 and no 3.40.1.1 artifact exists"
  - "Refuses to pin 3.30.8 and gives the migration: quarkus-junit + RestAssured post() against the mock event server"
  - "Notes that LambdaClient on the classpath disables the mock event server (medium confidence)"
  - "Lists the guard grep for quarkus-test-amazon-lambda and LambdaClient"
must_not:
  - "Agrees to pin 3.30.8"
  - "Keeps LambdaClient in any example"
```

---

## Scenario 5: Anti-Pattern Trap (real AWS in tests)

**Type**: Test profile that points to real AWS

```yaml
id: 5
name: trap-real-aws-endpoint-in-test-profile
skills: ["testing-quarkus-amazon-lambda-v3-40"]
query: "My handler writes to DynamoDB. In application.properties I set %test.quarkus.dynamodb.endpoint-override to the eu-west-1 endpoint and use CI access keys. Is that fine for the tests?"
must_pass:
  - "Rejects real AWS in tests as the family/team practice (not a statement of the guide): cost, data mutation, credential leakage, flaky tests"
  - "Says endpoint-override disables Dev Services; offers leaving it out of the test profile (container) as one option of the Ask First choice between Dev Services, @InjectMock and endpoint-override, not as a fixed rule"
  - "Offers @InjectMock on the CDI bean (rules in developing-quarkus-junit-v3-40) and asks whether Docker is available in CI and whether the SDK call must be exercised"
  - "Says Dev Services in @QuarkusIntegrationTest and the injected credentials are (unverified)"
must_not:
  - "Accepts the real endpoint"
  - "Uses @InjectMock inside a @QuarkusIntegrationTest"
  - "Asserts Docker-less Dev Services work"
```

---

## Scenario 6: Edge Case (secured HTTP Lambda)

**Type**: Ambiguous or unverified territory

```yaml
id: 6
name: edge-secured-http-lambda-test
skills: ["testing-quarkus-amazon-lambda-v3-40"]
query: "Test a Cognito-secured quarkus-amazon-lambda-http endpoint. Can I just use @TestSecurity? Show me the raw event helper."
must_pass:
  - "Prefers claims in the API Gateway event posted to /_lambda_ with quarkus.lambda-http.enable-security=true (guide: security is opt-in; default false tagged (medium confidence))"
  - "States @TestSecurity is only available for @QuarkusTest and that its effect through the Lambda mock event server is (unverified)"
  - "States the guide does not show the request(String) helper and the REST-API (AwsProxyRequest) raw-event example (unverified) and does not invent them"
  - "Notes the Cognito claim path differs between the HTTP API and the REST API (aws-lambda-http guide) and that cognito:username is an ID-token claim while access tokens carry username (AWS Cognito access-token page)"
must_not:
  - "Claims @TestSecurity works through the Lambda path"
  - "Presents an invented request() helper as documented"
  - "Designs the Cognito security model (belongs to securing-quarkus-lambda-cognito-v3-40)"
```
