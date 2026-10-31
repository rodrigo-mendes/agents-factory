# Always-Do — Classic aws_ses Family (separate from aws_sesv2)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources dated 2026-10-23. Only what the resource pages state.
Never copy arguments or value casing between this family and `aws_sesv2_*`.

## 9. Classic aws_ses identity policy

`aws_ses_identity_policy` takes `identity` (name or ARN), `name`, `policy` (the page suggests
`aws_iam_policy_document`) and an optional `region`. Import is `identity|name`
(page example `'example.com|example'`).

```hcl
# Fragment: aws_ses_domain_identity.example and data.aws_iam_policy_document.example are defined elsewhere
# (the IAM policy document: provisioning-aws-iam-v6).
resource "aws_ses_identity_policy" "example" {
  identity = aws_ses_domain_identity.example.arn
  name     = "example" # example
  policy   = data.aws_iam_policy_document.example.json
}
```

Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ses_identity_policy.html.markdown

Other classic facts:

- `aws_ses_domain_mail_from`: `behavior_on_mx_failure` "Defaults to `UseDefaultValue`" (classic casing; v2 uses `USE_DEFAULT_VALUE`). An MX record is required for validation and a TXT record may be needed for SPF. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ses_domain_mail_from.html.markdown
- `aws_ses_domain_identity_verification` waits for verification, "does not represent a real-world entity in AWS", and has a `create` timeout default of 45 minutes. Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/ses_domain_identity_verification.html.markdown
- Managing one identity with both families: no provider page documents conflicts (unverified).
