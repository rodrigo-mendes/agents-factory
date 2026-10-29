# State layout: one file per thing, one writer per file

Back to [SKILL.md](../SKILL.md). Why: a single shared `PIPELINE_STATE.md` drifted in every past run (header phase behind the log, empty G3 rows, units stuck at AUTHORED, truncated log lines, a different format per run). Now state is split, append-only, and the dashboard is generated.

## Folders

```
workspace/<slug>/
  PACKAGE_BRIEF.md   _family_facts.md   _family_rules.md   research_*.md   (durable across executions)
  LATEST             one line: execution-<N>  (resume reads it)
  execution-<N>/     one per run or test run; a new run never overwrites an older one
    PIPELINE_STATE.md      GENERATED dashboard (scripts/render_state.py); never edited by hand
    .run.lock              pid host start; one session per execution
    state/phases/P<k>.md   rows: timestamp | start|done | actor | note
    state/gates/G<k>.md    write-once; scope + verbatim user words
    state/units/<unit>.md  rows: timestamp | STATE | score | tokens | actor | note
    state/events.log       timestamp | phase | actor | CODE | text (<= 200 chars)
    state/findings.md      F-<n>: OPEN -> FIXED | WONTFIX | DEFERRED | REOPENED (latest row wins)
    state/deferred.md      D-<n>: OPEN -> RESUMED -> CLOSED, with owner and resume trigger
    state/decisions.md     DEC-<n>: short ADR (gate, who, decision, reason)
    state/sources.md       URL, read date, official, injection suspected, used by
    state/environment.md   snapshots from snapshot_env.py (P0 and P8)
    state/metrics.md       estimate vs actual tokens/minutes per unit, phase or run
    state/retro.md         R-<n>: brief | known-failure | lesson
    state/shared-touch.md  shared files changed by this run (HEAD vs now hash)
workspace/.shared.lock    repo-wide: only one run edits shared files at a time
    rounds/round-<k>/      <validate|test|audit>__<target>.md + scoreboard.md
    plan/commit-plan.json  the only commit-plan name
    briefs/                every brief sent to a worker (audit trail for G2/G3)
```

The version of a family file lives inside it (column or header), not in its name. Older runs without `execution-<N>` are **legacy (execution-0)**: read-only, inspected with `inspect_workspace.py`, never written to.

## The only writer: `scripts/state_event.py`

| Moment | Command |
|---|---|
| P0, new run | `state_event.py workspace/<slug> init` (add `--inherit` to carry `findings.md`, `deferred.md`, `decisions.md` from the previous execution) then `lock` |
| phase boundaries | `phase P<k> start` / `phase P<k> done --note "<exit evidence>"` |
| G1, G2, G3 | `gate G<k> --scope "<what>" --words "<verbatim user answer>"` |
| unit transitions | `unit <unit> RESEARCHED\|AUTHORED\|VERIFIED\|VALIDATED [--score S] [--tokens N]` |
| confirmed review finding | `finding add --sev HIGH\|MEDIUM\|LOW --round round-<k> --target <skill> --text "..."` then `finding F-<n> FIXED\|REOPENED\|WONTFIX\|DEFERRED` |
| left for later | `defer add --owner <who> --trigger "<when to resume>" --text "..."`, later `defer D-<n> RESUMED\|CLOSED` |
| decision with a reason | `decide --gate G<k>\|none --who user\|orchestrator --text "..." --reason "..."` |
| page read | `source <url> --read-on YYYY-MM-DD --official yes\|no [--injection yes] --used-by <unit>` |
| environment | `snapshot_env.py --write workspace/<slug> --phase P0\|P8` (its own file, `state/environment.md`) |
| before any apm install | `preflight_apm.py --slug <slug> --log workspace/<slug>` (logs PREFLIGHT) |
| cost | `metric <scope> estimate\|actual --tokens N [--minutes M]` (prints BUDGET EXCEEDED over `token_budget`) |
| lesson | `retro add --kind brief\|known-failure\|lesson --target <t> --text "..."` |
| shared file changed | `shared-lock` first, then `touch <path> --note "..."`; `shared-unlock` at the end ([policy](policy/shared-files.md)) |
| anything else | `event <phase> <CODE> "<text>"` with CODE in ROUND_DONE, FIX, SWEEP, INCIDENT, DEFER, DISCREPANCY, NOTE |
| P9 done | `unlock` (a lock older than 12 h can be freed with `unlock --stale`; it is logged) |

`init --inherit` carries only live items: findings OPEN/REOPENED/DEFERRED and deferred OPEN/RESUMED (with their full history), plus all decisions. Pass `--actor <worker>` when writing on a worker's behalf. Refusals (exit 1) are the point: done without start, a second G1, a unit going backwards without `--note`, an unknown event code, a locked execution. Read the refusal, do not edit the file by hand.

## Dashboard and checks

- `render_state.py workspace/<slug>` after every phase boundary and before every gate; show its summary to the user. Same inputs give byte-identical output.
- `check_state.py workspace/<slug>` before G2, G3 and P9; exit 1 blocks the gate. It flags: a phase started before an earlier one is done (P7 is optional), P3/P4/P9 started without G1/G2/G3, units not VALIDATED/DEFERRED/DROPPED after P6, rounds missing a kind or misnamed, malformed events, a lock left after P9, no environment snapshot after P0, no PREFLIGHT before P8, a finding reopened twice without a decision, a HIGH finding open at G3/P9, a source read more than 12 months ago (injected pages are a warning), rounds over `max_rounds` or tokens over `token_budget` without a decision citing them, a touched shared file missing from the commit plan, P9 without the shared lock or a shared lock left after P9 (warnings: empty `briefs/`, no retro row at the end).

## Who writes what

| File | Writer |
|---|---|
| `state/**`, `PIPELINE_STATE.md` | orchestrator, through the scripts only |
| `rounds/round-<k>/*` | the worker when it can write; otherwise the orchestrator writes the inline report verbatim to the same path (the normal case, not the exception) |
| `briefs/*` | orchestrator, before sending the brief |
| `workspace/.shared.lock` | `state_event.py shared-lock` / `shared-unlock` only |
| `_family_*` | orchestrator only (authors never edit them) |
