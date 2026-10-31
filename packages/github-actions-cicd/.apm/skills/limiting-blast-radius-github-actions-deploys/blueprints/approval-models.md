# Approval models

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Matrix: [isolation matrix](./isolation-matrix.md). Ask the plan and the model before generating CD (family rule 16).

## Contents

- Default (Pro and Team): ruleset plus main-only environments
- Solo maintainer
- Manual prod dispatch
- Free private variant (weaker)
- Upgrade path

## Default (Pro and Team): ruleset plus main-only environments

The human approval is the pull-request review of the rendered plan or diff before merge to `main`. The required check `ci-gate` is the aggregate job of the PR caller (family name); the plan or diff job of Terraform pipelines is one of the jobs it waits for.

```bash
# Representative; REST API version 2026-03-10
gh api -X POST repos/ORG/REPO/rulesets -H "X-GitHub-Api-Version: 2026-03-10" --input - <<'JSON'
{
  "name": "main-reviewed-deploys",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": false,
        "require_last_push_approval": true,
        "required_review_thread_resolution": true,
        "allowed_merge_methods": ["squash"] } },
    { "type": "required_status_checks", "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [ { "context": "ci-gate" } ] } }
  ]
}
JSON
# Expected: HTTP 201 with the ruleset JSON (id, enforcement "active")
```

Source: https://docs.github.com/en/rest/repos/rules ; https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets

Then restrict each deployable environment to `main`, prefer "selected branches" over "protected branches only":

```bash
gh api -X PUT repos/ORG/REPO/environments/prod -H "X-GitHub-Api-Version: 2026-03-10" --input - <<'JSON'
{ "deployment_branch_policy": { "protected_branches": false, "custom_branch_policies": true } }
JSON
gh api -X POST repos/ORG/REPO/environments/prod/deployment-branch-policies \
  -H "X-GitHub-Api-Version: 2026-03-10" -f name=main -f type=branch
# Expected: {"name":"main","type":"branch",...}; repeat for dev and stage
```

Source: https://docs.github.com/en/rest/deployments/branch-policies

Environment secrets and variables (role ARN, region, app URL) go in the environment, not the repository. The status check `ci-gate` must always run, so keep it as the single aggregate job without path filters (path-filtered required checks stay Pending). Fine-grained token permission names for these calls are (unverified). Create the environments before the first run; whether a workflow auto-creates a missing environment is (unverified).

## Solo maintainer

`require_last_push_approval` needs approval "from someone other than the last person to push", which the only collaborator cannot give. Options, in order:

1. Add a second collaborator (preferred); keep the ruleset unchanged.
2. Set `required_approving_review_count: 0` and keep the required status check; the plan becomes a self-review.
3. Use the manual prod dispatch below.

Bypass lists are not available on user-owned repositories ("only when the repository belongs to an organization"), so do not plan around them.
Source: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches

## Manual prod dispatch

Run prod from `ops-promote-<app>.yml` on `workflow_dispatch`. Running it needs write access; the environment branch policy rejects any ref other than `main`. This adds an explicit go without required reviewers, but any writer may press it. Whether this is acceptable is a user decision (medium confidence).
Source: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow

## Free private variant (weaker)

State this limit in the generated README: "On Free private, any writer can deploy to prod."

| Control | Pro or Team | Free private |
|---|---|---|
| Environments and secrets | yes | not available |
| Branch policy on deploy | environment policy `main` | none server-side |
| Protected `main` | ruleset | not available |
| AWS role trust | `environment:<env>` | `ref:refs/heads/main` |
| Static secrets (OCIR, Vercel) | environment secrets | repository secrets, least privilege, warning |

Design: keep the write-collaborator list minimal; AWS OIDC with the role trust pinned to `sub = repo:ORG/REPO:ref:refs/heads/main` (immutable format for repositories created after 2026-07-15, owned by `federating-github-actions-aws-oidc`); deploy only from `workflow_dispatch` with `if: github.ref == 'refs/heads/main'` (advisory, a writer can edit it); separate dev and prod by account or role. Do not reference `environment:` in Free private workflows; the behaviour is (unverified). Repository secrets are readable by any writer's run, which breaks family rule 10; record it as an accepted risk and recommend Pro or Team.
Source: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments ; https://docs.github.com/en/get-started/learning-about-github/githubs-plans

## Upgrade path

Only for a public repository or GitHub Enterprise: required reviewers (up to six, one approval suffices), `prevent_self_review`, wait timers, "Allow administrators to bypass" off, and artifact attestations (`actions/attest`, v4.2.2, private repositories need Enterprise Cloud). Never the default design.
Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
