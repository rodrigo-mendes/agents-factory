# Known source issues

Inconsistencies found while writing the package manuals. They live in the sources under `packages/`,
so the manuals describe what the sources say and flag the conflict. Nothing here has been fixed.

**How reliable this list is.** Items marked *(checked)* were verified directly against the files. All
other items come from the workers that wrote each manual, who read the sources for their packages; they
were not independently re-verified. Check an item before acting on it.

**Retracted.** An earlier note said the argument hint of `/provision-oci-serverless-stack` contains a
broken character. It does not: the file is correct, and the problem was how one console displayed an
em dash.

**Corrected.** An earlier version of this page listed the 34 source rules that use `applyTo:` as a possible scoping bug. It is not one: `applyTo:` is APM's source form, and APM converts it to `paths:` when it installs into `.claude/rules/` (documented in `scripts/restore-rule-metadata.py`). Two small things remain: the rule `rules-frontmatter` describes only the installed form, so it reads as if the sources were wrong, and one source rule (`java-functions-clean-code`) uses `paths:` directly. Whether the installed rules without any `paths:` are meant to load in every session was not established.

## 1. Fix first (behavior or safety)

| Where | Issue |
|---|---|
| `deploy-oci-function` | Evaluation scenarios 1 and 3 apply changes (scenario 3 applies a rollback) without the `approve=tfplan sha256=<hash>` gate that the skill and the `oci-deployer` agent require. |
| `debug-oci-function` | The skill and its scenario 3 send code fixes to `/deploy-oci-function`. The `oci-debugger` agent sends Java code fixes to `/develop-java-function` and only config, dependency and image fixes to the deployer. Scenario 2 sends a config fix to `@oci-terraform`, which the agent file does not do. |
| Research commands | None has an output-path parameter. Every platform sibling skill says to save under `workspace/docs/`, while `framework-researcher` says it never uses that folder unless it exists and the arguments point to it. |
| `oci-observability`, `oci-architecture` | Their agents load `provisioning-oci-*` skills that live in `oci-terraform`, but neither package depends on it. |
| `vercel-frontend` | The dependency line is commented out in `ui-design`, `nextjs-frontend` and the SaaS package, while the agents and descriptions use the Vercel skills and the committed `apm.lock.yaml` still lists the package. *(checked)* |
| `quality-validator` | Tools are Read, Grep, Glob and Write only, yet `--fix` needs Edit, `copilot-compatibility-review` needs web search, and several skills run shell commands. |
| `acceptance-test-reviewer` | Described as read-only but has Bash. The limit is prose only. |

## 2. Contradictions between a skill, its agent and its scenarios

**Terraform**
- `terraform-rules-author`: Never-Do says an executor skill "does not yet exist", but `provision-aws-terraform` exists. The hint marks `[platform]` optional, while the agent treats it as required. The hint is positional and the usage text is `KEY=VALUE`.
- `terraform-instructions-compiler`: "never generate without plan approval" conflicts with "unanswered questions get research defaults", and it never says which input variables it asks for.
- The two Terraform researchers: default depth is `exhaustive`, but Ask-First says to ask when `depth=` is absent. `terraform-engineering-best-practices-researcher` has the hint `<topic>`, but its body defines many more inputs. `technical-framework-researcher-terraform` takes a generic provider but cites DynamoDB locking and a 6-month freshness window, while its sibling uses 12.

**AWS**
- `aws-architect` P3 says "wait for user feedback", which contradicts its non-interactive contract.
- `aws-architecture-advisor` scenarios use HIGH and CRITICAL inconsistently.
- `observe-aws-workload`: `mode=validate` is called both the default and explicitly passed. The agent also accepts a fourth `instrument` mode that the command's `mode=` values do not list.
- `aws-lambda-deployment-preflight` says projects may deny agents access to `*.tfvars`, yet its glob includes `**/*.tfvars`.

**OCI**
- `provision-oci-infra`: the hint omits `connector-hub`, which the skill and scenario 2 use. Scenario 2's title says "API Gateway + IAM" but its input is streaming and connector-hub.
- `oci-observability` agent: the P5 hand-off option 2 tells the user to run `/observe-oci-workload`, which is the same command.
- `oci-serverless-stack` agent: "end at P3 with the plan" conflicts with the default mode, which continues to P4.
- `debug-oci-function` scenario 4 says "4-pillar"; `validating-oci-observability` has 5 pillars.
- Agents and skills reference paths that no package ships: `services/`, `services/.templates/`, `../../scripts/preflight.sh`, `libs/obs-commons`. The deployer and debugger hardcode the OCI profile `poc`.

