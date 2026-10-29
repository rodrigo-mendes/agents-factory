# handoff-core

Generic **agent handoff protocol v1**, shared by agent families (Quarkus/AWS, OCI).

| Kind | Name | Purpose |
|---|---|---|
| skill | `coordinating-agent-handoffs` | records (work-order, result, review, deploy/diagnosis report, spec-delta, escalation, verify, status), family profiles, parameterised limits + escalation, spec sync; stdlib Python scripts `check_records.py`, `board.py`, `detect_drift.py` + tests |
| command | `/syncing-spec-from-code` | on-demand code → spec sync (forks to `spec-synchronizer`) |
| agent | `spec-synchronizer` | spec review (E1/E3) and spec-delta proposals from drift (E8); never edits the spec |

Profiles plug in per family: `coordinating-quarkus-aws-handoffs` (package quarkus-aws-saas) and
`coordinating-oci-handoffs` (package oci-core). Record files never start with `report` (a Claude Code
subagent write guard on such names was observed in this build, (unverified), see the skill's register U2):
the factory convention is `result-NN-<role>.md`.

Tests: `python -m unittest discover -s scripts/tests` from the skill folder. Two drift tests create a
git repo in the temp directory; in sandboxes that forbid it they error out (see the build log).

The OpenSpec 1.15 skill `specifying-changes-with-openspec-v1-15` moved to the package `openspec-core` (dependency; name unchanged).

Depends on: factory-core, openspec-core. Used by: oci-core, quarkus-aws, aws-lambda, aws-observability, quarkus-aws-saas.
