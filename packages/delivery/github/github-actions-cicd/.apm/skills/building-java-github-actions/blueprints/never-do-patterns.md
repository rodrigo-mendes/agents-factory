# Never-do patterns with examples

Back to [SKILL.md](../SKILL.md). setup-java v6.1.0, Maven 3.10.0, Gradle 9.8.2; research date 2026-10-30. Each pattern shows the wrong form and the alternative.

Contents: N1 adopt | N2 old credential names | N3 publish on PR | N4 pull_request_target | N5 ignored failures | N6 rebuild | N7 double cache | N8 wrapper validation

## N1. Removed `adopt` distributions

v6 removed the legacy AdoptOpenJDK distributions; use `temurin` (for `adopt`, `adopt-hotspot`) or `semeru` (for `adopt-openj9`).

```yaml
# ❌ Wrong
with: { distribution: adopt, java-version: '17' }
# ✅ Correct
with: { distribution: temurin, java-version: '17' }
```

Source: https://github.com/actions/setup-java/blob/v6.1.0/README.md

## N2. Old credential input names

`server-username`, `server-password` and `gpg-passphrase` were renamed to `*-env-var`; the old names are deprecated aliases that warn. The values are names of environment variables, not secrets. The removal date of the aliases is not published (unverified).

```yaml
# ❌ Wrong
with: { server-id: central, server-password: MAVEN_TOKEN }
# ✅ Correct (the step env maps MAVEN_TOKEN from an environment secret)
with: { server-id: central, server-password-env-var: MAVEN_TOKEN }
```

Source: https://github.com/actions/setup-java/blob/v6.1.0/README.md

## N3. Publishing or deploying from `pull_request`

PR code is untrusted branch code; fork PRs get no secrets and a read-only token.

```yaml
# ❌ Wrong
on: pull_request
jobs: { release: { runs-on: ubuntu-latest, steps: [ { run: ./mvnw -B deploy } ] } }
# ✅ Correct
# ci-orders.yml (pull_request): ./mvnw -B -ntp verify
# cd-orders.yml (push to main): publish with packages: write
```

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

## N4. PR code under `pull_request_target`

The events page says to avoid this event "if you need to build or run code from the pull request"; risks include cache poisoning and unintended access to write privileges or secrets.

```yaml
# ❌ Wrong
on: pull_request_target
# steps: checkout of the PR head sha, then ./gradlew build
# ✅ Correct
on: pull_request
permissions: { contents: read }
```

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

## N5. Ignoring test failures

Surefire `testFailureIgnore`: "Its use is NOT RECOMMENDED". Gradle 9 `test` fails when it runs but discovers no tests.

```bash
# ❌ Wrong
./mvnw -B verify -Dmaven.test.failure.ignore=true
# ✅ Correct (failing tests fail the job; reports are uploaded by an always() step)
./mvnw -B -ntp verify
```

Sources: https://maven.apache.org/surefire/maven-surefire-plugin/test-mojo.html, https://docs.gradle.org/9.8.2/userguide/upgrading_major_version_9.html

## N6. Rebuilding the artifact per environment

The uploaded file has a SHA-256 `artifact-digest`; builds are reproducible only for the same inputs, so a rebuild is a different binary.

```yaml
# ❌ Wrong
deploy-prod: { steps: [ { run: ./gradlew buildZip } ] }
# ✅ Correct: download the zip built once (actions/download-artifact v8.0.2)
deploy-prod: { steps: [ { uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 } ] }  # v8.0.2
```

Source: https://github.com/actions/upload-artifact/blob/v7.0.2/README.md

## N7. Double caching Gradle User Home

When another tool manages Gradle User Home, setup-gradle wants `cache-provider: external`; two owners waste the 10 GB repository quota and make the summary inaccurate.

```yaml
# ❌ Wrong
- uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
  with: { distribution: temurin, java-version: '25', cache: gradle }
- uses: gradle/actions/setup-gradle@8da46b539cd8fe6ab27ca75128919a18d757604c # v6.4.1
# ✅ Correct
- uses: actions/setup-java@b843ebf9b913146b38da2eaa7aeddf76074ae1ad # v6.1.0
  with: { distribution: temurin, java-version: '25' }
- uses: gradle/actions/setup-gradle@8da46b539cd8fe6ab27ca75128919a18d757604c # v6.4.1
  with: { cache-provider: basic }
```

Sources: https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md, https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching

## N8. Disabling wrapper validation

Validation checks wrapper jars against known checksums and is on by default; snapshot wrappers are refused by default. A tampered `gradle-wrapper.jar` in a PR would run arbitrary code.

```yaml
# ❌ Wrong
with: { validate-wrappers: false, allow-snapshot-wrappers: true }
# ✅ Correct: omit both inputs (defaults validate and refuse snapshots)
```

Source: https://github.com/gradle/actions/blob/v6.4.1/docs/setup-gradle.md
