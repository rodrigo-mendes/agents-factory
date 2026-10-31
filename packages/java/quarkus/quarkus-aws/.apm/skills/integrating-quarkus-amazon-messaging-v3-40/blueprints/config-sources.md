# SSM and Secrets Manager Config Sources

Back to [SKILL.md](../SKILL.md). Quarkiverse amazon-services 3.23.0. Fetched 2026-10-28 (3.23.x pages and docs sources at tag 3.23.0). The runtime source at the tag was not inspected (L4). Both sources are part of `quarkus-amazon-ssm` and `quarkus-amazon-secretsmanager`; no separate artifact is needed ([SSM page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html), [Secrets Manager page](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-secretsmanager.html)).

## Contents

- [Configuration](#configuration)
- [Documented keys and defaults](#documented-keys-and-defaults)
- [Behaviour in Lambda](#behaviour-in-lambda)
- [Alternative: Parameters and Secrets Lambda Extension](#alternative-parameters-and-secrets-lambda-extension)
- [Security](#security)

## Configuration

```properties
# Quarkus 3.40 / amazon-services 3.23.0 - application.properties
# handler selection: lambda skill
quarkus.lambda.handler=orders-queue

# Secrets Manager config source (A10)
quarkus.secretsmanager.config.enabled=true
quarkus.secretsmanager.config.secrets."stripe.api-key"=prod/stripe/api-key

# SSM Parameter Store config source (Q1, Q2)
quarkus.ssm.config.enabled=true
quarkus.ssm.config.path=/myapp/prod/
quarkus.ssm.config.with-decryption=true
# choice per Q2; (medium confidence) for Lambda
quarkus.ssm.config.update-interval-minutes=0
```

## Documented keys and defaults

Defaults are stated per key; "default" means the documented default value.

| Key | Default | Notes | Source |
|---|---|---|---|
| `quarkus.ssm.config.enabled` | `false` | | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html |
| `quarkus.ssm.config.path` | no default | passed to `GetParametersByPathRequest` | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html |
| `quarkus.ssm.config.names` | no default | full parameter names, "Batched in groups of ten per AWS limit"; can be combined with `path` | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html |
| `quarkus.ssm.config.recursive` | `true` | | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html |
| `quarkus.ssm.config.with-decryption` | `true` | decrypts `SecureString` | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html |
| `quarkus.ssm.config.update-interval-minutes` | `5` | "Set to `0` to fetch only once at startup" | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-ssm.html |
| `quarkus.secretsmanager.config.enabled` | `false` | | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-secretsmanager.html |
| `quarkus.secretsmanager.config.secrets."<property>"` | no default listed | `Map<String,String>`, property to secret name | https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/amazon-secretsmanager.html |

- If both `path` and `names` are unset, "the config source is not registered" (SSM).
- SSM key mapping: "a leading `/` is removed and remaining `/` characters become `.`", so `/myapp/prod/url` becomes `myapp.prod.url`. JSON values are flattened to dotted keys. On reload failure "the previous snapshot (if any) is left in place".
- Secrets Manager JSON secrets are detected ("value starts with `{` or `[`") and flattened; with a mapping, the mapped property name becomes the prefix. Values are "loaded once at startup (the config source does not poll for updates)".
- Failed fetches (access denied, deletion, throttling) are logged and the other secrets still load (paraphrase by the tool, L2).
- Both sources use "the same ... client configuration as the rest of the extension", so the credentials and region rules of [A4](./always-do-patterns.md#a4-default-credentials-and-region) apply. Both are documented in the docs sources at tag 3.23.0 ([SSM adoc](https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/docs/modules/ROOT/pages/amazon-ssm.adoc), [Secrets Manager adoc](https://raw.githubusercontent.com/quarkiverse/quarkus-amazon-services/3.23.0/docs/modules/ROOT/pages/amazon-secretsmanager.adoc)).

## Behaviour in Lambda

- Config sources fetch at startup ("Quarkus will fetch secret values at startup"), which adds init latency per cold start. The size of that cost is (unverified) (U3): measure `Init Duration` in CloudWatch with and without the sources.
- Runtime behaviour of the SSM scheduled reload (`update-interval-minutes` above 0) in an execution environment that is frozen between invocations is (unverified) (I1): no page states it and the runtime source tree at the tag returned 404 (not inspected). Workaround: `update-interval-minutes=0`, or read at runtime ([Q1](./ask-first-decisions.md#q1-source-of-secrets-and-parameters) options B and C).
- Config-source values under SnapStart are captured in the snapshot at init; refresh after restore is not documented, so rotated values can stay stale for the life of the snapshot. This is (unverified) (I2): neither the Quarkus 3.40 SnapStart guide nor the Quarkiverse docs state it. Workaround: Q1 option C with a short TTL, or option B in the handler. SnapStart itself is the [lambda skill](../../developing-quarkus-amazon-lambda-v3-40/SKILL.md).

## Alternative: Parameters and Secrets Lambda Extension

The extension is "runtime-agnostic" and "works with any Lambda runtime": an HTTP call to `localhost:2773` with header `X-Aws-Parameters-Secrets-Token`; cache TTL default 300 s (range 0 to 300 s), cache size 1000, port 2773, max connections 3, timeouts default 0 (none). A Java sample exists on the AWS page ([AWS extension](https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html), [Parameter Store extension](https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html)).

- The token must come from the SDK credential provider chain inside the handler (N9).
- Set `PARAMETERS_SECRETS_EXTENSION_LOG_LEVEL=DEBUG` while setting up.
- In a VPC, Secrets Manager needs a VPC endpoint for the extension ([Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_lambda.html)).
- The Powertools parameters utility is `implementing-lambda-powertools-java` (mention only).

## Security

- Extension reads need `ssm:GetParameter` and `kms:Decrypt` for `SecureString`, and `secretsmanager:GetSecretValue` ([Parameter Store extension](https://docs.aws.amazon.com/systems-manager/latest/userguide/ps-integration-lambda-extensions.html), [AWS extension](https://docs.aws.amazon.com/lambda/latest/dg/with-secrets-manager.html)). Grant them in Terraform (`provisioning-aws-secrets-manager-v6`, `provisioning-aws-parameter-store-v6`).
- Use explicit secret mappings (A10) rather than "load all accessible secrets".
- Secrets never go in env vars or properties (family rule 5); AWS also recommends Secrets Manager over environment variables ([Lambda env vars](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)).
