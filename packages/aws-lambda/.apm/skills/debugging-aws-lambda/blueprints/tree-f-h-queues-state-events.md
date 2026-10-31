# Elimination Tree: Branches F, G and H

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Source ids resolve in the [source bibliography](./source-bibliography.md). Every command is on the [read-only allowlist](./read-only-allowlist.md). Tags map to the [register](./unverified-and-risks.md#tag-to-register-mapping).

## Contents

- [Branch F SQS event source mapping](#branch-f-sqs-event-source-mapping)
- [Branch G control-plane state](#branch-g-control-plane-state)
- [Branch H EventBridge asynchronous](#branch-h-eventbridge-asynchronous)

## Branch F SQS event source mapping

```bash
# Representative, adapt to your environment (2026-10-28). Read-only.
aws lambda list-event-source-mappings --function-name my-function \
  --query 'EventSourceMappings[].{UUID:UUID,State:State,Why:StateTransitionReason,Last:LastProcessingResult,Resp:FunctionResponseTypes,Batch:BatchSize,Window:MaximumBatchingWindowInSeconds,Scaling:ScalingConfig,Metrics:MetricsConfig}'
# ESM State: Creating, Enabling, Enabled, Disabling, Disabled, Updating, Deleting   (S49)
```

| Branch | Symptom | Evidence and reading | Source |
|---|---|---|---|
| F1 | Messages reprocessed | By default an error returns the whole batch to the queue after the visibility timeout, unless the function reports batch item failures (`ReportBatchItemFailures`) | S27, S44 |
| F2 | A batch always fails | An exception makes the whole batch a complete failure even with `ReportBatchItemFailures`; so do invalid JSON in the response, an empty or null `itemIdentifier`, or an identifier that does not exist. A drop of `NumberOfMessagesDeleted` to 0 means failures are not reported correctly | S27 |
| F3 | Backlog | `AWS/SQS ApproximateAgeOfOldestMessage` (seconds, dimension `QueueName`) and `ApproximateNumberOfMessagesVisible`. On throttling, Lambda retries until the message timestamp exceeds the queue's visibility timeout, then drops the message. The age metric excludes messages received 3 or more times and not deleted on standard queues, so read the DLQ too | S27, S43 |
| F4 | DLQ filling | DLQ `ApproximateNumberOfMessagesVisible`; `maxReceiveCount` recommended at least 5 | S43, S48 |
| F5 | Configuration | Source queue visibility timeout at least 6 times the function timeout (plus `MaximumBatchingWindowInSeconds` when batching); ESM `State`, `StateTransitionReason`, `LastProcessingResult` | S48, S49 |
| F6 | ESM metrics missing | SQS ESM metrics (`PolledEventCount`, `InvokedEventCount`, `FailedInvokeEventCount`, `DeletedEventCount`, `FilteredOutEventCount`) exist only when `EventCount` metrics are enabled on the ESM; `FailedInvokeEventCount` includes non-empty `BatchItemFailures` | S8 |

Reading the queue itself: `aws sqs get-queue-attributes --queue-url <url> --attribute-names VisibilityTimeout RedrivePolicy` is named from the SQS API and its page was not fetched (medium confidence); a manual receive on the source queue hides messages for the visibility timeout, so it is not on the allowlist.

Scaling reference (for capacity questions, owner decides): a standard-queue ESM starts with 5 concurrent invokes, adds up to 300 per minute, maximum 1,250 on-demand (S48). Provisioned-mode `MaximumPollers`: "2-10,000" (S44) versus "2-2000" (S48), pages disagree (unverified).

## Branch G control-plane state

| Branch | State | Reading | Source |
|---|---|---|---|
| G1 | `Pending` for more than 6 minutes | Invocations and other API actions fail while `Pending`. AWS lists `Update*` calls or `PublishVersion` as the way to unblock; those mutate, so hand them to the deployer | S1, S29 |
| G2 | `LastUpdateStatus` `Failed` or `InProgress` | Invocations continue to use the previous code and configuration, so "my deploy did not take effect" is diagnosed here. The deploy procedure belongs to `deploying-aws-lambda` | S29 |
| G3 | `Inactive` | An invocation fails and sets the function to `Pending`; if reactivation fails it returns to `Inactive` | S29, S30 |

Reason codes seen in `StateReasonCode` and `LastUpdateStatusReasonCode`: `InsufficientRolePermissions`, `SubnetOutOfIPAddresses`, `EniLimitExceeded`, `KMSKeyAccessDenied`, `KMSKeyNotFound`, `InvalidStateKMSKey`, `DisabledKMSKey`, `InvalidRuntime`, `InvalidZipFileException`, `FunctionError.InitTimeout`, `FunctionError.RuntimeInitError`, `FunctionError.InvalidEntryPoint`, `FunctionError.PermissionDenied`, `FunctionError.InitResourceExhausted`; state values also include `Deactivating`, `Deactivated`, `ActiveNonInvocable`, `Deleting` (S30). SnapStart check: `SnapStart.OptimizationStatus` `On` and `State` `Active` on the version (https://docs.aws.amazon.com/lambda/latest/dg/snapstart-monitoring.html, S32).

## Branch H EventBridge asynchronous

A rule invokes the function asynchronously (S60).

| Branch | Symptom | Evidence and reading | Source |
|---|---|---|---|
| H1 | Rule target not invoked | EventBridge does not retry permission and missing-resource errors; other errors are retried for 24 hours, up to 185 attempts. Rule DLQ message attributes: `RULE_ARN`, `TARGET_ARN`, `ERROR_CODE` (for example `NO_PERMISSIONS`, `THROTTLING`, `TIMEOUT`), `ERROR_MESSAGE`, `EXHAUSTED_RETRY_CONDITION`, `RETRY_ATTEMPTS`. DLQ metrics `InvocationsSentToDLQ`, `InvocationsFailedToBeSentToDLQ`. The exact name of the failed-invocation metric (`FailedInvocations`) is not on the pages read (unverified) | S45, S47 |
| H2 | Lambda accepted the event, the function failed | Lambda retries function errors twice (after 1 minute, then 2 minutes); throttles and 5xx are retried up to 6 hours with backoff from 1 s to 5 minutes; then the DLQ or on-failure destination. Metrics `AsyncEventsReceived`, `AsyncEventAge`, `AsyncEventsDropped`, `DeadLetterErrors`, `DestinationDeliveryFailures` | S8, S34 |
| H3 | Duplicate executions | Duplicates are possible even without errors (eventually consistent queue); a handler must tolerate them | S5, S34 |

Invoke permission for EventBridge: the principal `events.amazonaws.com` with the rule ARN as source is known from a search snippet only (medium confidence); read the policy with `get-policy` and report what it shows ([patterns](./always-do-patterns.md#8-separate-the-two-permission-planes)).
