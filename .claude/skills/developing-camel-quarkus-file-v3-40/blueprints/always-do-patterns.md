# Always-Do Patterns: Camel Quarkus File 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). The patterns are high confidence; only the code sample in pattern 2 is tagged (medium confidence) because it mirrors a `main`-branch example. Atomic writes and idempotency are in [file consumer and producer](./file-consumer-producer.md).

## 1. Extension through the platform BOM

Confidence: high (extension page plus Maven Central `camel-quarkus-file` 3.40.0). The extension provides `file:` in JVM and native mode since 0.4.0 and has no Quarkus configuration options. BOM alignment rules are in the core skill.

```xml
<!-- Camel Quarkus 3.40.x: version managed by quarkus-camel-bom 3.40.x -->
<dependency>
  <groupId>org.apache.camel.quarkus</groupId>
  <artifactId>camel-quarkus-file</artifactId>
</dependency>
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file.html ; https://repo1.maven.org/maven2/org/apache/camel/quarkus/camel-quarkus-file/ (3.40.0, 2026-09-24)

## 2. Explicit read lock

Confidence: high for the options and defaults (versioned 4.22.x page). `readLock` defaults to `none`. Related defaults: `readLockTimeout` `10000` ms (0 or less waits forever), `readLockCheckInterval` `1000` ms (the page warns this may be too fast for slow writers), `readLockMinAge` `0` (applies to `changed` only).

```java
// Camel Quarkus 3.40.x / Camel 4.22.x: mirrors the official CQ integration test (main branch) (medium confidence)
public class InboundFilesRoute extends org.apache.camel.builder.RouteBuilder {
    @Override
    public void configure() {
        from("file:target/in?readLock=changed&readLockMinAge=1000&readLockCheckInterval=2000"
             + "&readLockTimeout=5000&move=.done")
            .routeId("inbound-files")
            .to("direct:process");
    }
}
```

Sources: https://camel.apache.org/components/4.22.x/file-component.html ; https://raw.githubusercontent.com/apache/camel-quarkus/main/integration-tests/file/src/main/java/org/apache/camel/quarkus/component/file/it/FileRoutes.java (`main` branch, not the 3.40.x tag) (medium confidence): only the sample is tagged; the defaults above come from the versioned page.

## 3. Explicit post-processing

Confidence: high. "By default, Camel will move consumed files to the `.camel` subfolder relative to the directory where the file was consumed." `delete` and `noop` default to `false`; `noop=true` also sets `idempotent=true`. `move`, `moveFailed` and `preMove` have no default in the options table.

```java
// Camel Quarkus 3.40.x: archive on success, quarantine on failure
from("file:/data/in?readLock=changed"
     + "&move=archive/${date:now:yyyyMMdd}/${file:name}"
     + "&moveFailed=error/${file:name}")
    .to("direct:process");
```

Sources: https://camel.apache.org/components/4.22.x/file-component.html ; https://camel.apache.org/components/4.22.x/languages/file-language.html

## 4. SFTP host key verification

Confidence: high. `strictHostKeyChecking` defaults to `no`; `useUserKnownHostsFile` defaults to `true`. Externalize credentials with `{{...}}` placeholders (resolved by Camel from Quarkus config).

```java
// Camel Quarkus 3.40.x (camel-quarkus-ftp)
from("sftp:{{sftp.host}}/in?username={{sftp.user}}&privateKeyFile={{sftp.key}}"
     + "&strictHostKeyChecking=yes&knownHostsFile={{sftp.known-hosts}}"
     + "&readLock=changed&move=.done")
    .to("direct:process");
```

Source: https://camel.apache.org/components/4.22.x/sftp-component.html

## 5. One remote-file extension

Confidence: high (stated on both extension pages). Choose `camel-quarkus-ftp` (`ftp:`, `ftps:`, `sftp:`; JVM and native since 1.0.0) or `camel-quarkus-mina-sftp` (`mina-sftp:`; since 3.33.0), never both.

```xml
<!-- FTP, FTPS and SFTP -->
<artifactId>camel-quarkus-ftp</artifactId>
<!-- OR, SFTP only on Apache MINA SSHD (do not add alongside camel-quarkus-ftp) -->
<artifactId>camel-quarkus-mina-sftp</artifactId>
```

Sources: https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/ftp.html ; https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html
