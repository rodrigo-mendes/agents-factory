# Always Do Patterns — OCI APM & Management Dashboards

Mandatory patterns with full code examples. All patterns are non-negotiable for production OCI APM deployments.

---

## Pattern 1: Isolated APM Domain per Environment

**Pillar**: Security + Operational Efficiency

Provision distinct APM Domains per lifecycle environment inside dedicated compartments. Never share a production APM Domain with dev/test workloads.

```bash
# Create production APM Domain
rtk oci apm-control-plane apm-domain create \
  --compartment-id ocid1.compartment.oc1..prod \
  --display-name "Prod-APM-Domain" \
  --is-free-tier false

# Create separate dev APM Domain
rtk oci apm-control-plane apm-domain create \
  --compartment-id ocid1.compartment.oc1..dev \
  --display-name "Dev-APM-Domain" \
  --is-free-tier true
```

After provisioning, retrieve the domain endpoint and keys:

```bash
rtk oci apm-control-plane apm-domain get \
  --apm-domain-id <apm_domain_ocid> \
  --query "data.{Endpoint:\"data-upload-endpoint\", Status:\"lifecycle-state\"}"
```

---

## Pattern 2: Private Data Keys in OCI Vault via Instance Principal

**Pillar**: Security

Store the APM Private Data Key as an OCI Vault secret. Retrieve at runtime using Instance Principal — no static credentials in files or env vars.

### Step 1: Store key in OCI Vault
```bash
# Base64-encode the key value
KEY_B64=$(echo -n "<your_private_data_key>" | base64)

rtk oci vault secret create-base64 \
  --compartment-id ocid1.compartment.oc1..prod \
  --secret-name "APM_Private_Key" \
  --vault-id ocid1.vault.oc1..xxx \
  --key-id ocid1.key.oc1..xxx \
  --secret-content-content "$KEY_B64"
```

### Step 2: IAM Dynamic Group for compute nodes
```
# OCI Console → Identity → Dynamic Groups → Create
# Name: APMAgentsGroup
# Rule (matches all instances in prod compartment):
Any {instance.compartment.id = 'ocid1.compartment.oc1..prod'}
```

### Step 3: IAM Policy for secret access
```
allow dynamic-group APMAgentsGroup to read vaults in compartment ProdCompartment
allow dynamic-group APMAgentsGroup to read keys in compartment ProdCompartment
allow dynamic-group APMAgentsGroup to use secret-family in compartment ProdCompartment where target.secret.name = 'APM_Private_Key'
```

### Step 4: Retrieve key at runtime (Java startup script)
```bash
#!/bin/bash
# Fetch key from Vault using Instance Principal (no credentials needed on the instance)
APM_KEY=$(oci secrets secret-bundle get \
  --secret-id ocid1.vaultsecret.oc1..xxx \
  --auth instance_principal \
  --query "data.\"secret-bundle-content\".content" \
  --raw-output | base64 --decode)

export OCI_APM_PRIVATE_KEY="$APM_KEY"
export OCI_APM_UPLOAD_ENDPOINT="https://xxxxxxxx.apm-agt.us-ashburn-1.oci.oraclecloud.com"
```

---

## Pattern 3: IAM RBAC for Management Dashboards

**Pillar**: Security

Use group-level grants only. Separate view-only consumers from engineers who manage dashboard definitions.

```
# View-only: can see dashboards and filter data
allow group ObservabilityConsumers to use management-dashboards in compartment ProdCompartment
allow group ObservabilityConsumers to read apm-domains in compartment ProdCompartment

# SRE/DevOps: can create, edit, delete dashboard definitions
allow group ObservabilityEngineers to manage management-dashboards in compartment ProdCompartment
allow group ObservabilityEngineers to manage apm-domains in compartment ProdCompartment
```

Never grant `manage management-dashboards` to individual users — use groups only.

---

## Pattern 4: Global Dashboard Filters on Every Widget

**Pillar**: Operational Efficiency

All widgets must reference dashboard-level global variables, not hardcoded values. Configure in the OCI Console dashboard editor:

1. Open dashboard → **Edit** → top-right **Filters** button.
2. Add filters: `Compartment` (type: Compartment) and `ApmDomain` (type: APM Domain).
3. For each APM QL widget, open widget settings → check **Inherit Global Compartment Filter** and **Inherit Global APM Domain Filter**.

