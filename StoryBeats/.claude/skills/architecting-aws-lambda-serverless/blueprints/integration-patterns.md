# Integration Patterns — AWS Lambda Serverless Architecture

**Source**: Lambda Developer Guide · Serverless Applications Lens, accessed 2026-07-31

---

## Lambda ↔ API Gateway

**Pattern**: Synchronous HTTP front door with throttling, auth, and WAF integration.  
**Services**: Amazon API Gateway (REST or HTTP API) + AWS WAF + Amazon CloudFront (optional edge caching).  
**Compatibility**: API Gateway and Lambda are fully managed — no version pinning required.

**Architecture**:
```
Client → CloudFront (optional) → API Gateway + WAF → Lambda (arm64) → DynamoDB / Secrets Manager
```

**Configuration (SAM / CloudFormation)**:
```yaml
# SAM template snippet — HTTP API + Lambda with arm64
OrderProcessor:
  Type: AWS::Serverless::Function
  Properties:
    Runtime: python3.13
    Architectures: [arm64]
    MemorySize: 512          # Set from Power Tuning result
    Timeout: 29              # < API Gateway 29 s integration timeout
    AutoPublishAlias: production
    DeploymentPreference:
      Type: Canary10Percent5Minutes
    Events:
      ApiEvent:
        Type: HttpApi
        Properties:
          ApiId: !Ref OrderApi
          Path: /orders/{orderId}
          Method: GET
```

**Latency SLO path**:
- Spiky traffic with supported runtime → enable SnapStart on the alias
- Sustained low-latency → Provisioned Concurrency + Application Auto Scaling on the alias

**Key gotchas**:
- API Gateway integration timeout: **29 seconds** (REST) / **30 seconds** (HTTP API) — set function timeout below this.
- Default API Gateway throttle: 10,000 requests/second burst, 5,000 steady-state. Align Lambda reserved concurrency to avoid mismatch.
- For public APIs: always attach AWS WAF to the API Gateway stage or CloudFront distribution.

