---
name: building-java-github-actions
description: "Builds Java CI on GitHub Actions: reusable Maven 3.10 or Gradle 9.8 build workflow, JDK 17/21/25 matrix, JaCoCo, test summary, Lambda zip or image hand-off. Use when writing or reviewing Java pipelines. Publishing only in cd-* callers."
---

# Java builds on GitHub Actions (Maven 3.10, Gradle 9.8, JDK 17/21/25)

> Version lock: every claim applies to **actions/setup-java v6.1.0**, **Maven 3.10.0 via the Maven Wrapper**, **Gradle 9.8.2 with gradle/actions v6.4.1** and JDK LTS 25/21/17 on GitHub.com hosted runners. Research date **2026-10-30**.
> Claims tagged unverified or medium confidence were not fully confirmed against an official page; each tag maps to the [register](./blueprints/unverified-and-risks.md#tag-to-register-mapping).
> Scope: build, test, coverage, package. How `workflow_call` works belongs to `composing-github-actions-pipelines`; image push belongs to `publishing-container-images-github-actions`; Lambda release belongs to `deploying-aws-lambda`; SHA pinning and injection-safe scripting belong to `automating-github-repos-with-actions`.
> Provenance: the dated research file for this unit under the factory workspace; this skill never reads it at run time.

## Version Context

| Item | Value | Source (fetched 2026-10-30) |
|---|---|---|
| `actions/setup-java` | v6.1.0 = `b843ebf9b913146b38da2eaa7aeddf76074ae1ad` | https://github.com/actions/setup-java/releases |
| `gradle/actions` | v6.4.1 = `8da46b539cd8fe6ab27ca75128919a18d757604c` | https://github.com/gradle/actions/releases |
| `actions/checkout` | v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1` | https://github.com/actions/checkout/releases |
| `actions/upload-artifact` | v7.0.2 = `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | https://github.com/actions/upload-artifact/releases |
| `actions/download-artifact` | v8.0.2 = `9000827ccba6bdab643e8b6fd33ac0654aef8333` | https://github.com/actions/download-artifact/releases |
| Maven | 3.10.0 (2026-09-27); 3.9.16 still supported; Maven 4 not GA | https://maven.apache.org/docs/history.html |
| Gradle | 9.8.2 (2026-10-19) | https://gradle.org/releases/ |
| Java LTS | 25 (to Sep 2031), 21 (Dec 2029), 17 (Oct 2027) | https://adoptium.net/support/ |
| Surefire, Failsafe, JaCoCo, Jib, Shade | not family facts: blueprints show `<version>` placeholders; take the current version from the plugin page | https://maven.apache.org/surefire/maven-surefire-plugin/ |

**Version-lifetime risk** (as of 2026-10-30; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Maven 3.10.0 (2026-09-27) is a new minor line and turns many 3.9 warnings into build failures; runners still ship 3.9.x.
- gradle/actions v6 caching is proprietary under Terms of Use; v6.4.1 fixes an advisory in `dependency-submission`.
- Java 17 minimum support ends Oct 2027; Lambda `java17` on AL2 is deprecated Jun 30, 2027.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Verification Loop](#verification-loop)
- [Always-do patterns](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [Reusable workflow _java-build.yml](./blueprints/workflow-java-build.md)
- [Composite action setup-java-build](./blueprints/composite-setup-java-build.md)
- [Maven: wrapper, 3.10 changes, reports, JaCoCo](./blueprints/maven-build.md)
- [Gradle: setup-gradle, caching terms, JaCoCo, dependency graph](./blueprints/gradle-build.md)
- [Lambda zip and image hand-off](./blueprints/lambda-and-image-handoff.md)
- [Callers: ci, cd and JDK matrix](./blueprints/workflow-callers.md)
- [Unverified and risks register](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

Shape: `./.github/workflows/_java-build.yml` (inputs `tool`, `java-version`, `package`, `working-directory`; outputs `artifact-name`, `artifact-digest`) does build, test, coverage summary and packaging; the composite `./.github/actions/build/setup-java-build` installs the JDK and caches. Callers `ci-<app>.yml` (pull_request) and `cd-<app>.yml` (merge) wire them. Publishing exists only in `cd-*`.

### ✅ Always Do

- **Pin `distribution` and `java-version` explicitly in `actions/setup-java`** ([README](https://github.com/actions/setup-java/blob/v6.1.0/README.md)).
- **Pin Maven 3.10.0 with the Maven Wrapper** ([advanced usage](https://github.com/actions/setup-java/blob/v6.1.0/docs/advanced-usage.md)).
- **Know that hosted runners ship Maven 3.9.x**, which is why the wrapper pin matters ([advanced usage](https://github.com/actions/setup-java/blob/v6.1.0/docs/advanced-usage.md)).
- **Commit `distributionSha256Sum` in `maven-wrapper.properties`** ([Maven Wrapper](https://maven.apache.org/tools/wrapper/)).
- **Run `./mvnw -B -ntp verify`** so batch mode and no transfer progress apply ([Maven 3.10.0 CLI](https://maven.apache.org/ref/3.10.0/maven-embedder/cli.html)).
- **Use the `verify` phase so Failsafe integration tests run** ([Failsafe usage](https://maven.apache.org/surefire/maven-failsafe-plugin/usage.html)).
- **Cache Maven with `cache: maven` in setup-java** ([README](https://github.com/actions/setup-java/blob/v6.1.0/README.md)).
- **Keep sensitive data out of caches** ([dependency caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching)).
- **Run `gradle/actions/setup-gradle` before `./gradlew build`** ([setup-gradle](https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md)).
- **Leave Gradle wrapper validation at its default (on)** ([setup-gradle](https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md)).
- **Give every matrix artifact a unique name** ([upload-artifact](https://github.com/actions/upload-artifact/blob/v7.0.2/README.md)).
- **Set `retention-days` on every upload**; the default is 90 days ([store and share data](https://docs.github.com/en/actions/tutorials/store-and-share-data)).
- **Write the test summary to `$GITHUB_STEP_SUMMARY`** with a shell step ([workflow commands](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands)).
- **Give pull-request workflows `permissions: contents: read`** ([events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)).
- **Set `timeout-minutes` on every job and `concurrency` on every caller workflow** ([workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)).
- **Publish and deploy only from `cd-*` callers** (fork PRs get no secrets per [events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)).
- **Promote the uploaded file and its `artifact-digest`, never a rebuild** (digest output in [upload-artifact](https://github.com/actions/upload-artifact/blob/v7.0.2/README.md)).

Code for each rule: [always-do patterns](./blueprints/always-do-patterns.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Gradle cache provider on private repos | `basic` (MIT, default here) vs `enhanced` (proprietary `gradle-actions-caching`; "By upgrading to v6, you accept the Terms of Use"; Free Preview for private repos) | "Do you accept the gradle-actions-caching Terms of Use for this private repository?" |
| Cache writes on pull requests | Read-only cache on PR runs is a recommendation (medium confidence); GitHub already scopes PR caches to the merge ref, so no setup-java input is passed | "Should PR runs only read the cache?" |
| Maven 3.10 strictness | Fix the POM vs temporary `-Dmaven.resolver.validation=off` | "Fix duplicate declarations now or allow a temporary escape?" |
| Lambda packaging | Gradle `Zip` task (lib/ layout), Maven Shade JAR, Quarkus `function.zip` (by name only); Maven zip wrapping a JAR under lib/ is a generalisation (medium confidence) | "Which build tool and is a multi-release JAR in use?" |
| Shade plugin version | current maven-shade-plugin version not resolved (unverified) | "Which Shade version does the project already use?" |
| Container image | Hand the JAR to a Dockerfile build vs Jib `buildTar` (README on master, medium confidence) | "Is Jib already used?" |
| JDK matrix | 17/21/25 triples minutes; only the leg equal to the target runtime packages | "Which JDKs must pass, and which one is the runtime?" |
| Dependency graph | `contents: write` on a push job vs no submission | "Submit the Gradle dependency graph on push to main?" |
| Library publishing | `GITHUB_TOKEN` to GitHub Packages vs stored registry token; environment secrets in private repos need Pro/Team | "Which registry and which GitHub plan owns this repository?" |
| Maven Wrapper missing | Generate and commit it vs install Maven separately | "May the build add `mvnw` to the repository?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Use `distribution: adopt*` with setup-java v6 ([README](https://github.com/actions/setup-java/blob/v6.1.0/README.md)) | `temurin` or `semeru` |
| Use `server-password` and sibling old names ([README](https://github.com/actions/setup-java/blob/v6.1.0/README.md)) | `server-password-env-var` |
| Run `mvn deploy` or any publish from `pull_request` ([events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)) | verify on PR, deploy in `cd-*` |
| Build PR code under `pull_request_target` ([events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)) | `pull_request` with `contents: read` |
| Ignore failing tests with `-Dmaven.test.failure.ignore=true` ([Surefire](https://maven.apache.org/surefire/maven-surefire-plugin/test-mojo.html)) | let the job fail; upload reports |
| Rebuild per environment ([upload-artifact](https://github.com/actions/upload-artifact/blob/v7.0.2/README.md)) | download the same artifact |
| Add setup-java `cache: gradle` beside setup-gradle ([setup-gradle](https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md)) | one cache owner; `cache-provider: basic` |
| Set `validate-wrappers: false` or `allow-snapshot-wrappers: true` ([setup-gradle](https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md)) | omit both inputs |

Examples with alternatives: [never-do patterns](./blueprints/never-do-patterns.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| Hosted runner Maven | 3.9.x | https://github.com/actions/setup-java/blob/v6.1.0/docs/advanced-usage.md |
| Maven batch flags | `-B` non-interactive, `-ntp` no transfer progress | https://maven.apache.org/ref/3.10.0/maven-embedder/cli.html |
| Gradle JVM range | runs on JVM 17 to 27; Java 25 needs Gradle 9.1.0+ | https://docs.gradle.org/9.8.2/userguide/compatibility.html |
| Reports | `target/surefire-reports`, `target/failsafe-reports`, `build/test-results/test` | https://maven.apache.org/surefire/maven-surefire-plugin/test-mojo.html |
| Job summary | 1 MiB per step, 20 per job | https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands |
| Cache limits | 10 GB per repository; unused 7 days evicted | https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching |
| Artifact retention | default 90 days | https://docs.github.com/en/actions/tutorials/store-and-share-data |
| Lambda direct upload | below 50 MB, else via S3 | https://docs.aws.amazon.com/lambda/latest/dg/java-package.html |
| Reusable workflow location | workflows folder, no subfolders | https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows |

## Verification Loop

Run offline from the repository root after generating files. Expected output in the comment.

```bash
grep -rnE 'uses: [^ ]+@v[0-9]' .github/workflows .github/actions   # expected: no output (all SHA-pinned)
grep -rnE 'uses: [^ ]+@[0-9a-f]{40} # v' .github/workflows/_java-build.yml .github/actions/build   # expected: one line per action
grep -nE 'deploy|publish|packages: write' .github/workflows/ci-*.yml   # expected: no output
grep -n 'contents: read' .github/workflows/_java-build.yml .github/workflows/ci-*.yml   # expected: at least one hit per file
grep -rn 'distribution:' .github/actions/build   # expected: temurin only
./mvnw -v | head -1        # expected: Apache Maven 3.10.0
./gradlew --version | grep '^Gradle'   # expected: Gradle 9.8.2 (Gradle projects)
```

## External Resources

All fetched 2026-10-30.

- [setup-java v6.1.0 README](https://github.com/actions/setup-java/blob/v6.1.0/README.md)
- [setup-gradle v6.4.1](https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md)
- [Maven 3.10.0 release notes](https://maven.apache.org/docs/3.10.0/release-notes.html)
- [Gradle 9.8.2 user guide](https://docs.gradle.org/9.8.2/userguide/)
- [AWS Lambda Java packaging](https://docs.aws.amazon.com/lambda/latest/dg/java-package.html)
- [Full bibliography](./blueprints/unverified-and-risks.md#source-bibliography)
