# Evaluation Scenarios — design-oci-architecture

## Scenario 1: Canonical — Full-Stack Architecture Design

```json
{
  "skills": ["design-oci-architecture"],
  "query": "We are building a new serverless capability: a REST API for managing store data that authenticates users via OCI IAM Identity Domains and needs to store results in Object Storage. Design the full stack. Capability slug: store-data-api. Environments: dev and prod. Consumers: internal web app.",
  "expected_behavior": [
    "Routes to @oci-serverless-architect and triggers the full P0-P6 workflow",
    "Identifies scope as 'full-stack': Functions + API Gateway + IAM + Networking",
    "Presents architecture overview: API Gateway (public subnet) → Function (private subnet) → Object Storage (via Service Gateway)",
    "Specifies IAM: Dynamic Group for Functions with Resource Principal, policy for fn-invocation, and FaaS virtual-network-family",
    "Recommends JWT auth at API Gateway using IAM Identity Domain JWKS endpoint",
    "Recommends rate limiting per route (CLIENT_IP) and CORS with explicit origins",
    "Does NOT generate .tf or .java files — produces ADRs and handoff work-orders"
  ]
}
```

## Scenario 2: Edge — Security Model Review of an Existing Architecture

```json
{
  "skills": ["design-oci-architecture"],
  "query": "Review the security model of our existing OCI serverless architecture. Functions config has DB_PASSWORD as a plaintext environment variable. Capability slug: orders-api. Environment: prod. Consumers: internal web app.",
  "expected_behavior": [
    "Routes to @oci-serverless-architect and triggers P1 (Analyze) scan of .tf files and func.yaml",
    "Identifies the plaintext DB_PASSWORD as a critical Never-Do pattern: credentials visible in OCI Console and Terraform state",
    "Recommends replacing DB_PASSWORD with DB_SECRET_OCID pointing to an OCI Vault secret",
    "Specifies the required IAM policy: 'Allow dynamic-group <fn-dg> to read secret-bundles in compartment <name>'",
    "Recommends the function reads the secret at runtime using ResourcePrincipalAuthenticationDetailsProvider",
    "Produces a remediation ADR documenting the before/after design decision",
    "Does NOT refactor the Java or Terraform code itself — writes work-orders with `status: pending` and `to:` set to \"@oci-functions-java\" (stream-a) and \"@oci-terraform\" (stream-b/c)"
  ]
}
```

## Scenario 3: Edge — API Surface Design for Multi-Function Gateway

```json
{
  "skills": ["design-oci-architecture"],
  "query": "We have three Functions: one for store data, one for item data, and one for webhooks. How should we structure the API Gateway routes and deployments? Capability slug: store-gateway. Environments: dev and prod. Consumers: internal web app and an external webhook sender.",
  "expected_behavior": [
    "Routes to @oci-serverless-architect with scope 'api-surface'",
    "Recommends a single API Gateway with a single deployment grouping all three routes under a shared path prefix (e.g., /v1/)",
    "Maps each Function to its own ORACLE_FUNCTIONS_BACKEND route: /v1/stores, /v1/items, /v1/webhooks",
    "Applies JWT authentication at the Deployment level (not per-route) for the store and item routes",
    "Recommends ANONYMOUS auth for the webhook route with signature-based validation inside the Function",
    "Notes that rate limiting must be configured per route",
    "Asks a numbered question only if something is genuinely missing; does not invent a second-deployment requirement"
  ]
}
```

## Scenario 4: Misuse — Requesting Code Generation

