# saas-starter-team

SaaS Starter Team: the spec-driven project-manager orchestrator for a Quarkus Lambda + Next.js SaaS on AWS and its whole agent team. Pulls third-party/vercel-frontend transitively: exclude the Vercel skills from any paid export.

**Who it is for:** Teams that want a spec-driven build of a Quarkus Lambda and Next.js SaaS on AWS, run by one orchestrator and a team of agents.

## Contents

<!-- BEGIN GENERATED:contents -->
**Packages included:** [`aws-saas-serverless-quarkus-react-nextjs`](../../saas/aws-saas-serverless-quarkus-react-nextjs/README.md)
**Also installed as dependencies:** [`factory-core`](../../factory/factory-core/README.md), [`quarkus-aws`](../../java/quarkus/quarkus-aws/README.md), [`aws-lambda`](../../cloud/provider/aws/aws-lambda/README.md), [`aws-observability`](../../cloud/provider/aws/aws-observability/README.md), [`handoff-core`](../../delivery/protocol/handoff-core/README.md), [`aws-architect`](../../cloud/provider/aws/aws-architect/README.md), [`terraform`](../../cloud/terraform/terraform/README.md), [`stripe-java`](../../java/libs/stripe-java/README.md), [`openspec-github`](../../delivery/specs/openspec-github/README.md), [`openspec-poc`](../../delivery/specs/openspec-poc/README.md), [`solution-architecture`](../../architecture/solution-architecture/README.md), [`ui-design`](../../frontend/react/ui-design/README.md), [`nextjs-frontend`](../../frontend/react/nextjs-frontend/README.md), [`quarkus-langchain4j`](../../java/quarkus/quarkus-langchain4j/README.md), [`github-actions-cicd`](../../delivery/github/github-actions-cicd/README.md), [`quarkus-core`](../../java/quarkus/quarkus-core/README.md), [`aws-skills`](../../cloud/provider/aws/aws-skills/README.md), [`aws-terraform`](../../cloud/terraform/aws-terraform/README.md), [`openspec-core`](../../delivery/specs/openspec-core/README.md), [`research-core`](../../factory/research-core/README.md), [`artifact-authoring`](../../factory/artifact-authoring/README.md), [`github-core`](../../delivery/github/github-core/README.md), [`clean-code-quarkus`](../../java/clean-code/clean-code-quarkus/README.md)

