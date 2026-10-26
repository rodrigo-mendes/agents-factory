# Never-Do — Organization (Region, FullAWSAccess, SCP Limits, role_name, skip_destroy)

hashicorp/aws 6.x · Terraform ~> 1.16 · Sources fetched 2026-10-23.

## 1. Region on Organizations Resources

Organizations is global: the enhanced-region guide lists `aws_organizations_*` among resources that
do not accept `region`, and import IDs carry no `@region`.

```hcl
# WRONG — Organizations resources take no region
resource "aws_organizations_organizational_unit" "bad" {
  name      = "bad"
  parent_id = aws_organizations_organization.this.roots[0].id
  region    = "eu-west-1"   # WRONG
}
# terraform import aws_organizations_organizational_unit.bad ou-1234567@eu-west-1   # WRONG
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/guides/enhanced-region-support.html.markdown

# CORRECT — no region, plain ID
resource "aws_organizations_organizational_unit" "good" {
  name      = "good"
  parent_id = aws_organizations_organization.this.roots[0].id
}
# terraform import aws_organizations_organizational_unit.good ou-1234567
```

## 2. Removing FullAWSAccess

AWS attaches `FullAWSAccess` to every root, OU and account on creation. Removing it without
modifying or replacing it makes all AWS actions from member accounts fail. An allow list needs an
explicit `Allow` at every level from root to account.

```hcl
# WRONG — detaching FullAWSAccess with no replacement allow policy
# (all member-account actions then fail)

# CORRECT — keep FullAWSAccess and add Deny statements
resource "aws_organizations_policy" "deny_example" {
  name = "deny-example"
  content = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Deny", Action = ["organizations:LeaveOrganization"], Resource = "*" }]
  })
}
# Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html
# Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_evaluation.html
```

## 3. RCP Limits Applied to SCPs

5120 characters and 5 directly attached policies are the resource control policy limits. SCPs allow
10,240 characters and 10 attached per root, OU or account (minimum 1; the last SCP cannot be
removed).

```hcl
# WRONG — validating an SCP against the RCP size
variable "scp_json_wrong" {
  type = string
  validation {
    condition     = length(var.scp_json_wrong) <= 5120   # WRONG: RCP limit
    error_message = "too long"
  }
}
# Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html

# CORRECT
variable "scp_json" {
  type = string
  validation {
    condition     = length(var.scp_json) <= 10240   # SCP limit
    error_message = "SCP document must be at most 10,240 characters."
  }
}
```

## 4. SCP Expected to Restrict the Management Account

"SCPs don't affect users or roles in the management account." They do apply to member accounts that
are delegated administrators, and to the member root user. SCPs do not affect service-linked roles
or resource-based policies directly.

```hcl
# WRONG — assuming this attachment protects the management account
resource "aws_organizations_policy_attachment" "root" {
  policy_id = aws_organizations_policy.deny_example.id
  target_id = aws_organizations_organization.this.roots[0].id   # members only
}
# Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html
```

Instead, limit and review who can access the management account, use it only for tasks that
require it, and deploy no workloads there
(https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html).

## 5. role_name without ignore_changes

```hcl
# WRONG — always diffs after import (no API to read role_name back)
resource "aws_organizations_account" "bad" {
  name      = "bad"
  email     = "bad@example.com"
  role_name = "OrganizationAccountAccessRole"   # example value only
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_account.html.markdown

# CORRECT
resource "aws_organizations_account" "good" {
  name      = "good"
  email     = "good@example.com"
  role_name = "OrganizationAccountAccessRole"   # example value only
  lifecycle { ignore_changes = [role_name] }
}
```

## 6. skip_destroy Misread

On `aws_organizations_policy`, `skip_destroy = true` makes destroy remove the policy from state only;
it does not delete the policy. It does not "prevent the last attached SCP from being removed".

```hcl
# WRONG — comment claims protection that skip_destroy does not give
resource "aws_organizations_policy" "bad" {
  name         = "last-scp"
  content      = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }] })
  skip_destroy = true   # WRONG assumption: "protects the last attached SCP"
}
# Source: https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/main/website/docs/r/organizations_policy.html.markdown

# CORRECT — document the real behavior: state removal only; policy stays in AWS
resource "aws_organizations_policy" "kept" {
  name         = "must-stay-attached"
  content      = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }] })
  skip_destroy = true   # destroy removes it from state; the policy is not deleted
}
```
