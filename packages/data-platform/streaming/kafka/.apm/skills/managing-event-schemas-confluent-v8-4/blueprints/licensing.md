# Licensing, Confluent Schema Registry 8.4.0

Back to [SKILL.md](../SKILL.md). Official pages read 2026-11-04. This license split is held at (medium confidence, M16). The table and quoted wording below rest on M16 and quote the page they rest on. This is not legal advice.

## Summary

| Component | License | Source |
|---|---|---|
| Server project | Confluent Community License Agreement Version 1.0 | [README at v8.4.0](https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/README.md), [LICENSE-ConfluentCommunity](https://raw.githubusercontent.com/confluentinc/schema-registry/v8.4.0/LICENSE-ConfluentCommunity), [license page](https://docs.confluent.io/platform/8.4/installation/license.html) |
| Listed client, serde and tooling modules | Apache 2.0 | README at v8.4.0, [license page](https://docs.confluent.io/platform/8.4/installation/license.html) |
| RBAC through the Security Plugins | Confluent Enterprise license | [license page](https://docs.confluent.io/platform/8.4/installation/license.html) |
| Schema Linking | Confluent Enterprise license | license page, [Schema Linking](https://docs.confluent.io/platform/8.4/schema-registry/schema-linking-cp.html) (read in part) |
| Broker-side Schema ID Validation on Confluent Server | Enterprise license | [overview](https://docs.confluent.io/platform/8.4/schema-registry/index.html) (read in part) |
| `cp-schema-registry` Docker image | not stated on the pages read (unverified, I2) | page not recorded |

(medium confidence, M16 for all rows except the image row.)

## Exact wording

- README at tag v8.4.0: "The project is licensed under the Confluent Community License, except for the modules listed below, which are under the Apache 2.0 license". The README tells readers to see the LICENSE file in each subfolder.
- Apache 2.0 modules listed in the README: all `avro-*` modules; `schema-serializer`, `json-serializer`, `protobuf-serializer`, `json-schema-serializer`, `protobuf-serde`, `json-schema-serde`; all `client-*` and `client-encryption-*` modules; `schema-types`, `schema-rules`, `schema-converter`; `protobuf-types`; `dek-registry-client`; `maven-plugin`.
- Community License Agreement 1.0 grants a "non-exclusive, royalty-free, worldwide, non-transferable, non-sublicenseable license" to use, modify and distribute.
- It forbids exercising the license for an **Excluded Purpose**: "making available any software-as-a-service, platform-as-a-service, infrastructure-as-a-service or other similar online service that competes with Confluent products or services that provide the Software."
- Distribution conditions: modified files carry prominent notices, copyright notices are kept.
- License page: "The basic Schema Registry functionality is covered by the Community License and is free to use without a commercial license key." and "a license is required when using role-based access control (RBAC) by means of the Schema Registry Security Plugins". Schema Linking is listed under the Enterprise license.
- Overview page: "Schema Registry is licensed under the Confluent Community License." An Enterprise license is required for the Security Plugin, broker-side Schema ID Validation on Confluent Server, and Schema Linking.
- Security page: "The Schema Registry security plugins require a Confluent Enterprise license" ([security](https://docs.confluent.io/platform/8.4/schema-registry/security/index.html)).
- Schema Linking page extract: "Confluent Community editions don't support Schema Linking".

## Practical reading (inferred, not legal advice)

Running Schema Registry yourself for your own Kafka workloads is within the grant. Offering Schema Registry as a hosted service that competes with Confluent is the Excluded Purpose. Java serdes in your applications are Apache 2.0. A user planning a competing service must read the license text and ask a lawyer. (unverified, U23)

## Behavior rules for the agent

- Never assume RBAC, ACL authorizers or Schema Linking work without an Enterprise license (medium confidence, M16). State the license fact, then offer HTTPS plus Basic or mTLS and network and Kafka-ACL controls.
- Licensing of schema contexts used without Schema Linking is (unverified), U13.
- Do not state a license for the Docker image (unverified, I2).
- Confluent for Kubernetes licensing belongs to `operating-kafka-confluent-kubernetes-v3-4`, not here.
