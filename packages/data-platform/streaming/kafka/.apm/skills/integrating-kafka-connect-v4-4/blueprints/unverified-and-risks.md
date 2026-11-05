# Unverified and risks register, Kafka Connect 4.4.0

Back to [SKILL.md](../SKILL.md). Provenance: the [Source Bibliography](#source-bibliography) below (official pages, read 2026-11-04). Items U1, U3 and U4 are conflicts or gaps that this skill does not resolve: a human must verify them. Descriptive facts cited to one versioned page carry no tag. Recommendations, prohibitions and anything in Always Do or Never Do need two or more versioned pages; otherwise they sit outside the tiers as (medium confidence) with a row in the Medium confidence table.

## Version-lifetime risk

- Kafka 4.4.0 was released 2026-10-22 (downloads page [S19], read 2026-11-04). 4.4.x patch notes may follow.
- Kafka 5.0.0 makes `Allowlist` the default override policy and removes `Principal` [S9].
- KIP-909 asynchronous bootstrap resolution is not supported by Connect 4.4.0 (as of 2026-11-04) [S9][S10].
- Support policy: the Apache wiki Time Based Release Plan [S20] says rolling upgrades are tested from the last 3 releases, bugfix releases are attempted for the last 3, and a release ships every 4 months (medium confidence, M13). No official per-version end-of-life table exists (unverified, U17).
- The successor release number and date are not recorded in the pages read on 2026-11-04. Re-check the downloads page for any release after 4.4.0 before relying on this skill.

## Unverified (U1..U20): 20 items

| ID | Item | Tag | Note |
|---|---|---|---|
| U1 | Connect from the `apache/kafka:4.4.0` image: entrypoint, `/opt/kafka/bin` path, user, env-var mapping, host-local port binding, whether `apache/kafka-native` has the Connect scripts | (unverified) | Irresolvable from [S11][S12]. Compose is inferred. Human-verify |
| U2 | `connect-internal-topics.sh` syntax (`create --worker-config`) | (medium confidence) | KIP wiki [S17] only. The 4.4 docs name the tool without syntax |
| U3 | `connect.protocol` default: `sessioned` [S5] vs `compatible` [S3] | (medium confidence) | Two official 4.4 pages conflict. Not resolved here. Leave the key unset. Human-verify |
| U4 | Rolling-upgrade procedure for Connect workers, including node order | (unverified) | Not in the 4.4 docs read. Steps in the migration guide are inferred. Human-verify |
| U5 | Value format of `connector.client.config.override.allowlist` (full prefixed key or bare key) | (unverified) | The key has no entry of its own on the configs page |
| U6 | Fully qualified names of `BasicAuthSecurityRestExtension`, `PropertyFileLoginModule`, SMT and predicate classes | (unverified) | Pages list short names only |
| U7 | Effect of `org.apache.kafka.automatic.config.providers` on Connect workers | (unverified) | 4.4.0 notes describe dynamic broker config validation |
| U8 | Config provider references inside worker-level `listeners.https.*` settings | (unverified) | |
| U9 | `resume` of a STOPPED connector via `PUT /connectors/{name}/resume` | (medium confidence) | Implied by the administration page, not stated |
| U10 | FileStreamSink `file` key, `/connector-plugins` class names, REST response field names | (unverified) | |
| U11 | Official SMT or connector test harness | (unverified) | Absence of evidence |
| U12 | Alert thresholds for Connect metrics | (unverified) | Set from your own baseline |
| U13 | Whether `DELETE /connectors/{name}` removes stored offsets | (unverified) | |
| U14 | Listing several bootstrap servers as common practice | (unverified) | Practice, not a rule from the pages |
| U15 | Exact HTTP status when offsets of a running connector are changed | (unverified) | The pages say the connector must be stopped |
| U16 | Active Connect CVEs for 4.4.0 | (unverified) | No CVE search was run |
| U17 | Official per-version end-of-life table | (unverified) | None found. Wiki policy only (M13). Human-verify |
| U18 | Compatibility of Connect 4.4 with 3.9 brokers | (unverified) | Not researched. The compatibility page gives only the client protocol floor (2.1+) |
| U19 | Plain-HTTP REST listener behind a TLS proxy on a trusted Compose network as an exception to the HTTPS rule | (unverified) | Inferred for dev and CI. Human-verify |
| U20 | Multi-worker Compose cluster: same `group.id` and topics on every worker, own `rest.advertised.host.name` per worker | (unverified) | Inferred, no Compose example in the docs read |

## Irresolvable (I1..): 0 items

No separate irresolvable class is kept. Facts that cannot be resolved from documentation are listed once above as U-ids (U1, U3, U4) with a human-verify note.

## Medium confidence (M1..M17): 17 items

| ID | Claim | Tag |
|---|---|---|
| M1 | Client security settings repeated unprefixed, with `producer.` and with `consumer.`; only `bootstrap.servers` is inherited unprefixed ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), one page) | (medium confidence) |
| M2 | Protect the config, offset and status topics with ACLs (security model, one page) | (medium confidence) |
| M3 | Separate admin endpoints with `admin.listeners`, disable them with an empty value (security model, one page) | (medium confidence) |
| M4 | Separate Connect clusters for teams that do not trust each other (security model, one page) | (medium confidence) |
| M5 | Partition the worker principal's ACLs by topic prefix per connector (security model, one page) | (medium confidence) |
| M6 | Standalone workers cannot provide exactly-once; exactly-once source is distributed-only (user guide, one page) | (medium confidence) |
| M7 | ReplaceField `whitelist` and `blacklist` removed in 4.0.0 (upgrade notes, one page) | (medium confidence) |
| M8 | `plugin.path` must not use config provider variables (configs, one page) | (medium confidence) |
| M9 | REST authentication options, `PropertyFileLoginModule` not for production, no per-connector authorization (security model, one page) | (medium confidence) |
| M10 | Converter semantics: independent of connectors, schemaless JSON switch, connector may override (user guide, one page) | (medium confidence) |
| M11 | File provider `allowed.paths` and `allowlist.pattern` (configuration providers, one page) | (medium confidence) |
| M12 | Worker-to-broker TLS, trusted plugins only, empty `access.control.allow.origin` as single-page hardening items | (medium confidence) |
| M13 | Support policy from the Apache wiki Time Based Release Plan, last edited 2024-07-09 [S20] | (medium confidence) |
| M14 | Internal topic shape: config topic one partition, all three compacted ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), one page) | (medium confidence) |
| M15 | Internal topic replication factor 3 and -1 as broker default ([configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/), one page) | (medium confidence) |
| M16 | Unique `group.id` that does not clash with consumer group IDs ([user guide](https://kafka.apache.org/44/kafka-connect/user-guide/), one page) | (medium confidence) |
| M17 | One direct child directory of `plugin.path` per plugin ([configs](https://kafka.apache.org/44/configuration/kafka-connect-configs/), one page) | (medium confidence) |

## Coverage limits (L1..L5): 5 items

| ID | Limit |
|---|---|
| L1 | Every page was read through WebFetch, which returns a summarized page, not verbatim text |
| L2 | The configs page (111092 chars) and the monitoring page (157611 chars) were read in two windows each; the other pages fit in one window |
| L3 | Downloads page (S19) read 100000 of 152730 characters |
| L4 | The KIP-1209 wiki page is an accepted-KIP wiki page edited 2026-07-29, not versioned release docs |
| L5 | The 4.4 docs index was read as navigation only and is not cited |

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) | SKILL.md Version Context, image; Ask First, REST extension, image, rolling upgrade | U1, U4, U6 |
| (unverified) | SKILL.md Version Context, end-of-life table | U17 |
| (medium confidence) | SKILL.md Version Context, support policy | M13 |
| (medium confidence) | SKILL.md Ask First, REST authentication, converters, secured cluster | M9, M10, M1 |
| (medium confidence) | SKILL.md Ask First, internal topic shape and replication, group.id, plugin layout; ask-first-decisions.md same sections | M14, M15, M16, M17 |
| (medium confidence) | never-do-patterns.md, replication factor 3 in the alternative | M15 |
| (medium confidence) | SKILL.md Ask First and Quick Reference, `connect.protocol` | U3 |
| (medium confidence) | always-do-patterns.md, internal topic tool syntax | U2 |
| (unverified) | always-do-patterns.md, listeners.https providers, allowlist format | U8, U5 |
| (unverified) | deploy-compose.md, plain-HTTP listener exception, allowlist format | U19, U5 |
| (unverified) | SKILL.md Version Context, 3.9 broker compatibility | U18 |
| (medium confidence) | deploy-compose.md and security.md, `allowed.paths` | M11 |
| (medium confidence) | always-do-patterns.md, `allowed.paths` | M11 |
| (unverified) | never-do-patterns.md, allowlist format, HTTP status, bootstrap practice | U5, U15, U14 |
| (medium confidence) | ask-first-decisions.md, standalone, REST auth, converters, plugin path, ReplaceField, secured cluster, connect.protocol | M6, M9, M10, M8, M7, M1, U3 |
| (unverified) | ask-first-decisions.md, class names, image, upgrade procedure | U6, U1, U4 |
| (unverified) | deploy-compose.md, entrypoint, paths, port binding, `file` key, offsets on delete | U1, U10, U13 |
| (unverified) | deploy-compose.md, multi-worker group.id and advertised host name | U20 |
| (medium confidence) | deploy-compose.md, producer and consumer prefixes | M1 |
| (unverified) | error-handling-dlq.md, alert thresholds | U12 |
| (medium confidence) | security.md, hardening items, admin endpoints, ACLs, allowed.paths, REST authentication | M12, M3, M2, M4, M5, M11, M9 |
| (unverified) | security.md, automatic.config.providers | U7 |
| (unverified) | observability.md, offsets on delete, thresholds, harness, field and class names | U13, U12, U11, U10 |
| (medium confidence) | observability.md, resume of a stopped connector | U9 |
| (medium confidence) | migration-guide.md, ReplaceField, connect.protocol | M7, U3 |
| (unverified) | migration-guide.md, automatic.config.providers, upgrade steps, image, CVE search | U7, U4, U1, U16 |
| (unverified), (medium confidence) | evaluation-scenarios.md | U1, U3 |

## Source Bibliography

All pages read 2026-11-04 (S20 read 2026-11-04, last edited 2024-07-09). S18 is a navigation page and is not cited.

| ID | Title | URL |
|---|---|---|
| S1 | Kafka Connect User Guide, AK 4.4.X (last modified 2026-10-26) | https://kafka.apache.org/44/kafka-connect/user-guide/ |
| S2 | Kafka Connect Overview, AK 4.4.X | https://kafka.apache.org/44/kafka-connect/overview/ |
| S3 | Kafka Connect Administration, AK 4.4.X | https://kafka.apache.org/44/kafka-connect/administration/ |
| S4 | Connector Development Guide, AK 4.4.X | https://kafka.apache.org/44/kafka-connect/connector-development-guide/ |
| S5 | Kafka Connect Configs, AK 4.4.X | https://kafka.apache.org/44/configuration/kafka-connect-configs/ |
| S6 | Configuration Providers, AK 4.4.X | https://kafka.apache.org/44/configuration/configuration-providers/ |
| S7 | Kafka Connect Security Model, AK 4.4.X | https://kafka.apache.org/44/security/security-model-connect/ |
| S8 | Monitoring (Connect section), AK 4.4.X | https://kafka.apache.org/44/operations/monitoring/ |
| S9 | Upgrading, AK 4.4.X (last modified 2026-10-26) | https://kafka.apache.org/44/getting-started/upgrade/ |
| S10 | Apache Kafka 4.4.0 Release Announcement (2026-10-22) | https://kafka.apache.org/blog/2026/10/22/apache-kafka-4.4.0-release-announcement/ |
| S11 | Docker, AK 4.4.X | https://kafka.apache.org/44/getting-started/docker/ |
| S12 | Docker examples README, branch 4.4 | https://raw.githubusercontent.com/apache/kafka/4.4/docker/examples/README.md |
| S13 | Quick Start, AK 4.4.X | https://kafka.apache.org/44/getting-started/quickstart/ |
| S14 | Sample connect-distributed.properties, branch 4.4 | https://raw.githubusercontent.com/apache/kafka/4.4/config/connect-distributed.properties |
| S15 | Compatibility, AK 4.4.X | https://kafka.apache.org/44/getting-started/compatibility/ |
| S16 | Java Version, AK 4.4.X | https://kafka.apache.org/44/operations/java-version/ |
| S17 | KIP-1209: control internal topic creation in Kafka Connect (Apache wiki) | https://cwiki.apache.org/confluence/display/KAFKA/KIP-1209:+Add+configuration+to+control+internal+topic+creation+in+Kafka+Connect |
| S19 | Downloads page (Apache Kafka project) | https://kafka.apache.org/community/downloads/ |
| S20 | Time Based Release Plan (Apache Kafka wiki, official project wiki, last edited 2024-07-09) | https://cwiki.apache.org/confluence/display/KAFKA/Time+Based+Release+Plan |
