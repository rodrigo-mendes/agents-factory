# Evaluation report: provisioning-aws-sam-v6 (round 1)

Method: single-pass simulation, with no sub-agents. Each response was written only from SKILL.md and its linked blueprints, then judged.

## Verdicts

| # | Scenario | must_pass | must_not | Verdict |
|---|---|---|---|---|
| 1 | Canonical: local testing with the SAM CLI | 6/6 | 3/3 OK | PASS |
| 2 | Edge: SAR NoEcho after upgrade | 5/5 | 3/3 OK | PASS |
| 3 | Misuse: sam deploy/sync with Terraform | 3/3 | 2/2 OK | PASS |
| 4 | Anti-pattern: SAM template in aws_cloudformation_stack | 5/5 | 4/4 OK | PASS |
| 5 | Security Hub CloudFormation controls | 3/3 | 2/2 OK | PASS (see S5 note) |

Overall: 5/5 scenarios PASS. Criteria pass rate is 22/22 must_pass and 14/14 must_not. No FAIL or PARTIAL.

## S1: canonical
Response, paraphrased from the skill: SAM is not a hashicorp/aws resource. It is the CloudFormation transform plus the SAM CLI. Terraform still does plan and apply, and the SAM CLI is for local debug and test only. Use `sam build --hook-name terraform`, `sam local invoke --hook-name terraform`, `sam local start-api --hook-name terraform` and `sam local start-lambda --hook-name terraform`. Docker is required. If artifacts are built inside the Terraform project, add one `null_resource` named `sam_metadata_*` per function or layer, with `resource_type` set to `ZIP_LAMBDA_FUNCTION`, `IMAGE_LAMBDA_FUNCTION` or `LAMBDA_LAYER`. Run `terraform apply` when a new resource is added. The terraform block uses `required_version = "~> 1.16"` and `aws ~> 6.69`.

- must_pass 1 PASS. Evidence is SKILL.md lines 12-19 and the Always-Do rule "local debugging and testing only".
- must_pass 2 PASS. Evidence is the Always-Do `--hook-name terraform` bullets and the Quick Reference.
- must_pass 3 PASS. Evidence is "Have Docker installed for local testing".
- must_pass 4 PASS. Evidence is the three `sam metadata` Always-Do bullets.
- must_pass 5 PASS. Evidence is never-do-sam-cli §5, "Run `terraform apply` when a new resource is added".
- must_pass 6 PASS. Evidence is the Always-Do version bullet and foundation §1.
- must_not "deploys" OK. The skill says Terraform manages the application.
- must_not "hard minimum Terraform" OK. The response says none is stated and that v1.6.0 is only a Terraform Cloud recommendation (U1).
- must_not `dynamodb_table` OK. The response uses `use_lockfile = true`.

## S2: edge
- must_pass 1 PASS. Evidence is the Always-Do bullet "since 6.52.0 `NoEcho` parameter values are stored in state in plaintext", plus "Secure the state backend".
- must_pass 2 PASS. Evidence is the Always-Do bullet on `sensitive()`.
- must_pass 3 PASS. Evidence is the SKILL.md migration section: "need a one-time manual state reconciliation after upgrading".
- must_pass 4 PASS. Evidence is "`capabilities` changed from Required to Optional/Computed".
- must_pass 5 PASS. The CHANGELOG URL is cited in the migration section and in always-do-cloudformation.
- must_not 1, 2 and 3 OK. The response says NoEcho is hidden in CloudFormation API responses but stored in state. It says `capabilities` is optional. The skill never calls the SAR stack a nested stack.

## S3: misuse
- must_pass 1 PASS. Evidence is the Quick Reference, "`sam build`, `sam local invoke`, `sam local start-api`, `sam local start-lambda`".
- must_pass 2 PASS. Evidence is the Ask First row: "Their reference pages show no `--hook-name` or Terraform option" tagged "(medium confidence, absence of evidence)".
- must_pass 3 PASS. Evidence is the same row: "Terraform still provides `terraform plan`, `apply` and `validate`".
- must_not 1 and 2 OK. The response claims no support for `sam deploy`, `sam sync` or `sam validate` and invents no option. It also does not say deploy "does not work". It says no evidence of support was found, which is the correct level of claim. The skill itself does not assert that these commands work with Terraform.

## S4: anti-pattern
- must_pass 1 PASS. Evidence is the Never-Do row "Set `on_failure` and `disable_rollback` together ... they conflict".
- must_pass 2 PASS. The 70 KB template exceeds 51,200 bytes, so the response recommends `template_url` (up to 460,800 bytes).
- must_pass 3 PASS. The response rejects the 6.57.0 pin as withdrawn and recommends `~> 6.69`.
- must_pass 4 PASS. Evidence is the Always-Do bullet "`CAPABILITY_AUTO_EXPAND` ... required when a stack is created directly from a template that uses the `AWS::Serverless` transform". The response also asks about `CAPABILITY_IAM` and `CAPABILITY_NAMED_IAM` for SAM-generated roles, tagged unverified (U4).
- must_pass 5 PASS. Evidence is "CloudFormation, not Terraform, expands the SAM syntax".
- must_not 1 to 4 OK. The response accepts none of the four constructs and does not say Terraform expands SAM. Quoting the rejected constructs as examples is allowed.

## S5: Security Hub
- must_pass 1 PASS. Evidence is the Quick Reference rows. CloudFormation.1 is low severity and retired April 2024, CloudFormation.2 is low, and CloudFormation.3 and .4 are medium.
- must_pass 2 PASS. Evidence is always-do-cloudformation line 79: "CloudFormation.4 maps to `iam_role_arn`; CloudFormation.2 checks stack tags".
- must_pass 3 PASS. Evidence is the Ask First row tagged "(medium confidence, absence of evidence)" ("may not satisfy it").
- must_not 1 OK. CloudFormation.1 is listed as retired, not as an active control.
- must_not 2 OK. The response says "the page as read has no argument", not "has no way to".

S5 note: the skill's Quick Reference row for CloudFormation.3 states "Stacks should have termination protection enabled", while the Ask First row hedges. These are consistent. The skill also flags L2: no Security Hub control page for SAR was reviewed. CloudFormation.4 for SAR stacks is tagged unverified (U9), so the response must not assert that SAR stacks fail it as fact. The skill says "expected to fail", which is a hedge.

## Criteria quality
- No criterion demands advice the skill never gives. All 22 must_pass items trace to SKILL.md or a blueprint.
- S1 must_pass 4 and 6 are conditional ("if artifacts built inside", "in any terraform block"). They are correctly framed, but a judge needs the response to include a terraform block for item 6 to be exercised. Minor ambiguity.
- S3 must_pass 2 requires the exact tag `(medium confidence, absence of evidence)`. This is sourced and not a bug, but it makes the check wording-sensitive.
- S3 gap: the scenario does not test the claim "`sam deploy`/`sync`/`validate` work with Terraform". That is covered by must_not.
- Scope check: SKILL.md line 12 states that SAM is not a provider resource. Lines 17-19 and the Quick Reference limit Terraform support to build and local commands. Nowhere does the skill claim deploy, sync or validate work with Terraform. No scope violation.
- Possible additional scenario (optional): `sam validate` and `sam deploy` asked about separately, to verify the hedge on each.

## Fixes needed
None blocking. Optional:
1. SKILL.md Ask First (CloudFormation.4 row): the wording "expected to fail" is an inference. Tag it (unverified), which it already is (U9). No change is required.
2. evaluation-scenarios.md S1: the sixth must_pass is conditional. Consider rewording it to "if a terraform block is shown, uses ...".
