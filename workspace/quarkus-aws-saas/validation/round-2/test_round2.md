# Round 2 TEST (skill-evaluator, 2026-10-28; saved by orchestrator)
50/52 PASS. cognito 6/6 · lambda 6/6 · CQH 6/6 · CAH 6/6 · BQS 6/6 · OCI profile 4/5 · observe-aws-workload 5/6 · stripe 6/6 · quarkus-rest 5/5.
Both failures were SCENARIO defects, fixed by the orchestrator:
- observe-aws-workload S5 expected `partial` for a FAIL pillar (orchestrator's own earlier mapping error) → `failed` (agent rule + rule 14).
- OCI S5 required a command name `/provision-oci-infra` the skill never states → "@oci-terraform per the Hand off line".
Note: BQS knowledge-map.md:51 names quarkus-langchain4j in a fact row (LangChain4j deferred) — acceptable, watch.
