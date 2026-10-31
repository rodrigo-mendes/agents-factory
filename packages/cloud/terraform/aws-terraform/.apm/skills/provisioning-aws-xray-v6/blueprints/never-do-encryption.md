# Never-Do — Encryption Config

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources read 2026-10-23.

## 1. Removing the Encryption Config to Revert

The provider page states: "Removing this resource from Terraform does not change the encryption
configuration in X-Ray."
Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_encryption_config.html.markdown

The provider page defines `type = "NONE"` as default encryption; AWS: set `NONE` to return to default encryption.
Sources: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/xray_encryption_config.html.markdown ;
https://docs.aws.amazon.com/xray/latest/devguide/xray-console-encryption.html ;
https://docs.aws.amazon.com/xray/latest/devguide/xray-api-configuration.html

```hcl
# WRONG — removing this resource from Terraform does not change the encryption configuration in X-Ray
# resource "aws_xray_encryption_config" "cmk" {
#   type   = "KMS"
#   key_id = aws_kms_key.xray.arn   # fragment: defined elsewhere
# }

# CORRECT — apply the default-encryption setting
resource "aws_xray_encryption_config" "cmk" {
  type = "NONE"
}
```
