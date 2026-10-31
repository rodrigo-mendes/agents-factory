# Agents Factory — CLAUDE.md

AI artifact factory (**Skills, Subagents, Rules**) with an **anti-hallucination** focus. This
repository **produces** artifacts for code agents and **also runs on Claude Code**: operational
prompts are exposed as skills/commands that fork to subagents.

> **`.claude/` is the only source of truth — there is no `.github/`.** The pre-migration Copilot
> mirror was retired (see `.claude/MIGRATION.md`, Copilot Decommission). `audit-architecture-*`
> and `copilot-compatibility-review` still exist as generic tools for auditing *other* projects
> that target Copilot — they are not about this repo's own state.

## Principles (non-negotiable)

- **Version Absolutism** — 1 skill = 1 version; treat old versions as misinformation.
- **Source Hierarchy** — official doc/registry > official blog > official examples > verified
  community > reject the rest. Reject sources > 12 months old unless they are the current stable.
- **Executable Truth** — every claim links to a dated official source; without a source, mark as "unverified".
- **Workflow P0–P5** — Verify Docs → Analyze → Consult → Propose → Implement → Validate.
- **Three-Tier** — ✅ Always-Do · ⚠️ Ask-First · 🚫 Never-Do (with alternative).
- **Progressive disclosure** — `SKILL.md` lean (< 500 lines) linking blueprints; templates live in
  the `assets/` of the skill that owns them (no `.claude/templates/` — see Structure below).

## Naming conventions (kebab-case)

| Artifact | Pattern | Example |
|---|---|---|
| Skill — knowledge (auto-invocable, no `context: fork`) | `gerund-noun` | `researching-technical-frameworks` |
| Skill — action command (`context: fork`, routes to a subagent) | `action-noun` / `domain-role` | `cloud-architecture-researcher`, `skill-best-practices-validator` |
| Subagent | `domain-role` | `framework-researcher` |
| Rule | `scope-noun` | `skill-frontmatter` |

> Both skill kinds live under `.claude/skills/` — the distinction is the frontmatter shape (see
> [`skill-frontmatter.md`](.claude/rules/skill-frontmatter.md) and
> [`skill-creator/assets/TEMPLATE.KNOWLEDGE-SKILL.md`](.claude/skills/skill-creator/assets/TEMPLATE.KNOWLEDGE-SKILL.md) vs
> [`skill-creator/assets/TEMPLATE.SKILL.md`](.claude/skills/skill-creator/assets/TEMPLATE.SKILL.md)), not a separate folder.

## Routing — Skill (`/command`) → Subagent → Skills

Operational commands fork (`context: fork`) to a subagent. The 5 **routing-level** subagents
(directly invoked by a `/command`) live in [.claude/agents/](.claude/agents/):

| Subagent | Does | Commands it routes |
|---|---|---|
| [framework-researcher](.claude/agents/framework-researcher.md) | anti-hallucination research (uses WebSearch/WebFetch) | `researching-technical-frameworks`, `technical-framework-researcher-terraform`, `cloud-architecture-researcher`, `business-domain-researcher`, `requirements-methodology-researcher`, `architecture-methodology-researcher`, `terraform-engineering-best-practices-researcher`, **platform-software family** (orchestrator `researching-platform-software` → siblings: `researching-streaming-broker`, `researching-cache-store`, `researching-coordination-service`, `researching-search-engine`, `researching-api-gateway`, `researching-rdbms`, `researching-document-store`, `researching-kv-store`, `researching-wide-column-store`, `researching-graph-database`, `researching-timeseries-db`, `researching-columnar-analytics`, `researching-vector-store`, `researching-object-storage`) |
| [artifact-author](.claude/agents/artifact-author.md) | generates SKILL.md / agents / rules (renamed from `skill-author` — it authors 3 of the 4 artifact types) | `skill-creator`, `agent-creator`, `rules-compiler`, `methodologies-skill-generator`, `architecture-approaches-skill-generator`, `terraform-instructions-compiler` |
| [architecture-auditor](.claude/agents/architecture-auditor.md) | audits architecture (consensus = 3 lenses in parallel via Agent tool) | `audit-architecture-scope`, `audit-architecture-flow`, `audit-architecture-engine`, `audit-architecture-consensus` (Copilot target); `audit-cc-architecture-scope`, `audit-cc-architecture-flow`, `audit-cc-architecture-engine`, `audit-cc-architecture-consensus` (Claude Code target) |
| [quality-validator](.claude/agents/quality-validator.md) | validates quality/adherence | `skill-best-practices-validator`, `instructions-best-practices-validator`, `agent-router-pattern-validator`, `copilot-compatibility-review`, `project-analysis-validator` |
| [skill-evaluator](.claude/agents/skill-evaluator.md) | evaluates skill behavior via LLM-as-judge (runs evaluation-scenarios.md and verifies real responses) | `evaluating-skill-scenarios` |

