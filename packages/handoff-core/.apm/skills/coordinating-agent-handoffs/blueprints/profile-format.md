# handoff-profile.yaml format (protocol v1)

Back to [SKILL.md](../SKILL.md). One profile per agent family; the scripts read it with
`--profile`. A project may add `--override <file>` (same shape, `limits:` / `quality:` only).
Two complete examples are the test fixtures: `scripts/tests/fixtures/profiles/quarkus-aws.yaml`
(orchestrated, OpenSpec) and `.../oci.yaml` (user-mediated, no spec).

## Contents

- [Schema](#schema)
- [Overriding defaults](#overriding-defaults)
- [Limits and parameters](#limits-and-parameters)
- [Tracker](#tracker)
- [The `next` rules](#the-next-rules)
- [YAML subset](#yaml-subset-only-this-is-supported)

## Schema

| Key | Type | Req. | Default | Meaning |
|---|---|---|---|---|
| `profile` | string | yes | - | family name |
| `protocol` | string | no | `coordinating-agent-handoffs` | informational |
| `protocol_version` | int | no | `1` | must be 1 |
| `mode` | `orchestrated` \| `user-mediated` | yes | - | see [protocol](./protocol.md#modes) |
| `root` | string | yes | - | records folder template, `{change}` or `{capability}` placeholder (documentation for agents; scripts take the folder as argument) |
| `scope_key` | `change` \| `capability` | no | `change` | frontmatter field that names the scope |
| `spec` | map | yes | - | `kind: openspec \| none` (required); optional `functional`, `architecture`, `adr_dir` path templates |
| `roles` | map role -> agent or list | yes | - | e.g. `reviewer: [quarkus-code-reviewer, stripe-advisor]`; role names are free |
| `records` | map kind -> filename pattern | no | - | naming guidance (`{nn}`, `{role}`); not enforced |
| `kind_overrides` | map file name -> kind | no | `{}` | map legacy files to a kind (e.g. `deploy-report.md: deploy-report`) |
| `required_sections` | map kind -> list | no | built-in | replaces the built-in list of that kind |
| `values` | map kind -> field -> list | no | built-in | replaces allowed values (e.g. work-order `status` with `completed`) |
| `limits` | map name -> int >= 1 | no | `{}` | loop limits, see below |
| `limits_zero_confirmed` | bool | no | `false` | allows `0` in this source only |
| `quality` | map | no | `{}` | free parameters (e.g. `coverage_min: 80`); overridable like limits |
| `counters` | map name -> counter spec | no | built-in 5 | how each limit is counted |
| `fallback` | role \| `none` | no | `none` | next action when no rule matches |
| `next` | list of rules | yes | - | ordered next-action rules |
| `tracker` | map | no | absent (= `kind: none`) | optional external mirror of the records, see [Tracker](#tracker); ignored by the scripts except for a shape check |

## Overriding defaults

Built-in required sections and values are in [record-kinds](./record-kinds.md). Giving a kind in
`required_sections` / `values` **replaces** its built-in entry (no merging inside a kind).

## Limits and parameters

Built-in counters (override or extend in `counters:`):

| Limit | Counts (per task unless noted) | Reached when |
|---|---|---|
| `build_attempts` | reports with outcome `failed` or `partial` | count >= max(limit, 1) |
| `review_rounds` | reviews `changes-requested` | count >= max(limit, 1) |
| `deploy_cycles` (per change) | deploy-reports `failed` | count >= max(limit, 1) |
| `delta_revisions` (per change) | spec-deltas `revise` | count >= max(limit, 1) |
| `record_rejections` | max `rejections` field | count >= max(limit, 1) |

A counter spec: any of `kind`, `role`, `outcome`, `status` (scalar or list, ANDed), `scope`
(`task` default | `change`), or `max_field: <frontmatter int field>` instead of matchers.
A limit with no counter counts 0. Only records after the latest *answered* escalation for that
task/limit are counted.

**Precedence (most specific wins):** profile `limits` < project `--override` file < run `--args`
(`limits.review_rounds=4`). `board.py` stores every effective value and its source (`profile`,
`override (<file>)`, `args`) in `status.md`. Values must be integers >= 1; `0` (escalate on the
first failure: a limit is reached when count >= max(limit, 1)) behaves exactly like `1` (kept for explicitness) and is accepted only with `limits_zero_confirmed: true` in the same source
(`limits_zero_confirmed=true` in `--args`) - set it only after the user confirms explicitly.
Unknown limit names are errors.

## Tracker

Optional block for a family or project that mirrors its records into an external tracker. The
protocol scripts (`check_records.py`, `board.py`, `detect_drift.py`) never call a tracker: they
only validate the shape below and reject a malformed block. Records on disk stay canonical; a
bridge package (for example `openspec-github`, skill `syncing-openspec-with-github-projects`)
reads this block and does the mirroring.

| Key | Type | Req. | Default | Meaning |
|---|---|---|---|---|
| `kind` | `none` \| `github-projects` | yes | - | `none` disables the tracker |
| `owner` | string | when `github-projects` | - | user or organization login that owns the project |
| `owner_type` | `organization` \| `user` | when `github-projects` | - | selects the credential path of the bridge |
| `project_number` | int >= 1 | when `github-projects` | - | project number under `owner` |
| `repo` | `owner/name` | when `github-projects` | - | repository that holds the issues |
| `approval_source` | `chat` \| `github` \| `both` | no | `chat` | where gate answers may come from; anything but `chat` is an Ask First of the orchestrator |
| `approvers` | list of logins | when `approval_source` is not `chat` | - | only these logins can answer a gate on the tracker |
| `bot_login` | string | when `github-projects` | - | the automation identity whose recorded decisions and mirrored objects the bridge trusts (needed even with `approval_source: chat`); must not be an approver |

A project override (`--override`) cannot set `tracker`: the scripts read only `limits:` and
`quality:` from it, so a `tracker:` there is silently ignored. Keep project tracker values in the
bridge's own state file (the bridge documents where).

## The `next` rules

```yaml
next:
  - when: {limit_reached: any}          # must be the first rule when the profile has limits
    then: escalate
  - when: {kind: report, role: [code, stripe], outcome: success}
    then: reviewer
  - when: {pending_deltas: ">0"}
    then: orchestrator
  - when: {all_tasks: done, drift: false, pending_deltas: 0}
    then: final-gate
```

Rules are evaluated **in order; the first whose `when` fully matches wins** (all keys ANDed).

| Matcher | Value | True when |
|---|---|---|
| `kind` | string or list | the latest record's kind is (one of) |
| `role` | string or list | the latest record's role is (one of) |
| `outcome` | string or list | the latest record's `outcome` is (one of) |
| `limit_reached` | `any` / `true`, a limit name, list of names, `false` | some / that / none of the limits is reached; **a rule using it must be `next[0]`**, and when `limits` is non-empty `next[0]` must use it |
| `drift` | bool | uncovered `spec_impact` exists, or `--args drift=true` was passed (detect_drift exit 2) |
| `all_tasks` | `done` \| `open` | every non-cancelled task is done (and at least one task exists) / not |
| `pending_deltas` | int or quoted comparison (`">0"`, `">=2"`, `"==0"`) | number of spec-deltas `proposed`/`revise` |

`then` is a role from `roles`, `escalate` (the line includes the limit and task), or `final-gate`.
If nothing matches, `fallback` applies (`none` prints `NEXT: none (no rule matched)`).
Put event-specific rules (`kind: deploy-report ...`) **before** broad state rules (`all_tasks: done`),
otherwise the broad rule shadows them.

Output (stdout, one line): `NEXT: role=<role> agent=<a>[,<b>] rule=<n|fallback>`,
`NEXT: escalate [limit=<name> task=<id>] rule=<n>`, `NEXT: final-gate rule=<n>`.

## YAML subset (only this is supported)

Implemented in `scripts/_mini_yaml.py`, no third-party parser:

- block mappings and sequences by indentation (**spaces only**; a sequence may sit at the same
  indent as its key); sequence items may be scalars, flow values or block mappings
  (`- when: ...` + continuation lines aligned under `when`);
- one-line flow collections `{a: 1, b: [x, y]}` and `[a, b]`, nestable, with quoted strings;
- scalars: plain, `"double"`, `'single'`, `true`/`false`, `null`/`~`, integers, decimals;
- `#` comments at line start or after whitespace (outside quotes).

Not supported: anchors/aliases, tags, `|` / `>` block scalars, multi-line scalars, multiple
documents, tab indentation, complex keys. A value starting with `| > & * ! % @ \`` must be quoted
(for example `from: "@agent"`, `pending_deltas: ">0"`). Quote versions that must stay strings
(`"1.15"` would otherwise be a decimal).
