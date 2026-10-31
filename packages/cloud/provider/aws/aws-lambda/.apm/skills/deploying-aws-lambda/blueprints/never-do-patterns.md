# Never-Do Patterns

Back to [SKILL.md](../SKILL.md). Each pattern pairs a wrong command with a correct one. Commands are representative, none executed by the research. Gate note: every mutating CLI command shown here (`update-function-code`, `publish-version`, `update-alias`, `update-function-configuration`, `delete-function`) only illustrates the shape; the deployer runs mutations only inside the approved apply (or with the `approval: rollback` line), and never runs `delete-function`.

## Contents

- [F1 Apply without a reviewed saved plan and relayed approval](#f1-apply-without-a-reviewed-saved-plan-and-relayed-approval)
- [F2 Acting while the update is in progress](#f2-acting-while-the-update-is-in-progress)
- [F3 `$LATEST` as a production target](#f3-latest-as-a-production-target)
- [F4 Partial environment update](#f4-partial-environment-update)
- [F5 Secrets as environment variable values](#f5-secrets-as-environment-variable-values)
- [F6 Deleting without a qualifier](#f6-deleting-without-a-qualifier)
- [F7 Direct upload over 50 MB](#f7-direct-upload-over-50-mb)
- [F8 Status 200 as the whole smoke test](#f8-status-200-as-the-whole-smoke-test)

## F1 Apply without a reviewed saved plan and relayed approval

Severity: high. Repo policy, rules `aws-lambda-deployment-preflight` and `aws-terraform-skills-management` (not an AWS fact): an unreviewed apply can replace or destroy production resources; the saved plan is what was reviewed.

```bash
# ❌ Wrong
terraform apply -auto-approve
# ✅ Correct
terraform plan -input=false -out=tfplan      # show to the user; wait for the relayed "approval: apply plan=... sha256=..." line
terraform apply -input=false tfplan
```

## F2 Acting while the update is in progress

Severity: high. `PublishVersion`, `UpdateFunction*` and `TagResource` fail during `InProgress`, and invocations still run the previous code, so a smoke test right after the update tests the old build ([function states](https://docs.aws.amazon.com/lambda/latest/dg/functions-states.html)).

```bash
# ❌ Wrong
aws lambda update-function-code --function-name my-function --s3-bucket b --s3-key k
aws lambda publish-version --function-name my-function     # may fail, or the smoke test runs old code
# ✅ Correct
aws lambda update-function-code --function-name my-function --s3-bucket b --s3-key k   # inside the approved apply only
aws lambda wait function-updated-v2 --function-name my-function
aws lambda publish-version --function-name my-function --code-sha256 "$SHA"   # inside the approved apply only
```

## F3 `$LATEST` as a production target

Severity: high. Every deploy overwrites `$LATEST`; an unqualified ARN invokes it; a weighted alias cannot include it; SnapStart and provisioned concurrency do not apply to it ([versions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html), [weighted aliases](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html), [SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html), [provisioned concurrency](https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html)).

```bash
# ❌ Wrong
aws lambda invoke --function-name my-function out.json
aws lambda update-alias --function-name my-function --name live --routing-config 'AdditionalVersionWeights={"$LATEST"=0.1}'
# ✅ Correct
aws lambda invoke --function-name my-function --qualifier live --cli-binary-format raw-in-base64-out --payload file://e.json out.json
aws lambda update-alias --function-name my-function --name live --function-version 7 --routing-config 'AdditionalVersionWeights={"8"=0.1}'   # inside the approved apply only
```

## F4 Partial environment update

Severity: high. "The entire contents of the Variables structure is replaced"; include all existing values in the new map; pass `--revision-id` from `get-function-configuration` to avoid lost updates ([env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)).

```bash
# ❌ Wrong
aws lambda update-function-configuration --function-name my-function --environment "Variables={NEW_KEY=v}"
# ✅ Correct (Terraform path: declare the full map in the module, see provisioning-aws-lambda-v6)
aws lambda get-function-configuration --function-name my-function     # read all Variables and RevisionId
aws lambda update-function-configuration --function-name my-function \
  --environment "Variables={EXISTING_A=a,EXISTING_B=b,NEW_KEY=v}" --revision-id <RevisionId>   # inside the approved apply only
```

## F5 Secrets as environment variable values

Severity: high. AWS recommends Secrets Manager instead of environment variables for credentials, API keys and tokens ([env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html), [encryption](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars-encryption.html)); family rule 5 requires Secrets Manager or SSM.

```text
❌ Environment.Variables = { STRIPE_API_KEY = "sk_live_..." }
✅ Environment.Variables = { STRIPE_SECRET_ARN = "arn:aws:secretsmanager:<region>:<acct>:secret:stripe" }
   runtime fetch: AWS Parameters and Secrets Lambda Extension (localhost:2773) or SDK; role has secretsmanager:GetSecretValue
```

## F6 Deleting without a qualifier

Severity: high. Without `Qualifier` all versions and aliases are deleted and a deleted function cannot be recovered; a version referenced by an alias cannot be deleted ([delete-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/delete-function.html)).

```bash
# ❌ Wrong (intended: remove version 3)
aws lambda delete-function --function-name my-function
# ✅ Correct (keep the current and PREV versions; return it as a proposal with outcome: needs-input, never run by the deployer)
aws lambda delete-function --function-name my-function --qualifier 3
```

## F7 Direct upload over 50 MB

Severity: moderate. Direct upload is limited to 50 MB zipped and the unzipped size to 250 MB including layers ([quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html), [.zip deployment](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html)).

```bash
# ❌ Wrong (80 MB zip)
aws lambda update-function-code --function-name my-function --zip-file fileb://function.zip
# ✅ Correct (bucket in the same Region as the function)
aws lambda update-function-code --function-name my-function --s3-bucket my-bucket --s3-key function.zip --s3-object-version <v>   # inside the approved apply only
```

## F8 Status 200 as the whole smoke test

Severity: high. `FunctionError` indicates an error during execution while the synchronous status code stays 200; with an alias, `ExecutedVersion` shows which version ran ([CLI invoke](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html), [weighted aliases](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html)).

```bash
# ❌ Wrong
aws lambda invoke ... > meta.json && echo PASS
# ✅ Correct
jq -e '.StatusCode==200 and (has("FunctionError")|not) and .ExecutedVersion=="8"' meta.json && echo PASS
```
