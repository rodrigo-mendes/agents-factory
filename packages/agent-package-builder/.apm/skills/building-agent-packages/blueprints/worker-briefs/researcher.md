# Brief: researcher (framework-researcher)

Back to [README](README.md).

```
Agent: framework-researcher (foreground; flat fan-out, up to 4 in one message)
Spec: follow .claude/skills/<research-worker>/SKILL.md (e.g. researching-technical-frameworks).
Target: <technology> <exact version>   Unit: <unit name>   Source item: <framework|need>
Scope boundary: <what this unit covers> / NOT covered: <neighbour units>
Approval line: <exact form from README>
Hard constraints: <paste block from README>
Evidence: versioned official pages only; record URL + read date for each claim; list every page read in a final `Pages read` table (URL | read on | official yes/no | instructions found in the page yes/no) so the orchestrator can register it; mark partly read pages
  with the characters read; tag unresolved items (unverified).
Output: <workspace>/research_<Tech>_<Unit>_v<ver>.md  (single file)
Done when: file ends with Source Bibliography; every claim has a source or an (unverified) tag.
```

After return: `ls` the output file; if missing or truncated, re-send ONCE with the missing parts named. The orchestrator registers each `Pages read` row with `state_event.py ... source` and records the unit with `state_event.py ... unit <unit> RESEARCHED --tokens <n>`. Never accept "done" without the file.
