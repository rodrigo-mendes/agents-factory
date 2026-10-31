# Evaluation Scenarios: integrating-quarkus-amazon-data-v3-40

Six scenarios, covering the four required types. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (HTTP client choice with conflicting sources)](#scenario-2-edge-case-http-client-choice-with-conflicting-sources)
- [Scenario 3: Misuse Rejection (out-of-scope request)](#scenario-3-misuse-rejection-out-of-scope-request)
- [Scenario 4: Anti-Pattern Trap (static keys and localhost endpoint)](#scenario-4-anti-pattern-trap-static-keys-and-localhost-endpoint)
- [Scenario 5: Anti-Pattern Trap (tenant from path, Scan, long presigned URL)](#scenario-5-anti-pattern-trap-tenant-from-path-scan-long-presigned-url)
- [Scenario 6: Edge Case (decisions the pages do not settle)](#scenario-6-edge-case-decisions-the-pages-do-not-settle)

---

## Scenario 1: Canonical Path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-dynamodb-enhanced-and-s3
skills: ["integrating-quarkus-amazon-data-v3-40"]
query: "Add DynamoDB (enhanced client) and S3 to my Quarkus 3.40 Lambda: list a tenant's documents and read an S3 object."
must_pass:
  - "Imports io.quarkiverse.amazonservices:quarkus-amazon-services-bom:3.23.0 and declares quarkus-amazon-dynamodb, quarkus-amazon-dynamodb-enhanced and quarkus-amazon-s3 without versions"
  - "Says the HTTP client artifacts are optional and one matching *-client.type (default url, async default netty) must be added; asks which client before fixing it"
  - "Keeps aws.credentials.type=default and injects the clients through CDI instead of building them per call"
  - "Wraps S3Client.getObject in try-with-resources and uses the enhanced PageIterable (or a paginator) for the query"
  - "States that 3.23.0 is built on Quarkus 3.40.0 (High) and that the 3.40.1.1 pairing is (medium confidence)"
must_not:
  - "Pins a Quarkiverse 4.0.0.Beta* version"
  - "Chooses the HTTP client without asking"
  - "Writes Terraform, SAM or CDK"
```

---

## Scenario 2: Edge Case (HTTP client choice with conflicting sources)

**Type**: Two official sources that point in different directions

```yaml
id: 2
name: edge-http-client-crt-vs-url
skills: ["integrating-quarkus-amazon-data-v3-40"]
query: "AWS says to use the CRT HTTP client for Lambda, Quarkiverse defaults to url. Which one do I put in my native Quarkus Lambda?"
must_pass:
  - "Cites both sources: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/lambda-optimize-starttime.html and https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/common-features.html"
  - "Quotes that the CRT native library 'must be embedded in the docker image. This is not done by default.'"
  - "Says how to embed the CRT library in a native function.zip is (unverified) and asks whether to accept that work or stay on url"
  - "Treats the choice as Ask First tied to the JVM + SnapStart vs native ADR"
must_not:
  - "Declares one client the fastest for Quarkus Lambda"
  - "Invents a CRT packaging recipe"
```

---

## Scenario 3: Misuse Rejection (out-of-scope request)

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-sqs-terraform-quarkus-4
skills: ["integrating-quarkus-amazon-data-v3-40"]
query: "Wire SQS and SNS clients, write the Terraform for the DynamoDB table and the IAM policy, and use Quarkiverse 4.0.0.Beta3 with Quarkus 4."
must_pass:
  - "Declines SQS and SNS and points to integrating-quarkus-amazon-messaging-v3-40 by name"
  - "Points the table and bucket IaC to provisioning-aws-dynamodb-v6 and provisioning-aws-s3-v6, and IAM design to securing-aws-iam-serverless"
  - "Says the skill is locked to Quarkiverse 3.23.0 on Quarkus 3.40 and rejects 4.0.0.Beta* and Quarkus 4"
must_not:
  - "Produces SQS or SNS client configuration"
  - "Writes Terraform as part of this skill"
  - "Presents 4.0.0.Beta* content as valid"
```

---

## Scenario 4: Anti-Pattern Trap (static keys and localhost endpoint)

**Type**: Configuration review

```yaml
id: 4
name: trap-static-credentials-and-endpoint-override
skills: ["integrating-quarkus-amazon-data-v3-40"]
query: "My application.properties has quarkus.s3.aws.credentials.type=static with AKIA keys and quarkus.s3.endpoint-override=http://localhost:4566 so tests work. The function will use SnapStart. Is that fine?"
must_pass:
  - "Rejects static keys in a Lambda and gives credentials.type=default (execution role)"
  - "Rejects the global endpoint-override: it disables Dev Services and sends deployed traffic to localhost; says to leave it unset"
  - "Notes that access-key environment variables are not available to the SDK on SnapStart activation (AWS), so the default chain is required"
  - "If the `env-variable` credentials mapping is discussed, it is presented as an inference (medium confidence)"
must_not:
  - "Accepts static keys 'just for tests' in the packaged configuration"
  - "Recommends an alternative that is not High (family rule 9)"
```

---

## Scenario 5: Anti-Pattern Trap (tenant from path, Scan, long presigned URL)

**Type**: Code review of tenant isolation and presigning

```yaml
id: 5
name: trap-tenant-path-scan-and-7-day-url
skills: ["integrating-quarkus-amazon-data-v3-40"]
query: "Review: tenantId comes from the path parameter, I scan the table and filter by tenant, and I presign S3 uploads for 7 days from the Lambda role."
must_pass:
  - "Flags the tenant taken from the path and requires the tenant from the verified token (family rule 6)"
  - "Replaces the Scan with a Query on the tenant partition key; says Scan 'returns all items regardless of the leading keys' and must not be in a LeadingKeys policy"
  - "Says a role-signed URL expires when the role session expires, so 7 days is not honoured; recommends a short duration such as 10 minutes and says the real session lifetime is (unverified)"
  - "Tags the tenant-id-as-LeadingKeys application and the whitepaper statements as (medium confidence) and says per-request tenant-scoped clients are (unverified)"
must_not:
  - "Accepts the path-derived tenant"
  - "Gives a number for the Lambda role-session lifetime"
```

---

## Scenario 6: Edge Case (decisions the pages do not settle)

**Type**: Ambiguous or unverified territory

```yaml
id: 6
name: edge-region-presigner-devservices-sharing
skills: ["integrating-quarkus-amazon-data-v3-40"]
query: "Will quarkus.s3.aws.region pick up AWS_REGION in Lambda? Can I @Inject S3Presigner? Are Dev Services containers shared in tests?"
must_pass:
  - "Says the Quarkiverse region list omits AWS_REGION while the SDK chain includes it, and that whether 3.23.0 delegates is not stated (medium confidence, single tag); offers an explicit region or a deploy-time smoke test"
  - "Says the 3.23.x S3 page never mentions the presigner, the source shows presigner wiring, so injection is (medium confidence); offers building one S3Presigner as the documented option after asking"
  - "Cites both statements on sharing from the dev-services page ('Sharing is disabled by default in dev mode' vs table default shared=true) and asserts neither (unverified)"
must_not:
  - "Asserts AWS_REGION is picked up"
  - "Asserts @Inject S3Presigner works without a test"
  - "Picks one sharing statement silently"
```
