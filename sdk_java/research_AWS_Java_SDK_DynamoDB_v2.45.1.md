---
Full_Name: AWS SDK for Java 2.x - Amazon DynamoDB
Target_Version: 2.45.1
Release_Date: 2026-05-29
Support_Status: Active
Primary_Docs: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/home.html
Official_Repo: https://github.com/aws/aws-sdk-java-v2
Research_Date: 2026-06-01
Domain_Complexity: Standard
Research_Scope: Standard
---

# Executive Summary

This research defines implementation guardrails for Amazon DynamoDB integrations using AWS SDK for Java 2.x, strictly pinned to version 2.45.1. It covers practical runtime decisions for client selection (standard vs enhanced), data modeling, conditional writes, pagination, consistency, and table/index query strategy.

For Java 2.45.1, the architectural split is: `DynamoDbClient` for low-level and resource-level operations, `DynamoDbEnhancedClient` for type-safe CRUD and table mapping, and enhanced extensions for optimistic locking, counters, and timestamp generation. The document emphasizes deterministic patterns that reduce ambiguity for downstream skill authoring.

Domain complexity is classified as Standard because production DynamoDB usage requires coordinated decisions across schema/access patterns, consistency, condition expressions, batch/transaction semantics, and pagination behavior. This document provides mandatory patterns, conditional tradeoffs, anti-pattern corrections, and verification commands designed for immediate skill transformation.

# Input Validation

- SYSTEM_OR_TECH_NAME: AWS Java SDK DynamoDB (specific, valid)
- TARGET_VERSION: 2.45.1 (specific, valid)
- OFFICIAL_URL_IF_KNOWN: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/home.html
- INTEGRATION_PARTNERS_LIST: IAM/STS, AWS CLI shared config, Lambda streams, CloudWatch (derived from official examples)

# Authority and Versioning

- Primary authority: AWS SDK for Java 2.x Developer Guide and API Reference.
- Version lock: All implementation guidance in this file is for AWS SDK for Java 2.45.1.
- Release pin: aws-sdk-java-v2 release 2.45.1 dated 2026-05-29.
- Version absolutism warning: Do not mix AWS SDK Java 1.x (`com.amazonaws`) and 2.x (`software.amazon.awssdk`) runtime patterns in the same implementation module unless explicitly performing staged migration.

# Architectural Guardrails

### ✅ Mandatory Patterns

Pattern: Pin AWS SDK BOM and DynamoDB modules to 2.45.1
- Why: Prevents dependency drift and service model mismatch.
- Code:
```xml
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>software.amazon.awssdk</groupId>
      <artifactId>bom</artifactId>
      <version>2.45.1</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>

<dependencies>
  <dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>dynamodb</artifactId>
  </dependency>
  <dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>dynamodb-enhanced</artifactId>
  </dependency>
</dependencies>
```
- Source: AWS Java migration guidance and aws-sdk-java-v2 releases.

Pattern: Use `DefaultCredentialsProvider` and explicit region in production services
- Why: Aligns with AWS standardized auth chain and avoids region drift.
- Code:
```java
DynamoDbClient ddb = DynamoDbClient.builder()
    .region(Region.US_EAST_1)
    .credentialsProvider(DefaultCredentialsProvider.create())
    .build();
```
- Source: AWS credentials chain and region selection docs.

Pattern: Reuse long-lived DynamoDB clients and close on shutdown
- Why: Reuses HTTP connections and reduces latency/CPU churn.
- Code:
```java
public final class DynamoClients {
  private static final DynamoDbClient DDB = DynamoDbClient.builder()
      .region(Region.US_EAST_1)
      .build();

  private static final DynamoDbEnhancedClient ENHANCED =
      DynamoDbEnhancedClient.builder().dynamoDbClient(DDB).build();

  public static DynamoDbClient ddb() { return DDB; }
  public static DynamoDbEnhancedClient enhanced() { return ENHANCED; }

  public static void shutdown() {
    DDB.close();
  }
}
```
- Source: AWS enhanced client setup docs.

