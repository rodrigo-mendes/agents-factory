# Migration Notes

Back to [SKILL.md](../SKILL.md). AWS docs have no versioned changelog for the deploy procedure. "Changes" below are differences an older-memory procedure would get wrong; each is sourced to the current page (2026-10-28).

## Easy-to-miss differences

- The v2 waiters (`function-active-v2`, `function-updated-v2`) poll `GetFunction` every 1 s and give up after 300 checks; the v1 waiters poll `GetFunctionConfiguration` every 5 s and give up after 60 ([CLI wait index](https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/index.html)). Prefer v2; use `published-version-active` after publishing.
- Standard Lambda functions are now called "Event Functions"; the docs separately describe Lambda Web Functions, Lambda MicroVMs and Lambda Managed Instances ([quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)). Use 900 s timeout and 128 to 10,240 MB memory for Event Functions. A 32768 MB figure in CLI output patterns belongs to Managed Instances (medium confidence), register M8.
- The qualifier `$LATEST.PUBLISHED` appears in CLI patterns; it belongs to Lambda Managed Instances and is out of scope (the version-publishing page was seen only as a search snippet, coverage limit L2).
- S3 code storage mode `COPY` or `REFERENCE`; with `REFERENCE`, losing the object makes the function `Inactive` ([.zip deployment](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html), [function states](https://docs.aws.amazon.com/lambda/latest/dg/functions-states.html)).
- `State` values include `Deactivating`, `Deactivated`, `ActiveNonInvocable` and `Deleting` in addition to the four in the guide ([get-function-configuration](https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function-configuration.html)).
- No dedicated rollback page exists (coverage limit L3); rollback is documented through weighted alias routing and runtime rollback.

## Upgrade steps: from "deploy to `$LATEST`" to this procedure

1. Enable version publishing and create an alias in the Terraform module (`provisioning-aws-lambda-v6`; its `publish` argument defaults to false).
2. Repoint triggers, API Gateway integrations and resource-based permissions to the alias ARN ([using aliases](https://docs.aws.amazon.com/lambda/latest/dg/using-aliases.html), [stage variables](https://docs.aws.amazon.com/apigateway/latest/developerguide/amazon-api-gateway-using-stage-variables.html)).
3. Add post-apply verification: `wait function-updated-v2`, `wait published-version-active`, alias smoke test.
4. Record the previous version number before each apply.

## Compatibility

| Dependency | Min | Notes |
|---|---|---|
| AWS CLI | v2 (2.39.0 reference read) | `--cli-binary-format raw-in-base64-out` for inline payloads per the docs' examples |
| Terraform provider | `hashicorp/aws` 6.x | HCL in `provisioning-aws-lambda-v6` |
| SnapStart runtimes | Java 11+, Python 3.12+, .NET 8+ | not OS-only runtimes, so not Quarkus native |
| Java managed runtimes (family fact) | `java17.al2023`, `java21`, `java25` | `java17` (AL2) deprecates 2027-06-30 |
