# Integration Patterns — AWS Step Functions

Cross-service integration examples. All sources accessed 2026-07-31.

---

## Step Functions ↔ Lambda

**Pattern**: Task state with `arn:aws:states:::lambda:invoke`, explicit retriers, and timeout.

**IAM requirement**: `lambda:InvokeFunction` on the specific function ARN.

**Complete Task state**:
```json
{
  "InvokeLambdaTask": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke",
    "Parameters": {
      "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:MyFunction:$LATEST",
      "Payload.$": "$"
    },
    "ResultSelector": {
      "body.$": "$.Payload.body",
      "statusCode.$": "$.Payload.statusCode"
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

**Common issues**:
- `Lambda.Unknown` — unhandled exception inside the function; inspect Lambda CloudWatch logs
- `Lambda.ClientExecutionTimeoutException` — Lambda cold start + execution exceeded `TimeoutSeconds`; increase timeout or optimize function

---

## Step Functions ↔ S3 (Distributed Map + large-payload offload)

**Pattern A — Distributed Map reading S3 input**:

```json
{
  "ProcessS3Data": {
    "Type": "Map",
    "ItemProcessor": {
      "ProcessorConfig": {
        "Mode": "DISTRIBUTED",
        "ExecutionType": "EXPRESS"
      },
      "StartAt": "ProcessBatch",
      "States": {
        "ProcessBatch": {
          "Type": "Task",
          "Resource": "arn:aws:states:::lambda:invoke",
          "Parameters": {
            "FunctionName": "arn:aws:lambda:us-east-1:123456789012:function:ProcessBatch",
            "Payload.$": "$"
          },
          "TimeoutSeconds": 300,
          "End": true
        }
      }
    },
    "ItemReader": {
      "Resource": "arn:aws:states:::s3:getObject",
      "ReaderConfig": {
        "InputType": "JSON",
        "MaxItems": 100000
      },
      "Parameters": {
        "Bucket.$": "$.inputBucket",
        "Key.$": "$.inputKey"
      }
    },
    "ItemBatcher": {
      "MaxItemsPerBatch": 25
    },
    "MaxConcurrency": 500,
    "ToleratedFailurePercentage": 10,
    "ResultWriter": {
      "Resource": "arn:aws:states:::s3:putObject",
      "Parameters": {
        "Bucket.$": "$.resultsBucket",
        "Prefix": "results/"
      }
    },
    "End": true
  }
}
```

**IAM requirements for Distributed Map**:
- `s3:GetObject` / `s3:ListBucket` on input bucket
- `s3:PutObject` on results bucket
- `states:StartExecution` + `states:DescribeExecution` on the child state machine + its executions

**Pattern B — Large-payload offload via S3 ARN**:

Lambda writes large output to S3 and returns only the reference:
```python
import boto3, json, uuid

s3 = boto3.client("s3")

def handler(event, context):
    large_data = generate_large_report(event)
    key = f"payloads/{uuid.uuid4()}.json"
    s3.put_object(
        Bucket="my-step-functions-payloads",
        Key=key,
        Body=json.dumps(large_data),
        ServerSideEncryption="aws:kms"
    )
    return {"bucket": "my-step-functions-payloads", "key": key}
```

State reads from S3 ARN reference — never exceeds 256 KiB.

---

## Step Functions ↔ CloudWatch Logs

**Pattern**: Log group with `/aws/vendedlogs/states/` prefix, scoped log levels.

**CloudFormation resource** (SAM / CFN):
```yaml
MyStateMachineLogGroup:
  Type: AWS::Logs::LogGroup
  Properties:
    LogGroupName: /aws/vendedlogs/states/MyStateMachine
    RetentionInDays: 30

MyStateMachine:
  Type: AWS::StepFunctions::StateMachine
  Properties:
    StateMachineType: EXPRESS  # or STANDARD
    LoggingConfiguration:
      Level: ALL  # ALL | ERROR | FATAL | OFF
      IncludeExecutionData: true
      Destinations:
        - CloudWatchLogsLogGroup:
            LogGroupArn: !GetAtt MyStateMachineLogGroup.Arn
```

**Log level guidelines**:
| Environment | Level | Rationale |
|---|---|---|
| Development | `ALL` | Full trace; highest ingestion cost |
| Staging | `ERROR` | Errors + failures only |
| Production (Standard) | `ERROR` | Supplementary; native history is primary |
| Production (Express) | `ERROR` | CloudWatch is the only history source |

**Common issues**:
- Log group not prefixed with `/aws/vendedlogs/` → hits 5,120-char resource-policy limit; rename the log group
- `IncludeExecutionData: false` on Express → no input/output in logs; set to `true` if debugging is needed

---

## Step Functions ↔ KMS (customer-managed key encryption)

**Source**: [KMS CMK announcement (2024-06-25)](https://aws.amazon.com/about-aws/whats-new/2024/07/aws-step-functions-customer-managed-keys/)

**What it encrypts**: Workflow definition, execution data, logs, and activity inputs/outputs.

**When to apply**: Confirm against your compliance scope before treating as mandatory — see research file Assumptions section.

```json
{
  "EncryptionConfiguration": {
    "KmsKeyId": "arn:aws:kms:us-east-1:123456789012:key/mrk-1234abcd12ab34cd56ef1234567890ab",
    "KmsDataKeyReusePeriodSeconds": 300,
    "Type": "CUSTOMER_MANAGED_KMS_KEY"
  }
}
```

**Required KMS key policy** (execution role must be a key user):
```json
{
  "Effect": "Allow",
  "Principal": {
    "Service": "states.us-east-1.amazonaws.com"
  },
  "Action": ["kms:GenerateDataKey", "kms:Decrypt"],
  "Resource": "*"
}
```

---

## Step Functions ↔ SQS/SNS (`.waitForTaskToken` callback)

**Pattern**: Human-in-the-loop or async external callback.

**State definition**:
```json
{
  "WaitForHumanApproval": {
    "Type": "Task",
    "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
    "Parameters": {
      "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/ApprovalQueue",
      "MessageBody": {
        "taskToken.$": "$$.Task.Token",
        "requestId.$": "$.requestId",
        "approvalUrl.$": "States.Format('https://approvals.example.com/?token={}', $$.Task.Token)"
      }
    },
    "TimeoutSeconds": 86400,
    "HeartbeatSeconds": 3600,
    "ResultPath": "$.approvalResult",
    "Next": "ProcessApproval"
  }
}
```

**Approver calls back** (SDK or API Gateway backed Lambda):
```python
import boto3

sfn = boto3.client("stepfunctions")

def approve(task_token: str, approved: bool):
    if approved:
        sfn.send_task_success(
            taskToken=task_token,
            output='{"approved": true}'
        )
    else:
        sfn.send_task_failure(
            taskToken=task_token,
            error="ApprovalRejected",
            cause="Reviewer declined"
        )
```

**IAM requirement**: Execution role needs `sqs:SendMessage` on the specific queue ARN. Approver Lambda needs `states:SendTaskSuccess` + `states:SendTaskFailure` (no resource restriction needed — token is the auth).

**Common issues**:
- Heartbeat timeout fires before callback → worker must send heartbeat via `send_task_heartbeat` at least every `HeartbeatSeconds`
- Token lost → Standard execution remains open for `TimeoutSeconds`; implement token store (DynamoDB) keyed on `requestId`
