# Pre-Flight and Plan

Back to [SKILL.md](../SKILL.md). Representative commands, none executed by the research. Read-only unless marked M.

## Contents

- [Artifact size check](#artifact-size-check)
- [Configuration checks](#configuration-checks)
- [Record the rollback target](#record-the-rollback-target)
- [Plan and approval gate](#plan-and-approval-gate)

## Artifact size check

The artifact (for example `target/function.zip`) comes from the build; this skill does not build it. Limits: 50 MB zipped for direct upload, 250 MB unzipped including layers and custom runtimes, 5 layers, S3 bucket in the same Region as the function ([quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html), [.zip deployment](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html), [update-function-code](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html)).

```bash
ZIP=target/function.zip
test -f "$ZIP" || { echo "artifact missing"; exit 1; }
ZIPPED=$(wc -c < "$ZIP")
UNZIPPED=$(unzip -l "$ZIP" | tail -1 | awk '{print $1}')   # excludes layers: add layer sizes yourself
[ "$ZIPPED"   -le $((50*1024*1024))  ] || echo "WARN: over 50 MB zipped -> upload via S3 (same Region)"
[ "$UNZIPPED" -le $((250*1024*1024)) ] || echo "FAIL: over 250 MB unzipped incl. layers -> not deployable as .zip"
```

- Whether the `unzip -l` total equals Lambda's accounting is (medium confidence), register M1.
- Code storage quota: 300 GB unzipped per Region, not increasable; each function version and layer version consumes it ([quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)). Check the headroom before a large release.
- With S3 code storage mode `REFERENCE` the object must stay; deleting it or revoking bucket permissions makes the function `Inactive` ([function states](https://docs.aws.amazon.com/lambda/latest/dg/functions-states.html)).

## Configuration checks

| Check | Rule | Source |
|---|---|---|
| Timeout and memory | timeout up to 900 s, memory 128 to 10,240 MB for Event Functions | https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html |
| Environment variables | 4 KB aggregate; keys start with a letter, at least 2 characters, letters, digits, underscore, not reserved | https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html |
| Logging permissions | execution role can write to CloudWatch Logs (`AWSLambdaBasicExecutionRole`) | https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs.html |
| Secrets | role has `secretsmanager:GetSecretValue` (and `kms:Decrypt` for a customer managed key) where used | https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html ; https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars-encryption.html |
| Handler and runtime | match the artifact; the build skill owns the values (for Quarkus: `developing-quarkus-amazon-lambda-v3-40`) | page not recorded |

Secret-looking environment variable keys (read-only):

```bash
aws lambda get-function-configuration --function-name my-function --query 'Environment.Variables' --output json \
  | jq -r 'keys[]' | grep -Ei 'secret|password|passwd|token|api[_-]?key|private' && echo "REVIEW: secret-like key in env vars"
```

The key-name heuristic is an internal check (medium confidence), register M3. `STRIPE_SECRET_ARN` matches it and is allowed: the variable holds the secret ARN, not the value; a human reviews each hit.

## Record the rollback target

```bash
PREV=$(aws lambda get-alias --function-name my-function --name live --query FunctionVersion --output text)
echo "PREV=$PREV"     # keep it in the deploy report; needed by rollback
```

The `get-alias` page was not fetched (medium confidence), register M5. If no alias exists yet (first deploy), there is no `PREV`; the research documents no rollback for that case, so ask the user.

## Plan and approval gate

```bash
terraform fmt -check && terraform validate          # repo rule aws-terraform-code-standards (package aws-terraform)
terraform plan -input=false -out=tfplan             # Expected: only intended changes to function, version, alias
```

1. Show the plan to the user. Highlight any destroy or replace of the function, alias or permissions, and any change to reserved concurrency (see [C6](./ask-first-decisions.md#c6-reserved-concurrency)).
2. Wait for the line `approval: apply plan=<planfile> sha256=<hash> by=<user> at=<UTC> relayed-by=<orchestrator>`. Silence, a previous approval or the existence of the plan file is not approval. A regenerated plan voids the line.
3. Re-check the sha256 of the plan file (`sha256sum tfplan`) against the line, then apply only `tfplan` (see [apply blueprint](./apply-waiters-publish-alias.md)). On a mismatch stop with `needs-input`.

Why: the repo rules `aws-lambda-deployment-preflight` and `aws-terraform-skills-management` require a reviewed plan file and forbid `-auto-approve`; an unreviewed apply can replace or destroy production resources. This is repo policy, not an AWS fact.

If the plan shows more than the intended release change, stop and ask. Terraform HCL (arguments for `publish`, alias, `snap_start`, `source_code_hash`) is owned by `provisioning-aws-lambda-v6`; this skill does not restate it.
