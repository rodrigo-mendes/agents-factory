# Elimination Tree: Steps 0-1, Branches A and B

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Source ids (S1, K1 ...) resolve in the [source bibliography](./source-bibliography.md). Every command is on the [read-only allowlist](./read-only-allowlist.md). Tags map to the [register](./unverified-and-risks.md#tag-to-register-mapping).

## Contents

- [Step 0 control plane](#step-0-control-plane)
- [Step 1 classify](#step-1-classify)
- [Branch A API Gateway entry](#branch-a-api-gateway-entry)
- [Branch B invocation errors](#branch-b-invocation-errors)

## Step 0 control plane

```bash
# Representative, adapt to your environment (AWS docs 2026-10-28, CLI 2.39.0). Read-only.
aws lambda get-function-configuration --function-name my-function:prod \
  --query '{State:State,Reason:StateReasonCode,Upd:LastUpdateStatus,UpdReason:LastUpdateStatusReasonCode,Ver:Version,Timeout:Timeout,Mem:MemorySize,SnapStart:SnapStart,Vpc:VpcConfig,Kms:KMSKeyArn,Log:LoggingConfig,Trace:TracingConfig}'
# Expected healthy: State=Active, LastUpdateStatus=Successful   (S29, S30, S42)
```

Not `Active` or not `Successful`: go to [branch G](./tree-f-h-queues-state-events.md#branch-g-control-plane-state).

## Step 1 classify

| Evidence | Class | Go to |
|---|---|---|
| Invoke API status 4xx or 5xx (for example 429 `TooManyRequestsException`, 502 `KMS*`, `ENI*`, `EC2*`, 409 `SnapStartNotReadyException`) (S5) | invocation error | branch B |
| Invoke API status 200 plus `X-Amz-Function-Error` header (CLI JSON key `FunctionError`) (S2, S5) | function error | branch C |
| Metric `Throttles` above 0 (S8) | invocation error class | branch B |
| Metric `Errors` above 0; `Errors` excludes throttles (S8) | function error class | branch C |
| API Gateway `$context.integration.integrationStatus` is not 200 (S23, S53) | Lambda service refused or failed the invoke | branch B |
| `integrationStatus` is 200 and the client status is 502 (S23, S53) | function error or malformed proxy response | branch C and A4 |

The value set of `X-Amz-Function-Error` is not listed on the Invoke page (unverified); test only for presence.

## Branch A API Gateway entry

REST or HTTP API with a Lambda proxy integration. Read the access-log variables first ([format](./logs-insights-and-fields.md#api-gateway-access-log-format)).

| Client sees | Meaning and next read | Source |
|---|---|---|
| A1 429 | API Gateway's own throttle or usage-plan quota (`THROTTLED`, `QUOTA_EXCEEDED`), not Lambda. Account default 10,000 RPS, burst 5,000 (2,500 and 1,250 in some Regions) | S17, S24 |
| A2 403 | `MISSING_AUTHENTICATION_TOKEN` (wrong method, path or stage), `ACCESS_DENIED`, WAF | S24 |
| A3 500 | Lambda rejected the invoke: go to branch B. Also `API_CONFIGURATION_ERROR` (500) for invalid API configuration | S16, S24 |
| A4 502 | The function ran: function error (branch C) or a response not in the proxy format | S16, S21 |
| A5 504 | Integration timeout (REST gateway response `INTEGRATION_TIMEOUT`); compare Lambda `Duration` with the configured `Timeout` | S24 |
| A6 200 but wrong data | Confirm the executed version ([pattern 4](./always-do-patterns.md#4-confirm-the-executed-version)) | S2, S5 |

A3 evidence:
- HTTP API: `$context.integrationErrorMessage` shows the missing invoke permission; add it to the log format if absent; if the logs lack an error message add `$context.error.message` and `$context.error.responseType` (S13).
- REST execution log string "Execution failed due to configuration error: Invalid permissions on Lambda function" is known only from a Knowledge Center search snippet (unverified); decide by status plus `integrationStatus`.
- A SnapStart version still `Pending` can give a 500 in API Gateway (S31).

A4 evidence:
- REST and HTTP 1.0 proxy response shape: `isBase64Encoded`, `statusCode`, `headers`, `multiValueHeaders`, `body` (S21, S22).
- HTTP API format 2.0: valid JSON without `statusCode` is inferred as 200 `application/json` (S22).
- The REST log string "Malformed Lambda proxy response" is known only from the Knowledge Center (unverified); decide by status 502 plus `integrationStatus` 200.

A5 timeouts:
- REST integration timeout 50 ms to 29 s, raisable for Regional and private APIs at a cost in throttle quota; HTTP API maximum 30 s, not raisable (S14, S15).
- HTTP API timeout status code: not stated on any page read (unverified); read `$context.error.responseType` in the HTTP API access log (S13, S23).
- Long work should not sit behind a synchronous API; hand that to the architecture owner.
- A 503 for the API Gateway plus Lambda path is not documented on any page read (unverified).

## Branch B invocation errors

Evidence sources: Invoke API status, `StateReasonCode`, API Gateway `integrationStatus` (S1, S5, S29, S30).

| Branch | Error | Cause and evidence | Source |
|---|---|---|---|
| B1 | 429 `TooManyRequestsException` (`retryAfterSeconds`) | Concurrency: `ConcurrentInvocationLimitExceeded` (account) or `ReservedFunctionConcurrentInvocationLimitExceeded` (function). Default account 1,000; RPS limit 10 times concurrency; scaling 1,000 environments per 10 s per function; at least 100 unreserved always kept. Read `Throttles` (Sum), `ConcurrentExecutions` (Max), `ClaimedAccountConcurrency`, `get-account-settings`. One function using all concurrency is a reserved-concurrency question for the owner | S1, S5, S8, S26, S54 |
| B2 | 502 `KMSAccessDeniedException`, `KMSDisabledException`, `KMSInvalidStateException`, `KMSNotFoundException` | "Lambda couldn't decrypt the environment variables"; `StateReasonCode` `KMSKeyAccessDenied`, `DisabledKMSKey` and the like. `KMSDisabledException` means key disabled or grant revoked. The default `aws/lambda` key needs no KMS permissions; a customer managed key uses a grant Lambda creates | S1, S5, S30, S33 |
| B3 | 502 `ENILimitReachedException`, `SubnetIPAddressLimitReachedException`, `EC2ThrottledException`, `EC2AccessDeniedException`, `ENINotReadyException`, `InvalidSubnetIDException`, `InvalidSecurityGroupIDException` | VPC attach problems; ENI quota 3,000 per VPC | S3, S5, S54 |
| B4 | 409 `ResourceConflictException`; 502 `ResourceNotReadyException` | "currently in the following state: Pending" (VPC create); "function is inactive and its VPC connection is no longer available" | S1, S5 |
| B5 | SnapStart: 409 `SnapStartNotReadyException`, 408 `SnapStartTimeoutException`, 400 `SnapStartException`, 409 `SnapStartRegenerationFailureException` | Version `Inactive` after 14 days idle or recycled: wait for `Active`. 408: restore plus `afterRestore` exceeded 10 s (network or credential issues). 400: error in the `afterRestore` hook. The Quarkus guide says "Restoration is limited to 2 seconds"; cite both, do not choose (unverified) | S5, S6, S31, https://quarkus.io/version/3.40/guides/aws-lambda-snapstart |
| B6 | 413 `RequestTooLargeException` (6 MB sync, 1 MB async); 400 `RecursiveInvocationException`; 502 `InvalidRuntimeException`, `InvalidZipFileException`; 500 `ServiceException` | Payload, recursion, package problems | S5, S54 |
| B7 | "is not authorized to perform: lambda:InvokeFunction" | The caller's identity side lacks permission, not the function's policy | S1 |

SnapStart 408 fixture (AWS wording, S31): `"cause": "Lambda couldn't restore the snapshot within the timeout limit. (Service: Lambda, Status Code: 408, ...)"`, `"error": "Lambda.SnapStartTimeoutException"`.
