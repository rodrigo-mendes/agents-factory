# Never-do patterns (GitHub.com Actions, as of 2026-10-29)

Back to [SKILL.md](../SKILL.md). Every row has an alternative. N6 and N7 carry a tag. Sources fetched 2026-10-29.

## N1 Inline event text in run (severity critical)

The expression is substituted into the script before it executes, so a PR title such as `a"; ls $GITHUB_WORKSPACE"` runs. Impact: arbitrary commands with the job's token and secrets.

```yaml
# ❌ run: echo "${{ github.event.comment.body }}" | python3 tools/parse.py
# ✅
env:
  COMMENT_BODY: ${{ github.event.comment.body }}
run: printf '%s' "$COMMENT_BODY" | python3 tools/parse.py
```

Source: https://docs.github.com/en/actions/reference/security/secure-use ; https://docs.github.com/en/actions/concepts/security/script-injections

## N2 GITHUB_TOKEN for Projects (severity high)

"`GITHUB_TOKEN` is scoped to the repository level and cannot access projects." Every project call fails.

```yaml
# ❌ env: { GH_TOKEN: "${{ secrets.GITHUB_TOKEN }}" }
# ✅ env: { GH_TOKEN: "${{ steps.app-token.outputs.token }}" }
```

Source: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions

## N3 Fine-grained PAT for a user-owned project (severity high)

The PAT page lists fine-grained access to "Projects owned by a user account" as a gap. Use a classic PAT with `project` + `repo` and the risk warning in [tokens](./tokens-app-and-pat.md#classic-pat-for-user-owned-projects). Source: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

## N4 pull_request_target that runs PR code (severity critical)

It runs "in the context of the default branch of the base repository" with secrets; "Avoid using this event if you need to build or run code from the pull request". Checkout v7 refuses fork PR code there unless `allow-unsafe-pr-checkout: true`.

```yaml
# ❌ on: pull_request_target  + checkout of the PR head + run build
# ✅ on: pull_request        # fork PRs get a read-only token and no secrets
```

Sources: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows ; https://github.blog/changelog/2026-06-18-safer-pull_request_target-defaults-for-github-actions-checkout/

## N5 Mutable tag references (severity high)

Tags and branches can move after review: "Pin actions to a tag only if you trust the creator."

```yaml
# ❌ uses: actions/create-github-app-token@v3
# ✅ uses: actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510  # v3.3.0
```

Source: https://docs.github.com/en/actions/reference/security/secure-use

## N6 Writer without a loop guard (severity high, medium confidence)

Only events created with `GITHUB_TOKEN` are exempt from starting new runs; comments or labels written with an App token or PAT can retrigger the same workflow (inferred, medium confidence). Impact: comment storms and rate-limit exhaustion.

```yaml
# ❌ on: issue_comment, job posts a comment with the App token, no guard
# ✅
if: ${{ github.event.comment.user.login != 'my-app[bot]' }}
concurrency: { group: "reply-${{ github.event.issue.number }}", cancel-in-progress: false }
```

Source: https://docs.github.com/en/actions/concepts/security/github_token

## N7 user.type as the only bot check (severity medium, unverified)

The REST schema documents `user.type` only as a string; the value for App-authored comments is not enumerated (unverified). Compare `github.event.comment.user.login` with the exact bot login `<slug>[bot]` instead. Source: https://docs.github.com/en/rest/issues/comments

## N8 Plaintext or structured secrets (severity critical)

"Sensitive data should never be stored as plaintext in workflow files"; "Never use structured data as a secret" because redaction is an exact match.

```yaml
# ❌ GH_TOKEN: ghp_xxxxxxxx      (or one JSON secret holding client id and key)
# ✅ client-id: ${{ vars.APP_CLIENT_ID }}   private-key: ${{ secrets.APP_PRIVATE_KEY }}
```

Source: https://docs.github.com/en/actions/reference/security/secure-use

## N9 Path filters on a required check (severity medium)

A workflow skipped by a path or branch filter leaves its checks "Pending" and blocks merging; a job skipped by a conditional reports success.

```yaml
# ❌ on: pull_request: paths: ['src/**']   (docs-only PR stays Pending)
# ✅ no workflow filter; job-level if: for the expensive work
```

Source: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks
