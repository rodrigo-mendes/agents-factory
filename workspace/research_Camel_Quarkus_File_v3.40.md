# Research: Camel Quarkus File v3.40 (camel-quarkus-file 3.40.x / Camel 4.22.x / Quarkus 3.40.x)

> Version lock: every claim here applies to **Camel Quarkus 3.40.x** (Camel 4.22.x component docs) only. Anything from the v3.15 research file, or from 4.14.x or 3.27.x pages, counts as misinformation unless it is re-verified below.
> All sources were fetched on **2026-10-14**. camel.apache.org pages carry no page date. They are accepted as current because they are the versioned docs (3.40.x / 4.22.x) of the current stable LTS.
> Method note: WebFetch returns model summaries of pages, not raw HTML. Text in quotes is the tool's rendering. Confirm the exact wording on the live page before quoting it verbatim in a skill.
> Plan-approval step (P3 EnterPlanMode/ExitPlanMode) was **skipped**: this is a forked batch run with no user available to approve a plan. The orchestrator user approved the scheme in the parent session.
> Core topics (BOMs, CDI, routes discovery, TLS, Quarkus 4 risk) are not repeated here. See `workspace/research_Camel_Quarkus_Core_v3.40.md`.
> Tags: **[High]** = read on the cited official page. **[Medium]** = single source with a tool-summary ambiguity, or an inference from official text. **[UNVERIFIED]** = not confirmed on an official page.

---

## Metadata

```yaml
Full_Name: Apache Camel Quarkus — File extension (org.apache.camel.quarkus:camel-quarkus-file)
Target_Version: 3.40.x (3.40.0 on Maven Central, 2026-09-24 09:34 — https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-file/)
Underlying_Component: Camel File component 4.22.x (https://camel.apache.org/components/4.22.x/file-component.html)
Release_Date: 2026-09-28 per https://camel.apache.org/releases/ (Maven Central artifact timestamp 2026-09-24; both dates kept)
Support_Status: LTS (3.40.0 marked LTS at https://camel.apache.org/releases/; Quarkus 3.40 LTS maintained to 2027-09-30 per https://quarkus.io/releases; Camel Quarkus-specific end date UNVERIFIED)
Extension_Status: Stable, JVM + native since 0.4.0 (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file.html ; Stable per https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html)
Primary_Docs: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file.html
Official_Repo: https://github.com/apache/camel-quarkus
Research_Date: 2026-10-14
Domain_Complexity: Standard (multi-integration: FTP/SFTP, XSLT, JAXB; concurrency/read-lock; clustering; native mode; path-safety)
Research_Depth: deep
Max_Iterations: 3
Gap_Loop_Ran: true
Iterations_Used: 3 of 3
Triangulated_Count: 4
Unverified_Count: 9
Irresolvable_Count: 3
Research_Quality_Score: 88%   # ~100 claims; (100 - 9 - 3) / 100
```

---

## Executive Summary

`camel-quarkus-file` puts the Camel File component (`file:directoryName`) into Quarkus for JVM and native mode. It has been supported in both modes since 0.4.0, and the 3.40.x index lists it as Stable. Its extension page has **no Quarkus configuration options**. Every behaviour is set through Camel 4.22.x endpoint options. Cluster-singleton consumption ("only one node consumes") is a separate extension, `camel-quarkus-file-cluster-service`. Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file.html and https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html. [High]

Relevant changes since the 3.15 file (Camel 4.8) are all upstream Camel changes. The Camel Quarkus 3.40.0 migration guide has no file/ftp entries (https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html). [High]
- **Camel 4.22:** `preSort` changed from boolean to String (`name|modified|size|-name|-modified|-size|true`). `forceWrites` is deprecated and its default changed to `false`. Source: https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html. [High]
- **Camel 4.19:** the default `inProgressRepository` is now FIFO instead of LRU. Source: https://camel.apache.org/manual/camel-4x-upgrade-guide-4_19.html. [High]
- **Camel 4.21 / 4.22.1:** remote-file consumers enforce `jailStartingDirectory` (default `true`) for downloads too. Sources: https://camel.apache.org/manual/camel-4x-upgrade-guide-4_21.html and the 4_22 page. [Medium]
- **Camel Quarkus 3.33.0:** a new `camel-quarkus-mina-sftp` extension arrived. It **cannot coexist** with `camel-quarkus-ftp` (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html). [High]
- **Camel Quarkus 3.40.0, XSLT partner:** external entities are no longer resolved, and `document()` is denied without a URIResolver. Source: the 3.40.0 migration guide. [High]

Three critical patterns:
1. Pick a `readLock` explicitly. The default is `none`, so a file that is still being written can be consumed.
2. Decide on post-processing up front. The default moves files to `.camel/`. You can choose `noop`, `delete`, or `move`/`moveFailed`.
3. Write with `tempPrefix`/`tempFileName` or `doneFileName` so downstream consumers never see partial files.

The tier is **Standard**. The decision space is wide: locking, idempotency, clustering, the FTP/SFTP library choice, and native-mode resource rules. There is also a security angle (path jailing and SFTP host-key checking), but no auth or crypto design inside the File component itself.

---

## Architectural Guardrails

> Confidence legend: 🟢 High (2+ official sources, dated ≤12mo) | 🟡 Medium (1 source or dated 12–24mo) | 🔴 Low (community source or dated >24mo — verify before use)

