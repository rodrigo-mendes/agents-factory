---
name: [language]-[framework]-standards
description: "[LANGUAGE] coding standards for [FRAMEWORK] v[VERSION] — naming, structure, code quality, security, and mandatory patterns"
applyTo: "**/*.[extension]"
---

You are a [LANGUAGE] Code Quality specialist for [FRAMEWORK] v[VERSION].
Ensure all [LANGUAGE] code follows [STANDARD_NAME] best practices for production readiness.

For complete code patterns and implementation examples, load the relevant skill from `.github/skills/[skill-name]/SKILL.md`.

## When to Load Skills

These standards apply automatically via `applyTo`. When generating code, also load the relevant skill for implementation patterns. See `[language]-[framework]-skills.instructions.md` for the skill routing table.

## Version Constraints
- [LANGUAGE]: v[VERSION]+
- [FRAMEWORK]: v[VERSION]
- [SDK/Library]: v[VERSION]+
- ALWAYS pin versions in [dependency-file]

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| **Classes** | [convention] | [example] |
| **Methods/Functions** | [convention] | [example] |
| **Variables** | [convention] | [example] |
| **Constants** | [convention] | [example] |
| **Packages/Modules** | [convention] | [example] |
| **Files** | [convention] | [example] |

## Code Structure Standards
- [Structure rule 1]: [description]
- [Structure rule 2]: [description]
- [Structure rule 3]: [description]
- Import ordering: [ordering convention]

## Security Standards

### Authentication
- [Auth rule 1]: [description]
- NEVER [auth prohibition]: [reason]

### Secret Management
- [Secret rule 1]: [description]
- NEVER [secret prohibition]: [reason]

### Input Validation
- [Validation rule 1]: [description]
- [Validation rule 2]: [description]

### Logging Security
- NEVER log [sensitive data types]
- Log [correlation IDs] for support troubleshooting

## ✅ Always Do
1. [Mandatory practice 1]
2. [Mandatory practice 2]
3. [Mandatory practice 3]
4. [Mandatory practice 4]
5. [Mandatory practice 5]

## 🚫 Never Do
1. [Prohibited practice 1] — **Severity: CRITICAL**
2. [Prohibited practice 2] — **Severity: HIGH**
3. [Prohibited practice 3] — **Severity: HIGH**
4. [Prohibited practice 4] — **Severity: MEDIUM**
5. [Prohibited practice 5] — **Severity: MEDIUM**
