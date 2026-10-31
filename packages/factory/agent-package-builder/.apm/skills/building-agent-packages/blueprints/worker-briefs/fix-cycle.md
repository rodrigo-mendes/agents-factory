# Brief: fix cycle (artifact-author)

Back to [README](README.md).

```
Agent: artifact-author (one skill per message; skills in parallel, <= 4)
Input: only the triaged findings for THIS skill (HIGH + cheap MEDIUM), each with its F-id, file, evidence, fix hint
Approval line + Hard constraints: <paste from README>
Rules: change only what a finding names; keep tags/registers consistent; do not touch _family_* files;
  if a finding contradicts a family fact, stop and report it.
Done when: scripts/verify_skill.py exits 0 and a list "F-id -> what changed" is returned.
```

After return: rerun the scripts, then the next P6 round re-evaluates only changed skills.
