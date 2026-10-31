# Always-do patterns with code

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Full workflows: [scan](./workflow-security-scan.md), [licensed jobs](./workflow-licensed-jobs.md), [callers](./workflow-callers.md), [Dependabot](./dependabot-config.md).

Contents: [Pin Trivy](#pin-trivy-by-full-sha) | [Trivy version](#explicit-trivy-version) | [Trivy gate](#trivy-gate-that-fails) | [Digest scan](#scan-the-promoted-digest) | [Checkov hard fail](#checkov-hard-fail) | [Checkov version](#checkov-version-from-the-tags-page) | [Checkov skips](#checkov-skips-by-check-id) | [SARIF handling](#sarif-handling) | [Permissions](#minimal-permissions) | [CodeQL languages](#codeql-language-identifiers) | [Dependency review](#dependency-review-policy) | [After a compromise](#after-a-compromise)

## Pin Trivy by full SHA

```yaml
- uses: aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25 # v0.36.0
```

The 2026 compromise force-pushed 76 of 77 tags; only a full SHA is immutable. General SHA-pinning rules: see `automating-github-repos-with-actions`.
Source: https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23

## Explicit Trivy version

```yaml
with:
  version: v0.76.1   # the action defaults to v0.70.0
```

Source: https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md

## Trivy gate that fails

```yaml
with:
  severity: CRITICAL,HIGH
  exit-code: "1"           # default 0 never fails the job
  ignore-unfixed: true
```

Defaults are `exit-code: 0` and all severities, so an unconfigured scan gates nothing.
Source: https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md

## Scan the promoted digest

```yaml
image-ref: ${{ needs.build.outputs.image }}@${{ needs.build.outputs.digest }}
```

A tag can move between scan and promotion; a digest cannot (family decision, build once and promote the same artifact).

## Checkov hard fail

```yaml
- uses: bridgecrewio/checkov-action@c10e2438743528f9e4549758fad8b7a62052541d # v12.3136.0
  with:
    directory: .
    framework: terraform,github_actions
    # soft_fail not set: any failed check fails the job
```

`soft_fail` means "do not return an error code if there are failed checks"; unset is a hard fail.
Source: https://raw.githubusercontent.com/bridgecrewio/checkov-action/v12.3136.0/action.yml

## Checkov version from the tags page

Resolve checkov-action from https://github.com/bridgecrewio/checkov-action/tags. v12.3136.0 (2026-10-28) runs Checkov 3.4.0; the Releases "Latest" badge shows v12.1347.0 with Checkov 2.0.930.

## Checkov skips by check ID

```yaml
with:
  skip_check: CKV_<ID>,CKV2_<ID>   # one reviewed ID per entry, with a comment saying why
```

Skip by ID, never by disabling a framework or setting `soft_fail`. `hard_fail_on` and `soft_fail_on` also take check IDs.
Source: https://github.com/bridgecrewio/checkov-action/blob/v12.3136.0/README.md

## SARIF handling

```yaml
- if: always()
  uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
  with: { name: scan-sarif, path: "*.sarif", retention-days: 14 }
- if: (success() || failure()) && vars.CODE_SECURITY_ENABLED == 'true'
  uses: github/codeql-action/upload-sarif@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
  with: { sarif_file: trivy-image.sarif, category: trivy-image }
```

Private repositories need a GitHub Code Security licence to upload SARIF; keep the artifact as the default record. Set a distinct `category` per tool. `sarif_file` is (unverified), see the [register](./unverified-and-risks.md#unverified-11).
Source: https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/uploading-a-sarif-file-to-github

## Minimal permissions

```yaml
permissions: {}              # workflow default
jobs:
  scan:
    permissions: { contents: read }
  codeql:
    permissions: { contents: read, actions: read, security-events: write }
```

`security-events: write` is required by advanced-setup code scanning; private repositories also need `contents: read`.
Source: https://github.com/github/codeql-action/blob/v4.39.1/README.md

## CodeQL language identifiers

Use `java-kotlin` and `javascript-typescript` in `languages:`; Kotlin needs a build, so `build-mode: none` skips Kotlin with a warning.
Source: https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/customizing-your-advanced-setup-for-code-scanning

## Dependency review policy

```yaml
with:
  fail-on-severity: high
  allow-licenses: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC
  comment-summary-in-pr: on-failure   # needs pull-requests: write
```

Source: https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md

## After a compromise

If any pipeline ran an un-prefixed `aquasecurity/trivy-action` tag below 0.35.0 on 2026-03-19 or 2026-03-20, rotate every secret that pipeline could read, then re-pin by SHA. Verify Trivy binaries with cosign as the advisory instructs.
Source: https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23
