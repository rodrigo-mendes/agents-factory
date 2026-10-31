# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Severity wording: low, moderate, high. The mock-server port key names are advice, not a prohibition: see [Ask First C4](./ask-first-decisions.md#c4-fixed-or-random-mock-server-port).

## Contents

- [F1. Using `quarkus-test-amazon-lambda` or `LambdaClient`](#f1-using-quarkus-test-amazon-lambda-or-lambdaclient-severity-high)
- [F2. Calling real AWS from unit tests (team practice)](#f2-calling-real-aws-from-unit-tests-team-practice)
- [F3. `@InjectMock` or `@Inject` in a `@QuarkusIntegrationTest`](#f3-injectmock-or-inject-in-a-quarkusintegrationtest-severity-moderate)
- [F4. `sam.*.yaml` or `sam deploy` as the deployment path](#f4-samyaml-or-sam-deploy-as-the-deployment-path-severity-moderate)

## F1. Using `quarkus-test-amazon-lambda` or `LambdaClient` (severity: high)

"The Amazon Lambda Testing module `quarkus-test-amazon-lambda` and the `io.quarkus.amazon.lambda.test.LambdaClient`, which has been deprecated in Quarkus 2.3.0, have now been removed from Quarkus"; the instruction is to "move to using `RestAssured` instead" ([wiki 3.31](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)). The last Central version is 3.30.8 and the 3.40.1.1 POM returns HTTP 404 ([metadata](https://repo1.maven.org/maven2/io/quarkus/quarkus-test-amazon-lambda/maven-metadata.xml)). In source at tag 3.40.1.1, `LambdaClient` on the classpath ("legacy testing") means the mock event server is not started (medium confidence: source read through a summarising tool, [DevServicesLambdaProcessor](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/extensions/amazon-lambda/common-deployment/src/main/java/io/quarkus/amazon/lambda/deployment/DevServicesLambdaProcessor.java)). Impact: dependency resolution fails at 3.40.1.1; pinning 3.30.8 mixes Quarkus versions and disables the mock event server.

```xml
<!-- ❌ WRONG -->
<dependency>
  <groupId>io.quarkus</groupId>
  <artifactId>quarkus-test-amazon-lambda</artifactId>
  <scope>test</scope>
</dependency>
<!-- LambdaClient.invoke(Person.class, in) -->
```

```xml
<!-- ✅ CORRECT -->
<dependency><groupId>io.quarkus</groupId><artifactId>quarkus-junit</artifactId><scope>test</scope></dependency>
<dependency><groupId>io.rest-assured</groupId><artifactId>rest-assured</artifactId><scope>test</scope></dependency>
<!-- given().body(in).post().then().statusCode(200) -->
```

## F2. Calling real AWS from unit tests (team practice)

Basis: a family/team policy decision, not a statement of the guide. The guide says "Unit testing is the same as any other Java project and does not require running on Amazon" ([aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)), which does not forbid real AWS; Dev Services start "a containerized AWS stack ... when running tests" ([Dev Services](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html)). Impact the team wants to avoid: cost, data mutation, credentials leaking into CI, flaky tests.

```properties
# ❌ WRONG
%test.quarkus.dynamodb.endpoint-override=https://dynamodb.eu-west-1.amazonaws.com
# plus real access keys in CI env
```

```properties
# ✅ CORRECT: no endpoint-override in %test -> the Dev Services container starts (amazon-services 3.23.x)
```

Or `@InjectMock` on the CDI bean wrapping the client (`developing-quarkus-junit-v3-40`). Choosing between them is [decision C1](./ask-first-decisions.md#c1-dev-services-injectmock-or-endpoint-override).

## F3. `@InjectMock` or `@Inject` in a `@QuarkusIntegrationTest` (severity: moderate)

`@QuarkusIntegrationTest` "supports all the features mentioned in this guide except injecting into tests"; `@TestSecurity` "is only available for `@QuarkusTest`" ([testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing), [security-testing](https://quarkus.io/version/3.40/guides/security-testing)). Impact: the IT does not see the mock; the real bean, and possibly real I/O, runs.

```java
// ❌ WRONG
@QuarkusIntegrationTest
class OrderLambdaIT { @InjectMock OrderRepository repo; }
```

```java
// ✅ CORRECT: mocks only in @QuarkusTest
@QuarkusTest
class OrderLambdaTest { @InjectMock OrderRepository repo; }
```

Re-running the same class as an IT with `extends` is (medium confidence); see [always-do 4](./always-do-patterns.md#4-integration-and-native-tests). Container dependencies in an IT: whether Dev Services apply there is (unverified).

## F4. `sam.*.yaml` or `sam deploy` as the deployment path (severity: moderate)

The 3.40 guides present the SAM CLI under "Testing with the SAM CLI" and "Simulate AWS Lambda Deployment with SAM CLI", that is local testing ([aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda), [aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http)). Family rule: IaC is Terraform (`provisioning-aws-*-v6`).

```bash
# ❌ WRONG
sam deploy --template target/sam.jvm.yaml
```

```bash
# ✅ CORRECT (representative — adapt to your environment)
sam local invoke --template target/sam.jvm.yaml --event payload.json   # optional local emulation only
# deployment: Terraform (provisioning-aws-lambda-v6) consuming target/function.zip
```
