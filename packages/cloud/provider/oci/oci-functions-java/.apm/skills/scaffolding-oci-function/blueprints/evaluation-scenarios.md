# Evaluation Scenarios — scaffolding-oci-function

## Scenario 1: Canonical — new API Gateway function with OCI SDK

```json
{
  "skills": ["scaffolding-oci-function"],
  "query": "Create a new OCI function called func-order-processor in the services/ directory. It will be called from API Gateway, needs to read from Object Storage, and should use Vault for a DB connection string.",
  "expected_behavior": [
    "Reads FDK/SDK versions from an existing services/*/pom.xml before generating",
    "Selects APIGatewayFunction as the handler base class",
    "Includes oci-java-sdk-objectstorage AND oci-java-sdk-common-httpclient-jersey in pom.xml",
    "Adds OciSecretService or Vault config key for the DB connection string",
    "Implements the initError pattern: try-catch in configure(), check first in handler()",
    "Sets timeout to 60s in func.yaml",
    "Generates CMD in Dockerfile matching func.yaml cmd: field",
    "Does NOT hardcode FDK/SDK version numbers without reading from existing pom.xml"
  ]
}
```

## Scenario 2: Edge — ConnectorHub handler pattern

```json
{
  "skills": ["scaffolding-oci-function"],
  "query": "Scaffold a function for Service Connector Hub that will receive log records and forward them to an external SIEM. No API Gateway involved.",
  "expected_behavior": [
    "Selects ConnectorHubFunction as the base class (void handler)",
    "Does NOT use APIGatewayFunction or APIGatewayResponseEvent",
    "Explains that ConnectorHub handler is void — no response model needed",
    "Still implements initError pattern in configure()",
    "Still includes httpclient-jersey if external HTTP calls are made (to the SIEM)",
    "Sets appropriate timeout for external HTTP call latency",
    "Does NOT add APIGatewayTestFeature in the test template"
  ]
}
```

## Scenario 3: Edge — scaffold parameter collection (no uses-vault, no OCI SDK)

```json
{
  "skills": ["scaffolding-oci-function"],
  "query": "I need a simple function that transforms a JSON payload and calls an external REST API. No OCI services needed, no secrets.",
  "expected_behavior": [
    "Omits all oci-java-sdk-* dependencies from pom.xml",
    "Omits oci-java-sdk-common-httpclient-jersey (not needed without SDK)",
    "Includes a lightweight HTTP client (e.g., java.net.http.HttpClient or Jersey Client) for the external REST call",
    "Still implements initError pattern for the HTTP client initialization",
    "Still includes elapsed_ms in the response model",
    "Sets timeout to 60s (external HTTP call may be slow)",
    "Does NOT add OCI SDK dependencies 'just in case'"
  ]
}
```

## Scenario 4: Misuse — omitting CMD from Dockerfile

```json
{
  "skills": ["scaffolding-oci-function"],
  "query": "I copied a Dockerfile from an older project that uses ENTRYPOINT instead of CMD. Can I use ENTRYPOINT?",
  "expected_behavior": [
    "Explains that OCI Functions (Fn Project) requires CMD to pass the handler class reference",
    "States that ENTRYPOINT without CMD or with wrong format causes 502 on every invocation",
    "Shows the correct CMD format: CMD [\"<groupId>.<package>.<Class>Function::handler\"] (groupId asked from the user, e.g. com.example.functions)",
    "Notes that cmd: in func.yaml must match the CMD value exactly",
    "Does NOT suggest ENTRYPOINT as a valid alternative"
  ]
}
```

## Scenario 5: Misuse — putting credentials in func.yaml config

```json
{
  "skills": ["scaffolding-oci-function"],
  "query": "I want to put the database password directly in func.yaml config so the function can read it via ctx.getConfigurationByKey(). Is that safe?",
  "expected_behavior": [
    "States that func.yaml is checked into version control and stored in OCI state — never a safe place for credentials",
    "Explains that config values in func.yaml appear in OCI Console, Terraform state, and CI logs",
    "Provides two correct alternatives: Vault secret injection via OciSecretService, or Terraform-injected OCID reference",
    "Shows the correct func.yaml pattern: config key holds the Vault secret OCID, not the secret value",
    "Does NOT suggest encrypting the value in func.yaml as a workaround"
  ]
}
```
