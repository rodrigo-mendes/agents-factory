# Always-Do — Reporting and Commitments (CUR, Data Exports, Savings Plan)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23. Values marked `# example` are placeholders; condition operators are `# example (operator not taken from a page)` — the AWS pages are cited for the condition keys only.
These resources are global per the enhanced-region guide (no resource-level `region`). `s3_region` names the bucket's region; it is not the resource region.

## 10. Legacy CUR Report

The page says the service is "only available in `us-east-1` currently" (provider-region choice: see Ask First
in SKILL.md). Required: `report_name` (up to 256 chars), `time_unit` (`DAILY`, `HOURLY`, `MONTHLY`), `format`
(`textORcsv`, `Parquet`), `compression` (`GZIP`, `ZIP`, `Parquet`; Parquet pairs with Parquet),
`additional_schema_elements` (`RESOURCES`, `SPLIT_COST_ALLOCATION_DATA`, `MANUAL_DISCOUNT_COMPATIBILITY`),
`s3_bucket` (existing bucket), `s3_region`, `s3_prefix` (required since 6.0; an empty prefix makes the report
non-editable in the console), `additional_artifacts`. `ATHENA` must be alone and needs
`report_versioning = "OVERWRITE_REPORT"`.

```hcl
# Fragment — aws_s3_bucket.cur is defined elsewhere (see provisioning-aws-s3-v6)
resource "aws_cur_report_definition" "this" {
  report_name                = "cost-and-usage"   # example
  time_unit                  = "DAILY"
  format                     = "Parquet"
  compression                = "Parquet"
  additional_schema_elements = ["RESOURCES"]
  s3_bucket                  = aws_s3_bucket.cur.id
  s3_region                  = "eu-west-1"        # example: bucket region, not the resource region
  s3_prefix                  = "cur"              # example
  additional_artifacts       = ["ATHENA"]
  report_versioning          = "OVERWRITE_REPORT"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cur_report_definition.html.markdown
# Source (s3_prefix required): https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/version-6-upgrade.html.markdown
```

The resource page does not mention a bucket policy. AWS documents: principal `billingreports.amazonaws.com`;
`s3:GetBucketAcl` and `s3:GetBucketPolicy` on the bucket; `s3:PutObject` on `bucket/*`; conditions
`aws:SourceArn` = `arn:aws:cur:us-east-1:${AccountId}:definition/*` and `aws:SourceAccount`. Changing the
policy or bucket owner stops delivery; AWS recommends ACLs disabled.

```hcl
# Fragment — aws_s3_bucket.cur and data.aws_caller_identity.current are defined elsewhere
data "aws_iam_policy_document" "cur_bucket" {
  statement {
    actions   = ["s3:GetBucketAcl", "s3:GetBucketPolicy"]
    resources = [aws_s3_bucket.cur.arn]
    principals {
      type        = "Service"
      identifiers = ["billingreports.amazonaws.com"]
    }
    condition {
      test     = "StringEquals" # example (operator not taken from a page)
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
    condition {
      test     = "StringLike" # example (operator not taken from a page)
      variable = "aws:SourceArn"
      values   = ["arn:aws:cur:us-east-1:${data.aws_caller_identity.current.account_id}:definition/*"]
    }
  }
  statement {
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.cur.arn}/*"]
    principals {
      type        = "Service"
      identifiers = ["billingreports.amazonaws.com"]
    }
    condition {
      test     = "StringEquals" # example (operator not taken from a page)
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
    condition {
      test     = "StringLike" # example (operator not taken from a page)
      variable = "aws:SourceArn"
      values   = ["arn:aws:cur:us-east-1:${data.aws_caller_identity.current.account_id}:definition/*"]
    }
  }
}
# Source: https://docs.aws.amazon.com/cur/latest/userguide/cur-s3.html
```

Import: `report_name`.

## 11. Data Exports

Required: `export` with `name`, `data_query` (`query_statement`, optional `table_configurations`),
`destination_configurations.s3_destination` (`s3_bucket`, `s3_prefix`, `s3_region`, `s3_output_configurations`
with `compression` `GZIP`/`PARQUET`, `format` `TEXT_OR_CSV`/`PARQUET`, `output_type` `CUSTOM`, `overwrite`
`CREATE_NEW_REPORT`/`OVERWRITE_REPORT`) and `refresh_cadence.frequency` = `SYNCHRONOUS` (the only value).
If `table_configurations` is set, all its values must be set; for `COST_AND_USAGE_REPORT`, `BILLING_VIEW_ARN`
is required. AWS: CUR 2.0 is "the new and recommended way" to receive detailed cost and usage data; exports
refresh up to once per day.

```hcl
# Fragment — aws_s3_bucket.exports is defined elsewhere (see provisioning-aws-s3-v6)
resource "aws_bcmdataexports_export" "this" {
  export {
    name = "cost-export" # example

    data_query {
      query_statement = var.query_statement # placeholder: a valid SQL query per the Data Exports page (variable defined elsewhere)
    }

    destination_configurations {
      s3_destination {
        s3_bucket = aws_s3_bucket.exports.id
        s3_prefix = "exports"       # example
        s3_region = "eu-west-1"     # example: bucket region, not the resource region

        s3_output_configurations {
          compression = "PARQUET"
          format      = "PARQUET"
          output_type = "CUSTOM"
          overwrite   = "OVERWRITE_REPORT"
        }
      }
    }

    refresh_cadence {
      frequency = "SYNCHRONOUS"
    }
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/bcmdataexports_export.html.markdown
# Source (AWS notes): https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html
```

Bucket policy (AWS): principal `bcm-data-exports.amazonaws.com`, `s3:PutObject`, `ArnLike` `aws:SourceArn` =
`arn:aws:bcm-data-exports:us-east-1:{source-account-id}:export/*` plus `aws:SourceAccount`; cross-account
bucket delivery is supported. Source: https://docs.aws.amazon.com/cur/latest/userguide/dataexports-s3-bucket.html

Timeouts: create 30m, update 30m. Import: export ARN or `identity { arn }` (Terraform >= 1.12).
Refresh: https://docs.aws.amazon.com/cur/latest/userguide/dataexports-create-standard.html

## 12. Savings Plan

WARNING on the page: a financial commitment; an active plan "cannot be cancelled or deleted" — only `queued`
plans can be deleted, and destroying an active plan only removes it from state. Required:
`savings_plan_offering_id`, `commitment` (hourly USD). Optional: `purchase_time`, `upfront_payment_amount`
(required for All/Partial Upfront, omit for No Upfront), `tags`. The resource is
`aws_savingsplans_savings_plan` (documented at the page cited below). The exported `region`
attribute is "The AWS Region", not a resource argument.

```hcl
resource "aws_savingsplans_savings_plan" "compute" {
  savings_plan_offering_id = "00000000-0000-0000-0000-000000000000" # example placeholder
  commitment               = "1.0"                                    # example, hourly USD
  # upfront_payment_amount omitted: No Upfront
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/savingsplans_savings_plan.html.markdown
```

Timeouts: create/delete 30m. Import: `sp-…` ID. Provider support is "best effort" (6.62.0 CHANGELOG note).
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/CHANGELOG.md
