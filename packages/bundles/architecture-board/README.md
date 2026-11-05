# architecture-board

Architecture Board: solution architect and reviewer plus the AWS and OCI architecture advisors.

**Who it is for:** Architects who want a solution architect and reviewer plus AWS and OCI advisors in one install.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`solution-architecture`](../../architecture/solution-architecture/README.md), [`aws-architect`](../../cloud/provider/aws/aws-architect/README.md), [`oci-architecture`](../../cloud/provider/oci/oci-architecture/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`handoff-core`](../../delivery/protocol/handoff-core/README.md), [`openspec-core`](../../delivery/specs/openspec-core/README.md), [`aws-skills`](../../cloud/provider/aws/aws-skills/README.md), [`oci-core`](../../cloud/provider/oci/oci-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| agent | [`solution-architect`](../../architecture/solution-architecture/.apm/agents/solution-architect.agent.md) | `solution-architecture` |
| agent | [`solution-architecture-reviewer`](../../architecture/solution-architecture/.apm/agents/solution-architecture-reviewer.agent.md) | `solution-architecture` |
| command | [`/aws-architecture-advisor`](../../cloud/provider/aws/aws-architect/README.md#aws-architecture-advisor) | `aws-architect` |
| agent | [`aws-architect-reviewer`](../../cloud/provider/aws/aws-architect/.apm/agents/aws-architect-reviewer.agent.md) | `aws-architect` |
| agent | [`aws-architect`](../../cloud/provider/aws/aws-architect/.apm/agents/aws-architect.agent.md) | `aws-architect` |
| agent | [`aws-infrastructure-architect`](../../cloud/provider/aws/aws-architect/.apm/agents/aws-infrastructure-architect.agent.md) | `aws-architect` |
| command | [`/design-oci-architecture`](../../cloud/provider/oci/oci-architecture/README.md#design-oci-architecture) | `oci-architecture` |
| command | [`/provision-oci-serverless-stack`](../../cloud/provider/oci/oci-architecture/README.md#provision-oci-serverless-stack) | `oci-architecture` |
| agent | [`oci-serverless-architect`](../../cloud/provider/oci/oci-architecture/.apm/agents/oci-serverless-architect.agent.md) | `oci-architecture` |
| agent | [`oci-serverless-stack`](../../cloud/provider/oci/oci-architecture/.apm/agents/oci-serverless-stack.agent.md) | `oci-architecture` |
| command | [`/syncing-spec-from-code`](../../delivery/protocol/handoff-core/README.md#syncing-spec-from-code) | `handoff-core` |
| agent | [`spec-synchronizer`](../../delivery/protocol/handoff-core/.apm/agents/spec-synchronizer.agent.md) | `handoff-core` |

Plus 49 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/architecture-board --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py architecture-board           # dry run
python scripts/export-bundle.py architecture-board --apply   # writes dist/architecture-board/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/aws-architecture-advisor review my VPC design
/design-oci-architecture full-stack my-capability
```

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`aws-architect`](../../cloud/provider/aws/aws-architect/README.md): usage manual.
- [`oci-architecture`](../../cloud/provider/oci/oci-architecture/README.md): usage manual.
- [`solution-architecture`](../../architecture/solution-architecture/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
