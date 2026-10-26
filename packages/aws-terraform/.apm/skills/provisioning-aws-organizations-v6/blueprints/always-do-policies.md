# Always-Do — Policies (SCP, Attachments, Delegated Admin, Resource Policy, Test)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 5. Deny-list SCP and Attachment

SCPs grant no permissions; they set the maximum permissions for IAM users and roles in member
accounts. Keep `FullAWSAccess` and add `Deny` statements (deny list). SCPs do not affect the
management account. Limits: 10,240 characters, 10 attached per root/OU/account. Test on an OU
before attaching to the root.

```hcl
resource "aws_organizations_policy" "deny_leave_and_close" {
  name        = "deny-leave-and-close"
  description = "Deny LeaveOrganization and CloseAccount in member accounts"
  type        = "SERVICE_CONTROL_POLICY"   # default type

  content = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "DenyLeaveAndClose"
      Effect   = "Deny"
      Action   = ["organizations:LeaveOrganization", "account:CloseAccount"]
      Resource = "*"
    }]
  })
}

# Step 1: attach to a test OU and validate. Step 2: add the root attachment below only after testing.
resource "aws_organizations_policy_attachment" "test_ou" {
  policy_id = aws_organizations_policy.deny_leave_and_close.id
  target_id = aws_organizations_organizational_unit.prod.id
}

resource "aws_organizations_policy_attachment" "root" {
  policy_id = aws_organizations_policy.deny_leave_and_close.id
  target_id = aws_organizations_organization.this.roots[0].id
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_policy.html.markdown
# Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html
# Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html
```

Organizations created in the console after 2026-07-10 get the Leave/Close SCP automatically;
organizations created with the CLI, SDKs or CloudFormation, or before that date, must attach it
manually. That Terraform-created organizations need it too is an inference (medium confidence).
`skip_destroy = true` on the policy only removes it from state on destroy; on the attachment
it means destroy will not detach the policy.

## 6. Policy Types and Non-SCP Policies

`type` takes one of 12 values: `AISERVICES_OPT_OUT_POLICY`, `BACKUP_POLICY`, `BEDROCK_POLICY`,
`CHATBOT_POLICY`, `DECLARATIVE_POLICY_EC2`, `INSPECTOR_POLICY`, `RESOURCE_CONTROL_POLICY`,
`S3_POLICY`, `SECURITYHUB_POLICY`, `SERVICE_CONTROL_POLICY`, `TAG_POLICY`,
`UPGRADE_ROLLOUT_POLICY`. `content` syntax depends on the type. `INSPECTOR_POLICY` needs
`inspector2.amazonaws.com` and `SECURITYHUB_POLICY` needs `securityhub.amazonaws.com` in
`aws_service_access_principals`. Tag, backup and other management policies use their own syntax:
build them with `jsonencode`, not the IAM policy document data source (medium confidence).

```hcl
variable "tag_policy" {
  type = any   # document body per the tag policy syntax (not covered by this skill)
}

resource "aws_organizations_policy" "tags" {
  name    = "tag-standards"
  type    = "TAG_POLICY"
  content = jsonencode(var.tag_policy)
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_policy.html.markdown
```

## 7. Delegated Administrator and Resource Policy

Delegate services to member accounts rather than working from the management account. SCPs do
apply to member accounts that are delegated administrators. The resource-based delegation policy
is limited to 40,000 characters.

```hcl
resource "aws_organizations_delegated_administrator" "securityhub" {
  account_id        = aws_organizations_account.member["security"].id
  service_principal = "securityhub.amazonaws.com"   # example value
}

variable "delegation_policy_json" {
  type = string   # JSON in the delegation policy syntax
}

resource "aws_organizations_resource_policy" "this" {
  content = var.delegation_policy_json
  tags    = { Owner = "platform" }
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_delegated_administrator.html.markdown
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_resource_policy.html.markdown
# Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html
```

## 8. Policies for Target and Terraform Test

The data source needs `target_id` (`r-…`, 12-digit account ID or `ou-…`) and `filter`; it returns
`ids`. Its page lists 7 filter values, narrower than the resource's 12 types (unverified).

```hcl
data "aws_organizations_policies_for_target" "scp" {
  target_id = aws_organizations_organizational_unit.prod.id
  filter    = "SERVICE_CONTROL_POLICY"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/d/organizations_policies_for_target.html.markdown
```

`terraform test` runs `.tftest.hcl` files from `tests/` with `mock_provider` and `command = plan`.
The test below is an illustrative example (the values are not from the research); it asserts a limit
the research documents (SCP document at most 10,240 characters).

```hcl
# tests/scp_size.tftest.hcl  — illustrative example
mock_provider "aws" {}

variables {
  management_account_role_arn = "arn:aws:iam::111111111111:role/example"   # example value
  accounts                    = {}
  scp_json                    = "{}"                                         # example value
  tag_policy                  = {}
  delegation_policy_json      = "{}"
}

run "scp_within_size_limit" {
  command = plan
  assert {
    condition     = length(var.scp_json) <= 10240
    error_message = "SCP document must be at most 10,240 characters."
  }
}
# Source: https://developer.hashicorp.com/terraform/language/tests
```

The test needs `variable "scp_json"` declared in the root module (see never-do-organization §3).