`.claude/agents/` also has 2 **internal helper** subagents, not routed by any `/command` — invoked
directly by `framework-researcher` via the Agent tool during deep research: `research-synthesizer`
(assembles parallel findings into the output-format skeleton) and `section-investigator` (fetches
one research section in parallel). See [docs/manual/](docs/manual/) for details.

The **book-writing** package adds its own self-contained pipeline: `book-orchestrator` (routes
`writing-technical-book`, `writing-book-toc`, `rewriting-book-chapter`, `rewriting-book-introduction`,
`switching-book-language`, `enriching-book-chapter`), plus `book-translator`, `book-formatter`,
`epub-repairer` and `mermaid-renderer` (each fronted by one command) and 7 worker subagents spawned
by the orchestrator. Output goes to `Books/{slug}/` (gitignored); details in
[packages/content-generation/book-writing/README.md](packages/content-generation/book-writing/README.md).

The **Quarkus base** package `quarkus-core` holds the Quarkus 3.40 LTS skills shared by Camel and
AWS work: `developing-quarkus-{arc,rest,junit}-v3-40` (moved here from `camel-quarkus-skills`, names
unchanged). `refactoring-quarkus-java`, `refactoring-oci-java` and the two clean code rules
(`quarkus-clean-code`, `java-functions-clean-code`) live in `java/clean-code/` as two packages, one
per stack: `clean-code-quarkus` (a dependency of `quarkus-core`) and `clean-code-oci` (a dependency of
`oci-functions-java`) (split out 2026-10-31 so it can be sold as its own bundle).

The **Camel Quarkus** packages are a second self-contained set, not routed by a `/command`:
`camel-quarkus-skills` (10 version-locked knowledge skills `developing-camel-quarkus-*-v3-40` for Camel Quarkus
3.40 LTS / Camel 4.22 / Quarkus 3.40, generated from dated official-source research; depends on `quarkus-core`) and
`camel-quarkus-integrator` (the inline orchestrator skill `integrating-camel-quarkus`, the
`structuring-camel-quarkus-projects` skill, the non-interactive `camel-quarkus-integrator` subagent
and 3 scoped rules). Details and scope limits in
[packages/java/quarkus/camel-quarkus-integrator/README.md](packages/java/quarkus/camel-quarkus-integrator/README.md). These
skills follow the **hybrid knowledge-skill** format (lean `SKILL.md` + `blueprints/`, see
`.claude/rules/skill-structure.md`).

The **Terraform executors** live in `packages/cloud/terraform/terraform`: `terraform-rules-author` (non-interactive, compiles scoped Terraform rules from a research file) and `aws-terraform-engineer` (non-interactive, writes/reviews HCL for a CLOSED AWS requirement using the 26 `provisioning-aws-<service>-v6` skills from `packages/cloud/terraform/aws-terraform`; offline checks only — never apply/destroy/import). Command: `/provision-aws-terraform`. Details: [packages/cloud/terraform/aws-terraform/README.md](packages/cloud/terraform/aws-terraform/README.md).

