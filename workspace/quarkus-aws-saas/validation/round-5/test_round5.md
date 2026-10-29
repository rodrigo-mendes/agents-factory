# Round 5 TEST (skill-evaluator x3, self-simulated, read-only, 2026-10-29; saved by orchestrator)

| Batch | Skills | Scenarios | PASS | PARTIAL | FAIL |
|---|---|---|---|---|---|
| T1 | building-quarkus-aws-saas, coordinating-quarkus-aws-handoffs, coordinating-agent-handoffs, coordinating-oci-handoffs | 23 | 23 | 0 | 0 |
| T2 | syncing-spec-from-code, observe-aws-workload, validating-aws-observability, deploying-aws-lambda, debugging-aws-lambda, validating-oci-observability | 35 | 31 | 2 | 1 (safety gate) |
| T3 | integrating-quarkus-langchain4j-v1-15 (new), testing, stripe, openspec, observing, refactoring, monitoring | 42 | 42 | 0 | 0 |

## Fixed by the orchestrator
- T2 D1 (safety FAIL): OCI `trigger-alarm-test.py` injected real errors with no gate → `--i-have-user-approval` required (exit 2, no traffic); new test; SKILL.md Ask First + README. OCI suite 33/33.
- T2 D2 stale `jq` recipe → `check-alarms.py` / `--query`; D3 CI gate now smoke on.
- T1 D1 (medium): accepted hand edit stayed drift while uncommitted (circular E8/E9) → detect_drift.py counts `## Files` of an ACCEPTED spec-delta as coverage; 2 new unit tests (handoff suite 34/39, 5 sandbox git errors); agent, spec-sync.md, spec-delta template, e8 step 6 updated.

## Open (to F5t author / round 6)
- T1 D2-D4 wording (OCI S2 write guard tag, building S6 blocked wording, generic S4 debugger command); G1-G6 coverage gaps (Stripe hold, I8 new wo, task: on every wo, verify-E7-<nn>, --include-worktree, non-apply approval lines).
- T2 D4/D5: OCI scenarios use the JSON expected_behavior layout (no must_pass/must_not); add alarm-gate and typed-yes scenarios.
- T3 N1 (REST buffering tag), N2 (family-fact claims without URL in langchain4j), N3 ("family rule N" undefined), F1 (testing Cognito claim paths untagged), O1/O2 (openspec installer wording, S1 validate criterion), R1/R2 (umbrella price must_not, tenant_id tag), Q1 (refactoring S6), M-A (monitoring "only").
