# Kubernetes Operator Deployment Guide

For `DEPLOYMENT_MODEL=kubernetes-operator`. Use with any `PLATFORM_CATEGORY`.

---

## Operator vs StatefulSet: When to Use Each

| Aspect | Kubernetes Operator | StatefulSet (manual) |
|---|---|---|
| Upgrade | Automated rolling upgrade via CR update | Manual: update image tag + trigger rollout |
| Scaling | Controlled via CR spec (operator enforces quorum) | Manual: risk quorum violation if not careful |
| Backup | Integrated (operator-managed schedules) | Custom scripting with CronJob |
| Failover | Operator detects + coordinates | Kubernetes restarts pod; no cluster-aware coordination |
| Configuration | Operator validates and applies config changes safely | Manual ConfigMap updates; no validation |
| Learning curve | Must understand CRD schema | Must understand platform internals |
| Operator availability | Varies by platform — check if a mature operator exists | Always available |

**Rule**: Use an operator if a mature, officially-supported operator exists for the platform. Do not use unofficial operators in production.

---

## Official Operators by Platform

| Platform | Official Operator | Maturity | Helm Chart |
|---|---|---|---|
| Apache Kafka | Strimzi (CNCF) | Production | strimzi.io/charts |
| Apache Kafka (enterprise) | Confluent Operator | Production | charts.confluent.io |
| MongoDB | Percona Operator for MongoDB | Production | percona.com/helm |
| MongoDB (enterprise) | MongoDB Enterprise Operator | Production | mongodb.github.io |
| PostgreSQL | CloudNativePG (CNCF) | Production | cloudnativepg.io/charts |
| PostgreSQL | Crunchy Postgres Operator | Production | access.crunchydata.com/kubernetes |
| Redis | Redis Operator (spotahome) | Community | charts.redis.io |
| Redis (enterprise) | Redis Enterprise Operator | Production | redis.io/docs/latest/operate/kubernetes |
| Elasticsearch | Elastic Cloud on Kubernetes (ECK) | Production | helm.elastic.co |
| Cassandra | K8ssandra Operator | Production | helm.k8ssandra.io |
| etcd | etcd Operator (Bitnami) | Community | charts.bitnami.com |

---

## Namespace and RBAC Setup

```yaml
# Representative — adapt to your environment
apiVersion: v1
kind: Namespace
metadata:
  name: platform-kafka   # separate namespace per platform
---
# Install Strimzi operator in a dedicated namespace with cluster-scope
helm install strimzi-kafka-operator strimzi/strimzi-kafka-operator \
  --namespace strimzi-system \
  --create-namespace \
  --version 0.40.0 \
  --set watchNamespaces="{platform-kafka}"
```

---

## PersistentVolumeClaim Configuration

```yaml
# Representative — adapt to your environment
# Always request a storage class optimized for the workload:
#   - Streaming/high-throughput write: local-path (NVMe) or io1/io2 (AWS EBS)
#   - General datastore: gp3 (AWS) / premium-rwo (GKE) / managed-premium (AKS)
#   - Read-heavy/analytics: ceph-rbd or longhorn with replication
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-volume-kafka-0
spec:
  accessModes: [ReadWriteOnce]       # StatefulSet: always ReadWriteOnce (one pod per PVC)
  storageClassName: gp3              # pin to specific storage class — never use 'default'
  resources:
    requests:
      storage: 500Gi                 # size based on SCALE_TARGET × replication factor
```

---

## PodDisruptionBudget

```yaml
# Representative — adapt to your environment
# Ensures at least (N-1) pods are available during rolling upgrades and node drains
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: kafka-pdb
  namespace: platform-kafka
spec:
  minAvailable: 2   # for a 3-broker cluster: always keep 2 available → can disrupt 1 at a time
  selector:
    matchLabels:
      strimzi.io/name: kafka-cluster-kafka   # label from the Strimzi operator
```

---

## TopologySpreadConstraints (Zone Awareness)

```yaml
# Representative — adapt to your environment
# Add to the operator's pod template or CR spec (operator-specific field)
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule   # strict: do not schedule if spread would be violated
    labelSelector:
      matchLabels:
        app: kafka-broker
```

---

## Rolling Upgrade via CR (Strimzi example)

```yaml
# Representative — adapt to your environment
# Source: https://strimzi.io/docs/operators/latest/deploying.html#ref-operator-cluster-rolling-updates-str
# Step 1: Update the version field in the Kafka CR
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: kafka-cluster
spec:
  kafka:
    version: 3.7.0   # update from 3.6.x to 3.7.0
    # Strimzi handles the rolling restart of brokers in order
    # Monitors ISR before restarting each broker
```

```bash
# Step 2: Monitor upgrade progress
kubectl get pods -n platform-kafka -w

# Step 3: Verify cluster health post-upgrade
kubectl exec -n platform-kafka kafka-cluster-kafka-0 -- \
  bin/kafka-topics.sh --bootstrap-server localhost:9092 --describe --under-replicated-partitions
# Expected: no output (zero under-replicated partitions)
```

---

## Operator-Integrated Backup (CloudNativePG example)

```yaml
# Representative — adapt to your environment
# Source: https://cloudnativepg.io/docs/current/backup/
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: pg-cluster
spec:
  instances: 3
  backup:
    barmanObjectStore:
      destinationPath: "s3://my-bucket/pg-cluster"
      s3Credentials:
        accessKeyId:
          name: aws-creds
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: aws-creds
          key: SECRET_ACCESS_KEY
      wal:
        compression: bzip2
        maxParallel: 8
    retentionPolicy: "30d"
---
# Schedule backup
apiVersion: postgresql.cnpg.io/v1
kind: ScheduledBackup
metadata:
  name: pg-cluster-daily
spec:
  schedule: "0 3 * * *"   # 3am UTC daily
  backupOwnerReference: self
  cluster:
    name: pg-cluster
```

---

## Headless Service (StatefulSet stable network identity)

```yaml
# Representative — adapt to your environment
# Operators create this automatically; shown here for understanding
apiVersion: v1
kind: Service
metadata:
  name: kafka-brokers
  namespace: platform-kafka
spec:
  clusterIP: None    # headless: no VIP; DNS returns individual pod IPs
  selector:
    strimzi.io/name: kafka-cluster-kafka
  ports:
    - port: 9092
      name: tcp-clients
    - port: 9093
      name: tcp-replication
```

DNS resolution for StatefulSet pods:
```
<pod-name>.<service-name>.<namespace>.svc.cluster.local
kafka-cluster-kafka-0.kafka-brokers.platform-kafka.svc.cluster.local
kafka-cluster-kafka-1.kafka-brokers.platform-kafka.svc.cluster.local
```