The **LangChain4j** package (`packages/java/libs/langchain4j`) covers chat + streaming in plain Java on LangChain4j 1.22.0 with OpenAI and Anthropic: 3 version-locked knowledge skills (`developing-langchain4j-core-v1-22`, `integrating-langchain4j-openai-v1-22`, `integrating-langchain4j-provider-a-v1-22` — the Anthropic one, named without the reserved word), the non-interactive `langchain4j-integrator` subagent (no `/command`; spawned via the Agent tool) and 2 scoped rules. AiServices, `@Tool`, RAG, structured output and Spring/Quarkus are out of scope. Details: [packages/java/libs/langchain4j/README.md](packages/java/libs/langchain4j/README.md).

The **Quarkus on AWS Lambda SaaS + Next.js** set is a set of layered packages (plus the reusable OpenSpec and GitHub layers below) driven by the inline project-manager orchestrator
`/building-aws-saas-serverless-quarkus-react-nextjs` (spec-driven: interview, solution architecture + design + infrastructure specs with ADRs in three folders, OpenSpec functional spec, wireframes,
technical designs, then an agent team via handoff records; deploy runs in GitHub Actions after the user's PR merge; it is the only one that talks to the user). Planning runs in the session model (Opus); every worker is launched with `model: "sonnet"` except `solution-architect` and `aws-infrastructure-architect` (`opus`). Every deliverable has a different reviewer agent.
- `handoff-core`: the generic handoff protocol v1 (`coordinating-agent-handoffs`, with the Python
  scripts `check_records.py`, `board.py`, `detect_drift.py`; profiles may carry an optional `tracker:` block),
  the read-only `spec-synchronizer` subagent and the command `/syncing-spec-from-code`. The OCI profile
  `coordinating-oci-handoffs` (in `oci-core`) uses the same protocol. Depends on `openspec-core`.
- `openspec-core`: the OpenSpec 1.15 skill plus the rule `openspec-project-layout` (factory folder convention: `architecture/`, `design/`, `infrastructure/` with their own `adr/`).
- `quarkus-aws`: 11 knowledge skills (Lambda, HTTP, Cognito, data, messaging, testing, logging, tracing,
  metrics, observability umbrella, project structure), the executor `quarkus-lambda-integrator`, the
  read-only `quarkus-code-reviewer` and 2 rules.
- `quarkus-langchain4j`: `integrating-quarkus-langchain4j-v1-15` (pinned to 1.15.0.CR1, flagged as a candidate release) and the read-only `langchain4j-reviewer`.
- `solution-architecture`: `solution-architect` (opus) and `solution-architecture-reviewer`.
- `ui-design`: `ui-ux-designer` and `ui-design-reviewer` (use the Vercel design skills).
- `nextjs-frontend`: `nextjs-frontend-integrator`, `nextjs-code-reviewer` and the rule `nextjs-static-export` (Next.js static export to S3 + CloudFront).
- `aws-architect`: gains `aws-infrastructure-architect` (opus) and `aws-architect-reviewer`; `terraform` gains `terraform-code-reviewer`; `aws-observability` gains `static-site-verifier`.
- `aws-lambda`: runtime-agnostic `aws-lambda-deployer` (not used by this flow any more; the pipeline deploys) and
  read-only `aws-lambda-debugger`, with `deploying-aws-lambda` and `debugging-aws-lambda`.
- `aws-observability`: the `aws-observability` subagent, the command `/observe-aws-workload` and
  `validating-aws-observability` (read-only live checks in Python, approval flags for anything else).
- `aws-saas-serverless-quarkus-react-nextjs`: the orchestrator, the profile `coordinating-quarkus-aws-handoffs`
  and `integrating-stripe-quarkus-v3-40`; depends on all of the above plus `vercel-frontend` and `github-actions-cicd`.
Details: [packages/saas/aws-saas-serverless-quarkus-react-nextjs/README.md](packages/saas/aws-saas-serverless-quarkus-react-nextjs/README.md).

The **OpenSpec + GitHub** layer is 4 reusable packages: `openspec-core` (the OpenSpec 1.15 skill alone,
split out of `handoff-core`), `github-core` (generic `managing-github-projects-gh-v2-103` and
`automating-github-repos-with-actions`) and `openspec-github` (the bridge `syncing-openspec-with-github-projects`:
`gh_projects_sync.py` bootstrap/push/pull/close/status, dry-run by default, 4 workflow templates for comment
gates, spec CI, board sync and archive-by-PR; the non-interactive `openspec-github-syncer` agent, push/status only;
the command `/syncing-openspec-to-github`; one scoped rule). Git stays canonical; GitHub is a mirror plus an
optional approval channel that only the orchestrator reads (`pull`). `openspec-poc` drafts specs from the code of a POC
(back end and/or front end, any stack): the inline skill `/bootstrapping-spec-from-poc` runs `poc_inventory.py`, the read-only
`poc-spec-extractor` agent drafts requirements with `file:line` evidence, architecture and design drafts and questions into
`openspec/poc/<id>/`, `spec-synchronizer` reviews it (Mode A, POC variant), and promotion to a change needs the user's yes; POC
shortcuts become questions, never requirements. The SaaS orchestrator accepts `poc=`/`poc.back=`/`poc.front=` and uses the draft
only as input to its E1 interview. Organization projects use a GitHub App,
user projects a classic PAT. Off by default (`tracker.kind: none`). Details:
[packages/delivery/specs/openspec-github/README.md](packages/delivery/specs/openspec-github/README.md).

The **Vercel front-end** package (`packages/third-party/vercel-frontend`) copies no skill content. Its `apm.yml` points to 7 official Vercel skill repositories (agent-skills, next.js, ai-elements, streamdown, components.build, turborepo, agent-browser), each pinned to a commit SHA, and `apm install` brings in the 20 knowledge skills they publish (React/Next.js performance, composition, Cache Components, web design guidelines, AI chat UI, Turborepo, browser automation). Their names come from the upstream folders and do not follow the factory naming rules. On Windows the install needs `git config --global core.longpaths true` and takes about 25-40 minutes. `vercel/ai` and 3 skills that can only be installed from a subfolder (`path:`) are commented out because the install fails for them on Windows. Details: [packages/third-party/vercel-frontend/README.md](packages/third-party/vercel-frontend/README.md).

Note `rules-compiler` in the table above: it is itself a **knowledge skill** (no `context: fork`)
— a reference engine that `terraform-instructions-compiler` (an action command) links into for
its generic phases. It doesn't route on its own; it's listed because `artifact-author` maintains
it.

**Fallback (no matching command):** If a request does not match any `/command` listed above, respond with the closest matching command and its description. Do not attempt to fulfill the request inline — route or decline.

## How to run (no build step)

Not compiled code — artifacts run **in Claude Code** via `/<command>`:

- Search for a technology: `/researching-technical-frameworks <tech> <version>`
- Create a skill from a research file: `/skill-creator workspace/research_X_v1.md`
- Create a subagent: `/agent-creator <domain-role> [advisory|orchestrator]`
- Compile Terraform research into scoped rules: `/terraform-instructions-compiler <research-file>`
- Create a methodology skill (all-in-one): `/methodologies-skill-generator <methodology>`
- Audit a Claude Code project (consensus): `/audit-cc-architecture-consensus <target>`
- Audit a GitHub Copilot project (consensus): `/audit-architecture-consensus <target>`
- Validate skill quality: `/skill-best-practices-validator .claude/skills/`
- Audit full project health: `/project-analysis-validator .claude/`
- Evaluate skill behavior: `/evaluating-skill-scenarios cloud-architecture-researcher`
- Research self-managed platform software (auto-routes to the right sibling): `/researching-platform-software Kafka 3.7`
- Or call the sibling directly: `/researching-streaming-broker Kafka 3.7 deployment=kubernetes-operator`
- Datastore with modeling: `/researching-document-store MongoDB 7.0 deployment=kubernetes-operator`
- API gateway: `/researching-api-gateway Kong 3.7 deployment=kubernetes-operator`
- Build or evolve a Quarkus SaaS on AWS Lambda (inline orchestrator): `/building-aws-saas-serverless-quarkus-react-nextjs`
- Propose a spec-delta after code drift: `/syncing-spec-from-code <change-dir>`
- Review, provision or live-validate AWS observability: `/observe-aws-workload <work-order>`
- Refresh or check the GitHub Project mirror of an OpenSpec change: `/syncing-openspec-to-github <change-id>`
- Draft specs from a POC (inline, any stack): `/bootstrapping-spec-from-poc back=<dir> front=<dir>`

The 68 commands use `disable-model-invocation: true` (deliberate actions) — accessible via `/name`,
with no auto-listing cost. The other 189 skills are knowledge skills and auto-invoke instead of
routing via `/name`: `rules-compiler`, the 12 Camel Quarkus skills, the 4 `quarkus-core` skills, the 26 `provisioning-aws-<service>-v6` skills, the Quarkus on AWS Lambda SaaS skills, the inline coordinator `bootstrapping-spec-from-poc`, and the AWS architecture (`aws-skills`), OCI, Stripe, LangChain4j, OpenSpec and GitHub (`github-core`, `syncing-openspec-with-github-projects`) knowledge skills (their descriptions are
listed in every session of a project that installs them, so keep them short and specific).

## Structure

```
.claude/            ← GENERATED by `apm install --target claude`. Edit packages/, not this.
├── agents/     ← 55 subagents: 5 routing-level (framework-researcher, artifact-author,
│                 architecture-auditor, quality-validator, skill-evaluator) +
│                 2 internal helpers (research-synthesizer, section-investigator) +
│                 13 book-writing agents + camel-quarkus-integrator +
│                 terraform-rules-author + aws-terraform-engineer + aws-architect +
│                 7 OCI agents + 2 Stripe agents (stripe-advisor, stripe-integrator) +
│                 langchain4j-integrator + 6 Quarkus/AWS SaaS agents (quarkus-lambda-integrator,
│                 quarkus-code-reviewer, aws-lambda-deployer, aws-lambda-debugger,
│                 aws-observability, spec-synchronizer) + openspec-github-syncer + poc-spec-extractor +
│                 2 CI/CD agents (cicd-pipeline-engineer, cicd-pipeline-reviewer) +
│                 11 SaaS design/front/review agents (solution-architect, solution-architecture-reviewer,
│                 aws-infrastructure-architect, aws-architect-reviewer, ui-ux-designer, ui-design-reviewer,
│                 nextjs-frontend-integrator, nextjs-code-reviewer, langchain4j-reviewer,
│                 terraform-code-reviewer, static-site-verifier)
├── skills/     ← 257 skills: 68 fork → subagent commands + 189 knowledge/auto-invoke (incl. 20 Vercel and 9 GitHub Actions CI/CD knowledge skills); includes the
│                 platform-software family (1 orchestrator + 14 siblings),
│                 12 Camel Quarkus, 4 quarkus-core, 22 Quarkus/AWS SaaS, 26 AWS Terraform (provisioning-aws-*-v6), the AWS/OCI/Stripe/LangChain4j knowledge skills, and each skill's own assets/ (former .claude/templates/
│                 content) + blueprints/
├── rules/      ← 56 rules (most scoped by `paths:`; incl. nextjs-static-export, openspec-project-layout and 4 github-workflows-*): 5 factory rules + 3 Camel Quarkus + 3 AWS Terraform + OCI (incl. 2 oci-architecture guardrails), AWS-architect, Stripe, 2 LangChain4j and 5 Quarkus/AWS rules (quarkus-clean-code, 2 quarkus-lambda, aws-lambda-deployment-preflight, aws-observability-skills) + openspec-github-state
├── MIGRATION.md ← migration history Copilot → Claude Code (hand-authored, not generated)
├── settings.json         ← hand-authored, not generated (APM only merges `hooks:`, unused here)
└── settings.local.json   ← hand-authored, gitignored

packages/           ← the actual source of truth — 41 APM packages grouped in family folders
│                     (packages/<family>[/<sub>]/<pkg>), all installed by the root manifest (directly or
│                     transitively), each with its own apm.yml; plus 19 sales bundles (see bundles/ below)
├── factory/
│   ├── factory-core/             ← 5 rules (frontmatter + naming schemas), no skills/agents
│   ├── research-core/            ← framework-researcher + its 2 internal helpers, no skills
│   ├── researching-frameworks/   ← 5 generic research skills
│   ├── researching-platform/     ← 15 platform-software skills (indivisible — see its apm.yml)
│   ├── artifact-authoring/       ← artifact-author + 5 skill/agent/rule-authoring skills
│   └── agent-package-builder/    ← building-agent-packages: inline orchestrator of the whole
│                                   research → skills → agent/rules → quality loop → commit chain
├── harness-quality/
│   ├── auditing/                 ← architecture-auditor + 8 audit skills
│   ├── validating/               ← quality-validator + 5 validation skills
│   └── evaluating/               ← skill-evaluator + 1 skill (runtime dep on every package)
├── content-generation/
│   └── book-writing/             ← 13 agents + 10 commands for the technical-book pipeline
├── architecture/
│   └── solution-architecture/    ← solution-architect (opus) + solution-architecture-reviewer
├── cloud/
│   ├── terraform/
│   │   ├── terraform/            ← Terraform skills + 2 agents (terraform-rules-author,
│   │   │                           aws-terraform-engineer) + `/provision-aws-terraform`; depends on aws-terraform
│   │   ├── aws-terraform/        ← 26 version-locked skills (hashicorp/aws 6.x, Terraform ~> 1.16) + 3 rules
│   │   └── oci-terraform/        ← OCI Terraform provisioning skills + oci-terraform agent
│   └── provider/
│       ├── aws/                  ← aws-skills (AWS architecture knowledge), aws-architect (advisory agent),
│       │                           aws-lambda (deployer + debugger, any runtime),
│       │                           aws-observability (agent, /observe-aws-workload, live validation)
│       └── oci/                  ← oci-core (shared handoff profile), oci-functions-java, oci-observability,
│                                   oci-architecture — the OCI serverless family
├── delivery/
│   ├── protocol/handoff-core/    ← generic handoff protocol + scripts (optional tracker: block), spec-synchronizer, 1 command
│   ├── specs/                    ← openspec-core (OpenSpec 1.15 skill, reusable without handoff),
│   │                               openspec-github (OpenSpec ↔ GitHub Projects bridge: skill + scripts +
│   │                               4 workflow templates, syncer agent, 1 command, 1 rule),
│   │                               openspec-poc (specs drafted from a POC: inline skill + poc_inventory.py,
│   │                               poc-spec-extractor agent; draft area openspec/poc/<id>/)
│   └── github/                   ← github-core (gh 2.103 + Projects v2, Actions automation),
│                                   github-actions-cicd (9 CI/CD skills + engineer/reviewer agents)
├── java/
│   ├── quarkus/                  ← quarkus-core (Quarkus 3.40 LTS arc/rest/junit),
│   │                               quarkus-aws (11 Quarkus on Lambda skills, integrator + reviewer, 2 rules),
│   │                               quarkus-langchain4j (1.15.0.CR1 skill + langchain4j-reviewer),
│   │                               camel-quarkus-skills (10 Camel Quarkus 3.40 LTS skills),
│   │                               camel-quarkus-integrator (orchestrator + structure skills, 1 subagent, 3 rules)
│   ├── clean-code/               ← clean-code-quarkus (refactoring-quarkus-java + quarkus-clean-code),
│   │                               clean-code-oci (refactoring-oci-java + java-functions-clean-code)
│   └── libs/                     ← langchain4j (1.22.0 chat + streaming, langchain4j-integrator, 2 rules),
│                                   stripe-java (Stripe Java 34.x skills + advisor/integrator agents)
├── frontend/react/               ← ui-design (ui-ux-designer + ui-design-reviewer),
│                                   nextjs-frontend (integrator + code reviewer + 1 rule, static export)
├── third-party/vercel-frontend/  ← points to 7 official Vercel skill repos (never sold, see bundles)
├── saas/aws-saas-serverless-quarkus-react-nextjs/ ← project-manager orchestrator, handoff profile, Stripe skill
└── bundles/                      ← 19 sales meta-packages: apm.yml only (dependencies, no .apm/; an
                                    optional export.yml cuts what is sold); exported by scripts/export-bundle.py;
                                    NOT listed in the root apm.yml. See docs/comercial/estrategia-bundles.md

apm.yml             ← root manifest: aggregates the packages (factory-core, research-core,
                       camel-quarkus-skills, quarkus-core, openspec-core, github-core, openspec-github, openspec-poc and the
                       Quarkus/AWS SaaS layers below aws-saas-serverless-quarkus-react-nextjs (incl. vercel-frontend, github-actions-cicd) are NOT listed directly — they resolve transitively;
                       listing them twice triggers a real `apm audit --ci` failure,
                       "ambiguous resolved_by")
apm.lock.yaml       ← committed; regenerated by `apm install --target claude` (no CI check)
scripts/            ← 2 defensive post-install fixups (see NOTE in apm.yml above `lifecycle:`; both take
                       `--root <dir>`), reorganize-packages.py (the family move), export-bundle.py +
                       export_detectors.py (sales export and sensitive-data detectors; tests in scripts/tests/)
docs/
├── capacidades/  ← skills/commands catalog
├── como-usar/    ← operational guides
├── fluxos/       ← flow diagrams
├── manual/       ← subagent reference manual
├── templates/    ← POST_MORTEM_TEMPLATE.md (human procedure, not a Claude Code artifact)
└── referencia/   ← glossary and conventions
workspace/      ← research outputs and validation working files (versioned; was StoryBeat/); Camel Quarkus
                  research_*_v3.40.md + _family_facts/_family_rules are the provenance of its skills;
                  workspace/quarkus-aws-saas/ (historical folder name) holds the research, state and validation of the SaaS set
```

There is **no `.claude/templates/`** — every template lives in the `assets/` of the skill that
owns it (`skill-creator/assets/`, `agent-creator/assets/`, `rules-compiler/assets/`,
`terraform-instructions-compiler/assets/`). This is required for APM packaging: there is no
`templates` primitive, only skill subfolders (`assets/`, `references/`, `scripts/`) that deploy
with the skill.

**`.claude/{agents,skills,rules}/` are generated, and committed anyway** — a clone with no
network access and no `apm` CLI still has every `/command` working, exactly as before this
migration. There is no CI: nothing checks automatically that `.claude/` matches `packages/`, so
always regenerate it before committing (below).
To change a skill/agent/rule: edit it under `packages/**/.apm/` (family folders), then
`apm install --target claude` followed by `python scripts/restore-rule-metadata.py` and
`python scripts/fix-cross-package-links.py` to regenerate `.claude/` locally before committing both.

## Gotchas

- **Frontmatter conventions** (field names, model values, YAML quoting): see
  [`.claude/rules/skill-frontmatter.md`](.claude/rules/skill-frontmatter.md).
- Do not trust audit counts — verify with `ls`/`wc`/`grep`.
- `.claude/worktrees/` does not exist by default — Git worktrees are created on demand by
  worktree-based workflows, not a fixture of this repo.
