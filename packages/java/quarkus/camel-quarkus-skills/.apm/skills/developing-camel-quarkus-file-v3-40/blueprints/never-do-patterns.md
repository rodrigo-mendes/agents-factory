# Never-Do Patterns: Camel Quarkus File 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

Contents: [1 no read lock](#1-consuming-without-a-read-lock-severity-high) · [2 fileLock on a share](#2-readlockfilelock-on-a-mountshare-severity-high) · [3 SFTP host keys](#3-sftp-with-stricthostkeycheckingno-severity-high) · [4 ftp plus mina-sftp](#4-combining-camel-quarkus-ftp-and-camel-quarkus-mina-sftp-severity-high) · [5 jsch is SCP](#5-camel-quarkus-jsch-for-sftp-severity-moderate) · [6 charsets](#6-add-all-charsets-enabled-without-need-severity-low-inferred) · [7 deprecated options](#7-forcewrites-and-boolean-presort-severity-moderate-medium-confidence) · [8 dynamic paths](#8-placeholders-in-the-directory-path-severity-high-medium-confidence) · [9 large files](#9-loading-large-files-into-memory-severity-moderate-medium-confidence)

## 1. Consuming without a read lock (severity: high)

The default is `readLock=none`. Truncated or partial payloads get processed and then moved away.

```java
// ❌ WRONG: readLock defaults to none
from("file:/data/in").to("direct:process");
// ✅ CORRECT
from("file:/data/in?readLock=changed&readLockMinAge=1000").to("direct:process");
```

Source: https://camel.apache.org/components/4.22.x/file-component.html

## 2. readLock=fileLock on a mount/share (severity: high)

The page says this approach "should be avoided when accessing a remote file system via a mount/share". That locks are unreliable across nodes, so files can be processed twice, is an inference (medium confidence), not a page quote. Multi-node options are in Ask First "Several instances" in SKILL.md.

```java
// ❌ WRONG
from("file:/mnt/nfs/in?readLock=fileLock").to("direct:process");
// ✅ CORRECT (High): an explicit lock other than fileLock
from("file:/mnt/nfs/in?readLock=changed&readLockMinAge=1000").to("direct:process");
```

Multi-node coordination (shared `idempotentRepository`, cluster singleton) is medium confidence: see Ask First "Several instances" in SKILL.md and [file-watch and cluster](./file-watch-and-cluster.md).

Source: https://camel.apache.org/components/4.22.x/file-component.html

## 3. SFTP with strictHostKeyChecking=no (severity: high)

`no` is the default, and the page warns it leaves connections vulnerable to man-in-the-middle attacks.

```java
// ❌ WRONG: strictHostKeyChecking defaults to no
from("sftp:user@host/in?password=RAW({{sftp.pwd}})")
// ✅ CORRECT
from("sftp:user@host/in?privateKeyFile={{sftp.key}}&strictHostKeyChecking=yes&knownHostsFile={{sftp.known-hosts}}")
```

Source: https://camel.apache.org/components/4.22.x/sftp-component.html

## 4. Combining camel-quarkus-ftp and camel-quarkus-mina-sftp (severity: high)

Both pages state they cannot be used together; having both "can cause build-time failures".

```xml
<!-- ❌ WRONG -->
<artifactId>camel-quarkus-ftp</artifactId> ... <artifactId>camel-quarkus-mina-sftp</artifactId>
<!-- ✅ CORRECT -->
<artifactId>camel-quarkus-ftp</artifactId> <!-- ftp:, ftps:, sftp: -->
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/ftp.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html

## 5. camel-quarkus-jsch for SFTP (severity: moderate)

The reference index lists `camel-quarkus-jsch` as SCP, not SFTP. Using it gives no `sftp:` scheme.

```xml
<!-- ❌ WRONG for SFTP -->
<artifactId>camel-quarkus-jsch</artifactId>
<!-- ✅ CORRECT -->
<artifactId>camel-quarkus-ftp</artifactId>
```

Source: https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html

## 6. add-all-charsets enabled without need (severity: low, inferred)

The native guide says "By default, not all Charsets are available in native mode", and the fix applies when the error occurs. The File consumer defaults to `UTF-8` with no `charset` option. That enabling it "just in case" is wrong is an inference (medium confidence): the guide only calls it a fix for a missing charset, so this item is advisory and is not in the SKILL.md Never Do table.

```properties
# ❌ WRONG: enabled "just in case" (larger native image)
quarkus.native.add-all-charsets=true
# ✅ CORRECT: add it only after an UnsupportedCharsetException, for routes using charset=ISO-8859-1 etc.
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/user-guide/native-mode.html ; https://camel.apache.org/components/4.22.x/file-component.html

## 7. forceWrites and boolean preSort (severity: moderate, medium confidence)

Advisory only (Ask First in SKILL.md, not Never Do): the 4.22 upgrade guide was only partly read, so the entries below are medium confidence. In Camel 4.22 `forceWrites` is deprecated (default changed to `false`) and `preSort` changed from boolean to String.

```java
// ❌ WRONG
to("file:/out?forceWrites=true")
// ✅ CORRECT (preSort values per the research; medium confidence)
from("file:/in?preSort=modified&maxMessagesPerPoll=100")
```

Source: https://camel.apache.org/manual/camel-4x-upgrade-guide-4_22.html

## 8. Placeholders in the directory path (severity: high, medium confidence)

`directoryName` "must not contain `${ }` placeholders"; dynamic names belong in `fileName` or the `CamelFileName` header. The security framing (escape from the intended tree) is an inference. Remote consumers jail paths by default (`jailStartingDirectory=true`).

```java
// ❌ WRONG: directory from an untrusted header
.toD("file:/data/${header.tenant}/out")
// ✅ CORRECT: fixed root, validated header
.setHeader(Exchange.FILE_NAME, simple("${header.validatedTenant}/out-${file:onlyname}"))
.to("file:/data")
```

Sources: https://camel.apache.org/components/4.22.x/file-component.html ; https://camel.apache.org/components/4.22.x/sftp-component.html

## 9. Loading large files into memory (severity: moderate, medium confidence)

On the File page, `charset` carries "do not use this if you have big messages". For SFTP with `streamDownload=false` (default), remote files are loaded into memory unless `localWorkDirectory` is set.

```java
// ❌ WRONG
from("sftp:host/big?charset=ISO-8859-1").convertBodyTo(String.class).to("direct:parse");
// ✅ CORRECT (streamDownload=true cannot combine with stepwise=true)
from("sftp:host/big?localWorkDirectory=/tmp/camel-work")
    .split(body().tokenize("\n")).streaming()
    .to("direct:line");
```

Sources: https://camel.apache.org/components/4.22.x/file-component.html ; https://camel.apache.org/components/4.22.x/sftp-component.html. Splitter streaming wording for 4.22 is (unverified) (see the [register](./unverified-and-risks.md)).
