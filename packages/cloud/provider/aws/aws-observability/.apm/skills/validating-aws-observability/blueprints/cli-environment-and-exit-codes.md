# CLI environment, units and exit codes

Back to [SKILL.md](../SKILL.md). AWS CLI v2 reference 2.39.0 and the user guide, read 2026-10-28.

## Contents

- [Environment precedence](#environment-precedence)
- [Pager and output](#pager-and-output)
- [Retry mode](#retry-mode)
- [Return codes](#return-codes)
- [Time units per API](#time-units-per-api)
- [Windows notes](#windows-notes)
- [Script exit-code mapping](#script-exit-code-mapping)

## Environment precedence

- Command-line options override environment variables, and environment variables override profile settings ([env vars](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)).
- `AWS_REGION` overrides `AWS_DEFAULT_REGION` and the profile `region`; `AWS_PROFILE` selects the profile and `--profile` overrides it (same page).
- A Region must be set explicitly or by default; the scripts require `--region` or `AWS_REGION` and pass `--region` to every call.
- Credentials come only from the CLI chain (`AWS_PROFILE`, environment, SSO); the scripts never read them.

## Pager and output

- CLI v2 sends all output through the OS pager by default: `less` with `FRX` flags on Linux and macOS, `more` on Windows. `AWS_PAGER=""` disables it; `--no-cli-pager` does it per command ([pagination](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-pagination.html)).
- Always `--output json`. With `--output text` the output is paginated before `--query` runs, and the query runs once on each page; with `json` it runs once over the fully paginated structure ([filtering](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-filter.html)).
- `--query` is JMESPath built into the CLI and cannot parse a JSON string held in a field (`Segments[].Document`, `DashboardBody`); parse those with a JSON parser (the scripts use Python `json`; by hand, `jq` with `fromjson`).
- Do not confuse the CLI `--query` (filter) with `logs start-query --query-string` (the Insights query).

```bash
export AWS_PAGER=""
aws --region "$AWS_REGION" --output json --no-cli-pager logs describe-log-groups \
  --log-group-name-prefix "/aws/lambda/$FN" --query 'logGroups[].{n:logGroupName,r:retentionInDays}'
```

## Retry mode

Contradiction C1 (register I6): the two AWS pages disagree on the default retry mode, so set `AWS_RETRY_MODE` explicitly (scripts use `standard` unless you export another value).

- [Retries page](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-retries.html): standard mode "is the default mode for the AWS CLI version 2"; default max attempts 3 (2 retries); throttling errors and HTTP 500, 502, 503, 504 are retried; exponential backoff capped at 20 s. Adaptive mode is "experimental".
- [Environment variables page](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html): `AWS_RETRY_MODE` accepts "legacy (default), standard, and adaptive".

## Return codes

From the [return codes page](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-returncodes.html):

| Code | Meaning | Script reaction |
|---|---|---|
| 0 | success | continue |
| 1 | S3 transfer failure (S3 commands only) | not expected here; exit 3 |
| 2 | parse failure (all commands) | exit 3 |
| 130 | SIGINT | exit 3 |
| 252 | invalid syntax, unknown parameter or bad value | exit 3, fix the call |
| 253 | invalid environment or configuration (for example missing credentials) | exit 3, stop and do not retry |
| 254 | the service returned an error | exit 3 |
| 255 | the command failed; errors from the CLI or the service | exit 3 |

Read the code with `$?` in bash, `$lastexitcode` in PowerShell and `%errorlevel%` in cmd.

## Time units per API

| API | Parameter | Unit |
|---|---|---|
| `logs filter-log-events` | `--start-time`, `--end-time` | epoch milliseconds |
| `logs start-query` | `--start-time`, `--end-time` | epoch seconds, range inclusive |
| `cloudwatch get-metric-data` and other CLI `timestamp` parameters | `--start-time`, `--end-time`, `--start-date` | ISO 8601 or epoch seconds |
| `xray get-trace-summaries`, `start-trace-retrieval` | `--start-time`, `--end-time` | epoch seconds |

- `get-metric-data`: `StartTime` inclusive, `EndTime` exclusive; start times within the last 15 days round down to the minute, so align to the period.
- CLI v2 translates every response DateTime to ISO 8601 by default ([parameter types](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-parameters-types.html)). Some reference examples show epoch values or ISO strings that disagree with their descriptions (medium confidence); parse the documented structure, not the example.

```bash
END_S=$(date -u +%s)
START_MS=$(( SMOKE_START_S * 1000 )); END_MS=$(( END_S * 1000 ))              # filter-log-events
aws logs start-query --start-time "$SMOKE_START_S" --end-time "$END_S" ...    # seconds
M_START=$(( SMOKE_START_S / 60 * 60 )); M_END=$(( (END_S / 60 + 1) * 60 ))    # align to Period=60
```

## Windows notes

- The user guide's examples assume Linux-like shells; quoting differs by shell. Set the pager persistently on Windows with `setx AWS_PAGER ""`.
- `AWS_CLI_FILE_ENCODING` (for example `UTF-8` when the locale is `CP1252`) controls file encoding.
- `fileb://` paths resolve relative to the current working directory; the same for `file://` is (medium confidence), which is why `check-metrics.py` runs from the temp folder holding `q.json`.
- Run the scripts with `python` (the Windows launcher name) or `python3`. Git Bash conversion of arguments such as `/aws/lambda/x` passed to `python` is (unverified): AWS documents nothing. Test in the target shell and compare the group name that `describe-log-groups` returns.

## Script exit-code mapping

| Script exit | Cause |
|---|---|
| 0 | no check printed FAIL; WARN lines are inconclusive results and SKIPPED pillars also exit 0, so exit 0 does not mean every pillar is verified: those pillars are `not verified` and must be listed for E7 |
| 1 | at least one FAIL line |
| 2 | usage error, `aws` missing, AWS CLI v1 found, or `trigger-alarm-test.py` refused |
| 3 | any AWS CLI exit code from the table above, or any unexpected failure inside a script (for example malformed JSON from the CLI, which would otherwise end with a Python traceback and exit 1): the runner in `obs_common.py` catches it and exits 3 with an `ERROR: unexpected command failure` line |
