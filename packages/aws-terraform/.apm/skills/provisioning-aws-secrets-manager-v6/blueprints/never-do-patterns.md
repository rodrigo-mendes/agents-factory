# Never-Do Patterns — provisioning-aws-secrets-manager-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-23), and the correct alternative. Only sourced,
high-confidence facts are listed; inferred or absence-based items are Ask First in SKILL.md.

| Anti-pattern | Blueprint |
|---|---|
| Secret values in `secret_string` assumed safe in state | [never-do-secrets](./never-do-secrets.md#1-secret-values-in-secret_string) |
| Both plain and write-only value on one version | [never-do-secrets](./never-do-secrets.md#2-two-value-sources-on-one-version) |
| Deprecated `arn` on the version resource and data source | [never-do-secrets](./never-do-secrets.md#3-deprecated-arn-on-the-version) |
| Changing `type` after creation | [never-do-secrets](./never-do-secrets.md#4-changing-type-after-creation) |
| ISO-8601 rotation `duration` | [never-do-rotation-policy](./never-do-rotation-policy.md#1-iso-8601-rotation-duration) |
| `rotation_rules` with `rotation_enabled = false` | [never-do-rotation-policy](./never-do-rotation-policy.md#2-rotation_rules-with-rotation_enabled--false) |
| `null` / `""` policy to remove, `"{}"` on the policy resource | [never-do-rotation-policy](./never-do-rotation-policy.md#3-removing-a-policy-the-wrong-way) |
| Pinning withdrawn provider 6.57.0 | [never-do-rotation-policy](./never-do-rotation-policy.md#4-pinning-version-6570) |
