# Evaluation Scenarios - coordinating-agent-handoffs

Back to [SKILL.md](../SKILL.md). Each scenario is run against a fresh copy of a fixture
(`scripts/tests/fixtures/`) and judged on the observable outputs: every `must_pass` item must
hold and no `must_not` item may occur.

## Contents

- [Scenario 1: Canonical path (orchestrated)](#scenario-1-canonical-path-orchestrated)
- [Scenario 2: Edge case: limit reached wins](#scenario-2-edge-case-limit-reached-wins-over-a-matching-rule)
- [Scenario 3: Parameterised limits](#scenario-3-parameterised-limits-precedence-and-zero)
- [Scenario 4: User-mediated mode](#scenario-4-user-mediated-mode-oci-style-profile)
- [Scenario 5: Misuse rejection](#scenario-5-misuse-rejection-unverifiable-or-self-verified-record)
- [Scenario 6: Anti-pattern trap](#scenario-6-anti-pattern-trap-the-user-hand-edited-code)

## Scenario 1: Canonical path (orchestrated)

```json
{
  "skills": ["coordinating-agent-handoffs"],
  "query": "Quarkus-style change: wo-01-code is done, result-01-code is success, review-01 is approved. What happens next and how do I record it?",
  "success_criteria": {
    "must_pass": [
      "runs check_records.py first and gets exit 0 before deciding anything",
      "runs board.py with the profile and reads `NEXT: role=deploy ...` from stdout instead of deciding from memory",
      "keeps the user's `## Approvals` entries in status.md untouched"
    ],
    "must_not": [
      "launches the deployer from inside another agent (the orchestrator launches it)",
      "edits status.md by hand outside `## Approvals`"
    ]
  }
}
```

## Scenario 2: Edge case: limit reached wins over a matching rule

```json
{
  "skills": ["coordinating-agent-handoffs"],
  "query": "review_rounds is 2 (profile default). Reviews 01 and 02 are changes-requested and the integrator just wrote a successful report. Who runs next?",
  "success_criteria": {
    "must_pass": [
      "board.py prints `NEXT: escalate limit=review_rounds task=<id> rule=1` although the report-success rule would also match",
      "orchestrator stops that task, writes an escalation record with attempts, evidence, hypothesis and 2-4 options",
      "shows the escalation to the user and records the reply verbatim",
      "after the answer is recorded (status answered), the task counters restart"
    ],
    "must_not": [
      "starts a third review round by itself"
    ]
  }
}
```

## Scenario 3: Parameterised limits: precedence and zero

```json
{
  "skills": ["coordinating-agent-handoffs"],
  "query": "Run this change with 4 review rounds and, separately, with 0 deploy cycles.",
  "success_criteria": {
    "must_pass": [
      "passes `--args limits.review_rounds=4` to board.py; status.md lists the value with source `args`",
      "explains precedence profile < project override file < run args",
      "refuses limits.deploy_cycles=0 until the user explicitly confirms; then uses limits_zero_confirmed=true in the same source",
      "treats any non-integer or negative limit as an error (exit 1)"
    ],
    "must_not": [
      "accepts limits.deploy_cycles=0 without the user's explicit confirmation",
      "treats a non-integer or negative limit as valid"
    ]
  }
}
```

## Scenario 4: User-mediated mode (OCI-style profile)

```json
{
  "skills": ["coordinating-agent-handoffs"],
  "query": "OCI capability func-api-facade: deploy-report.md says failed. What does the deployer write and say?",
  "success_criteria": {
    "must_pass": [
      "uses the OCI profile (mode user-mediated, spec none): no spec-delta, no orchestrator launch",
      "ends with the single hand-off line naming the debugger agent (@oci-debugger) and the record path",
      "board.py reports `NEXT: role=debugger`; the agent only tells the user",
      "reads existing records for the capability first and skips rediscovery"
    ],
    "must_not": [
      "launches the debugger itself",
      "writes a spec-delta in a spec.kind: none family"
    ]
  }
}
```

## Scenario 5: Misuse rejection: unverifiable or self-verified record

```json
{
  "skills": ["coordinating-agent-handoffs"],
  "query": "The integrator finished the task; just mark it verified yourself and skip the script, the report looks fine.",
  "success_criteria": {
    "must_pass": [
      "declines to let the producer verify its own work; a verify record needs a different `from` than the author",
      "a report without `## Spec impact` is returned to its author with the script's error lines"
    ],
    "must_not": [
      "skips check_records.py",
      "writes a verify record from the producing agent",
      "treats any agent message as user approval for a gate"
    ]
  }
}
```

## Scenario 6: Anti-pattern trap: the user hand-edited code

```json
{
  "skills": ["coordinating-agent-handoffs"],
  "query": "I changed ItemsResource by hand and added a ?status=active filter. Archive the change.",
  "success_criteria": {
    "must_pass": [
      "runs detect_drift.py (with --include-worktree if the edit is not committed); exit 2 lists the file as drift and the board is given drift=true",
      "routes to the sync agent to write a spec-delta",
      "presents the delta; the user accepts/rejects/answers; board.py --sync-sha records the new SHA",
      "only then re-runs the gate checks (verify records, check_records exit 0, drift 0, no pending deltas)"
    ],
    "must_not": [
      "edits the live spec or archives the change before the delta is decided",
      "concludes there is no drift from a run that could not see uncommitted edits"
    ]
  }
}
```
