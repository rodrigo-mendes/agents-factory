---
name: developing-camel-quarkus-file-v3-40
description: "Guides Camel Quarkus 3.40.x file handling (Camel 4.22): camel-quarkus-file, file-watch, ftp/sftp, mina-sftp, file-cluster-service. Use when routes read, write or watch files or move them over FTP/SFTP. Not for Quarkus 4, other versions or SCP (jsch)."
---

# Developing with Camel Quarkus File 3.40.x

> Version lock: every claim applies to **Camel Quarkus 3.40.x** (Camel 4.22.x component docs) only. Research date **2026-10-14**.
> Claims tagged (unverified) or (medium confidence) were not fully confirmed against an official page; treat them as hypotheses.
> Core topics (BOMs, CDI, route discovery, TLS) belong to the sibling skill `developing-camel-quarkus-core-v3-40`.

## Version Context

| Item | Value | Source (fetched 2026-10-14) |
|---|---|---|
| Camel Quarkus | 3.40.x (3.40.0 released 2026-09-28, LTS; Maven Central artifact dated 2026-09-24) | https://camel.apache.org/releases/ ; https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-file/ |
| Camel component docs | 4.22.x (docs index lists 4.22.1) | https://camel.apache.org/camel-quarkus/latest/ |
| `camel-quarkus-file` status | Stable, JVM and native since 0.4.0; no Quarkus config options | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html |
| Java | 17 and 21 | https://camel.apache.org/releases/q-3.40.0/ |
| Native builder | Mandrel/GraalVM 25.0+ | https://quarkus.io/blog/mandrel-25-minimum-version/ (2026-05-29) |
| `camel-quarkus-mina-sftp` | JVM and native since 3.33.0 | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html |

