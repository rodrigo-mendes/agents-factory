# Licensed jobs: CodeQL, dependency review, SARIF upload

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. These jobs live in their own reusable workflow `./.github/workflows/_code-security.yml`, separate from [_security-scan.yml](./workflow-security-scan.md), so the scan gate (PR and deploy) never needs write scopes. The caller job gates it with `if: vars.CODE_SECURITY_ENABLED == 'true'` and alone grants `security-events: write` and `pull-requests: write` ([callers](./workflow-callers.md#pr-gate)).

Contents: [When these run](#when-these-run) | [Workflow header](#workflow-header) | [CodeQL job](#codeql-job) | [Dependency review job](#dependency-review-job) | [SARIF upload step](#sarif-upload-step) | [Notes](#notes)

## When these run

| Plan | Code Security | Result |
|---|---|---|
| Free private, Pro private | cannot be purchased | variable stays unset, jobs skipped |
| Team private | add-on, optional | set the variable only after enabling it |
| Public repository | included | set the variable to `true` |

Source: https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security (2026-10-30).

## Workflow header

```yaml
# ./.github/workflows/_code-security.yml
name: _code-security
on:
  workflow_call:
    inputs:
      targets: { type: string, default: "code,deps" }   # code = CodeQL, deps = dependency review
permissions: {}
jobs:
```

The jobs below go under `jobs:`. The `vars` check is done by the caller (U9 fallback), so the jobs carry no `vars` condition.

## CodeQL job

```yaml
  codeql:
    if: contains(inputs.targets, 'code')
    runs-on: ubuntu-latest
    timeout-minutes: 60
    permissions: { contents: read, actions: read, security-events: write }
    strategy:
      fail-fast: false
      matrix:
        include:   # delete entries for languages the repository does not contain
          - { language: java-kotlin, build-mode: none }
          - { language: javascript-typescript, build-mode: none }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: github/codeql-action/init@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
        with:
          languages: ${{ matrix.language }}
          build-mode: ${{ matrix.build-mode }}
          queries: security-extended
      - uses: github/codeql-action/analyze@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
        with:
          category: "/language:${{ matrix.language }}"
```

Build modes are `none`, `autobuild`, `manual` (init action v4.39.1). With `none`, Kotlin code is not analysed and a warning is produced; `none` may give less accurate Java results when code is generated during the build.

Manual build for Java, when the build needs a specific JDK (set `build-mode: manual` on that matrix entry):

```yaml
      - if: matrix.build-mode == 'manual'
        uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
        with: { distribution: temurin, java-version: "21" }
      - if: matrix.build-mode == 'manual'
        run: ./mvnw -B -DskipTests package
```

Put the manual steps between `init` and `analyze`. Gradle builds are not covered here: no Gradle action pin is used by this skill.

Sources: https://docs.github.com/en/code-security/code-scanning/creating-an-advanced-setup-for-code-scanning/codeql-code-scanning-for-compiled-languages ; https://raw.githubusercontent.com/github/codeql-action/v4.39.1/init/action.yml (2026-10-30).

## Dependency review job

```yaml
  dependency-review:
    if: contains(inputs.targets, 'deps') && github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions: { contents: read, pull-requests: write }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294 # v5.0.0
        with:
          fail-on-severity: high
          fail-on-scopes: runtime, development
          allow-licenses: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC
          comment-summary-in-pr: on-failure
```

Defaults it overrides: `fail-on-severity: low`, `fail-on-scopes: runtime`, `comment-summary-in-pr: never`. The action runs on node24 and needs runner v2.327.1 or later. Use `allow-licenses`; `deny-licenses` is deprecated and mutually exclusive with it.

Source: https://github.com/actions/dependency-review-action/blob/v5.0.0/README.md (2026-10-30).

## SARIF upload step

Optional. Add to the `scan` job of `_security-scan.yml`, after the artifact upload, to publish the Trivy image results to the Security tab (Checkov and Trivy `fs` SARIF stay artifacts only):

```yaml
      - if: (success() || failure()) && vars.CODE_SECURITY_ENABLED == 'true'
        uses: github/codeql-action/upload-sarif@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
        with:
          sarif_file: trivy-image.sarif
          category: trivy-image
```

The job then needs `security-events: write` and `actions: read`; add them to `scan` permissions only when you enable this step, and grant the same scopes in the caller job that calls `_security-scan.yml` (the deploy gate `scan-image`), only in a Code Security variant.

## Notes

- Input name `sarif_file` is (unverified): `upload-sarif/action.yml` was not opened; confirm before shipping.
- `build-mode: none` for `javascript-typescript` is (unverified): the compiled-languages page covers compiled languages only.
- A SARIF upload to a private repository without Code Security fails with "GitHub Code Security or GitHub Advanced Security must be enabled for this repository to use code scanning."
- Use a distinct `category` per tool so result sets do not overwrite each other.
- `contents: read` is required additionally for workflows in private repositories; `actions: read` is needed for uploads there.

Source: https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/uploading-a-sarif-file-to-github (2026-10-30).
