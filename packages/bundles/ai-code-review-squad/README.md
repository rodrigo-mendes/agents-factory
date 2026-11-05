# ai-code-review-squad

AI Code Review Squad: five read-only reviewer agents (Quarkus on Lambda, LangChain4j on Quarkus, Terraform, GitHub Actions CI/CD, Stripe Java) with the skills and rules they cite. The install pulls the whole source packages; export.yml cuts the sold package down to the reviewers.

**Who it is for:** Teams that want independent, read-only code review of Quarkus on Lambda, LangChain4j on Quarkus, Terraform, GitHub Actions and Stripe Java code.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`quarkus-langchain4j`](../../java/quarkus/quarkus-langchain4j/README.md), [`terraform`](../../cloud/terraform/terraform/README.md), [`github-actions-cicd`](../../delivery/github/github-actions-cicd/README.md), [`stripe-java`](../../java/libs/stripe-java/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`quarkus-aws`](../../java/quarkus/quarkus-aws/README.md), [`quarkus-core`](../../java/quarkus/quarkus-core/README.md), [`handoff-core`](../../delivery/protocol/handoff-core/README.md), [`aws-skills`](../../cloud/provider/aws/aws-skills/README.md), [`clean-code-quarkus`](../../java/clean-code/clean-code-quarkus/README.md), [`openspec-core`](../../delivery/specs/openspec-core/README.md), [`research-core`](../../factory/research-core/README.md), [`artifact-authoring`](../../factory/artifact-authoring/README.md), [`aws-terraform`](../../cloud/terraform/aws-terraform/README.md), [`github-core`](../../delivery/github/github-core/README.md)

> **Sold as a subset.** The exported package keeps only what `export.yml` selects. The table below lists what the packages provide, so the sold subset is narrower.
> - agents: `quarkus-code-reviewer`, `langchain4j-reviewer`, `terraform-code-reviewer`, `cicd-pipeline-reviewer`, `stripe-advisor`
> - skills: `cited`
> - rules: `cited`
> - include: `skills/provisioning-aws-*-v6`, `skills/*stripe*-v34`
> - exclude: `skills/building-aws-saas-serverless-quarkus-react-nextjs`, `skills/coordinating-quarkus-aws-handoffs`

| Type | Entry point or agent | Package |
|---|---|---|
| agent | [`langchain4j-reviewer`](../../java/quarkus/quarkus-langchain4j/.apm/agents/langchain4j-reviewer.agent.md) | `quarkus-langchain4j` |
| command | [`/provision-aws-terraform`](../../cloud/terraform/terraform/README.md#provision-aws-terraform) | `terraform` |
| command | [`/technical-framework-researcher-terraform`](../../cloud/terraform/terraform/README.md#technical-framework-researcher-terraform) | `terraform` |
| command | [`/terraform-engineering-best-practices-researcher`](../../cloud/terraform/terraform/README.md#terraform-engineering-best-practices-researcher) | `terraform` |
| command | [`/terraform-instructions-compiler`](../../cloud/terraform/terraform/README.md#terraform-instructions-compiler) | `terraform` |
| command | [`/terraform-rules-author`](../../cloud/terraform/terraform/README.md#terraform-rules-author) | `terraform` |
| agent | [`aws-terraform-engineer`](../../cloud/terraform/terraform/.apm/agents/aws-terraform-engineer.agent.md) | `terraform` |
| agent | [`terraform-code-reviewer`](../../cloud/terraform/terraform/.apm/agents/terraform-code-reviewer.agent.md) | `terraform` |
| agent | [`terraform-rules-author`](../../cloud/terraform/terraform/.apm/agents/terraform-rules-author.agent.md) | `terraform` |
| command | [`/building-cicd-pipelines`](../../delivery/github/github-actions-cicd/README.md#building-cicd-pipelines) | `github-actions-cicd` |
| agent | [`cicd-pipeline-engineer`](../../delivery/github/github-actions-cicd/.apm/agents/cicd-pipeline-engineer.agent.md) | `github-actions-cicd` |
| agent | [`cicd-pipeline-reviewer`](../../delivery/github/github-actions-cicd/.apm/agents/cicd-pipeline-reviewer.agent.md) | `github-actions-cicd` |
| command | [`/integrate-stripe-java`](../../java/libs/stripe-java/README.md#integrate-stripe-java) | `stripe-java` |
| command | [`/review-stripe-integration`](../../java/libs/stripe-java/README.md#review-stripe-integration) | `stripe-java` |
| agent | [`stripe-advisor`](../../java/libs/stripe-java/.apm/agents/stripe-advisor.agent.md) | `stripe-java` |
| agent | [`stripe-integrator`](../../java/libs/stripe-java/.apm/agents/stripe-integrator.agent.md) | `stripe-java` |
| agent | [`quarkus-code-reviewer`](../../java/quarkus/quarkus-aws/.apm/agents/quarkus-code-reviewer.agent.md) | `quarkus-aws` |
| agent | [`quarkus-lambda-integrator`](../../java/quarkus/quarkus-aws/.apm/agents/quarkus-lambda-integrator.agent.md) | `quarkus-aws` |
| command | [`/syncing-spec-from-code`](../../delivery/protocol/handoff-core/README.md#syncing-spec-from-code) | `handoff-core` |
| agent | [`spec-synchronizer`](../../delivery/protocol/handoff-core/.apm/agents/spec-synchronizer.agent.md) | `handoff-core` |
| agent | [`framework-researcher`](../../factory/research-core/.apm/agents/framework-researcher.agent.md) | `research-core` |
| agent | [`research-synthesizer`](../../factory/research-core/.apm/agents/research-synthesizer.agent.md) | `research-core` |
| agent | [`section-investigator`](../../factory/research-core/.apm/agents/section-investigator.agent.md) | `research-core` |
| command | [`/agent-creator`](../../factory/artifact-authoring/README.md#agent-creator) | `artifact-authoring` |
| command | [`/architecture-approaches-skill-generator`](../../factory/artifact-authoring/README.md#architecture-approaches-skill-generator) | `artifact-authoring` |
| command | [`/methodologies-skill-generator`](../../factory/artifact-authoring/README.md#methodologies-skill-generator) | `artifact-authoring` |
| command | [`/skill-creator`](../../factory/artifact-authoring/README.md#skill-creator) | `artifact-authoring` |
| agent | [`artifact-author`](../../factory/artifact-authoring/.apm/agents/artifact-author.agent.md) | `artifact-authoring` |

Plus 100 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/ai-code-review-squad --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py ai-code-review-squad           # dry run
python scripts/export-bundle.py ai-code-review-squad --apply   # writes dist/ai-code-review-squad/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

The sold package keeps only the five reviewer agents and the skills and rules they cite. They have no commands: ask Claude to use one by name.

```text
Use the cicd-pipeline-reviewer agent to review our .github/workflows for security and blast radius.
Use the stripe-advisor agent to review my webhook handler for signature verification order.
```

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`quarkus-langchain4j`](../../java/quarkus/quarkus-langchain4j/README.md): usage manual.
- [`terraform`](../../cloud/terraform/terraform/README.md): usage manual.
- [`github-actions-cicd`](../../delivery/github/github-actions-cicd/README.md): usage manual.
- [`stripe-java`](../../java/libs/stripe-java/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
