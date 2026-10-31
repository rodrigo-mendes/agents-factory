# Never-Do Anti-Patterns — applying-aws-serverless-well-architected-lens

Source: AWS Well-Architected Framework — Serverless Applications Lens, content dated 2022-07-14 (accessed 2026-08-27).

> ⚠️ Source dated 2022-07; verify currency.

Each anti-pattern pairs a ❌ Wrong / ✅ Correct example using exact AWS service names.

---

## ND-1 — Shared IAM role across multiple Lambda functions

**Risk**: HIGH — violates least privilege (SEC 2); over-broad roles "open up your systems for abuse"; lateral privilege escalation, compliance violation.

- ❌ **Wrong**: One `lambda-exec-role` with `dynamodb:*` on `*` attached to 12 different Lambda functions.
- ✅ **Correct**: `order-writer-role` granting only `dynamodb:PutItem` on `arn:aws:dynamodb:...:table/Orders`, attached to the single `order-writer` function.

**Detection**: Enumerate execution roles and flag any role attached to more than one function; run IAM Access Analyzer.
```bash
aws lambda list-functions --query 'Functions[*].Role' \
  --output text | tr '\t' '\n' | sort | uniq -d
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html (2022-07-14)

---

## ND-2 — API Gateway API keys as the authorization gate

**Risk**: HIGH — "API Gateway API Keys is not a security mechanism"; keys only track usage. Unauthorized access / data exfiltration.

- ❌ **Wrong**: API Gateway method with `apiKeyRequired: true` and no authorizer, treating the key as the security gate.
- ✅ **Correct**: Method with `authorizationType: COGNITO_USER_POOLS` (or `AWS_IAM` / Lambda authorizer / mTLS); API keys used only in usage plans for throttling.

**Detection**: List methods whose only control is `x-api-key`.
```bash
aws apigateway get-resources --rest-api-id <API_ID> \
  --query 'items[*].resourceMethods' --output json
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/identity-and-access-management.html (2022-07-14)

---

## ND-3 — Chaining Lambda functions via `lambda.invoke` in code

**Risk**: MEDIUM — produces "a monolithic and tightly coupled application"; hidden failures, harder retries and observability.

- ❌ **Wrong**: `functionA` calls `lambda.invoke(functionB)` which calls `functionC`, embedding retry/rollback logic in code.
- ✅ **Correct**: AWS Step Functions Standard state machine orchestrating A → B → C with built-in retries, catch, and a saga compensation branch feeding an SQS DLQ.

**Detection**: Search function code for `Invoke` / `invoke` calls forming chains.

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/general-design-principles.html (2022-07-14)

---

## ND-4 — Async processing without DLQ or with unchecked partial failures

**Risk**: HIGH — silent data loss; stuck Kinesis / DynamoDB Streams shards. `PutRecords` / `BatchWriteItem` return success even if only one record succeeds.

- ❌ **Wrong**: Async Lambda consumer with no on-failure destination; code assumes `dynamodb.BatchWriteItem` fully succeeded.
- ✅ **Correct**: Lambda with `Destination on Failure` → Amazon SQS DLQ; `MaximumRetryAttempts`, `MaximumRecordAge` and `BisectBatchOnFunctionError` set; code inspects `UnprocessedItems` from `BatchWriteItem` and `FailedRecordCount` from `PutRecords`.

**Detection**: Functions lacking a DLQ / on-failure destination; code review for unchecked batch responses.
```bash
aws lambda get-function-event-invoke-config --function-name <FUNCTION_NAME>
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html (2022-07-14)

---

## ND-5 — Sensitive data in URLs/logs or unencrypted in storage

**Risk**: CRITICAL — URL paths/query strings can leak into CloudWatch Logs unencrypted; data breach / compliance violation.

- ❌ **Wrong**: `GET /users?ssn=123-45-6789` with API Gateway access logging enabled, and an S3 bucket without encryption at rest.
- ✅ **Correct**: SSN sent in an encrypted POST body; S3 / DynamoDB encryption at rest via AWS KMS; secrets in AWS Secrets Manager with rotation; API Gateway logging enabled only after compliance review.

**Detection**: Scan access logs / stdout for PII; confirm KMS encryption at rest on all stores.
```bash
aws dynamodb describe-table --table-name <TABLE_NAME> --query 'Table.SSEDescription'
aws s3api get-bucket-encryption --bucket <BUCKET_NAME>
```

**Source**: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/data-protection.html (2022-07-14)
