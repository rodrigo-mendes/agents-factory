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
| Counts in docs wrong | numbers came from agent estimates | `scripts/check_counts.py`; never copy a documented count |
| Lockfile hashes stale after edits | `apm.lock.yaml` not regenerated | `apm install`, then `--frozen` + `git diff --exit-code` |
| Foreign files staged (IDE), gitignored files added | `git add -A`, shared index | `scripts/commit_groups.py` explicit paths; `git reset -q` first |
| Files vanish or change by an unknown actor | external cleanup/IDE | `git status` before each commit; ask the user, do not "restore" blindly |
| `git push` denied | harness policy | not a workaround target; G4 is the user's |
| Hung loop, endless fixes | no stop rule | [triage and stop](policy/triage-and-stop-rules.md) |

## From the 2026 runs in `workspace/` (aws-terraform, quarkus-aws-saas, langchain4j, openspec-github, terraform-agent)

| Symptom | Cause | Countermeasure |
|---|---|---|
| Dashboard phase behind the log (P3 shown, run at P8); G3 rows empty though approved; units stuck at AUTHORED after 7 rounds | one shared state file, rewritten by hand, no rule for who advances what | [state layout](state-layout.md): `state_event.py` only, `render_state.py` dashboard, `check_state.py` before gates |
| `inspect_workspace.py` lists no skills on Windows | `os.walk` returns backslash paths; suffix test used `/` | fixed (paths normalised); rerun inspect after upgrading |
| Each run named commit plans and round reports differently | no template, no naming rule | `plan/commit-plan.json`; `rounds/round-<k>/<kind>__<target>.md`; `check_state.py` flags others |
| A rerun or test overwrote the previous run's state | one folder per slug | one `execution-<N>/` per run; `init --inherit` carries only open findings, deferred items, decisions |
| Worker refused to write its report file | subagent write guard | the orchestrator writes the inline report verbatim to the same path, as the normal path |

## apm install recovery (what `preflight_apm.py` points to)

| Preflight message / install error | Recovery (ask the user before anything destructive) |
|---|---|
| another run holds `.run.lock` | wait for it to finish, or ask the user; never install over a live run |
| untracked or modified files in `.claude/` | the preflight groups them by owning package (`--package <yours>`): yours are a warning, others block; for others find the run (`git log`, its slug); save yours with `git stash push -- .claude apm.lock.yaml` |
| CRLF-only deployed copies / "modified since deployment" | the repo now has `.gitattributes` with `* text=auto eol=lf`; if it reappears, convert the working copy to LF (the index is already LF) |
| rules without `name:`/`description:`, links into `apm_modules/` after install | the post-install hooks did not run: `scripts/after_install.py` (always, right after every install) |
| package listed in the root apm.yml and reached transitively | remove the direct entry ("ambiguous resolved_by" in `apm audit --ci`) |
| content hash mismatch on a remote dependency | rerun once; if it repeats, log an INCIDENT and ask before `--force` or a lock regeneration |
| install "cleaned" hundreds of files of remote dependencies ("recovery incomplete", lock lost their entries) | `after_install.py` reports it; restore the files with `git ls-files --deleted -- .claude` + `git restore --source=HEAD`, then `merge_lock.py --package <yours> --apply` (HEAD lock + only your entries) and `after_install.py` again |
| "Installation refused ... conflicts with unmanaged file" | the file was in `.claude/` before apm deployed it (another run's partial copy, a hand copy), so the lock never recorded it; the preflight flags it. Delete `.claude/skills/<your skill>/` (generated) and reinstall |
| a skill or agent reads `workspace/<slug>/...` at runtime | `workspace/` exists only in the factory; ship the file in the skill (`references/`) and point readers at `.claude/skills/<skill>/references/...` |
| install hangs on a remote dependency | network or another package's remote deps; stop it, log an INCIDENT, do not retry in a loop |
