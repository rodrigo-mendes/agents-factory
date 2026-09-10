# VM and Bare-Metal Deployment Guide

For `DEPLOYMENT_MODEL=vm` or `DEPLOYMENT_MODEL=bare-metal`. Suitable for: production environments where Kubernetes is not available, maximum performance tuning, regulated environments requiring bare-metal isolation.

---

## OS and Kernel Tuning

These settings apply regardless of the platform. Research the platform-specific recommendations and compare against these baseline tunings:

### File Descriptor Limits

```bash
# Representative — adapt to your environment
# Most platforms (Kafka, MongoDB, Elasticsearch) require high fd limits
# /etc/security/limits.conf or /etc/systemd/system/[service].service.d/limits.conf

[platform-user] soft nofile 65536
[platform-user] hard nofile 65536

# Or in systemd unit:
[Service]
LimitNOFILE=65536
```

### Virtual Memory (for Elasticsearch, Redis with AOF, PostgreSQL)

```bash
# Representative — adapt to your environment
# vm.swappiness: how aggressively the kernel swaps memory to disk
# For databases: low value (1) — keep data in RAM, avoid swap

# /etc/sysctl.conf or /etc/sysctl.d/99-platform.conf
vm.swappiness = 1                # 1 for databases (not 0 — fully disable can cause OOM kill)
vm.overcommit_memory = 1        # for Redis — allows Redis fork() for RDB snapshots
vm.dirty_ratio = 15             # max % of memory that can be dirty before blocking writes
vm.dirty_background_ratio = 5   # % of memory that triggers background writeback

# Apply without reboot
sysctl -p /etc/sysctl.d/99-platform.conf
```

### Huge Pages

```bash
# Representative — adapt to your environment
# PostgreSQL benefits from huge pages (2MB pages reduce TLB misses)
# MongoDB (WiredTiger) requires huge pages DISABLED (set to madvise)
# Kafka/Elasticsearch: not applicable (JVM)

# PostgreSQL — enable huge pages
sysctl -w vm.nr_hugepages=512    # number of 2MB pages = desired_huge_memory / 2MB
# /etc/sysctl.d/99-hugepages.conf
vm.nr_hugepages = 512

# PostgreSQL postgresql.conf
huge_pages = on

# MongoDB/Redis — disable transparent huge pages (THP)
# /etc/systemd/system/disable-thp.service
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
```

### Network Tuning (for high-throughput streaming platforms)

```bash
# Representative — adapt to your environment
# Increase socket buffer sizes for Kafka, Pulsar
net.core.rmem_max = 134217728         # 128MB receive buffer
net.core.wmem_max = 134217728         # 128MB send buffer
net.ipv4.tcp_rmem = 4096 65536 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_congestion_control = bbr  # better for high-latency links
```

---

## Disk Layout

```
Recommended disk layout for stateful platforms:
  /data/[platform]/data     → data volume (NVMe/SSD — sized for SCALE_TARGET × replication)
  /data/[platform]/logs     → WAL/journal volume (separate disk reduces write contention)
  /data/[platform]/backup   → local backup cache (HDD acceptable)
  /var/log/[platform]       → application logs (OS disk is fine)

Filesystem:
  ext4: most portable; good for most workloads
  xfs: better for large files and high-throughput sequential writes (Kafka, Elasticsearch)
  
Mount options (add to /etc/fstab):
  noatime,nodiratime         — skip access time updates (reduces I/O overhead)
  defaults,noatime           — safe default for most platforms

RAID:
  Do NOT use software RAID 5 for write-heavy databases — write penalty too high
  RAID 10 (striped mirrors): best performance + redundancy for local storage
  For distributed platforms (Kafka RF=3, MongoDB RS=3): local RAID unnecessary — platform handles replication
```

---

## systemd Service Unit

```ini
# Representative — adapt to your environment
# /etc/systemd/system/[platform].service

[Unit]
Description=[Platform] Service
After=network.target
Wants=network.target

[Service]
Type=forking                          # or 'simple' if process stays in foreground
User=[platform-user]
Group=[platform-group]
ExecStart=/opt/[platform]/bin/[start-command] --config /etc/[platform]/[platform].conf
ExecStop=/opt/[platform]/bin/[stop-command]
Restart=on-failure
RestartSec=5

# Resource limits
LimitNOFILE=65536
LimitNPROC=32768
LimitMEMLOCK=infinity                # for platforms that lock memory (Elasticsearch, Redis with mlock)

# JVM platforms: set heap via environment
Environment="JAVA_OPTS=-Xms8g -Xmx8g -XX:+UseG1GC"

# Security hardening (optional — adjust per platform requirements)
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/data/[platform] /var/log/[platform]

[Install]
WantedBy=multi-user.target
```

```bash
# Apply changes
systemctl daemon-reload
systemctl enable [platform]
systemctl start [platform]
systemctl status [platform]
journalctl -u [platform] -f    # follow logs
```

---

## JVM Tuning (Kafka, Elasticsearch, Cassandra, ZooKeeper)

```bash
# Representative — adapt to your environment
# Common JVM flags for database/platform workloads on JDK 17+

JVM_OPTS="-Xms${HEAP_SIZE} -Xmx${HEAP_SIZE}"   # always set min = max (avoid GC resize pauses)
JVM_OPTS="${JVM_OPTS} -XX:+UseG1GC"              # G1 GC — default for most platforms
JVM_OPTS="${JVM_OPTS} -XX:MaxGCPauseMillis=200"  # target GC pause < 200ms
JVM_OPTS="${JVM_OPTS} -XX:G1HeapRegionSize=16m"  # larger regions for big heaps
JVM_OPTS="${JVM_OPTS} -XX:+PrintGCDetails -Xlog:gc*:file=/var/log/[platform]/gc.log:time:filecount=10,filesize=100m"  # GC logging

# Heap sizing:
# Elasticsearch: max 26–32GB (compressed ordinary object pointers threshold)
# Kafka: 4–8GB (broker relies more on OS page cache than heap)
# Cassandra: 8–16GB (tuned via cassandra-env.sh)
# ZooKeeper: 1–2GB (small metadata store)
```

---

## Security: Non-root Service User

```bash
# Representative — adapt to your environment
# Always run platform as a dedicated non-root user

# Create system user (no login shell, no home directory)
useradd --system --no-create-home --shell /bin/false [platform-user]

# Set ownership of data and config directories
chown -R [platform-user]:[platform-group] /data/[platform]
chown -R [platform-user]:[platform-group] /etc/[platform]

# Verify process runs as expected user
ps aux | grep [platform-process-name]
```

---

## CPU Tuning (NUMA awareness)

```bash
# Representative — adapt to your environment
# Multi-socket servers: bind platform process to one NUMA node to avoid cross-socket memory latency

numactl --hardware                      # list NUMA topology
numactl --cpunodebind=0 --membind=0 \   # bind to NUMA node 0
  /opt/[platform]/bin/[start-command]

# Or via numactl in systemd ExecStart:
ExecStart=numactl --cpunodebind=0 --membind=0 /opt/[platform]/bin/[start-command]
```