For OCI Monitoring widgets, use MQL with variable substitution:
```
# Correct — references filter variable
CPUUtilization[1m]{compartmentId = "${compartment_id}"}.mean()

# Wrong — hardcoded compartment
CPUUtilization[1m]{compartmentId = "ocid1.compartment.oc1..abc"}.mean()
```

For APM QL widgets, reference variables:
```sql
-- Correct: uses dashboard variable
show spans | where apmDomainId = '${apm_domain_id}'
  | group by serviceName | select avg(duration)

-- Wrong: hardcoded OCID
show spans | where apmDomainId = 'ocid1.apmdomain.oc1..xyz'
  | group by serviceName | select avg(duration)
```

---

## Pattern 5: APM Java Agent via `-javaagent` JVM Flag

**Pillar**: Operational Efficiency

Auto-instrument JVM applications (Tomcat, WildFly, WebLogic) using the OCI APM Java Agent. Do not manually instrument JDBC, HTTP clients, or frameworks that the agent covers.

### Agent.properties (minimal required config)
```properties
# /opt/oracle/apmagent/config/Agent.properties
com.oracle.apm.agent.public.data.key=<PUBLIC_KEY>     # For RUM/browser — optional if server-only
com.oracle.apm.agent.service.name=payment-service      # Logical service name in traces
com.oracle.apm.agent.data.upload.endpoint=https://xxxxxxxx.apm-agt.us-ashburn-1.oci.oraclecloud.com
```

For server Private Key (preferred: use env var, not this file):
```properties
# Only if NOT using OCI Vault + Instance Principal
com.oracle.apm.agent.private.data.key=${OCI_APM_PRIVATE_KEY}
```

### JVM startup injection
```bash
# Tomcat (setenv.sh)
export JAVA_OPTS="-javaagent:/opt/oracle/apmagent/lib/system/bootstrap-tomcat.jar $JAVA_OPTS"

# Generic JAR
java -javaagent:/opt/oracle/apmagent/lib/system/bootstrap.jar \
     -Dcom.oracle.apm.agent.service.name=my-service \
     -jar app.jar
```

### Kubernetes — container spec (agent as init container)
```yaml
initContainers:
  - name: apm-agent-init
    image: container-registry.oracle.com/apmagent:latest
    command: ["cp", "-r", "/opt/oracle/apmagent", "/shared/apmagent"]
    volumeMounts:
      - name: agent-volume
        mountPath: /shared/apmagent

containers:
  - name: app
    env:
      - name: OCI_APM_PRIVATE_KEY
        valueFrom:
          secretKeyRef:
            name: apm-secret
            key: private-key
      - name: OCI_APM_UPLOAD_ENDPOINT
        value: "https://xxxxxxxx.apm-agt.us-ashburn-1.oci.oraclecloud.com"
      - name: JAVA_OPTS
        value: "-javaagent:/shared/apmagent/lib/system/bootstrap.jar"
    volumeMounts:
      - name: agent-volume
        mountPath: /shared/apmagent
```

---

## Integration Patterns

### OCI APM ↔ OpenTelemetry (OTLP — no OCI library required)

```bash
# Environment variables for any OTel-instrumented service
export OTEL_EXPORTER_OTLP_ENDPOINT="https://<apm_domain_endpoint>/20200101/observations/public-span"
export OTEL_EXPORTER_OTLP_HEADERS="authorization=dataKey <PRIVATE_DATA_KEY>"
export OTEL_SERVICE_NAME="my-service"
export OTEL_TRACES_EXPORTER="otlp"
```

For Java with OTel SDK:
```java
// No OCI-specific library needed — standard OTel configuration
SdkTracerProvider tracerProvider = SdkTracerProvider.builder()
    .addSpanProcessor(BatchSpanProcessor.builder(
        OtlpHttpSpanExporter.builder()
            .setEndpoint(System.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))
            .addHeader("authorization", "dataKey " + System.getenv("APM_PRIVATE_KEY"))
            .build())
        .build())
    .build();
```

### OCI APM ↔ Browser RUM Agent

```html
<!-- Add to <head> of every HTML page served -->
<!-- Use PUBLIC data key only — never Private key here -->
<script>
  window.apmrum = {
    "serviceName": "my-web-app",
    "webApplication": "MyApp",
    "ociDataUploadEndpoint": "https://<apm_domain_endpoint>",
    "dataKey": "<PUBLIC_DATA_KEY>"
  };
</script>
<script async src="https://<apm_domain_endpoint>/static/jslib/apmrum.min.js"></script>
```
