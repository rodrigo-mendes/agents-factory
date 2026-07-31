# Always Do Patterns — AWS Lambda Serverless Architecture

**Tier**: Complex (security-critical, multi-service) | **Source**: Lambda Developer Guide, accessed 2026-07-31

---

## Pattern 1 — Initialize clients/connections outside the handler

**Pillar**: Performance Efficiency, Cost Optimization  
**Source**: [Best practices — Function code](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

The execution environment may be reused across invocations. Module-level initialization runs once per environment (not once per request).

```python
import boto3

# ✅ Module-level: runs once per execution environment, reused on warm invocations
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('OrdersTable')
secrets_client = boto3.client('secretsmanager')

def handler(event, context):
    # Per-request logic only — no SDK client creation here
    item = table.get_item(Key={'orderId': event['orderId']})
    return {'statusCode': 200, 'body': item.get('Item', {})}
```

**What to cache**: SDK clients, DB connection pools, parsed config, Lambda Layer assets from `/tmp`.  
**What NOT to cache**: Per-user/session data — cross-invocation state creates data-leak risk between tenants.  
**Verification**: CloudWatch `REPORT` line — warm invocations have no `Init Duration`.

---

## Pattern 2 — Least-privilege execution role

**Pillar**: Security  
**Source**: [Best practices — Function configuration](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

One IAM execution role per function. Scope `Action` and `Resource` to exact ARNs.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadOrdersOnly",
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:Query"],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/OrdersTable"
    },
    {
      "Sid": "WriteOrderMetrics",
      "Effect": "Allow",
      "Action": ["cloudwatch:PutMetricData"],
      "Resource": "*",
      "Condition": {"StringEquals": {"cloudwatch:namespace": "OrderService"}}
    }
  ]
}
```

**Verification**:
```bash
# Check for overly broad permissions
aws iam get-role-policy --role-name "$ROLE_NAME" --policy-name "$POLICY_NAME"
aws lambda get-policy --function-name "$FUNCTION_NAME"
# Detect findings: IAM Access Analyzer, Security Hub CSPM Lambda controls
```

---

## Pattern 3 — Idempotent handlers on at-least-once sources

**Pillar**: Reliability  
**Source**: [Best practices — Working with streams](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

SQS, Kinesis, and DynamoDB Streams event source mappings deliver **at least once**. Duplicates are guaranteed — handlers must be safe to replay.

```python
# Using Powertools for AWS Lambda — Idempotency utility (Python)
from aws_lambda_powertools.utilities.idempotency import (
    idempotent, DynamoDBPersistenceLayer, IdempotencyConfig
)

persistence_store = DynamoDBPersistenceLayer(table_name='IdempotencyTable')
config = IdempotencyConfig(event_key_jmespath='body.orderId')

@idempotent(persistence_store=persistence_store, config=config)
def handler(event, context):
    # Guaranteed to execute exactly once per unique orderId
    return process_order(event['body']['orderId'])
```

**Without Powertools** (manual DynamoDB conditional write):
```python
import boto3
from botocore.exceptions import ClientError

table = boto3.resource('dynamodb').Table('OrdersTable')

