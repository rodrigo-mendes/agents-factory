# Packages

Every capability in the factory lives in an APM package under `packages/`. This page lists them by
family. Each package has its own README with its contents, dependencies, entry points and agents.

The tables below are generated from the package files. Do not edit them by hand.

## All packages

<!-- BEGIN GENERATED:packages-by-family -->
### architecture

| Package | Commands | Orchestrators | Knowledge | Agents | Rules |
|---|---|---|---|---|---|
| `solution-architecture` | 0 | 0 | 0 | 2 | 0 |

### cloud

| Package | Commands | Orchestrators | Knowledge | Agents | Rules |
|---|---|---|---|---|---|
| `aws-architect` | 1 | 0 | 0 | 3 | 2 |
| `aws-lambda` | 0 | 0 | 2 | 2 | 1 |
| `aws-observability` | 1 | 0 | 1 | 2 | 1 |
| `aws-skills` | 0 | 0 | 40 | 0 | 0 |
| `oci-architecture` | 2 | 0 | 6 | 2 | 2 |
| `oci-core` | 0 | 0 | 1 | 0 | 0 |
| `oci-functions-java` | 3 | 0 | 10 | 3 | 16 |
| `oci-observability` | 1 | 0 | 9 | 1 | 1 |
| `aws-terraform` | 0 | 0 | 26 | 0 | 3 |
| `oci-terraform` | 2 | 0 | 18 | 1 | 8 |
| `terraform` | 5 | 0 | 0 | 3 | 0 |

### content-generation

| Package | Commands | Orchestrators | Knowledge | Agents | Rules |
|---|---|---|---|---|---|
| `book-writing` | 10 | 0 | 0 | 13 | 0 |

### data-platform

| Package | Commands | Orchestrators | Knowledge | Agents | Rules |
|---|---|---|---|---|---|
| `kafka` | 0 | 0 | 8 | 0 | 1 |

### delivery

| Package | Commands | Orchestrators | Knowledge | Agents | Rules |
|---|---|---|---|---|---|
| `github-actions-cicd` | 1 | 0 | 9 | 2 | 4 |
| `github-core` | 0 | 0 | 2 | 0 | 0 |
| `handoff-core` | 1 | 0 | 1 | 1 | 0 |
| `openspec-core` | 0 | 0 | 1 | 0 | 1 |
| `openspec-github` | 1 | 0 | 1 | 1 | 1 |
| `openspec-poc` | 0 | 1 | 0 | 1 | 0 |

### factory

| Package | Commands | Orchestrators | Knowledge | Agents | Rules |
|---|---|---|---|---|---|
| `agent-package-builder` | 0 | 1 | 0 | 0 | 0 |
| `artifact-authoring` | 4 | 0 | 1 | 1 | 0 |
| `factory-core` | 0 | 0 | 0 | 0 | 5 |
| `package-docs` | 0 | 1 | 0 | 1 | 1 |
| `research-core` | 0 | 0 | 0 | 3 | 0 |
| `researching-frameworks` | 5 | 0 | 0 | 0 | 0 |
| `researching-platform` | 15 | 0 | 0 | 0 | 0 |

### frontend

| Package | Commands | Orchestrators | Knowledge | Agents | Rules |
|---|---|---|---|---|---|
| `nextjs-frontend` | 0 | 0 | 0 | 2 | 1 |
| `ui-design` | 0 | 0 | 0 | 2 | 0 |

### harness-quality

| Package | Commands | Orchestrators | Knowledge | Agents | Rules |
|---|---|---|---|---|---|
| `auditing` | 8 | 0 | 0 | 1 | 0 |
| `evaluating` | 1 | 0 | 0 | 1 | 0 |
| `validating` | 5 | 0 | 0 | 1 | 0 |

### java

| Package | Commands | Orchestrators | Knowledge | Agents | Rules |
|---|---|---|---|---|---|
| `clean-code-oci` | 0 | 0 | 1 | 0 | 1 |
| `clean-code-quarkus` | 0 | 0 | 1 | 0 | 1 |
| `langchain4j` | 0 | 0 | 3 | 1 | 2 |
| `stripe-java` | 2 | 0 | 4 | 2 | 1 |
| `camel-quarkus-integrator` | 0 | 1 | 1 | 1 | 3 |
| `camel-quarkus-skills` | 0 | 0 | 10 | 0 | 0 |
| `quarkus-aws` | 0 | 0 | 11 | 2 | 2 |
| `quarkus-core` | 0 | 0 | 3 | 0 | 0 |
| `quarkus-langchain4j` | 0 | 0 | 1 | 1 | 0 |

### quality

| Package | Commands | Orchestrators | Knowledge | Agents | Rules |
|---|---|---|---|---|---|
| `acceptance-testing` | 0 | 0 | 1 | 1 | 1 |
| `quarkus-acceptance-testing` | 1 | 0 | 2 | 1 | 1 |

