# Reusable workflow: _security-scan.yml

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Licensed jobs (CodeQL, dependency review, SARIF upload): [licensed jobs](./workflow-licensed-jobs.md). Callers: [callers and gates](./workflow-callers.md).

Contents: [Contract](#contract) | [Scan job](#scan-job) | [Notes](#notes)

## Contract

| Item | Value |
|---|---|
| Path | `./.github/workflows/_security-scan.yml` (reusable workflows cannot sit in subfolders, F16) |
| Input `targets` | string, comma list of `deps`, `code`, `iac`, `image` |
| Input `image-ref` | string, `repo@sha256:<64 hex>`; required when `targets` has `image` |
| Input `fail-on` | string, Trivy severities that block, default `CRITICAL,HIGH` |
| Input `environment` | string, default empty; the deploy gate passes the environment that holds `REGISTRY_PULL_USER` and `REGISTRY_PULL_TOKEN` (Pro and Team); empty on PR runs and on Free private |
| Secrets | none declared; the `scan` job reads `secrets.REGISTRY_PULL_USER` and `secrets.REGISTRY_PULL_TOKEN` from its environment (family rule 10), image scans only |
| Output `blocking-findings` | `true` when Checkov or Trivy found blocking issues in the `scan` job |

Checkov and Trivy gate by exit code and need no licence. Each scanner step uses `continue-on-error`, so SARIF is always uploaded as an artifact; the `verdict` step then fails the job.

## Scan job

```yaml
# ./.github/workflows/_security-scan.yml  (Trivy CLI v0.76.1, trivy-action v0.36.0)
name: _security-scan
on:
  workflow_call:
    inputs:
      targets: { type: string, required: true }
      image-ref: { type: string, default: "" }
      fail-on: { type: string, default: "CRITICAL,HIGH" }
      environment: { type: string, default: "" }
    outputs:
      blocking-findings:
        description: "true when Checkov or Trivy reported blocking findings"
        value: ${{ jobs.scan.outputs.blocking }}
permissions: {}
jobs:
  scan:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    environment: ${{ inputs.environment }}
    permissions: { contents: read }
    outputs:
      blocking: ${{ steps.verdict.outputs.blocking }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Require a digest reference
        if: contains(inputs.targets, 'image')
        env: { IMAGE_REF: "${{ inputs.image-ref }}" }
        run: |
          [[ "$IMAGE_REF" =~ @sha256:[0-9a-f]{64}$ ]] || { echo "::error::image-ref must end with @sha256:<digest>"; exit 1; }
      - id: checkov
        if: contains(inputs.targets, 'iac')
        continue-on-error: true
        uses: bridgecrewio/checkov-action@c10e2438743528f9e4549758fad8b7a62052541d # v12.3136.0
        with:
          directory: .
          framework: terraform,github_actions
          output_format: cli,sarif
          output_file_path: console,checkov.sarif
          quiet: true
      - id: trivy-fs
        if: contains(inputs.targets, 'deps')
        continue-on-error: true
        uses: aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25 # v0.36.0
        with:
          version: v0.76.1
          scan-type: fs
          scan-ref: .
          scanners: vuln,secret
          severity: ${{ inputs.fail-on }}
          ignore-unfixed: true
          exit-code: "1"
          format: sarif
          output: trivy-fs.sarif
          limit-severities-for-sarif: true
      - id: trivy-image
        if: contains(inputs.targets, 'image')
        continue-on-error: true
        env:
          TRIVY_USERNAME: ${{ secrets.REGISTRY_PULL_USER }}
          TRIVY_PASSWORD: ${{ secrets.REGISTRY_PULL_TOKEN }}
        uses: aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25 # v0.36.0
        with:
          version: v0.76.1
          scan-type: image
          image-ref: ${{ inputs.image-ref }}
          severity: ${{ inputs.fail-on }}
          ignore-unfixed: true
          exit-code: "1"
          format: sarif
          output: trivy-image.sarif
          limit-severities-for-sarif: true
      - if: always()
        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: scan-sarif-${{ github.run_attempt }}-${{ inputs.targets }}
          path: |
            checkov.sarif
            trivy-fs.sarif
            trivy-image.sarif
          retention-days: 14
      - id: verdict
        if: always()
        env:
          R_CHECKOV: ${{ steps.checkov.outcome }}
          R_FS: ${{ steps.trivy-fs.outcome }}
          R_IMAGE: ${{ steps.trivy-image.outcome }}
        run: |
          blocking=false
          for r in "$R_CHECKOV" "$R_FS" "$R_IMAGE"; do [ "$r" = failure ] && blocking=true; done
          echo "blocking=$blocking" >> "$GITHUB_OUTPUT"
          [ "$blocking" = false ] || { echo "::error::blocking findings, see the SARIF artifact"; exit 1; }
```

The `code` target and dependency review live in a separate reusable workflow, `_code-security.yml`, see [licensed jobs](./workflow-licensed-jobs.md).

## Notes

- An empty `environment` value on the Free private variant (no environments, F25) means the two secrets are repository secrets; see the warning in [callers](./workflow-callers.md#deploy-gate).
- Trivy `version` is explicit because the action defaults to Trivy v0.70.0 while the latest is v0.76.1 (F41).
- `scan-ref` is the filesystem path input (unverified); confirm in the action's `action.yml` at v0.36.0 before relying on it.
- Scanning `repo@sha256:` as `image-ref` is (medium confidence): the README shows tag references only.
- `TRIVY_USERNAME` and `TRIVY_PASSWORD` reaching the action's process are (unverified); the fallback is a login step in the same job.
- `vars` use inside a called workflow is (unverified); this skill avoids it by evaluating `vars.CODE_SECURITY_ENABLED` in the caller-side `if` of the `_code-security.yml` job.
- A called workflow can only narrow the caller's token permissions, so the caller job must grant the union of the called jobs' permissions (unverified). `_security-scan.yml` needs only `contents: read`, so both callers grant just that.
- The `framework: terraform,github_actions` comma list is (medium confidence): the CLI documents the values, the action input does not.
- Trivy `fs` is the dependency-review stand-in; it reports all lockfile vulnerabilities, not only those added by the pull request (medium confidence).
- Findings appear only in the SARIF artifact for Trivy (format `sarif` writes no console table); the job log shows the verdict.
- Checkov: leave `soft_fail` unset (hard fail); skip by check ID with `skip_check`, see [always-do patterns](./always-do-patterns.md#checkov-skips-by-check-id).
