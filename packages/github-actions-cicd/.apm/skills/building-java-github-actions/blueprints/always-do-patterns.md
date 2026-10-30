# Always-do patterns with code

Back to [SKILL.md](../SKILL.md). Each rule is one claim with one source. Pins: setup-java v6.1.0, gradle/actions v6.4.1, checkout v7.0.1, upload-artifact v7.0.2. Research date 2026-10-30.

Contents: [A1 JDK pin](#a1-pin-the-jdk) | [A2 Maven flags](#a2-maven-flags-and-phase) | [A3 wrapper](#a3-maven-wrapper) | [A4 caches](#a4-caches) | [A5 Gradle](#a5-gradle) | [A6 artifacts](#a6-artifacts) | [A7 summary](#a7-test-summary) | [A8 PR and publish](#a8-pull-requests-and-publishing) | [A9 promote](#a9-promote-the-same-file)

## A1. Pin the JDK

`distribution` is required and keywords are case-sensitive; use an LTS major (25, 21, 17). Source: https://github.com/actions/setup-java/blob/v6.1.0/README.md

```yaml
- uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
  with:
    distribution: temurin
    java-version: '25'
```

`temurin` and `microsoft` are the only distributions with package signature verification; most others get checksum verification (same page).

## A2. Maven flags and phase

`-B` runs non-interactive, `-ntp` hides transfer progress (https://maven.apache.org/ref/3.10.0/maven-embedder/cli.html); `verify` also runs Failsafe (https://maven.apache.org/surefire/maven-failsafe-plugin/usage.html).

```bash
./mvnw -B -ntp verify
```

## A3. Maven Wrapper

Runners ship Maven 3.9.x; the wrapper pins 3.10.0 (https://github.com/actions/setup-java/blob/v6.1.0/docs/advanced-usage.md). Checksums go in `maven-wrapper.properties` (https://maven.apache.org/tools/wrapper/). Full steps: [Maven blueprint](./maven-build.md#wrapper-pin).

## A4. Caches

setup-java's Maven key hashes `pom.xml` files, `.mvn/wrapper/maven-wrapper.properties` and `.mvn/extensions.xml`. Anyone with read access can read cache contents through a PR, so store no sensitive data in a cache (https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching). Default 10 GB per repository; unused caches evicted after 7 days.

```yaml
- uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
  with: { distribution: temurin, java-version: '25', cache: maven }
```

## A5. Gradle

```yaml
- uses: gradle/actions/setup-gradle@8da46b539cd8fe6ab27ca75128919a18d757604c # v6.4.1
  with:
    cache-provider: basic
- run: ./gradlew build
```

Source: https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md. Wrapper validation is on by default; Gradle's own wrapper page says the action "automatically validates the Wrapper JAR as part of every build" (https://docs.gradle.org/9.8.2/userguide/gradle_wrapper.html). Provider choice: [Gradle blueprint](./gradle-build.md#setup-and-caching).

## A6. Artifacts

Names "must be unique" within a run, so include the matrix value; set `retention-days` (default 90). Report folders: Surefire `target/surefire-reports`, Failsafe `target/failsafe-reports`, Gradle `build/test-results/test`, JaCoCo Maven `target/site/jacoco`, JaCoCo Gradle `build/reports/jacoco/test/html`. Sources: https://github.com/actions/upload-artifact/blob/v7.0.2/README.md, https://docs.github.com/en/actions/tutorials/store-and-share-data.

```yaml
- if: ${{ always() }}
  uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
  with:
    name: test-reports-jdk${{ matrix.java }}
    path: |
      target/surefire-reports/
      target/failsafe-reports/
      target/site/jacoco/
    retention-days: 7
    if-no-files-found: warn
```

`if: always()` as the status check that keeps upload running after a failed test step is (medium confidence); the upload-artifact page does not state it.

## A7. Test summary

Markdown appended to `GITHUB_STEP_SUMMARY` appears on the run summary page; GitHub flavored Markdown; 1 MiB per step; 20 step summaries per job; secrets are masked; an oversized summary fails its upload with an annotation but does not change job status. Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands. The parser step is in [the workflow blueprint](./workflow-java-build.md#workflow); setup-gradle also writes its own Gradle job summary.

## A8. Pull requests and publishing

For fork PRs "secrets are not passed to the runner" and the `GITHUB_TOKEN` is read-only; `GITHUB_SHA` on `pull_request` is the merge commit of the PR ref. Source: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

```yaml
# ./.github/workflows/ci-orders.yml
on: pull_request
permissions:
  contents: read
```

`mvn deploy`, Jib `build` and Lambda updates exist only in `cd-<app>.yml` on the protected branch (fork PRs get no secrets).

## A9. Promote the same file

upload-artifact outputs `artifact-digest`; Maven 3.10.0 makes Reproducible Builds active by default and Gradle 9 archives are reproducible by default (https://maven.apache.org/docs/3.10.0/release-notes.html, https://docs.gradle.org/9.8.2/userguide/upgrading_major_version_9.html). Hand the artifact name and digest to `deploying-aws-lambda`; never rebuild for production. Wiring: [callers](./workflow-callers.md).
