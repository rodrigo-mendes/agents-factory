# Evaluation Scenarios: developing-quarkus-amazon-lambda-v3-40

Six scenarios, covering the four required types. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (SnapStart restore limit and renamed property)](#scenario-2-edge-case-snapstart-restore-limit-and-renamed-property)
- [Scenario 3: Misuse Rejection (out-of-scope request)](#scenario-3-misuse-rejection-out-of-scope-request)
- [Scenario 4: Anti-Pattern Trap (SnapStart on native)](#scenario-4-anti-pattern-trap-snapstart-on-native)
- [Scenario 5: Anti-Pattern Trap (uniqueness and CRaC reference)](#scenario-5-anti-pattern-trap-uniqueness-and-crac-reference)
- [Scenario 6: Edge Case (decisions the guide does not settle)](#scenario-6-edge-case-decisions-the-guide-does-not-settle)

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-plain-handler-function-zip
skills: ["developing-quarkus-amazon-lambda-v3-40"]
query: "Create a plain (non-HTTP) AWS Lambda in Quarkus 3.40 that takes a JSON InputObject and returns an OutputObject, and tell me what to hand to Terraform."
must_pass:
  - "Adds quarkus-amazon-lambda without a version (BOM-managed) and a class implementing RequestHandler<InputObject, OutputObject> annotated @Named"
  - "States the Lambda handler is io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest and the user class is selected with quarkus.lambda.handler (env QUARKUS_LAMBDA_HANDLER) matching the @Named value"
  - "Names target/function.zip as the only deployment artifact and defers IaC to provisioning-aws-lambda-v6 (no SAM or CDK)"
  - "Asks the user whether to use JVM, JVM + SnapStart or native before fixing a runtime"
must_not:
  - "Pins a handler value of the user class"
  - "Chooses native or SnapStart without asking"
  - "Writes Terraform or SAM templates"
```

---

## Scenario 2: Edge Case (SnapStart restore limit and renamed property)

**Type**: Conflicting sources and a deprecated name the guide still shows

```yaml
id: 2
name: edge-restore-limit-and-snapstart-enabled
skills: ["developing-quarkus-amazon-lambda-v3-40"]
query: "My afterRestore hook takes 5 seconds. Is that allowed? Also the Quarkus guide says quarkus.snapstart.enable=true, is that right?"
must_pass:
  - "Cites both statements: the Quarkus 3.40 SnapStart guide says restoration is limited to 2 seconds, AWS says runtime load plus afterRestore must finish within 10 seconds or SnapStartTimeoutException"
  - "Tags which limit applies as (unverified) and recommends keeping afterRestore work minimal"
  - "Says quarkus.snapstart.enable is deprecated since 3.26 and gives quarkus.snapstart.enabled"
must_not:
  - "Silently picks 2 s or 10 s as the one true limit"
  - "Recommends quarkus.snapstart.enable"
```

---

## Scenario 3: Misuse Rejection (out-of-scope request)

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-http-api-gateway-and-quarkus-4
skills: ["developing-quarkus-amazon-lambda-v3-40"]
query: "Expose my Quarkus Lambda behind API Gateway with a Cognito authorizer, and write the SAM template. Use Quarkus 4 while you are at it."
must_pass:
  - "Declines to cover HTTP/API Gateway and points to developing-quarkus-amazon-lambda-http-v3-40 by name"
  - "Points Cognito to securing-quarkus-lambda-cognito-v3-40 by name"
  - "Says IaC for this family is Terraform (provisioning-aws-lambda-v6), not SAM"
  - "Says the skill is locked to Quarkus 3.40 and does not cover Quarkus 4"
must_not:
  - "Invents API Gateway or Cognito configuration"
  - "Produces a SAM template as the deployment path"
  - "Presents Quarkus 4 or Beta content as valid for 3.40"
```

---

## Scenario 4: Anti-Pattern Trap (SnapStart on native)

**Type**: Request that mixes two mutually exclusive modes

```yaml
id: 4
name: trap-snapstart-on-native-provided-runtime
skills: ["developing-quarkus-amazon-lambda-v3-40"]
query: "Build the native function.zip, deploy it on provided.al2023 and turn on SnapStart with ApplyOn=PublishedVersions for the fastest cold start."
must_pass:
  - "Says SnapStart does not support OS-only runtimes, so it cannot be combined with a native Quarkus function"
  - "Offers the two valid paths (JVM function.zip on java21 or java17.al2023 with SnapStart, or native without SnapStart) and asks the user to choose"
  - "If native is chosen, sets DISABLE_SIGNAL_HANDLERS=true and states the zip contains the executable renamed bootstrap"
  - "Tags the native on provided.al2023 pairing as (medium confidence)"
must_not:
  - "Agrees to configure SnapStart on the native function"
  - "States how Lambda behaves when it is configured anyway (rejected vs ignored is unverified)"
  - "Recommends provided.al2 or java17 (AL2) for a new function"
```

---

## Scenario 5: Anti-Pattern Trap (uniqueness and CRaC reference)

**Type**: Code review of SnapStart state

```yaml
id: 5
name: trap-init-time-uuid-and-unreferenced-resource
skills: ["developing-quarkus-amazon-lambda-v3-40"]
query: "Review this: an @ApplicationScoped bean has `final String instanceId = UUID.randomUUID().toString();` and a @PostConstruct that calls Core.getGlobalContext().register(new CacheWarmer()). The function uses SnapStart."
must_pass:
  - "Flags the init-time UUID as not unique across execution environments and moves generation to the handler or afterRestore, with java.security.SecureRandom for randomness"
  - "Flags the unreferenced new CacheWarmer(): the global context holds a WeakReference so hooks may never run; keeps the instance in a field"
  - "Notes that using the CDI bean as the strong reference is an inference (medium confidence)"
must_not:
  - "Accepts the init-time UUID"
  - "Claims org.crac must be added to the build (unverified)"
```

---

## Scenario 6: Edge Case (decisions the guide does not settle)

**Type**: Ambiguous or unverified territory

```yaml
id: 6
name: edge-native-handler-value-and-sqs-input
skills: ["developing-quarkus-amazon-lambda-v3-40"]
query: "For the native function which handler string do I put in Terraform, and can my handler take an SQSEvent directly? Is 3 seconds enough timeout?"
must_pass:
  - "States the guide does not give the native handler value and that this is (unverified); does not invent one"
  - "States aws-lambda-java-events is on the classpath through quarkus-amazon-lambda-common but using SQSEvent as input is not documented in the 3.40 guide (unverified)"
  - "States 3 seconds is the AWS default timeout (maximum 900 s) and that whether it covers a JVM cold first call is (unverified); asks for measured duration"
must_not:
  - "Asserts QuarkusStreamHandler::handleRequest works for native without saying the guide does not state it"
  - "Guarantees a timeout number"
```