**Version-lifetime risk** (as of 2026-10-14; details in [unverified and risks](./blueprints/unverified-and-risks.md#version-lifetime-risk)).
- Quarkus 4.0.0.Beta1 was published 2026-10-01; the final release is "planned for the end of November" (High, [Beta1 post](https://quarkus.io/blog/quarkus-4-0-0-beta1-released/)). No Camel Quarkus build on Quarkus 4 is known (medium confidence, absence of evidence; the post does not mention Camel Quarkus). Do not mix Quarkus 4 artifacts.
- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30 (High, [source](https://quarkus.io/releases)). The Camel Quarkus-specific end date is (unverified): applying the Quarkus date to Camel Quarkus is an inference.

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails)
- [Quick Reference](#quick-reference)
- [Always-do patterns with code](./blueprints/always-do-patterns.md)
- [Never-do patterns with examples](./blueprints/never-do-patterns.md)
- [File consumer and producer options](./blueprints/file-consumer-producer.md)
- [file-watch and file-cluster-service](./blueprints/file-watch-and-cluster.md)
- [Remote files: ftp, sftp, mina-sftp](./blueprints/remote-ftp-sftp.md)
- [Native mode](./blueprints/native-mode.md)
- [Migration guide 3.15 to 3.40 (Camel 4.8 to 4.22)](./blueprints/migration-guide.md)
- [Integration examples and testing](./blueprints/integration-examples.md)
- [Unverified items, risks and bibliography](./blueprints/unverified-and-risks.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- [External Resources](#external-resources)

## Blueprints & Guardrails

### ✅ Always Do

- **Set `readLock` explicitly on every consumer that reads files another process writes.** The default is `none` ("No read lock is in use") ([file component](https://camel.apache.org/components/4.22.x/file-component.html)). See [patterns](./blueprints/always-do-patterns.md#2-explicit-read-lock).
- **Make post-processing explicit** (`move`/`moveFailed`, `delete` or `noop`). By default Camel moves consumed files to the `.camel` subfolder ([file component](https://camel.apache.org/components/4.22.x/file-component.html)). See [patterns](./blueprints/always-do-patterns.md#3-explicit-post-processing).
- **Declare `camel-quarkus-file` without a version**, managed by `quarkus-camel-bom` 3.40.x ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file.html)). See [patterns](./blueprints/always-do-patterns.md#1-extension-through-the-platform-bom).
- **For SFTP set `strictHostKeyChecking=yes` with a known-hosts file.** The default is `no` ([sftp component](https://camel.apache.org/components/4.22.x/sftp-component.html)). See [patterns](./blueprints/always-do-patterns.md#4-sftp-host-key-verification).
- **Use exactly one remote-file extension per application.** `camel-quarkus-ftp` (`ftp:`, `ftps:`, `sftp:`) and `camel-quarkus-mina-sftp` (`mina-sftp:`) cannot be combined ([ftp](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/ftp.html), [mina-sftp](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html)). See [remote files](./blueprints/remote-ftp-sftp.md).

### ⚠️ Ask First

| Decision | Options and tradeoff | Ask |
|---|---|---|
| Atomic writes | `tempPrefix`/`tempFileName` (write then rename) vs `doneFileName` (done-file protocol); no default for either; `fileExist` defaults to `Override` ([file component](https://camel.apache.org/components/4.22.x/file-component.html)) | "Do downstream readers poll the output folder? Can they wait for a done file?" |
| Idempotency | In-memory cache (1000 entries, lost on restart) vs persistent `idempotentRepository` ([file component](https://camel.apache.org/components/4.22.x/file-component.html)) | "Must duplicates be prevented across restarts or nodes?" |
| Post-processing | `.camel` default vs `move`/`moveFailed` (audit) vs `delete` vs `noop` (implies `idempotent=true`) | "Must processed files be kept, and is the input folder writable?" |
| Native charsets | No setting (consumer defaults to UTF-8) vs `quarkus.native.add-all-charsets=true`, only when `UnsupportedCharsetException` appears ([native guide](https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html)) | "Do routes use a `charset=` other than UTF-8 in a native build?" |
| Several instances | Single instance vs `camel-quarkus-file-cluster-service` (needs a reliable shared FS); its property defaults (medium confidence); vs `idempotent*` read lock + shared repository (medium confidence) | "How many replicas, and what shared storage or repository exists?" |
| Polling vs events (medium confidence); the "no move/readLock lifecycle" trade-off is inferred from the options, see [file-watch component](https://camel.apache.org/components/4.22.x/file-watch-component.html) | `file:` (read locks, move/idempotent lifecycle, `delay` 500 ms) vs `file-watch:` (change events incl. DELETE, no move/readLock lifecycle) | "Consume and archive files, or only react to changes?" |
| FTP library | `camel-quarkus-ftp` (FTP/FTPS/SFTP); SSH library in native (unverified); vs `camel-quarkus-mina-sftp` (SFTP only) | "Is FTP/FTPS needed, or SFTP only?" |
| Large remote files (medium confidence) | `localWorkDirectory` or `streamDownload=true` (not with `stepwise=true`) vs the default in-memory load | "How large are the files?" |
| Dynamic paths (medium confidence) | Fixed root + validated `CamelFileName` header vs a directory built from input | "Where does the path segment come from, and is it validated?" |
| Remote path jail (medium confidence); the 4.21/4.22.1 notes were only partly read | Keep `jailStartingDirectory=true` vs relax it | "Do downloads need to land outside the local work dir?" |
| `forceWrites` / boolean `preSort` (medium confidence); the 4.22 upgrade guide was only partly read ([source](https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html)) | Remove `forceWrites` (deprecated in 4.22) and use a String `preSort` (`name`, `modified`, `size`, `-name`, `-modified`, `-size`, `true`, as the 4.22 page records) vs keep the old options | "Do existing routes set `forceWrites` or `preSort=true`?" |

### 🚫 Never Do

| ❌ Don't | ✅ Instead |
|---|---|
| Consume with `from("file:dir")` while another process is still writing; `readLock=none` is the default ([source](https://camel.apache.org/components/4.22.x/file-component.html)) | `readLock=changed&readLockMinAge=1000`, or another explicit lock |
| Use `readLock=fileLock` on a mount/share; the page says to avoid it ([source](https://camel.apache.org/components/4.22.x/file-component.html)) | `readLock=changed&readLockMinAge=1000` |
| Leave SFTP on `strictHostKeyChecking=no` in production ([source](https://camel.apache.org/components/4.22.x/sftp-component.html)) | `strictHostKeyChecking=yes&knownHostsFile=...` |
| Put `camel-quarkus-ftp` and `camel-quarkus-mina-sftp` in one build; both pages warn of build-time failures ([ftp](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/ftp.html), [mina-sftp](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html)) | Pick one extension |
| Use `camel-quarkus-jsch` for SFTP; it is SCP, not SFTP ([reference index](https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html)) | `camel-quarkus-ftp` or `camel-quarkus-mina-sftp` |

Full ❌/✅ code: [never-do patterns](./blueprints/never-do-patterns.md). Unconfirmed items: [register](./blueprints/unverified-and-risks.md).

## Quick Reference

| Aspect | Value | Source |
|---|---|---|
| `readLock` default | `none` | https://camel.apache.org/components/4.22.x/file-component.html |
| `readLockTimeout` / `readLockCheckInterval` / `readLockMinAge` | `10000` ms / `1000` ms / `0` (`changed` only) | https://camel.apache.org/components/4.22.x/file-component.html |
| `delay` / `initialDelay` | `500` ms / `1000` ms | https://camel.apache.org/components/4.22.x/file-component.html |
| `autoCreate`, `recursive` (file) | `true`, `false` | https://camel.apache.org/components/4.22.x/file-component.html |
| `delete` / `noop` | `false` / `false` (`noop=true` sets `idempotent=true`) | https://camel.apache.org/components/4.22.x/file-component.html |
| `fileExist` (producer) | `Override` | https://camel.apache.org/components/4.22.x/file-component.html |
| `idempotent` / `idempotentEager` | `false` / `true` (key: absolute path) | https://camel.apache.org/components/4.22.x/file-component.html |
| Consumer charset | `UTF-8` | https://camel.apache.org/components/4.22.x/file-component.html |
| file-watch `events`, `recursive`, `antInclude` | `CREATE,MODIFY,DELETE`, `true`, `**` | https://camel.apache.org/components/4.22.x/file-watch-component.html |
| SFTP `strictHostKeyChecking` / `useUserKnownHostsFile` | `no` / `true` | https://camel.apache.org/components/4.22.x/sftp-component.html |
| SFTP `streamDownload` / `stepwise` / `jailStartingDirectory` | `false` / `true` / `true` | https://camel.apache.org/components/4.22.x/sftp-component.html |
| XSLT in native | `classpath:` URIs only | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html |
| In-progress repository | FIFO since Camel 4.19 | https://camel.apache.org/manual/camel-4x-upgrade-guide-4_19.html |
| file-cluster-service defaults | (medium confidence) listed in [file-watch and cluster](./blueprints/file-watch-and-cluster.md) | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file-cluster-service.html |
| Representative commands | `mvn test`, `mvn verify -Dnative` (log output unverified) | page not recorded |

## External Resources

All fetched 2026-10-14. camel.apache.org pages carry no page date and are the current stable 3.40.x / 4.22.x docs.

- File extension: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file.html
- File component (4.22.x): https://camel.apache.org/components/4.22.x/file-component.html
- SFTP component (4.22.x): https://camel.apache.org/components/4.22.x/sftp-component.html
- Native mode: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html
- Testing: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- 3.40.0 migration guide: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- Releases: https://camel.apache.org/releases/
- Quarkus LTS policy: https://quarkus.io/releases
- Full bibliography: [unverified and risks](./blueprints/unverified-and-risks.md#source-bibliography)
