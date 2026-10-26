# Corrections and Limits — Step Functions on hashicorp/aws 6.x

Pages read 2026-10-23. These are claims seen in older write-ups. Rows marked (medium confidence,
absence of evidence) rest on a page not stating the item, not on a page forbidding it; they are
notes, not Never rules.

| Claim seen elsewhere | What the pages state |
|---|---|
| A resource `aws_sfn_state_machine_version` exists | No page found for it: the raw docs URL `https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine_version.html.markdown` returned 404 on 2026-10-23 (medium confidence, absence of evidence). Versions come from `publish = true` ("during creation") on https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sfn_state_machine.html.markdown and from the data source on https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/sfn_state_machine_versions.html.markdown |
| A `definition_substitutions` argument | Not listed on the `aws_sfn_state_machine` page (medium confidence, absence of evidence); `definition` is an ASL JSON string on that page; `templatefile()` and `jsonencode()` are the substitutes (medium confidence) |
| Role trust includes `delivery.logs.amazonaws.com` | The role trust principal is `states.amazonaws.com` (https://docs.aws.amazon.com/step-functions/latest/dg/procedure-create-iam-role.html); `delivery.logs.amazonaws.com` appears in the key policy (https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html) |
| Logging policy without `logs:CreateLogStream` | The logging action list on https://docs.aws.amazon.com/step-functions/latest/dg/cw-logs.html includes `logs:CreateLogStream` |
| Key policy grants `delivery.logs` Encrypt/GenerateDataKey | The encryption page asks `kms:Decrypt` for that principal (https://docs.aws.amazon.com/step-functions/latest/dg/encryption-at-rest.html) |
| The 6.0 upgrade guide changes Step Functions resources | No `aws_sfn_*` entry was found (medium confidence, absence of evidence): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown |

## Coverage limits

| Tag | Item |
|---|---|
| L1 | Provider CHANGELOG read in chunks; the 6.55.0 enhancement list was truncated in one chunk |
| L2 | The `encryption_configuration` text on the provider page contains an unfilled "[TBD]" |
| L3 | Distributed Map, JSONata, HTTP Task and redrive are not covered in depth |
