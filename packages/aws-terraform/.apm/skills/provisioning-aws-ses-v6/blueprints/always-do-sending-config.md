# Always-Do — Sending Configuration (Configuration Set, Events, Pool, Contacts, Account Level, Test)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources dated 2026-10-23. All names and ARNs below are examples.

## 4. Configuration set

Security Hub SES.3 (medium severity) checks that configuration sets have TLS enabled; `tls_policy = "REQUIRE"` is the configuration set argument.
SES.2 (low severity) checks that configuration sets are tagged.
Indexing `delivery_options[0]` in the test in §8 (list vs set) is (unverified). The control page states that by default SES uses opportunistic TLS and that controls may not be available in all Regions.

```hcl
resource "aws_sesv2_configuration_set" "main" {
  configuration_set_name = "main" # example

  delivery_options {
    tls_policy = "REQUIRE"
    # Optional (Ask First): link a dedicated IP pool defined in §6
    # sending_pool_name = aws_sesv2_dedicated_ip_pool.main.pool_name
  }

  reputation_options {
    reputation_metrics_enabled = true
  }

  sending_options {
    sending_enabled = true
  }

  suppression_options {
    suppressed_reasons = ["BOUNCE", "COMPLAINT"]
  }

  tags = { Environment = "example" } # example
}
```

Sources: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set.html.markdown ,
https://docs.aws.amazon.com/securityhub/latest/userguide/ses-controls.html

## 5. Event destination

`enabled` defaults to `false`; set it to `true`. `matching_event_types` is required. This snippet uses one
destination block; whether several can coexist in one `event_destination` is (unverified).

```hcl
# Fragment: the topic is provisioned with provisioning-aws-sns-v6; var.event_topic_arn is defined in
# always-do-identity-dns.md §1 (example value).
resource "aws_sesv2_configuration_set_event_destination" "sns" {
  configuration_set_name = aws_sesv2_configuration_set.main.configuration_set_name
  event_destination_name = "sns-events" # example

  event_destination {
    enabled              = true
    matching_event_types = ["BOUNCE", "COMPLAINT", "REJECT"]

    sns_destination {
      topic_arn = var.event_topic_arn
    }
  }
}
```

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set_event_destination.html.markdown

## 6. Dedicated IP pool, contact list and identity policy

`scaling_mode` is `STANDARD` or `MANAGED`; the pool is linked through `delivery_options.sending_pool_name` (Ask First).
Tag the contact list (Security Hub SES.1, low severity, checks tagging). The page example uses `OPT_IN`; other
`default_subscription_status` values are (unverified).

```hcl
resource "aws_sesv2_dedicated_ip_pool" "main" {
  pool_name    = "main-pool" # example
  scaling_mode = "STANDARD"
}

resource "aws_sesv2_contact_list" "main" {
  contact_list_name = "newsletter" # example
  description       = "Newsletter subscribers" # example

  topic {
    topic_name                  = "weekly" # example
    display_name                = "Weekly digest" # example
    default_subscription_status = "OPT_IN" # value used in the page example
  }

  tags = { Environment = "example" } # example
}

# Fragment: var.sending_policy_json is a JSON policy document whose Resource is the identity ARN.
resource "aws_sesv2_email_identity_policy" "sending" {
  email_identity = aws_sesv2_email_identity.domain.email_identity
  policy_name    = "sending-authorization" # example
  policy         = var.sending_policy_json
}
```

Sources: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_dedicated_ip_pool.html.markdown ,
https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_contact_list.html.markdown ,
https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity_policy.html.markdown

## 7. Account-level VDM

The resource is `aws_sesv2_account_vdm_attributes`; `vdm_enabled` is `ENABLED` or `DISABLED`. Import ID is the
literal `ses-account-vdm-attributes`. Destroy behaviour is (unverified) — confirm ownership first (Ask First).

```hcl
resource "aws_sesv2_account_vdm_attributes" "this" {
  vdm_enabled = "ENABLED"
}
```

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_account_vdm_attributes.html.markdown

## 8. Terraform test

`mock_provider "aws"` with `command = plan` is the documented way to test without real resources. Fragment: the configuration set and
the variables `domain` and `event_topic_arn` (example defaults) come from the other blueprints; `dkim_private_key`
and `sending_policy_json` have no default, so omit those snippets from the tested configuration or supply values.

```hcl
# tests/ses.tftest.hcl
mock_provider "aws" {}

run "tls_is_required" {
  command = plan

  assert {
    condition     = aws_sesv2_configuration_set.main.delivery_options[0].tls_policy == "REQUIRE"
    error_message = "Configuration sets must set tls_policy = REQUIRE (Security Hub SES.3)."
  }
}
```

Sources: https://developer.hashicorp.com/terraform/language/tests ,
https://developer.hashicorp.com/terraform/language/tests/mocking
