# Evaluation Scenarios: integrating-quarkus-amazon-messaging-v3-40

Six scenarios, covering the four required types. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (limits and bus type)](#scenario-2-edge-case-limits-and-bus-type)
- [Scenario 3: Misuse Rejection (out-of-scope request)](#scenario-3-misuse-rejection-out-of-scope-request)
- [Scenario 4: Anti-Pattern Trap (handler and publisher review)](#scenario-4-anti-pattern-trap-handler-and-publisher-review)
- [Scenario 5: Edge Case (config sources in Lambda)](#scenario-5-edge-case-config-sources-in-lambda)
- [Scenario 6: Anti-Pattern Trap (SNS FIFO and HTTP client)](#scenario-6-anti-pattern-trap-sns-fifo-and-http-client)

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-sqs-partial-batch-handler
skills: ["integrating-quarkus-amazon-messaging-v3-40"]
query: "Write a Quarkus 3.40 Lambda that consumes an SQS queue, publishes a follow-up message to SNS, and tell me what the queue and event source mapping need."
must_pass:
  - "Uses io.quarkiverse.amazonservices 3.23.0 through quarkus-amazon-services-bom with unversioned quarkus-amazon-sqs and quarkus-amazon-sns, and adds software.amazon.awssdk:url-connection-client explicitly"
  - "Implements RequestHandler<SQSEvent, SQSBatchResponse> that catches per record and returns the failed messageId values, with ReportBatchItemFailures on the event source mapping"
  - "States visibility timeout at least 6 times the function timeout (plus the batch window) and maxReceiveCount at least 5, and defers them to provisioning-aws-sqs-v6 (no SAM or CDK)"
  - "Makes the handler idempotent on messageId and keeps credentials at their default (execution role) and tags the AWS_REGION pick-up as (medium confidence), pointing to the data skill's Ask First C3"
must_not:
  - "Throws from the handler for one bad record"
  - "Writes static AWS keys in the production profile"
  - "Writes Terraform, SAM or CDK"
```

---

## Scenario 2: Edge Case (limits and bus type)

**Type**: Conflicting limits and an unverified SDK capability

```yaml
id: 2
name: edge-batch-limits-and-eventbridge-bus
skills: ["integrating-quarkus-amazon-messaging-v3-40"]
query: "What is the SQS max message size, how many entries can I put in a PutEvents call, and how big can an SNS message be?"
must_pass:
  - "Says SQS messages are up to 1,048,576 bytes (1 MiB) with at most 10 per batch, not 256 KB"
  - "Says SNS defaults to 256 KiB and is raisable to 1 MiB with MaximumMessageSize"
  - "Says classic-bus PutEvents takes 1 to 10 entries while the quota page lists 1 to 100 for the Custom Event Bus, and asks which bus type applies (Ask First Q5)"
  - "Tags SDK 2.55.6 support of the Custom Event Bus as (unverified) (U6) and chunks at 10 until verified"
must_not:
  - "Gives 100 entries as the single answer without asking the bus type"
  - "States 256 KB as the SQS limit"
```

---

## Scenario 3: Misuse Rejection (out-of-scope request)

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-dynamodb-terraform-and-quarkus-4
skills: ["integrating-quarkus-amazon-messaging-v3-40"]
query: "Add a DynamoDB idempotency table, write the Terraform for the SQS queue and its redrive policy, and use quarkus-amazon-sqs 4.0.0.Beta3 on Quarkus 4."
must_pass:
  - "Points the DynamoDB idempotency store to integrating-quarkus-amazon-data-v3-40 by name"
  - "Says the queue and redrive policy are Terraform in provisioning-aws-sqs-v6 and gives only the values to hand over (visibility timeout at least 6x, maxReceiveCount at least 5)"
  - "Says the skill is locked to Quarkiverse 3.23.0 on Quarkus 3.40 and rejects 4.0.0.Beta* as the Quarkus 4 line"
must_not:
  - "Writes DynamoDB client code or a Terraform resource block"
  - "Presents 4.0.0.Beta3 content as valid for 3.40"
```

---

## Scenario 4: Anti-Pattern Trap (handler and publisher review)

**Type**: Code review of three traps at once

```yaml
id: 4
name: trap-throwing-handler-ignored-failed-and-static-keys
skills: ["integrating-quarkus-amazon-messaging-v3-40"]
query: "Review: the SQS handler is RequestHandler<SQSEvent, Void> and rethrows on a bad body; a publisher calls sqs.sendMessageBatch with 250 entries and ignores the result; application.properties sets quarkus.sqs.aws.credentials.type=static with AKIA keys."
must_pass:
  - "Flags that a thrown exception makes the whole batch a complete failure and returns SQSBatchResponse with failed messageId values instead (N1, N2)"
  - "Flags the ignored result: HTTP 200 does not mean every entry succeeded, so the Failed list must be inspected (N4); notes the accessor name failed() is (medium confidence) (M4)"
  - "Flags 250 entries in one call (maximum 10) and splits into chunks of 10, checking each response (N5)"
  - "Flags the static keys in the production profile and keeps the default credentials type, static only under %dev (N7)"
must_not:
  - "Accepts retry-everything as a fix for the missing result check"
  - "Keeps the AKIA keys in a prod property file"
```

---

## Scenario 5: Edge Case (config sources in Lambda)

**Type**: Behaviour no page documents

```yaml
id: 5
name: edge-ssm-reload-and-snapstart-config-source
skills: ["integrating-quarkus-amazon-messaging-v3-40"]
query: "I enable quarkus.ssm.config with the default update interval and SnapStart. Will rotated parameters refresh, and how much cold start does it add?"
must_pass:
  - "States that SSM reload in a frozen Lambda environment (I1) and config-source values under SnapStart (I2) are (unverified): no official page states them"
  - "States the cold-start cost is (unverified) (U3) and suggests measuring Init Duration with and without the sources"
  - "Lists documented defaults per key: enabled false, recursive true, with-decryption true, update-interval-minutes 5, 0 meaning fetch once"
  - "Asks (Q1, Q2) whether runtime refresh is required and offers the injected client or the Parameters and Secrets Lambda Extension (token from the credential provider chain in the handler) for rotated values; update-interval-minutes=0 is (medium confidence)"
must_not:
  - "Asserts that parameters will or will not refresh under SnapStart"
  - "Quotes a cold-start figure"
```

---

## Scenario 6: Anti-Pattern Trap (SNS FIFO and HTTP client)

**Type**: Design trap plus an Ask-First decision

```yaml
id: 6
name: trap-sns-fifo-trigger-and-apache-native
skills: ["integrating-quarkus-amazon-messaging-v3-40"]
query: "Subscribe my Quarkus Lambda to an SNS FIFO topic and set quarkus.sns.sync-client.type=apache for the native build. Should I switch to the CRT client for faster starts?"
must_pass:
  - "Says Lambda supports SNS triggers for standard topics only and points ordered processing to architecting-aws-sns-pubsub (N8)"
  - "Says native sync mode should prefer the URL Connection client over Apache and keeps sync-client.type=url plus url-connection-client (N10)"
  - "Treats the CRT choice as Ask First (Q4): the CRT native library is not embedded by default (since CRT 0.31.0), links integrating-quarkus-amazon-data-v3-40, and asks whether many independent calls or a CRT standard apply"
must_not:
  - "Subscribes the Lambda to the FIFO topic"
  - "Recommends the CRT client as the default"
```
