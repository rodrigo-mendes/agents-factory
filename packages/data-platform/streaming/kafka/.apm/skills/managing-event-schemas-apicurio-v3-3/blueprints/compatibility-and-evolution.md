# Compatibility rules and schema evolution, Apicurio Registry 3.3.4

Back to [SKILL.md](../SKILL.md). Pages read 2026-11-04. Doc base: `https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/`.

## Content model

Source: [glossary](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-concepts-glossary.html).

- Content is organized as groups, artifacts, versions. An artifact is identified by `groupId` + `artifactId`.
- A version is an immutable snapshot with a `globalId`. Identical content shares one `contentId`.
- Version states documented in 3.3.x: `ENABLED`, `DISABLED`, `DEPRECATED` ([glossary](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-concepts-glossary.html), [artifact reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-artifact-reference.html)). The 3.3.4 OpenAPI file, partly read, also lists `DRAFT` and `SUNSET`: teach only the three documented states (medium confidence, M5).

## Artifact types for Kafka

Source: [artifact reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-artifact-reference.html).

| Type | Supported |
|---|---|
| `AVRO` | 1.0 to 1.12 |
| `PROTOBUF` | proto2 and proto3 |
| `JSON` | JSON Schema draft-04, draft-07, 2019-09, 2020-12 |

## Rules

Sources: [rules](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-intro-to-registry-rules.html), [rule reference](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-rule-reference.html).

- Rule types: `VALIDITY`, `COMPATIBILITY`, `INTEGRITY`, at global, group and artifact level. Precedence: artifact over group over global.
- "If no global rules are configured, then no rules are applied." Configure one explicitly.
- Global rule by property (`apicurio.rules.global.compatibility`) or `POST /admin/rules`. Per-artifact rule by `POST /groups/{groupId}/artifacts/{artifactId}/rules` with `ruleType` and `config` (body shape from a partly read OpenAPI file, medium confidence, M4).

```bash
# Representative: dry run before registering (dryRun semantics from the 3.3.4 OpenAPI file, medium confidence, M4)
curl -X POST "$REGISTRY/apis/registry/v3/groups/payments/artifacts?ifExists=FIND_OR_CREATE_VERSION&dryRun=true" \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"artifactId":"orders-value","artifactType":"AVRO",
       "firstVersion":{"content":{"content":"<escaped .avsc>","contentType":"application/json"}}}'
```

`ifExists` values `FAIL` (default), `CREATE_VERSION`, `FIND_OR_CREATE_VERSION` also come from that file (medium confidence, M4).

## Compatibility modes

Source: [compatibility modes](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-compatibility-modes.html).

| Mode | Checks against |
|---|---|
| `BACKWARD` | The latest version only |
| `BACKWARD_TRANSITIVE` | Every prior version |
| `FULL`, `FULL_TRANSITIVE` | Both directions; `FULL_TRANSITIVE` is the strictest mode |
| `NONE` | No check; the best-practices page says avoid it in production (medium confidence, M1) |

Which side (producer or consumer) must upgrade first for each mode is not stated (unverified, U1). Do not assert an order. Choosing the level is an Ask First item ([ask-first-decisions](./ask-first-decisions.md)).

## Evolution practices

Sources: [compatibility modes](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-registry-compatibility-modes.html), [best practices](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-schema-lifecycle-best-practices.html).

- Avro: add new fields with defaults. For optional fields use `["null", "type"]` with `default: null`. Adding a field without a default is not backward compatible.
- Protobuf: when removing a field add `reserved` for its number and name. Removing it without reserving is incompatible.
- Compatibility gate in CI: register through `io.apicurio:apicurio-registry-maven-plugin` (goal `register`). A failed build signals a violation (medium confidence, M2). The plugin XML was not read (unverified, U15).

```avro
{"name": "discountCode", "type": ["null", "string"], "default": null}
```

```protobuf
message Order { reserved 2; reserved "coupon"; string id = 1; int64 total = 3; }
```

## Registering through the REST API

Source: [managing artifacts](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-managing-registry-artifacts-api.html) plus the partly read 3.3.4 OpenAPI file (medium confidence, M4). Use the `curl` form in the Rules section above without `dryRun` once the dry run passes.
