# Never-Do — Attachment and Scope (rule resource args, CloudFront, HTTP API, region)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-22.

## 4. Wrong arguments on aws_wafv2_web_acl_rule

The parent is identified by `web_acl_arn`; `scope` is not an argument of this resource.

```hcl
# WRONG — web_acl_id and scope
resource "aws_wafv2_web_acl_rule" "bad" {
  name       = "rule"
  priority   = 1
  web_acl_id = aws_wafv2_web_acl.app.id   # WRONG
  scope      = "REGIONAL"                 # WRONG — not an argument
  # ...
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_rule.html.markdown

# CORRECT
resource "aws_wafv2_web_acl_rule" "good" {
  name        = "rule"
  priority    = 1
  web_acl_arn = aws_wafv2_web_acl.app.arn
  # statement and visibility_config required
}
```

## 5. Association with CloudFront

The association page states: "Do not use this resource to associate a WAFv2 Web ACL with a CloudFront
Distribution."

```hcl
# WRONG
resource "aws_wafv2_web_acl_association" "bad" {
  resource_arn = aws_cloudfront_distribution.site.arn   # WRONG
  web_acl_arn  = aws_wafv2_web_acl.cloudfront.arn
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_association.html.markdown

# CORRECT — on the distribution
resource "aws_cloudfront_distribution" "site" {
  # ...
  web_acl_id = aws_wafv2_web_acl.cloudfront.arn
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/cloudfront_distribution.html.markdown
```

## 6. Association with an HTTP API

The association supports an API Gateway stage "REST only; HTTP is unsupported".

```hcl
# WRONG — HTTP API stage
resource "aws_wafv2_web_acl_association" "bad" {
  resource_arn = aws_apigatewayv2_stage.http.arn   # WRONG — HTTP API
  web_acl_arn  = aws_wafv2_web_acl.app.arn
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl_association.html.markdown

# CORRECT — REST API stage ARN (see provisioning-aws-api-gateway-v6)
resource "aws_wafv2_web_acl_association" "good" {
  resource_arn = var.rest_api_stage_arn
  web_acl_arn  = aws_wafv2_web_acl.app.arn
}
```

## 7. CLOUDFRONT scope in the wrong region

For `scope = "CLOUDFRONT"` the docs require the region `us-east-1` on the AWS provider; the API says to
use the Region endpoint us-east-1 for all calls.

```hcl
# WRONG — CLOUDFRONT scope with the default provider region (e.g. eu-west-1)
resource "aws_wafv2_web_acl" "bad" {
  name  = "cf"
  scope = "CLOUDFRONT"   # WRONG without a us-east-1 provider
  # ...
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/wafv2_web_acl.html.markdown

# CORRECT — provider alias on us-east-1
resource "aws_wafv2_web_acl" "good" {
  provider = aws.us_east_1
  name     = "cf"
  scope    = "CLOUDFRONT"
  # ...
}
# Alternative: region = "us-east-1" on the resource (medium confidence)
```
