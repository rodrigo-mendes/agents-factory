# Gradle: setup-gradle, caching terms, JaCoCo, dependency graph

Back to [SKILL.md](../SKILL.md). Gradle 9.8.2, gradle/actions v6.4.1. Research date 2026-10-30.

Contents: [Setup and caching](#setup-and-caching) | [Wrapper](#wrapper) | [JaCoCo](#jacoco) | [Lambda zip task](#lambda-zip-task) | [Dependency graph](#dependency-graph) | [Migration notes](#migration-notes)

## Setup and caching

The composite [setup-java-build](./composite-setup-java-build.md) runs `gradle/actions/setup-gradle` with `cache-provider: basic`; the build step is `./gradlew build`.

| Provider | Licence and cost | Use |
|---|---|---|
| `basic` | MIT, built on `@actions/cache`, free for all repositories | default here |
| `enhanced` | proprietary `gradle-actions-caching`; "By upgrading to v6, you accept the Terms of Use"; free for public repositories, Free Preview for private ones | only after the user accepts the terms (Ask First) |
| `external` | another tool manages Gradle User Home; better than `cache-disabled` and keeps the job summary accurate | when setup-java or a cache action owns the directory |

Source: https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md and https://github.com/gradle/actions/releases.

- Cache writes come from the default branch; PR runs are read-only by default (same page).
- Making the read-only stance explicit on PRs is a recommendation, because GitHub already scopes PR caches to the merge ref (medium confidence).
- `cache-encryption-key` for configuration-cache data applies only to the `enhanced` provider.
- The Free Preview for private repositories has no stated future pricing on the page: that is why the default is `basic`.

## Wrapper

- setup-gradle validates `gradle-wrapper.jar` against known checksums by default and refuses snapshot wrappers; omit `validate-wrappers` and `allow-snapshot-wrappers`.
- Commit `gradle/wrapper/gradle-wrapper.jar`, `gradle-wrapper.properties`, `gradlew` and `gradlew.bat` (https://docs.gradle.org/9.8.2/userguide/gradle_wrapper.html).
- Upgrade: `./gradlew :wrapper --gradle-version 9.8.2`, run it twice to update all wrapper files.
- Gradle 9 needs a JVM between 17 and 27 to run; Java 25 needs Gradle 9.1.0 or later (https://docs.gradle.org/9.8.2/userguide/compatibility.html).
- A project whose build root is not the repository root: whether setup-gradle takes a build-root input was not checked (unverified).

## JaCoCo

```kotlin
// build.gradle.kts, Gradle 9.8.2
plugins { java; jacoco }
tasks.test { finalizedBy(tasks.jacocoTestReport) }
tasks.jacocoTestReport { dependsOn(tasks.test) }
```

- HTML report: `build/reports/jacoco/test/html`; XML test results: `build/test-results/test`.
- The plugin's default `toolVersion` is 0.8.15 (supports Java 26); raise it with `jacoco { toolVersion = "<version>" }`, taking the current version from https://www.jacoco.org/jacoco/trunk/doc/changes.html (placeholder, not a family fact).
- `jacocoTestCoverageVerification` is not wired into `check` by default.
- JUnit Jupiter needs the Jupiter, Platform and `junit-platform-launcher` (`testRuntimeOnly`) dependencies declared.
- Gradle 9 `test` fails when no tests are discovered; do not blanket-disable with `failOnNoDiscoveredTests = false`.

Source: https://docs.gradle.org/9.8.2/userguide/jacoco_plugin.html, https://docs.gradle.org/9.8.2/userguide/java_testing.html, https://docs.gradle.org/9.8.2/userguide/upgrading_major_version_9.html.

## Lambda zip task

```kotlin
// build.gradle.kts, Gradle 9.8.2 (lazy register API)
tasks.register<Zip>("buildZip") {
    into("lib") {
        from(tasks.jar)
        from(configurations.runtimeClasspath)
    }
}
```

The Kotlin form is a translation of the AWS Groovy snippet and is shown on neither page (medium confidence). Output: `build/distributions/*.zip`; run `./gradlew build buildZip`. Layout and duplicate-class check: [Lambda zip and image hand-off](./lambda-and-image-handoff.md).

## Dependency graph

Dependency review belongs to `securing-supply-chain-github-actions`; this unit only submits the graph. The `cd-` prefix marks a merge-triggered workflow.

```yaml
# ./.github/workflows/cd-dependency-graph.yml
name: cd-dependency-graph
on:
  push:
    branches: [main]
permissions:
  contents: read
concurrency:
  group: cd-dependency-graph
  cancel-in-progress: false
jobs:
  submit:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: write   # dependency submission needs write; only this job
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
        with: { distribution: temurin, java-version: '25' }
      - uses: gradle/actions/dependency-submission@8da46b539cd8fe6ab27ca75128919a18d757604c # v6.4.1
```

- `contents: write` stays on the push job; never grant it to a PR job that runs fork code. For public-fork PRs the docs split a `pull_request` job (`contents: read`) from a `workflow_run` job (`contents: write`) (https://github.com/gradle/actions/blob/v6.4.1/docs/dependency-submission.md).
- v6.4.1 fixes advisory GHSA-chpw-2mqm-95cc in `dependency-submission`; "All users should upgrade".

## Migration notes

- gradle/actions v5 to v6: caching moved to proprietary `gradle-actions-caching`; `cache-provider` added (`enhanced` default, `basic`, and from v6.4.0 `external`); rudimentary configuration-cache support removed.
- v6.4.0: Gradle version support status in annotations and job summary (end-of-life Gradle two or more majors behind warns).
- The v6 Node runtime and removed inputs are not stated on the pages read (unverified).
- Gradle 8.14 to 9.x: daemon needs JVM 17+; Convention API removed; archives reproducible by default; configuration-cache incompatible tasks discard the entry.
