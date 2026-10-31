# Never-do patterns with examples

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Every row has a High-confidence alternative.

Contents: [N1 mutable trivy-action refs](#n1-mutable-or-un-prefixed-trivy-action-refs) | [N2 injectable versions](#n2-trivy-action-0310-to-0340) | [N3 setup-trivy](#n3-unpinned-setup-trivy) | [N4 Trivy defaults](#n4-trivy-defaults-that-gate-nothing) | [N5 stale Checkov](#n5-checkov-version-from-the-releases-badge) | [N6 unlicensed uploads](#n6-code-scanning-features-on-an-unlicensed-private-repo) | [N7 attestations](#n7-attestation-verification-on-team-pro-or-free-private) | [N8 deny-licenses](#n8-deny-licenses) | [N9 PR credentials](#n9-deployable-credentials-on-pull-requests)

## N1 mutable or un-prefixed trivy-action refs

Severity: critical. In March 2026 the un-prefixed tags 0.0.1 to 0.34.2 were force-pushed to credential-stealing commits (GHSA-69fq-xp46-6x23, CVE-2026-33634); every secret reachable by a pipeline that ran them is exposed.

```yaml
# ❌ Wrong
- uses: aquasecurity/trivy-action@0.33.0
- uses: aquasecurity/trivy-action@master
# ✅ Correct
- uses: aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25 # v0.36.0
```

Source: https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23

## N2 trivy-action 0.31.0 to 0.34.0

Severity: high. GHSA-9p44-j4g5-cfx5 (script injection through a sourced env file, fixed in 0.34.1): untrusted input such as a pull request title can run shell code.

```yaml
# ❌ Wrong
- uses: aquasecurity/trivy-action@v0.34.0
# ✅ Correct
- uses: aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25 # v0.36.0
```

Source: https://github.com/aquasecurity/trivy-action/security/advisories/GHSA-9p44-j4g5-cfx5

## N3 unpinned setup-trivy

Severity: critical. `aquasecurity/setup-trivy` tags v0.2.0 to v0.2.6 were replaced in the same incident; use of an unpinned reference was affected. The safe tag named by the advisory is v0.2.6. This skill ships no setup-trivy SHA.

```yaml
# ❌ Wrong
- uses: aquasecurity/setup-trivy@v0.2.5
# ✅ Correct: let trivy-action install Trivy, pinned by SHA with an explicit version
- uses: aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25 # v0.36.0
  with: { version: v0.76.1 }
```

Source: https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23

## N4 Trivy defaults that gate nothing

Severity: high. `exit-code` defaults to `0` and `severity` to all levels, so a green scan can mean no gate.

```yaml
# ❌ Wrong
with: { image-ref: "ghcr.io/org/app:latest" }
# ✅ Correct
with:
  image-ref: "ghcr.io/org/app@sha256:<digest>"
  severity: CRITICAL,HIGH
  exit-code: "1"
  ignore-unfixed: true
```

Source: https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md

## N5 Checkov version from the Releases badge

Severity: high. Releases shows v12.1347.0 as Latest, which pins Checkov 2.0.930. The tags page shows v12.3136.0 pinning Checkov 3.4.0.

```yaml
# ❌ Wrong
- uses: bridgecrewio/checkov-action@v12.1347.0
# ✅ Correct
- uses: bridgecrewio/checkov-action@c10e2438743528f9e4549758fad8b7a62052541d # v12.3136.0
```

Sources: https://github.com/bridgecrewio/checkov-action/tags ; https://github.com/bridgecrewio/checkov-action/releases

## N6 code scanning features on an unlicensed private repo

Severity: moderate. CodeQL, SARIF upload and dependency review need GitHub Code Security on private repositories, which Free and Pro cannot purchase. Unconditional jobs go red for reasons unrelated to findings, and teams then add `continue-on-error`, hiding real failures.

```yaml
# ❌ Wrong
- uses: github/codeql-action/upload-sarif@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
# ✅ Correct
- if: vars.CODE_SECURITY_ENABLED == 'true'
  uses: github/codeql-action/upload-sarif@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
# else keep SARIF as a workflow artifact (actions/upload-artifact)
```

Source: https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security

## N7 attestation verification on Team, Pro or Free private

Severity: moderate. Artifact attestations on Free, Pro and Team are available only for public repositories; private repositories need GitHub Enterprise Cloud.

```bash
# ❌ Wrong: a deploy gate on a Team private repository
gh attestation verify oci://ghcr.io/ORG/IMAGE@sha256:<digest> -R ORG/PRIVATE-REPO
# ✅ Correct: gate on the Trivy digest scan, then promote the same digest
```

Source: https://docs.github.com/en/code-security/getting-started/github-security-features

## N8 deny-licenses

Severity: moderate. `deny-licenses` is deprecated for possible removal in the next major release and is mutually exclusive with `allow-licenses`.

```yaml
# ❌ Wrong
deny-licenses: GPL-3.0, AGPL-3.0
# ✅ Correct
allow-licenses: MIT, Apache-2.0, BSD-3-Clause, ISC
```

Source: https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md

## N9 deployable credentials on pull requests

Severity: high. Branch code runs during pull-request jobs (family rules 7 and 13). Scanning a pull-request image uses a PR-only read role.

```yaml
# ❌ Wrong
scan-pr:
  environment: prod
# ✅ Correct
scan-pr:
  environment: prod-pr      # Pro or Team; on Free use a read-only role trusting pull_request
```

Source: family rules 7 and 13 (family decision).