```json
{
  "skills": ["design-oci-architecture"],
  "query": "Design the architecture and also write the Terraform for the VCN, subnets, and API Gateway. Capability slug: edge-network-api. Environments: dev and prod. Consumers: internal web app.",
  "expected_behavior": [
    "Produces the architecture design, ADRs, and component diagrams for VCN + API Gateway",
    "Generates the Terraform work-order (stream-b-terraform-infra.md) under docs/handoff/<capability>/ specifying the resources to create, with `to: \"@oci-terraform\"` and `status: pending`",
    "Does NOT write the actual .tf files directly — delegation is expressed only through the work-order `to:` field",
    "Closes with ONE path: `/provision-oci-serverless-stack edge-network-api` OR `/develop-java-function` + `/provision-oci-infra`, never both"
  ]
}
```

## Scenario 5: Edge — Incomplete Request Returns NEEDS-INPUT

```json
{
  "skills": ["design-oci-architecture"],
  "query": "Design the architecture for our new serverless API.",
  "expected_behavior": [
    "Routes to @oci-serverless-architect and classifies the domain at P0, but finds scope, consumers, environment and capability slug missing",
    "Returns a numbered list of questions (e.g. who consumes the API, which identity provider, latency SLA, environments) instead of assuming answers",
    "Does NOT wait for interactive feedback; ends with 'Status: NEEDS-INPUT' in the Questions / Limitations section",
    "Writes no files — no docs/handoff/ work-orders are created",
    "States no OCI facts of its own while asking"
  ]
}
```

## Scenario 6: Routing — Object Storage Request Loads designing-oci-object-storage

```json
{
  "skills": ["design-oci-architecture", "designing-oci-object-storage"],
  "query": "We will keep partner report PDFs in a bucket and share them with an external partner for a week. Versioning is on. Design the storage and access.",
  "expected_behavior": [
    "Classifies the request as the Object Storage domain at P0 and loads designing-oci-object-storage by name as the primary skill",
    "Resolves the access-pattern and data-protection Ask First items as '[Decision] ... → Recommendation ...' blocks citing the skill",
    "Applies the family anti-pattern checks for Pre-Authenticated Requests (OCI-R82), versioned bucket without lifecycle (OCI-R83) and public buckets (OCI-R85)",
    "Does NOT copy the skill body into the answer and does NOT generate .tf files",
    "Verification checklist lists the commands from the skill's Verification Loop"
  ]
}
```

## Scenario 7: Routing — Pub/Sub Request Loads designing-oci-event-driven-pubsub

```json
{
  "skills": ["design-oci-architecture", "designing-oci-event-driven-pubsub"],
  "query": "An order-created event must fan out to a notification consumer and an audit consumer using Streaming and Service Connector Hub. Review our design where the stream pool uses a private endpoint.",
  "expected_behavior": [
    "Classifies the request as the event-driven pub/sub domain and loads designing-oci-event-driven-pubsub by name",
    "Flags the private-endpoint-only stream pool with SCH as source as a CRITICAL fail citing OCI-R89, with the immutable-pool consequence taken from the skill",
    "Recommends one Service Connector per consumer (OCI-R62 / OCI-R90) and checks the SCH cold-start ceiling (OCI-R72) and the fn-function verb (OCI-R92)",
    "Orders recommendations CRITICAL → HIGH → MEDIUM → LOW, each naming the governing skill",
    "Does NOT generate .tf or .java code"
  ]
}
```

## Scenario 8: Edge — Unverified Item Surfaced in Questions / Limitations

```json
{
  "skills": ["design-oci-architecture"],
  "query": "Review our API Gateway + Vault design: one public gateway, JWT auth, functions in a private subnet reading one Vault secret. Environment: prod. Consumers: internal web app. Capability slug: orders-api.",
  "expected_behavior": [
    "The final Questions / Limitations section states explicitly that no (unverified) or (medium confidence) items were found in the loaded skills (none are tagged in designing-oci-api-gateway or designing-oci-vault-security)",
    "Does NOT invent (unverified) / (medium confidence) tags and does not attribute such tags to any skill",
    "Does not state OCI facts from its own memory; every fact cites a loaded skill",
    "Ends the response with 'Status: COMPLETE' or 'Status: NEEDS-INPUT'"
  ]
}
```

## Scenario 9: Handoff — Commands and Write Scope

```json
{
  "skills": ["design-oci-architecture"],
  "query": "The design for capability func-orders is final: one public API Gateway with JWT auth, one Java function func-orders in a private subnet (256 MB, 60 s), reading a Vault secret via Resource Principal, in dev and prod, consumed by an internal web app. Produce the handoff for the Terraform infrastructure and the Java function.",
  "expected_behavior": [
    "Writes work-orders ONLY under docs/handoff/func-orders/ (stream-a-java.md, stream-b-terraform-infra.md, stream-c-terraform-integration.md); never to the docs/handoff/ root or any other directory",
    "Work-orders follow the coordinating-oci-handoffs template: status: pending, createdAt: <pending>, no 'command:' frontmatter field; states that user approval is needed before running any command",
    "Frontmatter 'to' is \"@oci-functions-java\" for stream-a and \"@oci-terraform\" for streams b and c; dependsOn is none for streams a and b and [stream-a, stream-b] for stream-c",
    "Closes with ONE path: /provision-oci-serverless-stack func-orders, or per stream /develop-java-function (stream A) + /provision-oci-infra (streams B/C); explicitly says never to run both",
    "Does NOT reference removed commands /add-functions-infra or /add-oci-function",
    "Does NOT write .tf or .java files"
  ]
}
```

## Scenario 10: Edge — Only the Capability Slug Is Missing

```json
{
  "skills": ["design-oci-architecture"],
  "query": "Design a REST API on one public API Gateway with JWT auth and one Java function in a private subnet reading a Vault secret via Resource Principal. Environments: dev and prod. Consumers: internal web app. Latency SLA: P99 under 1 s.",
  "expected_behavior": [
    "All other context is present, so delivers the FULL design (P0-P5): architecture overview, review by area, ADRs, roadmap and verification checklist",
    "Skips P6: writes no files and creates no docs/handoff/ work-orders",
    "Does NOT stop at the first question: the missing slug does not suppress the design",
    "Ends with exactly one numbered question asking for the capability slug (kebab-case)",
    "Ends the response with 'Status: NEEDS-INPUT'"
  ]
}
```
