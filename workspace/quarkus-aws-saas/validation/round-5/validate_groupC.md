# Round 5 VALIDATE — group C (saved by orchestrator from the inline report, 2026-10-28)

| Skill | HIGH | MED | LOW | Score |
|---|---|---|---|---|
| structuring-quarkus-lambda-projects | 0 | 1 | 3 | 96.0 |
| refactoring-quarkus-java | 1 | 0 | 2 | 93.0 |
| deploying-aws-lambda | 0 | 4 | 2 | 89.0 |
| debugging-aws-lambda | 0 | 3 | 5 | 90.0 |
| validating-aws-observability | 1 | 1 | 3 | 90.0 |

- structuring M: Never Do "Hardcode packages or paths" team convention untagged. L: no URL :62,:67 (lock-file URL); "family fact 24" ref; N4 gap.
- refactoring H: method sourced from OCI skill refactoring-oci-java and OCI rule java-functions-clean-code (not shipped with quarkus-core). L: reviewer-checklist Source "register"; nested tags :65.
- deploying M: canary weight "no line kind" vs "each step an approved apply". M: cleanup `delete-function --qualifier` gated by free-text approval (no line kind). M: never-do/apply blueprints show mutating CLI without gate note. M: SKILL.md:85 function-updated-v2 after create (should be function-active-v2). L: I-class; register at 160 lines.
- debugging M: register row merged (U9 mapping broken). M: verdict-and-handoff:85 factory path D=packages/... M: SKILL.md:133 EventBridge 24 h/185 cited to Lambda page. L: start-live-tail; verify-E7-<nn> name; Insights gate in Never Do ✅; I-class; "In1 row NN" refs.
- VAO H: docs say "by default --skip logs,traces" but validate-observability.sh skips nothing by default → billable calls without approval. M: scripts don't enforce the approval (no flag, no plan line). L: >5 --trace-ids to batch-get-traces; workspace paths; I-class.
Cross-cutting: approval-lines.md has no kind for cleanup or canary weight steps.
