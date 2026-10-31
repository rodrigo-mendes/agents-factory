# Never-Do Patterns — provisioning-aws-parameter-store-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-23), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| `insecure_value` on a `SecureString` | [never-do-secrets](./never-do-secrets.md#1-insecure_value-on-a-securestring) |
| `value` for a `SecureString` expecting no plaintext in state | [never-do-secrets](./never-do-secrets.md#2-value-for-a-securestring-expecting-a-clean-state) |
| `aws_ssm_parameter` data source reading a `SecureString` expecting a clean state | [never-do-secrets](./never-do-secrets.md#3-aws_ssm_parameter-data-source-expecting-a-clean-state) |
| `aws_ssm_parameters_by_path` with decryption expecting a clean state | [never-do-secrets](./never-do-secrets.md#4-aws_ssm_parameters_by_path-with-decryption-expecting-a-clean-state) |
| `name` on the ephemeral `aws_ssm_parameter` | [never-do-secrets](./never-do-secrets.md#5-name-on-the-ephemeral-aws_ssm_parameter) |
| Path name without a leading `/` | [never-do-names-version](./never-do-names-version.md#1-path-name-without-a-leading-slash) |
| Pinning withdrawn provider 6.57.0 | [never-do-names-version](./never-do-names-version.md#2-pinning-version-6570) |
