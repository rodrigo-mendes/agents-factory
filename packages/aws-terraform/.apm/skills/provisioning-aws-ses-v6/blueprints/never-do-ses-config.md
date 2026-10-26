# Never-Do — SES Configuration (MAIL FROM, DKIM, Event Bus)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources dated 2026-10-23. All names and ARNs are examples.
Indexing `dkim_signing_attributes[0].tokens` (list vs set) is (unverified) for every snippet in this file.

## 1. REJECT_MESSAGE without mail_from_domain

The `aws_sesv2_email_identity_mail_from_attributes` page says `mail_from_domain` is required when
`behavior_on_mx_failure = "REJECT_MESSAGE"`.

```hcl
# WRONG — mail_from_domain is required with REJECT_MESSAGE
resource "aws_sesv2_email_identity_mail_from_attributes" "bad" {
  email_identity         = "example.com" # example
  behavior_on_mx_failure = "REJECT_MESSAGE" # WRONG without mail_from_domain
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity_mail_from_attributes.html.markdown

# CORRECT
resource "aws_sesv2_email_identity_mail_from_attributes" "good" {
  email_identity         = "example.com" # example
  mail_from_domain       = "mail.example.com" # example
  behavior_on_mx_failure = "REJECT_MESSAGE"
}
```

## 2. Several MX records on the MAIL FROM domain

AWS: "you must publish exactly one MX record … If the MAIL FROM domain has multiple MX records, the
custom MAIL FROM setup with Amazon SES will fail."

The DNS records are created with provisioning-aws-route53-v6; the zone data below is DNS content, not
provider arguments.

```
# WRONG — two MX records on the MAIL FROM subdomain (example domain and Region)
mail.example.com  MX  10 feedback-smtp.eu-west-1.amazonses.com
mail.example.com  MX  20 mail.other-example.com        # WRONG — second MX record
# Source: https://docs.aws.amazon.com/ses/latest/dg/mail-from.html

# CORRECT — exactly one MX record
mail.example.com  MX  10 feedback-smtp.eu-west-1.amazonses.com
```

## 3. Underscore-prefixed DKIM CNAME name

AWS gives `abc123._domainkey.domain.com` as correct and `_abc123._domainkey.domain.com` as incorrect.

```hcl
# WRONG — leading underscore on the token (fragment: aws_sesv2_email_identity.domain is defined elsewhere)
locals {
  dkim_names_bad = [
    for t in aws_sesv2_email_identity.domain.dkim_signing_attributes[0].tokens :
    "_${t}._domainkey.example.com" # WRONG — example domain
  ]
}
# Source: https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html

# CORRECT
locals {
  dkim_names = [
    for t in aws_sesv2_email_identity.domain.dkim_signing_attributes[0].tokens :
    "${t}._domainkey.example.com" # example domain
  ]
}
```

## 4. Custom event bus in event_bridge_destination

The event destination page says "Only the default bus is supported."

```hcl
# WRONG — custom bus (fragment: var.custom_bus_arn is the ARN of a custom event bus)
resource "aws_sesv2_configuration_set_event_destination" "bad" {
  configuration_set_name = "main" # example
  event_destination_name = "events" # example
  event_destination {
    enabled              = true
    matching_event_types = ["BOUNCE"]
    event_bridge_destination {
      event_bus_arn = var.custom_bus_arn # WRONG — only the default bus is supported
    }
  }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_configuration_set_event_destination.html.markdown

# CORRECT (fragment: var.default_bus_arn is the ARN of the default event bus; see provisioning-aws-eventbridge-v6)
resource "aws_sesv2_configuration_set_event_destination" "good" {
  configuration_set_name = "main" # example
  event_destination_name = "events" # example
  event_destination {
    enabled              = true
    matching_event_types = ["BOUNCE"]
    event_bridge_destination {
      event_bus_arn = var.default_bus_arn
    }
  }
}
```
