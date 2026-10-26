# Always-Do Patterns — applying-aws-serverless-well-architected-lens

Source: AWS Well-Architected Framework — Serverless Applications Lens, content dated 2022-07-14 (accessed 2026-08-27).

> ⚠️ Source dated 2022-07; verify currency. The "2026" on the PDF is a copyright stamp, not a content revision.

---

## AD-1 — One least-privilege IAM role per Lambda function

**Pillar alignment**: Security (SEC 2 — security boundaries)
**Why**: "Sharing an IAM role within more than one Lambda function will likely violate least-privileged access."

**Architecture decision**: Give each function a dedicated execution role granting only the specific actions and resources it needs; use tag-based access control for API-level granularity.

**Verification**:
```bash
aws lambda list-functions --query 'Functions[*].Role' \
  --output text | tr '\t' '\n' | sort | uniq -d
# Expected: no output (no role shared by two functions)
```
Also review per-function policies with IAM Access Analyzer for over-broad grants.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html (2022-07-14)

---

## AD-2 — Enforce a real API authorization mechanism (never API keys alone)

**Pillar alignment**: Security (SEC 1 — control access to your serverless API)
**Why**: "API Gateway API Keys is not a security mechanism and should not be used for authorization unless it's a public API."

**Architecture decision** — choose by caller type:

| Caller | Mechanism |
|---|---|
| AWS-internal callers | `AWS_IAM` |
| End users / social IdP | Amazon Cognito user pools |
| Custom or external IdP | Lambda authorizer (can be shared cross-account) |
| Restrict by account / IP / VPC endpoint | Resource policies (+ private endpoints, VPC endpoint policies) |
| IoT / app-to-app | Mutual TLS |

Layer AWS WAF managed rule groups (SQLi/XSS) in front of the API.

**Verification**: Inspect each method's `authorizationType`; confirm a WAF WebACL is associated; confirm API keys are not the sole gate.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html (2022-07-14)

---

## AD-3 — Orchestrate with Step Functions, not chained Lambda code

**Pillar alignment**: Operational Excellence / Reliability (general design principle)
**Why**: Chaining Lambda executions in code "results in a monolithic and tightly coupled application. Instead, use a state machine to orchestrate transactions and communication flows."

**Architecture decision**: Move retry, back-off, try/catch and saga rollback out of function code into a Step Functions state machine — Express for short high-volume, Standard for durable long-running audited workflows (see [ask-first-decisions.md](./ask-first-decisions.md), Decision 2).

**Verification**: Review whether functions invoke other functions directly vs. Step Functions definitions; check for saga/DLQ steps.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html, https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html (2022-07-14)

---

## AD-4 — Idempotent operations + DLQ on every async function

**Pillar alignment**: Reliability (failure management; principle "Design for failures and duplicates")
**Why**: "Operations triggered from requests or events must be idempotent, as failures can occur and a given request or event can be delivered more than once." Failed async transactions should be captured and retried, otherwise data loss can occur.

**Architecture decision**:
- Use idempotency keys / DynamoDB conditional writes so retried events do not double-process.
- Async functions: `Destination on Failure` → Amazon SQS DLQ.
- Kinesis / DynamoDB Streams: set `MaximumRetryAttempts`, `MaximumRecordAge`, `BisectBatchOnFunctionError` to isolate poison pills.
- Inspect partial failures: `UnprocessedItems` (`BatchWriteItem`) and `FailedRecordCount` (`PutRecords`) — these calls return success even if only some records succeed.

**Verification**:
```bash
aws lambda get-function-event-invoke-config --function-name <FUNCTION_NAME>
aws lambda list-event-source-mappings \
  --query 'EventSourceMappings[*].[FunctionArn,DestinationConfig,BisectBatchOnFunctionError]'
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html, https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html (2022-07-14)

---

## AD-5 — Structured JSON logging with correlation IDs

**Pillar alignment**: Operational Excellence (Operate — centralized logging)
**Why**: "Unstructured logging using `print` or `console.log` statements is unfavorable." Structured JSON fields are auto-discovered by CloudWatch Logs Insights.

**Architecture decision**: Emit JSON with timestamp, level, service, function name, request ID, `cold_start` flag and correlation ID; propagate correlation ID and log level downstream; sample DEBUG logs at scale; adopt Powertools for AWS Lambda (the lens calls it "Lambda Powertools").

**Verification**: Query in CloudWatch Logs Insights; confirm correlation IDs are present across services.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-logging.html (2022-07-14)

---

## AD-6 — AWS X-Ray active tracing on all functions

**Pillar alignment**: Operational Excellence (Operate — distributed tracing)
**Why**: "Active tracing with AWS X-Ray should be enabled to provide distributed tracing capabilities as well as to enable visual service maps for faster troubleshooting."

**Architecture decision**: `TracingConfig=Active`; subsegments for external dependencies; annotations (indexed key-value pairs) for business transactions; tune socket read/write timeouts to fail fast.

**Verification**:
```bash
aws lambda list-functions --query 'Functions[*].[FunctionName,TracingConfig.Mode]' --output table
# Expected: Mode = Active for every function
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-distributed-tracing.html (2022-07-14)

---

## AD-7 — Four-tier CloudWatch metrics with tiered alarms

**Pillar alignment**: Operational Excellence (OPS 1 — understand application health)
**Tiers**: Business · Customer experience · System · Operational; alarms at individual and aggregate level.

| Service | Metrics to alarm on |
|---|---|
| Lambda | `Duration`, `Errors`, `Throttles`, `ConcurrentExecutions`, `DeadLetterErrors`, `ProvisionedConcurrencySpilloverInvocations` |
| Kinesis / DynamoDB Streams | `IteratorAge` |
| API Gateway | `IntegrationLatency`, `Latency`, `5XXError` |
| SQS | `ApproximateAgeOfOldestMessage` |
| DynamoDB | throttle metrics |
| Step Functions | `ExecutionsFailed`, `ExecutionThrottled` |
| EventBridge | `FailedInvocations`, `ThrottledRules` |

Use CloudWatch Embedded Metric Format (EMF) for asynchronous custom metrics when Powertools is unavailable for the runtime.

**Verification**: Compare the CloudWatch alarm inventory against this list for every service in use.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/opex-metrics-and-alerts.html (2022-07-14)

---

## AD-8 — Protect sensitive data; validate all input

**Pillar alignment**: Security (SEC 3 — data protection / application security)
**Why**: URL paths/query strings can leak into CloudWatch Logs; "We strictly advise against sending, logging, and storing unencrypted sensitive data."

**Architecture decision**: Encrypt sensitive payloads before processing/logging; KMS encryption at rest on DynamoDB, S3, OpenSearch; API Gateway JSON-schema request validation plus deep app-level validation; secrets in AWS Secrets Manager with rotation and audited access; sign Lambda code with AWS Signer.

**Verification**:
```bash
aws dynamodb describe-table --table-name <TABLE_NAME> --query 'Table.SSEDescription'
aws s3api get-bucket-encryption --bucket <BUCKET_NAME>
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/data-protection.html (2022-07-14)
