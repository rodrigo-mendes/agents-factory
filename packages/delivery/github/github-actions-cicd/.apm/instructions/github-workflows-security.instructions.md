---
name: github-workflows-security
description: "Security guardrails for every GitHub Actions workflow file: SHA pins, minimal permissions, keyless cloud login, trigger and injection hygiene. Use when creating, editing or reviewing a file under .github/workflows."
applyTo: "**/.github/workflows/**,**/.github/actions/**"
---

# GitHub Actions workflow security

You review and write workflow files so a compromised action, a fork PR or hostile event text cannot reach cloud credentials. Details live in the skills named below; this rule states what to check on each edit. Tags `(unverified)` and `(medium confidence)` from the skills apply here too.

## Rules

1. Pin every third-party action by full commit SHA with the tag in a trailing comment. Take the SHA from the skill that owns that action, never from memory or doc examples.
2. Declare `permissions:` explicitly: workflow level `contents: read`; widen per job only for what that job needs.
3. `id-token: write` only on the single job that logs in to a cloud.
4. Prefer keyless login (OIDC) over long-lived keys wherever the cloud supports it. Where it does not (OCI default, OCIR, Vercel), keep the key in an environment secret with least privilege. Only in the documented Free private variant (no environments available) is a repository secret allowed, with least privilege and an explicit warning.
5. Pass event data (title, body, branch name, comment, SHAs) through `env:`, never interpolated inside `run:`.
6. Do not combine `pull_request_target` with a checkout of the PR head. Use `pull_request` for untrusted code.
7. Run third-party code (npm, scanners, build) in steps that hold no write token or cloud credential.
8. Scanner supply chain: the Trivy compromise (GHSA-69fq-xp46-6x23, CVE-2026-33634, 2026-03-21) hit unpinned `trivy-action` and `setup-trivy` tags. Pin by SHA from `securing-supply-chain-github-actions`, rotate secrets exposed to affected pipelines.
9. Injection and token-hardening detail: load `automating-github-repos-with-actions`; do not restate it here.

## Load the skill

- `securing-supply-chain-github-actions` for scanners, Dependabot, the Trivy incident and pins.
- `federating-github-actions-aws-oidc` or `federating-github-actions-oci` for cloud login.
- `composing-github-actions-pipelines` for block structure.

## Always Do

- Keep the tag as a trailing comment next to each SHA so Dependabot can update it.
- Scope secrets to environments for anything that can deploy (Free private variant excepted, with warning).
- Set `persist-credentials: false` on checkout unless a later step must push (source and example: `automating-github-repos-with-actions`, always-do patterns).

## Ask First

- Adding a job with `id-token: write` or any write permission.
- Any use of `pull_request_target` or `workflow_run` with secrets.

## Never Do

- Use a floating tag or branch (`@v4`, `@main`) for an action. Alternative: full SHA plus tag comment.
- Put `${{ github.event.* }}` text inside `run:`. Alternative: map it to `env:` and read the variable.
- Check out PR head code under `pull_request_target`. Alternative: `pull_request` with a read-only role.
- Store cloud keys as repository secrets when OIDC is available. Alternative: role trust on environment or `main` ref (`ref:refs/heads/main` in the Free variant).
- Use `secrets: inherit`. Alternative: pass each secret by name.