### ✅ Mandatory Patterns

**1. Declare the extension through the Quarkus platform BOM (no version on the artifact)**
> Confidence: 🟢 High | [✓✓ Triangulated | CQ file extension page (2026-10-14) + Maven Central camel-quarkus-file 3.40.0 (2026-09-24)]
- Why: the extension provides `file:` in JVM and native mode since 0.4.0 [High]. BOM alignment rules are in the core research file.
- Code:
  ```xml
  <!-- Camel Quarkus 3.40.x — version managed by quarkus-camel-bom 3.40.x -->
  <dependency>
    <groupId>org.apache.camel.quarkus</groupId>
    <artifactId>camel-quarkus-file</artifactId>
  </dependency>
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file.html (2026-10-14); https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-file/ (3.40.0, 2026-09-24)

**2. Set an explicit `readLock` on every consumer that reads files another process writes**
> Confidence: 🟢 High | [✓✓ Triangulated | Camel 4.22 File page (2026-10-14) + apache/camel-quarkus integration-tests/file FileRoutes.java (main, 2026-10-14)]
- Why: `readLock` defaults to `none`, "No read lock is in use" [High]. Allowed values are `none, markerFile, fileLock, rename, changed, idempotent, idempotent-changed, idempotent-rename` [High]. Related defaults:
  - `readLockTimeout` = `10000` ms; 0 or less waits forever [High]
  - `readLockCheckInterval` = `1000` ms; the page warns this may be too fast for slow writers [High]
  - `readLockMinAge` = `0`; applies to `changed` only [High]

  Source for all three: https://camel.apache.org/components/4.22.x/file-component.html
- Code:
  ```java
  // Camel Quarkus 3.40.x / Camel 4.22.x — mirrors the official CQ integration test
  from("file:target/in?readLock=changed&readLockMinAge=1000&readLockCheckInterval=2000"
       + "&readLockTimeout=5000&move=.done")
      .routeId("inbound-files")
      .to("direct:process");
  ```
- Source: https://camel.apache.org/components/4.22.x/file-component.html (2026-10-14); https://raw.githubusercontent.com/apache/camel-quarkus/main/integration-tests/file/src/main/java/org/apache/camel/quarkus/component/file/it/FileRoutes.java (main branch, 2026-10-14; Medium for 3.40.x tag equivalence)

**3. Make post-processing explicit: `move` / `moveFailed` / `delete` / `noop`**
> Confidence: 🟢 High | [✓✓ Triangulated | Camel 4.22 File page options table + Usage text (2026-10-14)]
- Why: "By default, Camel will move consumed files to the `.camel` subfolder relative to the directory where the file was consumed" [High, confirmed in gap iteration 1]. Option defaults [High]:
  - `delete` = `false`
  - `noop` = `false`; `noop=true` also sets `idempotent=true`
  - `move`, `moveFailed` and `preMove` have no default in the table

  Source for all: https://camel.apache.org/components/4.22.x/file-component.html
- Code:
  ```java
  // Camel Quarkus 3.40.x — archive on success, quarantine on failure
  from("file:/data/in?readLock=changed"
       + "&move=archive/${date:now:yyyyMMdd}/${file:name}"
       + "&moveFailed=error/${file:name}")
      .to("direct:process");
  ```
- Source: https://camel.apache.org/components/4.22.x/file-component.html ; https://camel.apache.org/components/4.22.x/languages/file-language.html (2026-10-14)

**4. Write atomically for downstream readers (`tempPrefix` / `tempFileName` or `doneFileName`)**
> Confidence: 🟡 Medium (single page: Camel 4.22 File page)
- Why: with `tempPrefix`/`tempFileName` the file "is written under the temporary name, then renamed". `doneFileName` makes the consumer wait for a done file and makes the producer write one. Neither option has a default. `fileExist` defaults to `Override` (values: Override, Append, Fail, Ignore, Move, TryRename). [High] Source: https://camel.apache.org/components/4.22.x/file-component.html
- Code:
  ```java
  // Camel Quarkus 3.40.x — producer side
  from("direct:export")
      .setHeader(org.apache.camel.Exchange.FILE_NAME, simple("orders-${date:now:yyyyMMddHHmmss}.xml"))
      .to("file:/data/out?tempPrefix=.inprogress-&fileExist=Fail&doneFileName=${file:name}.done");
  ```
- Source: https://camel.apache.org/components/4.22.x/file-component.html (2026-10-14). The `CamelFileName` and `CamelFileNameProduced` headers are confirmed on the same page.

**5. Use idempotency with a persistent repository when duplicates matter**
> Confidence: 🟡 Medium (single page)
- Why:
  - `idempotent` defaults to `false`. Without an `idempotentRepository`, Camel uses "a memory based LRUCache that holds 1000 entries", which is lost on restart.
  - `idempotentKey` defaults to the absolute file path.
  - `idempotentEager` defaults to `true`.

  [High] Source: https://camel.apache.org/components/4.22.x/file-component.html
- Code:
  ```java
  // Camel Quarkus 3.40.x — repository bean named "fileRepo" (e.g. a JDBC/Infinispan idempotent repository)
  from("file:/data/in?idempotent=true&idempotentRepository=#fileRepo"
       + "&idempotentKey=${file:name}-${file:size}&move=done/${file:name}")
      .to("direct:process");
  ```
- Source: https://camel.apache.org/components/4.22.x/file-component.html (2026-10-14)

### ⚠️ Conditional Patterns

**A. Native mode: charsets (downgraded from 3.15 "mandatory")**
> Confidence: 🟢 High (CQ 3.40.x native-mode guide)
- Options:
  - Default: no setting.
  - `quarkus.native.add-all-charsets=true` when an `UnsupportedCharsetException` appears.
- The guide says "By default, not all Charsets are available in native mode". The fix applies only when the error occurs. With no `charset` option, the File consumer uses `UTF-8` by default (https://camel.apache.org/components/4.22.x/file-component.html). [High]
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Default | Image size | Non-default charsets missing | UTF-8 only |
  | add-all-charsets | Any `charset=` works | Larger native image | `charset=ISO-8859-1` etc. in native |

- Agent: "Ask user: do routes use `charset=` other than UTF-8 and do you build native?"
- Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html (2026-10-14)

**B. Post-processing strategy**
> Confidence: 🟢 High
- Options:
  - default move to `.camel`
  - `move=`/`moveFailed=` to archive
  - `delete=true`
  - `noop=true`, which implies idempotent; files stay in place
- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | move/moveFailed | Audit, replay | Disk | Compliance |
  | delete | Disk | Recovery | Transient drops |
  | noop | Source untouched | Memory/idempotent repo growth | Read-only shares |

- Agent: "Ask user: must processed files be retained, and is the input directory writable?"
- Source: https://camel.apache.org/components/4.22.x/file-component.html (2026-10-14)

**C. Multi-instance deployment: cluster-singleton consumer**
> Confidence: 🟢 High (existence); 🟡 Medium (property defaults)
- Options:
  - single instance
  - `camel-quarkus-file-cluster-service` (FileLock-based Camel Cluster Service SPI; JVM and native since 3.10.0; Stable)
  - another cluster service (for example Kubernetes; not researched here)
  - `readLock=idempotent*` with a shared repository
- `quarkus.camel.cluster.file.*` properties, per https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file-cluster-service.html [Medium, from a tool summary]:

  | Property | Default |
  |---|---|
  | `enabled` | `true` |
  | `id` | null |
  | `root` | null |
  | `order` | `2147482647` |
  | `acquire-lock-delay` | 1000ms (from the description) |
  | `acquire-lock-interval` | 10000ms (from the description) |
  | `cluster-data-task-max-attempts` | `5` |
  | `cluster-data-task-timeout` | 10 seconds |
  | `heartbeat-timeout-multiplier` | UNVERIFIED |

- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | Single instance | Simplicity | HA | One node |
  | file-cluster-service | Shared-FS leadership | Needs a reliable shared FS and file locks | Few nodes on NFS/shared volume |
  | idempotent readLock + shared repo | All nodes consume | Repo infrastructure | Throughput across nodes |

- Agent: "Ask user: how many replicas and what shared storage/repository is available?"
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file-cluster-service.html (2026-10-14)

**D. Polling vs event-driven (`file` vs `file-watch`)**
> Confidence: 🟢 High
- `camel-quarkus-file-watch` exists: JVM and native since 1.0.0, Stable.
- Native note: on macOS the JVM mode uses a JNA WatchService. Native mode overrides it with `java.nio.file.WatchService`, which may be slower (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file-watch.html).
- `file-watch` defaults (https://camel.apache.org/components/4.22.x/file-watch-component.html) [High]:

  | Option | Default |
  |---|---|
  | `events` | `CREATE,MODIFY,DELETE` |
  | `recursive` | `true` (note: `file:` defaults to `false`) |
  | `antInclude` | `**` |
  | `useFileHashing` | `true` |
  | `autoCreate` | `true` |
  | `concurrentConsumers` | `1` |
  | `pollThreads` | `1` |
  | `queueSize` | `2147483647` |
  | `fileHasher` | `#murmur3FFileHasher` |

