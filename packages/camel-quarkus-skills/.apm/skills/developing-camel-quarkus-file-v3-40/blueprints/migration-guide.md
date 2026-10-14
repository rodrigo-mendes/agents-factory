# Migration Guide for File Users: Camel Quarkus 3.15 to 3.40 (Camel 4.8 to 4.22)

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Every file-relevant change is an upstream Camel change; the Camel Quarkus 3.40.0 migration guide has no file/ftp entries ([guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)).

## Camel changes (per-version upgrade guides)

Pages follow `https://camel.apache.org/manual/camel-4x-upgrade-guide-4_<minor>.html`.

| Camel | Change | Page | Confidence |
|---|---|---|---|
| 4.10 | Methods taking `GenericFile` now take `Supplier<GenericFile>` (custom file components only); name-only filtering optimized; consumers whose starting directory cannot be created retry on each poll | `-4_10.html` | (medium confidence) |
| 4.10.x (ftp) | `CamelFileName` includes the relative path with `recursive=true`, matching camel-file | `-4_10.html` | (medium confidence) |
| 4.11 | Dynamic polling via the `fileName` header (`DynamicPollingConsumer` API) | `-4_11.html` | (medium confidence) |
| 4.13 | poll/pollEnrich: eager max-messages-per-poll behaviour changed; exact option name and default (unverified) | `-4_13.html` | (unverified) |
| 4.18 | `GenericFileOperations.storeFileDirectly` added (custom implementers) | `-4_18.html` | (medium confidence) |
| 4.19 | "The default `inProgressRepository` is now FIFO based instead of LRU" (camel-file, aws2-s3, ibm-cos) | `-4_19.html` | high |
| 4.21 | ftp/sftp/mina-sftp/smb/azure-files reject downloads outside the local work dir unless `jailStartingDirectory=false` | `-4_21.html` (partly read) | (medium confidence) |
| 4.22 | `preSort` becomes a String; `forceWrites` deprecated (default `true` changed to `false`); 4.22.1 applies `jailStartingDirectory` to remote consumers | `-4_22.html` (partly read) | (medium confidence) for preSort, forceWrites and jail; page only partly read |

## Camel Quarkus changes

- 3.31: `camel-quarkus-junit5` was renamed to `camel-quarkus-junit` ([guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html)).
- 3.33.0: `camel-quarkus-mina-sftp` added, mutually exclusive with `camel-quarkus-ftp` ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html)).
- 3.40.0: no file/ftp entries. XSLT changes: external entities and DTDs in input documents are no longer resolved; `document()` is denied unless an application URIResolver resolves it; `quarkus.camel.xslt.features` now applies to every template ([guide](https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html)).

## Upgrade steps

1. Bump `quarkus.platform.version` to 3.40.x (see the core skill).
2. Search routes for `forceWrites` and `preSort=`; remove or adjust them.
3. Recompile custom `GenericFile*` implementations against Camel 4.22 (`Supplier<GenericFile>`, `storeFileDirectly`).
4. For FTP/SFTP, re-test `localWorkDirectory` and paths because of the jail enforcement.
5. Rename the test dependency to `camel-quarkus-junit` (see the skill `developing-camel-quarkus-junit-v3-40`).
6. For pollers that depend on batch size, check the real option name and defaults in the 4.13 upgrade guide (`camel-4x-upgrade-guide-4_13.html`); the name is (unverified).

## Compatibility

| Dependency | Min | Max | Source |
|---|---|---|---|
| Camel | 4.22.0 | 4.22.x | https://camel.apache.org/camel-quarkus/latest/ |
| Quarkus | 3.40.0 | 3.40.x | No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence; see [risks](./unverified-and-risks.md#version-lifetime-risk)) |
| Java | 17 | 21 | https://camel.apache.org/releases/q-3.40.0/ |
| GraalVM/Mandrel | 25.0 | none stated | https://quarkus.io/blog/mandrel-25-minimum-version/ |
| ftp / mina-sftp | 3.40.0 | 3.40.x | mutually exclusive |
