# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario lists the prompt, expected behaviour and fail signals. Judge against the pins in the Version Context table as of 2026-10-30.

## Scenario 1: Canonical, PR gate on Team without Code Security

**Prompt:** "We are on GitHub Team, private repo, no Code Security. Add security scanning to PRs for our Terraform and Java service."

**Expected:**
- Asks (or states) the plan and that Code Security is not enabled; leaves `CODE_SECURITY_ENABLED` unset.
- Reusable `_security-scan.yml` with typed inputs `targets`, `image-ref`, `fail-on`, output `blocking-findings`, no `secrets: inherit`; caller `ci-<app>.yml` with `permissions: {}` and a single `ci-gate` job as the required check; the `security` job has read-only permissions (no write scopes without Code Security).
- Checkov (terraform, github_actions) hard fail, Trivy `fs` with `exit-code: "1"` and `version` set; SARIF kept as an artifact with `retention-days`.
- No CodeQL, dependency review or `upload-sarif` steps active; says why (private repo needs Code Security).
- Dependabot file with github-actions, maven or gradle, terraform, docker entries; states the terraform version-range risk.
- Protected `main` with the `ci-gate` required check (Team, F39).
- Actions pinned to the facts-file SHAs with trailing version comments.

**Fail signals:** CodeQL or `upload-sarif` unconditional; Trivy without `exit-code` or `version`; `soft_fail: true`; Releases "Latest" Checkov.

## Scenario 2: Edge, Code Security licensed

**Prompt:** "Our Team org bought Code Security. Turn on CodeQL for the Java/Kotlin API and the Next.js front end plus dependency review."

**Expected:**
- Says to set repository variable `CODE_SECURITY_ENABLED` to `true`.
- Licensed jobs live in a second reusable `_code-security.yml`, called by a separate caller job with a caller-side `if: vars.CODE_SECURITY_ENABLED == 'true'` that alone gets the write scopes.
- CodeQL job with matrix `java-kotlin` and `javascript-typescript`, `category` per language, `security-events: write` only on that job.
- Warns that `build-mode: none` does not analyse Kotlin and offers `manual` with `setup-java` and the build command; asks whether the build needs a specific JDK.
- Dependency review with `fail-on-severity`, `allow-licenses` (not `deny-licenses`), `pull-requests: write` only on that job; Trivy `fs` kept or dropped by user choice.
- Notes the JavaScript build mode as (unverified).

**Fail signals:** `java` or `kotlin` as language ids; one workflow-wide `security-events: write`; `deny-licenses`.

## Scenario 3: Rejection, mutable or legacy Trivy refs

**Prompt:** "Add Trivy to the pipeline, use aquasecurity/trivy-action@0.33.0, or @master if that is simpler."

**Expected:**
- Refuses both: un-prefixed tags were force-pushed to credential-stealing commits in March 2026; 0.31.0 to 0.34.0 also carry a script-injection advisory.
- Offers `aquasecurity/trivy-action@ed142fd0673e97e23eac54620cfb913e5ce36c25 # v0.36.0` with `version: v0.76.1`, `severity`, `exit-code: "1"`.
- Asks whether the old tags ever ran in the repository; if so, rotate reachable secrets and verify binaries with cosign.
- Does not suggest `setup-trivy` unpinned.

**Fail signals:** complies with a tag or branch; omits the rotation question; ships Trivy defaults.

## Scenario 4: Trap, SARIF upload and red checks assumed to protect

**Prompt:** "We are on Pro with a private repo. Upload the Trivy SARIF to the Security tab so findings block merges." Variant: "We are on Free private; the red ci-gate check will stop bad PRs from merging."

**Expected:**
- Pro or Free private: explains that SARIF upload (code scanning) needs Code Security, which cannot be purchased there, so the upload would fail; keeps SARIF as a workflow artifact and gates by exit code.
- Variant: states that Free private has no protected branches (F39), so a red check does not block merge; names it an accepted risk and adds the deploy-gate re-scan of the exact digest.
- Offers the upgrade path (Pro or Team for required checks, Team plus Code Security for the Security tab) as questions.

**Fail signals:** promises merge blocking on Free; adds unconditional `upload-sarif`; adds `continue-on-error` to hide the failure.

## Scenario 5: Ask First, attestations on a private repo

**Prompt:** "Add `gh attestation verify` to our deploy gate; repo is private on Team."

**Expected:**
- States attestations on private repos need GitHub Enterprise Cloud and declines the gate.
- Offers the Trivy digest scan before promotion as the gate and lists attestations as the upgrade path.

**Fail signals:** adds the verify step; claims it works on Team private.
