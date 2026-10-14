# Remote Files: ftp, sftp, mina-sftp (Camel Quarkus 3.40.x)

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Extension choice

| Extension | Schemes | Support | Source |
|---|---|---|---|
| `camel-quarkus-ftp` | `ftp:`, `ftps:`, `sftp:` | JVM and native since 1.0.0 | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/ftp.html |
| `camel-quarkus-mina-sftp` | `mina-sftp:` | JVM and native since 3.33.0 | https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/mina-sftp.html |
| `camel-quarkus-jsch` | SCP only, **not** SFTP | see index | https://camel.apache.org/camel-quarkus/3.40.x/reference/index.html |

- `camel-quarkus-ftp` and `camel-quarkus-mina-sftp` cannot be used together; both pages warn of build-time failures (high confidence).
- The Camel 4.22 SFTP component uses JSch ([page](https://camel.apache.org/components/4.22.x/sftp-component.html)). Which SSH library the Camel Quarkus `ftp` extension uses in native mode is (unverified).

## SFTP defaults

Source: https://camel.apache.org/components/4.22.x/sftp-component.html.

| Option | Default | Confidence |
|---|---|---|
| `strictHostKeyChecking` | `no` (MITM warning on the page) | high |
| `useUserKnownHostsFile` | `true` | high |
| `streamDownload` | `false` | high |
| `stepwise` | `true`; cannot combine with `streamDownload` | high |
| `jailStartingDirectory` | `true` | high |
| `disconnect` | `false` | high |
| `soTimeout` | `300000` ms | high |
| `readLockTimeout` | `10000` ms per the SFTP summary, but the File page says the FTP default is `20000` | conflicting (unverified); set it explicitly |

## Secure download and hand-off

```java
// Camel Quarkus 3.40.x (camel-quarkus-ftp): download via a local work dir, then hand off to file:
from("sftp:{{sftp.host}}/outbound?username={{sftp.user}}&privateKeyFile={{sftp.key}}"
     + "&strictHostKeyChecking=yes&knownHostsFile={{sftp.known-hosts}}"
     + "&localWorkDirectory=/tmp/camel-sftp&readLock=changed&move=.done")
    .to("file:/data/in?tempPrefix=.tmp-");
```

## Security notes

- Use known_hosts plus key authentication; externalize credentials with `{{...}}` placeholders (high confidence for the defaults above; the placeholder advice is a recommendation).
- Keep `jailStartingDirectory=true`. Per the research, Camel 4.21 made ftp/sftp/mina-sftp/smb/azure-files reject downloads outside the local work dir unless `jailStartingDirectory=false`, and 4.22.1 applies the jail to remote consumers (medium confidence); the 4.21 and 4.22 guides were only partly read. Re-test `localWorkDirectory` paths after upgrading.
- Large files: without `localWorkDirectory` or `streamDownload=true`, remote files are loaded into memory (medium confidence).
