---
name: integrating-camel-quarkus
description: "Interviews the user and orchestrates Camel Quarkus 3.40 integrations, loading only the matching developing-camel-quarkus-* skills. Use when designing end-to-end routes on Camel Quarkus 3.40. Not for Quarkus 4, other versions, Kafka/JMS, JDBC or Quarkus security."
---

# Integrating Camel Quarkus 3.40

> Version lock: **Camel Quarkus 3.40.x** (Camel 4.22, Quarkus 3.40 LTS). This skill holds workflow only.
> Every technical fact lives in the 13 installed `developing-*-v3-40` skills; load them, do not restate them.
> Claims those skills tag (unverified) or (medium confidence) stay tagged when you relay them.

## Overview

Inline interactive orchestrator. It interviews the user (four blocks), confirms a requirement summary,
loads the project-structure skill and the core skill, then loads only the skills and blueprints that the
answers map to. It generates code only after the user confirms the summary.

## Version Context

| Item | Value | Confidence | Source |
|---|---|---|---|
| Camel Quarkus | 3.40.x (3.40.0 released 2026-09-28, LTS) | High | https://camel.apache.org/releases/ |
| Camel / Quarkus under it | Camel 4.22.1, Quarkus 3.40.1 | High | https://camel.apache.org/camel-quarkus/latest/ |
| Quarkus 3.40 LTS | released 2026-09-30, community-maintained until 2027-09-30 | High | https://quarkus.io/releases |
| Camel Quarkus-specific LTS end date | not published | (unverified) | https://camel.apache.org/camel-quarkus/latest/ ("LTS Until" column blank) |
| Java | 17 and 21 | High | https://camel.apache.org/releases/q-3.40.0/ |
| Quarkus 4 | 4.0.0.Beta1 published 2026-10-01, final planned for the end of November, Java 21 base | High | https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ |
| Camel Quarkus on Quarkus 4 | no build is known | (medium confidence, absence of evidence) | https://quarkus.io/blog/quarkus-4-0-0-beta1-released/ |

Quarkus 4 risk: this skill is locked to 3.40.x; ask before any move to Quarkus 4 artifacts or another Camel Quarkus line.

This skill is deliberately not suffixed `-v3-40` and has no register of its own: it is updated in place when a new Camel Quarkus version appears (the sibling skills are one-skill-per-version), and every (medium confidence)/(unverified) tag in it relays the register of the sibling skill named beside it.

## Quick Navigation

