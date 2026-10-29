# Always-do patterns (with commands)

Back to [SKILL.md](../SKILL.md).

| # | Pattern | How |
|---|---|---|
| 1 | Preflight before E1 and at each resume | `ls .claude/agents .claude/skills`; `python --version`; `openspec --version`; stop with the exact missing list |
| 2 | One validation chain after every record | `check_records.py` -> `detect_drift.py` -> `board.py`; read `NEXT:`; never skip because "nothing changed" |
| 3 | Gate answers verbatim | `## Approvals` line: `- <UTC> \| gate=<id> \| subject=<...> \| user said: "<verbatim>"`; cite in the brief with the approval line from [worker briefs](worker-briefs.md#approval-line) |
| 4 | Questions in rounds of at most 10 | numbered, concrete options, "not blocking" always allowed; playback after each block |
| 5 | Ask only what is missing | read `openspec/specs/**`, `proposal.md`, prior approvals before the round |
| 6 | Independent verification per passage | E1/E3 `spec-synchronizer`; E2/E4 `aws-architect`; I7 `quarkus-code-reviewer`; E7 `aws-lambda-debugger` mode B; gates by scripts |
| 7 | Re-run the build myself | `mvn -q verify` in the project before accepting `result-NN-code`; compare to the agent's claim |
| 8 | Real timestamps | `date -u +%Y-%m-%dT%H:%M:%SZ` for `createdAt`; placeholders are rejected by the checker |
| 9 | Save inline records for read-only agents | file name from the profile patterns, `saved-by: building-quarkus-aws-saas`, content verbatim |
| 10 | Hash the artifact and the plan | `sha256sum <zip>` for the work-order; for the plan, the deployer returns it and I recompute before relaying approval |
| 11 | Pass run arguments through the board | `board.py ... --args limits.review_rounds=4` (last on the line); `status.md` is the record of effective values |
| 12 | Escalate by record | `escalation-NN.md`: attempts, evidence (command output, `file:line`), hypothesis, 2-4 options with impact; reply verbatim under `## Answer` |
| 13 | Relay confidence tags | keep `(unverified)` / `(medium confidence)` exactly when telling the user or briefing an agent |
| 14 | State the version context | Quarkus 3.40 LTS, quarkus-amazon-services 3.23.x, OpenSpec 1.15.0, protocol v1; refuse silent drift to other lines |
| 15 | Tell the user what is not available or pre-release | LangChain4j on Quarkus is pre-release-locked (1.15.0.CR1), dashboards/SLO coverage gaps, pending agents/skills: before the plan, not after |
| 16 | Keep work-orders minimal and closed | requirements + scenarios + ADR paths + skills + limits + paths; an incomplete work-order only costs a `needs-input` round |
| 17 | Parallelise only independent tasks | disjoint files, <= 4 agents at once; collect all results, then run the chain per record |

## Verification Loop (self-check before reporting a phase done)

```bash
python <scripts>/check_records.py <handoff> --profile <profile>   # exit 0
python <scripts>/board.py <handoff> --profile <profile>           # one NEXT: line
python <scripts>/detect_drift.py <repo> --change <handoff> --include-worktree   # exit 0 before E9
openspec validate <id> --type change --strict --json --no-interactive
```
