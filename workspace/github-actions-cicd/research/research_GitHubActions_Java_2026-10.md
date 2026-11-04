# Research: Java builds on GitHub Actions (setup-java v6.1.0, Maven 3.10, Gradle 9.8 via gradle/actions v6.4.1, JDK 25/21/17)

> Unit: `building-java-github-actions`. Source item: "Java: Maven->image, Maven->Lambda zip, Gradle, CI only".
> Spec: `researching-technical-frameworks` (default depth = exhaustive, MAX_ITERATIONS = 5).
> Brief: `workspace/github-actions-cicd/execution-1/briefs/P4-research-building-java-github-actions.md`.
> Every page was read on 2026-10-30. Family facts F1-F24 and family rules 1-16
> (`workspace/github-actions-cicd/_family_facts.md`, `_family_rules.md`) are applied as given.
> This document is provenance for the skill author; the shipped skill must not read it (brief constraint).
>
> Section-order note: the brief requires the file to END with `## Source Bibliography`, so that
> section moves from its template position to the end, after `## Pages read`. All 15 template
> sections are present.
>
> Version note: every action major/SHA below comes from the facts file (F4, F5, F10, F23, F24).
> The official GitHub tutorials for Maven/Gradle/publishing still show `actions/setup-java@v4`,
> `actions/upload-artifact@v4` and `gradle/actions/setup-gradle@...# v4.4.2`, and the gradle/actions
> docs at v6.4.1 show `actions/setup-java@v5`. These are stale doc examples and are NOT used
> (brief lesson 1).

## Metadata

```yaml
Full_Name: Building and testing Java (Maven and Gradle) on GitHub Actions (GitHub.com hosted runners)
Target_Version: actions/setup-java v6.1.0 (F4); Maven 3.10.0 (F12); Gradle 9.8.2 (F13) with gradle/actions v6.4.1 (F5); JDK LTS 25 / 21 / 17 (F11)
Release_Dates: setup-java v6.1.0 "14 Oct" (year not shown; 2026 by order); v6.0.0 "24 Aug"; gradle/actions v6.4.1 "28 Oct", v6.0.0 "23 Mar"; Maven 3.10.0 2026-09-27 (F12); Gradle 9.8.2 2026-10-19 (F13)
Support_Status: all current stable; Maven 3.9.16 still supported (F12); Maven 4 not GA (F12)
Primary_Docs:
  - https://github.com/actions/setup-java/blob/v6.1.0/README.md
  - https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md
  - https://maven.apache.org/ref/3.10.0/maven-embedder/cli.html
  - https://docs.gradle.org/9.8.2/userguide/
Integration_Partners: Maven Surefire/Failsafe 3.6.1, JaCoCo, Maven Wrapper, Gradle Wrapper, AWS Lambda Java .zip packaging, Jib (container image), actions/upload-artifact v7.0.2 (F23)
Neighbour_Units (by name only, rule 12): publishing-container-images-github-actions (image push), deploying-aws-lambda (release), composing-github-actions-pipelines (caller/reusable structure), automating-github-repos-with-actions (github-core: SHA pinning, injection)
Research_Date: 2026-10-30
Domain_Complexity: Standard (build + test + package; credentials only for optional publishing)
Research_Depth: exhaustive (default)
Max_Iterations: 5
Gap_Loop_Ran: true
Iterations_Used: 2 of 5
Triangulated_Count: 7
Unverified_Count: 6
Irresolvable_Count: 0
Research_Quality_Score: 88%   # ~60 claims, 6 unverified, 5 medium confidence
```

## Executive Summary

