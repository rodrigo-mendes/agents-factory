# Never-Do Patterns — provisioning-aws-cloudfront-v6

Index of the never-do blueprints, split by topic. Each entry has a `# WRONG` block, the documented
reason with its source (fetched 2026-10-22), and the correct alternative.

| Anti-pattern | Blueprint |
|---|---|
| `minimum_protocol_version` omitted (provider default `TLSv1`) | [never-do-security](./never-do-security.md#1-relying-on-the-default-minimum_protocol_version) |
| `allow-all` viewer policy, `http-only` origin, `SSLv3` | [never-do-security](./never-do-security.md#2-allow-all-viewer-protocol-and-insecure-origin-protocols) |
| OAI for new S3 origins; OAC on S3 website endpoints | [never-do-security](./never-do-security.md#3-oai-for-new-s3-origins-and-oac-on-website-endpoints) |
| `trusted_signers` instead of `trusted_key_groups` | [never-do-security](./never-do-security.md#4-trusted_signers-instead-of-trusted_key_groups) |
| `region` on CloudFront resources; certificate outside us-east-1 | [never-do-provider-operations](./never-do-provider-operations.md#1-setting-region-on-cloudfront-resources) |
| `forwarded_values` (deprecated) | [never-do-provider-operations](./never-do-provider-operations.md#2-forwarded_values) |
| Configured `etag` on response headers policy | [never-do-provider-operations](./never-do-provider-operations.md#3-configuring-etag-on-a-response-headers-policy) |
| Public key `encoded_key` without trailing newline | [never-do-provider-operations](./never-do-provider-operations.md#4-public-key-without-trailing-newline) |
| Function deleted while associated; `retain_on_delete` surprises | [never-do-provider-operations](./never-do-provider-operations.md#5-deleting-a-function-still-associated-or-assuming-fast-deletes) |
| Pin 6.57.0; S3 backend `dynamodb_table` | [never-do-provider-operations](./never-do-provider-operations.md#6-pins-and-backend) |
