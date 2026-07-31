# Never Do Patterns — AWS Lambda Serverless Architecture

**Tier**: Complex | **Source**: Lambda Developer Guide, accessed 2026-07-31

Each entry shows the ❌ wrong pattern, ✅ correct alternative, detection guidance, and blast radius.

---

## AP-1 — Hardcoded secrets or plaintext env vars

**Risk**: CRITICAL | **Pillar**: Security  
**Source**: [Lambda security](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html)

```python
# ❌ WRONG — credentials in code or plaintext environment variables
DB_PASSWORD = "P@ssw0rd"   # readable in source control and Lambda console

import os
password = os.environ['DB_PASSWORD']   # readable via GetFunctionConfiguration — no encryption
```

```python
# ✅ CORRECT — retrieve from Secrets Manager at runtime; cache in execution environment
import boto3, json

_secrets_client = boto3.client('secretsmanager')
_cached_creds = None

def get_db_credentials():
    global _cached_creds
    if not _cached_creds:
        resp = _secrets_client.get_secret_value(SecretId='prod/rds/credentials')
        _cached_creds = json.loads(resp['SecretString'])
    return _cached_creds

# Env vars encrypted with a customer-managed KMS key:
# aws lambda update-function-configuration \
#   --function-name "$FUNCTION_NAME" \
#   --kms-key-arn "arn:aws:kms:us-east-1:123:key/mrk-..."
```

**Detection**: Security Hub CSPM Lambda controls; `aws lambda get-function-configuration` — check `Environment.Variables` for secret-like names; git secret scanning (truffleHog, gitleaks).  
**Blast radius**: Credential leak → account/data compromise, compliance violation.

---

## AP-2 — Wildcard execution-role permissions in production

