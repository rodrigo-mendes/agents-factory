# Never-Do Patterns — provisioning-aws-acm-v6

Index of the never-do blueprints. Entries give the documented reason with its source (fetched
2026-10-22) and the correct alternative; most have a `# WRONG` block, §2 is explanatory only.

| Anti-pattern | Blueprint |
|---|---|
| `private_key` on an imported certificate (stored in state) | [never-do-certificates](./never-do-certificates.md#1-private_key-on-an-imported-certificate) |
| Pinning ACM certificates | [never-do-certificates](./never-do-certificates.md#2-pinning-acm-certificates) |
| Deleting validation CNAMEs of an in-use certificate | [never-do-certificates](./never-do-certificates.md#3-deleting-validation-cnames) |
| Pinning withdrawn provider 6.57.0 | [never-do-certificates](./never-do-certificates.md#4-pinning-version-6570) |
| CloudFront viewer certificate outside `us-east-1` | [never-do-certificates](./never-do-certificates.md#5-cloudfront-certificate-outside-us-east-1) |
| `validation_method` on an imported certificate | [never-do-certificates](./never-do-certificates.md#6-validation_method-on-an-imported-certificate) |
| Legacy constraints (`>= 1.7`, `dynamodb_table`) | [never-do-certificates](./never-do-certificates.md#7-legacy-version-and-backend-settings) |