Pattern: Prefer Enhanced Client for strongly typed table CRUD and mapping
- Why: Reduces low-level attribute map verbosity and improves type safety.
- Code:
```java
@DynamoDbBean
public class Customer {
  private String id;
  private String email;

  @DynamoDbPartitionKey
  public String getId() { return id; }
  public void setId(String id) { this.id = id; }

  public String getEmail() { return email; }
  public void setEmail(String email) { this.email = email; }
}

DynamoDbEnhancedClient enhanced = DynamoDbEnhancedClient.builder()
    .dynamoDbClient(ddb)
    .build();

DynamoDbTable<Customer> customerTable =
    enhanced.table("Customer", TableSchema.fromBean(Customer.class));

customerTable.putItem(customer);
Customer loaded = customerTable.getItem(Key.builder().partitionValue("c-123").build());
```
- Source: Enhanced client basic usage docs.

Pattern: Enforce conditional writes for concurrency-sensitive updates
- Why: Prevents lost updates and stale overwrites in concurrent writers.
- Code:
```java
UpdateItemRequest request = UpdateItemRequest.builder()
    .tableName("Orders")
    .key(Map.of("OrderId", AttributeValue.builder().s(orderId).build()))
    .updateExpression("SET #status = :newStatus")
    .conditionExpression("#status = :expectedStatus")
    .expressionAttributeNames(Map.of("#status", "Status"))
    .expressionAttributeValues(Map.of(
        ":newStatus", AttributeValue.builder().s("PAID").build(),
        ":expectedStatus", AttributeValue.builder().s("PENDING").build()))
    .build();

ddb.updateItem(request);
```
- Source: DynamoDB conditional operation examples.

Pattern: Always paginate `Query` and `Scan` flows
- Why: DynamoDB responses can be partial; missing pages causes silent data loss.
- Code:
```java
Map<String, AttributeValue> lastEvaluatedKey = null;

do {
  QueryRequest.Builder req = QueryRequest.builder()
      .tableName("Events")
      .keyConditionExpression("#pk = :pk")
      .expressionAttributeNames(Map.of("#pk", "TenantId"))
      .expressionAttributeValues(Map.of(":pk", AttributeValue.builder().s("t-1").build()))
      .limit(100);

  if (lastEvaluatedKey != null) {
    req.exclusiveStartKey(lastEvaluatedKey);
  }

  QueryResponse response = ddb.query(req.build());
  response.items().forEach(System.out::println);
  lastEvaluatedKey = response.lastEvaluatedKey();

  if (lastEvaluatedKey != null && lastEvaluatedKey.isEmpty()) {
    lastEvaluatedKey = null;
  }
} while (lastEvaluatedKey != null);
```
- Source: DynamoDB query pagination examples.

### ⚠️ Conditional Patterns

Decision: Standard client vs Enhanced client
- Options: `DynamoDbClient`, `DynamoDbEnhancedClient`, mixed approach.
- Tradeoffs:

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Standard client | Full low-level API and resource operations | Verbose code and lower type safety | Table ops, custom expressions, advanced controls |
| Enhanced client | Typed mapping and cleaner CRUD | Less direct control for some low-level constructs | Domain-driven services and table-centric APIs |
| Mixed | Flexibility | Architectural complexity | Systems using typed CRUD plus advanced low-level updates |

- Agent ask-first prompt: Is this service primarily table CRUD with domain models, or heavy low-level expression/resource operations?
- Source: Enhanced-vs-standard comparison docs.

Decision: Consistency mode for reads
- Options: Eventual (`consistentRead=false`) vs Strong (`consistentRead=true` where supported).
- Tradeoffs:

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Eventual reads | Lower latency/cost in many workloads | May return stale values briefly | Read-heavy user-facing workloads |
| Strong reads | Freshness guarantees | Higher read cost and potential latency | Financial/critical control paths |

- Agent ask-first prompt: Is bounded staleness acceptable, or must reads reflect latest committed write?
- Source: DynamoDB query examples with consistency configuration.

Decision: Access path strategy (Query base table vs Query GSI vs Scan)
- Options: Base table key query, GSI query, filtered scan.
- Tradeoffs:

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Base table query | Efficiency and predictable RCUs | Requires key-compatible access pattern | Primary read path by PK/SK |
| GSI query | Alternate access without full table scan | Index maintenance and design complexity | Secondary lookup patterns |
| Scan + filter | Simplicity for ad hoc ops | High cost/latency at scale | Admin/one-off maintenance jobs |

- Agent ask-first prompt: Do you have a key-compatible access pattern, or do you need a new GSI for this query?
- Source: DynamoDB query/GSI examples.

Decision: Optimistic locking approach
- Options: Enhanced extension (`VersionedRecordExtension`) vs manual condition expressions.
- Tradeoffs:

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| VersionedRecordExtension | Declarative optimistic locking | Requires schema tags and extension wiring | Enhanced-client mapped entities |
| Manual condition expressions | Full control and low-level portability | More boilerplate and human error risk | Standard-client-heavy code paths |

