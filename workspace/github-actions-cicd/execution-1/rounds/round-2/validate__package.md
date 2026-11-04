# Validate r2: package (agents, rules, command, README, apm.yml) (validator B, 2026-10-30)

Score: 91.0 (0 HIGH, 3 MEDIUM, 4 LOW). Base: packages/github-actions-cicd/

## Round-1 findings
- H1 FIXED: write scope names the extra files consistently: engineer agent :51-53, Never Do :162-164 (return anything else as user-must-add), README.md:78, command SKILL.md:51-52, eval scenario :63.
- M1 REOPENED: rule github-workflows-merge-cd.instructions.md:19,45 still forbids prod deploys without `_smoke-test`/`_rollback`, yet the CD examples of publishing (`cd-image.yml`, workflow-callers.md:36-63) and nextjs (`workflow-callers.md`, zero smoke/rollback matches) have none. Concurrency wording is fixed (rule :16 per app and environment). Hint: label those callers "no smoke shown; add per blast-radius" or scope the rule.
- M2 FIXED: Free-private carve-out in security rule :16,32, merge-cd rule :15,20,44 and reviewer :115.
- L1 FIXED: engineer :162 now refers to the write scope, not "Never Do, step 6".
- L2 not re-checked beyond new text (reasons added in updated rules, e.g. security :16); no score change.
- L3 FIXED: README.md:61 uses `ref:refs/heads/main`.
- L4 OPEN (LOW, convention-level): command SKILL.md has no Quick Navigation or three-tier section.
- L5 REOPENED: command evaluation-scenarios.md:13 still asks for prod "required reviewers" on Pro private with no correction expected (F25: public/Enterprise only); `AWS_DEPLOY_ROLE_ARN` is fixed.
- L6 REOPENED: pr-ci rule :14 unchanged while securing `ci-api` grants `pull-requests: write` on `code-security`.

## Cross-skill contracts
- catalog-reference.md: `role-duration-seconds` of login-aws present (:41). NOT current: no `_code-security.yml` row; `_security-scan.yml` (:31) lacks the `environment` input and lists secrets that are now env-read; `_image-publish.yml` (:27) lacks `artifact-name`, still lists `aws-role-arn` and secrets `OCIR_*` (no such input or declared secrets in workflow-image-publish.md:25-35); `_smoke-test.yml` (:30) lists `environment`, removed.

## New findings
- N1 MEDIUM (catalog-reference.md:27,30,31, absent row): the catalog does not match the owners, contrary to its own claim at :17 and the instruction "never add an input the owner does not define". Callers built from it would pass `aws-role-arn`/`secrets` that do not exist and miss `_code-security.yml`. Fix: update the three rows, add `_code-security.yml` (input `targets`; no outputs) and drop `environment` from `_smoke-test.yml`.
- N2 MEDIUM (publishing ecr-ocir.md:16,30; workflow-callers.md:81): `vars.ECR_PUSH_ROLE_ARN` in environment `<env>-publish` is acceptable as a third, push-only role (separation from deploy) but is in no family contract: rule 17 lists only `AWS_PR_ROLE_ARN`/`AWS_DEPLOY_ROLE_ARN`, and no other skill, catalog row or trust-policy blueprint (federating-aws-oidc) mentions it or the `environment:<env>-publish` sub claim. Fix: add the publish role and `<env>-publish` environment to rule 17/family docs and the AWS trust-policy blueprint, or fold it into `AWS_DEPLOY_ROLE_ARN`.
