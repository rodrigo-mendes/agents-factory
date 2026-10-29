# Scripts: validating-aws-observability

Back to [SKILL.md](../SKILL.md). Python 3 scripts that prove, with calls that change no resource (two start a billable query or retrieval; one script, `trigger-alarm-test.py`, is mutating and gated), that the logs, metrics, traces, alarms and dashboards of a deployed Lambda work after a smoke test. Targets the AWS CLI v2 reference 2.39.0 and AWS docs read on 2026-10-28. The scripts are representative: the author never ran them against AWS; the offline tests below use a fake `aws`.

## Contents

- [Prerequisites](#prerequisites)
- [Files](#files)
- [Exit-code contract](#exit-code-contract)
- [Common options](#common-options)
- [Per-script options](#per-script-options)
- [Approval gate for billable reads](#approval-gate-for-billable-reads)
- [The mutating script and the approval flag](#the-mutating-script-and-the-approval-flag)
- [Design choices](#design-choices)
- [Offline tests](#offline-tests)
- [Known limitations](#known-limitations)

## Prerequisites

- Python 3 (standard library only) and the AWS CLI v2 (`aws --version` must start with `aws-cli/2.`). Nothing else. Run a script as `python3 scripts/<name>.py ...` from the skill folder; on Windows the interpreter is usually `python` (`python scripts\<name>.py ...`). Linux and Windows are both supported.
- Credentials and Region through the normal CLI chain (`AWS_PROFILE`, environment, SSO). The scripts never read or store credentials. A Region is required: `--region` or `AWS_REGION` (then `AWS_DEFAULT_REGION`).
- `VAO_AWS_CMD` overrides the AWS CLI command (default `aws`; split like a shell command line, Windows rules on Windows). The offline tests use it to select the fake; leave it unset for live use.
- Git Bash on Windows: the scripts call `aws` directly, but Git Bash can convert arguments such as `/aws/lambda/x` that it passes to `python`; AWS does not document this (register I5). When `MSYSTEM` is set the scripts print a note to stderr.
- IAM: the read set in [command allowlist and IAM](../blueprints/command-allowlist-and-iam.md). `trigger-alarm-test.py` additionally needs `cloudwatch:SetAlarmState`.

## Files

| File | Role | Mutating |
|---|---|---|
| `obs_common.py` | shared module imported from the script's own folder: result lines, option parsing, `run_aws`, exit-code mapping. Not executable on its own (exit 2) | no |
| `check-logs.py` | log group, retention, required JSON fields via Logs Insights | no |
| `check-metrics.py` | `AWS/Lambda` metrics and optional custom metrics via `get-metric-data` | no |
| `check-traces.py` | trace destination, X-Ray or Transaction Search read path, segment origins | no |
| `check-alarms.py` | alarm state, actions, SNS subscriptions | no |
| `check-dashboards.py` | dashboard body references against metrics, log groups and alarms | no |
| `validate-observability.py` | runs the five checks above and aggregates | no |
| `trigger-alarm-test.py` | `set-alarm-state ALARM` on one alarm, then reads the Action history | **yes**, approval flag required |
| `tests/run_tests.py` | offline tests with `tests/fakes/fake_aws.py` and `tests/fixtures/` | no |

## Exit-code contract

| Code | Meaning |
|---|---|
| 0 | no check printed FAIL (WARN lines allowed and mean inconclusive; SKIPPED pillars also exit 0, so exit 0 does not mean every pillar is verified: they are `not verified` and the E7 verifier must list them) |
| 1 | at least one check printed FAIL |
| 2 | usage error, missing tool (`aws`, AWS CLI v1), or `trigger-alarm-test.py` refused |
| 3 | AWS CLI error: the CLI exited 252, 253, 254, 255, 130 or another non-zero code; also any unexpected failure such as malformed JSON from the CLI (the runner in `obs_common.py` catches it and prints `ERROR: unexpected command failure ...`) |

CLI codes: 252 invalid syntax or parameter, 253 invalid environment or configuration such as missing credentials (stop, do not retry), 254 service error, 255 command failed. `validate-observability.py` exits 2 if any pillar script exited 2, else 1 if any pillar failed, else 3 if any pillar hit a CLI error, else 0. Output lines: `PASS`, `FAIL`, `WARN` (check name, detail) and one `SUMMARY` line. Only counts, ids and statuses are printed, never log messages or subscriber endpoints.

## Common options

`--region`, `--profile`, `--function`, `--start-s EPOCH` (smoke start, epoch seconds), `--window-min N` (default 15), `--max-polls N` (30), `--poll-seconds N` (2), `--wait-seconds N` (0, keep re-checking for late data), `--retry-seconds N` (15), `--help`. `check-traces.py`, `check-alarms.py` and `check-dashboards.py` accept `--wait-seconds` and `--retry-seconds` through these common options but ignore them (register L5).

## Per-script options

| Script | Required | Options |
|---|---|---|
| `check-logs.py` | `--function` or `--log-group` | `--fields A,B` (default `requestId,tenantId`; the first identifies application lines), `--min-events N`, `--allow-no-retention`, `--i-have-logs-insights-approval` |
| `check-metrics.py` | `--function` | `--min-invocations N`, `--max-errors N`, `--custom-namespace NS`, `--custom 'Name:Dim=Val,Dim2=Val2'` (repeatable), `--custom-stat STAT` |
| `check-traces.py` | `--function` | `--api-type REST\|HTTP\|NONE` (default NONE), `--trace-ids "ID ID"`, `--max-traces 1-5`, `--expect-aws-call NAME`, `--i-have-trace-retrieval-approval` |
| `check-alarms.py` | `--alarm-prefix P` or `--alarm-names A,B` | `--fail-on-insufficient-data` |
| `check-dashboards.py` | `--dashboard NAME` (repeatable) or `--dashboard-prefix P` | none |
| `validate-observability.py` | `--function` | every option above, forwarded to its script (the two approval flags go to logs and traces respectively); `--skip logs,metrics,...`; alarms and dashboards are SKIPPED without selectors |
| `trigger-alarm-test.py` | `--alarm-name NAME`, `--i-have-user-approval` | `--allow-composite`, `--reason TEXT`; `--wait-seconds` defaults to 60 and `--retry-seconds` to 5 here |

## Approval gate for billable reads

`check-logs.py` (Logs Insights `start-query`) and `check-traces.py` (X-Ray `start-trace-retrieval`) start a billable query or retrieval. Each is gated by a flag. Pass `--i-have-logs-insights-approval` (`check-logs.py`) only when the caller holds `approval: logs-insights scope=<log-group> window=<min> by=<user> at=<UTC> relayed-by=<orchestrator>` whose `scope` is the log group queried and whose `window` covers the query; pass `--i-have-trace-retrieval-approval` (`check-traces.py`) only with the same line for `scope=xray`. `validate-observability.py` forwards each flag to its pillar; there is no default skip, but without the flags no billable call is made: `check-logs.py` runs only the retention check and prints `WARN logs.query not verified ...`, `check-traces.py` on the Transaction Search path (destination `CloudWatchLogs`) prints `WARN traces.retrieval not verified ...` (the X-Ray `batch-get-traces` path is unchanged). Both exit 0; report those pillars as `not verified`. `--skip logs,traces` remains valid but is no longer the safety mechanism. A flag is a caller assertion: the script cannot verify the approval line itself.

## The mutating script and the approval flag

`trigger-alarm-test.py` is the only script that changes AWS state. Without `--i-have-user-approval` it prints `REFUSED`, makes no AWS call and exits 2. The agent passes the flag only when the orchestrator relayed the user's explicit approval for that exact alarm; an agent's own message, a plan comment or a previous run is never an approval. A composite alarm is refused unless `--allow-composite`. It sends nothing when `ActionsEnabled` is false or `AlarmActions` is empty. `validate-observability.py` never calls it.

## Design choices

- Every call uses `--output json` and the script parses it with Python `json` (jq-compatible helpers in `obs_common.py`), never `--query`: `--query` cannot parse JSON-in-string fields such as `Segments[].Document` and `DashboardBody`, and one parser keeps the fake `aws` simple. Manual `--query` and `jq` forms are in the pillar blueprints.
- One `run_aws` wrapper adds `--output json --no-cli-pager --region`, closes stdin, captures stderr and maps CLI exit codes to exit 3. `AWS_PAGER` is set empty and `AWS_RETRY_MODE` to `standard` unless already exported.
- Time units follow each API: Logs Insights `start-query` and X-Ray take epoch seconds, CloudWatch metrics take seconds aligned to the 60 s period.
- INSUFFICIENT_DATA is a WARN by default and an Insights count query with no result row is read as zero (medium confidence, register M12). Both are repo choices, not AWS statements.

## Offline tests

```sh
python3 scripts/tests/run_tests.py   # run from the skill folder; exit 0 = all passed
```

The runner sets `VAO_AWS_CMD` to `tests/fakes/fake_aws.py` (run with the same Python), so no real `aws` is called. The fake returns `tests/fixtures/<scenario>/<service>_<subcommand>.json` (scenario from `FAKE_AWS_SCENARIO`, default `green`) and can simulate a CLI exit code with `FAKE_AWS_EXIT` or an unknown parameter (exit 252) with `FAKE_AWS_REJECT_ARG`; it applies the `--namespace`/`--metric-name` filters of `list-metrics` like the service does. The call log is in `FAKE_AWS_LOG`. Covered: green path; a log line missing `tenantId`; no traces; Transaction Search (no `batch-get-traces` call); Lambda in PassThrough; REST and HTTP origin rules; an alarm in INSUFFICIENT_DATA; a pending SNS subscription; a dashboard widget naming a missing metric; metric aggregation per statistic (Duration maximum, custom Sum, Maximum, Minimum, Average labels); malformed JSON exiting 3; `--skip` with an unknown pillar name exiting 2; `trigger-alarm-test.py` refused without the flag, on a composite alarm without `--allow-composite`, and on an alarm already in `ALARM`; the `--alarm-types` fallback on CLI exit 252; the RECOVERY hint after a CLI error following `set-alarm-state`; CLI exit 253, 254 and 255 mapped to exit 3; static guards (no mutating subcommand outside the trigger script; `set-alarm-state` only in `trigger-alarm-test.py`; the only `start-*` verbs are `start-query` and `start-trace-retrieval`; no `--unmask`, `--interleaved`, `--output text`); every script compiles and answers `--help`. Last run 2026-10-28: 137 passed, 0 failed. To call a script without `python3` in front, it needs the executable bit (shebang `#!/usr/bin/env python3`).

## Known limitations

- Dashboard rendering cannot be proven through the API; the script ends with a WARN (K7 covers the partial check).
- `list-metrics` is not a freshness probe; a missing metric on a new dashboard may only be late (up to 15 minutes).
- Ingestion-to-query delay for logs is undocumented (register I1): use `--wait-seconds`; WARN means inconclusive.
- The `Spans[].Document` shape of `list-retrieved-traces` is (medium confidence); origin mismatches on that path are WARN, not FAIL.
- Metric math rows in dashboard widgets are skipped, not evaluated.
- No plan line before `start-query`: `check-logs.py` resolves the log group at run time and queries `--start-s` to now without printing either first, so the caller cannot match `scope` and `window` of the approval from the output; resolve them beforehand (register L5).
- The approval flags (`--i-have-logs-insights-approval`, `--i-have-trace-retrieval-approval`, `--i-have-user-approval`) are caller assertions: the scripts cannot verify the relayed approval line; the caller holds it.
- `--trace-ids` is not limited to 5 ids; `batch-get-traces` accepts 1 to 5, so pass at most 5 (only `--max-traces` is capped).
