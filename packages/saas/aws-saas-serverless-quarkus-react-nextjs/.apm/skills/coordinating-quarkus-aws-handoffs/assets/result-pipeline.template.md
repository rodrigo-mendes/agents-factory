---
kind: report
id: result-<nn>-pipeline
from: building-aws-saas-serverless-quarkus-react-nextjs   # the orchestrator writes it from read-only `gh` output; no agent produces it
to: building-aws-saas-serverless-quarkus-react-nextjs
change: <change-id>
role: pipeline-ci                # REQUIRED: pipeline-ci | pipeline-cd (without it the board derives `orchestrator`)
refs: []
outcome: success                 # success | partial | failed | needs-input
spec_impact: none
run_url: <https://github.com/<owner>/<repo>/actions/runs/<id>>
run_id: <id>
workflow: <ci-app | cd-app>
environment: <none | dev | prod>      # cd-app only
head_sha: <git sha of the run>
createdAt: <ISO 8601 UTC>
---

## Done

Which jobs ran and their result (build Java, build front, tests, scans, terraform plan comment, ci-gate; or apply, Lambdas, front, smoke, rollback).
`pipeline-ci`: `success` only when the required check `ci-gate` is green. `pipeline-cd`: `success` only when apply, deploy and smoke are green;
`failed` when any of them failed (counts in `deploy_cycles`); `partial` when the run is green but a step was skipped.

## Evidence

- Commands (read-only): `gh pr checks <pr>`, `gh run view <run_id>`, `gh run view <run_id> --log-failed` -> the lines that matter (redacted).
- `smoke_start_epoch`: <epoch seconds when the smoke step began> (cd-app; the observability window starts there).
- Artifact digest / version / alias / `out/` dirhash (`portable.py dirhash out`) promoted: <values>.
- Failed job: <name, step, error lines> (or "none").

## Spec impact

- none (a pipeline run changes no requirement).

## Suggested next step

`pipeline-ci` green: the user reviews the plan comment and merges (`gate=E7-merge`). `pipeline-ci` failed: the owner of the failing file fixes it (E6) and the user pushes again.
`pipeline-cd` green: `aws-observability` mode C, then `aws-lambda-debugger` mode B (+ `static-site-verifier` when the change has a front). `pipeline-cd` failed: `aws-lambda-debugger` mode A or the owner, per the failure table.
