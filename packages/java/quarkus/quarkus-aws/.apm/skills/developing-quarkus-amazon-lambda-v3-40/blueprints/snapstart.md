# SnapStart for Quarkus 3.40 JVM functions

Back to [SKILL.md](../SKILL.md). Fetched 2026-10-28. SnapStart applies to JVM builds on Java managed runtimes only; the choice against native is Ask First ([C1](./ask-first-decisions.md#c1-jvm-snapstart-or-native)).

## Platform facts (AWS)

| Aspect | Value | Source |
|---|---|---|
| Supported | Java managed runtimes; OS-only runtimes "are not supported" | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html |
| Targets | published versions and aliases pointing to versions; not `$LATEST` | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html |
| Incompatible with | provisioned concurrency, EFS, S3 Files, ephemeral storage above 512 MB | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html |
| Cost | no additional cost on Java managed runtimes; duration charges include runtime hooks | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html |
| Version states | `Pending`, `Active`, `Inactive`, `Failed` | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html |
| Idle | Java snapshot deleted after 14 days without invocation; the version goes `Inactive`, the next invoke returns `SnapStartNotReadyException` and a new snapshot is initialised. Rollback to an old version: wait for `Active` (check `get-function-configuration` on the version: `SnapStart.OptimizationStatus=On`, `State=Active`) | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html |
| Regions | all commercial Regions except Asia Pacific (New Zealand) and Asia Pacific (Taipei); the Quarkus guide says only "not in all regions" | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html |
| Credentials | the runtime uses container credentials (`AWS_CONTAINER_CREDENTIALS_FULL_URI`, `AWS_CONTAINER_AUTHORIZATION_TOKEN`) instead of access-key env vars "to prevent credentials from expiring before the function is restored" | https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html |
| Connections | network connections opened at init are "not guaranteed" after restore; AWS SDK connections "in most cases" resume | https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html |

Refresh ephemeral data (temporary credentials, cached timestamps) in the handler. Secrets come from Secrets Manager or SSM, never from code.

## Quarkus properties (3.40 configuration reference)

| Property | Default | Note |
|---|---|---|
| `quarkus.snapstart.enabled` | page not recorded | replaces deprecated `quarkus.snapstart.enable` (since 3.26) |
| `quarkus.snapstart.preload-classes` | `true` (medium confidence) | class preloading |
| `quarkus.snapstart.generate-application-class-list` | `true` (medium confidence) | application class list generation |
| `quarkus.snapstart.initialize-classes` | `true` (medium confidence) | class initialisation |
| `quarkus.snapstart.full-warmup` | `true` (medium confidence) | listed in the reference, absent from the SnapStart guide |

Source: [all-config](https://quarkus.io/version/3.40/guides/all-config) (all 232,437 characters read in three windows through a summarising tool; defaults are (medium confidence, M9) until a verbatim row is recorded). The custom class list is `META-INF/quarkus-preload-classes.txt`, one class per line, built from `-verbose:class` CloudWatch logs ([SnapStart guide](https://quarkus.io/version/3.40/guides/aws-lambda-snapstart)).

## Hooks and timing

- CRaC `Resource` hooks: `beforeCheckpoint` runs before the snapshot, `afterRestore` after it. The Quarkus guide registers an `@ApplicationScoped @Startup` bean; see [always-do 7](./always-do-patterns.md#7-crac-strong-reference).
- Restore limit: Quarkus guide says "Restoration is limited to 2 seconds"; AWS says 10 seconds before `SnapStartTimeoutException`. Which applies is (unverified) ([C6](./ask-first-decisions.md#c6-restore-time-budget)).
- Uniqueness scanner: SpotBugs plugin `aws-lambda-snapstart-java-rules` ([AWS uniqueness](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html)). Its repository page was not fetched (page not recorded).
- SDK client behaviour after restore belongs to the siblings `integrating-quarkus-amazon-data-v3-40` and `integrating-quarkus-amazon-messaging-v3-40`.

## Behaviour on an OS-only runtime

Exactly what happens when SnapStart is configured on an OS-only runtime (rejected vs ignored) is (unverified). Do not promise either outcome; avoid the combination.
