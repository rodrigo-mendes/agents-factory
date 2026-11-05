# Compatibility rules and schema evolution, Confluent Schema Registry 8.4.0

Back to [SKILL.md](../SKILL.md). Provenance: official pages read 2026-11-04. Main sources: [schema evolution](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/schema-evolution.html), [config](https://docs.confluent.io/platform/8.4/schema-registry/installation/config.html), [API](https://docs.confluent.io/platform/8.4/schema-registry/develop/api.html).

## Concepts

- A **subject** is "a named scope for schema evolution". A **version** is "a position within a subject's sequence".
- Each registered schema gets a globally unique ID: "monotonically increasing and unique, but not necessarily consecutive". Identical schema definitions share one ID across subjects. IDs are allocated on the primary node ([fundamentals](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/index.html)).
- The default compatibility is `BACKWARD`, not `BACKWARD_TRANSITIVE`. BACKWARD checks only against the previous version (X-1).
- Supported formats: Avro, Protobuf, JSON Schema.

## Compatibility types

| Type | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| BACKWARD (default) | Consumers can rewind to the start of the topic | Checks only X-1 | Two readable versions are enough |
| BACKWARD_TRANSITIVE | Every old version stays readable | Stricter evolution | Protobuf, long retention |
| FORWARD, FORWARD_TRANSITIVE | Producers upgrade first | Harder to use. Protobuf cannot add message types | Old data is no longer consumed |
| FULL, FULL_TRANSITIVE | Producers and consumers upgrade independently | Fewest allowed changes | Independent release trains |
| NONE | No checks | No safety | Avoid. For breaking changes use a new topic (medium confidence, M14) |

Upgrade order: under BACKWARD or BACKWARD_TRANSITIVE upgrade consumers before producers write the new schema, under FORWARD producers first (medium confidence, M2).

Kafka Streams: the schema evolution page says Streams supports "only BACKWARD" and also lists FULL, FULL_TRANSITIVE and BACKWARD_TRANSITIVE. The wording is internally inconsistent (unverified, U3). Not resolved here: ask which type the Streams team uses.

## The `LOGICAL` policy (new in 8.4)

8.4 adds Logical Types (SQL types translated to Avro, Protobuf or JSON Schema) and a `LOGICAL` compatibility policy that "conflicts with the `FORWARD` and `FORWARD_TRANSITIVE` compatibility types" ([release notes](https://docs.confluent.io/platform/current/release-notes/index.html), a page not versioned to 8.4, medium confidence, M19). Handling: see the `LOGICAL` row in [ask-first-decisions](./ask-first-decisions.md#single-source-anti-patterns). The request body that sets the policy is (unverified), U10.

## Check compatibility in CI

```bash
# Representative, Schema Registry 8.4.0
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" -u "$SR_USER:$SR_PASSWORD" \
  --data @candidate.json \
  "https://schema-registry:8081/compatibility/subjects/orders-value/versions/latest?verbose=true"
# Expected: {"is_compatible": true}
```

The Maven plugin has the goals `download`, `set-compatibility`, `test-local-compatibility`, `test-compatibility`, `validate`, `register`, `derive-schema` ([Maven plugin](https://docs.confluent.io/platform/8.4/schema-registry/develop/maven-plugin.html)). Run `test-compatibility` in CI and `register` in CD. XML element names beyond `schemaRegistryUrls`, `subjects`, `schemaTypes` and `references` are (unverified), U19.

## Register and set mode (REST)

Content type `application/vnd.schemaregistry.v1+json`. `schemaType` defaults to AVRO when omitted.

```bash
# Representative
curl -s -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" -u "$SR_USER:$SR_PASSWORD" \
  --data '{"schemaType":"AVRO","schema":"{\"type\":\"record\",\"name\":\"Order\",\"namespace\":\"com.acme\",\"fields\":[{\"name\":\"id\",\"type\":\"string\"}]}"}' \
  "https://schema-registry:8081/subjects/orders-value/versions?normalize=true"
# Expected: {"id":<n>, ...}   (response shape beyond id is (unverified), U7)
```

`PUT /mode` accepts IMPORT, READONLY, READWRITE (default) or FORWARD and works only when the server runs with `mode.mutability=true`. A switch to IMPORT is refused when schemas exist unless `?force=true`. Whether `mode.mutability` defaults to off is (unverified), U11.

## Format notes

- **Avro**: nullable field is a union with `"null"` first and `"default": null`. Specific classes need `specific.avro.reader=true` (default false) (medium confidence, M13). Bundled Avro is pinned to 1.12.1 (medium confidence, M17).
- **Protobuf**: referenced schemas are auto-registered recursively. Null on a field causes NPE, use optional or wrapper types (medium confidence, M15). Google Protobuf v4 is not supported. Do not upload Google or Protobuf dependencies to Schema Registry ([Protobuf serdes](https://docs.confluent.io/platform/8.4/schema-registry/fundamentals/serdes-develop/serdes-protobuf.html)).
- **JSON Schema**: drafts 04, 06, 07 and 2020-12, `json.schema.spec.version` default `draft_7`, `json.fail.invalid.schema` default false. The open or closed content model (`additionalProperties`) changes which evolutions are allowed (medium confidence, M13).

## Deleting schemas

Soft delete keeps the schema and its ID. Hard delete removes all metadata including IDs and needs a prior soft delete ([deletion guidelines](https://docs.confluent.io/platform/8.4/schema-registry/schema-deletion-guidelines.html)). See N2 in [never-do-patterns](./never-do-patterns.md).

## 8.4.0 behavior changes worth testing

From the 8.4.0 changelog (medium confidence, M17): "Pin Avro to 1.12.1", "Block registration of subjects with the name *", "Return 403 instead of 5xx for permission errors", "Reject if/then/else and not schemas" (JSON Schema), "Gate JSON single-member oneOf collapse by version", "Skip schema normalization in IMPORT mode". Impact on existing JSON Schemas with `if/then/else` or `not` is (unverified), U16.
