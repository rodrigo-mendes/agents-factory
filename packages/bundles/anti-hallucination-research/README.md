# anti-hallucination-research

Anti-Hallucination Research: version-absolute research of frameworks, cloud, methodologies and 14 self-managed platform categories, every claim tied to a dated official source.

**Who it is for:** Anyone who needs researched, version-pinned knowledge of a framework, a cloud, a method, a domain or a self-hosted platform before writing code or skills.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`researching-frameworks`](../../factory/researching-frameworks/README.md), [`researching-platform`](../../factory/researching-platform/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`research-core`](../../factory/research-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| command | [`/architecture-methodology-researcher`](../../factory/researching-frameworks/README.md#architecture-methodology-researcher) | `researching-frameworks` |
| command | [`/business-domain-researcher`](../../factory/researching-frameworks/README.md#business-domain-researcher) | `researching-frameworks` |
| command | [`/cloud-architecture-researcher`](../../factory/researching-frameworks/README.md#cloud-architecture-researcher) | `researching-frameworks` |
| command | [`/requirements-methodology-researcher`](../../factory/researching-frameworks/README.md#requirements-methodology-researcher) | `researching-frameworks` |
| command | [`/researching-technical-frameworks`](../../factory/researching-frameworks/README.md#researching-technical-frameworks) | `researching-frameworks` |
| command | [`/researching-api-gateway`](../../factory/researching-platform/README.md#researching-api-gateway) | `researching-platform` |
| command | [`/researching-cache-store`](../../factory/researching-platform/README.md#researching-cache-store) | `researching-platform` |
| command | [`/researching-columnar-analytics`](../../factory/researching-platform/README.md#researching-columnar-analytics) | `researching-platform` |
| command | [`/researching-coordination-service`](../../factory/researching-platform/README.md#researching-coordination-service) | `researching-platform` |
| command | [`/researching-document-store`](../../factory/researching-platform/README.md#researching-document-store) | `researching-platform` |
| command | [`/researching-graph-database`](../../factory/researching-platform/README.md#researching-graph-database) | `researching-platform` |
| command | [`/researching-kv-store`](../../factory/researching-platform/README.md#researching-kv-store) | `researching-platform` |
| command | [`/researching-object-storage`](../../factory/researching-platform/README.md#researching-object-storage) | `researching-platform` |
| command | [`/researching-platform-software`](../../factory/researching-platform/README.md#researching-platform-software) | `researching-platform` |
| command | [`/researching-rdbms`](../../factory/researching-platform/README.md#researching-rdbms) | `researching-platform` |
| command | [`/researching-search-engine`](../../factory/researching-platform/README.md#researching-search-engine) | `researching-platform` |
| command | [`/researching-streaming-broker`](../../factory/researching-platform/README.md#researching-streaming-broker) | `researching-platform` |
| command | [`/researching-timeseries-db`](../../factory/researching-platform/README.md#researching-timeseries-db) | `researching-platform` |
| command | [`/researching-vector-store`](../../factory/researching-platform/README.md#researching-vector-store) | `researching-platform` |
| command | [`/researching-wide-column-store`](../../factory/researching-platform/README.md#researching-wide-column-store) | `researching-platform` |
| agent | [`framework-researcher`](../../factory/research-core/.apm/agents/framework-researcher.agent.md) | `research-core` |
| agent | [`research-synthesizer`](../../factory/research-core/.apm/agents/research-synthesizer.agent.md) | `research-core` |
| agent | [`section-investigator`](../../factory/research-core/.apm/agents/section-investigator.agent.md) | `research-core` |

Plus 0 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/anti-hallucination-research --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py anti-hallucination-research           # dry run
python scripts/export-bundle.py anti-hallucination-research --apply   # writes dist/anti-hallucination-research/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/researching-technical-frameworks FastAPI 0.115
/researching-platform-software Kafka 3.7
```

The agent shows a plan and waits for your approval before it writes the research file.

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`researching-frameworks`](../../factory/researching-frameworks/README.md): usage manual.
- [`researching-platform`](../../factory/researching-platform/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
