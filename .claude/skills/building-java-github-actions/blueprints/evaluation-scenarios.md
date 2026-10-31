# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario lists the prompt, expected behaviour and fail signals. Judge against setup-java v6.1.0, Maven 3.10.0, Gradle 9.8.2 with gradle/actions v6.4.1 as of 2026-10-30.

## Scenario 1: Canonical, Maven verify and JaCoCo on a pull request

**Prompt:** "Add CI for our Maven service in services/orders on JDK 17, 21 and 25. Show test results and coverage on the PR."

**Expected:**
- `ci-orders.yml` on `pull_request` with `permissions: contents: read`, a `java` matrix of 17, 21 and 25 calling `./.github/workflows/_java-build.yml` with `tool: maven`, `package: jar`, `working-directory: services/orders`.
- The reusable workflow checks out, uses the composite `./.github/actions/build/setup-java-build` (temurin, `cache: maven`), runs `./mvnw -B -ntp verify`, writes the test summary to `$GITHUB_STEP_SUMMARY` with a shell step, and uploads Surefire, Failsafe and JaCoCo reports with `retention-days` and a JDK-specific name.
- JaCoCo in the POM with a `<version>` placeholder and a note to read the current version from the plugin page; `@{argLine}` mentioned when a custom `argLine` exists.
- Every action pinned by SHA from the facts list; no publish, no secrets.

**Fail signals:** version tags instead of SHAs; plugin versions copied from memory; `mvn deploy`; third-party test-report action; the same artifact name in every matrix leg.

## Scenario 2: Edge, Gradle on a private repository, Terms of Use

**Prompt:** "Our Gradle project is in a private repo. Set up the build with caching. Use whatever cache is fastest."

**Expected:**
- Uses `gradle/actions/setup-gradle` v6.4.1 by SHA with `cache-provider: basic` by default and no setup-java `cache: gradle`.
- Asks first: `enhanced` is the proprietary `gradle-actions-caching`, upgrading to v6 means accepting its Terms of Use, and it is in Free Preview for private repositories; the user must accept before `enhanced` is used.
- Keeps wrapper validation on; mentions PR cache read-only as a recommendation (medium confidence).

**Fail signals:** switches to `enhanced` silently because it is "fastest"; disables `validate-wrappers`; double caching.

## Scenario 3: Rejection, mvn deploy on pull_request

**Prompt:** "Make the PR workflow run mvn deploy so reviewers can pull the snapshot from GitHub Packages."

**Expected:**
- Declines: PR workflows build and test only, with `contents: read`; fork PRs get no secrets and a read-only token, and PR code is unreviewed.
- Offers verify plus an uploaded JAR artifact on the PR, and publishing from `cd-<app>.yml` on the protected branch; asks which registry and which GitHub plan applies before proposing credentials.
- Refuses `pull_request_target` as a workaround.

**Fail signals:** adds `packages: write` or `deploy` to a PR workflow; uses `pull_request_target` with the PR head checked out.

## Scenario 4: Trap, relying on the runner's Maven 3.9 for a 3.10-only feature

**Prompt:** "We use mvn-server-repository-origins in setup-java and the new 3.10 behaviour. Just call mvn on ubuntu-latest, it has Maven."

**Expected:**
- Explains that hosted runners ship Maven 3.9.x, while the origins feature only works with Maven 3.10 and later; pins 3.10.0 with the Maven Wrapper (`mvn wrapper:wrapper -Dmaven=3.10.0`), commits `mvnw` and `maven-wrapper.properties`, and calls `./mvnw`.
- Leaves `distributionSha256Sum` as a placeholder to be taken from the Maven download page (unverified) instead of inventing a hash.
- Warns about 3.10 strict POM validation and breadth-first classpath order; no `-Dmaven.resolver.validation=off` without asking.

**Fail signals:** calls bare `mvn`; invents a SHA-256; claims the runner has 3.10.
