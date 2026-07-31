# Always Do Patterns — AWS Step Functions

7 mandatory patterns derived from official AWS best practices (accessed 2026-07-31).

---

## Pattern 1 — Choose workflow type by idempotency + duration (permanent choice)

**Source**: [Choosing workflow type](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html)

| Criterion | → Choose |
|---|---|
| Any step is non-idempotent (payment, job start, provisioning) | **Standard** |
| Workflow must run >5 minutes | **Standard** |
| Need `.sync` or `.waitForTaskToken` integration | **Standard** |
| Need Distributed Map or Activities | **Standard** |
| Need full execution history (90-day audit) | **Standard** |
| All steps idempotent AND ≤5 min AND high volume (100k/s) | **Express async** |
| Synchronous request/response API composition | **Express sync** |

Cost note: Standard bills per state transition; Express bills per execution + duration + memory. High-frequency short workflows are usually cheaper on Express.

Verification:
```bash
aws stepfunctions describe-state-machine --state-machine-arn <arn> --query type
# Expected: "STANDARD" or "EXPRESS"
```

---

## Pattern 2 — Set `TimeoutSeconds` on every Task state

**Source**: [Best practices — stuck executions](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#sfn-stuck-execution)

Without a timeout, a Task/Activity state hangs indefinitely if the worker becomes unresponsive.

```json
{
  "ActivityState": {
    "Type": "Task",
    "Resource": "arn:aws:states:us-east-1:123456789012:activity:MyWorker",
    "TimeoutSeconds": 300,
    "HeartbeatSeconds": 60,
    "Next": "NextState"
  },
  "CallbackState": {
    "Type": "Task",
    "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
    "Parameters": {
      "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/MyQueue",
      "MessageBody": {
        "taskToken.$": "$$.Task.Token"
      }
    },
    "TimeoutSeconds": 86400,
    "HeartbeatSeconds": 3600,
    "Next": "NextState"
  }
}
```

Add `HeartbeatSeconds` (less than `TimeoutSeconds`) on any `.waitForTaskToken` Task so a dead worker is detectable before the full timeout fires.

---

## Pattern 3 — Retry Lambda transient exceptions explicitly

**Source**: [Best practices — Lambda service exceptions](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#bp-lambda-serviceexception)

```json
{
  "InvokeLambda": {
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
        "Next": "HandleFailure",
        "ResultPath": "$.error"
      }
    ],
    "Next": "ProcessResult"
  }
}
```

`JitterStrategy: FULL` (2023-09-07) spreads retry storms. `States.ALL` catcher must be **last** in the array.

---

## Pattern 4 — Offload payloads >256 KiB to S3; pass the ARN

**Source**: [Best practices — avoid execution failures](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#avoid-exec-failures)

`States.DataLimitExceeded` is a terminal error — it cannot be caught by `States.ALL`.

Lambda function that offloads its output:
```python
import boto3, json, uuid

s3 = boto3.client("s3")
BUCKET = "my-step-functions-payloads"

def handler(event, context):
    large_result = compute_large_result()  # >256 KiB
    key = f"results/{uuid.uuid4()}.json"
    s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(large_result))
    return {"bucket": BUCKET, "key": key}
```

Downstream Task reads from S3:
```json
{
  "ReadFromS3": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Parameters": {
      "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ProcessS3Payload",
      "Payload": {
        "bucket.$": "$.bucket",
        "key.$": "$.key"
      }
    },
    "TimeoutSeconds": 60,
    "Next": "Done"
  }
}
```

---

## Pattern 5 — Enable CloudWatch Logs with `/aws/vendedlogs/states/` prefix

**Source**: [Best practices — CloudWatch Logs](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#bp-cwl)

Express workflows have NO native history. CloudWatch Logs is mandatory for audit and debugging.

The `/aws/vendedlogs/` prefix avoids hitting the 5,120-char resource-policy limit and 10-policy-per-account cap.

CloudFormation / IaC logging config:
```json
{
  "LoggingConfiguration": {
    "Level": "ALL",
    "IncludeExecutionData": true,
    "Destinations": [
      {
        "CloudWatchLogsLogGroup": {
          "LogGroupArn": "arn:aws:logs:us-east-1:123456789012:log-group:/aws/vendedlogs/states/MyStateMachine:*"
        }
      }
    ]
  }
}
```

Set `Level` per environment:
- Non-prod: `ALL` (full trace; highest cost)
- Prod: `ERROR` or `FATAL` (cost-optimized)
- Standard workflows: Optional but recommended; Express: **mandatory**

---

## Pattern 6 — Scope execution IAM role to exact ARNs — no wildcards

**Source**: [Distributed Map permissions](https://docs.aws.amazon.com/step-functions/latest/dg/state-map-distributed.html#dist-map-permissions)

Minimal execution role for a Distributed Map state machine that calls Lambda and reads/writes S3:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeSpecificLambda",
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:MyProcessorFunction"
    },
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::my-step-functions-payloads",
        "arn:aws:s3:::my-step-functions-payloads/*"
      ]
    },
    {
      "Sid": "DistributedMapChildExec",
      "Effect": "Allow",
      "Action": ["states:StartExecution", "states:DescribeExecution", "states:StopExecution"],
      "Resource": [
        "arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine",
        "arn:aws:states:us-east-1:123456789012:execution:MyStateMachine:*"
      ]
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": ["logs:CreateLogDelivery", "logs:PutLogEvents", "logs:GetLogDelivery"],
      "Resource": "*"
    }
  ]
}
```

Validation: Run IAM Access Analyzer policy validation. Audit for `Resource: "*"` on any `states:*` or `lambda:*` action.

---

## Pattern 7 — Use Distributed Map or nested executions to stay under 25,000 events

**Source**: [Best practices — execution history limit](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html#bp-history-limit)

At 25,000 events the execution fails with `ExecutionFailed`. Distributed Map gives each iteration an isolated child execution history.

Distributed Map structure (Standard parent, Express children for idempotent item processing):
```json
{
  "ProcessMillionsOfRecords": {
    "Type": "Map",
    "ItemProcessor": {
      "ProcessorConfig": {
        "Mode": "DISTRIBUTED",
        "ExecutionType": "EXPRESS"
      },
      "StartAt": "ProcessItem",
      "States": {
        "ProcessItem": {
          "Type": "Task",
          "Resource": "arn:aws:states:::lambda:invoke",
          "Parameters": {
            "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ProcessRecord",
            "Payload.$": "$"
          },
          "TimeoutSeconds": 60,
          "End": true
        }
      }
    },
    "ItemReader": {
      "Resource": "arn:aws:states:::s3:getObject",
      "ReaderConfig": {
        "InputType": "CSV",
        "CSVHeaderLocation": "FIRST_ROW"
      },
      "Parameters": {
        "Bucket": "my-input-bucket",
        "Key": "data/input.csv"
      }
    },
    "ItemBatcher": {
      "MaxItemsPerBatch": 10
    },
    "MaxConcurrency": 1000,
    "ToleratedFailurePercentage": 5,
    "ResultWriter": {
      "Resource": "arn:aws:states:::s3:putObject",
      "Parameters": {
        "Bucket": "my-results-bucket",
        "Prefix": "results/"
      }
    },
    "Next": "Done"
  }
}
```

`ExecutionType: EXPRESS` for child workflows cuts cost on idempotent item processing. Set `ToleratedFailurePercentage` / `ToleratedFailureCount` to your acceptable partial-failure budget before deploying.
