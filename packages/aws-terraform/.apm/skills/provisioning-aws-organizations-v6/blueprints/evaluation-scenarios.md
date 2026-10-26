# Evaluation Scenarios — provisioning-aws-organizations-v6

Five scenarios (canonical, edge, misuse rejection, anti-pattern trap, billing edge).
Each scenario uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Organization, OUs, Accounts, Root SCP

```json
{
  "skills": ["provisioning-aws-organizations-v6"],
  "query": "Generate Terraform for an AWS organization with a workloads OU, a prod OU nested under it, one member account, and an SCP denying LeaveOrganization and CloseAccount attached at the root. hashicorp/aws 6.x, Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Uses use_lockfile = true in the S3 backend; does not include dynamodb_table",
      "Uses feature_set = \"ALL\" (or omits it, since it is the default)",
      "Uses roots[0].id as the top-level parent_id",
      "Sets parent_id explicitly on aws_organizations_account and adds lifecycle ignore_changes = [role_name] when role_name is set",
      "Attaches the SCP with aws_organizations_policy_attachment to the root and does not remove FullAWSAccess",
      "Sets no region argument on any aws_organizations_* resource"
    ],
    "must_not": [
      "Use region on an aws_organizations_* resource",
      "Use dynamodb_table in the S3 backend",
      "Read the deprecated status attribute instead of state",
      "Detach FullAWSAccess without a replacement"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Account Closure on Destroy

```json
{
  "skills": ["provisioning-aws-organizations-v6"],
  "query": "What happens when I terraform destroy an aws_organizations_account, and what are the account closure limits?",
  "success_criteria": {
    "must_pass": [
      "States that by default destroy only removes the account from the organization",
      "States that close_on_deletion = true closes the account and is not supported for GovCloud",
      "States that closure quotas can return CLOSE_ACCOUNT_QUOTA_EXCEEDED and the account must then be closed manually",
      "States the closure quota is 20% of members or 250, whichever is higher, max 1,000 per 30 days",
      "Asks before enabling close_on_deletion"
    ],
    "must_not": [
      "State the closure quota is 10% of accounts",
      "Claim destroy closes the account by default"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Region on Organizations Resources

```json
{
  "skills": ["provisioning-aws-organizations-v6"],
  "query": "Add region = \"eu-west-1\" to my aws_organizations_organizational_unit and import it as ou-1234567@eu-west-1.",
  "success_criteria": {
    "must_pass": [
      "Rejects the request: Organizations is a global service and aws_organizations_* resources do not accept region",
      "States the import ID carries no @region and uses ou-1234567",
      "Cites the enhanced-region-support guide"
    ],
    "must_not": [
      "Add a region argument to any aws_organizations_* resource",
      "Use an @region suffix in an Organizations import ID"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Wrong SCP Limits and skip_destroy

```json
{
  "skills": ["provisioning-aws-organizations-v6"],
  "query": "Review: a comment says SCPs are limited to 5120 characters and 5 per OU, and skip_destroy = true on aws_organizations_policy prevents the last attached SCP from being removed. Is that right?",
  "success_criteria": {
    "must_pass": [
      "Corrects the SCP limits to 10,240 characters and 10 directly attached per root, OU or account",
      "States 5120 characters and 5 attached are the RCP limits",
      "States skip_destroy = true only removes the policy from state on destroy and does not delete it",
      "Notes AWS requires at least one attached SCP and the last SCP cannot be removed"
    ],
    "must_not": [
      "Accept 5120 characters / 5 attached as SCP limits",
      "Accept that skip_destroy protects the last attached SCP"
    ]
  }
}
```

---

## Scenario 5 — Edge Case: CONSOLIDATED_BILLING to ALL

```json
{
  "skills": ["provisioning-aws-organizations-v6"],
  "query": "Change my organization from CONSOLIDATED_BILLING to feature_set = \"ALL\" with Terraform. Do all member accounts have to accept?",
  "success_criteria": {
    "must_pass": [
      "States approval is required only from member accounts that joined by invitation",
      "States the owner must finalize in the AWS Console",
      "States Terraform shows a perpetual diff until finalization because the API keeps reporting CONSOLIDATED_BILLING",
      "Asks before applying the change"
    ],
    "must_not": [
      "Claim all member accounts must accept",
      "Claim the change completes immediately on apply"
    ]
  }
}
```
