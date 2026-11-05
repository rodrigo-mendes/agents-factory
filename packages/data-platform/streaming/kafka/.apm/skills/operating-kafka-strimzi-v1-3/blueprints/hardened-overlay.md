# Hardened production overlay, Strimzi 1.3.x (assembled, unverified)

Back to [SKILL.md](../SKILL.md). Split out of [deploy-install-and-cr](./deploy-install-and-cr.md) to keep each blueprint under 160 lines.


Assembled from documented fields; the combination was never validated on a cluster (unverified, U3). On 1.3.1 use `version: 4.3.2`; its `metadataVersion` is not recorded (unverified, U8), so keep the value from the example until checked. Validate the assembled file with `kubectl apply --dry-run=server -f <file>` before applying (unverified, U6). The overlay shows only the `Kafka` resource: it needs a controller `KafkaNodePool` and a broker pool, both labelled `strimzi.io/cluster: my-cluster`; the controller pool is fixed at creation (see [never-do N4](./never-do-patterns.md#n4-changing-a-controller-pool) and [deploy-install-and-cr](./deploy-install-and-cr.md)).

```yaml
apiVersion: kafka.strimzi.io/v1
kind: Kafka
metadata:
  name: my-cluster
spec:
  kafka:
    version: 4.3.2
    metadataVersion: "4.3-IV0"
    rack:
      type: topology-label
      topologyKey: topology.kubernetes.io/zone
    listeners:
      - name: tls
        port: 9093
        type: internal
        tls: true
        authentication:
          type: tls
        networkPolicyPeers:
          - podSelector:
              matchLabels:
                app: kafka-client
    authorization:
      type: simple
      superUsers:
        - CN=my-admin
    config:
      default.replication.factor: 3
      min.insync.replicas: 2
      auto.create.topics.enable: false   # (medium confidence) M3
    metricsConfig:
      type: strimziMetricsReporter
  maintenanceTimeWindows:
    - "* * 0-1 ? * SUN,MON,TUE,WED,THU *"   # UTC
  entityOperator:
    topicOperator: {}
    userOperator: {}
  cruiseControl: {}
  kafkaExporter:
    groupRegex: ".*"
    topicRegex: ".*"
```

Broker pool sizing (assembled, unverified; the values are the documented example, not a recommendation):

```yaml
spec:
  replicas: 3
  roles: [broker]
  resources:
    requests: { cpu: "1", memory: 2Gi }
    limits:   { cpu: "2", memory: 2Gi }
  jvmOptions:
    "-Xms": 512m
    "-Xmx": 1g
```

The storage `class` field name and where the PDB template lives on a node pool were not confirmed (unverified, U11).
