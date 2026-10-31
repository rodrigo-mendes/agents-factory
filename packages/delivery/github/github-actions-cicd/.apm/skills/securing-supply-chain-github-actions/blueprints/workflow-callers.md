# Callers and gates: PR gate, deploy gate, plan variants

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Reusable workflow: [_security-scan.yml](./workflow-security-scan.md).

Contents: [PR gate](#pr-gate) | [Deploy gate](#deploy-gate) | [Plan variants](#plan-variants) | [Notes](#notes)

## PR gate

Pull-request workflows are read-only: no cloud login, no deploy, no shared environment (family rules 7 and 13).

```yaml
# ./.github/workflows/ci-api.yml
name: ci-api
on: { pull_request: { branches: [main] } }
permissions: {}
concurrency:
  group: ci-api-${{ github.event.pull_request.number }}
  cancel-in-progress: true
jobs:
  security:                    # default: read-only, no Code Security needed
    uses: ./.github/workflows/_security-scan.yml
    permissions: { contents: read }
    with:
      targets: "iac,deps"
      fail-on: "CRITICAL,HIGH"
  code-security:               # only with Code Security; the only job with write scopes
    if: vars.CODE_SECURITY_ENABLED == 'true'
    uses: ./.github/workflows/_code-security.yml
    permissions:
      contents: read
      actions: read
      security-events: write   # CodeQL
      pull-requests: write     # dependency review comment
    with:
      targets: "code,deps"
  ci-gate:                     # the single required check
    if: always()
    needs: [security, code-security]
    runs-on: ubuntu-latest
    timeout-minutes: 5
    permissions: {}
    env:
      NEEDS: ${{ toJSON(needs) }}
    steps:
      - run: |
          if echo "$NEEDS" | grep -Eq '"result": "(failure|cancelled)"'; then exit 1; fi
```

| Scanner | PR behaviour | Licence |
|---|---|---|
| Checkov (terraform, github_actions) | hard fail on any failed check | none |
| Trivy `fs` | dependency-review stand-in, exit 1 on `fail-on` severities | none |
| CodeQL, dependency review (`code-security` job) | run when `CODE_SECURITY_ENABLED` is `true`; skipped otherwise, and a skipped need passes `ci-gate` | Code Security |

Trivy `fs` reports every vulnerability in the lockfiles, so a pull request can fail on a finding it did not introduce (medium confidence). Dependabot alerts never block by themselves; their pull requests pass through this gate.

## Deploy gate

The image is scanned by digest before promotion; promotion then uses the same digest (family rule 8). Build and publish are owned by `publishing-container-images-github-actions` (`_image-publish.yml`, GHCR shown; its contract is in that skill). Its output `image-ref` already ends in `@sha256:<digest>`, so the scan takes it as is. Promotion is owned by the images and federation skills.

```yaml
# ./.github/workflows/cd-api.yml  (excerpt)
jobs:
  publish:
    uses: ./.github/workflows/_image-publish.yml
    permissions: { contents: read, packages: write }
    with: { registry: ghcr, image-name: acme/api, push: true }
  scan-image:
    needs: [publish]
    uses: ./.github/workflows/_security-scan.yml
    permissions: { contents: read }   # licensed jobs are not called here
    with:
      targets: "image"
      image-ref: ${{ needs.publish.outputs.image-ref }}   # repo@sha256:...
      fail-on: "CRITICAL,HIGH"
      environment: staging            # holds the pull secrets; empty on Free
  promote:
    needs: [publish, scan-image]      # a failed scan stops promotion
    # promotes the same image-ref, never rebuilds
```

The pull credential is a read-only registry token scoped to pulling; never reuse a push or deploy credential. On Pro and Team it is an environment secret (`REGISTRY_PULL_USER`, `REGISTRY_PULL_TOKEN`, family rule 10) read inside the scan job. On Free private there are no environments (F25): pass an empty `environment`, store both as repository secrets and warn the user that any workflow in the repository can read them. Cloud logins for promotion are owned by the AWS and OCI federation skills.

## Plan variants

Family rule 16. Ask which plan owns the repository before generating anything.

| Variant | Gate enforcement | Code Security | Notes |
|---|---|---|---|
| Default: Pro or Team private | protected `main`, required status check `ci-gate`, PR review before merge (F39) | Team only, optional | environments with `main` branch policy for promotion (F25) |
| Weaker: Free private | none: no protected branches (F39), no environments (F25) | cannot be purchased | red checks do not block merge |
| Public, or Enterprise | as default | included | attestations become possible (F33) |

Free private accepted risk: a pull request can be merged with a red `ci-gate`. The deploy gate therefore re-scans the exact digest before promotion, so a vulnerable image cannot deploy even if the pull request merged red. Say this to the user; never present the PR check as a merge control on Free. The registry pull token is a repository secret there, with least privilege and the warning above.

Source: https://docs.github.com/en/get-started/learning-about-github/githubs-plans (2026-10-30).

## Notes

- Required reviewers, wait timers and artifact attestations are an upgrade path only: they need public repositories or Enterprise plans.
- The single always-running `ci-gate` job as the only required check is a design (medium confidence); the pending-check behaviour behind it is documented.
- A path-filtered caller leaves its required check pending; keep the `ci-gate` job unfiltered.
- Fork pull requests receive a read-only token and no secrets; the scan job needs neither for Checkov or Trivy `fs`.
- Whether rulesets or required status checks exist on Free private repositories is not stated by the pages read; F39 governs (medium confidence).
- Attestation verification with `gh attestation verify` applies only to public repositories or GitHub Enterprise Cloud; it is not a gate on Team, Pro or Free private.
