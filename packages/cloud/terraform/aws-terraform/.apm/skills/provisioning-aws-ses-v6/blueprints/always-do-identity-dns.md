# Always-Do — Identity and DNS (Terraform Block, Domain Identity, DKIM, MAIL FROM)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources dated 2026-10-23. All names, domains and ARNs below are examples.
Indexing `dkim_signing_attributes[0].tokens` (list vs set) is (unverified) for every snippet in this file.
Fragment note: `var.dkim_private_key` has no default; supply it when using the BYODKIM snippet.

## 1. Terraform block and S3 backend

Root modules use `~>`; `use_lockfile = true` is the S3 backend's native locking and `dynamodb_table` is deprecated.

```hcl
terraform {
  required_version = "~> 1.16"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.69"
    }
  }
  backend "s3" {
    bucket       = "my-tf-state"            # example
    key          = "ses/terraform.tfstate"  # example
    region       = "eu-west-1"              # example
    use_lockfile = true
    encrypt      = true
  }
}

provider "aws" {
  region = "eu-west-1" # example; SES resources default to the provider Region
}

variable "domain" {
  type    = string
  default = "example.com" # example
}

variable "event_topic_arn" {
  type    = string
  default = "arn:aws:sns:eu-west-1:111122223333:ses-events" # example
}
```

Sources: https://developer.hashicorp.com/terraform/language/backend/s3 ,
https://developer.hashicorp.com/terraform/language/expressions/version-constraints

## 2. Domain identity and Easy DKIM

`email_identity` accepts an email address or a domain. To send from the same identity in more than one
Region, create and verify a separate identity in each Region (AWS identities page). `tokens` is exported by
the identity page (Easy DKIM: strings for CNAME records).

```hcl
# Fragment: aws_sesv2_configuration_set.main is defined in always-do-sending-config.md §4.
resource "aws_sesv2_email_identity" "domain" {
  email_identity         = var.domain
  configuration_set_name = aws_sesv2_configuration_set.main.configuration_set_name

  dkim_signing_attributes {
    next_signing_key_length = "RSA_2048_BIT" # or RSA_1024_BIT
  }

  tags = { Environment = "example" } # example
}

# DKIM CNAME record names (AWS form: <token>._domainkey.<domain>, three records).
# The record VALUE is the token followed by a Region/identity-specific hosted-zone domain;
# how to obtain that suffix in HCL is (unverified). Create the Route 53 records with
# provisioning-aws-route53-v6.
output "dkim_cname_names" {
  value = [
    for t in aws_sesv2_email_identity.domain.dkim_signing_attributes[0].tokens :
    "${t}._domainkey.${var.domain}"
  ]
}
```

`PENDING` is a documented `verification_status` value; whether creation returns before verification completes is (medium confidence), and the page documents no waiter (unverified).
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity.html.markdown ,
https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html

BYODKIM alternative: the private key is Sensitive, 1024- or 2048-bit RSA, base64, with the first and last PEM lines and the line breaks removed.

```hcl
variable "dkim_private_key" {
  type      = string
  sensitive = true
}

resource "aws_sesv2_email_identity" "byodkim" {
  email_identity = "byodkim.example.com" # example

  dkim_signing_attributes {
    domain_signing_private_key = var.dkim_private_key
    domain_signing_selector    = "selector1" # example
  }
}
```

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity.html.markdown

## 3. Custom MAIL FROM

The MAIL FROM domain must be a subdomain of the parent domain of a verified identity. AWS lists the records
to publish on it: one `MX 10 feedback-smtp.<region>.amazonses.com` and a TXT `"v=spf1 include:amazonses.com ~all"`.

```hcl
resource "aws_sesv2_email_identity_mail_from_attributes" "domain" {
  email_identity         = aws_sesv2_email_identity.domain.email_identity
  mail_from_domain       = "mail.${var.domain}" # example subdomain
  behavior_on_mx_failure = "USE_DEFAULT_VALUE"  # or REJECT_MESSAGE (requires mail_from_domain)
}
```

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/sesv2_email_identity_mail_from_attributes.html.markdown ,
https://docs.aws.amazon.com/ses/latest/dg/mail-from.html
