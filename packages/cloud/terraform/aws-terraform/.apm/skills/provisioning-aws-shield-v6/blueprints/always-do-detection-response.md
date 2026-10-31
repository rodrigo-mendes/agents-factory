# Always-Do — Health Checks, SRT Access, Proactive Engagement

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 4. Health Check Association

Hosted zones cannot use health-based detection, and proactive engagement requires health checks;
the association is optional otherwise. Ask First on the choice of health check: AWS says it must
report healthy when associated, be relevant to the resource, and not be deleted while used
(medium confidence). Shield Advanced does not manage health checks for you.

```hcl
variable "health_check_arn" {
  type        = string
  description = "ARN of a healthy Route 53 health check relevant to the protected resource"
}

resource "aws_shield_protection_health_check_association" "cdn" {
  health_check_arn     = var.health_check_arn
  shield_protection_id = aws_shield_protection.cdn.id
}
```

Import ID: `<shield_protection_id>+<health_check_arn>`.

Sources:
- https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_protection_health_check_association.html.markdown
- https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-health-checks.html

## 5. SRT Access

`role_arn` is the role the Shield Response Team uses; attach the managed policy
`AWSShieldDRTAccessPolicy` before the request. The log bucket association takes the S3 bucket
holding logs to share and the ID of the role association. Timeouts: 30m (create/update/delete on
the role association; create/delete on the log bucket association).

```hcl
variable "drt_role_arn" {
  type        = string
  description = "Role with AWSShieldDRTAccessPolicy attached"
}

resource "aws_shield_drt_access_role_arn_association" "this" {
  role_arn = var.drt_role_arn
}

resource "aws_shield_drt_access_log_bucket_association" "logs" {
  log_bucket              = aws_s3_bucket.waf_logs.bucket
  role_arn_association_id = aws_shield_drt_access_role_arn_association.this.id
}
```

Import: role association by account ID; log bucket association by `log_bucket` name.

Sources:
- https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_drt_access_role_arn_association.html.markdown
- https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_drt_access_log_bucket_association.html.markdown

## 6. Proactive Engagement (when approved)

Ask First: contacts defined here replace any contacts already configured in AWS. At least one
contact must have a phone number (`+` and up to 15 digits). AWS requires health checks (section 4).

```hcl
resource "aws_shield_proactive_engagement" "this" {
  enabled = true

  emergency_contact {
    email_address = "secops@example.com"
    phone_number  = "+12065550100"
    contact_notes = "24x7 on-call"
  }
}
```

Import by account ID. Whether apply fails without the DRT role association is not documented
on the page (unverified).

Sources:
- https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/shield_proactive_engagement.html.markdown
- https://docs.aws.amazon.com/waf/latest/developerguide/ddos-advanced-health-checks.html