**Risk**: CRITICAL | **Pillar**: Security  
**Source**: [Best practices — Function configuration](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

```json
// ❌ WRONG — full account access from a single function
{
  "Statement": [{
    "Effect": "Allow",
    "Action": "*",
    "Resource": "*"
  }]
}
```

```json
// ✅ CORRECT — scoped to exact operations and ARNs
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadOrdersOnly",
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:Query"],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/OrdersTable"
    }
  ]
}
```

**Detection**: IAM Access Analyzer; Security Hub CSPM; `aws iam simulate-principal-policy` to verify effective permissions.  
**Blast radius**: Compromised function can act across the entire account — privilege escalation, data exfiltration.

---

## AP-3 — Non-idempotent handler on an at-least-once source

**Risk**: HIGH | **Pillar**: Reliability  
**Source**: [Best practices — Working with streams](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

```python
# ❌ WRONG — SQS-triggered insert with no deduplication
def handler(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        # A redelivered message creates a duplicate order row
        db.execute("INSERT INTO orders VALUES (?)", (body['orderId'],))
```

```python
# ✅ CORRECT — conditional write that is safe to replay
import boto3
from botocore.exceptions import ClientError

table = boto3.resource('dynamodb').Table('OrdersTable')

def handler(event, context):
    batch_item_failures = []
    for record in event['Records']:
        body = json.loads(record['body'])
        try:
            table.put_item(
                Item={'orderId': body['orderId'], 'status': 'processed'},
                ConditionExpression='attribute_not_exists(orderId)'
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                continue   # Already processed — safe to skip
            batch_item_failures.append({'itemIdentifier': record['messageId']})
    return {'batchItemFailures': batch_item_failures}
```

**Detection**: Replay a message; assert exactly one side effect (one DB row, one email sent).  
**Blast radius**: Duplicate side effects — double charges, double inserts, duplicate emails, financial errors.

---

## AP-4 — Orchestrating workflows by chaining Lambda invocations in code

**Risk**: HIGH | **Pillar**: Operational Excellence, Reliability  
**Source**: [Serverless Lens — Design principles](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html) (⚠️ 2022-07)

```python
# ❌ WRONG — hand-coded Lambda chain (tightly-coupled monolith)
import boto3

lambda_client = boto3.client('lambda')

def handler(event, context):
    # A invokes B synchronously; B invokes C; no retry visibility; cascades on failure
    resp = lambda_client.invoke(
        FunctionName='validate-order',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    result = json.loads(resp['Payload'].read())
    lambda_client.invoke(
        FunctionName='charge-payment',
        InvocationType='RequestResponse',
        Payload=json.dumps(result)
    )
```

```yaml
# ✅ CORRECT — AWS Step Functions state machine (built-in retries, catch, execution history)
States:
  ValidateOrder:
    Type: Task
    Resource: arn:aws:lambda:us-east-1:123:function:validate-order
    Retry:
      - ErrorEquals: [Lambda.ServiceException]
        IntervalSeconds: 2
        MaxAttempts: 3
    Catch:
      - ErrorEquals: [States.ALL]
        Next: HandleFailure
    Next: ChargePayment
  ChargePayment:
    Type: Task
    Resource: arn:aws:lambda:us-east-1:123:function:charge-payment
    End: true
  HandleFailure:
    Type: Fail
    Cause: "Order processing failed"
```

**Detection**: Search codebase for `lambda.invoke(` calls that pass results to subsequent invocations; architecture review for tightly-coupled function chains.  
**Blast radius**: Cascading failure, no observability, no retry/compensation, tightly-coupled monolith hidden behind a serverless facade.

---

## AP-5 — Running on a deprecated runtime

**Risk**: HIGH | **Pillar**: Security  
**Source**: [Lambda runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)

```bash
# ❌ WRONG — creating or leaving functions on deprecated runtimes
aws lambda create-function \
  --runtime python3.10 \   # AL2-based, deprecated — AL2 EOL June 30, 2026
  ...
```

```bash
# ✅ CORRECT — use a supported AL2023-based runtime
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --runtime python3.13   # Supported AL2023-based runtime

# Detection command — list all functions on deprecated runtimes
DEPRECATED="python3.10 python3.11 nodejs16.x java11 java17 ruby3.2 provided.al2 go1.x dotnet6"
for rt in $DEPRECATED; do
  FUNCS=$(aws lambda list-functions \
    --query "Functions[?Runtime=='$rt'].FunctionName" --output text)
  [ -n "$FUNCS" ] && echo "DEPRECATED $rt: $FUNCS"
done
```

**AL2 deprecation timeline**: Amazon Linux 2 EOL was June 30, 2026. `provided.al2` deprecated July 31, 2026. AL2-based managed runtimes (`java11`, `java17`, `python3.10`, `python3.11`, `ruby3.2`) on deprecation path.

**Detection**: AWS Trusted Advisor "Functions Using Deprecated Runtimes"; AWS Health Dashboard.  
**Blast radius**: Unpatched CVEs; eventually blocked from `CreateFunction` and `UpdateFunctionConfiguration`.

---

## AP-6 — Async invocations with no DLQ or on-failure destination

**Risk**: HIGH | **Pillar**: Reliability  
**Source**: [Best practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

```bash
# ❌ WRONG — async function with no failure capture
# Default: Lambda retries failed async invocations twice, then silently drops the event
aws lambda create-function --function-name "$FUNCTION_NAME" ...
# No DestinationConfig, no DeadLetterConfig — failed events vanish
```

```bash
# ✅ CORRECT — configure on-failure destination (richer than bare DLQ: includes request+response)
aws lambda put-function-event-invoke-config \
  --function-name "$FUNCTION_NAME" \
  --destination-config \
    '{"OnFailure":{"Destination":"arn:aws:sqs:us-east-1:123:failed-events-dlq"}}'

# Verify:
aws lambda get-function-event-invoke-config --function-name "$FUNCTION_NAME"
# Expected: DestinationConfig.OnFailure.Destination populated
```

**Detection**: `aws lambda get-function-event-invoke-config` — check for empty `DestinationConfig` on async-triggered functions; alarm on `Errors` + `DeadLetterErrors` metrics.  
**Blast radius**: Silent event loss after 2 retries exhaust — data loss with no trace.

---

## AP-7 — SQS visibility timeout less than or equal to function timeout

**Risk**: MEDIUM | **Pillar**: Reliability  
**Source**: [Best practices — Function configuration](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

```bash
# ❌ WRONG — visibility timeout (30 s) shorter than function timeout (60 s)
# The message becomes visible again mid-execution → concurrent duplicate processing
aws sqs create-queue --queue-name orders-queue \
  --attributes '{"VisibilityTimeout":"30"}'
# Function timeout: 60 s → overlap guaranteed
```

```bash
# ✅ CORRECT — visibility timeout >= 6× function timeout (AWS guidance)
FUNCTION_TIMEOUT=60   # seconds
VISIBILITY_TIMEOUT=$((FUNCTION_TIMEOUT * 6))   # = 360 s

aws sqs set-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attributes "{\"VisibilityTimeout\":\"$VISIBILITY_TIMEOUT\"}"

# Verify alignment:
aws sqs get-queue-attributes --queue-url "$QUEUE_URL" \
  --attribute-names VisibilityTimeout
aws lambda get-function-configuration --function-name "$FUNCTION_NAME" --query 'Timeout'
```

**Detection**: Compare `VisibilityTimeout` vs `Timeout` across all SQS-triggered functions; alert if `VisibilityTimeout < Timeout * 6`.  
**Blast radius**: Duplicate concurrent processing of the same message — data duplication, wasted compute cost.

---

## AP-8 — Memory guessing without right-sizing

**Risk**: MEDIUM | **Pillar**: Cost Optimization, Performance Efficiency  
**Source**: [Best practices — Function configuration](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

```bash
# ❌ WRONG — all functions pinned at 128 MB (or arbitrary round number) without measurement
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --memory-size 128   # No measurement; may be 10× underpowered or 5× over-provisioned
```

```bash
# ✅ CORRECT — measure with Power Tuning; set at cost-latency optimum
# 1. Deploy the Power Tuning state machine (one-time setup)
# https://github.com/alexcasalboni/aws-lambda-power-tuning

# 2. Run it against the function
aws stepfunctions start-execution \
  --state-machine-arn "$POWER_TUNING_ARN" \
  --input '{
    "lambdaARN": "arn:aws:lambda:us-east-1:123:function:OrderProcessor",
    "powerValues": [128, 256, 512, 1024, 1536, 2048, 3008],
    "num": 50,
    "payload": {"orderId": "test-123"},
    "strategy": "cost"
  }'

# 3. Apply the recommended memory
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --memory-size 512   # Derived from Power Tuning result, not guessed
```

**Detection**: Compare `Max Memory Used` vs configured memory in CloudWatch `REPORT` lines. If `Max Memory Used` < 50% of configured memory, the function is over-provisioned. If near 100%, it's under-provisioned.  
**Blast radius**: Chronic cost overrun (too much memory) or latency degradation (too little CPU from too little memory).

---

## AP-9 — Mutable global user/session state in execution environment

**Risk**: MEDIUM | **Pillar**: Security, Reliability  
**Source**: [Best practices — Function code](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

```python
# ❌ WRONG — per-user data stored in a module-global dict
user_cache = {}   # module-level — persists across warm invocations

def handler(event, context):
    user_id = event['userId']
    user_cache[user_id] = fetch_user_profile(user_id)
    # On a warm invocation for a DIFFERENT user, stale data from a previous user remains
    # This creates a cross-user data leak
    return user_cache.get(user_id)
```

```python
# ✅ CORRECT — only immutable, non-sensitive shared assets in globals
import boto3

# ✅ Safe to cache: SDK clients, static config, Lambda layer assets
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('UserProfilesTable')

def handler(event, context):
    # ✅ Per-request state is local to the handler; never leaks
    user_id = event['userId']
    response = table.get_item(Key={'userId': user_id})
    return response.get('Item', {})
```

**Detection**: Code review for mutable global dicts/lists indexed by user ID, session token, or request ID.  
**Blast radius**: Cross-user data leakage — privacy violation; "share nothing" architecture principle violated.
