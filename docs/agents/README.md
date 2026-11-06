# Subagents

A subagent is a worker with its own instructions, its own tools and a fixed model. Commands and
orchestrators start subagents; you rarely start one yourself.

For how subagents are started and how they talk to each other, read
[Agent architecture](architecture.md). For the commands that start them, see
[Entry points](../entry-points/README.md).

## Roster

Generated from the agent files. Do not edit these tables by hand.

<!-- BEGIN GENERATED:agents-roster -->
| Agent | Package | Model | Started by | What it does |
|---|---|---|---|---|
| `solution-architect` | `solution-architecture` | opus | other agents or an orchestrator | Solution Architect - non-interactive designer of the logical solution of a SaaS on AWS: pieces (screens, API, Lambdas, data, queues and events, AI, observability), contracts between them, data model,… |
| `solution-architecture-reviewer` | `solution-architecture` | sonnet | other agents or an orchestrator | Solution Architecture Reviewer - independent, read-only verifier of the solution architecture (E2a) and of each technical design of a change (E4: one design per flow, plus the index and its requireme… |
| `aws-architect-reviewer` | `aws-architect` | sonnet | other agents or an orchestrator | AWS Architect Reviewer - independent, read-only verifier of the infrastructure design (infrastructure/spec.md at E2c, infra-design.md of a change at E4). |
| `aws-architect` | `aws-architect` | sonnet | `/aws-architecture-advisor` | AWS Architecture Advisor — reviews, designs, and evaluates AWS architectures using the 40 aws-skills knowledge base (WAF six pillars, security, networking, serverless, data stores, messaging, observa… |
| `aws-infrastructure-architect` | `aws-architect` | opus | other agents or an orchestrator | AWS Infrastructure Architect - non-interactive designer of the AWS infrastructure where the pieces of an already reviewed solution architecture run, before anyone writes Terraform: accounts and envir… |
| `aws-lambda-debugger` | `aws-lambda` | sonnet | other agents or an orchestrator | AWS Lambda Debugger - non-interactive, read-only, runtime-agnostic diagnoser for deployed AWS Lambda Event Functions. |
| `aws-lambda-deployer` | `aws-lambda` | sonnet | other agents or an orchestrator | AWS Lambda Deployer - non-interactive, runtime-agnostic executor that releases an already-built Lambda .zip through a Terraform saved plan, applies ONLY a plan the user approved (approval line relaye… |
| `aws-observability` | `aws-observability` | sonnet | `/observe-aws-workload` | AWS Observability Engineer (non-interactive executor) — reviews the observability section of an architecture spec, writes observability Terraform for AWS Lambda workloads (log groups and retention, m… |
| `static-site-verifier` | `aws-observability` | sonnet | other agents or an orchestrator | Static Site Verifier - non-interactive, read-only verifier of a static front end published on S3 behind CloudFront after the pipeline deployed it. |
| `oci-serverless-architect` | `oci-architecture` | sonnet | `/design-oci-architecture` | OCI Serverless Solution Architect — designs and reviews OCI serverless architectures (Functions, API Gateway, networking, Vault/IAM, Object Storage, Streaming pub/sub) by reasoning over 6 architectur… |
| `oci-serverless-stack` | `oci-architecture` | sonnet | `/provision-oci-serverless-stack` | Full-Stack Serverless Deployer — validates the three work-orders of an end-to-end OCI serverless capability (Java function + Terraform infra + API Gateway route), hands streams A and B to their agent… |
| `oci-debugger` | `oci-functions-java` | sonnet | `/debug-oci-function` | OCI Function Debugger — diagnoses runtime issues in deployed functions using systematic elimination by HTTP status code (P0-P4 diagnostic workflow). |
| `oci-deployer` | `oci-functions-java` | sonnet | `/deploy-oci-function` | OCI Function Deployer — orchestrates build, push, deploy, and validation of OCI Functions on existing infrastructure following a P0-P6 workflow. |
| `oci-functions-java` | `oci-functions-java` | sonnet | `/develop-java-function` | OCI Functions Java Developer — orchestrates Java function development with FDK v1.1.x following a 6-step workflow (P0-P5) with skill-driven patterns. |
| `oci-observability` | `oci-observability` | sonnet | `/observe-oci-workload` | OCI Observability Engineer — designs, provisions, and validates infra-level observability for OCI serverless (APM & distributed tracing, Logging, Monitoring alarms, Connector Hub pipelines, Managemen… |
| `oci-terraform` | `oci-terraform` | sonnet | `/cleaning-up-oci-resources`, `/provision-oci-infra` | OCI Infrastructure Provisioner — orchestrates Terraform provisioning of OCI serverless resources following a 6-step workflow (P0-P5) with skill-driven patterns. |
| `aws-terraform-engineer` | `terraform` | sonnet | `/provision-aws-terraform` | AWS Terraform Engineer - non-interactive executor that writes or reviews HCL for a CLOSED AWS requirement (hashicorp/aws 6.x), using only the matching provisioning-aws-<service>-v6 skills. |
| `terraform-code-reviewer` | `terraform` | sonnet | other agents or an orchestrator | Terraform Code Reviewer - independent, read-only reviewer (step I7) of the HCL written by aws-terraform-engineer (infra) or aws-observability (observability). |
| `terraform-rules-author` | `terraform` | sonnet | `/terraform-rules-author` | Terraform Rules Author — non-interactive executor that generates scoped Terraform rules/instruction files for a target project, given a Terraform research file and project context. |
| `book-formatter` | `book-writing` | sonnet | `/formatting-book-epub` | Technical Book EPUB 3.0 Formatter — converts a language-specific book.md into a valid EPUB 3.0 source tree (OEBPS structure) ready for zip and upload to Amazon KDP. |
| `book-orchestrator` | `book-writing` | opus | `/enriching-book-chapter`, `/rewriting-book-chapter`, `/rewriting-book-introduction` +3 more | Technical Book Writing Orchestrator — generates a complete technical book through a 7-phase pipeline (TOC research, introduction writing, chapter writing, parallel asset generation, assembly, narrati… |
| `book-translator` | `book-writing` | sonnet | `/translating-book` | Technical Book Translator — translates a completed book.md to a target language (pt-BR or es) while preserving all Markdown formatting, code blocks, and Mermaid diagrams in English. |
| `chapter-assembler` | `book-writing` | sonnet | other agents or an orchestrator | Technical Book Chapter Assembler — merges prose, code examples, Mermaid diagrams, expert notes, and skeptical review notes into a single coherent chapter.md file. |
| `chapter-enricher` | `book-writing` | sonnet | other agents or an orchestrator | Technical Book Chapter Enricher — infers [CODE:] and [DIAGRAM:] injection points in external unstructured prose using heuristic rules and writes an enriched prose.md with markers inserted and origina… |
| `chapter-writer` | `book-writing` | opus | other agents or an orchestrator | Technical Book Chapter Writer — writes audience-calibrated prose for a single book chapter, inserting [CODE:] and [DIAGRAM:] markers at injection points for downstream asset agents. |
| `code-illustrator` | `book-writing` | sonnet | other agents or an orchestrator | Technical Book Code Illustrator — generates code examples, algorithms, and pseudocode for a single book chapter by resolving [CODE:] markers from chapter prose. |
| `code-validator` | `book-writing` | sonnet | other agents or an orchestrator | Technical Book Code Validator — reviews code.md for language consistency, generates missing language blocks for additional_languages, and attempts to compile/execute each real code block. |
| `diagram-illustrator` | `book-writing` | sonnet | other agents or an orchestrator | Technical Book Diagram Illustrator — generates Mermaid diagrams for a single book chapter by resolving [DIAGRAM:] markers from chapter prose. |
| `epub-repairer` | `book-writing` | sonnet | `/repairing-book-epub` | EPUB 3.0 Validator and Repairer — validates generated .epub files against the ZIP/EPUB spec and repacks any that fail using the canonical build-epub.py blueprint. |
| `expert-reviewer` | `book-writing` | sonnet | other agents or an orchestrator | Technical Book Expert Reviewer — reviews a chapter's prose as a senior domain practitioner and produces prioritized annotations (💡 Expert Note callouts) for integration by chapter-assembler. |
| `mermaid-renderer` | `book-writing` | sonnet | `/rendering-mermaid-diagrams` | Mermaid Diagram Renderer — converts Mermaid blocks in a completed book.md into PNG images via the Mermaid CLI and rewrites the file with image references. |
| `skeptic-reviewer` | `book-writing` | sonnet | other agents or an orchestrator | Technical Book Skeptical Reviewer — reviews a chapter's prose as a rigorous skeptic and produces critical challenge notes (⚠️ Critical Note callouts) for integration by chapter-assembler. |
| `cicd-pipeline-engineer` | `github-actions-cicd` | sonnet | `/building-cicd-pipelines` | CI/CD Pipeline Engineer - non-interactive executor that writes or fixes GitHub Actions workflows (.github/workflows/**) and composite actions (.github/actions/**) for a CLOSED requirement, loading on… |
| `cicd-pipeline-reviewer` | `github-actions-cicd` | sonnet | other agents or an orchestrator | CI/CD Pipeline Reviewer - read-only advisor that audits existing GitHub Actions workflows (.github/workflows/**) and composite actions (.github/actions/**) against the nine github-actions-cicd knowle… |
| `spec-synchronizer` | `handoff-core` | sonnet | `/syncing-spec-from-code` | Spec Synchronizer - reviews a spec (gaps, contradictions, testability, conflicts with accepted ADRs) and proposes OpenSpec spec-deltas when code has drifted from the spec. |
| `openspec-github-syncer` | `openspec-github` | sonnet | `/syncing-openspec-to-github` | OpenSpec GitHub Syncer - non-interactive executor that mirrors one OpenSpec change into its GitHub Project with gh_projects_sync.py (push and status only) and reports PLAN or applied lines, exit code… |
| `poc-spec-extractor` | `openspec-poc` | sonnet | other agents or an orchestrator | POC Spec Extractor - read-only drafter that turns the source code of a proof of concept (back end and/or front end, any stack) plus its inventory (poc_inventory.py output) into a draft spec bundle: O… |
| `artifact-author` | `artifact-authoring` | sonnet | `/terraform-instructions-compiler`, `/agent-creator`, `/architecture-approaches-skill-generator` +2 more | Skill & Instructions Author — turns validated research into production-ready SKILL.md and rules/instructions artifacts following official Claude best practices and team conventions. |
| `package-manual-author` | `package-docs` | sonnet | other agents or an orchestrator | Package Manual Author - non-interactive writer that turns the files of one or more APM packages into usage manuals (README.md): installation, quick start, usage scenarios, a command or skill referenc… |
| `framework-researcher` | `research-core` | opus | `/technical-framework-researcher-terraform`, `/terraform-engineering-best-practices-researcher`, `/architecture-methodology-researcher` +19 more | Technical/Framework/Cloud/Domain Researcher — builds hallucination-proof, version-absolute knowledge bases from official documentation. |
| `research-synthesizer` | `research-core` | sonnet | other agents or an orchestrator | Research Merge & Format Enforcement Agent — receives raw findings from parallel section-investigators and assembles them into the mandatory output-format skeleton for a research knowledge base. |
| `section-investigator` | `research-core` | sonnet | other agents or an orchestrator | Lightweight parallel sub-investigator for a single research section. |
| `nextjs-code-reviewer` | `nextjs-frontend` | sonnet | other agents or an orchestrator | Next.js Code Reviewer - independent, read-only reviewer (step I7) of the front-end diff produced by nextjs-frontend-integrator for a Next.js static export (S3 + CloudFront). |
| `nextjs-frontend-integrator` | `nextjs-frontend` | sonnet | other agents or an orchestrator | Next.js Frontend Integrator - non-interactive executor that implements ONE closed front-end task of a SaaS (Next.js static export on S3 + CloudFront, React, pnpm, Node 26) from a work-order: tests fi… |
| `ui-design-reviewer` | `ui-design` | sonnet | other agents or an orchestrator | UI Design Reviewer - independent, read-only reviewer of design and of its implementation: the design system and design ADRs (E2b), the wireframes and navigation (E3b) and the fidelity of the built fr… |
| `ui-ux-designer` | `ui-design` | sonnet | other agents or an orchestrator | UI/UX Designer - non-interactive, read-only designer of the product look and use: the design system with light and dark tokens and contrast, component states, design ADRs (E2b) and wireframes with na… |
| `architecture-auditor` | `auditing` | opus | `/audit-architecture-consensus`, `/audit-architecture-engine`, `/audit-architecture-flow` +5 more | Agent-Architecture Auditor — audits an agent project (scope hierarchy, invocation flow, engine mechanics) and produces a compliance report with scoring and remediation. |
| `skill-evaluator` | `evaluating` | sonnet | `/evaluating-skill-scenarios` | Skill Behavioral Evaluator — executes evaluation scenarios from a skill's blueprints/evaluation-scenarios.md by invoking the skill under test and applying LLM-as-judge to check responses against must… |
| `quality-validator` | `validating` | sonnet | `/agent-router-pattern-validator`, `/copilot-compatibility-review`, `/instructions-best-practices-validator` +2 more | Quality & Best-Practices Validator — analyzes skills, rules/instructions, agent-router compliance, Copilot-compatibility, or a complete agent project against official docs and team conventions, and e… |
| `langchain4j-integrator` | `langchain4j` | sonnet | other agents or an orchestrator | LangChain4j Integrator — non-interactive executor that implements or reviews a CLOSED LangChain4j 1.22.0 chat + streaming requirement in plain Java with OpenAI and/or Anthropic providers. |
| `stripe-advisor` | `stripe-java` | sonnet | `/review-stripe-integration` | Stripe Java Integration Advisor — read-only reviewer that audits and guides a Stripe Java integration against the four stripe-java v34 knowledge skills. |
| `stripe-integrator` | `stripe-java` | sonnet | `/integrate-stripe-java` | Stripe Java Integrator — non-interactive executor that implements a CLOSED Stripe Java integration (PaymentIntent flow, webhook endpoint, subscription, idempotent calls) in a target Java project usin… |
| `camel-quarkus-integrator` | `camel-quarkus-integrator` | sonnet | other agents or an orchestrator | Camel Quarkus Integrator — non-interactive executor that implements a CLOSED integration requirement (routes, REST endpoints, HTTP clients, file processing, XML/XSLT transformation, tests) in a Camel… |
| `quarkus-code-reviewer` | `quarkus-aws` | sonnet | other agents or an orchestrator | Quarkus Code Reviewer — independent, read-only reviewer (step I7) of the diff produced by quarkus-lambda-integrator. |
| `quarkus-lambda-integrator` | `quarkus-aws` | sonnet | other agents or an orchestrator | Quarkus Lambda Integrator — non-interactive executor that implements ONE closed task of a Quarkus 3.40 on AWS Lambda project from a work-order record: tests first, minimal implementation, refinement,… |
| `langchain4j-reviewer` | `quarkus-langchain4j` | sonnet | other agents or an orchestrator | LangChain4j Reviewer - independent, read-only reviewer (step I7) of AI code written with quarkus-langchain4j 1.15.0.CR1 on Quarkus Lambda. |
| `acceptance-test-reviewer` | `acceptance-testing` | sonnet | other agents or an orchestrator | Acceptance Test Reviewer - read-only, non-interactive reviewer that checks Gherkin .feature files against an OpenSpec spec or change delta and, when given, against step definitions. |
| `acceptance-test-engineer` | `quarkus-acceptance-testing` | sonnet | `/building-acceptance-tests` | Acceptance Test Engineer - non-interactive executor that derives Gherkin features from an OpenSpec change or spec root and implements Cucumber 8.0 acceptance tests in a Quarkus 3.40 project (step def… |
<!-- END GENERATED:agents-roster -->

"Started by" lists the commands whose `agent:` field names the subagent. Agents with no command are
started by an orchestrator or by another agent.

## Tools per agent

Read-only reviewers have no `Write` or `Edit`. Only four agents can start other agents (`Agent`).

<!-- BEGIN GENERATED:agents-tools -->
| Agent | Read | Grep | Glob | Edit | Write | Bash | WebSearch | WebFetch | Agent |
|---|---|---|---|---|---|---|---|---|---|
| `solution-architect` | x | x | x |  | x |  |  |  |  |
| `solution-architecture-reviewer` | x | x | x |  |  |  |  |  |  |
| `aws-architect-reviewer` | x | x | x |  |  |  |  |  |  |
| `aws-architect` | x | x | x |  |  |  |  |  |  |
| `aws-infrastructure-architect` | x | x | x |  | x |  |  |  |  |
| `aws-lambda-debugger` | x | x | x |  |  | x |  |  |  |
| `aws-lambda-deployer` | x | x | x |  | x | x |  |  |  |
| `aws-observability` | x | x | x | x | x | x |  |  |  |
| `static-site-verifier` | x | x | x |  |  | x |  |  |  |
| `oci-serverless-architect` | x | x | x |  | x |  |  |  |  |
| `oci-serverless-stack` | x | x | x | x | x | x |  |  |  |
| `oci-debugger` | x | x | x |  | x | x |  |  |  |
| `oci-deployer` | x | x | x | x | x | x |  |  |  |
| `oci-functions-java` | x | x | x | x | x | x |  |  |  |
| `oci-observability` | x | x | x | x | x | x |  |  |  |
| `oci-terraform` | x | x | x | x | x | x |  |  |  |
| `aws-terraform-engineer` | x | x | x | x | x | x |  |  |  |
| `terraform-code-reviewer` | x | x | x |  |  |  |  |  |  |
| `terraform-rules-author` | x | x | x | x | x |  |  |  |  |
| `book-formatter` | x |  |  |  | x |  |  |  |  |
| `book-orchestrator` | x | x | x |  | x | x | x | x | x |
| `book-translator` | x |  |  |  | x |  |  |  |  |
| `chapter-assembler` | x |  |  |  | x |  |  |  |  |
| `chapter-enricher` | x |  |  |  | x |  |  |  |  |
| `chapter-writer` | x |  |  |  | x |  |  |  |  |
| `code-illustrator` | x |  |  |  | x |  |  |  |  |
| `code-validator` | x |  |  |  | x | x |  |  |  |
| `diagram-illustrator` | x |  |  |  | x |  |  |  |  |
| `epub-repairer` | x |  |  |  |  | x |  |  |  |
| `expert-reviewer` | x |  |  |  | x |  |  |  |  |
| `mermaid-renderer` | x |  |  |  |  | x |  |  |  |
| `skeptic-reviewer` | x |  |  |  | x |  |  |  |  |
| `cicd-pipeline-engineer` | x | x | x | x | x | x |  |  |  |
| `cicd-pipeline-reviewer` | x | x | x |  |  |  |  |  |  |
| `spec-synchronizer` | x | x | x |  |  | x |  |  |  |
| `openspec-github-syncer` | x | x | x |  |  | x |  |  |  |
| `poc-spec-extractor` | x | x | x |  |  | x |  |  |  |
| `artifact-author` | x | x | x | x | x |  |  |  |  |
| `package-manual-author` | x | x | x | x | x | x |  |  |  |
| `framework-researcher` | x | x | x |  | x |  | x | x | x |
| `research-synthesizer` | x | x |  |  | x |  |  |  |  |
| `section-investigator` |  |  |  |  |  |  | x | x |  |
| `nextjs-code-reviewer` | x | x | x |  |  |  |  |  |  |
| `nextjs-frontend-integrator` | x | x | x | x | x | x |  |  |  |
| `ui-design-reviewer` | x | x | x |  |  |  |  |  |  |
| `ui-ux-designer` | x | x | x |  |  |  |  |  |  |
| `architecture-auditor` | x | x | x |  | x | x |  |  | x |
| `skill-evaluator` | x | x | x | x | x |  |  |  | x |
| `quality-validator` | x | x | x |  | x |  |  |  |  |
| `langchain4j-integrator` | x | x | x | x | x | x |  |  |  |
| `stripe-advisor` | x | x | x |  |  |  |  |  |  |
| `stripe-integrator` | x | x | x | x | x | x |  |  |  |
| `camel-quarkus-integrator` | x | x | x | x | x | x |  |  |  |
| `quarkus-code-reviewer` | x | x | x |  |  |  |  |  |  |
| `quarkus-lambda-integrator` | x | x | x | x | x | x |  |  |  |
| `langchain4j-reviewer` | x | x | x |  |  |  |  |  |  |
| `acceptance-test-reviewer` | x | x | x |  |  | x |  |  |  |
| `acceptance-test-engineer` | x | x | x | x | x | x |  |  |  |
<!-- END GENERATED:agents-tools -->

## Detailed manuals for the factory agents

These pages describe the seven factory agents in depth. They are being rewritten and may still
mention the retired GitHub Copilot setup.

- [framework-researcher](framework-researcher.md)
- [artifact-author](artifact-author.md)
- [architecture-auditor](architecture-auditor.md)
- [quality-validator](quality-validator.md)
- [skill-evaluator](skill-evaluator.md)
- [research-synthesizer](research-synthesizer.md)
- [section-investigator](section-investigator.md)

Domain agents (OCI, AWS, Quarkus, Stripe and others) are described in the README of their package.
See [Packages](../packages/README.md).
