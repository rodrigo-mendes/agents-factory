# Test P6 r2 - composing-github-actions-pipelines (S1, S4)

Own-context simulation, 2026-10-30. S1 PASS, S4 PASS. Score 97 (1 MEDIUM new, 1 LOW reopened).

| r1 finding | Status | Evidence |
|---|---|---|
| D-1 HIGH `_java-build.yml` call | FIXED | monorepo-ci-gate.md:57-63 `tool: maven`, `working-directory: services/api`, `package: jar`; :84 states owner inputs; catalog-reference.md:23-24 real inputs and outputs `artifact-name`, `artifact-digest` |
| D-2 LOW `_node-build` dist path | FIXED | no `/dist` left; catalog :24 matches owner (`app-dir`, `mode`, `retention-days`) |
| D-3 LOW "list secrets once" | REOPENED (LOW) | no text in SKILL.md or central-blocks-repo.md; scenario 3 still expects it |

## Catalog checks asked in the brief
- `role-duration-seconds` of login-aws: present (catalog :41) and matches owner (login-composite-action.md:30,42,47). OK.
- `artifact-name` of `_image-publish.yml`: owner defines it (workflow-image-publish.md:35) but catalog :27 does NOT list it. Missing.
- `environment` of `_security-scan.yml`: owner defines it (workflow-security-scan.md:15,32) but catalog :31 does NOT list it. Missing.
- `_code-security.yml`: absent from the catalog, although the owner defines it (workflow-licensed-jobs.md:21-25, input `targets`). Missing.

## New findings
- N-1 (MEDIUM) catalog-reference.md:27,31 still contradict owners and the page says "never add an input the owner does not define" (:17). `_image-publish.yml` row lists `aws-role-arn` (not an input; owner reads `vars.ECR_PUSH_ROLE_ARN` in the job) and secrets `OCIR_USERNAME`, `OCIR_AUTH_TOKEN` (owner declares no secrets, workflow-image-publish.md:10); `_security-scan.yml` row lists secrets `registry-username`, `registry-password` (owner declares none, reads `REGISTRY_PULL_*` from its environment, workflow-security-scan.md:16). A caller built from the catalog fails or leaks credentials through the wrong channel. Fix: rewrite both rows from the owners, add `artifact-name`, `environment`, and a `_code-security.yml` row (`targets`; caller-side `if` on `vars.CODE_SECURITY_ENABLED`).

## Publish role (rule 17 gap)
`<env>-publish` + `vars.ECR_PUSH_ROLE_ARN` (images: registry-credentials.md:21-22, workflow-callers.md:81,94, workflow-image-publish-ecr-ocir.md:30,66). Verdict: acceptable third role (push-only, separate from deploy and PR, consistent with rule 13 and least privilege), not a defect in the images skill. But it is documented only in the images skill: rule 17 and the AWS OIDC skill (trust shape `environment:<env>-publish`, owner of the trust format that images defers to) do not name it, and the catalog does not mention the environment. Other skills (terraform, blast-radius, composing, OCI) do not refer to it. LOW doc gap: add one line to rule 17 and a trust-policy row in aws-oidc.