### saas

| Package | Commands | Orchestrators | Knowledge | Agents | Rules |
|---|---|---|---|---|---|
| `aws-saas-serverless-quarkus-react-nextjs` | 0 | 1 | 2 | 0 | 0 |

### third-party

| Package | Commands | Orchestrators | Knowledge | Agents | Rules |
|---|---|---|---|---|---|
| `vercel-frontend` | 0 | 0 | 0 | 0 | 0 |
<!-- END GENERATED:packages-by-family -->

## Families

| Family | Purpose |
|---|---|
| `factory/` | Build artifacts: research, authoring, the package builder. |
| `harness-quality/` | Check artifacts: audits, validators, evaluations. |
| `content-generation/` | The technical book pipeline. |
| `architecture/` | Solution architecture for SaaS work. |
| `cloud/` | Terraform and provider knowledge for AWS and OCI. |
| `data-platform/` | Streaming and data-platform knowledge (Kafka). |
| `delivery/` | Handoff protocol, OpenSpec and GitHub delivery. |
| `java/` | Quarkus, Camel Quarkus, LangChain4j, Stripe and Java clean code. |
| `quality/` | Acceptance testing from specs. |
| `frontend/` | React and Next.js frontend work. |
| `third-party/` | Upstream Vercel skills, installed from their repositories. |
| `saas/` | The Quarkus, AWS Lambda and Next.js SaaS orchestrator. |
| `bundles/` | Sales meta-packages, not counted as packages. |

## Bundles

Bundles are dependency lists that group packages for a sale. Each one has an `apm.yml` and a README
that links to the manuals of the packages it contains. They are not part of the root manifest. See
[the bundle strategy](../commercial/bundle-strategy.md).

<!-- BEGIN GENERATED:bundles -->
| Bundle | Packages | Subset export |
|---|---|---|
| [`ai-code-review-squad`](../../packages/bundles/ai-code-review-squad/README.md) | `quarkus-langchain4j`, `terraform`, `github-actions-cicd`, `stripe-java` | yes |
| [`anti-hallucination-research`](../../packages/bundles/anti-hallucination-research/README.md) | `researching-frameworks`, `researching-platform` | no |
| [`architecture-board`](../../packages/bundles/architecture-board/README.md) | `solution-architecture`, `aws-architect`, `oci-architecture` | no |
| [`aws-terraform-complete`](../../packages/bundles/aws-terraform-complete/README.md) | `terraform` | no |
| [`aws-well-architected-reviewer`](../../packages/bundles/aws-well-architected-reviewer/README.md) | `aws-architect` | no |
| [`camel-quarkus-integration`](../../packages/bundles/camel-quarkus-integration/README.md) | `camel-quarkus-integrator` | no |
| [`cloud-observability`](../../packages/bundles/cloud-observability/README.md) | `aws-observability`, `oci-observability` | no |
| [`github-actions-secure-cicd`](../../packages/bundles/github-actions-secure-cicd/README.md) | `github-actions-cicd` | no |
| [`harness-quality-kit`](../../packages/bundles/harness-quality-kit/README.md) | `auditing`, `validating`, `evaluating` | no |
| [`java-ai-langchain4j`](../../packages/bundles/java-ai-langchain4j/README.md) | `langchain4j`, `quarkus-langchain4j` | no |
| [`java-clean-code`](../../packages/bundles/java-clean-code/README.md) | `clean-code-quarkus`, `clean-code-oci` | no |
| [`multi-cloud-terraform`](../../packages/bundles/multi-cloud-terraform/README.md) | `terraform`, `oci-terraform` | no |
| [`oci-serverless-complete`](../../packages/bundles/oci-serverless-complete/README.md) | `oci-functions-java`, `oci-observability`, `oci-architecture`, `oci-terraform` | no |
| [`saas-starter-team`](../../packages/bundles/saas-starter-team/README.md) | `aws-saas-serverless-quarkus-react-nextjs` | no |
| [`serverless-java-aws`](../../packages/bundles/serverless-java-aws/README.md) | `quarkus-aws`, `aws-lambda` | no |
| [`skill-factory-pro`](../../packages/bundles/skill-factory-pro/README.md) | `agent-package-builder`, `package-docs`, `artifact-authoring`, `researching-frameworks` | no |
| [`spec-driven-delivery`](../../packages/bundles/spec-driven-delivery/README.md) | `openspec-github` | no |
| [`stripe-for-java`](../../packages/bundles/stripe-for-java/README.md) | `stripe-java` | no |
| [`technical-book-author`](../../packages/bundles/technical-book-author/README.md) | `book-writing` | no |
<!-- END GENERATED:bundles -->
