---
name: [language]-project-config
description: "[LANGUAGE] project configuration standards — dependency management, environment setup, build, and project structure"
applyTo: "**/{[dependency-file],[config-file],[build-file]}"
---

You are a [LANGUAGE] Project Configuration specialist for [FRAMEWORK] v[VERSION].
Ensure all project files ([dependency-file], [config-file], [build-file]) follow correct patterns for production-ready [LANGUAGE] applications.

For project directory layout and naming conventions, see `[language]-project-structure.instructions.md`.
For complete code patterns and configuration examples, load the skill: `.github/skills/[developing-skill-name]/SKILL.md`

## When to Load This Skill

Load `[developing-skill-name]` when the user request involves:
- Creating or modifying [dependency-file] dependencies
- Configuring [config-file] settings
- Writing or modifying [build-file]
- Sizing or performance-tuning the application

## Dependency Management Rules

### Version Pinning Requirements
- ALWAYS pin framework version — no LATEST or SNAPSHOT
- ALWAYS use [dependency-management-strategy] for version alignment
- ALWAYS pin test dependency versions
- NEVER mix dependency versions — use [bom-or-lockfile] for alignment

### Version Reference

| Component | Version | Identifier |
|-----------|---------|------------|
| [Framework] | [version] | [identifier] |
| [SDK/Library] | [version] | [identifier] |
| [Testing Framework] | [version] | [identifier] |

## [Config File] Rules

- [Rule 1]: [description of config file rule]
- [Rule 2]: [description of config file rule]
- [Rule 3]: [description of config file rule]
- Precedence: [precedence order description]

## [Build File] Rules

- [Rule 1]: [description of build file rule]
- [Rule 2]: [description of build file rule]
- [Rule 3]: [description of build file rule]

## Resource Sizing Guide

| Resource Level | Capacity | Use Case |
|---------------|----------|----------|
| [Level 1] | [capacity] | [use case] |
| [Level 2] | [capacity] | [use case] |
| [Level 3] | [capacity] | [use case] |

### Sizing Strategy
- Start at [recommended default]
- Measure via [monitoring tool/metric]
- Increase only if [threshold condition]

## ✅ Always Do
- [Mandatory rule 1]
- [Mandatory rule 2]
- [Mandatory rule 3]
- [Mandatory rule 4]

## 🚫 Never Do
- [Prohibited pattern 1] — [consequence]
- [Prohibited pattern 2] — [consequence]
- [Prohibited pattern 3] — [consequence]
- [Prohibited pattern 4] — [consequence]