- Tradeoffs:

  | Option | Optimizes | Sacrifices | Best When |
  |--------|-----------|------------|-----------|
  | `file:` polling | Read locks, move/idempotent lifecycle | Latency (`delay` default 500 ms) | Batch ingestion |
  | `file-watch:` | Low latency, change events incl. DELETE | No move/readLock lifecycle | Reacting to changes |

- Agent: "Ask user: do you need to consume (and archive) files or only react to change events?"
- Source: URLs above (2026-10-14)

**E. Remote files: `camel-quarkus-ftp` vs `camel-quarkus-mina-sftp`**
> Confidence: 🟢 High
- `camel-quarkus-ftp` covers `ftp:`, `ftps:` and `sftp:`. It is JVM and native since 1.0.0 (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/ftp.html).
- `camel-quarkus-mina-sftp` (`mina-sftp:`) is JVM and native since 3.33.0 (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html).
- The two **cannot be used together in the same application**; having both "can cause build-time failures" (stated on both pages).
- `camel-quarkus-jsch` is SCP, not SFTP (https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html).
- The Camel 4.22 SFTP component uses JSch (https://camel.apache.org/components/4.22.x/sftp-component.html). Which SSH library the CQ ftp extension uses in native mode is UNVERIFIED.
- Agent: "Ask user: FTP/FTPS also needed (choose camel-quarkus-ftp) or SFTP only with MINA SSHD (camel-quarkus-mina-sftp)?"
- Source: URLs above (2026-10-14)

### 🚫 Forbidden Patterns

**1. Consuming without a read lock while another process is still writing**
> Severity: High
> Confidence: 🟢 High
- Why: the default is `readLock=none` (https://camel.apache.org/components/4.22.x/file-component.html).
- Impact: truncated or partial payloads get processed and then moved away.
- ❌ Wrong:
  ```java
  from("file:/data/in").to("direct:process"); // CQ 3.40.x: readLock defaults to none
  ```
- ✅ Correct:
  ```java
  from("file:/data/in?readLock=changed&readLockMinAge=1000").to("direct:process");
  ```
- Source: https://camel.apache.org/components/4.22.x/file-component.html (2026-10-14)

**2. Using `readLock=fileLock` on a mounted/remote share**
> Severity: High
> Confidence: 🟢 High
- Why: the page says that approach "should be avoided when accessing a remote file system via a mount/share" (https://camel.apache.org/components/4.22.x/file-component.html).
- Impact: locks are unreliable across nodes, so files get processed twice.
- ❌ Wrong:
  ```java
  from("file:/mnt/nfs/in?readLock=fileLock").to("direct:process");
  ```
- ✅ Correct:
  ```java
  from("file:/mnt/nfs/in?readLock=idempotent-changed&idempotentRepository=#sharedRepo")
      .to("direct:process"); // or a cluster-singleton via camel-quarkus-file-cluster-service
  ```
- Source: https://camel.apache.org/components/4.22.x/file-component.html (2026-10-14)

**3. Putting `${}` placeholders in the directory path, or building paths from untrusted headers**
> Severity: High
> Confidence: 🟡 Medium (the path rule is High; the security framing is an inference)
- Why: `directoryName` "must not contain `${ }` placeholders" (https://camel.apache.org/components/4.22.x/file-component.html). Dynamic names belong in `fileName`/`CamelFileName`. Remote consumers jail paths by default (`jailStartingDirectory=true`, https://camel.apache.org/components/4.22.x/sftp-component.html).
- Impact: wrong endpoints get created, or a write escapes the intended tree.
- ❌ Wrong:
  ```java
  .toD("file:/data/${header.tenant}/out") // directory from an untrusted header
  ```
- ✅ Correct:
  ```java
  .setHeader(Exchange.FILE_NAME, simple("${header.validatedTenant}/out-${file:onlyname}"))
  .to("file:/data"); // fixed root; validate the header before use
  ```
- Source: https://camel.apache.org/components/4.22.x/file-component.html (2026-10-14)

**4. Combining `camel-quarkus-ftp` and `camel-quarkus-mina-sftp`**
> Severity: High
> Confidence: 🟢 High
- Why: both pages state that they cannot be used together.
- Impact: the build fails.
- ❌ Wrong:
  ```xml
  <artifactId>camel-quarkus-ftp</artifactId> ... <artifactId>camel-quarkus-mina-sftp</artifactId>
  ```
- ✅ Correct:
  ```xml
  <artifactId>camel-quarkus-ftp</artifactId> <!-- ftp:, ftps:, sftp: -->
  ```
- Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/ftp.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html (2026-10-14)

**5. SFTP with `strictHostKeyChecking=no` in production**
> Severity: Critical
> Confidence: 🟢 High
- Why: the default is `no`, which the page warns leaves connections vulnerable to man-in-the-middle attacks. `useUserKnownHostsFile` defaults to `true`. (https://camel.apache.org/components/4.22.x/sftp-component.html)
- Impact: credentials and data get exposed to an attacker in the middle.
- ❌ Wrong:
  ```java
  from("sftp:user@host/in?password=RAW({{sftp.pwd}})")  // strictHostKeyChecking defaults to no
  ```
- ✅ Correct:
  ```java
  from("sftp:user@host/in?privateKeyFile={{sftp.key}}&strictHostKeyChecking=yes&knownHostsFile={{sftp.known-hosts}}")
  ```
- Source: https://camel.apache.org/components/4.22.x/sftp-component.html (2026-10-14)

**6. Using `charset=` or in-memory loading for very large files**
> Severity: Medium
> Confidence: 🟡 Medium
- Why: the File page says of `charset` "do not use this if you have big messages", because the producer may load the whole message into memory. For SFTP, with `streamDownload=false` (the default), "the remote files are loaded into memory before being sent into the route" unless `localWorkDirectory` is set. Sources: https://camel.apache.org/components/4.22.x/file-component.html and https://camel.apache.org/components/4.22.x/sftp-component.html
- Impact: OutOfMemoryError on large payloads.
- ❌ Wrong:
  ```java
  from("sftp:host/big?charset=ISO-8859-1").convertBodyTo(String.class).to("direct:parse");
  ```
- ✅ Correct:
  ```java
  from("sftp:host/big?localWorkDirectory=/tmp/camel-work")   // or streamDownload=true (not with stepwise=true)
      .split(body().tokenize("\n")).streaming()
      .to("direct:line");
  ```
- Source: URLs above (2026-10-14). Splitter streaming is a Camel EIP and was not re-fetched for 4.22 (UNVERIFIED wording).

**7. Using the deprecated `forceWrites` option, or `preSort` as a boolean-only option**
> Severity: Medium
> Confidence: 🟢 High
- Why: in Camel 4.22, `forceWrites` is deprecated and has had no effect since 2.20. `preSort` is now a String (https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html).
- ❌ Wrong:
  ```java
  to("file:/out?forceWrites=true")
  ```
- ✅ Correct:
  ```java
  from("file:/in?preSort=modified&eagerMaxMessagesPerPoll=true&maxMessagesPerPoll=100")
  ```
- Source: https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html (2026-10-14)

---

## Migration Guide

> Confidence: 🟢 High | Sources: https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (2026-10-14) + https://camel.apache.org/manual/camel-4x-upgrade-guide.html index and per-version pages (2026-10-14)

**Breaking/behaviour changes affecting file users, from 3.15 (Camel 4.8) to 3.40 (Camel 4.22):**

| Camel ver. | Change | Source | Conf. |
|---|---|---|---|
| 4.10 | Methods taking `GenericFile` now take `Supplier<GenericFile>` (custom file components only). Name-only filtering is optimized. Consumers whose starting directory cannot be created retry on each poll. | https://camel.apache.org/manual/camel-4x-upgrade-guide-4_10.html | Medium |
| 4.10.x (ftp) | `CamelFileName` includes the relative path with `recursive=true`, to match camel-file | same | Medium |
| 4.11 | Dynamic polling via the `fileName` header (`DynamicPollingConsumer` API) | https://camel.apache.org/manual/camel-4x-upgrade-guide-4_11.html | Medium |
| 4.13 | poll/pollEnrich: eager max-messages-per-poll behaviour changed. The exact option name and default are UNVERIFIED (investigators disagree) | https://camel.apache.org/manual/camel-4x-upgrade-guide-4_13.html | UNVERIFIED |
| 4.18 | `GenericFileOperations.storeFileDirectly` added (custom implementers) | https://camel.apache.org/manual/camel-4x-upgrade-guide-4_18.html | Medium |
| 4.19 | "The default `inProgressRepository` is now FIFO based instead of LRU" (camel-file, aws2-s3, ibm-cos) | https://camel.apache.org/manual/camel-4x-upgrade-guide-4_19.html | High |
| 4.21 | ftp/sftp/mina-sftp/smb/azure-files reject downloads outside the local work dir unless `jailStartingDirectory=false` | https://camel.apache.org/manual/camel-4x-upgrade-guide-4_21.html | Medium |
| 4.22 | `preSort` becomes a String. `forceWrites` is deprecated (default `true` changed to `false`). 4.22.1 applies `jailStartingDirectory` to remote consumers | https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html | High |

**Camel Quarkus side:**
- 3.31: `camel-quarkus-junit5` was renamed to `camel-quarkus-junit` (core research file).
- 3.33.0: `camel-quarkus-mina-sftp` was added.
- 3.40.0: no file/ftp entries. The XSLT changes are listed under Implementation Blueprint → Integration.

**Upgrade Steps:**
1. Bump `quarkus.platform.version` to 3.40.x (core research file).
2. Search routes for `forceWrites` and `preSort=`, and remove or adjust them.
3. If you have custom `GenericFile*` implementations, recompile against Camel 4.22 (`Supplier<GenericFile>`, `storeFileDirectly`).
4. For SFTP and FTP, re-test `localWorkDirectory` and paths, because of the jail enforcement.
5. Rename the test dependency to `camel-quarkus-junit`.

**Compatibility Matrix**:

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Camel | 4.22.0 | 4.22.x | docs index lists 4.22.1 (https://camel.apache.org/camel-quarkus/latest/) |
| Quarkus | 3.40.0 | 3.40.x | Quarkus 4 not supported (core research file) |
| Java | 17 | 21 | https://camel.apache.org/releases/q-3.40.0/ |
| GraalVM/Mandrel | 25.0 | — | https://quarkus.io/blog/mandrel-25-minimum-version/ |
| camel-quarkus-ftp / mina-sftp | 3.40.0 | 3.40.x | mutually exclusive |

---

## Implementation Blueprint

> Confidence: 🟢 High | [✓✓ Triangulated | official CQ integration test (FileRoutes.java) + Camel 4.22 File page]

**Lifecycle**:
```java
// Camel Quarkus 3.40.x — discovered RouteBuilder (no CDI needed unless @Inject/@ConfigProperty)
public class FileIngestRoute extends org.apache.camel.builder.RouteBuilder {
    @Override
    public void configure() {
        // Consumer error handling: route exceptions from polling into the route error handler
        errorHandler(deadLetterChannel("file:/data/dlq").maximumRedeliveries(3));

        from("file:/data/in"
             + "?antInclude=**/*.xml&recursive=true"          // recursive default false
             + "&readLock=changed&readLockMinAge=1000"
             + "&move=archive/${file:name}&moveFailed=error/${file:name}"
             + "&maxMessagesPerPoll=100&sortBy=file:modified"
             + "&bridgeErrorHandler=true")                    // default false
            .routeId("file-ingest")
            .log("Got ${file:name} (${file:size} bytes)")
            .to("direct:process");
    }
}
```
- Defaults [High], source https://camel.apache.org/components/4.22.x/file-component.html:
  - `initialDelay` = `1000` ms; `delay` = `500` ms
  - `autoCreate` = `true`
  - `bufferSize` = `131072` bytes (Medium)
  - `include`/`exclude` are case-insensitive regexes
  - `antExclude` overrides `antInclude`
- The consumed body "will be a `File` object" (same page) [High]. The runtime type `GenericFile<File>` is UNVERIFIED.
- Without `bridgeErrorHandler`, the default consumer `ExceptionHandler` logs and ignores polling exceptions. `onCompletionExceptionHandler` logs commit/rollback failures at WARN. [High], same page.
- File language variables (https://camel.apache.org/components/4.22.x/languages/file-language.html) [High]:
  - names: `file:name`, `file:name.ext`, `file:name.noext`, `file:onlyname`, `file:onlyname.noext`
  - paths: `file:ext`, `file:parent`, `file:path`, `file:absolute`, `file:absolute.path`
  - size and time: `file:length`/`file:size` (Long), `file:modified` (Date)
  - dates: `date:<command>:<pattern>`
  - `file:absolute*` and `date:file:` are consumer-only

**Integration**: Camel Quarkus File ↔ XSLT (camel-quarkus-xslt) + JAXB (camel-quarkus-jaxb) + Bean (camel-quarkus-bean)
```java
// Camel Quarkus 3.40.x
// application.properties (build-time, needed for native):  quarkus.camel.xslt.sources = xslt/order.xsl
from("file:/data/in?antInclude=*.xml&readLock=changed")
    .to("xslt:xslt/order.xsl")                 // classpath: URI — required in native
    .unmarshal().jaxb("com.example.orders")    // JAXB data format
    .bean("orderService", "handle")            // CDI bean named "orderService"
    .marshal().jaxb("com.example.orders")
    .to("file:/data/out?tempPrefix=.tmp-&fileExist=Fail");
```
- XSLT facts from https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html [High]:
  - Native mode supports only `classpath:` URIs; `file:` and `http:` URIs are JVM-only.
  - Stylesheets listed in `quarkus.camel.xslt.sources` are compiled to translets at build time.
  - `quarkus.camel.xslt.package-name` defaults to `org.apache.camel.quarkus.component.xslt.generated`.
  - `<xsl:messaging>` and `XsltSaxonAggregationStrategy` are JVM-only.
  - Which properties are build-time vs runtime: UNVERIFIED.
- XSLT changes in 3.40.0 (https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html) [High]:
  - External entities and DTDs in input documents are no longer resolved.
  - `document()` is denied unless an application URIResolver resolves it.
  - `quarkus.camel.xslt.features` now applies to every template.
- JAXB (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html) [High]: in native mode, POJOs created by a custom `ObjectFactory` without JAXB annotations must be registered for reflection (`@RegisterForReflection` or `quarkus.camel.native.reflection.include-patterns`).
- Bean (https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html) [High]: JVM and native since 0.1.0, with no config. For naming beans, see the core research file.

**Integration**: Camel Quarkus File ↔ FTP/SFTP (camel-quarkus-ftp)
```java
// Camel Quarkus 3.40.x — download large files via a local work dir, then hand off to file:
from("sftp:{{sftp.host}}/outbound?username={{sftp.user}}&privateKeyFile={{sftp.key}}"
     + "&strictHostKeyChecking=yes&knownHostsFile={{sftp.known-hosts}}"
     + "&localWorkDirectory=/tmp/camel-sftp&readLock=changed&move=.done")
    .to("file:/data/in?tempPrefix=.tmp-");
```
- SFTP defaults (https://camel.apache.org/components/4.22.x/sftp-component.html):

  | Option | Default | Conf. |
  |---|---|---|
  | `streamDownload` | `false` | High |
  | `stepwise` | `true`; cannot combine with `streamDownload` | High |
  | `jailStartingDirectory` | `true` | High |
  | `disconnect` | `false` | High |
  | `soTimeout` | `300000` ms | High |
  | `readLockTimeout` | `10000` ms per the summary; the File page says the FTP default is `20000` | Medium, conflicting |

**Native resources**: anything loaded from the classpath at runtime needs `quarkus.native.resources.includes` (comma-separated Ant globs). The `xslt` sources are compiled instead. Source: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html [High].

---

## Quality Control

**Verification Commands**:
```bash
# Representative — adapt to your environment (Camel Quarkus 3.40.x)
# Init
mvn io.quarkus.platform:quarkus-maven-plugin:3.40.1:create -DprojectGroupId=org.acme -DprojectArtifactId=file-app \
  -Dextensions="org.apache.camel.quarkus:camel-quarkus-file"
# Expected: BUILD SUCCESS; pom lists camel-quarkus-file without version
# Test (JVM)
mvn test
# Expected: Tests run: N, Failures: 0
# Native integration tests
mvn verify -Dnative
# Expected: *IT classes pass against the native binary
# Smoke
mkdir -p target/in && echo '<a/>' > target/in/a.xml && sleep 3 && ls target/in/.camel
# Expected: a.xml moved to .camel/ (default post-processing)
```
- `quarkus.platform.version` 3.40.1 comes from the core research file. The plugin coordinate form is UNVERIFIED for this exact command.

**Mocking** (https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html) [High]:
- `camel-quarkus-junit` (test scope) provides `CamelQuarkusTestSupport`, which is JVM-only.
- One CamelContext is shared per suite. Restart it with `@TestProfile`; manual stop/start throws.
- AdviceWith: advise routes from `src/main` in `doBeforeEach`, or per method with `adviceRoute()`. Avoid wildcard URIs.
- `@QuarkusIntegrationTest` runs out of process. Test it through the network or "by observing the file system".
- NotifyBuilder is not covered on the CQ page: UNVERIFIED for CQ.

```java
// Camel Quarkus 3.40.x — JVM test with AdviceWith; replace file input with direct:, mock the output
@io.quarkus.test.junit.QuarkusTest
class FileIngestRouteTest extends org.apache.camel.quarkus.test.CamelQuarkusTestSupport {
    @Override
    protected void doBeforeEach(io.quarkus.test.junit.callback.QuarkusTestMethodContext ctx) throws Exception {
        org.apache.camel.builder.AdviceWith.adviceWith(context, "file-ingest", a -> {
            a.replaceFromWith("direct:in");
            a.weaveByToUri("direct:process").replace().to("mock:out");
        });
    }
    @org.junit.jupiter.api.Test
    void routesFile() throws Exception {
        getMockEndpoint("mock:out").expectedMessageCount(1);
        template.sendBodyAndHeader("direct:in", "<a/>", org.apache.camel.Exchange.FILE_NAME, "a.xml");
        getMockEndpoint("mock:out").assertIsSatisfied();
    }
}
```
- The `doBeforeEach` signature and the package names are taken from the testing guide's method mapping. The exact parameter type is UNVERIFIED; check it against the guide.
- The official file integration test uses fixed `target/test-files/...` paths and `consumerTemplate.receiveBodyNoWait(...)`. Source: https://raw.githubusercontent.com/apache/camel-quarkus/main/integration-tests/file/src/main/java/org/apache/camel/quarkus/component/file/it/FileResource.java [High, `main` branch].

---

## Production Readiness

- **Performance**:
  - Polling cadence: `delay` defaults to 500 ms, `initialDelay` to 1000 ms.
  - Batch size: `maxMessagesPerPoll` has no limit by default.
  - In 4.22, use `preSort` with `eagerMaxMessagesPerPoll` to take the oldest N files cheaply.
  - Sources: https://camel.apache.org/components/4.22.x/file-component.html ; https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html
- **Scalability**:
  - Several nodes on shared storage need either a cluster-singleton (`camel-quarkus-file-cluster-service`) or idempotent read locks with a shared repository.
  - The in-memory idempotent cache holds 1000 entries and does not survive restarts.
  - The in-progress repository is FIFO since 4.19.
- **Monitoring**:
  - Route metrics come from core/micrometer (see core research file).
  - Watch the `moveFailed` directory and the DLQ.
  - `readLockLoggingLevel` is used in the official test; its default was not recorded, so it is UNVERIFIED.
- **Security**:
  - SFTP: set `strictHostKeyChecking=yes` and use known_hosts plus key auth.
  - Keep the `jailStartingDirectory=true` default.
  - Never build the directory from headers.
  - XSLT entity hardening is on by default in 3.40.0.
  - Externalize credentials with `{{...}}` placeholders and Quarkus config.

---

## Reference Implementations

- Official CQ integration test, file: https://github.com/apache/camel-quarkus/tree/main/integration-tests/file. It contains FileRoutes.java, FileResource.java, FileLanguageRoutes.java and FileWatchResource.java. This is the `main` branch, not a 3.40.x tag.
- Camel 4.22 File component reference: https://camel.apache.org/components/4.22.x/file-component.html
- Camel 4.22 File language: https://camel.apache.org/components/4.22.x/languages/file-language.html
- Camel 4.22 File Watch: https://camel.apache.org/components/4.22.x/file-watch-component.html
- CQ testing guide: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html

---

## Source Bibliography

**Primary** (all fetched 2026-10-14; camel.apache.org pages have no page date and are current-stable versioned docs):
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file-cluster-service.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file-watch.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/ftp.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/xslt.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/jaxb.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/bean.html
- https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html
- https://camel.apache.org/camel-quarkus/3.40.x/user-guide/testing.html
- https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html
- https://camel.apache.org/components/4.22.x/file-component.html
- https://camel.apache.org/components/4.22.x/languages/file-language.html
- https://camel.apache.org/components/4.22.x/file-watch-component.html
- https://camel.apache.org/components/4.22.x/sftp-component.html
- https://camel.apache.org/manual/camel-4x-upgrade-guide.html and the per-version pages `-4_9` … `-4_22` (4_18, 4_21 and 4_22 read only partially)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-file/ (3.40.0, 2026-09-24)
- https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-ftp/ (3.40.0, 2026-09-24)
- https://camel.apache.org/releases/ (3.40.0 LTS, 2026-09-28)

**Validation**:
- https://raw.githubusercontent.com/apache/camel-quarkus/main/integration-tests/file/src/main/java/org/apache/camel/quarkus/component/file/it/FileRoutes.java
- https://raw.githubusercontent.com/apache/camel-quarkus/main/integration-tests/file/src/main/java/org/apache/camel/quarkus/component/file/it/FileResource.java

Both are on the `main` branch, fetched 2026-10-14.

**All Deep-Links**: inline next to each claim above.

**Rejected**: the v3.15 research file's citations (4.14.x and 3.27.x pages with a fabricated "Published: March 5, 2026"). They were used only as a topic checklist.

---

## Research Gaps

```
Gap: Camel Quarkus-specific LTS end date for 3.40
Impact: support-window planning
Workaround: assume Quarkus 3.40 LTS dates (to 2027-09-30) as inference
Follow-up: https://camel.apache.org/releases/ "LTS Until" column; dev list
§7-ref: Iteration 1 — IRRESOLVABLE
```
```
Gap: quarkus.camel.cluster.file.heartbeat-timeout-multiplier default (and build-time vs runtime per property)
Impact: cluster failover tuning
Workaround: set explicitly
Follow-up: file-cluster-service.html raw page / extension source in apache/camel-quarkus
§7-ref: Iteration 2 — IRRESOLVABLE
```
```
Gap: Camel 4.13 eager max-messages-per-poll change (exact option name and old/new default)
Impact: poll/pollEnrich batch behaviour
Workaround: set eagerMaxMessagesPerPoll explicitly
Follow-up: https://camel.apache.org/manual/camel-4x-upgrade-guide-4_13.html (raw read)
§7-ref: Iteration 3 — IRRESOLVABLE
```
Other UNVERIFIED items (not looped):
- the runtime body type `GenericFile<File>`
- the SSH library the CQ ftp extension uses in native
- NotifyBuilder in CQ
- XSLT build-time vs runtime properties
- splitter streaming wording for 4.22
- the `doBeforeEach` parameter type
- the plugin create command form
- the `readLockLoggingLevel` default
- the remaining parts of the 4_21 and 4_22 guides (only partly read)

---

## Research Iteration Changelog

| Iteration | Section | Item | Action | Source |
|-----------|---------|------|--------|--------|
| 1 | Mandatory 3 | Default post-processing (`.camel` subfolder) | Resolved (table showed no default; Usage text confirms `.camel`) | https://camel.apache.org/components/4.22.x/file-component.html (2026-10-14) |
| 1 | Conditional A | Consumer charset default UTF-8 | Resolved | https://camel.apache.org/components/4.22.x/file-component.html (2026-10-14) |
| 1 | Conditional E | mina-sftp extension, since 3.33.0, exclusive with ftp | Resolved | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html (2026-10-14) |
| 1 | Migration | 3.40.0 migration guide file/ftp entries | Resolved: none; XSLT changes added | https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.40.0.html (2026-10-14) |
| 1 | Metadata | Camel Quarkus LTS end date | ⚠️ IRRESOLVABLE — no CQ-specific support policy page exists | — |
| 2 | Forbidden 6 | SFTP streamDownload/localWorkDirectory memory behaviour | Resolved | https://camel.apache.org/components/4.22.x/sftp-component.html (2026-10-14) |
| 2 | Conditional C | heartbeat-timeout-multiplier default | ⚠️ IRRESOLVABLE — page shows no default | — |
| 3 | Migration | 4.19 inProgressRepository FIFO (verbatim) | Resolved; upgraded to High | https://camel.apache.org/manual/camel-4x-upgrade-guide-4_19.html (2026-10-14) |
| 3 | Migration | 4.13 eager max-messages option name/default | ⚠️ IRRESOLVABLE — conflicting tool summaries; iteration budget exhausted | — |

---

## Completion Checklist

- [x] Domain complexity tier assessed and documented (Standard)
- [x] All scope areas cited (options, naming, file-watch, large files, errors, FTP/SFTP, native, testing, partners)
- [x] Pattern counts driven by domain needs (5 / 5 / 7)
- [x] Every anti-pattern has alternative
- [x] All CLI commands validated/marked as representative
- [x] Integration examples complete (XSLT + JAXB + Bean; SFTP)
- [x] Sources dated and linked
- [x] Security documented
- [x] 1+ copy-paste working example
- [x] Confidence badge applied to every pattern entry
- [x] All Always-Do patterns triangulated (deep) or downgraded to 🟡 Medium (patterns 4 and 5 downgraded)
- [x] Research Iteration Changelog present and complete
- [x] Research_Quality_Score calculated and added to Metadata
- [x] Every Research Gap cross-referenced in §7

---

## Agent Operation Notes

- **High Confidence (execute without asking)**:
  - Mandatory 1–3 (✓✓ triangulated)
  - the readLock, post-processing and producer defaults read from the 4.22 File page
  - extension availability and the ftp/mina-sftp exclusivity
  - XSLT native classpath-only and the 3.40.0 XSLT hardening
  - SFTP host-key defaults
- **Medium Confidence (validate with user)**:
  - Mandatory 4–5 (single source)
  - the file-cluster-service property defaults (tool summary)
  - the upgrade-guide entries for 4.10, 4.11, 4.18 and 4.21
  - the SFTP readLockTimeout default (conflicting)
  - the integration-test code taken from the `main` branch
- **Low Confidence (must ask human)**: the 3 IRRESOLVABLE items, plus the 9 UNVERIFIED items listed in Research Gaps.
- **Edge Cases (pause)**:
  - 3.40.0 was released on 2026-09-28, 16 days before research (<30 days). Docs looked complete, but patch releases are expected.
  - Quarkus 4 is imminent (core research file).
- **Emergency Stop**: not triggered. All sources are official.
