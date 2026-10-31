# POC shortcuts

Back to [SKILL.md](../SKILL.md). A POC is built fast; some of what it does is a shortcut, not a product
rule. Every shortcut becomes a **question** in `questions.md`. None becomes a requirement. The
`spec-synchronizer` review treats a shortcut written as a requirement as a HIGH finding.

| Inventory `kind` | Seen as | Question to write (theme) |
|---|---|---|
| `hardcoded-secret` | a literal password, key, token or client secret in code or config | "`<file>:<line>` holds a hard-coded `<name>`. Where will this secret live, and who rotates it?" (security) |
| `cors-wildcard` | CORS open to any origin | "CORS accepts any origin (`<file>:<line>`). Which origins may call the API?" (security) |
| `permit-all` | an endpoint or app explicitly open without auth | "`<file>:<line>` allows anonymous access. Which actors may call this, with which role?" (actors, security) |
| no `security[]` signal at all | no authentication anywhere | "The POC has no authentication. Who are the users, how do they sign in, what can each role do?" (actors, security) |
| `mock-data` | a `mock`/`fake`/`stub`/`fixture`/`seed` file outside tests | "Data comes from `<file>`. What is the real source, who owns it, how long is it kept?" (data) |
| `localhost-url` | a hard-coded `http://localhost...` | "The front calls `<url>` at `<file>:<line>`. Which environments exist?" (operation) |
| `todo` with a business word (tenant, owner, permission, limit, price, delete) | an unfinished rule | "`<file>:<line>` says `<text>`. Is this a rule the product must enforce?" (business rules) |
| `cross.front_only` | a call with no endpoint | "The front calls `<METHOD> <path>` (`<file>:<line>`) and no back-end route answers it. Missing endpoint, other service or dead code?" (features) |
| `cross.back_only` | an endpoint nothing calls | "`<METHOD> <path>` (`<file>:<line>`) is never called by the front. Admin, machine caller or remove?" (features, actors) |
| a 2xx-only flow | no error handling on a path that can fail | "What should the user see when `<action>` fails?" (features, screens) |

Rules:

- Cite file, line and kind only. **Never copy the value** of a secret, token or password.
- The script does not classify todos: the extractor judges the business word from the `text` field. A plain `todo` without one goes to `inventory.md`, not to `questions.md`; the reviewer flags only a business `todo` left without a question.
- When the same shortcut appears in many files, write one question and list every `file:line`.
