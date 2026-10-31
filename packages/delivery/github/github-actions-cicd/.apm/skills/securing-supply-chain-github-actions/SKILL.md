---
name: securing-supply-chain-github-actions
description: "Secures GitHub Actions supply chains on Team, Pro and Free private repos: Checkov and Trivy exit-code gates, Dependabot, CodeQL and dependency review when Code Security is licensed. Use when adding security scans, reviewing pipelines or responding to the Trivy compromise."
---

# Supply-chain security in GitHub Actions (Team, Pro, Free private)

> Version lock: every claim applies to the pins in the table below on GitHub.com Actions. Research date **2026-10-30**.
> Claims tagged unverified or medium confidence were not fully confirmed against an official page; each tag maps to the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: scanners, scan gates and Dependabot. SHA pinning and injection-safe scripting belong to `automating-github-repos-with-actions`; `workflow_call` mechanics to `composing-github-actions-pipelines`; image build and attestation generation to `publishing-container-images-github-actions`.
> Provenance: the dated research file for this unit under the factory workspace; this skill never reads it at run time.

## Version Context

| Item | Value | Source (fetched 2026-10-30) |
|---|---|---|
| `bridgecrewio/checkov-action` | v12.3136.0 = `c10e2438743528f9e4549758fad8b7a62052541d`, runs Checkov 3.4.0; tag only, the Releases "Latest" is stale | https://github.com/bridgecrewio/checkov-action/tags |
| `aquasecurity/trivy-action` | v0.36.0 = `ed142fd0673e97e23eac54620cfb913e5ce36c25`; default Trivy v0.70.0 | https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md |
| Trivy CLI (set via `version`) | v0.76.1 latest | https://github.com/aquasecurity/trivy/releases |
| `github/codeql-action` | v4.39.1 = `9b3254085494b55a0f7c4c2b3d2d52cc712ce370` | https://github.com/github/codeql-action/blob/v4.39.1/README.md |
| `actions/dependency-review-action` | v5.0.0 = `a1d282b36b6f3519aa1f3fc636f609c47dddb294`; runner v2.327.1 or later | https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md |
| `actions/checkout` | v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1` | https://github.com/actions/checkout/releases |
| `actions/upload-artifact` | v7.0.2 = `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | https://github.com/actions/upload-artifact/releases |
| `actions/setup-java` | v6.1.0 = `b843ebf9b913146b38da2eaa7aeddf76074ae1ad` (CodeQL manual build only) | https://github.com/actions/setup-java/releases |
| Plan availability | Code Security (CodeQL, SARIF upload, dependency review) purchasable on Team and Enterprise only | https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security |

