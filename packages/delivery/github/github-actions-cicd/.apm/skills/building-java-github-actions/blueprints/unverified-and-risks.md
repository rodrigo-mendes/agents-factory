# Unverified and risks register

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Tags are plain parentheses: (unverified) and (medium confidence).

## Version-lifetime risk

As of 2026-10-30.

- Maven 3.10.0 shipped on 2026-09-27; many 3.9 warnings now fail the build and classpath order changed. Hosted runners still ship 3.9.x, so the wrapper pin is what makes 3.10 behaviour reproducible. Source: https://maven.apache.org/docs/3.10.0/release-notes.html
- Maven 4 is not GA (4.0.0-rc-7); this skill does not target it. Source: https://maven.apache.org/docs/history.html
- gradle/actions v6 caching is proprietary under Terms of Use; v6.4.1 fixes GHSA-chpw-2mqm-95cc in `dependency-submission`. Re-read the releases page before moving the pin. Source: https://github.com/gradle/actions/releases
- setup-java v6 deprecates the old credential input names; removal timing is not published. Source: https://github.com/actions/setup-java/releases
- Java 17 minimum support ends Oct 2027; Lambda `java17` on AL2 is deprecated Jun 30, 2027 and `java25`, `java21`, `java17.al2023` on Jun 30, 2029. Sources: https://adoptium.net/support/, https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
- Pinned SHAs (setup-java v6.1.0, gradle/actions v6.4.1, checkout v7.0.1, upload-artifact v7.0.2, download-artifact v8.0.2) were resolved on 2026-10-30; re-run `git ls-remote` before bumping.
- Plugin versions (Surefire, Failsafe, JaCoCo, Jib, Shade) are placeholders in the blueprints on purpose; they are not family facts.

## Unverified (8)

| ID | Claim | Impact | Workaround |
|---|---|---|---|
| U1 | setup-java behaviour for `cache: ''` (empty string) | a single step with an empty cache may misbehave | two setup-java steps selected with `if:` |
| U2 | SHA-256 of `apache-maven-3.10.0-bin.zip` for `distributionSha256Sum` | wrapper has no checksum | placeholder; take the value from the Maven download page |
| U3 | gradle/actions v6 Node runtime and removed inputs | an input used in an old workflow may be gone | read the v6.0.0 release note before upgrading from v5 |
| U4 | Removal date of setup-java deprecated input aliases | breakage on removal | use the `*-env-var` names now |
| U5 | Current maven-shade-plugin version | wrong pin in the Lambda JAR example | placeholder; take it from the Shade plugin page |
| U6 | `zip` binary present on `ubuntu-latest` | Maven zip step fails | use the Gradle zip task or add an install step |
| U7 | setup-gradle input for a build root other than the repository root | cache or summary scope wrong in monorepos | keep the Gradle project at the repository root |
| U8 | `inputs` context available in `defaults.run.working-directory` and in a local composite action `with:` | workflow fails validation | repeat `working-directory` on each step |

## Irresolvable (0)

No irresolvable items recorded in this unit.

## Medium confidence (8)

| ID | Claim | Why medium | Check |
|---|---|---|---|
| M1 | Surefire and Gradle JUnit XML attributes `tests`, `failures`, `errors`, `skipped` on the first `<testsuite` tag | schema page not read | read the Surefire XML report schema |
| M2 | `if: always()` keeps report steps running after a failed step | expressions page not re-read | read the status-check functions page |
| M3 | Read-only cache on PR runs (explicit stance, Gradle and Maven) | recommendation; GitHub already scopes PR caches; no setup-java input is used | confirm with the user |
| M4 | Kotlin `tasks.register<Zip>("buildZip")` equals the AWS Groovy snippet | translation, not shown on either page | run `./gradlew build buildZip` |
| M5 | A shaded Maven JAR under `lib/` in a zip is accepted by Lambda | AWS states it for multi-release JARs only | deploy to a test function |
| M6 | Jib `buildTar` and `target/jib-image.tar` behaviour | README read on master, not a tag | read the README at the release tag |
| M7 | JaCoCo Maven details (`forkCount`, `@{argLine}`, report path) | trunk page is unversioned | read the page for the pinned version |
| M8 | Surefire and Failsafe current version | version seen in a page header, not a release page | read the plugin release history |

## Coverage limits (6)

