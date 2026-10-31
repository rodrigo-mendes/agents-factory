# Draft format (`openspec/poc/<poc-id>/`)

Back to [SKILL.md](../SKILL.md). The draft area is a factory convention (rule `openspec-project-layout`),
not official OpenSpec: it sits outside `specs/` and `changes/`, so neither `openspec validate` nor
`openspec archive` treats it as a spec. The functional files still use the OpenSpec live-spec format so
they can be promoted without rewriting (format facts: skill `specifying-changes-with-openspec-v1-15`).

## Contents

- [Folder](#folder)
- [inventory.md](#inventorymd)
- [functional/capability/spec.md](#functionalcapabilityspecmd)
- [architecture-draft.md](#architecture-draftmd)
- [design-draft.md](#design-draftmd)
- [questions.md](#questionsmd)
- [traceability.md](#traceabilitymd)
- [verify-poc.md](#verify-pocmd)

## Folder

```
openspec/poc/<poc-id>/
├── inventory.json                 written by poc_inventory.py (coordinator)
├── inventory.md                   extractor
├── functional/<capability>/spec.md extractor (one per capability)
├── architecture-draft.md          extractor
├── design-draft.md                extractor (only with a front end)
├── questions.md                   extractor
├── traceability.md                extractor; Decision column filled with the user
└── verify-poc.md                  spec-synchronizer review, saved by the coordinator
```

Every Markdown file the coordinator saves starts with an HTML comment `<!-- saved-by: <coordinator> | from: <agent> | <UTC ts> -->`, except `verify-poc.md` (frontmatter must stay on line 1; add `saved-by: <coordinator>` as a frontmatter field instead) and `inventory.json`.

## inventory.md

Counts, then one table per side (endpoints with method, path, `file:line`, source; routes; calls), then
`front_only` and `back_only`, then shortcuts by kind (file and line only), then skipped files.

## functional/capability/spec.md

```markdown
# Orders Specification

## Purpose
Lets a customer place, list and cancel orders; drafted from the POC, not yet confirmed.

## Requirements

### Requirement: P1 Place an order
The system SHALL create an order when the customer submits a total greater than zero.

#### Scenario: Valid order
- **WHEN** the customer submits an order with a total of 30
- **THEN** the order is created and returned with its identifier

#### Scenario: Missing total
- **WHEN** the customer submits an order without a total
- **THEN** the order is rejected with a validation error

Evidence: back:src/server.js:7, front:src/App.jsx:14 - confidence: medium
```

- `P<n>` ids are provisional and unique inside the draft; promotion or the consumer may renumber them.
- One behaviour per requirement; text under 500 characters (validator warning, fails `--strict`).
- No framework, cloud, database or library names in requirement text.
- A requirement with no negative scenario in the POC gets a question asking for one, not an invented scenario.
- Purpose >= 50 characters (validator warning below that).

## architecture-draft.md

Sections, all with `file:line`:

1. **Pieces observed** - front end, API, handlers or functions, data stores, queues/events, external services.
2. **Contracts** - one block per endpoint group: method, path, input fields, output fields, error statuses, who calls it (front `file:line` or "nobody").
3. **Data model** - entities and fields seen, the owner when visible (user, tenant, none), validations.
4. **Security observed** - auth signals, or "none".
5. **Observed technical choices (ADR candidates)** - table: choice, where, what to decide. Example: "REST over HTTP with JAX-RS | ItemResource.java:9 | API style and framework stay or change?". Never "decided".
6. **Non-functional hints** - timeouts, pagination, caching, retries seen in code.

## design-draft.md

Screens (route, file, purpose), navigation between them, states seen per screen (`loading`, `error`,
`empty`, `forbidden`; missing ones listed), forms with their fields and client-side validations.

## questions.md

```markdown
# Questions from the POC <poc-id>

## Security
1. `src/main/java/.../ExternalClient.java:4` holds a hard-coded `api_key`. Where will this secret live, and who rotates it?

## Features
2. The front calls `POST /items/{}/archive` (`lib/api.ts:13`) and no back-end route answers it. Missing endpoint, other service or dead code?
```

Themes, in this order, only those with questions: Vision, Actors, Features, Business rules, Data,
Non-functional, Constraints, Operation, Screens, Security. Numbering runs across the whole file.

## traceability.md

| P | Title | Evidence | Confidence | Decision |
|---|---|---|---|---|
| P1 | Place an order | back:src/server.js:7 | medium | |

`Decision` is filled only from the user's answers: `adopted` (optionally the final id), `changed: <how>`,
`dropped: <user's reason>`.

## verify-poc.md

The `verify` record body returned by `spec-synchronizer` (Mode A, POC variant), in the shape of the
`verify` template of `coordinating-agent-handoffs`: `kind: verify`, `id: verify-poc`,
`from: spec-synchronizer`, `to: <coordinator>`, `change: <poc-id>`, `stage: poc`,
`refs: [poc-spec-extractor]`, `outcome: pass | fail`, `createdAt`; sections `## Criteria` and
`## Evidence` (file:line, severity per finding). It lives outside a handoff folder, so
`check_records.py` does not read it; `fail` when any HIGH finding exists.