**Version-lifetime risk** (as of 2026-10-30; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Trivy v0.76.1 is a security release published 2026-10-21 and trivy-action had an active incident in 2026; re-read the advisories before moving a pin.
- Dependabot lists Terraform support to 1.15.x while the family pins 1.17.1.
- Pinned SHAs go stale; re-resolve them with `git ls-remote` before every bump.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Reusable workflow _security-scan.yml](./blueprints/workflow-security-scan.md)
- [Licensed jobs: CodeQL, dependency review, SARIF upload](./blueprints/workflow-licensed-jobs.md)
- [Callers, PR gate, deploy gate, plan variants](./blueprints/workflow-callers.md)
- [Dependabot configuration](./blueprints/dependabot-config.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [Verification Loop](#verification-loop)
- [External Resources](#external-resources)

## Blueprints & Guardrails

Shape: one reusable `./.github/workflows/_security-scan.yml` (inputs `targets`, `image-ref`, `fail-on`; output `blocking-findings`) called from `ci-<app>.yml` (PR gate, required check `ci-gate`) and `cd-<app>.yml` (digest gate on the `image-ref` of `_image-publish.yml` before promotion). Checkov and Trivy fail by exit code with no licence; SARIF stays a workflow artifact. CodeQL and dependency review sit in a separate `_code-security.yml`, called only when the repository variable `CODE_SECURITY_ENABLED` is `true`, so only that caller job gets write scopes. Dependabot covers every ecosystem on every plan.

### ✅ Always Do

- **Pin `aquasecurity/trivy-action` by the full SHA of v0.36.0** ([advisory](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)).
- **Set the Trivy `version` input explicitly**; the action defaults to v0.70.0 ([README v0.36.0](https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md)).
- **Set `exit-code: "1"` and `severity` on every Trivy gate step**; the default exit code is 0 ([README v0.36.0](https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md)).
- **Scan the exact image digest that will be promoted** (family decision, build once and promote the same artifact).
- **Rotate every secret reachable by a pipeline that ran an affected trivy-action tag** ([advisory](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)).
- **Verify Trivy binaries with cosign** as the advisory instructs ([advisory](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)).
- **Leave Checkov `soft_fail` unset** so failed checks fail the job ([action.yml v12.3136.0](https://raw.githubusercontent.com/bridgecrewio/checkov-action/v12.3136.0/action.yml)).
- **Take the checkov-action version from the tags page**, not the Releases badge ([tags](https://github.com/bridgecrewio/checkov-action/tags)).
- **Skip Checkov checks by check ID with `skip_check`** ([README v12.3136.0](https://github.com/bridgecrewio/checkov-action/blob/v12.3136.0/README.md)).
- **Gate `upload-sarif` with `vars.CODE_SECURITY_ENABLED`**; private repositories need a Code Security licence ([SARIF docs](https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/uploading-a-sarif-file-to-github)).
- **Grant `security-events: write` only to jobs that upload SARIF or run CodeQL** ([codeql-action README v4.39.1](https://github.com/github/codeql-action/blob/v4.39.1/README.md)).
- **Keep scan SARIF as a workflow artifact with `retention-days`** (family decision; [upload-artifact](https://github.com/actions/upload-artifact/releases)).
- **Use `java-kotlin` and `javascript-typescript` as CodeQL language identifiers** ([customizing advanced setup](https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/customizing-your-advanced-setup-for-code-scanning)).
- **Set `fail-on-severity` and `allow-licenses` on dependency review** ([README v5.0.0](https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md)).
- **Commit one `.github/dependabot.yml` listing every ecosystem in the repository** ([options reference](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference)).
- **Run pull-request scan jobs with read-only permissions and no deployable credentials** (family decision, rules 7 and 13).

Code for each rule: [always-do patterns](./blueprints/always-do-patterns.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Plan and Code Security | Free, Pro: only Checkov, Trivy, Dependabot. Team: add Code Security (CodeQL, dependency review, SARIF upload) or stay on the free stack | "Which GitHub plan owns the repository, and is Code Security enabled?" |
| SAST without a licence | none offered; CodeQL CLI licence terms for private code are (unverified) | "Is a paid Code Security add-on acceptable?" |
| CodeQL build mode | `none` (Kotlin not analysed) vs `manual` with `setup-java` and the build command | "Does the Java build need a specific JDK or generated sources?" |
| Dependency stand-in | Trivy `fs` reports all lockfile vulnerabilities, not only those added by the PR (medium confidence) | "Is a failing PR on a pre-existing finding acceptable?" |
| Checkov invocation | Docker action vs `pip install`; the action needing a Linux runner is (unverified) | "Are runners Linux, and is a PyPI-pinned install preferred?" |
| Checkov skips | by check ID (default); inline suppression syntax is (unverified); severity thresholds without a platform key are (unverified) | "Who approves each skipped check ID?" |
| Severity and ignore policy | CRITICAL only, CRITICAL+HIGH (default), all; `.trivyignore` entries with `exp:` dates (medium confidence) | "What severity blocks, and who owns ignore entries?" |
| Gate job | one always-running required check (medium confidence) vs one required check per scanner | "Are scanners path-filtered?" |
| Free private | no protected branches on private repos; red checks do not block merge (medium confidence); the deploy gate re-scans | "Is that accepted risk, or should the plan change?" |
| Dependabot terraform | support to 1.15.x vs Terraform 1.17.1 (unverified) | "Keep the entry and bump providers by hand if skipped?" |
| Dependabot SHA pins | Dependabot refreshes SHA and `# vX` comment (medium confidence) | "Is Dependabot enabled for github-actions?" |
| Registry pull credential | read-only token as environment secret on Pro and Team; repository secret with a warning on Free | "Which token scope can the scan use?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Reference trivy-action by an un-prefixed legacy tag or `master` ([GHSA-69fq-xp46-6x23](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)) | the v0.36.0 full SHA with `# v0.36.0` |
| Use trivy-action 0.31.0 to 0.34.0 ([GHSA-9p44-j4g5-cfx5](https://github.com/aquasecurity/trivy-action/security/advisories/GHSA-9p44-j4g5-cfx5)) | the v0.36.0 SHA |
| Use `setup-trivy` unpinned ([GHSA-69fq-xp46-6x23](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)) | trivy-action pinned by SHA with `version` |
| Rely on Trivy default `exit-code` and `severity` ([README](https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md)) | `exit-code: "1"`, `severity: CRITICAL,HIGH` |
| Take Checkov from the Releases "Latest" badge ([tags](https://github.com/bridgecrewio/checkov-action/tags)) | the v12.3136.0 SHA |
| Run CodeQL, `upload-sarif` or dependency review unconditionally on a private repo ([plans](https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security)) | gate with `CODE_SECURITY_ENABLED`; keep SARIF as an artifact |
| Gate on `gh attestation verify` for Team, Pro or Free private ([security features](https://docs.github.com/en/code-security/getting-started/github-security-features)) | Trivy digest scan, then promote the same digest |
| Use `deny-licenses` ([README v5.0.0](https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md)) | `allow-licenses` |
| Run scanners with deployable-environment credentials on pull requests (family decision, rules 7 and 13) | a PR-only read role or environment |

Examples with alternatives: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Available on every plan | dependency graph, SBOM export, Dependabot alerts, security updates, version updates | https://docs.github.com/en/code-security/getting-started/github-security-features |
| Needs Code Security (private) | code scanning, SARIF upload, dependency review | https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security |
| Attestations on private repos | GitHub Enterprise Cloud only | https://docs.github.com/en/code-security/getting-started/github-security-features |
| Trivy defaults | `exit-code` 0, all severities, `version` v0.70.0 | https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md |
| Dependency review defaults | `fail-on-severity` low, `fail-on-scopes` runtime, `comment-summary-in-pr` never | https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md |
| Dependabot cooldown | 3 days for version updates, not security updates | https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference |
| Protected branches on private repos | Pro and Team | https://docs.github.com/en/get-started/learning-about-github/githubs-plans |

## Verification Loop

Representative commands; run from the repository root (offline, no network).

```bash
# 1. Every third-party action pinned by a 40-character SHA with a trailing version comment
grep -rEn 'uses: [^.][^@]+@' .github/workflows | grep -vE '@[0-9a-f]{40} # v'
# Expected: no output

# 2. No mutable trivy-action refs
grep -rEn 'aquasecurity/trivy-action@(master|main|v?[0-9])' .github/workflows
# Expected: no output

# 3. Each Trivy step fails the job
grep -rn -A14 'aquasecurity/trivy-action@' .github/workflows | grep -c 'exit-code: "1"'
# Expected: equals the number of trivy-action steps

# 4. Checkov not soft-failing
grep -rn 'soft_fail: true' .github/workflows
# Expected: no output (or a documented exception)

# 5. Dependabot covers github-actions
grep -n 'package-ecosystem: github-actions' .github/dependabot.yml
# Expected: one match

# 6. SARIF uploads are licence-gated
grep -rn -B3 'codeql-action/upload-sarif@' .github/workflows | grep -c 'CODE_SECURITY_ENABLED'
# Expected: equals the number of upload-sarif steps
```

Scanners are tested with fixtures (a Terraform file with a known-bad resource must fail Checkov; an old base image must make Trivy exit 1) on `workflow_dispatch` in a sandbox repository (medium confidence).

## External Resources

All fetched 2026-10-30.

- [About GitHub Advanced Security plans](https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security)
- [Security features by plan](https://docs.github.com/en/code-security/getting-started/github-security-features)
- [Trivy compromise advisory](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
