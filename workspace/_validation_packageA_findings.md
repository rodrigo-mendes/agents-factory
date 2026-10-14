# Independent validation of packages/camel-quarkus-integrator (orchestrator relayed the validator's message; no report file was written by the validator)
Package root: packages/camel-quarkus-integrator/ . Siblings = packages/camel-quarkus-skills/.apm/skills/ (the factual authority). Policy: workspace/_family_rules_v3.40.md and _family_facts_v3.40.md.
Scores /10: integrating-camel-quarkus 8.0; structuring-camel-quarkus-projects 7.0; agent 8.0; rule code-standards 7.5; rule project-config 6.5; rule skills-management 6.5; README+apm.yml 7.5.

## HIGH
- H1 .apm/skills/structuring-camel-quarkus-projects/SKILL.md:40: "a RouteBuilder under `model` breaks discovery" has no support in the siblings (core: routes are discovered automatically). Reword to "routes belong in `integration.routes` by project convention (team convention)"; remove the discovery claim.
- H2 .apm/instructions/camel-quarkus-integrator-project-config.instructions.md:40: "Widen TLS globally" is under Never; policy 2 = Ask First only (the same rule lists "TLS scope" under Ask first, line 32). Delete the Never bullet; keep the Ask first entry and add "prefer a named TLS configuration".

## MEDIUM
- M1 integrating-camel-quarkus/SKILL.md:133 "Declare the `direct:` extension once per project if it is missing" is stronger than the siblings (rest skill: camel-quarkus-direct is medium, main-branch example; core silent): tag (medium confidence) and point to the rest skill's Ask First row "Dependencies beyond the transport".
- M2 blueprints/core-routes.md:55 and code-standards rule:36: "Never start, stop or replace the CamelContext in production code" / "Never create or manage a CamelContext manually" are stronger than the core skill (it only says the CamelContext follows the Quarkus lifecycle; the Never Do about this is in the junit skill and covers tests). AGREED WORDING for both files: "do not manage the CamelContext lifecycle: Quarkus drives it (core skill, Quick Reference Bootstrap) (medium confidence)", moved out of Never/Always lists to Ask First or a labelled team convention.
- M3 SKILL.md:143,156 vs core-routes.md:11,58: the requirement table sends timer, aggregation and monitoring to the core skill as if covered, but core-routes says no installed skill documents timer, SEDA, scheduler or aggregation EIP options: add "(not documented; see core-routes coverage note)" to those rows and a "documented gaps" line next to Out of Scope; interview options for aggregation/timer get the same marker.
- M4 skills-management rule:13-23 holds routing logic duplicating README/orchestrator (router validator flags it): cut to the three Always/Never bullets plus a pointer to the orchestrator and README.
- M5 skills-management rule:4 and code-standards rule:4: path-scoped rules load only when a matching file is read, so the "new integration" step cannot fire when no integration/routes file exists; two rules share the same glob: state in the rule that it only helps on existing layouts (or widen with src/main/java/**/*Route*.java for one of them); rely on README and the agent for the new-project flow.
- M6 blueprints/http-clients.md:43 "Handle HttpOperationFailedException with onException" is under Always Do but the http skill tags the throw semantics medium and the package unverified: move to Ask First or tag (medium confidence).
- M7 blueprints/rest-apis.md:59 "Never ship Camel's default CORS (*) to production" is in Never Do untagged; the rest skill marks it medium (unversioned manual) in Ask First: move to Ask First or tag (medium confidence).
- M8 README.md:56 "no Camel Quarkus build on it and no quarkus-camel-bom 4.x is known" untagged: policy 1 requires "(medium confidence, absence of evidence)" everywhere; the README also states the Quarkus 4 ban without the tag.
- M9 project-config rule:37 and agent.md:77: "Mix Quarkus 4 artifacts" is a Never Do row; policy 1: Quarkus 4 is never a Never Do row: move to the intro or an Ask First "version lock" line.
- M10 integrating-camel-quarkus/SKILL.md has no `## Version Context` section (only a blockquote) though skill-structure expects one for a version-locked hybrid knowledge skill: add Version Context (Camel Quarkus 3.40.x, Camel 4.22, Quarkus 3.40 LTS, Java 17 and 21 High per q-3.40.0, Quarkus 4 risk with the family tags). It has no unverified-and-risks blueprint although it relays tags: state explicitly "this skill has no register of its own: every (medium confidence)/(unverified) tag relays the register of the sibling skill named next to it".
- M11 agent.md:34-42: the agent reads only the table in the orchestrator SKILL.md and never the blueprints (Ask First, Never Do, team conventions); the orchestrator handoff passes "summary, skill list, blueprint list" but the agent has no input contract: add "if the caller supplies a skill/blueprint list, use it; otherwise derive it from the orchestrator table. Read the matching `integrating-camel-quarkus/blueprints/*.md` for Ask First and Never Do."
- M12 structuring SKILL.md:29,55 vs testing.md:57: the structure skill says one [ClassName]Test per route class; testing.md says one test class per routeId plus one for the error handler: state "per RouteBuilder class" in the structure skill and mark the testing item (per routeId) as its explicit refinement.

## LOW
- L1 `./mvnw` vs `mvn` ("representative") across package and structure skill: use "`./mvnw` (or `mvn` when the project has no wrapper)" everywhere in the package.
- L2 structuring SKILL.md:10 "migrated from the former project-structure-v1": delete (README keeps the migration note).
- L3 assets/project-structure.yml:78,80 examples DatabaseConfig and OrderModel point at an out-of-scope area: use HttpClientConfig.
- L4 orchestrator SKILL.md:67 interview example "new CSV files in /input" invites CSV (not covered): use XML. Map "data masking" under the security answer to the log skill row.
- L5 code-standards rule:15 / core-routes.md:42: "unique route id" is labelled team convention in the blueprint only: label it in the rule too.
- L6 project-config rule:41 "No secrets in committed properties" and skills-management rule:28 "load whole skill files" are not confirmed by any skill: label team convention; reword the second to "read the whole SKILL.md" (consistent with "load only what is mapped").
- L7 rules have no one-line reason per Never: add one.
- L8 project-config rule glob `**/{pom.xml,application.properties,application.yml}` loads in every Maven/Spring project: restrict with a src/main/resources pattern or keep and say so.
- L9 README.md:42-46 column header `applyTo` but generated rules use `paths:`: say "source applyTo, generated paths".
- L10 README.md:48 "Rules carry only conventions the skills confirm" overstated: soften (they also carry labelled team conventions).
- L11 blueprints link laterally (file-processing -> data-transformation, testing): list the cross-references in SKILL.md instead.
- L12 agent.md:29,40 "default to assume if answered 'your choice'" vs "never assume": say a skill-named default is the only allowed default.
- L13 README.md:66 keeps the old prompt name /camel-quarkus-integrator-unified as migration context: acceptable, keep (intentional).