**Factory and quality tooling**
- Report paths: `architecture-auditor` and `quality-validator` save to `.claude/reports/...`, but each skill names a different file. It is unclear which wins.
- `--fix` is supported by the validators but listed in no argument hint. The `evaluating` misuse scenario says fixes need a human or `artifact-author`.
- `agent-router-pattern-validator` says "8 sections" and "10 required sections".
- `skill-creator` says "at least 4" evaluation scenarios in one place and "at least 3" in two others.
- `artifact-author` P3 requires approval and describes no non-interactive mode (also true of the other four agents in `artifact-authoring`, `auditing`, `validating` and `evaluating`).
- The Copilot-family audits read `.claude/agents` and `.claude/skills` while using the `L0`-`L4` layer model with `.github/` names.
- `testing-quarkus-cucumber-v8-0` defines B1 and B2 as "who starts the app", while the agent, rule and `building-acceptance-tests` call them the `*IT` runner and the `@Suite` runner.
- `researching-technical-frameworks` says "13 required sections", lists 15, and its checklist says "All 15". `framework-researcher` lists the two Terraform researchers (not in its package) and its skill-path table omits the platform siblings.
- The methodology and domain researchers use different source-age flags (6, 12, 18 and 24 months).

**Java**
- Camel rule `camel-quarkus-integrator-skills-management` points to a "new-project flow" in the package README and agent that neither describes.
- `integrating-camel-quarkus` says "13 installed developing-*-v3-40 skills", which does not match `CLAUDE.md` (12 Camel Quarkus skills plus 4 `quarkus-core` skills).
- Clean-code guidance conflicts: the old READMEs said not to install both clean-code rules in one project, `quarkus-clean-code` says the more restrictive guidance wins when both load, and the bundle `java-clean-code` installs both.
- `refactoring-quarkus-java` says the rule `quarkus-clean-code` is in `quarkus-core`; it now ships in `clean-code-quarkus`.
- `java-functions-clean-code` lists `pom.xml`, `func.yaml` and `Dockerfile` in `paths:`, but its body covers only `src/main/java`.
- The `langchain4j` and Camel rules use globs that match every Java file; only the rule body narrows them.

## 3. Missing, stale or wrongly named things

| Where | Issue |
|---|---|
| Book commands | Nine commands and `skill-creator` have no standard `evaluation-scenarios.md`, although `skill-structure` requires one per command. |
| `writing-technical-book`, `writing-book-toc` | Argument hints omit `depth=quick`, which the orchestrator accepts. |
| Entry points without a hint | `building-agent-packages`, `integrating-camel-quarkus` and the SaaS orchestrator have no `argument-hint`. |
| `terraform/apm.yml` | Description omits `terraform-rules-author` and `terraform-code-reviewer`. |
| `artifact-authoring/apm.yml` | Says "5 commands"; there are 4 commands and one knowledge skill. |
| `stripe-java/apm.yml` | No description, author or license. |
| `solution-architecture/apm.yml` | Description is in Portuguese. |
| `quarkus-core` | `.apm/instructions/` is an empty folder. *(checked: generated table shows no rules)* |
| `clean-code-oci` | A review report, `refactoring-oci-java-best-practices-review.md`, sits inside the skill folder and ships with it. Its scenarios file is JSON, unlike every other skill, and the skill has no version-lock line. |
| `agent-package-builder` | A `__pycache__` folder is committed. The old README listed 6 scripts; the skill ships about 17. |
| `aws-skills` | Several skills have no Version Context table, and some Never-Do lists are only a link to a blueprint. |
| `aws-security-baseline` | Cites `family-rules-v2026.md`, which was not checked for existence. |
| `oci-functions-java` | The agent's own list of instruction files omits three rules. |
| `deriving-gherkin-from-openspec-v1-15` | Repeats the "Version-lifetime risk" line twice; the `gherkin-official` floor differs between PyPI (3.10) and main (3.11). |
| Scripts | `gate_command.py`, `portable.py` and `check_feature_coverage.py` document no exit codes or option defaults; `poc_inventory.py` gives no defaults for `--max-files` and `--max-bytes`; `gh_projects_sync.py` and `gate_command.py` fail at `--help` unless the handoff scripts are found. |
| Hook | `static-site-verifier` relies on `${CLAUDE_PROJECT_DIR}` expansion, which the agent itself marks unverified. |
| `building-cicd-pipelines` | The argument hint embeds a long example, so there is no clean parameter list. |

## 4. Language and format

- Portuguese remains in `oci-debugger` and `oci-deployer` (the RMS skill line and one interaction example), in `validating-oci-observability/scripts/README.md` (which also hardcodes the profile `poc` and region `sa-saopaulo-1`), in `openspec-github/.../bootstrap-and-credentials.md`, and as the word "Roteamento" in a `project-analysis-validator` example. Response field names `erro` and `detalhe` are Portuguese by design.
- Evaluation scenario files use five formats: YAML `query:`, JSON `"query"`, `**Input**:` blocks, `**Prompt**`, and prose. The skill evaluator parses JSON `success_criteria`.
- Relative links in some source rules and skills (for example `skill-frontmatter` linking `../skills/skill-creator/SKILL.md`) resolve only after installation, not from the package folder.

## Related

- [Maintaining the docs](maintaining-docs.md).
- [Conventions](conventions.md) and the [frontmatter cheatsheet](frontmatter-cheatsheet.md).
