# Verification Loop

Back to [SKILL.md](../SKILL.md). Commands are representative; adapt them to your environment. Test depth (mock event server, Dev Services) is the [testing skill](../../testing-quarkus-amazon-lambda-v3-40/SKILL.md).

## Verification Loop

```bash
# Representative - adapt to your environment
# 1. Only 3.23.x of the Quarkiverse extensions on the classpath
mvn -q dependency:tree -Dincludes=io.quarkiverse.amazonservices
# Expected: quarkus-amazon-{sqs,sns,eventbridge,ssm,secretsmanager}:3.23.0 (no 4.0.0.Beta*)

# 2. Sync HTTP implementation present for SQS/SNS/EventBridge
mvn -q dependency:tree -Dincludes=software.amazon.awssdk:url-connection-client
# Expected: one match

# 3. No static AWS keys outside %dev/%test
grep -nE '^quarkus\.[a-z]+\.aws\.credentials\.static-provider' src/main/resources/application.properties
# Expected: no output (exit code 1)

# 4. SQS handlers return SQSBatchResponse
grep -rn "RequestHandler<SQSEvent" src/main/java | grep -v "SQSBatchResponse"
# Expected: no output

# 5. Batch publish results are inspected
grep -rnE "sendMessageBatch|publishBatch|putEvents" src/main/java
# Expected: every call site assigns the response and reads failed() / entries()

# 6. events library version resolved (managed version 3.16.1 is medium confidence, M13; native reflection U4, unverified)
mvn -q dependency:tree -Dincludes=com.amazonaws
```

## Handler unit test

The handler logic can be tested by building `SQSEvent` / `SQSMessage` objects and asserting `batchItemFailures`. The services can run locally through Quarkiverse Dev Services (`quarkus.<svc>.devservices.*`; provider options include `localstack`, `ministack`, `moto`, `floci` on the SNS and EventBridge pages) ([SNS page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-sns.html), [EventBridge page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-eventbridge.html)). The JUnit style is `developing-quarkus-junit-v3-40`.

```java
// Illustrative (medium confidence): setters from aws-lambda-java-events are (medium confidence)
SQSEvent.SQSMessage bad = new SQSEvent.SQSMessage();
bad.setMessageId("id2");
bad.setBody("not-json");
SQSEvent event = new SQSEvent();
event.setRecords(List.of(bad));
SQSBatchResponse resp = handler.handleRequest(event, null);
assertEquals("id2", resp.getBatchItemFailures().get(0).getItemIdentifier());
```

## Runtime checks

- Init time: compare `Init Duration` in CloudWatch with and without the config sources (U3, unverified).
- Queue health: `NumberOfMessagesDeleted` and `ApproximateAgeOfOldestMessage` ([AWS](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)).