- [Version Context](#version-context)
- [Blueprints & Guardrails](#blueprints--guardrails)
- [Interview](#interview)
- [Shared Foundation](#shared-foundation)
- [Requirement to Skills](#requirement-to-skills)
- [Requirement to Blueprints](#requirement-to-blueprints)
- [Out of Scope](#out-of-scope)
- [Generation Flow](#generation-flow)
- [Final Checklist](#final-checklist)
- Blueprints: [core routes](./blueprints/core-routes.md), [REST APIs](./blueprints/rest-apis.md), [file processing](./blueprints/file-processing.md), [HTTP clients](./blueprints/http-clients.md), [data transformation](./blueprints/data-transformation.md), [testing](./blueprints/testing.md)
- [Evaluation scenarios](./blueprints/evaluation-scenarios.md)
- Cross-references between blueprints (listed here, not linked inside them): file processing hands content to data transformation; file processing hands test needs to testing

## Blueprints & Guardrails

### ✅ Always Do

- **Confirm the requirement summary before generating.** Restate source, processing, destination and extras; wait for a yes.
- **Load `structuring-camel-quarkus-projects` first, then `developing-camel-quarkus-core-v3-40`.** File paths, packages and naming come from the structure skill, never from memory.
- **Load only what the answers map to.** Use the two mapping tables below; one skill or blueprint per need.
- **Join specialties through `direct:` endpoints.** One RouteBuilder per specialty (team convention); see [Shared Foundation](#shared-foundation).
- **Relay confidence tags.** If a loaded skill marks a default or behavior unverified, say so and offer a way to test it.
- **Finish with the [checklist](#final-checklist).** Compile before declaring done.

### ⚠️ Ask First

- **Out-of-scope requirement** (broker, database, security, e-mail): see [Out of Scope](#out-of-scope).
- **Alternatives a skill leaves open** (REST DSL vs Quarkus REST resource, `xslt` vs `xslt-saxon`, `ftp` vs `mina-sftp`): ask the skill's own Ask First question.
- **Tests**: unit only, route tests with AdviceWith, or packaged/native; load the testing blueprint only if requested.
- **New project or existing one**: existing code and `pom.xml` extensions must be checked before adding files.
- **Batch execution** of a closed requirement: offer the handoff in [Generation Flow](#generation-flow).

### 🚫 Never Do

- **Never load all 13 skills "just in case".** Instead: load per the tables; skills cost context.
- **Never invent a skill, extension or API for an uncovered area.** Instead: declare it out of scope and offer research.
- **Never present an unverified or medium-confidence claim as fact.** Instead: relay the tag.
- **Never generate before the user confirms the summary.** Instead: ask, then wait.
- **Never write Spring annotations, `camel-quarkus-junit5`, `camel-quarkus-resilience4j` or patterns from older Camel Quarkus lines.** Instead: apply the loaded skills; correct the user and explain why (see [evaluation scenarios](./blueprints/evaluation-scenarios.md)).
- **Never copy technical facts into answers from memory.** Instead: read the skill section and point to it.

## Interview

Ask all four blocks in one message. Skip any block the user already answered; do not ask twice.

### 1. Data source (input)

Where does the data come from?

- **timer**: scheduled execution (every 5 seconds, daily at 9 AM) (documented gap: not documented, see core-routes coverage note)
- **file-watch**: file system monitoring (new XML files in `/input`)
- **http-endpoint**: HTTP requests received (`POST /api/webhook`)
- **message-queue**: message consumption (Kafka topic, RabbitMQ queue) - out of scope
- **database-query**: database polling (query a table every hour) - out of scope
- **ftp/sftp**: remote file download
- **direct-call**: internal call from another Camel route

### 2. Data processing

What should happen with the data?

- **validation**: format, business rules, schema compliance
- **transformation**: convert formats (XML/JSON (REST binding only))
- **enrichment**: add data from external sources (API calls, lookups)
- **filtering**: filter records by condition
- **aggregation**: group, sum, count, statistics (documented gap: not documented, see core-routes coverage note)
- **routing**: route to different destinations by content

### 3. Data destination (output)

Where should the processed data go?

- **log-output**: application logs
- **file-write**: local files
- **http-forward**: HTTP endpoint or API
- **message-queue**: publish to a queue - out of scope
- **database-store**: store in a database - out of scope
- **ftp/sftp-upload**: upload to a remote server
- **email-send**: send by e-mail - out of scope

### 4. Additional requirements

- **error-handling**: retry, dead letter queue, notifications (out of scope)
- **monitoring**: metrics, health checks, alerting (documented gap beyond health checks)
- **security**: authentication (out of scope), encryption (TLS), data masking (log skill row)
- **testing**: unit, integration, performance tests (documented gap)
- **documentation**: OpenAPI, README, deployment guide (documented gap)

After the answers, post a summary table (block, answer, mapped skills, mapped blueprints, out-of-scope items) and ask for confirmation.

## Shared Foundation

Applies to every integration. The specialist blueprints do not repeat it.

1. **Read the structure skill** `structuring-camel-quarkus-projects`: paths, base package, class and test naming.
2. **Read the core skill** `developing-camel-quarkus-core-v3-40`: BOM, route discovery, CDI, native basics.
3. **Check existing code**: search for a class with the same purpose; check `pom.xml` for the needed extensions before adding any.
4. **Place each file** where the structure skill says; one class per specialty (team convention).
5. **Keep the build green**: `./mvnw clean compile` (or `mvn` when the project has no wrapper) after generation.

### Boundaries matrix

| Specialty | Owns | Hands off through | Does not own |
|---|---|---|---|
| Core routes | Timers (documented gap), `direct:`/internal routing, content-based routing, error handlers, bean calls, logging | `direct:` consumers it defines | HTTP server, file I/O, outbound HTTP, format conversion |
| REST APIs | Inbound HTTP: `rest()` DSL, platform-http, OpenAPI, uploads | `to("direct:<flow>")` | Business routing, file writes, outbound calls |
| File processing | `file:`, `file-watch:`, FTP/SFTP consume and produce | `direct:` in and out | Parsing and format conversion of content |
| HTTP clients | Outbound `http:`/`https:`, auth, timeouts, circuit breaker | `direct:` in | Inbound endpoints, retries elsewhere |
| Data transformation | JAXB, XSLT, mapping between formats | `direct:` in and out | Where data comes from or goes |
| Testing | Route and unit tests of all the above | n/a | Production code |

### Integration contract

- Specialties talk only through `direct:` endpoints (team convention; `direct:` is synchronous, same CamelContext, defaults in the core skill Quick Reference).
- The producer of a flow step owns the endpoint name; the name follows the naming convention of the structure skill (team convention).
- The `direct:` extension (`camel-quarkus-direct`) may be missing from `pom.xml` (medium confidence; rest skill, main-branch example, core only in an example dependency list): ask first, see the rest skill's Ask First row "Dependencies beyond the transport".
- The specialist that receives the exchange documents the expected body type in the route's Javadoc (team convention).

## Requirement to Skills

All names are the installed skills. Load the core and structure skills always; add rows only when the answer matches.

| Requirement | Skill(s) to load |
|---|---|
| Any integration (always) | `structuring-camel-quarkus-projects`, `developing-camel-quarkus-core-v3-40` |
| Source `direct-call`; routing, filtering, error handling | `developing-camel-quarkus-core-v3-40` (already loaded) |
| Source timer; aggregation | `developing-camel-quarkus-core-v3-40` (already loaded), but not documented there (documented gap; see core-routes coverage note) |
| Source or destination local files, file-watch, FTP/SFTP | `developing-camel-quarkus-file-v3-40` |
| Source http-endpoint (any inbound HTTP) | `developing-camel-quarkus-platform-http-v3-40` |
| REST DSL, JSON binding, OpenAPI, CORS, request validation | `developing-camel-quarkus-rest-v3-40` (+ platform-http) |
| Jakarta REST resources or typed REST clients instead of REST DSL (only if the user chooses them) | `developing-quarkus-rest-v3-40` |
| Destination http-forward, enrichment by API call, circuit breaker | `developing-camel-quarkus-http-v3-40` |
| XML to or from Java objects, XSD validation | `developing-camel-quarkus-jaxb-v3-40` |
| XML to XML or XML to text by stylesheet | `developing-camel-quarkus-xslt-v3-40` |
| Custom Java logic called from routes (`bean:`, `class:`, `@Handler`) | `developing-camel-quarkus-bean-v3-40` (+ `developing-quarkus-arc-v3-40`) |
| CDI beans with scopes, qualifiers, `@Identifier`, unused-bean removal | `developing-quarkus-arc-v3-40` |
| Destination log-output, data masking, MDC correlation | `developing-camel-quarkus-log-v3-40` |
| Testing Camel routes (AdviceWith, MockEndpoint) | `developing-camel-quarkus-junit-v3-40` + `developing-quarkus-junit-v3-40` |
| Testing only generic Quarkus code or REST Assured endpoints | `developing-quarkus-junit-v3-40` |
| Monitoring: health checks | `developing-camel-quarkus-core-v3-40` (health row); metrics and alerting are not documented (documented gap) |
| Security: TLS | The TLS section of the core, http or platform-http skill that applies |
| Documentation: OpenAPI | `developing-camel-quarkus-rest-v3-40` |

JSON-only or CSV/Excel conversion has no dedicated skill. JSON binding in REST context is covered by the REST skill; for the rest, say it is not documented and ask before proceeding.

## Requirement to Blueprints

Load a blueprint only when the matching answer appears. Each blueprint lists which skills to load for its specialty.

| Interview answer | Blueprint(s) |
|---|---|
| timer, direct-call, routing, filtering, aggregation, bean logic, error handling, log-output | [core routes](./blueprints/core-routes.md) |
| http-endpoint, REST, OpenAPI, upload | [REST APIs](./blueprints/rest-apis.md) |
| file-watch, ftp/sftp, file-write, ftp/sftp-upload | [file processing](./blueprints/file-processing.md) |
| http-forward, enrichment by API, circuit breaker | [HTTP clients](./blueprints/http-clients.md) |
| validation by schema, transformation (XML/Java/XSLT) | [data transformation](./blueprints/data-transformation.md) |
| testing requested | [testing](./blueprints/testing.md) |
| message-queue, database, security (auth), e-mail | none; see [Out of Scope](#out-of-scope) |

## Out of Scope

No skill in this package covers: **message queues and brokers (Kafka, JMS, RabbitMQ, AMQP), databases (JDBC/SQL), Quarkus security (OIDC, authentication, authorization), e-mail.**

Documented gaps (inside the covered stack, but no installed skill documents them): timer and SEDA endpoints, cron-style scheduling, aggregation EIP options, monitoring beyond health checks, CSV/Excel and standalone JSON conversion. Treat them like out-of-scope items for naming extensions or options.

When an answer touches them:

1. Say plainly that no installed skill documents the area, so you cannot vouch for its extension names, options or defaults.
2. Ask whether to proceed with only the documented parts (the rest stays a stub route or a `direct:` boundary the user fills in).
3. Offer to research it first with `/researching-technical-frameworks <technology> <version>`, then build a skill from the research.
4. Never name an extension, annotation or option for it as if verified.

## Generation Flow

1. **Interview** (four blocks) and **summary confirmation**.
2. **Load** the foundation skills, then the mapped skills and blueprints.
3. **Resolve** each loaded blueprint's Ask First decisions; keep answers in the summary.
4. **Generate** one class per specialty at the paths from the structure skill; add the `pom.xml` extensions without versions (the BOM manages them, per the core skill).
5. **Verify** with the [checklist](#final-checklist); report unverified items the code depends on.

**Handoff.** When the requirement is closed (all four blocks confirmed, no open Ask First) and the user wants batch execution, delegate to the subagent `camel-quarkus-integrator` with the confirmed summary, the skill list and the blueprint list. Do not delegate while questions remain open.

## Final Checklist

- [ ] Summary confirmed by the user; out-of-scope items agreed or removed
- [ ] Files created at the paths defined by `structuring-camel-quarkus-projects`
- [ ] Only the mapped skills and blueprints were loaded
- [ ] `./mvnw clean compile` passes (or `mvn` when the project has no wrapper)
- [ ] Tests added if requested, using `camel-quarkus-junit` (not `-junit5`) and run with `./mvnw test` (or `mvn test`)
- [ ] Unverified or medium-confidence items the code relies on listed for the user