- Agent ask-first prompt: Should optimistic locking be standardized by schema annotation, or explicitly coded per write path?
- Source: Enhanced extensions docs.

### 🚫 Forbidden Patterns

Anti-Pattern: Hardcoded AWS credentials
```java
// DON'T
DynamoDbClient.builder()
  .credentialsProvider(StaticCredentialsProvider.create(
      AwsBasicCredentials.create("AKIA...", "SECRET...")))
  .build();
```
- Why: Credential leakage and rotation failures.
- Instead:
```java
// DO
DynamoDbClient.builder()
  .credentialsProvider(DefaultCredentialsProvider.create())
  .build();
```
- Impact: Security incident risk and compliance violations.
- Source: AWS credentials chain guidance.

Anti-Pattern: Mixing Java SDK v1 and v2 in normal runtime path
```java
// DON'T
import com.amazonaws.services.dynamodbv2.AmazonDynamoDB;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
```
- Why: Inconsistent models and migration ambiguity.
- Instead: Use only `software.amazon.awssdk.*` in v2.45.1 modules.
- Impact: Runtime defects and maintenance complexity.
- Source: Java 1.x to 2.x migration docs.

Anti-Pattern: Missing pagination loop on query/scan
```java
// DON'T
QueryResponse r = ddb.query(req);
return r.items(); // Ignores lastEvaluatedKey
```
- Why: Returns incomplete data silently when response is truncated.
- Instead: Loop until `lastEvaluatedKey` is null.
- Impact: Partial reads, data inconsistency in business logic.
- Source: Query pagination examples.

Anti-Pattern: Using `Scan` for primary user-facing access pattern
```java
// DON'T
ScanRequest request = ScanRequest.builder().tableName("Orders").build();
ddb.scan(request);
```
- Why: Full table traversal scales poorly in cost and latency.
- Instead: Model PK/SK and use `Query`, or add targeted GSI.
- Impact: Cost spikes and unpredictable p95 latency.
- Source: DynamoDB query vs scan guidance in examples.

Anti-Pattern: Unconditional updates where concurrency matters
```java
// DON'T
ddb.updateItem(UpdateItemRequest.builder()
    .tableName("Orders")
    .key(key)
    .updateExpression("SET #status = :s")
    .expressionAttributeNames(Map.of("#status", "Status"))
    .expressionAttributeValues(Map.of(":s", AttributeValue.builder().s("PAID").build()))
    .build());
```
- Why: Last-writer-wins may overwrite valid intermediate state transitions.
- Instead: Add `conditionExpression` or use optimistic locking extension.
- Impact: Lost updates and invalid state transitions.
- Source: Conditional operation and extension docs.

# Migration Guide

## Breaking Changes (v1 to v2, relevant for DynamoDB)

1. Package/groupId changed from `com.amazonaws` to `software.amazon.awssdk`.
2. Request/response models are immutable and built with builders.
3. Method and model naming differs (`*Response` in v2; no v1-style `withX` chain usage pattern).
4. `DynamoDBMapper` high-level workflow maps to v2 Enhanced Client patterns.
5. Credential and region resolution are standardized via 2.x provider chains.

## Upgrade Steps

1. Replace v1 dependencies with v2 BOM and `dynamodb`/`dynamodb-enhanced` pinned to 2.45.1.
2. Migrate imports and model construction to immutable v2 builders.
3. Replace `DynamoDBMapper` entity paths with `DynamoDbEnhancedClient` and `TableSchema`.
4. Add condition expressions or versioned extension for concurrency-sensitive writes.
5. Ensure all query/scan callsites implement pagination loops.
6. Run verification suite in Quality Control section.

## Compatibility Matrix

| Dependency | Min | Max | Notes |
|------------|-----|-----|-------|
| Java runtime | 8+ | Current LTS | AWS SDK Java 2.x baseline is Java 8+ |
| aws-sdk-java-v2 BOM | 2.45.1 | 2.45.1 | Strict pin for version absolutism |
| DynamoDB module | 2.45.1 | 2.45.1 | Match BOM |
| DynamoDB Enhanced module | 2.45.1 | 2.45.1 | Match BOM |

# Implementation Blueprint

## Lifecycle (Init, Use, Cleanup)

