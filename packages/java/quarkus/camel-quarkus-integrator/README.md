# Camel Quarkus Integrator

Implements integration requirements in **Camel Quarkus 3.40 LTS** projects (Camel 4.22, Quarkus 3.40), driven by 13 version-locked knowledge skills instead of model memory. It replaces the older Copilot-style `camel-quarkus-integrator` router (Camel Quarkus 3.15).

The package adds: the orchestrator skill `integrating-camel-quarkus`, the structure skill `structuring-camel-quarkus-projects`, the non-interactive subagent `camel-quarkus-integrator`, and 3 scoped rules. The 13 `developing-*-v3-40` knowledge skills come from the `camel-quarkus-skills` package (a dependency).

---

## Installation

Installed through APM; the package depends on `factory-core` and `camel-quarkus-skills`, which resolve transitively:

```bash
apm install ./packages/java/quarkus/camel-quarkus-integrator --target claude
```

(or list `./packages/java/quarkus/camel-quarkus-integrator` in the root `apm.yml` and run `apm install --target claude`). Edit sources here under `.apm/`, **never** in `.claude/` (generated).

---

## Two entry points

| Entry point | Mode | Use when |
|---|---|---|
| `/integrating-camel-quarkus` (inline skill) | Interactive: asks about input, processing, output, errors and tests, then loads the right skills and generates code | The requirement is still open, or you want to answer questions |
| `camel-quarkus-integrator` (subagent) | Non-interactive: takes a closed requirement, reads the structure and needed skills, generates code, runs `./mvnw clean compile` (or `mvn` when the project has no wrapper; and tests if requested), verifies files and `pom.xml`, reports | The requirement is fully specified and delegated to an agent |

A subagent cannot interview the user. If the requirement is incomplete or needs an uncovered area, it returns **questions** (status `NEEDS-INPUT`) instead of assuming.

The requirement-to-skills mapping lives only in `integrating-camel-quarkus`; the rules and the agent point there.

---

## Scope

**In scope** (Camel Quarkus 3.40 LTS / Camel 4.22 / Quarkus 3.40, 13 skills): core (BOMs, routes, CDI, native), bean, file (incl. FTP/SFTP), HTTP client, platform-http, REST DSL, JAXB, XSLT, log/MDC, Camel route testing (`camel-quarkus-junit`), plus the generic Quarkus pieces ARC (CDI), Quarkus REST and Quarkus JUnit.

**Out of scope, no skill exists:** message queues/brokers (Kafka, JMS, RabbitMQ, AMQP), databases (JDBC/SQL), Quarkus security (OIDC, authentication, authorization), e-mail. The agent reports these as a limitation and does not improvise.

**Documented gaps (no installed skill documents them):** timer and SEDA endpoints, cron-style scheduling, aggregation EIP options, monitoring beyond health checks, CSV/Excel and standalone JSON conversion -> return as a limitation or tag (unverified).

## Rules (scoped)

| Rule | Source `applyTo` (generated as `paths`) |
|---|---|
| `camel-quarkus-integrator-code-standards` | `**/integration/routes/**/*.java` |
| `camel-quarkus-integrator-project-config` | `**/{pom.xml,src/main/resources/application.properties,src/main/resources/application.yml}` |
| `camel-quarkus-integrator-skills-management` | `**/integration/routes/**/*.java` |

Rules carry conventions the skills confirm plus a few labelled team conventions, and refer to skills by name for facts. Path-scoped rules load only when a matching file is read, so they help on existing layouts; the new-project flow lives in this README and in the `camel-quarkus-integrator` agent. The two route rules split the work: `code-standards` holds code conventions, `skills-management` only points to the orchestrator and structure skills.

---

## Version lifetime

As of 2026-10-14:

- Quarkus 4.0 GA is planned for the end of November 2026; no Camel Quarkus build on it and no `quarkus-camel-bom` 4.x is known (medium confidence, absence of evidence). Quarkus 4 artifacts are not covered by these skills; ask before mixing them (medium confidence, absence of evidence).
- Quarkus 3.40 LTS is maintained to **2027-09-30**. The Camel Quarkus-specific end date is (unverified) (not published); applying the Quarkus date is an inference.
- A new Camel Quarkus version means new `developing-*` skills (one skill = one version), not edits of those; the orchestrator is the exception (see Design notes).

## Design notes

- `integrating-camel-quarkus` is deliberately NOT suffixed `-v3-40` and has no register of its own: it is updated in place when a new Camel Quarkus version appears (the sibling skills are one-skill-per-version), and every tag in it relays the register of the sibling skill named beside it.
- The two route rules (`code-standards`, `skills-management`) share one glob by design; they are not merged because one holds code conventions and the other only points to the orchestrator and structure skills.

## Provenance

The skills were generated on 2026-10-14 from dated official-source research (camel.apache.org, quarkus.io, Maven Central). Each skill tags unverified and medium-confidence claims; the agent and rules carry those tags through rather than asserting them.

## Migrating from the Copilot version

Prompts such as `/camel-quarkus-integrator-unified` and the 3.15 skills no longer apply. The old router and its second routing rule were replaced by the orchestrator skill. The old rules' `applyTo: **/*.java` was narrowed so Camel context does not load in every Java file.
