# Elimination Tree: Branches C, D and E

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). Source ids resolve in the [source bibliography](./source-bibliography.md). Every command is on the [read-only allowlist](./read-only-allowlist.md). Tags map to the [register](./unverified-and-risks.md#tag-to-register-mapping).

## Contents

- [Branch C function errors](#branch-c-function-errors)
- [Branch D cold start and latency](#branch-d-cold-start-and-latency)
- [Branch E VPC and network](#branch-e-vpc-and-network)

## Branch C function errors

Evidence: REPORT `Status` and `Error Type`, the function log, the `X-Amz-Function-Error` header (S2, S6). Formats: [platform log formats](./platform-log-formats.md).

| Branch | Symptom | Evidence and reading | Source |
|---|---|---|---|
| C1 | Timeout | "Task timed out after N seconds" or REPORT `Status: timeout`; `Duration` close to the configured `Timeout`. Causes to check: downstream slowness, large payloads, VPC egress (branch E). Maximum timeout 900 s; the console default is 3 s | S2, S3, S6, S35, S54 |
| C2 | Init failure | `INIT_REPORT ... Phase: init Status: timeout` or `error`; `Sandbox.Timedout`. Init limit 10 s on-demand, retried at the first invocation with the function timeout ("suppressed init"); 15 minutes for provisioned concurrency and SnapStart. `StateReasonCode` `FunctionError.InitTimeout`, `FunctionError.RuntimeInitError`, `FunctionError.InitResourceExhausted` | S1, S6, S30 |
| C3 | Crash | REPORT `Status: error Error Type: Runtime.ExitError`, or the old-style line "Runtime exited without providing a reason". Count crashes with `filter @message like /Process exited/` (S11). The string "Runtime exited with error: signal: killed" for out-of-memory is not on any page read (unverified); do not quote it | S6, S11 |
| C4 | Memory | `Max Memory Used` equal to `Memory Size` (query `@maxMemoryUsed=@memorySize`); a leak shows as growth across warm invocations; large payloads; "the execution environment stops the function". Units of `@maxMemoryUsed`: pages disagree (unverified). CPU grows with memory; one vCPU "At 1.8 GB" (S35) versus at 1,769 MB (S54), pages differ (unverified) | S2, S11, S35, S54 |
| C5 | Handler or class | Java strings "Class not found: function.Handler" and "No public method named handleRequest with appropriate method signature found on class function.Handler" mean the handler setting does not match the code. Quarkus handler must be `io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest`. `Couldn't find valid bootstrap(s)` (`Runtime.InvalidEntrypoint`) for a `provided.al2023` zip. The `Runtime.ImportModuleError` token is not on the pages read; the page shows "Unable to import module 'function'" (unverified) | S1, S4, In1 |
| C6 | Payload or JSON | Malformed input, URL-encoded S3 keys, Java `null` from `Records` or `eventSourceARN` casing | S2, S44 |
| C7 | `AccessDenied` in an SDK call | Execution role problem: check with `simulate-principal-policy`; client-side decrypt of environment variables needs `kms:Decrypt` on the role. That an SDK `AccessDeniedException` surfaces as a function error in the function log is an inference (medium confidence) | S33, S38, S61 |
| C8 | Java slower after 11 to 17 or later | `JAVA_TOOL_OPTIONS=-XX:-TieredCompilation` reverts the compiler behaviour; a change for the code owner, not for the debugger | S2 |

OOM method (no string needed): REPORT `Max Memory Used` equal to `Memory Size`, plus `Status: error Error Type: Runtime.ExitError` (S6, S11). `Runtime.OutOfMemory` belongs to Web Functions and is not searched for (S62).

## Branch D cold start and latency

| Branch | Check | Source |
|---|---|---|
| D1 | Cold-start percentage: REPORT lines containing "Init Duration" ([query](./logs-insights-and-fields.md#aws-sample-queries)). `Init Duration` present means a new execution environment | S11 |
| D2 | SnapStart: the cold-start duration is `Restore Duration` plus `Duration`; `Init Duration` moves to `INIT_REPORT` ([query](./logs-insights-and-fields.md#aws-sample-queries)) | S32 |
| D3 | Provisioned concurrency configured but cold starts: check the invoked qualifier is the alias, not `$LATEST`; read `ProvisionedConcurrencySpilloverInvocations`; 10 RPS per provisioned concurrency | S1, S8 |
| D4 | Expected size: cold starts typically occur in under 1% of invocations, from under 100 ms to over 1 second | S6 |

`Duration` excludes the cold start (S8); a larger REPORT `Duration` than the START-to-REPORT wall time indicates a suppressed init after an earlier failure (S6).

## Branch E VPC and network

| Branch | Symptom and check | Source |
|---|---|---|
| E1 | Timeouts or `ETIMEDOUT` after attaching a VPC: no NAT route from a private subnet. "Connecting a function to a public subnet doesn't give it internet access" | S3, S46 |
| E2 | AWS services unreachable without internet: VPC endpoints | S3 |
| E3 | Intermittent TCP or UDP with network ACLs: allow ports 1024-65535 both ways | S3 |
| E4 | `UnknownHostException`: DNS, at most 20 concurrent TCP DNS connections, not increasable. SnapStart on Java 11: DNS negative cache (`AWS_LAMBDA_JAVA_NETWORKADDRESS_CACHE_NEGATIVE_TTL=0`), not needed on Java 17 and later | S3, S31 |

Read `VpcConfig` from [step 0](./tree-a-b-entry-and-invocation.md#step-0-control-plane); route tables and NAT are outside the allowlist, so ask the owner for them or hand the question over as a work-order.