```java
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.AttributeValue;
import software.amazon.awssdk.services.dynamodb.model.PutItemRequest;

import java.util.Map;

public final class DynamoApp {
  private final DynamoDbClient ddb;

  public DynamoApp(Region region) {
    this.ddb = DynamoDbClient.builder()
        .region(region)
        .credentialsProvider(DefaultCredentialsProvider.create())
        .build();
  }

  public void putOrder(String tableName, String orderId, String status) {
    PutItemRequest req = PutItemRequest.builder()
        .tableName(tableName)
        .item(Map.of(
            "OrderId", AttributeValue.builder().s(orderId).build(),
            "Status", AttributeValue.builder().s(status).build()))
        .build();

    ddb.putItem(req);
  }

  public void close() {
    ddb.close();
  }
}
```

## Integration Example: Enhanced Client + optimistic locking extension

```java
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbEnhancedClient;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbTable;
import software.amazon.awssdk.enhanced.dynamodb.TableSchema;
import software.amazon.awssdk.enhanced.dynamodb.extensions.VersionedRecordExtension;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbBean;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbPartitionKey;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbVersionAttribute;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;

@DynamoDbBean
class InventoryItem {
  private String id;
  private Integer version;
  private Integer quantity;

  @DynamoDbPartitionKey
  public String getId() { return id; }
  public void setId(String id) { this.id = id; }

  @DynamoDbVersionAttribute
  public Integer getVersion() { return version; }
  public void setVersion(Integer version) { this.version = version; }

  public Integer getQuantity() { return quantity; }
  public void setQuantity(Integer quantity) { this.quantity = quantity; }
}

DynamoDbEnhancedClient enhanced = DynamoDbEnhancedClient.builder()
    .dynamoDbClient(ddb)
    .extensions(VersionedRecordExtension.builder().build())
    .build();

DynamoDbTable<InventoryItem> table =
    enhanced.table("Inventory", TableSchema.fromBean(InventoryItem.class));

InventoryItem item = new InventoryItem();
item.setId("sku-1");
item.setQuantity(10);
table.putItem(item);
```

## Integration Example: Conditional update with expression attribute names

```java
import software.amazon.awssdk.services.dynamodb.model.UpdateItemRequest;

UpdateItemRequest req = UpdateItemRequest.builder()
    .tableName("Inventory")
    .key(Map.of("Id", AttributeValue.builder().s("sku-1").build()))
    .updateExpression("SET #qty = #qty - :decrement")
    .conditionExpression("#qty >= :decrement")
    .expressionAttributeNames(Map.of("#qty", "Quantity"))
    .expressionAttributeValues(Map.of(
        ":decrement", AttributeValue.builder().n("1").build()))
    .build();

ddb.updateItem(req);
```

# Quality Control

## Verification Commands (project-level)

```bash
# 1) Dependency pin check
mvn -q dependency:tree -Dincludes=software.amazon.awssdk:dynamodb,software.amazon.awssdk:dynamodb-enhanced
# Expected: both modules appear at 2.45.1 and align with BOM

# 2) Compile check
mvn -q -DskipTests compile
# Expected: BUILD SUCCESS

# 3) Unit tests
mvn -q test
# Expected: BUILD SUCCESS and no required live AWS network dependency

# 4) Static analysis (if configured)
mvn -q spotbugs:check
# Expected: No high severity findings

# 5) DynamoDB smoke execution (requires configured credentials/table)
AWS_REGION=us-east-1 mvn -q -Dexec.mainClass=com.example.dynamodb.Smoke exec:java
# Expected: put/get/query flow success or explicit IAM/resource error with actionable code
```

## Verification Commands (document self-validation)

```bash
# Ensure three-tier sections exist
grep -E "^### ✅|^### ⚠️|^### 🚫" sdk_java/research_AWS_Java_SDK_DynamoDB_v2.45.1.md
# Expected: all three section headers found

# Ensure version and versioning context appear repeatedly
grep -i "2.45.1\|2.x\|version" sdk_java/research_AWS_Java_SDK_DynamoDB_v2.45.1.md | wc -l
# Expected: >= 5

# Ensure bibliography links exist
grep -E "http" sdk_java/research_AWS_Java_SDK_DynamoDB_v2.45.1.md | head -10
# Expected: non-empty output
```

## Isolation and Mocking

