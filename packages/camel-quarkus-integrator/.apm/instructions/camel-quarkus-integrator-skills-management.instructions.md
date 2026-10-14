---
name: camel-quarkus-integrator-skills-management
description: "Points Camel Quarkus route work to the orchestrator and structure skills. Use when creating or changing route classes under integration/routes."
applyTo: "**/integration/routes/**/*.java"
---

# Skills for Camel Quarkus route work

This rule routes nothing itself. The requirement-to-skills mapping and the entry points live in
the orchestrator skill `integrating-camel-quarkus` and in the package README; do not copy them here.
Path-scoped rules load only when a matching file is read, so this helps on existing layouts only;
the new-project flow lives in the README and the `camel-quarkus-integrator` agent.

## Always

- Read `structuring-camel-quarkus-projects` before creating any file: it owns file locations.
- Read the whole `SKILL.md` of each skill you use (team convention), and follow its Always / Ask
  First / Never tiers.
- Note in a class comment which skills the code follows (team convention).

## Never

- Rely on memory for Camel Quarkus facts: the skills cover version 3.40 only.
- Improvise for areas without a skill (messaging, databases, Quarkus security, e-mail): no skill
  covers them; tell the user the limitation.
