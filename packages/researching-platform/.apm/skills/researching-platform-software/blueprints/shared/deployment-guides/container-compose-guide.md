# Container / Docker Compose Deployment Guide

For `DEPLOYMENT_MODEL=container-compose`. Suitable for: development, integration testing, small-scale staging. NOT recommended for production HA.

---

## Limitations vs Kubernetes

| Concern | Docker Compose | Kubernetes (operator) |
|---|---|---|
| HA / failover | No — single host; no automatic failover | Yes — multi-node; operator-managed |
| Cluster networking | No — all containers on same host | Yes — pod-to-pod across nodes |
| Persistent volume management | Manual — bind mount or named volume | Managed — PVC with storage class |
| Rolling upgrade | No — manual stop + start | Yes — operator CR update |
| Production suitability | Dev/test/staging only | Production |

**Use Compose for**: local development, CI pipelines, integration tests, proof of concept.

---

## General Compose Template Pattern

```yaml
# Representative — adapt to your environment
# Always pin exact image versions — never use 'latest'
# Source: official Docker Hub image page for the platform
version: "3.9"

volumes:
  data-volume:
    driver: local

networks:
  platform-net:
    driver: bridge

services:
  [platform-service-name]:
    image: [official-image]:[EXACT_VERSION_TAG]   # pin to exact version
    container_name: [platform-name]
    restart: unless-stopped

    environment:
      # Minimal required config via environment variables
      [ENV_VAR_NAME]: [value]

    ports:
      - "127.0.0.1:[host-port]:[container-port]"  # bind to localhost only — not 0.0.0.0

    volumes:
      - data-volume:/[data-directory-inside-container]

    networks:
      - platform-net

    healthcheck:
      test: [health check command]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

---

## Kafka Compose Example (KRaft mode, single broker)

```yaml
# Representative — adapt to your environment
# Source: https://hub.docker.com/r/apache/kafka (DATE)
# KRaft mode (no ZooKeeper) — available since Kafka 3.3; recommended since 3.6
version: "3.9"

services:
  kafka:
    image: apache/kafka:3.7.0   # pin exact version
    container_name: kafka
    ports:
      - "127.0.0.1:9092:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_CONTROLLER_QUORUM_VOTERS: "1@kafka:9093"
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "false"
    volumes:
      - kafka-data:/var/lib/kafka/data
    healthcheck:
      test: ["CMD", "kafka-topics.sh", "--bootstrap-server", "localhost:9092", "--list"]
      interval: 30s
      timeout: 10s
      retries: 5

volumes:
  kafka-data:
```

---

## MongoDB Compose Example (single node with auth)

```yaml
# Representative — adapt to your environment
# Source: https://hub.docker.com/_/mongo (DATE)
version: "3.9"

services:
  mongo:
    image: mongo:7.0.8   # pin exact version
    container_name: mongo
    ports:
      - "127.0.0.1:27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD_FILE: /run/secrets/mongo_root_password  # never plain text password
    volumes:
      - mongo-data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/init.js:ro
    healthcheck:
      test: ["CMD", "mongosh", "--quiet", "--eval", "db.adminCommand('ping').ok"]
      interval: 30s
      timeout: 10s
      retries: 3
    secrets:
      - mongo_root_password

secrets:
  mongo_root_password:
    file: ./secrets/mongo_root_password.txt   # file with password; never commit to git

volumes:
  mongo-data:
```

---

## Redis Compose Example (with auth and persistence)

```yaml
# Representative — adapt to your environment
# Source: https://hub.docker.com/_/redis (DATE)
version: "3.9"

services:
  redis:
    image: redis:7.2.4-alpine   # pin exact version; alpine for smaller image
    container_name: redis
    command: >
      redis-server
      --requirepass $${REDIS_PASSWORD}
      --appendonly yes
      --appendfsync everysec
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
    ports:
      - "127.0.0.1:6379:6379"   # never expose to 0.0.0.0 without auth + firewall
    volumes:
      - redis-data:/data
    environment:
      REDIS_PASSWORD_FILE: /run/secrets/redis_password
    healthcheck:
      test: ["CMD", "redis-cli", "--pass", "$${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 5s
      retries: 3
    secrets:
      - redis_password

secrets:
  redis_password:
    file: ./secrets/redis_password.txt

volumes:
  redis-data:
```

---

## Secrets Management in Compose

```
NEVER: environment variable with plain text password in compose file
  BAD: POSTGRES_PASSWORD: mypassword  ← committed to git → exposed

ALWAYS: use one of:
  1. Docker secrets (file-based):
     secrets:
       db_password:
         file: ./secrets/db_password.txt
  2. .env file (not committed to git; listed in .gitignore):
     DB_PASSWORD=${DB_PASSWORD}    ← value comes from .env or CI environment
  3. External secret manager (Vault, AWS Secrets Manager) with init container

Template for .gitignore:
  .env
  secrets/
  *.secret
  *.key
```

---

## Volume Strategy

```
Named volumes (Docker-managed):
  ✅ Automatic location management
  ✅ Survives container removal
  ❌ Harder to inspect or back up directly

Bind mounts (host path):
  ✅ Easy to inspect and back up (just copy the directory)
  ✅ Exact path control
  ❌ Permissions issues between host and container user
  ❌ Platform-specific (breaks on different OSes)

Recommendation:
  - Development: bind mounts for easy inspection
  - Staging/CI: named volumes for consistency
  - Production: neither — use Kubernetes PVC
```
