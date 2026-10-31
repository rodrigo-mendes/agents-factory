# packages/

Source of truth for every skill, subagent and rule in this repo: 40 APM packages grouped in family
folders, plus 19 sales bundles. `.claude/` is generated from here by `apm install --target claude`.

Layout: `packages/<family>[/<sub>]/<package>/`. Each package has its own `apm.yml` and its content
under `.apm/` (`skills/`, `agents/`, `instructions/`). A bundle has only an `apm.yml`.

## Families

```
packages/
├── factory/                     building artifacts
│   ├── factory-core               frontmatter and naming rules (base of everything)
│   ├── research-core              framework-researcher + internal helpers
│   ├── researching-frameworks     5 generic research commands
│   ├── researching-platform       15 platform-software research commands
│   ├── artifact-authoring         artifact-author + skill/agent/rule authoring
│   └── agent-package-builder      research → skills → agent/rules → quality → commit
├── harness-quality/             checking artifacts
│   ├── auditing                   architecture-auditor + 8 audit commands
│   ├── validating                 quality-validator + 5 validation commands
│   └── evaluating                 skill-evaluator (LLM-as-judge scenarios)
├── content-generation/
│   └── book-writing               technical book pipeline (13 agents)
├── architecture/
│   └── solution-architecture      solution-architect + reviewer
├── cloud/
│   ├── terraform/                 IaC for every provider
│   │   ├── terraform                aws-terraform-engineer, terraform-rules-author
│   │   ├── aws-terraform            26 provisioning-aws-<service>-v6 skills
│   │   └── oci-terraform            OCI provisioning + oci-terraform agent
│   └── provider/
│       ├── aws/                     aws-skills, aws-architect, aws-lambda, aws-observability
│       └── oci/                     oci-core, oci-functions-java, oci-observability, oci-architecture
├── delivery/
│   ├── protocol/handoff-core      handoff protocol v1 + scripts
│   ├── specs/                     openspec-core, openspec-github
│   └── github/                    github-core, github-actions-cicd
├── java/
│   ├── quarkus/                   quarkus-core, quarkus-aws, quarkus-langchain4j,
│   │                              camel-quarkus-skills, camel-quarkus-integrator
│   ├── clean-code/                clean-code-quarkus, clean-code-oci (one per stack)
│   └── libs/                      langchain4j, stripe-java
├── frontend/react/              nextjs-frontend, ui-design
├── third-party/vercel-frontend  points to 7 official Vercel skill repositories (not our content)
├── saas/                        aws-saas-serverless-quarkus-react-nextjs (orchestrator)
└── bundles/                     19 sales meta-packages (apm.yml only; one also has export.yml)
```

## Dependency map

Each layer depends only on the layers below it. `factory-core` is a dependency of every package
except `vercel-frontend`, so it is left out of the lists.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 5 · ORCHESTRATOR                                                   │
│   saas/aws-saas-serverless-quarkus-react-nextjs                          │
└──────────────────────────────────────────────────────────────────────────┘
                 ▲ uses 14 packages from the layers below
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 4 · SPECIALISED EXECUTORS                                          │
│   aws-lambda            quarkus-langchain4j                              │
│   oci-functions-java    oci-terraform        camel-quarkus-integrator    │
│   oci-observability     oci-architecture                                 │
└──────────────────────────────────────────────────────────────────────────┘
                 ▲
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 3 · DOMAIN AGENTS                                                  │
│   terraform             aws-architect        aws-observability           │
│   quarkus-aws           oci-core             solution-architecture       │
│   nextjs-frontend       ui-design            openspec-github             │
│   camel-quarkus-skills                                                   │
└──────────────────────────────────────────────────────────────────────────┘
                 ▲
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 2 · PROTOCOLS AND COMPOSED PACKAGES                                │
│   handoff-core          researching-frameworks   researching-platform    │
│   github-actions-cicd   quarkus-core                                     │
└──────────────────────────────────────────────────────────────────────────┘
                 ▲
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 1 · LEAF PACKAGES (depend only on factory-core)                    │
│   research-core    artifact-authoring   agent-package-builder            │
│   clean-code-quarkus    clean-code-oci                                   │
│   auditing         validating           evaluating                       │
│   book-writing     langchain4j          stripe-java                      │
│   aws-skills       aws-terraform                                         │
│   openspec-core    github-core                                           │
└──────────────────────────────────────────────────────────────────────────┘
                 ▲