def handler(event, context):
    order_id = event['orderId']
    try:
        table.put_item(
            Item={'orderId': order_id, 'status': 'processed'},
            ConditionExpression='attribute_not_exists(orderId)'
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return {'result': 'already_processed'}
        raise
    return process_order(order_id)
```

**Verification**: Replay a duplicate event; assert exactly one side effect in the target system.

---

## Pattern 4 — Structured JSON logging + async EMF metrics

**Pillar**: Operational Excellence  
**Source**: [Best practices — Metrics and alarms](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

Use JSON-structured logs (CloudWatch Logs Insights) and Embedded Metric Format for custom metrics. EMF embeds metric data in log events — no synchronous `PutMetricData` API call in the hot path.

```python
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger(service="order-processor", level="INFO")
metrics = Metrics(namespace="OrderService", service="order-processor")
tracer = Tracer(service="order-processor")

@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
@metrics.log_metrics
def handler(event, context):
    order_id = event.get('orderId')
    logger.info("Processing order", order_id=order_id, source=event.get('source'))

    with tracer.capture_method("process_order"):
        result = process_order(order_id)

    metrics.add_metric(name="OrdersProcessed", unit=MetricUnit.Count, value=1)
    return result
```

**Verification**:
```bash
# Query structured logs
aws logs start-query \
  --log-group-name /aws/lambda/$FUNCTION_NAME \
  --start-time $(date -d '-1 hour' +%s) --end-time $(date +%s) \
  --query-string 'fields @timestamp, order_id, level | filter level = "INFO"'
```

---

## Pattern 5 — Secrets outside code + KMS-encrypted env vars

**Pillar**: Security  
**Source**: [Lambda security](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html) · [Best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

Never hardcode credentials. Retrieve secrets at runtime; cache in the execution environment. Encrypt env vars with a customer-managed KMS key.

```python
import boto3
import json

# ✅ Client initialized at module level; secret cached across warm invocations
_secrets_client = boto3.client('secretsmanager')
_cached_db_credentials = None

def get_db_credentials():
    global _cached_db_credentials
    if not _cached_db_credentials:
        resp = _secrets_client.get_secret_value(SecretId='prod/rds/credentials')
        _cached_db_credentials = json.loads(resp['SecretString'])
    return _cached_db_credentials

def handler(event, context):
    creds = get_db_credentials()
    # Use creds['username'], creds['password'] — never log these
```

**Env vars**: Pass non-secret operational config (e.g., `TABLE_NAME`, `REGION`) as env vars. Encrypt the entire function env var set with a customer-managed KMS key via Lambda console/API:
```bash
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --kms-key-arn "arn:aws:kms:us-east-1:123:key/mrk-..."
```

**Verification**: `aws lambda get-function-configuration --function-name "$FUNCTION_NAME"` — confirm `KMSKeyArn` is populated; confirm no secret-like values in `Environment.Variables`.

---

## Pattern 6 — Right-size memory and timeout (measure, don't guess)

**Pillar**: Performance Efficiency, Cost Optimization  
**Source**: [Best practices — Function configuration](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

Memory increase = proportional CPU increase. A faster function at higher memory can cost *less* in GB-seconds.

```bash
# Run AWS Lambda Power Tuning state machine
aws stepfunctions start-execution \
  --state-machine-arn "$POWER_TUNING_ARN" \
  --input '{
    "lambdaARN": "arn:aws:lambda:us-east-1:123:function:OrderProcessor",
    "powerValues": [128, 256, 512, 1024, 1536, 2048, 3008],
    "num": 50,
    "payload": {"orderId": "test-123"},
    "strategy": "cost"
  }'

# Read Max Memory Used from REPORT lines
aws logs filter-log-events \
  --log-group-name /aws/lambda/$FUNCTION_NAME \
  --filter-pattern "REPORT" \
  --query 'events[*].message' --output text \
  | grep -oP 'Max Memory Used: \d+ MB'
```

**Decision rule**: Set memory at the cost-latency optimum from Power Tuning. Set timeout to 2× p99 observed duration from CloudWatch (never guess a round number).

---

## Pattern 7 — Async error handling: DLQ/destinations + partial batch response

**Pillar**: Reliability  
**Source**: [Best practices — Working with streams](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html) · [Best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

**Async invocations** (S3, SNS, EventBridge): configure on-failure destination or DLQ to capture failed invocation records.

```bash
# Configure on-failure destination (richer than bare DLQ — includes request/response context)
aws lambda put-function-event-invoke-config \
  --function-name "$FUNCTION_NAME" \
  --destination-config '{"OnFailure":{"Destination":"arn:aws:sqs:us-east-1:123:failed-events-dlq"}}'
```

**Stream/queue event source mappings**: enable partial batch response so only failed records are retried, not the entire batch.

```python
def handler(event, context):
    batch_item_failures = []
    for record in event['Records']:
        try:
            process_record(record)
        except Exception as e:
            # ✅ Report only the failed message — rest of batch succeeds
            batch_item_failures.append({'itemIdentifier': record['messageId']})
    return {'batchItemFailures': batch_item_failures}
