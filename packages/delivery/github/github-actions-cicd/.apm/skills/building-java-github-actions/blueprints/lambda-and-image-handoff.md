# Lambda zip and image hand-off

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. This unit builds and uploads; it never pushes an image or updates a function.

## Lambda packaging options

Source for this table: https://docs.aws.amazon.com/lambda/latest/dg/java-package.html.

| Option | Layout | Notes |
|---|---|---|
| Gradle `Zip` task | project JAR and `runtimeClasspath` JARs in `lib/`; `build/distributions/*.zip` | Lambda loads `lib/` JARs in Unicode alphabetical order and the first duplicate class wins |
| Maven Shade JAR | one JAR with all dependencies in `target/` | AWS accepts a .zip or a JAR; `aws-lambda-java-log4j2` needs a Shade transformer |
| Multi-release JAR | shaded JAR placed in `lib/` and zipped | stated by AWS for multi-release JARs |
| Quarkus `function.zip` | produced by the Quarkus build | out of scope; see the Quarkus Lambda skills and `deploying-aws-lambda` |

- Packages above 50 MB go through S3 in the function's Region.
- Java 25 AOT caches are "strongly" discouraged for .zip or JAR deployments (same page).
- The reusable workflow wraps a Maven JAR under `lib/` for `package: zip`; AWS states that layout for multi-release JARs, so extending it to ordinary shaded JARs is a generalisation (medium confidence). A plain shaded JAR with `package: jar` is also accepted by AWS.
- The Maven zip step needs the `zip` binary (unverified, see the [register](./unverified-and-risks.md#tag-to-register-mapping)).

Duplicate-class check from the AWS page (run on the Gradle zip):

```bash
# Representative: adapt paths to your project
mkdir -p expanded && unzip -o build/distributions/*.zip -d expanded
find ./expanded/lib -name '*.jar' | xargs -n1 zipinfo -1 | grep '.*.class' | sort | uniq -c | sort
```

## Runtime choice

Package only from the matrix leg equal to the Lambda runtime: `java25`, `java21` or `java17.al2023` (all three deprecate Jun 30, 2029); `java17` on AL2 is deprecated Jun 30, 2027. Source: https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html. The JDK in the artifact name (`app-<sha>-jdk21`) tells the release which leg built it.

## Image hand-off

| Path | Who builds the image | This unit does |
|---|---|---|
| Dockerfile (default) | `publishing-container-images-github-actions` from the JAR artifact | `package: image` uploads the JAR and exports `artifact-name` and `artifact-digest` |
| Jib `buildTar` | this unit may write `target/jib-image.tar`; the push stays with the publishing unit | optional |

Jib notes, from the plugin README on the master branch, not a tag (medium confidence): `jib:buildTar` writes `target/jib-image.tar` and is not described as needing Docker; `jib:dockerBuild` needs `docker` on PATH; `jib:build` pushes to a registry and therefore belongs to the publishing unit and to `cd-*` only; the default base is `eclipse-temurin:{8,11,17,21,25}-jre`.

```xml
<plugin>
  <groupId>com.google.cloud.tools</groupId>
  <artifactId>jib-maven-plugin</artifactId>
  <version><!-- current version from the Jib releases page --></version>
</plugin>
```

```bash
./mvnw -B -ntp package jib:buildTar   # expected: target/jib-image.tar
```

The README showed 3.5.2; the Jib version is not a family fact, so keep the placeholder.

## Hand-off contract

1. `cd-<app>.yml` calls `./.github/workflows/_java-build.yml` with `package: zip` (Lambda) or `image`.
2. It passes `needs.build.outputs.artifact-name` and `artifact-digest` to the release workflow of `deploying-aws-lambda` or to the image workflow of `publishing-container-images-github-actions`.
3. The consumer downloads that artifact with `actions/download-artifact` (v8.0.2, `9000827ccba6bdab643e8b6fd33ac0654aef8333`) and deploys the same file; it never rebuilds.

Caller wiring: [callers](./workflow-callers.md).
