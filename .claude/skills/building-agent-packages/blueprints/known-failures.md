# Known failures (from the Camel Quarkus build)

Back to [SKILL.md](../SKILL.md).

| Symptom | Cause | Countermeasure |
|---|---|---|
| Researcher returns with no file | it spawned background section-investigators whose results go to the main session | brief: "do not spawn investigators; fetch pages yourself"; re-send once if the file is missing |
| `/worker` cannot be run from the orchestrator | worker skills are `context: fork` + `disable-model-invocation` | launch the subagent with the worker SKILL.md as spec ([briefs](worker-briefs/README.md)) |
| Worker refuses "approval relayed" | it requires a genuine user approval at its P3 gate | get a real answer with the question tool, then relay it with exact attribution; never reword it stronger |
| Authored skills land in `.claude/skills/` | skill-creator writes there; `.claude/` is generated | brief the target `packages/<pkg>/.apm/skills/`; move outputs before `apm install` |
| Inferred claims presented as High (e.g. "mandatory", "must start with") | extrapolation beyond the page | evidence rule; orchestrator re-fetches the page; correct and record in `_family_facts` |
| Same fact differs between sibling skills | each author resolved it alone | `_family_facts` / `_family_rules`; P7 sweep |
| Validator HIGH is wrong or already fixed | validators over-flag or read stale files | re-check every HIGH against the file before fixing |
| Counts in docs wrong | numbers came from agent estimates | `scripts/check_counts.sh`; never copy a documented count |
| Lockfile hashes stale after edits | `apm.lock.yaml` not regenerated | `apm install`, then `--frozen` + `git diff --exit-code` |
| Foreign files staged (IDE), gitignored files added | `git add -A`, shared index | `scripts/commit_groups.py` explicit paths; `git reset -q` first |
| Files vanish or change by an unknown actor | external cleanup/IDE | `git status` before each commit; ask the user, do not "restore" blindly |
| `git push` denied | harness policy | not a workaround target; G4 is the user's |
| Hung loop, endless fixes | no stop rule | [triage and stop](policy/triage-and-stop-rules.md) |
