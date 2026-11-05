# github-actions-secure-cicd

GitHub Actions Secure CI/CD: 9 pipeline skills (OIDC to AWS and OCI, supply chain, blast radius, Java, Next.js, Terraform, containers) and the pipeline engineer and reviewer agents.

**Who it is for:** Teams that write or review GitHub Actions pipelines with OIDC, pinned actions and limited blast radius.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`github-actions-cicd`](../../delivery/github/github-actions-cicd/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`github-core`](../../delivery/github/github-core/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| command | [`/building-cicd-pipelines`](../../delivery/github/github-actions-cicd/README.md#building-cicd-pipelines) | `github-actions-cicd` |
| agent | [`cicd-pipeline-engineer`](../../delivery/github/github-actions-cicd/.apm/agents/cicd-pipeline-engineer.agent.md) | `github-actions-cicd` |
| agent | [`cicd-pipeline-reviewer`](../../delivery/github/github-actions-cicd/.apm/agents/cicd-pipeline-reviewer.agent.md) | `github-actions-cicd` |

Plus 11 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/github-actions-secure-cicd --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py github-actions-secure-cicd           # dry run
python scripts/export-bundle.py github-actions-secure-cicd --apply   # writes dist/github-actions-secure-cicd/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/building-cicd-pipelines Java Lambda CI+CD to AWS via OIDC, Pro private repo, dev+prod, monorepo ./
```

To audit existing workflows, ask Claude to use the cicd-pipeline-reviewer agent.

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`github-actions-cicd`](../../delivery/github/github-actions-cicd/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