A Java CI job on GitHub Actions has three moving parts: `actions/setup-java` installs a JDK and
(optionally) caches Maven/Gradle dependencies; the build tool runs non-interactively (`mvn -B` /
`./gradlew build`); and `actions/upload-artifact` keeps the outputs (test reports, coverage, the
deployable .zip or image tarball). setup-java v6 (v6.0.0 "24 Aug", v6.1.0 "14 Oct") renames the
credential inputs to `server-username-env-var`, `server-password-env-var` and
`gpg-passphrase-env-var` (old names work with warnings), removes the legacy AdoptOpenJDK
distributions (`adopt*` -> `temurin` / `semeru`), adds `cache-jdk` and `cache-read-only`, and in
v6.1.0 adds Maven server credential origins, which "only works with Maven 3.10 and later"
(https://github.com/actions/setup-java/blob/v6.1.0/README.md;
https://github.com/actions/setup-java/blob/v6.1.0/docs/advanced-usage.md, both read 2026-10-30).
Maven 3.10.0 turns many 3.9 validation WARNINGs into build failures, changes classpath ordering to
breadth-first, and makes Reproducible Builds active by default
(https://maven.apache.org/docs/3.10.0/release-notes.html, read 2026-10-30). GitHub-hosted runners
ship Maven 3.9.x, so pin 3.10.0 through the Maven Wrapper (advanced-usage, read 2026-10-30).

For Gradle, `gradle/actions/setup-gradle` v6 provides caching, wrapper validation (on by default),
a job summary and dependency-graph submission. v6.0.0 moved caching into a proprietary
`gradle-actions-caching` component: "By upgrading to v6, you accept the Terms of Use"; it is "free
for public repositories and in Free Preview for private ones", while `cache-provider: basic` is
MIT-licensed and free for all repositories (https://github.com/gradle/actions/releases;
https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md, read 2026-10-30). Because the
family targets PRIVATE repositories (rule 16), the provider choice is an Ask-First item. v6.4.1 fixes
security advisory GHSA-chpw-2mqm-95cc in `dependency-submission` ("All users should upgrade").
Gradle 9.x needs a JVM between 17 and 27 to run, so a 17/21/25 matrix is fine for both tools
(https://docs.gradle.org/9.8.2/userguide/compatibility.html).

Three critical patterns: (1) pull-request runs build and test only, with `contents: read`, no
secrets, no publish, no deploy (rules 7 and 13; fork PRs get no secrets and a read-only token per
GitHub); (2) build the deployable once on the merge commit, upload it with an
`artifact-digest`, and promote that same file (rule 8), using the reproducible-by-default archives of
Maven 3.10 and Gradle 9; (3) report tests in `$GITHUB_STEP_SUMMARY` from the Surefire/Gradle XML
reports with a shell step, with no third-party reporting action.

## Architectural Guardrails

> Confidence legend: High = official page read in full; Triangulated = 2+ independent official
> sources | (medium confidence) = one source, partly read, or inferred | (unverified) = no official
> confirmation found. SHAs: F4 setup-java, F5 gradle/actions, F10 checkout, F23 upload-artifact.

### ✅ Mandatory Patterns

**A1. Pin the JDK distribution and version explicitly in `actions/setup-java`**
> Confidence: High (setup-java v6.1.0 README; F11)
- Why: `distribution` is required (unless a `.sdkmanrc` supplies it) and keywords are case-sensitive; `java-version` accepts exact versions, ranges and `latest`. Use an LTS major from F11 (25, 21 or 17). `temurin` and `microsoft` are the only distributions with package signature verification; most others get checksum verification.
- Code:
  ```yaml
  # setup-java v6.1.0 (F4)
  - uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
    with:
      distribution: temurin
      java-version: '25'
  ```
- Source: https://github.com/actions/setup-java/blob/v6.1.0/README.md (2026-10-30); https://adoptium.net/support/ via F11

**A2. Run Maven non-interactively: `-B` (batch) and `-ntp` (no transfer progress), phase `verify`**
> Confidence: High | [✓✓ Triangulated | Maven 3.10.0 CLI reference + GitHub Maven tutorial + Failsafe usage]
- Why: `-B` = "Run in non-interactive (batch) mode (disables output color)"; `-ntp` = "Do not display transfer progress when downloading or uploading". The GitHub tutorial uses `mvn --batch-mode --update-snapshots verify`. `verify` also runs Failsafe integration tests: "invoke Maven with a phase of `verify` or later in order to run the integration tests".
- Code:
  ```bash
  # Maven 3.10.0 via wrapper
  ./mvnw -B -ntp verify
  ```
- Source: https://maven.apache.org/ref/3.10.0/maven-embedder/cli.html; https://docs.github.com/en/actions/tutorials/build-and-test-code/java-with-maven; https://maven.apache.org/surefire/maven-failsafe-plugin/usage.html (all 2026-10-30)

**A3. Pin Maven 3.10.0 with the Maven Wrapper (runners ship 3.9.x)**
> Confidence: High | [✓✓ Triangulated | Maven Wrapper page + setup-java advanced-usage]
- Why: setup-java advanced-usage notes that GitHub-hosted runners ship Maven 3.9.x, so users need the Maven Wrapper or Maven 3.10+ for 3.10-only features. The wrapper is created with `mvn wrapper:wrapper -Dmaven=<version>`; the default type is `only-script`; checksums go in `.mvn/wrapper/maven-wrapper.properties` as `distributionSha256Sum` (and `wrapperSha256Sum` for the jar type) "To avoid supply-chain-attacks".
- Code:
  ```bash
  # Run once locally, commit mvnw, mvnw.cmd, .mvn/wrapper/maven-wrapper.properties
  mvn wrapper:wrapper -Dmaven=3.10.0
  # then add distributionSha256Sum=<sha256 of apache-maven-3.10.0-bin.zip> to maven-wrapper.properties
  ```
- Source: https://maven.apache.org/tools/wrapper/ (2026-10-30); https://github.com/actions/setup-java/blob/v6.1.0/docs/advanced-usage.md (2026-10-30). The SHA-256 value of the 3.10.0 distribution was not resolved (Research Gaps G3).

**A4. Cache dependencies with `cache: maven` (setup-java) or setup-gradle; keep caches free of secrets**
> Confidence: High | [✓✓ Triangulated | setup-java README + GitHub dependency-caching reference]
- Why: setup-java's Maven key hashes `pom.xml` files, `.mvn/wrapper/maven-wrapper.properties` and `.mvn/extensions.xml`; `cache` also turns on `cache-jdk` by default. GitHub: "Don't store sensitive information in a cache", because anyone with read access can open a PR and read cache contents. Caches unused for 7 days are evicted; default limit 10 GB per repository.
- Code:
  ```yaml
  - uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
    with:
      distribution: temurin
      java-version: '25'
      cache: maven
  ```
- Source: https://github.com/actions/setup-java/blob/v6.1.0/README.md; https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching (both 2026-10-30)

**A5. Use `gradle/actions/setup-gradle` then `./gradlew build`; keep wrapper validation on**
> Confidence: High | [✓✓ Triangulated | setup-gradle v6.4.1 docs + Gradle 9.8.2 wrapper docs]
- Why: setup-gradle validates wrapper jars against known checksums by default (`validate-wrappers`); Gradle docs: the Setup Gradle action "automatically validates the Wrapper JAR as part of every build". Cache writes only from the default branch; PR runs are read-only by default. Commit `gradle/wrapper/gradle-wrapper.jar`, `gradle-wrapper.properties`, `gradlew`, `gradlew.bat`.
- Code:
  ```yaml
  - uses: gradle/actions/setup-gradle@8da46b539cd8fe6ab27ca75128919a18d757604c # v6.4.1
  - run: ./gradlew build
  ```
- Source: https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md; https://docs.gradle.org/9.8.2/userguide/gradle_wrapper.html (both 2026-10-30)

**A6. Upload test and coverage reports as artifacts even when tests fail, with unique names in a matrix**
> Confidence: High (upload-artifact v7.0.2 README; F23) — `if: always()` semantics (medium confidence, page not read this run)
- Why: artifact names "must be unique" within a run; in a matrix include matrix values in the name. Default retention is 90 days (F23); set `retention-days` (1-90). Surefire writes to `${project.build.directory}/surefire-reports`, Failsafe to `.../failsafe-reports`, Gradle XML results to `layout.buildDirectory.dir("test-results/$testTaskName")`, Gradle JaCoCo HTML to `reports/jacoco/test/html`, Maven JaCoCo example report at `target/site/jacoco/index.html`.
- Code:
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
- Source: https://github.com/actions/upload-artifact/blob/v7.0.2/README.md; https://maven.apache.org/surefire/maven-surefire-plugin/test-mojo.html; https://maven.apache.org/surefire/maven-failsafe-plugin/integration-test-mojo.html; https://docs.gradle.org/9.8.2/userguide/java_testing.html; https://docs.gradle.org/9.8.2/userguide/jacoco_plugin.html; https://www.jacoco.org/jacoco/trunk/doc/maven.html (all 2026-10-30)

**A7. Write a test summary to `$GITHUB_STEP_SUMMARY` without a third-party action**
> Confidence: High for the mechanism (workflow-commands page); the XML attribute names used by the parser are (medium confidence)
- Why: Markdown appended to `GITHUB_STEP_SUMMARY` is shown on the run summary page; GitHub flavored Markdown; 1 MiB per step; up to 20 step summaries per job; secrets are masked automatically. An oversized summary fails its upload with an error annotation but does not change job status.
- Code: see Implementation Blueprint step 5.
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands (2026-10-30)

**A8. Pull-request workflows build and test only (`contents: read`), never publish or deploy**
> Confidence: High | [✓✓ Triangulated | events-that-trigger-workflows + dependency-caching + family rules 7/13]
- Why: for fork PRs "secrets are not passed to the runner" and "The `GITHUB_TOKEN` has read-only permissions"; PR runs execute branch code. `GITHUB_SHA` on `pull_request` is the merge commit of `refs/pull/<n>/merge`, so it is not the commit that will land. Publishing (`mvn deploy`, Jib push, Lambda update) happens only in `cd-<app>.yml` on the protected branch (rule 5, rule 7).
- Code:
  ```yaml
  # .github/workflows/ci-orders.yml
  on: pull_request
  permissions:
    contents: read
  ```
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows (2026-10-30)

**A9. Build the deployable once on the merge commit and promote the same file by digest**
> Confidence: High | [✓✓ Triangulated | upload-artifact `artifact-digest` output + Maven 3.10 reproducible builds + Gradle 9 reproducible archives] (family rule 8)
- Why: upload-artifact outputs `artifact-digest` (SHA-256). Maven 3.10.0: "Reproducible Builds are active by default" (Super POM now sets a default `project.build.outputTimestamp`). Gradle 9.0: archive tasks "produce reproducible archives by default". Hand the uploaded .zip/JAR and its hash to `deploying-aws-lambda`; never rebuild for prod.
- Source: https://github.com/actions/upload-artifact/blob/v7.0.2/README.md; https://maven.apache.org/docs/3.10.0/release-notes.html; https://docs.gradle.org/9.8.2/userguide/upgrading_major_version_9.html (all 2026-10-30)

### ⚠️ Conditional Patterns

**C1. Gradle caching provider on private repositories: `enhanced` (default) vs `basic` vs `external`**
- Options: `enhanced` = proprietary `gradle-actions-caching`, "Free Preview" for private repos, accepting its Terms of Use on upgrade to v6; `basic` = MIT, built on `@actions/cache`, free for all repos; `external` = another tool manages Gradle User Home (better than `cache-disabled`, keeps the job summary accurate).
- Tradeoffs: enhanced caches more (and is the only one where `cache-encryption-key` for configuration-cache data applies); basic avoids a proprietary licence and a preview whose future pricing is not stated on the page.
- When: family targets PRIVATE repos (rule 16) -> ask the user; suggested default `cache-provider: basic` until the user accepts the enhanced terms.
- Source: https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md; https://github.com/gradle/actions/releases (2026-10-30)

**C2. Lambda .zip packaging: Gradle `Zip` task (lib/ layout) vs Maven Shade uber-JAR vs Quarkus `function.zip`**
- Options: (a) Gradle: a `Zip` task putting the project jar and `configurations.runtimeClasspath` into `lib/`, output in `build/distributions`; (b) Maven: `maven-shade-plugin` produces one JAR with all dependencies, uploaded directly (AWS accepts .zip or JAR); for a multi-release JAR, AWS says to put the shaded JAR in `lib/` and zip it; (c) Quarkus projects produce `function.zip` — covered by name only; see the Quarkus Lambda skills in `quarkus-aws` and `deploying-aws-lambda`.
- Tradeoffs: Lambda loads `lib/` JARs in Unicode alphabetical order and the first duplicate class wins (Gradle zip); Shade merges everything (needs a transformer when using `aws-lambda-java-log4j2`). Packages over 50 MB must go through S3.
- When: build tool already chosen; MRJAR in use; log4j2 appender in use.
- Source: https://docs.aws.amazon.com/lambda/latest/dg/java-package.html (2026-10-30)

**C3. Container image: Jib `buildTar` in CI vs Dockerfile hand-off**
- Options: (a) Jib Maven plugin (3.5.2 per README): `jib:buildTar` writes `target/jib-image.tar` and is not described as needing Docker; `jib:dockerBuild` needs `docker` on PATH; `jib:build` pushes to a registry; default base `eclipse-temurin:{8,11,17,21,25}-jre`; digest written to `target/jib-image.digest`. (b) A Dockerfile built by `publishing-container-images-github-actions` from the JAR artifact.
- Tradeoffs: `jib:build` is a registry push, which belongs to the neighbour unit and to `cd-` only; in this unit use `buildTar` (or just upload the JAR) and hand over.
- When: team already uses Jib vs Dockerfile; registry auth model (owned by the publishing unit).
- Source: https://github.com/GoogleContainerTools/jib/tree/master/jib-maven-plugin (2026-10-30). Jib plugin version is not in the facts file (Facts requested FR3).

**C4. JDK matrix 17/21/25 vs single JDK**
- Options: matrix over F11 LTS majors; or one JDK equal to the Lambda runtime (`java25`, `java21`, `java17.al2023`; `java17` on AL2 deprecates Jun 30, 2027).
- Tradeoffs: matrix triples minutes; only one leg should produce the deployable (the leg equal to the target runtime) so rule 8 holds. Gradle runs on JVM 17-27; Java 25 needs Gradle 9.1.0+ (toolchains and running). Maven 3.10.0 runs on Java 8+.
- Source: https://docs.gradle.org/9.8.2/userguide/compatibility.html; https://maven.apache.org/docs/3.10.0/release-notes.html; https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html (2026-10-30)

**C5. Dependency graph: `gradle/actions/dependency-submission` on push vs PR**
- Options: push to `main` with `contents: write`; for PR dependency review add `pull_request` too; for public-fork PRs split into a `pull_request` job (`generate-and-upload`, `contents: read`) plus a `workflow_run` job (`download-and-submit`, `contents: write`).
- Tradeoffs: `contents: write` on a PR job conflicts with rule 7's read-only PR stance for fork code; the split keeps the write in a job that does not run PR code. Dependency review itself belongs to the supply-chain unit (F9).
- Source: https://github.com/gradle/actions/blob/v6.4.1/docs/dependency-submission.md (2026-10-30)

**C6. Publishing a library (`mvn deploy`) from `cd-` only: GITHUB_TOKEN to GitHub Packages vs stored token to another registry**
- Options: GitHub Packages with `permissions: contents: read, packages: write`, distribution repository `id` `github`, `GITHUB_TOKEN` (no stored secret); or another registry with `server-id` + `server-username-env-var` / `server-password-env-var` read from an environment secret.
- Tradeoffs: environment secrets in PRIVATE repos need Pro/Team (GitHub Free: "environment secrets are only available in public repositories"); on Free private, prefer GITHUB_TOKEN + GitHub Packages or accept a repository secret as a documented exception to rule 10. With Maven 3.10, `mvn-server-repository-origins` scopes a credential to named origins.
- Source: https://docs.github.com/en/actions/tutorials/publish-packages/publish-java-packages-with-maven; https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments; https://github.com/actions/setup-java/blob/v6.1.0/docs/advanced-usage.md (all 2026-10-30)

### 🚫 Forbidden Patterns

**N1. Using the removed `adopt` distributions with setup-java v6**
- Why: v6 removed the legacy AdoptOpenJDK distributions; use `temurin` (for `adopt`/`adopt-hotspot`) or `semeru` (for `adopt-openj9`). Invalid inputs now fail with targeted errors.
- ❌ Wrong:
  ```yaml
  with: { distribution: adopt, java-version: '17' }
  ```
- ✅ Correct:
  ```yaml
  with: { distribution: temurin, java-version: '17' }
  ```
- Impact: step fails on v6.
- Source: https://github.com/actions/setup-java/blob/v6.1.0/README.md (2026-10-30)

**N2. Using the old credential input names (`server-username`, `server-password`, `gpg-passphrase`)**
- Why: renamed in v6 to `*-env-var`; the old names are deprecated aliases that warn. The values are names of environment variables, not secrets.
- ❌ Wrong:
  ```yaml
  with: { server-id: central, server-password: MAVEN_TOKEN }
  ```
- ✅ Correct:
  ```yaml
  with: { server-id: central, server-password-env-var: MAVEN_TOKEN }
  # step env: MAVEN_TOKEN: ${{ secrets.MAVEN_TOKEN }}
  ```
- Impact: deprecation warnings now, breakage when aliases are removed (removal timing unverified).
- Source: https://github.com/actions/setup-java/blob/v6.1.0/README.md (2026-10-30)

**N3. Publishing or deploying from a pull_request workflow**
- Why: PR code is untrusted branch code; fork PRs get no secrets and a read-only token; rules 7 and 13.
- ❌ Wrong:
  ```yaml
  on: pull_request
  jobs: { release: { steps: [ { run: ./mvnw -B deploy } ] } }
  ```
- ✅ Correct:
  ```yaml
  # ci-orders.yml (pull_request): ./mvnw -B -ntp verify
  # cd-orders.yml (push to main): ./mvnw -B -ntp deploy, permissions packages: write
  ```
- Impact: credential exposure or unreviewed artifacts in a registry.
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows (2026-10-30)

**N4. Running PR code under `pull_request_target` to get secrets for the build**
- Why: "Avoid using this event if you need to build or run code from the pull request"; risks include "cache poisoning and granting unintended access to write privileges or secrets".
- ❌ Wrong:
  ```yaml
  on: pull_request_target
  steps: [ { uses: actions/checkout@... , with: { ref: "${{ github.event.pull_request.head.sha }}" } }, { run: ./gradlew build } ]
  ```
- ✅ Correct:
  ```yaml
  on: pull_request
  permissions: { contents: read }
  ```
- Impact: secret exfiltration, poisoned caches.
- Source: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows (2026-10-30)

**N5. Ignoring test failures to keep the pipeline green**
- Why: Surefire `testFailureIgnore` "Its use is NOT RECOMMENDED"; Gradle 9 `test` "will now fail with an error if it runs but doesn't discover any tests" — do not blanket-disable with `failOnNoDiscoveredTests = false`.
- ❌ Wrong:
  ```bash
  ./mvnw -B verify -Dmaven.test.failure.ignore=true
  ```
- ✅ Correct:
  ```bash
  ./mvnw -B -ntp verify   # failing tests fail the job; reports uploaded with if: always()
  ```
- Impact: broken builds promoted as deployables.
- Source: https://maven.apache.org/surefire/maven-surefire-plugin/test-mojo.html; https://docs.gradle.org/9.8.2/userguide/upgrading_major_version_9.html (2026-10-30)

**N6. Rebuilding the artifact for each environment**
- Why: family rule 8; the uploaded file has a SHA-256 `artifact-digest`; builds are reproducible by default only for the same inputs.
- ❌ Wrong:
  ```yaml
  deploy-prod: { steps: [ { run: ./gradlew buildZip }, ... ] }
  ```
- ✅ Correct:
  ```yaml
  deploy-prod: { steps: [ { uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 }, ... ] } # v8.0.2, same zip as staging
  ```
- Impact: prod runs a binary nobody tested.
- Source: https://github.com/actions/upload-artifact/blob/v7.0.2/README.md (2026-10-30); F24

**N7. Double caching Gradle User Home (setup-java `cache: gradle` plus setup-gradle default cache)**
- Why: setup-gradle says when another tool manages Gradle User Home, use `cache-provider: external` (more accurate than `cache-disabled`, keeps the job summary right).
- ❌ Wrong:
  ```yaml
  - uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
    with: { distribution: temurin, java-version: '25', cache: gradle }
  - uses: gradle/actions/setup-gradle@8da46b539cd8fe6ab27ca75128919a18d757604c # v6.4.1
  ```
- ✅ Correct:
  ```yaml
  - uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
    with: { distribution: temurin, java-version: '25' }
  - uses: gradle/actions/setup-gradle@8da46b539cd8fe6ab27ca75128919a18d757604c # v6.4.1
    with: { cache-provider: basic }
  ```
- Impact: wasted cache quota (10 GB/repo default), inaccurate summary.
- Source: https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md; https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching (2026-10-30)

**N8. Disabling Gradle wrapper validation or allowing snapshot wrappers by default**
- Why: validation checks wrapper jars against known checksums and is on by default; snapshot wrappers are refused by default.
- ❌ Wrong:
  ```yaml
  with: { validate-wrappers: false, allow-snapshot-wrappers: true }
  ```
- ✅ Correct:
  ```yaml
  # omit both inputs (defaults: validate, no snapshots)
  ```
- Impact: a tampered `gradle-wrapper.jar` in a PR runs arbitrary code.
- Source: https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md (2026-10-30)

## Migration Guide

### setup-java v5 -> v6 (v6.0.0 "24 Aug"; v6.1.0 "14 Oct")
| Change | Action | Source |
|---|---|---|
| `server-username` / `server-password` / `gpg-passphrase` renamed to `*-env-var` | Rename; old names warn | README v6.1.0 |
| Legacy `adopt`, `adopt-hotspot`, `adopt-openj9` removed | Use `temurin` / `semeru` | README; releases page ("Remove legacy Adopt distributions in v6") |
| `jdkFile` -> `jdk-file` (v5 per README; listed in v6.0.0 notes) | Rename | README; releases |
| `mvn-repositories-include-central: false` now disables Central for plugins too | Review custom repo setups | README |
| GPG passphrase via `gpg.passphraseEnvName` | Needs `maven-gpg-plugin` 3.2.0+ | README; advanced-usage |
| GraalVM sets `GRAALVM_HOME` | none | README |
| ESM migration | "not a user-facing breaking change" (releases) | releases |
| New: `cache-jdk`, `cache-read-only`, `cache-path` | Optional | README |
| v6.1.0: `mvn-server-repository-origins`, plugin repositories in generated settings.xml, Temurin RISC-V | Origins need Maven 3.10+ | releases; advanced-usage |
| Runtime Node 24 (since v5); self-hosted runner >= v2.327.1 | Upgrade self-hosted runners | README |

### Maven 3.9 -> 3.10.0
- Stricter POM validation: "many WARNINGs from the 3.9 lineage... will now FAIL the build" (duplicate dependencies/plugins). Temporary escape `-Dmaven.resolver.validation=off` — fix the POM instead.
- Classpath order depth-first -> breadth-first; old behaviour `-Daether.system.dependencyVisitor=preOrder`.
- Super POM: `release-profile` and plugin management removed; UTF-8 encodings and default `project.build.outputTimestamp` set.
- Repository credentials are scoped to origins Maven can associate with the server id.
- A misconfigured plugin-requested toolchain now fails the build.
- Upgrade: `mvn wrapper:wrapper -Dmaven=3.10.0`, commit, run `./mvnw -B -ntp verify`.
- Source: https://maven.apache.org/docs/3.10.0/release-notes.html (2026-10-30)

### Gradle 8.14 -> 9.x (target 9.8.2)
- Daemon needs JVM 17+; wrapper/launcher still start on JVM 8.
- Convention API removed; Kotlin DSL language 2.2; reproducible archives by default; `test` fails when no tests are discovered; configuration-cache incompatible tasks discard the entry.
- JUnit Jupiter: declare JUnit Jupiter, JUnit Platform and `junit-platform-launcher` (`testRuntimeOnly`) dependencies (java_testing troubleshooting).
- Upgrade: `./gradlew :wrapper --gradle-version 9.8.2` and run it twice to update all wrapper files.
- Source: https://docs.gradle.org/9.8.2/userguide/upgrading_major_version_9.html; https://docs.gradle.org/9.8.2/userguide/gradle_wrapper.html; https://docs.gradle.org/9.8.2/userguide/java_testing.html (2026-10-30)

### gradle/actions v5 -> v6 (v6.0.0 "23 Mar"; v6.4.1 "28 Oct")
- Caching extracted into proprietary `gradle-actions-caching`; "By upgrading to v6, you accept the Terms of Use"; rudimentary configuration-cache support removed; `cache-provider` added (`enhanced` default, `basic`, and since v6.4.0 `external`).
- v6.4.0: Gradle version support status in annotations and job summary; dependency graph includes Gradle itself.
- v6.4.1: fixes GHSA-chpw-2mqm-95cc in `dependency-submission`.
- Node runtime and any removed inputs for v6 are not stated on the pages read (unverified).
- Source: https://github.com/gradle/actions/releases (2026-10-30)

## Implementation Blueprint

Step 1 — Caller layout (rule 5; structure details belong to `composing-github-actions-pipelines`):
`.github/workflows/ci-<app>.yml` (pull_request) and `cd-<app>.yml` (push to main) both call
`./.github/workflows/_java-build.yml` (rule 15 real paths).

Step 2 — Reusable build workflow (rule 6: typed inputs, explicit outputs, own permissions, no secrets):

```yaml
# .github/workflows/_java-build.yml
# setup-java v6.1.0 (F4) | gradle/actions v6.4.1 (F5) | checkout v7.0.1 (F10) | upload-artifact v7.0.2 (F23)
name: _java-build
on:
  workflow_call:
    inputs:
      build-tool:      { type: string,  required: true }   # maven | gradle
      java-version:    { type: string,  required: false, default: '25' }
      package-lambda:  { type: boolean, required: false, default: false }
    outputs:
      artifact-name:   { value: '${{ jobs.build.outputs.artifact-name }}' }
      artifact-digest: { value: '${{ jobs.build.outputs.artifact-digest }}' }
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      artifact-name:   ${{ steps.names.outputs.artifact }}
      artifact-digest: ${{ steps.up.outputs.artifact-digest }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
        with:
          distribution: temurin
          java-version: ${{ inputs.java-version }}
          cache: ${{ inputs.build-tool == 'maven' && 'maven' || '' }}
          cache-read-only: ${{ github.event_name == 'pull_request' }}
      - if: ${{ inputs.build-tool == 'gradle' }}
        uses: gradle/actions/setup-gradle@8da46b539cd8fe6ab27ca75128919a18d757604c # v6.4.1
        with:
          cache-provider: basic          # C1: private repos; enhanced only after the user accepts its terms
      - if: ${{ inputs.build-tool == 'maven' }}
        run: ./mvnw -B -ntp verify
      - if: ${{ inputs.build-tool == 'gradle' }}
        run: ./gradlew build
      # Step 5 summary step goes here (if: always())
      - id: names
        run: echo "artifact=app-${{ github.sha }}" >> "$GITHUB_OUTPUT"
      - if: ${{ inputs.package-lambda }}
        id: up
        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
        with:
          name: ${{ steps.names.outputs.artifact }}
          path: |
            build/distributions/*.zip
            target/*.jar
          retention-days: 14
          if-no-files-found: error
```

Notes: `cache: ''` for Gradle avoids N7 (setup-java treats empty as no cache — (medium confidence),
README does not state empty-string behaviour). The `cache-read-only` input exists in setup-java
v6.1.0 (default false); setting it on PR runs mirrors setup-gradle's default — (medium confidence)
as a recommendation, since GitHub already scopes PR caches to the merge ref.

Step 3 — Lambda .zip with Gradle 9.8.2 (AWS pattern, written with the lazy `register` API that
Gradle recommends over eager `task`/`create`):

```kotlin
// build.gradle.kts — Gradle 9.8.2
tasks.register<Zip>("buildZip") {
    into("lib") {
        from(tasks.jar)
        from(configurations.runtimeClasspath)
    }
}
```
Output: `build/distributions/*.zip`. Run `./gradlew build buildZip`. Source:
https://docs.aws.amazon.com/lambda/latest/dg/java-package.html;
https://docs.gradle.org/9.8.2/userguide/task_configuration_avoidance.html (2026-10-30). The Kotlin
translation of the AWS Groovy snippet is (medium confidence) — not shown verbatim on either page.

Step 4 — Lambda JAR with Maven 3.10.0: `maven-shade-plugin` bound to `package` with
`createDependencyReducedPom=false`; `./mvnw -B -ntp package` writes the shaded JAR to `target/`.
The AWS page shows Shade 3.2.2, which is an old doc version; the current Shade version was not
resolved (Facts requested FR2). Source: https://docs.aws.amazon.com/lambda/latest/dg/java-package.html (2026-10-30).

Step 5 — Test summary without third-party actions (A7):

```bash
# Representative — adapt to your environment. Works on Surefire/Failsafe and Gradle JUnit XML.
# XML attribute names tests/failures/errors/skipped: (medium confidence), not confirmed on a page read this run.
shopt -s nullglob
files=(target/surefire-reports/TEST-*.xml target/failsafe-reports/TEST-*.xml build/test-results/test/TEST-*.xml)
t=0; f=0; e=0; s=0
for x in "${files[@]}"; do
  line=$(grep -m1 -o '<testsuite [^>]*>' "$x")
  get() { echo "$line" | sed -n "s/.* $1=\"\([0-9]*\)\".*/\1/p"; }
  t=$((t+$(get tests))); f=$((f+$(get failures))); e=$((e+$(get errors))); s=$((s+$(get skipped)))
done
{
  echo "### Tests (JDK ${JAVA_VERSION:-?})"
  echo "| total | failed | errors | skipped |"
  echo "|---|---|---|---|"
  echo "| $t | $f | $e | $s |"
} >> "$GITHUB_STEP_SUMMARY"
```
Run it in a step with `if: ${{ always() }}`. setup-gradle also writes its own Gradle job summary
(`add-job-summary: always` by default).

Step 6 — JDK matrix in `ci-<app>.yml` (C4): call `_java-build.yml` per `java-version` in
`['17','21','25']`; set `package-lambda: true` only in `cd-<app>.yml` with the version equal to the
Lambda runtime. Matrix artifact names must include the matrix value (A6).

Step 7 — Hand-off: `cd-<app>.yml` passes `artifact-name` and `artifact-digest` to
`deploying-aws-lambda` (zip) or to `publishing-container-images-github-actions` (JAR / Jib tarball).
This unit never pushes images or updates functions.

## Quality Control

```bash
# Representative — adapt to your environment (Maven 3.10.0 / Gradle 9.8.2 / JDK 25)
./mvnw -v                        # Expected: "Apache Maven 3.10.0" (wrapper pin works)
./mvnw -B -ntp verify            # Expected: BUILD SUCCESS; target/surefire-reports/TEST-*.xml exist
./gradlew --version              # Expected: "Gradle 9.8.2"
./gradlew build buildZip         # Expected: BUILD SUCCESSFUL; build/distributions/*.zip
unzip -l build/distributions/*.zip | grep ' lib/'    # Expected: lib/<project>.jar plus dependency jars
# Duplicate class check from AWS docs:
mkdir -p expanded && unzip -o build/distributions/*.zip -d expanded
find ./expanded/lib -name '*.jar' | xargs -n1 zipinfo -1 | grep '.*.class' | sort | uniq -c | sort
# Workflow static checks (no network): grep that every 'uses:' is SHA-pinned
grep -nE 'uses: [^ ]+@[0-9a-f]{40}' .github/workflows/*.yml
grep -nE 'uses: [^ ]+@v[0-9]' .github/workflows/*.yml   # Expected: no output
```
Coverage: JaCoCo 0.8.16 (released 2026/10/24) officially supports up to Java 27; 0.8.14 added Java 25
support. Gradle's `jacoco` plugin defaults `toolVersion` to 0.8.15 (supports Java 26). The Maven
JaCoCo agent needs forked test execution ("forkCount of 0" prevents the javaagent); with a custom
Surefire `argLine` use late replacement `@{argLine}`. `jacocoTestCoverageVerification` is not wired
into `check` by default. Sources: https://www.jacoco.org/jacoco/trunk/doc/changes.html,
https://www.jacoco.org/jacoco/trunk/doc/maven.html, https://docs.gradle.org/9.8.2/userguide/jacoco_plugin.html,
https://maven.apache.org/surefire/maven-surefire-plugin/test-mojo.html (2026-10-30).

## Production Readiness

- Cache budget: 10 GB/repo default, 7-day eviction, PR caches scoped to the merge ref (dependency-caching page).
- Artifact retention: default 90 days (F23); set short retention for reports, longer for promoted zips.
- Lambda limits: direct upload < 50 MB, else via S3 in the function's Region; Java 25 AOT caches are "strongly" discouraged for .zip/JAR deploys (java-package page).
- Runtime support: `java25`, `java21`, `java17.al2023` deprecate Jun 30, 2029; `java17` (AL2) Jun 30, 2027 (lambda-runtimes page).
- Plan limits (rule 16, private repos): required reviewers, wait timers and custom protection rules are public-repo only on Free/Pro/Team; environment secrets and deployment branch policies need Pro/Team for private repos (not Free). This unit needs no environment for CI; publishing in C6 depends on it.
- Gradle version annotations: setup-gradle v6.4.0+ warns for end-of-life Gradle (two or more majors behind).

## Reference Implementations

- Official: GitHub tutorial "Building and testing Java with Maven" / "with Gradle" (structure only; action versions stale).
- Official: setup-java advanced usage (publishing, GPG, matrix) at tag v6.1.0.
- Official: gradle/actions docs at v6.4.1 (setup-gradle, dependency-submission).
- Official: AWS sample apps `java-basic`, `s3-java` (Gradle `buildZip`) linked from the java-package page.
- Official: Jib Maven plugin README (GoogleContainerTools).

## Research Gaps

| ID | Gap | Status | Follow-up |
|---|---|---|---|
| G1 | Surefire/Gradle JUnit XML attribute names (`tests`, `failures`, `errors`, `skipped`) used by the summary parser | (medium confidence) | Read Surefire XML report schema page |
| G2 | setup-java behaviour for `cache: ''` (empty string) | (unverified) | Read action.yml/source at v6.1.0; alternative: two setup-java steps with `if:` |
| G3 | SHA-256 of `apache-maven-3.10.0-bin.zip` for `distributionSha256Sum` | (unverified) | Read the `.sha512`/`.sha256` file on repo.maven.apache.org; author leaves a placeholder |
| G4 | gradle/actions v6 Node runtime / removed inputs | (unverified) | Read full v6.0.0 release note |
| G5 | Removal date for setup-java deprecated input aliases | (unverified) | None published |
| G6 | `if: always()` status-check semantics (not re-read this run) | (medium confidence) | Read docs.github.com expressions page |
| G7 | Current versions of maven-shade-plugin and jib-maven-plugin for pins | Facts requested FR2/FR3 | Orchestrator to add to facts file |

## Research Iteration Changelog

| Iteration | Gap | Resolution | Source |
|---|---|---|---|
| 1 | Default report directories for Surefire/Failsafe (usage page silent) | Resolved from mojo pages: `${project.build.directory}/surefire-reports`, `/failsafe-reports` | test-mojo / integration-test-mojo pages |
| 1 | JaCoCo released version (trunk docs show snapshot) | Resolved: 0.8.16 (2026/10/24); Java 25 since 0.8.14 | jacoco changes page |
| 2 | Whether eager `task buildZip(type: Zip)` is acceptable in Gradle 9 | Partly: `register` recommended, eager API "should be avoided"; not stated deprecated | task_configuration_avoidance |
| 2 | Environment features on private repos (brief lesson 2) | Resolved: see Production Readiness | deployments-and-environments |

## Completion Checklist

- [x] Metadata, Executive Summary, three guardrail tiers (9 / 6 / 8)
- [x] Every Never Do has ❌/✅ examples
- [x] Migration guide for setup-java v6, Maven 3.10, Gradle 9, gradle/actions v6
- [x] Action SHAs only from facts file (F4, F5, F10, F23, F24)
- [x] Version-tagged examples; target versions stated 5+ times
- [x] Pages read table; prompt-injection check done
- [x] Ends with Source Bibliography
- [ ] Commands executed live (not run: research only; marked Representative)

## Agent Operation Notes

- High confidence: setup-java v6 inputs/breaking changes; Maven 3.10 CLI flags and breaking changes; setup-gradle cache/validation defaults and licensing; fork PR secret/token behaviour; environment feature availability by plan; Lambda packaging layout and runtimes; artifact name uniqueness and digest output.
- Medium confidence: summary parser XML attributes; Kotlin translation of `buildZip`; `cache-read-only` on PRs as a recommendation; `if: always()` semantics.
- Low / unverified: G2-G5.

## Pages read

| URL | read on | official | prompt-injection-like instructions found |
|---|---|---|---|
| https://github.com/actions/setup-java/blob/v6.1.0/README.md | 2026-10-30 | yes | no |
| https://github.com/actions/setup-java/releases | 2026-10-30 (v6.0.0 notes truncated at "Read more") | yes | no |
| https://github.com/actions/setup-java/blob/v6.1.0/docs/advanced-usage.md | 2026-10-30 | yes | no |
| https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md | 2026-10-30 | yes | no |
| https://github.com/gradle/actions/releases | 2026-10-30 (v6.0.0 notes partly visible) | yes | no |
| https://github.com/gradle/actions/blob/v6.4.1/docs/dependency-submission.md | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/tutorials/build-and-test-code/java-with-maven | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/tutorials/build-and-test-code/java-with-gradle | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/tutorials/publish-packages/publish-java-packages-with-maven | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands | 2026-10-30 (job summary + annotation sections) | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows | 2026-10-30 (pull_request, pull_request_target sections) | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching | 2026-10-30 | yes | no |
| https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments | 2026-10-30 | yes | no |
| https://github.com/actions/upload-artifact/blob/v7.0.2/README.md | 2026-10-30 | yes | no |
| https://maven.apache.org/ref/3.10.0/maven-embedder/cli.html | 2026-10-30 | yes | no |
| https://maven.apache.org/docs/3.10.0/release-notes.html | 2026-10-30 | yes | no |
| https://maven.apache.org/tools/wrapper/ | 2026-10-30 | yes | no |
| https://maven.apache.org/surefire/maven-failsafe-plugin/usage.html | 2026-10-30 | yes | no |
| https://maven.apache.org/surefire/maven-surefire-plugin/test-mojo.html | 2026-10-30 (100000 of 102734 characters) | yes | no |
| https://maven.apache.org/surefire/maven-failsafe-plugin/integration-test-mojo.html | 2026-10-30 (100000 of 103662 characters) | yes | no |
| https://www.jacoco.org/jacoco/trunk/doc/maven.html | 2026-10-30 | yes | no |
| https://www.jacoco.org/jacoco/trunk/doc/changes.html | 2026-10-30 (top entries) | yes | no |
| https://docs.gradle.org/9.8.2/userguide/compatibility.html | 2026-10-30 | yes | no |
| https://docs.gradle.org/9.8.2/userguide/upgrading_major_version_9.html | 2026-10-30 | yes | no |
| https://docs.gradle.org/9.8.2/userguide/java_testing.html | 2026-10-30 | yes | no |
| https://docs.gradle.org/9.8.2/userguide/gradle_wrapper.html | 2026-10-30 | yes | no |
| https://docs.gradle.org/9.8.2/userguide/jacoco_plugin.html | 2026-10-30 | yes | no |
| https://docs.gradle.org/9.8.2/userguide/task_configuration_avoidance.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/lambda/latest/dg/java-package.html | 2026-10-30 | yes | no |
| https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html | 2026-10-30 | yes | no |
| https://github.com/GoogleContainerTools/jib/tree/master/jib-maven-plugin | 2026-10-30 (README on master, not a tag) | yes | no |

## Facts requested

| ID | Item | Value seen | Source | Why |
|---|---|---|---|---|
| FR1 | Maven Surefire / Failsafe plugin version | 3.6.1 (page header) | https://maven.apache.org/surefire/maven-surefire-plugin/test-mojo.html (2026-10-30) | Pin in pom examples (rule 11) |
| FR2 | maven-shade-plugin current version | not resolved (AWS page shows old 3.2.2) | https://maven.apache.org/plugins/maven-shade-plugin/ (not read) | Lambda JAR example |
| FR3 | jib-maven-plugin version | 3.5.2 (README on master) | https://github.com/GoogleContainerTools/jib/tree/master/jib-maven-plugin (2026-10-30) | Jib example; needs release-page confirmation |
| FR4 | JaCoCo latest release | 0.8.16 (2026/10/24) | https://www.jacoco.org/jacoco/trunk/doc/changes.html (2026-10-30) | Coverage plugin pin |
| FR5 | GitHub-hosted runner Maven version | "3.9.x" per setup-java docs | https://github.com/actions/setup-java/blob/v6.1.0/docs/advanced-usage.md (2026-10-30) | Justifies wrapper pin; runner-images page not read |

No new GitHub Action is needed beyond F4, F5, F10, F23, F24.

## Source Bibliography

### Primary Sources (all read 2026-10-30)
- actions/setup-java README v6.1.0 — https://github.com/actions/setup-java/blob/v6.1.0/README.md
- actions/setup-java advanced usage v6.1.0 — https://github.com/actions/setup-java/blob/v6.1.0/docs/advanced-usage.md
- actions/setup-java releases (v6.1.0 "14 Oct", v6.0.0 "24 Aug") — https://github.com/actions/setup-java/releases
- gradle/actions setup-gradle v6.4.1 — https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md
- gradle/actions dependency-submission v6.4.1 — https://github.com/gradle/actions/blob/v6.4.1/docs/dependency-submission.md
- gradle/actions releases (v6.4.1 "28 Oct", v6.0.0 "23 Mar") — https://github.com/gradle/actions/releases
- actions/upload-artifact README v7.0.2 — https://github.com/actions/upload-artifact/blob/v7.0.2/README.md
- Maven 3.10.0 CLI reference (Last Published 2026-09-27) — https://maven.apache.org/ref/3.10.0/maven-embedder/cli.html
- Maven 3.10.0 release notes (Last Published 2026-10-27) — https://maven.apache.org/docs/3.10.0/release-notes.html
- Maven Wrapper (site 3.3.4, Last Published 2025-09-08; current wrapper docs) — https://maven.apache.org/tools/wrapper/
- Surefire 3.6.1 test mojo — https://maven.apache.org/surefire/maven-surefire-plugin/test-mojo.html
- Failsafe 3.6.1 usage / integration-test mojo — https://maven.apache.org/surefire/maven-failsafe-plugin/usage.html, https://maven.apache.org/surefire/maven-failsafe-plugin/integration-test-mojo.html
- JaCoCo Maven plugin + change history — https://www.jacoco.org/jacoco/trunk/doc/maven.html, https://www.jacoco.org/jacoco/trunk/doc/changes.html
- Gradle 9.8.2 user guide: compatibility, upgrading to 9, Java testing, wrapper, JaCoCo plugin, task configuration avoidance — https://docs.gradle.org/9.8.2/userguide/
- GitHub Docs: Java with Maven, Java with Gradle, publish Java packages with Maven, workflow commands, events that trigger workflows, dependency caching, deployments and environments — https://docs.github.com/en/actions/
- AWS Lambda: Java .zip/JAR packaging; runtimes — https://docs.aws.amazon.com/lambda/latest/dg/java-package.html, https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
- Jib Maven plugin README — https://github.com/GoogleContainerTools/jib/tree/master/jib-maven-plugin

### Family facts used
- F4 setup-java v6.1.0, F5 gradle/actions v6.4.1, F10 checkout v7.0.1, F11 Java LTS, F12 Maven 3.10.0, F13 Gradle 9.8.2, F23 upload-artifact v7.0.2, F24 download-artifact v8.0.2 — `workspace/github-actions-cicd/_family_facts.md`
