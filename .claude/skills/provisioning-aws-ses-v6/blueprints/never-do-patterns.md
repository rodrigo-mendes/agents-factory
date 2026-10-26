# Never-Do Patterns — provisioning-aws-ses-v6

Index of the never-do blueprints. Each entry has a `# WRONG` block, the documented reason with its
source (dated 2026-10-23), and the correct alternative. One row per row of the SKILL.md table.

| Anti-pattern | Blueprint |
|---|---|
| `REJECT_MESSAGE` without `mail_from_domain` | [never-do-ses-config](./never-do-ses-config.md#1-reject_message-without-mail_from_domain) |
| Several MX records on the MAIL FROM domain | [never-do-ses-config](./never-do-ses-config.md#2-several-mx-records-on-the-mail-from-domain) |
| DKIM CNAME name with a leading underscore on the token | [never-do-ses-config](./never-do-ses-config.md#3-underscore-prefixed-dkim-cname-name) |
| Custom event bus in `event_bridge_destination` | [never-do-ses-config](./never-do-ses-config.md#4-custom-event-bus-in-event_bridge_destination) |
| Pinning withdrawn provider 6.57.0 | [never-do-provider-migration](./never-do-provider-migration.md#1-pinning-version-6570) |
| S3 backend with `dynamodb_table` (deprecated) | [never-do-provider-migration](./never-do-provider-migration.md#2-s3-backend-with-dynamodb_table) |
