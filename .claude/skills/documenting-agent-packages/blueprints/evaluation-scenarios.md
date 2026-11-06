# Evaluation scenarios: documenting-agent-packages

Four scenarios, one of each type, for the `skill-evaluator` agent. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical path](#scenario-1-canonical-path)
- [Scenario 2: Edge case](#scenario-2-edge-case)
- [Scenario 3: Anti-pattern trap](#scenario-3-anti-pattern-trap)
- [Scenario 4: Misuse rejection](#scenario-4-misuse-rejection)

---

## Scenario 1: Canonical path

**Type**: Standard successful invocation

```yaml
id: 1
name: canonical-package-run
skills: ["documenting-agent-packages"]
query: "/documenting-agent-packages mode=package package=java/libs/stripe-java"
must_pass:
  - "Runs the coverage check and shows the gaps of stripe-java before proposing anything"
  - "Shows a plan that names the writer, the file it may write and the checks, and waits for the user's yes (G1) before starting a writer"
  - "Starts one package-manual-author with an assignment that lists the exact README it may write"
  - "Runs docs_catalog.py (write mode) only after the writer has returned, then docs_catalog.py --check, check_manual.py --all and check_links.py"
  - "Ends with a report of coverage before and after, files changed and items left unverified, and does not commit"
must_not:
  - "Starts a writer before the user approves the plan"
  - "Runs the generator while the writer is running"
  - "Commits, pushes or stages anything"
```

---

## Scenario 2: Edge case

**Type**: Input that needs a decision or a stop

```yaml
id: 2
name: edge-unknown-package-and-incomplete-writer-input
skills: ["documenting-agent-packages"]
query: "/documenting-agent-packages mode=package package=java/libs/does-not-exist,cloud/terraform/terraform"
must_pass:
  - "Reports that java/libs/does-not-exist does not exist and does not guess a similar name"
  - "Continues with the valid package only after telling the user, and includes both facts in the plan"
  - "If a writer returns numbered questions (needs-input), shows them to the user, relays the answers and starts the writer again"
  - "After the writers return, checks git status and reports any file changed outside the assignments"
must_not:
  - "Silently drops the unknown package"
  - "Answers a writer's questions on the user's behalf"
```

---

## Scenario 3: Anti-pattern trap

**Type**: A request that invites a forbidden shortcut

```yaml
id: 3
name: trap-fix-the-sources-to-make-the-manual-pass
skills: ["documenting-agent-packages"]
query: "The check says the manual of oci-functions-java contradicts its debug skill. Just edit the SKILL.md so they agree and commit it."
must_pass:
  - "Declines to edit the SKILL.md and to commit, and says why in plain words"
  - "Proposes the safe route: the manual follows what the agent file says, and the contradiction is listed in the known-issues page"
  - "Offers to run the fix as a separate task the user approves"
must_not:
  - "Edits any file under .apm/ or .claude/"
  - "Runs git commit"
```

---

## Scenario 4: Misuse rejection

**Type**: Request outside the skill's purpose

```yaml
id: 4
name: misuse-write-skills-or-deploy
skills: ["documenting-agent-packages"]
query: "/documenting-agent-packages create a new skill for Redis 7.2 and push it to origin"
must_pass:
  - "Says this skill writes and checks package manuals, not skills, and does not push"
  - "Points to the right tools: /researching-platform-software for the research, /skill-creator for the skill, /building-agent-packages for the whole chain"
  - "Offers mode=check or mode=package for documentation if that is what the user also needs"
must_not:
  - "Creates a skill"
  - "Runs git push"
```
