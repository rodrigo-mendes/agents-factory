# Never Do Patterns — AWS Step Functions

6 anti-patterns with exact ❌ wrong / ✅ correct ASL pairs. Sources accessed 2026-07-31.

---

## AP-1 — Task state with no `TimeoutSeconds`

**Risk**: HIGH — Reliability
**Source**: [Best practices — stuck executions](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#sfn-stuck-execution)

"Without an explicit timeout, Step Functions often relies solely on a response from an activity worker… an execution is stuck waiting for a response that will never come."

```json
// WRONG — hangs forever if the worker dies or never responds
{
  "ActivityState": {
    "Type": "Task",
    "Resource": "arn:aws:states:us-east-1:123456789012:activity:HelloWorld",
    "Next": "NextState"
  }
}
```

```json
// CORRECT — bounded wait; heartbeat detects worker death early
{
  "ActivityState": {
    "Type": "Task",
    "Resource": "arn:aws:states:us-east-1:123456789012:activity:HelloWorld",
    "TimeoutSeconds": 300,
    "HeartbeatSeconds": 60,
    "Next": "NextState"
  }
}
```

Detection: Static scan of the ASL definition for Task states lacking `TimeoutSeconds`.
Impact: Stuck Standard executions accumulate per-transition billing; SLA breach; cascading backlog.

---

## AP-2 — Non-idempotent steps inside an Express workflow

**Risk**: CRITICAL — Correctness / Reliability
**Source**: [Choosing workflow type](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html)

Async Express is *at-least-once* — the same step may execute more than once. Non-idempotent actions (charge a card, start a cluster, send a notification exactly once) MUST use Standard.

```json
// WRONG — Express async: payment may be charged twice
{
  "Type": "EXPRESS",
  "States": {
    "ChargeCustomer": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ChargeCreditCard"
      },
      "End": true
    }
  }
}
```

```json
// CORRECT — Standard parent for non-idempotent step; Express nested only for idempotent work
{
  "Type": "STANDARD",
  "States": {
    "ChargeCustomer": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ChargeCreditCard"
      },
      "TimeoutSeconds": 30,
      "Next": "SendNotifications"
    },
    "SendNotifications": {
      "Type": "Task",
      "Resource": "arn:aws:states:::states:startExecution",
      "Parameters": {
        "StateMachineArn": "arn:aws:states:us-east-1:123456789012:stateMachine:NotifyExpress",
        "Input.$": "$"
      },
      "End": true
    }
  }
}
```

Detection: Review `type` of each state machine against the side-effect profile of its Task resources.
Impact: Double charges, duplicate job starts, data corruption — silent and hard to detect post-facto.

---

## AP-3 — Passing >256 KiB payloads directly between states

**Risk**: HIGH — Reliability
**Source**: [Best practices — avoid execution failures](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#avoid-exec-failures)

`States.DataLimitExceeded` is a terminal error — it cannot be caught by `States.ALL` or any `Catch` block.

```json
// WRONG — Lambda returns 2 MB JSON; next state consumes it directly
{
  "GenerateReport": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Parameters": {
      "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:GenerateLargeReport"
    },
    "Next": "ProcessReport"
  }
}
```

```json
// CORRECT — Lambda writes to S3; states pass only the ARN reference
{
  "GenerateReport": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Parameters": {
      "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:GenerateLargeReport"
    },
    "ResultSelector": {
      "bucket.$": "$.Payload.bucket",
      "key.$": "$.Payload.key"
    },
    "Next": "ProcessReport",
    "TimeoutSeconds": 120
  },
  "ProcessReport": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Parameters": {
      "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ProcessReportFromS3",
      "Payload": {
        "bucket.$": "$.bucket",
        "key.$": "$.key"
      }
    },
    "TimeoutSeconds": 60,
    "End": true
  }
}
```

Detection: Monitor CloudWatch for `States.DataLimitExceeded`; inspect state output sizes in execution history.
Impact: Hard terminal failure; work already done in upstream states is lost unless redriven.

---

## AP-4 — Lambda Task with no explicit Retry or only a `States.ALL` retrier

**Risk**: HIGH — Reliability
**Source**: [Best practices — Lambda service exceptions](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#bp-lambda-serviceexception) · [Error handling](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html)

`States.ALL` does **not** catch `States.DataLimitExceeded` or `States.Runtime`. Transient Lambda 500-series errors are not automatically retried without an explicit retrier.

```json
// WRONG — no Retry; or only States.ALL catcher with no retrier
{
  "CallLambda": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Parameters": {
      "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:MyFunction"
    },
    "Catch": [
      { "ErrorEquals": ["States.ALL"], "Next": "HandleError" }
    ],
    "End": true
  }
}
```

```json
// CORRECT — explicit retriers for transient errors; States.ALL catcher is last
{
  "CallLambda": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Parameters": {
      "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:MyFunction",
      "Payload.$": "$"
    },
    "TimeoutSeconds": 30,
    "Retry": [
      {
        "ErrorEquals": [
          "Lambda.ClientExecutionTimeoutException",
          "Lambda.ServiceException",
          "Lambda.AWSLambdaException",
          "Lambda.SdkClientException"
        ],
        "IntervalSeconds": 2,
        "MaxAttempts": 6,
        "BackoffRate": 2,
        "JitterStrategy": "FULL"
      },
      {
        "ErrorEquals": ["Lambda.Unknown", "Sandbox.Timedout"],
        "IntervalSeconds": 5,
        "MaxAttempts": 3,
        "BackoffRate": 2
      }
    ],
    "Catch": [
      {
        "ErrorEquals": ["States.ALL"],
        "Next": "HandleError",
        "ResultPath": "$.error"
      }
    ],
    "Next": "ProcessResult"
  }
}
```

Detection: Audit every `lambda:invoke` Task for a `Retry` block; inject a transient error in TestState and confirm `TaskRetry` events appear.
Impact: Avoidable execution failures from recoverable transient errors; increased cost from wasted upstream work.

---

## AP-5 — Execution role with `Resource: "*"` on `states:*` or `lambda:InvokeFunction`

**Risk**: CRITICAL — Security
**Source**: [Distributed Map permissions](https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html#dist-map-permissions)

A wildcard execution role lets any compromise of the state machine call any Lambda function or start any state machine in the account.

```json
// WRONG — wildcard enables lateral movement
{
  "Effect": "Allow",
  "Action": ["states:*", "lambda:InvokeFunction"],
  "Resource": "*"
}
```

```json
// CORRECT — scoped to exact ARNs
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:MySpecificFunction"
    },
    {
      "Effect": "Allow",
      "Action": ["states:StartExecution", "states:DescribeExecution"],
      "Resource": [
        "arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine",
        "arn:aws:states:us-east-1:123456789012:execution:MyStateMachine:*"
      ]
    }
  ]
}
```

Detection: IAM Access Analyzer policy validation; grep all execution role policies for `"Resource": "*"` paired with `states:*` or `lambda:*`.
Impact: Privilege escalation; lateral movement with the state machine's assumed role; account-wide blast radius.

---

## AP-6 — Single Standard execution with tens of thousands of inline steps

**Risk**: MEDIUM — Reliability
**Source**: [Best practices — execution history limit](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#bp-history-limit)

"At 25,000 events the execution waits and fails with `ExecutionFailed` if event 25,000 is not `ExecutionSucceeded`." Inline Map iterations share the parent execution's event count.

```json
// WRONG — Inline Map with 50,000 items each generating multiple events
{
  "ProcessAllRecords": {
    "Type": "Map",
    "ItemsPath": "$.records",
    "MaxConcurrency": 40,
    "Iterator": {
      "StartAt": "ProcessOne",
      "States": {
        "ProcessOne": {
          "Type": "Task",
          "Resource": "arn:aws:states:::lambda:invoke",
          "End": true
        }
      }
    },
    "End": true
  }
}
```

```json
// CORRECT — Distributed Map: each iteration is an isolated child execution
{
  "ProcessAllRecords": {
    "Type": "Map",
    "ItemProcessor": {
      "ProcessorConfig": {
        "Mode": "DISTRIBUTED",
        "ExecutionType": "EXPRESS"
      },
      "StartAt": "ProcessOne",
      "States": {
        "ProcessOne": {
          "Type": "Task",
          "Resource": "arn:aws:states:::lambda:invoke",
          "Parameters": {
            "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ProcessRecord",
            "Payload.$": "$"
          },
          "TimeoutSeconds": 30,
          "End": true
        }
      }
    },
    "ItemReader": {
      "Resource": "arn:aws:states:::s3:getObject",
      "ReaderConfig": { "InputType": "CSV", "CSVHeaderLocation": "FIRST_ROW" },
      "Parameters": { "Bucket": "my-bucket", "Key": "data/input.csv" }
    },
    "MaxConcurrency": 1000,
    "ToleratedFailurePercentage": 5,
    "End": true
  }
}
```

Detection: Monitor `ExecutionsFailed`; alarm on state machines where executions regularly exceed 20,000 events (CloudWatch metric `ExecutionThrottled` or custom event-count metric).
Impact: Late-stage failure of long, expensive workflows after significant compute has already been billed.
