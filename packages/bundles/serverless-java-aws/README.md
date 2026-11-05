# serverless-java-aws

Serverless Java on AWS: Quarkus 3.40 on Lambda (HTTP, Cognito, data, messaging, testing, observability), Lambda deploy and debug agents.

**Who it is for:** Java teams that run Quarkus 3.40 on AWS Lambda and want deploy and debug agents.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`quarkus-aws`](../../java/quarkus/quarkus-aws/README.md), [`aws-lambda`](../../cloud/provider/aws/aws-lambda/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`quarkus-core`](../../java/quarkus/quarkus-core/README.md), [`handoff-core`](../../delivery/protocol/handoff-core/README.md), [`aws-skills`](../../cloud/provider/aws/aws-skills/README.md), [`clean-code-quarkus`](../../java/clean-code/clean-code-quarkus/README.md), [`openspec-core`](../../delivery/specs/openspec-core/README.md), [`aws-terraform`](../../cloud/terraform/aws-terraform/README.md), [`aws-observability`](../../cloud/provider/aws/aws-observability/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| agent | [`quarkus-code-reviewer`](../../java/quarkus/quarkus-aws/.apm/agents/quarkus-code-reviewer.agent.md) | `quarkus-aws` |
| agent | [`quarkus-lambda-integrator`](../../java/quarkus/quarkus-aws/.apm/agents/quarkus-lambda-integrator.agent.md) | `quarkus-aws` |
| agent | [`aws-lambda-debugger`](../../cloud/provider/aws/aws-lambda/.apm/agents/aws-lambda-debugger.agent.md) | `aws-lambda` |
| agent | [`aws-lambda-deployer`](../../cloud/provider/aws/aws-lambda/.apm/agents/aws-lambda-deployer.agent.md) | `aws-lambda` |
| command | [`/syncing-spec-from-code`](../../delivery/protocol/handoff-core/README.md#syncing-spec-from-code) | `handoff-core` |
| agent | [`spec-synchronizer`](../../delivery/protocol/handoff-core/.apm/agents/spec-synchronizer.agent.md) | `handoff-core` |
| command | [`/observe-aws-workload`](../../cloud/provider/aws/aws-observability/README.md#observe-aws-workload) | `aws-observability` |
| agent | [`aws-observability`](../../cloud/provider/aws/aws-observability/.apm/agents/aws-observability.agent.md) | `aws-observability` |
| agent | [`static-site-verifier`](../../cloud/provider/aws/aws-observability/.apm/agents/static-site-verifier.agent.md) | `aws-observability` |

Plus 86 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/serverless-java-aws --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py serverless-java-aws           # dry run
python scripts/export-bundle.py serverless-java-aws --apply   # writes dist/serverless-java-aws/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

This bundle has no commands. Its agents work from work-orders written by an orchestrator, and its skills load by description.

```text
Since the last release clients get HTTP 500 from the HTTP API. The function code did not change. Find the cause.
```

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`quarkus-aws`](../../java/quarkus/quarkus-aws/README.md): usage manual.
- [`aws-lambda`](../../cloud/provider/aws/aws-lambda/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
