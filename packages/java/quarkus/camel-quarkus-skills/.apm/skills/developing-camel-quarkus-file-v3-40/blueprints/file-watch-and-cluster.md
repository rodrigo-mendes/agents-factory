# file-watch and file-cluster-service: Camel Quarkus 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## file-watch (event-driven)

`camel-quarkus-file-watch` is JVM and native since 1.0.0, Stable ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file-watch.html)). On macOS the JVM mode uses a JNA WatchService; native mode overrides it with `java.nio.file.WatchService`, which may be slower (same page).

Defaults (high confidence, https://camel.apache.org/components/4.22.x/file-watch-component.html):

| Option | Default |
|---|---|
| `events` | `CREATE,MODIFY,DELETE` |
| `recursive` | `true` (note: `file:` defaults to `false`) |
| `antInclude` | `**` |
| `useFileHashing` | `true` |
| `autoCreate` | `true` |
| `concurrentConsumers` / `pollThreads` | `1` / `1` |
| `queueSize` | `2147483647` |
| `fileHasher` | `#murmur3FFileHasher` |

```java
// Camel Quarkus 3.40.x: react to changes, no move/readLock lifecycle
from("file-watch:/data/watch?events=CREATE,MODIFY&antInclude=**/*.csv")
    .to("direct:changed");
```

| Choice | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `file:` polling | Read locks, move/idempotent lifecycle | Latency (`delay` 500 ms) | Batch ingestion |
| `file-watch:` | Low latency, change events incl. DELETE | No move/readLock lifecycle | Reacting to changes |

## file-cluster-service (singleton consumer)

`camel-quarkus-file-cluster-service` is a FileLock-based Camel Cluster Service SPI, JVM and native since 3.10.0, Stable. It needs a reliable shared file system with working file locks ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/file-cluster-service.html)).

`quarkus.camel.cluster.file.*` defaults (medium confidence); the page was read through a tool summary:

| Property | Default |
|---|---|
| `enabled` | `true` |
| `id`, `root` | null |
| `order` | `2147482647` |
| `acquire-lock-delay` | 1000 ms (from the description) |
| `acquire-lock-interval` | 10000 ms (from the description) |
| `cluster-data-task-max-attempts` | `5` |
| `cluster-data-task-timeout` | 10 seconds |
| `heartbeat-timeout-multiplier` | (unverified): set it explicitly |

The build-time vs runtime flag of each property is also (unverified).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Single instance | Simplicity | HA | One node |
| file-cluster-service | Shared-FS leadership | Needs a reliable shared FS and file locks | Few nodes on NFS or a shared volume |
| `idempotent*` read lock + shared repository | All nodes consume | Repository infrastructure | Throughput across nodes |

Other cluster services (for example Kubernetes) were not researched here. Do not use `readLock=fileLock` on shared mounts as a substitute (see [never-do](./never-do-patterns.md)).
