# Smoke Test and Verification Loop

Back to [SKILL.md](../SKILL.md). Representative commands, none executed by the research.

## Contents

- [Smoke test](#smoke-test)
- [Log tail](#log-tail)
- [Verification Loop](#verification-loop)

## Smoke test

A smoke test executes function code, so the real invoke is step kind X and needs `approval: smoke payload=<file or sha256> by=<user> at=<UTC> relayed-by=<orchestrator>` before it runs; `DryRun` is read-only. Use a payload without side effects (medium confidence, internal recommendation), register M10. `--invocation-type DryRun` validates parameters and permission without running the function and returns 204 ([CLI invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)).

```bash
aws lambda invoke --function-name my-function --qualifier live --invocation-type DryRun /dev/null   # expect StatusCode 204
aws lambda invoke --function-name my-function --qualifier live \
  --cli-binary-format raw-in-base64-out --payload file://smoke-event.json \
  --log-type Tail out.json > meta.json
jq -e '.StatusCode==200 and (has("FunctionError")|not)' meta.json   # pass/fail gate
jq -r '.ExecutedVersion' meta.json                                  # must equal the version just published
```

- `StatusCode` is 200 for `RequestResponse`, 202 for `Event`, 204 for `DryRun`; `FunctionError` is present when the function errored, so a 200 can still carry a function error ([CLI invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)).
- With an alias, `ExecutedVersion` "indicates which version the alias resolved to". Synchronous responses carry `x-amz-executed-version`; logs carry `START RequestId: ... Version: N` ([weighted aliases](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html)). During a weighted canary, repeat the invoke until both versions have answered.
- Inline JSON payloads need `--cli-binary-format raw-in-base64-out` with CLI v2, as the docs' examples show ([CLI invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)).
- Never smoke-test unqualified or on `$LATEST`: that tests the unreleased copy, not the alias callers use ([versions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html)).
- The `jq` gate is an internal recommendation (medium confidence), register M2. `jq` is not a deployer precondition: the same check without it is `python3 -c "import json,sys; m=json.load(open('meta.json')); sys.exit(0 if m.get('StatusCode')==200 and 'FunctionError' not in m else 1)"`; the contract is the documented fields (`StatusCode`, `FunctionError`, `ExecutedVersion`).
- API Gateway REST: request the stage invoke URL plus resource path and assert status and body; a missing permission for the alias or version yields 500 ([stage variables](https://docs.aws.amazon.com/apigateway/latest/developerguide/amazon-api-gateway-using-stage-variables.html)). The invoke URL host format `https://<api-id>.execute-api.<region>.amazonaws.com/<stage>/<path>` is (medium confidence), register M7. HTTP API behaviour is (unverified), register U2.

## Log tail

`LogResult` is base64, 4 KB, `--log-type Tail`, synchronous invocations only.

```bash
jq -r '.LogResult' meta.json | base64 --decode     # START / END / REPORT lines; macOS: base64 -D
```

Whether the 4 KB are the first or the last 4 KB is (unverified): the Lambda guide says "first 4 KB", the CLI reference says "last 4 KB" (irresolvable, register I2). Do not grep the tail for a specific line and treat its absence as proof. For full output read CloudWatch Logs `/aws/lambda/<function-name>`, which may take 5 to 10 minutes to appear; Live Tail has no 4 KB limit ([CloudWatch logs](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html), [viewing logs](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-view.html)).

## Verification Loop

Run after every apply, in order. Stop at the first failing line.

```bash
terraform fmt -check && terraform validate                       # before the plan
terraform plan -input=false -out=tfplan                          # Expected: only intended changes
# line "approval: apply plan=tfplan sha256=<hash> ..." relayed by the orchestrator, sha256 re-checked -> terraform apply -input=false tfplan
aws lambda wait function-updated-v2 --function-name my-function          # rc 0; rc 255 after 300 failed checks (medium confidence, L1)
aws lambda wait published-version-active --function-name my-function --qualifier <N>   # rc 0; rc 255 after 312 (medium confidence, L1)
aws lambda get-function-configuration --function-name my-function:<N> \
  --query '{State:State,Upd:LastUpdateStatus,Sha:CodeSha256,Snap:SnapStart.OptimizationStatus}'
aws lambda invoke --function-name my-function --qualifier live --invocation-type DryRun /dev/null   # 204
# real invoke below only with the "approval: smoke payload=..." line
aws lambda invoke --function-name my-function --qualifier live --cli-binary-format raw-in-base64-out \
  --payload file://smoke-event.json --log-type Tail out.json > meta.json
jq -e '.StatusCode==200 and (has("FunctionError")|not) and .ExecutedVersion=="<N>"' meta.json
```

| Result | Action |
|---|---|
| Waiter rc 255 (medium confidence, L1) or `LastUpdateStatus=Failed` | Stop; do not publish or shift; hand over to `debugging-aws-lambda` |
| `Snap` is not `On` for a SnapStart function | Do not shift traffic; read the version `State` and `LastUpdateStatusReason` |
| `FunctionError` present or wrong `ExecutedVersion` | Rollback ([rollback](./rollback-and-cleanup.md)) only with the `approval: rollback` line |
| All pass | Report the version number, `CodeSha256` and `PREV` |
