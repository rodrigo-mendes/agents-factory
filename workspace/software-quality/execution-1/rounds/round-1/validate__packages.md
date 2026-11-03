# Round 1 - package validation (acceptance-testing, quarkus-acceptance-testing)

Scope: apm.yml, README, 2 agents, 2 rules, command skill, reference resolution. Skill bodies not assessed.

## Scores
- acceptance-testing: 9.0/10 (0 HIGH, 1 MEDIUM, 2 LOW)
- quarkus-acceptance-testing: 8.5/10 (0 HIGH, 1 MEDIUM, 3 LOW)

## Reference resolution (all OK)
- Dependencies exist: factory/factory-core, delivery/specs/openspec-core, java/quarkus/quarkus-core (apm.yml present); ../acceptance-testing resolves.
- Skills referenced exist: specifying-changes-with-openspec-v1-15 (openspec-core), developing-quarkus-{junit,rest,arc}-v3-40 (quarkus-core), the 3 package skills, building-acceptance-tests.
- Root apm.yml:43 lists only quarkus-acceptance-testing; acceptance-testing resolves transitively (correct per CLAUDE.md, no double listing).
- Versions in README (Cucumber 8.0.4, RestAssured 6.0.1, wiremock 1.8.1, Testcontainers 2.0.5) match _family_facts F1/F5/F8/F13.
- Frontmatter: both rules have name/description/applyTo; globs are valid. Command skill has context: fork + agent: acceptance-test-engineer + disable-model-invocation: true, and the agent exists. Both agents have "Use when" descriptions.

## Findings

### MEDIUM
1. acceptance-test-engineer.agent.md:13,89-95 - Tools include Write/Edit/Bash with no path restriction. The spec forbids "Write outside the Quarkus project dir", "commit, push", and "edit skill, agent or rule files", but enforcement is prose only. The reviewer file states this limit honestly ("the Bash tool itself is not restricted"); the engineer does not. Fix: add the same one-line honesty note, or add a hook or permission deny later. Not HIGH: the prohibition is documented, and Edit/Write are needed for the role.
2. acceptance-test-reviewer.agent.md:12,36-39 - Bash is granted for the coverage script; allowed commands are enforced by prose only. Same fix class, and already disclosed in the file. Kept at MEDIUM only because "cannot edit" depends on Bash discipline (Bash could write files). Fix: optionally note that script output is the only Bash write-free guarantee, or drop to LOW.

### LOW
3. quarkus-acceptance-testing/README.md:50 - Testcontainers 2.0.5 is "medium confidence" in family facts F5 but untagged in the README table. Fix: add "(medium confidence)".
4. acceptance-testing/README.md:7 vs apm.yml:9 - README does not say why factory-core is a dependency. Fix: one clause, e.g. frontmatter/naming rules.
5. quarkus-acceptance-testing/README.md:16-18 - lists the quarkus-core skills as "comes from" but the package's own agent/rules only reference `developing-quarkus-junit-v3-40`; rest/arc are unused by the shipped artifacts. Fix: confirm the intent, or trim.
6. acceptance-test-engineer.agent.md:61-64 - "B1 unless the caller chose otherwise" duplicates the skill default (quarkus-acceptance-tests rule says the same); fine, but a single source (the skill) is cleaner. Cosmetic.
7. acceptance-testing agent description is a long one-line paragraph that mixes role and a "Use when" example; fine, but "Use when" appears only at the end. Cosmetic.

## Checks passed
- Non-interactive executor returns numbered questions (NEEDS-INPUT, P0 and Ask First).
- Reviewer has no Write/Edit; its Never table matches its tools.
- Neither agent states a technical fact of its own; both defer to skills.
- Rules: Always/Ask First/Never/Verify present; Verify greps are consistent with skills; the Quarkus-only activation caveat is stated; glob `**/src/test/resources/features/**` overlaps the gherkin rule's `**/*.feature` by design.
- Command skill: argument-hint, routing, usage, eval link present; blueprints/evaluation-scenarios.md exists.
- Pilot open items on testing-quarkus-cucumber-v8-0 not re-assessed here (skill body out of scope).

Result: 0 HIGH. Packages are installable and consistent.