Framework: JUnit 5 + Mockito
- Mocking: mock `DynamoDbClient` or repository wrappers; avoid live AWS in unit tests.
- Example:
```java
@ExtendWith(MockitoExtension.class)
class OrderRepositoryTest {
  @Mock DynamoDbClient ddb;

  @Test
  void putOrder_callsPutItem() {
    OrderRepository repo = new OrderRepository(ddb, "Orders");
    repo.putOrder("o-1", "PENDING");

    verify(ddb, times(1)).putItem(any(PutItemRequest.class));
  }
}
```
- Guarantee: unit tests remain deterministic and offline; integration tests gated by explicit profile.

# Production Readiness

- Performance
  - Design for `Query` first; reserve `Scan` for constrained admin tasks.
  - Use pagination and bounded page sizes.
  - Prefer projection expressions to reduce payload size.

- Scalability
  - Align PK/SK and GSI design with dominant access paths.
  - Use conditional writes and idempotency where duplicate requests are possible.
  - Evaluate batch and transaction APIs for multi-item workflows.

- Monitoring
  - Log request IDs and AWS error codes from `DynamoDbException`.
  - Track latency, throttling exceptions, and retry counts.
  - Monitor query vs scan ratios and consumed capacity patterns.

- Security
  - Prefer IAM roles over static credentials.
  - Enforce least-privilege policies on table/index actions.
  - Validate encryption and access controls at table and application layers.

# Source Bibliography

## Primary Sources

1. AWS SDK for Java v2 GitHub Releases
   - URL: https://github.com/aws/aws-sdk-java-v2/releases
   - Published: 2026-05-29 (release 2.45.1)
   - Accessed: 2026-06-01

2. AWS SDK for Java 2.x Developer Guide (Home)
   - URL: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/home.html
   - Published: Living documentation (no fixed publish timestamp exposed)
   - Accessed: 2026-06-01

3. DynamoDB examples using SDK for Java 2.x
   - URL: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/java_dynamodb_code_examples.html
   - Published: Living documentation (no fixed publish timestamp exposed)
   - Accessed: 2026-06-01

4. Learn the basics of the DynamoDB Enhanced Client API
   - URL: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-use.html
   - Published: Living documentation (no fixed publish timestamp exposed)
   - Accessed: 2026-06-01

5. Use extensions to customize DynamoDB Enhanced Client operations
   - URL: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-extensions.html
   - Published: Living documentation (no fixed publish timestamp exposed)
   - Accessed: 2026-06-01

6. Create an enhanced client and DynamoDbTable
   - URL: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/ddb-en-client-getting-started-dynamodbTable.html
   - Published: Living documentation (no fixed publish timestamp exposed)
   - Accessed: 2026-06-01

7. Default credentials provider chain in AWS SDK for Java 2.x
   - URL: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/credentials-chain.html
   - Published: Living documentation (no fixed publish timestamp exposed)
   - Accessed: 2026-06-01

8. Setting the AWS Region for AWS SDK for Java 2.x
   - URL: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/region-selection.html
   - Published: Living documentation (no fixed publish timestamp exposed)
   - Accessed: 2026-06-01

9. Migration differences between AWS SDK for Java 1.x and 2.x
   - URL: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/migration-whats-different.html
   - Published: Living documentation (no fixed publish timestamp exposed)
   - Accessed: 2026-06-01

## Validation Sources

1. Maven repository listing for `software.amazon.awssdk:dynamodb`
   - URL: https://mvnrepository.com/artifact/software.amazon.awssdk/dynamodb
   - Published: 2026-05-30 entry for 2.45.1
   - Accessed: 2026-06-01

2. Maven repository listing for `software.amazon.awssdk:dynamodb-enhanced`
   - URL: https://mvnrepository.com/artifact/software.amazon.awssdk/dynamodb-enhanced
   - Published: 2026-05-30 entry for 2.45.1
   - Accessed: 2026-06-01

# Agent Operation Notes

- Confidence for skill authoring: High
- Safe to enforce without user confirmation:
  - BOM/module pinning to 2.45.1
  - Default credentials chain and explicit region baseline
  - Query-first/paginated-access baseline
  - Conditional writes for concurrency-sensitive flows

- Ask user before final skill generation if:
  - Service should be Enhanced-client-first or mixed with low-level client
  - Strong consistency is mandatory for critical reads
  - GSI creation is acceptable for required access paths

- Final warning:
  - This research is version-locked to AWS SDK for Java 2.45.1 and Java 2.x patterns. Do not mix with AWS SDK Java 1.x runtime patterns in generated skill behavior.
