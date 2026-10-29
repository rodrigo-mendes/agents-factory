# aws-observability

AWS observability for Lambda workloads (model: `oci-observability`).

| Kind | Names |
|---|---|
| skill | `validating-aws-observability` — live 5-pillar validation with read-only Python scripts (`check-logs.py`, `check-metrics.py`, `check-traces.py` incl. the Transaction Search path, `check-alarms.py`, `check-dashboards.py`, `validate-observability.py`); billable Logs Insights / trace retrieval need `--i-have-logs-insights-approval` / `--i-have-trace-retrieval-approval`; `trigger-alarm-test.py` is the only mutating script and refuses without `--i-have-user-approval` |
| command | `/observe-aws-workload <function> [region=] [mode=validate\|provision\|review]` |
| agent | `aws-observability` (spec review, offline observability Terraform, live validation) |
| rule | `aws-observability-skills` (routing) |

Scripts need Python 3 (standard library) and AWS CLI v2. Offline tests: `python3 scripts/tests/run_tests.py` (fake `aws`, no AWS
calls). Code instrumentation belongs to `observing-quarkus-lambda` (package quarkus-aws).

Depends on: factory-core, handoff-core, aws-skills, aws-terraform.
