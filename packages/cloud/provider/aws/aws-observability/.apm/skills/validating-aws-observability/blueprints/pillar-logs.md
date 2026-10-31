# Pillar: logs

Back to [SKILL.md](../SKILL.md). Script: `scripts/check-logs.py`. AWS CLI 2.39.0 reference and CloudWatch Logs docs read 2026-10-28. The manual `bash` forms below use `jq`; the Python scripts do not.

## Contents

- [Assertion chain](#assertion-chain)
- [Commands and JSON paths](#commands-and-json-paths)
- [Required fields](#required-fields)
- [Units and delays](#units-and-delays)
- [Limits and cost](#limits-and-cost)
- [Script behaviour](#script-behaviour)

## Assertion chain

1. The log group exists. Its name is `LoggingConfig.LogGroup` of the function, default `/aws/lambda/<function name>` ([get-function-configuration](https://docs.aws.amazon.com/cli/latest/reference/lambda/get-function-configuration.html)).
2. Retention is set: `logGroups[].retentionInDays` (1 to 3653 days) ([describe-log-groups](https://docs.aws.amazon.com/cli/latest/reference/logs/describe-log-groups.html)). Whether the field is absent when logs never expire is (unverified); the script treats absence as FAIL by repo policy.
3. At least N application JSON lines exist in the smoke window and each carries the required fields.

## Commands and JSON paths

| Step | Command | Read |
|---|---|---|
| group name | `lambda get-function-configuration --function-name F` | `.LoggingConfig.LogGroup` |
| retention | `logs describe-log-groups --log-group-name-prefix LG` | `.logGroups[] \| select(.logGroupName==LG) \| .retentionInDays` |
| start | `logs start-query --log-group-name LG --start-time S --end-time E --query-language CWLI --query-string Q` | `.queryId` |
| poll | `logs get-query-results --query-id ID` | `.status`, `.results[][]{field,value}`, `.statistics.recordsMatched` |

- `--log-group-name-prefix` and `--log-group-name-pattern` are mutually exclusive on `describe-log-groups`.
- `start-query` requires exactly one of `--log-group-name`, `--log-group-names`, `--log-group-identifiers` (each list up to 50) ([start-query](https://docs.aws.amazon.com/cli/latest/reference/logs/start-query.html)). The `--query-language` values are `CWLI`, `SQL`, `PPL`; the page states no default, so pass `CWLI`.
- `status` is one of `Scheduled`, `Running`, `Complete`, `Failed`, `Cancelled`, `Timeout`, `Unknown`; while `Running` only partial results come back, so retry on `Scheduled` and `Running` ([get-query-results](https://docs.aws.amazon.com/cli/latest/reference/logs/get-query-results.html)).
- Do not confuse `--query-string` (Insights) with the CLI `--query` (JMESPath).
- `start-query` is billed per GB scanned and needs `approval: logs-insights scope=<log-group> window=<min> by=<user> at=<UTC> relayed-by=<orchestrator>`. `check-logs.py` resolves the log group at run time (`LoggingConfig.LogGroup`, else `/aws/lambda/<function>`) and queries `--start-s` to now without printing them first (register L5): resolve them yourself and match `scope` and `window` before running. Pass `--i-have-logs-insights-approval` only with that relayed line; without the flag only the retention check runs, the field checks print `WARN logs.query not verified` and no `start-query` is made (exit 0): the pillar is `not verified`.

```bash
# lines carrying the anchor field, then lines missing the second field (documented functions only)
Q1='filter ispresent(requestId) | stats count(*) as n'
Q2='filter ispresent(requestId) and not ispresent(tenantId) | stats count(*) as n'   # expect n = 0
for i in $(seq 1 30); do R=$(aws --output json logs get-query-results --query-id "$QID")
  case "$(jq -r .status <<<"$R")" in Complete) break;; Scheduled|Running) sleep 2;; *) echo FAIL; exit 1;; esac; done
jq -r '.results[0][] | "\(.field)=\(.value)"' <<<"$R"
```

`sum(ispresent(...))` as an aggregation is (unverified); the two-query form uses only documented `ispresent()` and boolean `and`/`not` ([functions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-operations-functions.html)). A count query with no result row is read as zero (medium confidence).

## Required fields

- Family rule 7: log JSON with `requestId` and `tenantId`, no PII. The names are application-defined (emitted by the Quarkus JSON logger of `logging-quarkus-lambda-v3-40`), so the script takes them as `--fields`; they are (medium confidence) because Lambda's own JSON format uses the key `AWSrequestId` for Java ([log formats](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-cloudwatchlogs-logformat.html)).
- Lambda does not double-encode logs that are already JSON. Insights discovers Lambda fields only in the first embedded JSON fragment of each event, at most 200 fields, Standard log class only ([discovered fields](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_AnalyzeLogData-discoverable-fields.html)). With the Text log format, discovery is (medium confidence).
- Print counts only. `--unmask` needs `logs:Unmask` and is forbidden.

## Units and delays

- `start-query` and `--end-time` are epoch seconds and the range is inclusive; `filter-log-events` uses epoch milliseconds.
- The delay between a log line and its availability in Insights or `filter-log-events` is (unverified): poll until a deadline and report WARN (inconclusive), not FAIL.
- Query results are available for 7 days; a query times out after 60 minutes ([analyzing log data](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)).

## Limits and cost

- `DescribeLogGroups`, `StartQuery` and `GetQueryResults` default to 10 TPS per account per Region; `FilterLogEvents` is 25 TPS in us-east-1, 5 TPS in ap-northeast-3, ap-southeast-3, ca-west-1, eu-central-1 and il-central-1, 10 TPS elsewhere ([quotas](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/cloudwatch_limits_cwl.html)).
- 100 concurrent Logs Insights QL queries including dashboard queries; Insights is charged per GB of uncompressed data scanned, so keep the window to the smoke window.

## Script behaviour

`check-logs.py --function F [--fields requestId,tenantId] [--min-events N] [--wait-seconds N]` prints `logs.group`, `logs.retention`, `logs.events`, `logs.field.<name>`. Zero matching lines is WARN (inconclusive), fewer than `--min-events` is FAIL, a failed or timed-out query is FAIL or WARN. Exit codes: [CLI environment](./cli-environment-and-exit-codes.md#script-exit-code-mapping).