**Source**: [Best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

---

## Lambda ↔ SQS (Queue-based Load Leveling)

**Pattern**: SQS buffers bursty producers; Lambda event source mapping drains the queue with bounded concurrency.  
**Services**: Amazon SQS (standard or FIFO) + Lambda event source mapping.

**Configuration**:
```bash
# Create queue with correct visibility timeout (>= 6× function timeout)
FUNCTION_TIMEOUT=30  # seconds — set from actual measurement
VISIBILITY=$(( FUNCTION_TIMEOUT * 6 ))  # = 180 s

aws sqs create-queue \
  --queue-name orders-queue \
  --attributes "{
    \"VisibilityTimeout\": \"$VISIBILITY\",
    \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"
  }"

# Create event source mapping with partial batch response
aws lambda create-event-source-mapping \
  --function-name OrderProcessor \
  --event-source-arn "$QUEUE_ARN" \
  --batch-size 10 \
  --function-response-types ReportBatchItemFailures \
  --scaling-config '{"MaximumConcurrency": 50}'
```

**Handler with partial batch response**:
```python
def handler(event, context):
    batch_item_failures = []
    for record in event['Records']:
        try:
            body = json.loads(record['body'])
            process_order(body['orderId'])
        except Exception:
            batch_item_failures.append({'itemIdentifier': record['messageId']})
    return {'batchItemFailures': batch_item_failures}
```

**Scaling**: Reserved concurrency on the Lambda function limits the drain rate — use this to protect downstream resources (RDS, third-party APIs).

**FIFO queues**: Use for strict ordering (per message group ID); lower throughput than standard queues. Prefer Kinesis for high-throughput ordered streams.

**Source**: [Best practices — Working with streams](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

---

## Lambda ↔ DynamoDB Streams (Stream Processing)

**Pattern**: Capture item-level changes from DynamoDB and process them with Lambda; partial batch response prevents a single poison record from blocking the shard.  
**Services**: Amazon DynamoDB (Streams enabled) + Lambda event source mapping.

**Configuration**:
```bash
# Enable DynamoDB Streams on the table
aws dynamodb update-table \
  --table-name OrdersTable \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES

# Create event source mapping with partial batch response
aws lambda create-event-source-mapping \
  --function-name OrderStreamProcessor \
  --event-source-arn "$STREAM_ARN" \
  --starting-position LATEST \
  --batch-size 100 \
  --bisect-batch-on-function-error \
  --function-response-types ReportBatchItemFailures \
  --destination-config '{"OnFailure":{"Destination":"'$DLQ_ARN'"}}'
```

**Idempotent stream handler**:
```python
import boto3

table = boto3.resource('dynamodb').Table('ProcessedRecords')

def handler(event, context):
    batch_item_failures = []
    for record in event['Records']:
        sequence_number = record['dynamodb']['SequenceNumber']
        try:
            # Idempotency key = stream sequence number
            table.put_item(
                Item={'sequenceNumber': sequence_number, 'processed': True},
                ConditionExpression='attribute_not_exists(sequenceNumber)'
            )
            process_change(record['dynamodb'])
        except Exception as e:
            if 'ConditionalCheckFailedException' in str(type(e)):
                pass  # Already processed
            else:
                batch_item_failures.append({'itemIdentifier': sequence_number})
    return {'batchItemFailures': batch_item_failures}
```

**Scaling**: Throughput scales linearly with the number of DynamoDB shards (1 Lambda invocation per shard). Monitor `IteratorAge` — alarm if > 30,000 ms (stream falling behind).

**Source**: [Best practices — Working with streams](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

---

## Lambda ↔ Step Functions (Workflow Orchestration)

**Pattern**: Step Functions coordinates Lambda tasks with built-in retries, catch/compensation, and execution history — avoids hand-coded orchestration in Lambda.  
**Services**: AWS Step Functions (Express or Standard workflows) + Lambda task states.

**When to use**: Multi-step workflows, sagas (compensating transactions), human-in-the-loop, long-running processes that exceed Lambda's 15-minute timeout.

**State machine snippet (Standard Workflow)**:
```json
{
  "Comment": "Order processing saga",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:ValidateOrder",
      "Retry": [{"ErrorEquals": ["Lambda.ServiceException"], "IntervalSeconds": 2, "MaxAttempts": 3, "BackoffRate": 2}],
      "Catch": [{"ErrorEquals": ["ValidationError"], "Next": "RejectOrder"}],
      "Next": "ChargePayment"
    },
    "ChargePayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:ChargePayment",
      "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "RefundAndCancel"}],
      "Next": "FulfillOrder"
    },
    "FulfillOrder": {"Type": "Task", "Resource": "arn:aws:lambda:us-east-1:123:function:FulfillOrder", "End": true},
    "RejectOrder":  {"Type": "Fail", "Cause": "Validation failed"},
    "RefundAndCancel": {"Type": "Task", "Resource": "arn:aws:lambda:us-east-1:123:function:RefundOrder", "End": true}
  }
}
```

**Cost note**: Standard Workflows charge per state transition. Express Workflows charge by duration+invocations — better for high-volume, short-duration flows.

**Source**: [Serverless Lens — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (⚠️ 2022-07)

---

## Lambda ↔ EventBridge (Event-Driven Fan-out)

**Pattern**: One event published to EventBridge triggers multiple Lambda subscribers independently; each scales and fails independently.  
**Services**: Amazon EventBridge (event bus) + Lambda targets + EventBridge Schema Registry.

**Architecture**:
```
Producer Lambda → EventBridge event bus → Rule (filter) → Lambda A
                                        → Rule (filter) → Lambda B
                                        → Rule (filter) → SQS queue → Lambda C
```

**Producer (Lambda emitting an event)**:
```python
import boto3, json
from datetime import datetime, timezone

events_client = boto3.client('events')

def emit_order_placed(order_id: str, customer_id: str):
    events_client.put_events(Entries=[{
        'Source': 'com.mycompany.orders',
        'DetailType': 'OrderPlaced',
        'Detail': json.dumps({
            'orderId': order_id,
            'customerId': customer_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }),
        'EventBusName': 'OrdersEventBus'
    }])
```

**EventBridge rule targeting Lambda**:
```bash
# Create rule filtering on DetailType
aws events put-rule \
  --name "OnOrderPlaced" \
  --event-bus-name "OrdersEventBus" \
  --event-pattern '{"source":["com.mycompany.orders"],"detail-type":["OrderPlaced"]}'

# Add Lambda as target
aws events put-targets \
  --rule "OnOrderPlaced" \
  --event-bus-name "OrdersEventBus" \
  --targets '[{"Id":"SendConfirmationEmail","Arn":"arn:aws:lambda:us-east-1:123:function:SendEmail"}]'
```

**Reliability**: EventBridge delivers at least once — Lambda consumers must be idempotent. Configure a DLQ on the Lambda target for failed deliveries.

**Schema Registry**: Use EventBridge Schema Registry to version and govern event contracts across producers and consumers.

**Source**: [Serverless Lens — Event-driven architectures](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/event-driven-architectures.html) (⚠️ 2022-07) · [Best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
