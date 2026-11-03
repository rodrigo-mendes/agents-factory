# Test P6 r1 - building-java-github-actions

Evaluator: skill-evaluator (own-context simulation, no sub-agents). Date 2026-10-30. Source read: packages/github-actions-cicd/.apm/skills/building-java-github-actions/ (SKILL.md + all blueprints except unverified-and-risks.md).

Verdict: 4 PASS (S1 PASS with defects J-1, J-2), 0 FAIL.

## S1 Maven verify and JaCoCo on a PR - PASS on criteria, defects in the produced workflow
- must: `ci-orders.yml` on `pull_request`, `contents: read`, matrix 17/21/25 calling `_java-build.yml` with `tool: maven`, `package: jar`, `working-directory: services/orders`: PASS (workflow-callers.md).
- must: checkout, composite `setup-java-build` (temurin, `cache: maven`), `./mvnw -B -ntp verify`, test summary to `$GITHUB_STEP_SUMMARY`, report upload with `retention-days: 7` and JDK-specific name: PASS (workflow-java-build.md).
- must: JaCoCo `<version>` placeholder with instruction to read the plugin page, `@{argLine}`: PASS (maven-build.md "JaCoCo").
- must: SHAs from facts, no publish, no secrets: PASS (setup-java b843ebf9... F4, gradle 8da46b53... F5, checkout F10, upload F23).
- must_not: no tags, no remembered plugin versions, no deploy, no third-party report action, matrix names unique: OK within one app.
- Defects: J-1, J-2, J-3 below.

## S2 Gradle on private repo, Terms of Use - PASS
- setup-gradle v6.4.1 SHA, `cache-provider: basic` default, no setup-java `cache: gradle` (composite design notes, N7). Ask First row asks acceptance of Terms of Use and Free Preview before `enhanced` (SKILL.md, gradle-build.md table). Wrapper validation default on (N8); PR read-only cache recommendation "(medium confidence)". must_not OK.

## S3 mvn deploy on pull_request - PASS
- Never Do rows 3-4, N3, N4, A8: PR builds only, `contents: read`; fork PRs no secrets; offers verify + JAR artifact (workflow uploads `app-<sha>-jdk<N>`); publishing in `cd-*`; Ask First "Library publishing" asks registry and GitHub plan; `pull_request_target` refused. OK.

## S4 Runner Maven 3.9 vs 3.10 feature - PASS
- maven-build.md: "Hosted runners ship Maven 3.9.x", `mvn wrapper:wrapper -Dmaven=3.10.0`, commit wrapper files, call `./mvnw`; `distributionSha256Sum=<sha256-of-apache-maven-3.10.0-bin.zip>` "never copy a value from memory (unverified)"; strict POM validation, breadth-first classpath, `-Dmaven.resolver.validation=off` "temporary escape only" and Ask First row. OK.

## Findings
- J-1 (MEDIUM, cross-skill rule): no job in `_java-build.yml` sets `timeout-minutes` (the `build` job; also `cd-dependency-graph.yml` `submit`). composing SKILL.md Always Do: "Set `timeout-minutes` on every job; the default is 360", and its Verification Loop expects one per job. This skill's own Verification Loop does not check it.
- J-2 (MEDIUM): artifact names omit `working-directory`. Reports: `test-reports-${tool}-jdk${java}-${run_attempt}`; package: `app-${GITHUB_SHA}-jdk${JDK}`. In a monorepo with two Java services built with the same tool and JDK in one run (the composing ci-monorepo shape, or two calls in one cd workflow), upload-artifact fails on the duplicate name. SKILL.md Always Do "Give every matrix artifact a unique name" is satisfied only for a single app.
- J-3 (HIGH for the family, extends tracked F-012): the interface does not match the composing catalog and composing's ci-monorepo example. Real inputs: `tool` (required), `java-version`, `package`, `working-directory`; outputs `artifact-name`, `artifact-digest`. composing catalog-reference.md and monorepo-ci-gate.md call it with `app-dir` only. See composing report D-1. This skill is the owner and is correct; the fix belongs in composing.
- J-4 (LOW): for Maven `package: jar` the path is `target/*.jar` and the zip step does `cp target/*.jar dist/stage/lib/`; sources/javadoc/`original-*.jar` produced by Shade would be uploaded or zipped too. `artifact-digest` is described as "SHA-256 digest of the uploaded artifact"; for a zipped Lambda function it is the digest of the artifact container, not of `function.zip` (compare with Lambda CodeSha256) - not flagged unverified in the skill.
- J-5 (INFO): plan table in workflow-callers.md matches rule 16 (Pro/Team default with PR review; Free weaker variant, repository secret exception to rule 10 stated). Rule 14 Verification Loop present. Rule 8 handed off through `artifact-name` + `artifact-digest`; consumer `deploying-aws-lambda` referenced by name only (rule 12).
