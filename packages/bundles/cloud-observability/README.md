# cloud-observability

Cloud Observability: logs, metrics, traces, alarms and dashboards for AWS Lambda and OCI Functions, with read-only live validation scripts.

**Who it is for:** Teams that need logs, metrics, traces, alarms and dashboards for AWS Lambda or OCI Functions, with read-only live validation.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`aws-observability`](../../cloud/provider/aws/aws-observability/README.md), [`oci-observability`](../../cloud/provider/oci/oci-observability/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`handoff-core`](../../delivery/protocol/handoff-core/README.md), [`aws-skills`](../../cloud/provider/aws/aws-skills/README.md), [`aws-terraform`](../../cloud/terraform/aws-terraform/README.md), [`openspec-core`](../../delivery/specs/openspec-core/README.md), [`oci-core`](../../cloud/provider/oci/oci-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| command | [`/observe-aws-workload`](../../cloud/provider/aws/aws-observability/README.md#observe-aws-workload) | `aws-observability` |
| agent | [`aws-observability`](../../cloud/provider/aws/aws-observability/.apm/agents/aws-observability.agent.md) | `aws-observability` |
| agent | [`static-site-verifier`](../../cloud/provider/aws/aws-observability/.apm/agents/static-site-verifier.agent.md) | `aws-observability` |
| command | [`/observe-oci-workload`](../../cloud/provider/oci/oci-observability/README.md#observe-oci-workload) | `oci-observability` |
| agent | [`oci-observability`](../../cloud/provider/oci/oci-observability/.apm/agents/oci-observability.agent.md) | `oci-observability` |
| command | [`/syncing-spec-from-code`](../../delivery/protocol/handoff-core/README.md#syncing-spec-from-code) | `handoff-core` |
| agent | [`spec-synchronizer`](../../delivery/protocol/handoff-core/.apm/agents/spec-synchronizer.agent.md) | `handoff-core` |

Plus 79 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/cloud-observability --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py cloud-observability           # dry run
python scripts/export-bundle.py cloud-observability --apply   # writes dist/cloud-observability/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/observe-aws-workload orders-api region=eu-west-1 mode=validate
/observe-oci-workload func-orders pillar: alarms
```

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`aws-observability`](../../cloud/provider/aws/aws-observability/README.md): usage manual.
- [`oci-observability`](../../cloud/provider/oci/oci-observability/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