┌──────────────────────────────────────────────────────────────────────────┐
│ LAYER 0 · BASE                                                           │
│   factory-core        vercel-frontend (third party, no dependencies)     │
└──────────────────────────────────────────────────────────────────────────┘
```

Direct dependencies, read as "package → needs":

```
FACTORY
  researching-frameworks   → research-core
  researching-platform     → research-core

ARCHITECTURE
  solution-architecture    → handoff-core

CLOUD / TERRAFORM
  terraform                → aws-terraform, research-core, artifact-authoring, handoff-core
  oci-terraform            → oci-core

CLOUD / PROVIDER / AWS
  aws-architect            → aws-skills, handoff-core
  aws-observability        → aws-skills, aws-terraform, handoff-core
  aws-lambda               → aws-skills, aws-terraform, aws-observability, handoff-core

CLOUD / PROVIDER / OCI
  oci-core                 → handoff-core
  oci-functions-java       → oci-core, clean-code-oci
  oci-observability        → oci-core
  oci-architecture         → oci-core

DELIVERY
  handoff-core             → openspec-core
  openspec-github          → openspec-core, handoff-core, github-core
  github-actions-cicd      → github-core

JAVA / QUARKUS
  quarkus-core             → clean-code-quarkus
  camel-quarkus-skills     → quarkus-core
  camel-quarkus-integrator → camel-quarkus-skills
  quarkus-aws              → quarkus-core, aws-skills, handoff-core
  quarkus-langchain4j      → quarkus-aws

FRONTEND / REACT
  nextjs-frontend          → vercel-frontend, handoff-core
  ui-design                → vercel-frontend, handoff-core

SAAS
  aws-saas-serverless-quarkus-react-nextjs
                           → quarkus-aws, quarkus-langchain4j, aws-lambda, aws-observability,
                             aws-architect, terraform, stripe-java, solution-architecture,
                             ui-design, nextjs-frontend, vercel-frontend, openspec-github,
                             github-actions-cicd, handoff-core
```

All other packages need only `factory-core`.

`handoff-core` is the hub that crosses families: `cloud`, `architecture`, `frontend`, `java/quarkus`
and `saas` all depend on it.

## Rules for dependencies

- A package cites its dependencies with a relative path from its own folder
  (`cloud/provider/aws/aws-lambda` → `../../../../factory/factory-core`). Different packages can cite
  the same dependency with different texts; APM 0.35.0 accepts this (tested 2026-10-31).
- The root `apm.yml` lists only top-level packages. Never add one that is already reached
  transitively: `apm audit --ci` fails with "ambiguous resolved_by".
- Bundles are not listed in the root `apm.yml` for the same reason.

## Bundles

`bundles/<name>/apm.yml` groups whole packages into a product for sale. It has no `.apm/` content and
lists only the top-level packages of the product; the rest comes transitively.

An optional `bundles/<name>/export.yml` (ignored by APM, read by `scripts/export-bundle.py`) cuts what
is sold out of what is installed: `agents` / `skills` / `rules` take a list of names, `cited` or `all`
(default), plus `include` / `exclude` paths. Only `ai-code-review-squad` uses it.

Export for sale (compiled target dir as a folder + zip, Vercel removed, sensitive-data detectors):
`python scripts/export-bundle.py <bundle> --apply`. Catalog, prices and publishing steps:
[docs/comercial/estrategia-bundles.md](../docs/comercial/estrategia-bundles.md).

## Moving or adding a package

- New package: create `packages/<family>/<name>/apm.yml` + `.apm/`, cite its dependencies with
  relative paths, add it to the root `apm.yml` only if nothing else depends on it.
- Moving packages: `scripts/reorganize-packages.py` did this layout (flat → families, 2026-10-31). Its
  `FAMILY` map can be edited for a later move only if the source folders are flat again; otherwise use
  `git mv`, fix every `path:` that cites the package, and run `apm install --target claude`.