| Type | Entry point or agent | Package |
|---|---|---|
| inline orchestrator | [`building-aws-saas-serverless-quarkus-react-nextjs`](../../saas/aws-saas-serverless-quarkus-react-nextjs/README.md#building-aws-saas-serverless-quarkus-react-nextjs) | `aws-saas-serverless-quarkus-react-nextjs` |
| agent | [`quarkus-code-reviewer`](../../java/quarkus/quarkus-aws/.apm/agents/quarkus-code-reviewer.agent.md) | `quarkus-aws` |
| agent | [`quarkus-lambda-integrator`](../../java/quarkus/quarkus-aws/.apm/agents/quarkus-lambda-integrator.agent.md) | `quarkus-aws` |
| agent | [`aws-lambda-debugger`](../../cloud/provider/aws/aws-lambda/.apm/agents/aws-lambda-debugger.agent.md) | `aws-lambda` |
| agent | [`aws-lambda-deployer`](../../cloud/provider/aws/aws-lambda/.apm/agents/aws-lambda-deployer.agent.md) | `aws-lambda` |
| command | [`/observe-aws-workload`](../../cloud/provider/aws/aws-observability/README.md#observe-aws-workload) | `aws-observability` |
| agent | [`aws-observability`](../../cloud/provider/aws/aws-observability/.apm/agents/aws-observability.agent.md) | `aws-observability` |
| agent | [`static-site-verifier`](../../cloud/provider/aws/aws-observability/.apm/agents/static-site-verifier.agent.md) | `aws-observability` |
| command | [`/syncing-spec-from-code`](../../delivery/protocol/handoff-core/README.md#syncing-spec-from-code) | `handoff-core` |
| agent | [`spec-synchronizer`](../../delivery/protocol/handoff-core/.apm/agents/spec-synchronizer.agent.md) | `handoff-core` |
| command | [`/aws-architecture-advisor`](../../cloud/provider/aws/aws-architect/README.md#aws-architecture-advisor) | `aws-architect` |
| agent | [`aws-architect-reviewer`](../../cloud/provider/aws/aws-architect/.apm/agents/aws-architect-reviewer.agent.md) | `aws-architect` |
| agent | [`aws-architect`](../../cloud/provider/aws/aws-architect/.apm/agents/aws-architect.agent.md) | `aws-architect` |
| agent | [`aws-infrastructure-architect`](../../cloud/provider/aws/aws-architect/.apm/agents/aws-infrastructure-architect.agent.md) | `aws-architect` |
| command | [`/provision-aws-terraform`](../../cloud/terraform/terraform/README.md#provision-aws-terraform) | `terraform` |
| command | [`/technical-framework-researcher-terraform`](../../cloud/terraform/terraform/README.md#technical-framework-researcher-terraform) | `terraform` |
| command | [`/terraform-engineering-best-practices-researcher`](../../cloud/terraform/terraform/README.md#terraform-engineering-best-practices-researcher) | `terraform` |
| command | [`/terraform-instructions-compiler`](../../cloud/terraform/terraform/README.md#terraform-instructions-compiler) | `terraform` |
| command | [`/terraform-rules-author`](../../cloud/terraform/terraform/README.md#terraform-rules-author) | `terraform` |
| agent | [`aws-terraform-engineer`](../../cloud/terraform/terraform/.apm/agents/aws-terraform-engineer.agent.md) | `terraform` |
| agent | [`terraform-code-reviewer`](../../cloud/terraform/terraform/.apm/agents/terraform-code-reviewer.agent.md) | `terraform` |
| agent | [`terraform-rules-author`](../../cloud/terraform/terraform/.apm/agents/terraform-rules-author.agent.md) | `terraform` |
| command | [`/integrate-stripe-java`](../../java/libs/stripe-java/README.md#integrate-stripe-java) | `stripe-java` |
| command | [`/review-stripe-integration`](../../java/libs/stripe-java/README.md#review-stripe-integration) | `stripe-java` |
| agent | [`stripe-advisor`](../../java/libs/stripe-java/.apm/agents/stripe-advisor.agent.md) | `stripe-java` |
| agent | [`stripe-integrator`](../../java/libs/stripe-java/.apm/agents/stripe-integrator.agent.md) | `stripe-java` |
| command | [`/syncing-openspec-to-github`](../../delivery/specs/openspec-github/README.md#syncing-openspec-to-github) | `openspec-github` |
| agent | [`openspec-github-syncer`](../../delivery/specs/openspec-github/.apm/agents/openspec-github-syncer.agent.md) | `openspec-github` |
| inline orchestrator | [`bootstrapping-spec-from-poc`](../../delivery/specs/openspec-poc/README.md#bootstrapping-spec-from-poc) | `openspec-poc` |
| agent | [`poc-spec-extractor`](../../delivery/specs/openspec-poc/.apm/agents/poc-spec-extractor.agent.md) | `openspec-poc` |
| agent | [`solution-architect`](../../architecture/solution-architecture/.apm/agents/solution-architect.agent.md) | `solution-architecture` |
| agent | [`solution-architecture-reviewer`](../../architecture/solution-architecture/.apm/agents/solution-architecture-reviewer.agent.md) | `solution-architecture` |
| agent | [`ui-design-reviewer`](../../frontend/react/ui-design/.apm/agents/ui-design-reviewer.agent.md) | `ui-design` |
| agent | [`ui-ux-designer`](../../frontend/react/ui-design/.apm/agents/ui-ux-designer.agent.md) | `ui-design` |
| agent | [`nextjs-code-reviewer`](../../frontend/react/nextjs-frontend/.apm/agents/nextjs-code-reviewer.agent.md) | `nextjs-frontend` |
| agent | [`nextjs-frontend-integrator`](../../frontend/react/nextjs-frontend/.apm/agents/nextjs-frontend-integrator.agent.md) | `nextjs-frontend` |
| agent | [`langchain4j-reviewer`](../../java/quarkus/quarkus-langchain4j/.apm/agents/langchain4j-reviewer.agent.md) | `quarkus-langchain4j` |
| command | [`/building-cicd-pipelines`](../../delivery/github/github-actions-cicd/README.md#building-cicd-pipelines) | `github-actions-cicd` |
| agent | [`cicd-pipeline-engineer`](../../delivery/github/github-actions-cicd/.apm/agents/cicd-pipeline-engineer.agent.md) | `github-actions-cicd` |
| agent | [`cicd-pipeline-reviewer`](../../delivery/github/github-actions-cicd/.apm/agents/cicd-pipeline-reviewer.agent.md) | `github-actions-cicd` |
| agent | [`framework-researcher`](../../factory/research-core/.apm/agents/framework-researcher.agent.md) | `research-core` |
| agent | [`research-synthesizer`](../../factory/research-core/.apm/agents/research-synthesizer.agent.md) | `research-core` |
| agent | [`section-investigator`](../../factory/research-core/.apm/agents/section-investigator.agent.md) | `research-core` |
| command | [`/agent-creator`](../../factory/artifact-authoring/README.md#agent-creator) | `artifact-authoring` |
| command | [`/architecture-approaches-skill-generator`](../../factory/artifact-authoring/README.md#architecture-approaches-skill-generator) | `artifact-authoring` |
| command | [`/methodologies-skill-generator`](../../factory/artifact-authoring/README.md#methodologies-skill-generator) | `artifact-authoring` |
| command | [`/skill-creator`](../../factory/artifact-authoring/README.md#skill-creator) | `artifact-authoring` |
| agent | [`artifact-author`](../../factory/artifact-authoring/.apm/agents/artifact-author.agent.md) | `artifact-authoring` |

Plus 106 knowledge skills that Claude loads by description. Each package manual lists them.
<!-- END GENERATED:contents -->

## Installation

From the folder of the project that should receive the bundle:

```bash
apm install <path-to-agents-factory>/packages/bundles/saas-starter-team --target claude
```

Add `--dry-run` to preview. APM installs the packages listed above and their dependencies into `.claude/`.

To produce the folder and zip that are sold or shared, export the bundle from this repository:

```bash
python scripts/export-bundle.py saas-starter-team           # dry run
python scripts/export-bundle.py saas-starter-team --apply   # writes dist/saas-starter-team/ and the zip
```

The export holds the `.claude/` folder and a `docs/` folder with the usage manuals of the packages it
includes.

## Quick Start

```text
/building-aws-saas-serverless-quarkus-react-nextjs
```

Planning runs in your session. This bundle pulls the Vercel front-end skills transitively; they are free, third-party and not part of a paid export.

## Documentation

The usage manuals cover installation, quick start, usage scenarios, a command or skill reference,
agents and limits:

- [`aws-saas-serverless-quarkus-react-nextjs`](../../saas/aws-saas-serverless-quarkus-react-nextjs/README.md): usage manual.

See also the [package catalog](../../../docs/packages/README.md) and the
[entry points](../../../docs/entry-points/README.md).
