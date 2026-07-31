# Evaluation & Iteration

> Content sourced from [Official Claude Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration).

## Contents
- [Build Evaluations First](#build-evaluations-first)
- [Evaluation-Driven Development](#evaluation-driven-development)
- [Iterative Development with Claude A/B](#iterative-development-with-claude-ab)
- [Observe How Claude Navigates Skills](#observe-how-claude-navigates-skills)

---

## Build Evaluations First

Create evaluations BEFORE writing extensive documentation. This ensures your skill solves real problems rather than documenting imagined ones.

### Evaluation-Driven Development

1. **Identify gaps**: Run Claude on representative tasks WITHOUT a skill. Document specific failures or missing context
2. **Create evaluations**: Build at least 3 scenarios that test these gaps
3. **Establish baseline**: Measure Claude's performance without the skill
4. **Write minimal instructions**: Create just enough content to address the gaps and pass evaluations
5. **Iterate**: Execute evaluations, compare against baseline, and refine

### Evaluation Structure

```json
{
  "skills": ["skill-name"],
  "query": "Perform [specific task] and save result to [output]",
  "files": ["test-files/input.ext"],
  "expected_behavior": [
    "Successfully reads the input using appropriate library/tool",
    "Processes content from all relevant sections",
    "Saves output in the correct format"
  ]
}
```

---

## Iterative Development with Claude A/B

The most effective skill development involves two Claude instances:

- **Claude A** (the expert): Helps you design and refine the skill instructions
- **Claude B** (the tester): Uses the skill to perform real tasks — reveals gaps

### Creating a New Skill

1. **Complete a task without a skill** — work through a problem with Claude A using normal prompting. Notice what context you repeatedly provide.
2. **Identify the reusable pattern** — what context would be useful for similar future tasks?
3. **Ask Claude A to create the skill** — "Create a skill that captures this pattern we just used."
4. **Review for conciseness** — check that Claude A hasn't added unnecessary explanations. Ask: "Remove the explanation about [concept] — Claude already knows that."
5. **Improve information architecture** — ask Claude A to organize content effectively. Example: "Organize this so the table schema is in a separate reference file."
6. **Test with Claude B** — use the skill with a fresh Claude instance on related use cases. Observe whether Claude B finds the right information and applies rules correctly.
7. **Iterate based on observation** — if Claude B struggles, return to Claude A with specifics.

### Iterating on Existing Skills

1. **Use the skill in real workflows** — give Claude B actual tasks, not test scenarios
2. **Observe Claude B's behavior** — note where it struggles, succeeds, or makes unexpected choices
3. **Return to Claude A for improvements** — share the current SKILL.md and describe what you observed
4. **Review Claude A's suggestions** — it might suggest reorganizing, using stronger language ("MUST" vs "always"), or restructuring sections
5. **Apply and test changes** — update, then test again with Claude B
6. **Repeat based on usage** — each iteration improves based on real behavior

### Gathering Team Feedback

1. Share skills with teammates and observe their usage
2. Ask: Does the skill activate when expected? Are instructions clear? What's missing?
3. Incorporate feedback to address blind spots

---

## Observe How Claude Navigates Skills

As you iterate, watch for:

- **Unexpected exploration paths**: Claude reads files in a surprising order → structure may not be intuitive
- **Missed connections**: Claude fails to follow references → links need to be more explicit
- **Overreliance on certain sections**: Claude repeatedly reads the same file → consider moving that content to main SKILL.md
- **Ignored content**: Claude never accesses a bundled file → it might be unnecessary or poorly signaled

The `name` and `description` in YAML frontmatter are particularly critical — Claude uses these to decide whether to trigger the skill. Make sure they clearly describe what and when.

---

**Source**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#evaluation-and-iteration
