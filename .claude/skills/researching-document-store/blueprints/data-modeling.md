# Document Data Modeling

For `DATASTORE_TYPE=document`. Platforms: MongoDB, Couchbase, RavenDB.

---

## Fundamental Rule: Model for Your Access Patterns

Document databases do not support efficient joins. Every relationship must be resolved at schema design time:
- **Embed**: bring related data into the same document → fast reads, no join needed
- **Reference**: store an ID and do a second query → flexibility, but 2+ round trips

---

## Embedding vs Referencing Decision Tree

```
Ask these questions for each relationship:

1. Is the related data ALWAYS accessed with the parent?
   YES → embed (eliminates second query)
   NO  → consider reference (avoid loading unused data)

2. Can the embedded array grow WITHOUT BOUND over time?
   YES → reference (unbounded arrays → 16MB limit violation)
   NO  → embed is safe

3. Are the related entities accessed INDEPENDENTLY (without the parent)?
   YES → reference (they need their own collection)
   NO  → embedding is fine

4. Do updates happen to PARENT and CHILD TOGETHER atomically?
   YES → embed (same document = atomic write)
   NO  → reference + multi-document transaction if strict consistency needed

5. Is there a HIGH RATIO of children per parent (1:many)?
   < 100 children → embed
   100–10,000 children → reference from child to parent ("parent reference" pattern)
   > 10,000 children → always reference; consider separate collection
```

---

## Embedding Patterns

### Basic Embedding

```json
// Order document with embedded line items (always accessed together)
{
  "_id": "order_123",
  "customer_id": "cust_456",
  "status": "shipped",
  "items": [
    { "product_id": "prod_789", "quantity": 2, "price": 29.99 },
    { "product_id": "prod_012", "quantity": 1, "price": 9.99 }
  ],
  "total": 69.97
}
```

### Bucket Pattern (for time-series-like data within a document)

```json
// Instead of one document per sensor reading, bucket by time period
{
  "_id": "sensor_A_2024-01-15",
  "sensor_id": "A",
  "date": "2024-01-15",
  "readings_count": 24,
  "readings": [
    { "hour": 0, "temp": 22.1 },
    { "hour": 1, "temp": 21.8 }
    // ... up to 24 readings
  ]
}
// Benefits: fewer documents; array bounded to 24; efficient date-range queries
```

---

## Referencing Patterns

### Child Reference (store parent ID in child)

```json
// Order references customer by ID; customer exists independently
{
  "_id": "order_123",
  "customer_id": "cust_456",   // reference — requires second query if customer data needed
  "items": [...]
}
```

### Extended Reference Pattern (cache frequently needed parent fields)

```json
// Cache the customer's name to avoid second query for display
{
  "_id": "order_123",
  "customer_id": "cust_456",
  "customer_name": "Rodrigo Mendes",   // cached — acceptable if name doesn't change often
  "items": [...]
}
// Trade-off: stale data if customer name changes; must update in both places
```

---

## Index Design (MongoDB)

### ESR Rule for Compound Indexes

**E**quality → **S**ort → **R**ange — always in this order within a compound index.

```javascript
// Query: db.orders.find({ customer_id: "cust_456", status: "shipped" }).sort({ created_at: -1 })
// ESR index: equality (customer_id, status) → sort (created_at)
db.orders.createIndex({ customer_id: 1, status: 1, created_at: -1 });
```

### Index Types

| Type | When to Use |
|---|---|
| Single field | Simple equality or range on one field |
| Compound | Multi-field queries (apply ESR rule) |
| Multikey | Queries on array field values |
| Text | `$text` operator for full-text search |
| Wildcard | Dynamic schemas with unpredictable field names |
| Partial | Index only documents matching a filter (e.g., only active orders) |
| Geospatial (2dsphere) | Location-based `$near` / `$geoWithin` queries |

### Covered Query (zero document fetch)

A query is "covered" when all fields in the query and projection are in the index — no document heap access.
This is the highest-performance read path for high-frequency queries.

---

## Schema Validation

Enforce schema at the collection level to prevent invalid data:

```javascript
db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["customer_id", "items", "status"],
      properties: {
        customer_id: { bsonType: "string" },
        status: { enum: ["pending", "shipped", "delivered", "cancelled"] },
        items: {
          bsonType: "array",
          minItems: 1,
          items: {
            bsonType: "object",
            required: ["product_id", "quantity"],
            properties: {
              product_id: { bsonType: "string" },
              quantity: { bsonType: "int", minimum: 1 }
            }
          }
        }
      }
    }
  },
  validationAction: "error"  // reject invalid documents; use "warn" during migration
});
```

---

## Schema Versioning for Documents

```json
// Add a _schema_version field to all documents
{
  "_id": "order_123",
  "_schema_version": 2,
  "customer_id": "cust_456",
  // ... v2 fields
}
```

Migration strategy for schema changes:
1. Deploy code that reads both v1 and v2 documents (forward-compatible reader)
2. Backfill existing v1 documents to v2 in background batches
3. After all documents are v2, remove v1 reading code
4. This is the Expand-Contract pattern applied to documents