```

Or with Powertools Batch:
```python
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor, EventType, process_partial_response
)

processor = BatchProcessor(event_type=EventType.SQS)

def record_handler(record):
    return process_order(record.json_body['orderId'])

def handler(event, context):
    return process_partial_response(event, record_handler, processor, context)
```

**Verification**: Inject a failing record; confirm only it lands in the DLQ / is retried.

---

## Pattern 8 — Versions + aliases for safe deploy and rollback

**Pillar**: Operational Excellence  
**Source**: [Lambda runtimes — use after deprecation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) · [Best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

Publish immutable versions; use aliases to point traffic. Rollback = repoint alias, not code rollback.

```bash
# 1. Publish a new immutable version
NEW_VERSION=$(aws lambda publish-version \
  --function-name "$FUNCTION_NAME" \
  --query 'Version' --output text)

# 2. Canary: route 10% to new version, 90% to stable
aws lambda update-alias \
  --function-name "$FUNCTION_NAME" \
  --name production \
  --function-version "$NEW_VERSION" \
  --routing-config "AdditionalVersionWeights={\"$PREV_VERSION\":0.9}"

# 3. Full cutover after validation
aws lambda update-alias \
  --function-name "$FUNCTION_NAME" \
  --name production \
  --function-version "$NEW_VERSION"

# 4. Instant rollback
aws lambda update-alias \
  --function-name "$FUNCTION_NAME" \
  --name production \
  --function-version "$PREV_VERSION"
```

**Integration**: Use AWS CodeDeploy with a Lambda deployment group for automated canary/linear shifts with pre/post traffic hooks.

---

## Pattern 9 — Stay on a supported runtime; own the upgrade cadence

**Pillar**: Security, Operational Excellence  
**Source**: [Lambda runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)

Deprecated runtimes stop receiving security patches and eventually block `CreateFunction`/`UpdateFunctionConfiguration`.

```bash
# Identify deprecated runtimes across all functions
DEPRECATED_RUNTIMES="python3.10 python3.11 nodejs16.x java11 java17 ruby3.2 provided.al2 go1.x dotnet6 nodejs14.x python3.8 python3.9"

for rt in $DEPRECATED_RUNTIMES; do
  FUNCS=$(aws lambda list-functions \
    --query "Functions[?Runtime=='$rt'].FunctionName" \
    --output text)
  [ -n "$FUNCS" ] && echo "DEPRECATED $rt: $FUNCS"
done

# Migrate to supported runtime
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --runtime python3.13
```

**Proactive monitoring**: Enable AWS Trusted Advisor check "AWS Lambda Functions Using Deprecated Runtimes". Subscribe to AWS Health Dashboard events (180-day advance notice before deprecation enforcement).

---

## Pattern 10 — Guard against recursive invocation loops

**Pillar**: Reliability, Cost Optimization  
**Source**: [Best practices — Function code](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

A function that writes to its own trigger source creates a recursive loop causing unbounded invocations and cost escalation. Lambda has built-in recursive-loop detection for SQS and SNS but does not cover all trigger types.

```bash
# Emergency throttle — set reserved concurrency to 0 to halt immediately
aws lambda put-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --reserved-concurrent-executions 0
# Remove the concurrency cap after the loop is resolved:
aws lambda delete-function-concurrency --function-name "$FUNCTION_NAME"

# Set a CloudWatch alarm to detect invocation spikes
aws cloudwatch put-metric-alarm \
  --alarm-name "${FUNCTION_NAME}-invocation-spike" \
  --metric-name Invocations \
  --namespace AWS/Lambda \
  --dimensions Name=FunctionName,Value="$FUNCTION_NAME" \
  --statistic Sum --period 60 \
  --threshold 10000 --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions "$SNS_ALERT_ARN"
```

**Architectural check**: During design, verify that the function's write targets are not also its event sources. Never invoke `lambda.invoke` where the invoked function could write back to the same SQS queue, S3 bucket, or SNS topic that triggered the caller.