| ID | Limit |
|---|---|
| L1 | Surefire test mojo page read for 100000 of 102734 characters; Failsafe integration-test mojo page 100000 of 103662 |
| L2 | setup-java releases page: the v6.0.0 notes were truncated at "Read more" |
| L3 | gradle/actions releases page: the v6.0.0 notes were only partly visible |
| L4 | GitHub tutorials for Maven, Gradle and publishing show older action majors (setup-java v4, upload-artifact v4); this skill uses only the pinned versions from the family facts |
| L5 | The runner Maven version "3.9.x" comes from the setup-java docs; the runner-images page was not read |
| L6 | Which GitHub plan owns the repository is unknown; environment features depend on it |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | composite-setup-java-build.md design notes (`cache: ''`) | U1 |
| (unverified) | maven-build.md wrapper pin (checksum) | U2 |
| (unverified) | gradle-build.md migration notes (Node runtime) | U3 |
| (unverified) | never-do-patterns.md N2 | U4 |
| (unverified) | SKILL.md Ask First (Shade); maven-build.md Lambda JAR with Shade | U5 |
| (unverified) | workflow-java-build.md notes; lambda-and-image-handoff.md packaging options | U6 |
| (unverified) | composite-setup-java-build.md design notes; gradle-build.md wrapper | U7 |
| (unverified) | workflow-java-build.md notes (inputs context) | U8 |
| (medium confidence) | workflow-java-build.md notes (summary parser) | M1 |
| (medium confidence) | workflow-java-build.md notes; always-do-patterns.md A6 | M2 |
| (medium confidence) | SKILL.md Ask First (cache writes); gradle-build.md setup and caching | M3 |
| (medium confidence) | gradle-build.md Lambda zip task | M4 |
| (medium confidence) | SKILL.md Ask First (Lambda packaging); lambda-and-image-handoff.md packaging options | M5 |
| (medium confidence) | SKILL.md Ask First (container image); lambda-and-image-handoff.md image hand-off | M6 |
| (medium confidence) | maven-build.md JaCoCo | M7 |
| (medium confidence) | maven-build.md Surefire and Failsafe | M8 |

## Source Bibliography

All fetched 2026-10-30.

**GitHub Actions repositories**
- https://github.com/actions/setup-java/blob/v6.1.0/README.md
- https://github.com/actions/setup-java/blob/v6.1.0/docs/advanced-usage.md
- https://github.com/actions/setup-java/releases
- https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md
- https://github.com/gradle/actions/blob/v6.4.1/docs/dependency-submission.md
- https://github.com/gradle/actions/releases
- https://github.com/actions/upload-artifact/blob/v7.0.2/README.md

**GitHub Docs**
- https://docs.github.com/en/actions/tutorials/build-and-test-code/java-with-maven
- https://docs.github.com/en/actions/tutorials/build-and-test-code/java-with-gradle
- https://docs.github.com/en/actions/tutorials/publish-packages/publish-java-packages-with-maven
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching
- https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- https://docs.github.com/en/actions/tutorials/store-and-share-data

**Maven, Surefire, JaCoCo**
- https://maven.apache.org/ref/3.10.0/maven-embedder/cli.html
- https://maven.apache.org/docs/3.10.0/release-notes.html
- https://maven.apache.org/docs/history.html
- https://maven.apache.org/tools/wrapper/
- https://maven.apache.org/surefire/maven-surefire-plugin/test-mojo.html
- https://maven.apache.org/surefire/maven-failsafe-plugin/usage.html
- https://maven.apache.org/surefire/maven-failsafe-plugin/integration-test-mojo.html
- https://www.jacoco.org/jacoco/trunk/doc/maven.html
- https://www.jacoco.org/jacoco/trunk/doc/changes.html

**Gradle**
- https://docs.gradle.org/9.8.2/userguide/compatibility.html
- https://docs.gradle.org/9.8.2/userguide/upgrading_major_version_9.html
- https://docs.gradle.org/9.8.2/userguide/java_testing.html
- https://docs.gradle.org/9.8.2/userguide/gradle_wrapper.html
- https://docs.gradle.org/9.8.2/userguide/jacoco_plugin.html
- https://docs.gradle.org/9.8.2/userguide/task_configuration_avoidance.html

**Cloud and image tooling**
- https://docs.aws.amazon.com/lambda/latest/dg/java-package.html
- https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
- https://github.com/GoogleContainerTools/jib/tree/master/jib-maven-plugin
- https://adoptium.net/support/
- SHA verification: `git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag>`
