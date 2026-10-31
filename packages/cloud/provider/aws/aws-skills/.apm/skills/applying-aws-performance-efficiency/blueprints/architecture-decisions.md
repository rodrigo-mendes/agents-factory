# Architecture Decisions — Performance Efficiency Pillar

Full option/tradeoff matrices for the three ⚠️ Ask-First decision points in SKILL.md.

Source: AWS Well-Architected Framework Performance Efficiency Pillar (Nov 6, 2024); service currency verified 2026-08-28.

---

## Decision A — Compute Model Selection

**Architect Instruction**: Ask what are the p99 latency requirements, expected traffic shape (spiky vs steady), and stateful/stateless constraints when the team proposes a compute model.

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| Functions | AWS Lambda | Ops simplicity, scale-to-zero, event-driven responsiveness | Cold start latency, 15-minute execution limit | Spiky or event-driven workloads, short tasks, unpredictable traffic |
| Containers | Amazon ECS / EKS + AWS Fargate | Portability, packing density, orchestration control | Cluster and orchestration management overhead | Microservices, steady long-running services, migration from on-premises containers |
| Instances | Amazon EC2 | Full control, widest instance and accelerator choice | OS patching, scaling management, operational burden | Specialised OS/kernel requirements, GPU/HPC, ISV licensing, legacy lift |
| Batch | AWS Batch | Managed parallel throughput, job scheduling | Not suitable for interactive or low-latency workloads | Large batch or parallel data processing jobs |

**Source**: PERF02-BP01 — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/perf_compute_hardware_select_best_compute_options.html

---

## Decision B — Processor Architecture

**Architect Instruction**: Ask whether all application dependencies and third-party binaries support ARM64, and whether the target region carries M9g/C9g, before committing to Graviton5. If a memory-optimised ARM64 instance is required, default to Graviton4 R8g until an R-series Graviton5 is confirmed GA.

⚠️ **Migration Note (2026)**: Graviton5 is now the default current-generation ARM64. Do not present Graviton4 as the newest generation.

| Option | AWS Service | Optimizes | Sacrifices | Best When |
|--------|-------------|-----------|------------|-----------|
| ARM64 (current gen, Graviton5) | M9g/M9gd, C9g/C9gd | Best price-performance in EC2; up to 25% better compute vs Graviton4; 5x L3 cache; higher network/EBS bandwidth | ARM64 recompilation/compatibility effort; no R-series Graviton5 confirmed GA yet; limited regions at launch | New general-purpose/compute-optimised builds where all dependencies are ARM64-compatible and region carries M9g/C9g |
| ARM64 (prior gen, Graviton4) | M8g, C8g, R8g | Broad regional availability; R8g memory-optimised ARM64 option; strong price-performance vs x86 | One generation behind Graviton5 on compute | Memory-optimised ARM64 needs (R8g), or regions without Graviton5 |
| x86 | Intel/AMD EC2 instance families | Broadest binary compatibility, no recompilation required | Higher cost per unit performance, higher energy consumption | x86-only ISV software, binaries without source access |

**Pre-migration checklist**:
1. Audit all application dependencies and third-party binaries for ARM64 compatibility.
2. Confirm target region carries M9g (general-purpose) or C9g (compute-optimised) families.
3. Benchmark on Graviton5 in non-production against current instance type.
4. Run AWS Compute Optimizer to identify migration candidates from existing x86 fleets.

**Source**: PERF02-BP06 + https://aws.amazon.com/ec2/graviton/ + https://aws.amazon.com/blogs/aws/amazon-ec2-c9g-and-c9gd-instances-powered-by-aws-graviton5-processors-are-now-available/

---

## Decision C — Data Store Selection (Mechanical Sympathy)

**Architect Instruction**: Ask what the data access pattern is (lookup by key, complex query, full-text search, cached read, binary object) before selecting a data store — never default to a single RDS instance for all patterns.

| Use Case | AWS Service | Optimizes | Sacrifices |
|----------|-------------|-----------|------------|
| Key-value / high scale | Amazon DynamoDB | Throughput, serverless operations, horizontal scale | Complex relational queries, joins |
| Relational / ACID | Amazon Aurora / Amazon RDS | SQL expressiveness, transactional integrity | Horizontal write scaling limits |
| Read-heavy / caching | Amazon ElastiCache (Redis / Memcached) | Sub-millisecond read latency | Consistency guarantees, additional cost |
| Full-text search / relevance | Amazon OpenSearch Service | Relevance ranking, analytics | Operational overhead, cost |
| Object / blob storage | Amazon S3 | Cost, durability, scale | Latency compared to in-memory or block storage |

**Source**: Design principle "Consider mechanical sympathy" + Data management best-practice area — https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/data-management.html

---

## Reference Architecture — Variable-Traffic Web Application (2026)

**Context**: Multi-tier web application with variable traffic, requiring efficient compute, caching, and data store alignment.

| Layer | Service | Purpose |
|-------|---------|---------|
| Compute | EC2 Auto Scaling (Graviton5 M9g/C9g; Graviton4 M8g/C8g fallback) | Right-sized ARM64 application tier with target-tracking |
| Load balancing | Application Load Balancer (ALB) | Distributes traffic; provides `RequestCountPerTarget` for target-tracking |
| Caching | Amazon ElastiCache (Redis) | Sub-millisecond read caching to offload Aurora |
| Relational data | Amazon Aurora | ACID-compliant relational data store |
| Key-value / scale | Amazon DynamoDB | High-throughput key-value access patterns |
| Observability | CloudWatch + CloudWatch Agent | CPU, memory, IOPS, network → Compute Optimizer data source |
| Optimisation | AWS Compute Optimizer | Continuous right-sizing recommendations |

**Key pre-deployment decisions**:
- Lambda vs EC2 (based on traffic shape, latency requirements, stateful/stateless nature)
- Graviton5 vs Graviton4 vs x86 (ARM64 binary compatibility of all dependencies + regional M9g/C9g availability)

**Scaling path**:
1. Begin with EC2 Auto Scaling on Graviton5 M9g behind ALB.
2. Migrate stateless event-driven components to Lambda as traffic patterns become well-understood.
3. Introduce DynamoDB Accelerator (DAX) if DynamoDB read latency becomes a bottleneck.

**Source**: Derived from PERF02-BP01, PERF02-BP04, PERF02-BP05, PERF02-BP06, and PERF03 data management best-practice area.
