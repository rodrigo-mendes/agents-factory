# Publishing guide — common preparation

Step by step of what **you** run to take a bundle from the repository to the platforms. This guide
covers the common part; after it, follow the platform guide:
[SkillHQ](skillhq-guide.md) · [Agensi](agensi-guide.md). The strategy (what to sell and for how much) is in
[bundle-strategy.md](bundle-strategy.md).

Each step says **what to do**, **the command**, **what you should see** and **what to do if it fails**.

## 0. Before you start

- [ ] Branch `chore/packages-families` up to date: `git pull`.
- [ ] Python 3, Git and `apm` 0.35.0 installed: `python --version`, `git --version`, `apm --version`.
- [ ] Git with long paths enabled: `git config --global core.longpaths` answers `true`
      (if not: `git config --global core.longpaths true`).
- [ ] Node.js and npm, only if you will use SkillHQ: `node --version`, `npm --version`.
- [ ] Accounts on SkillHQ and/or Agensi (the guide for each platform explains how to create them).
- [ ] **Written authorization** to sell the content
      ([bundle-strategy.md, section 2](bundle-strategy.md#2-before-you-sell-blockers)).

## 1. Regenerate `.claude/` and the lock (outside VS Code)

`apm install` rewrites `apm_modules/` and fails when another program is watching that folder. VS Code
does this. So this step runs **with VS Code closed**.

```bash
# close VS Code; open "Git Bash" from the Start menu
cd /c/agents/agents-factory
rm -rf apm_modules
apm install --target claude
python scripts/restore-rule-metadata.py
python scripts/fix-cross-package-links.py
python packages/factory/agent-package-builder/.apm/skills/building-agent-packages/scripts/check_counts.py
```

**You should see:**
- `Installed N APM dependencies` at the end of `apm install`;
- `done -- N file(s) patched` and `done -- 0 link(s) fixed`;
- in `check_counts.py`: `skills 256`, `agents 54`, `rules 56` and `packages 39 (+ 19 bundles)`.

**If it fails:**

| Symptom | What to do |
|---|---|
| `WinError 5 Access is denied` or `WinError 145 The directory is not empty` | 1. Check in Task Manager that no `Code.exe` is open. 2. Run `apm install --target claude` again: the error is intermittent (in the tests, the 2nd or 3rd attempt passed). 3. If it continues, ask IT for an antivirus exclusion for `C:\agents\agents-factory\apm_modules`. 4. To avoid closing VS Code next time: `Settings → files.watcherExclude` → add `**/apm_modules/**`. |
| `Filename too long` | `git config --global core.longpaths true` and run again. |
| Counts different from the expected ones | Run `git status` and check whether a package was added or removed; the documented counts are in `CLAUDE.md`. |

Optional: `apm audit` to check the installation.

After that: `git status` shows `.claude/` and `apm.lock.yaml` changed. Commit those files together
with the changes in `packages/`.

## 2. Generate the sales packages

```bash
python scripts/export-bundle.py --all              # dry run: lists ✅ and ⛔ per bundle, writes nothing
python scripts/export-bundle.py stripe-for-java --apply
```

What the script does: it installs only the bundle into a temporary folder with a short name (`C:\tmp\ax\`), removes the Vercel
skills, applies the bundle's `export.yml` (if there is one), looks for sensitive data (client name,
emails, OCIDs, keys…) and, if everything is clean, writes:

```
dist/
├── stripe-for-java/claude/          ← folder for SkillHQ (README.md + .claude/)
└── stripe-for-java-claude.zip       ← same content, for Agensi
```

**You should see:** `✅ stripe-for-java  OK — 6 skills, 2 agents, 6 rules; zip 72 KB sha256 …`.

**If it fails:**

| Symptom | What to do |
|---|---|
| `⛔ <bundle> BLOQUEADO` | Open `dist/<bundle>/BLOCKED.txt`: each line gives the detector, the file and the line. Fix **at the source** (`packages/...`), redo step 1 and then step 2. Never edit `dist/` by hand. |
| `Another APM operation is still running` | APM accepts only one operation at a time on the machine (lock in `~/.apm`). Wait for the other one to finish; do not run step 1 and step 2 at the same time. |
| `⚠️ <bundle> INSTALL FAILED` | Windows file lock (close VS Code and run again) or a path that is too long: do not change the working folder to one longer than `C:\tmp\ax` (`--work`). |
| A bundle takes a long time | `saas-starter-team` downloads the Vercel repositories (about 25-40 min the first time). |

`dist/` is in `.gitignore`: nothing from it goes to Git.

## 3. Choose the platform

| I want to… | Follow |
|---|---|
| sell by download, one-time purchase, with a command line | [skillhq-guide.md](skillhq-guide.md) |
| sell by subscription, or reach agents beyond Claude | [agensi-guide.md](agensi-guide.md) |
| both | both, starting with the free test on each one |

## 4. Record the free test results

Fill this in after the free test on each platform (phase D of both guides). With this table we decide the
final format before publishing any paid bundle.

| Platform | Did it validate? | Was it approved? | What the buyer received (skills / agents / rules) | Error message | Date |
|---|---|---|---|---|---|
| SkillHQ | | | | | |
| Agensi | | | | | |

**Why test first:** both platforms document a `SKILL.md` at the root of the uploaded package.
What we export is the compiled directory (`.claude/skills/<name>/SKILL.md`, plus agents and rules). We do not
know yet whether the platforms accept this format.
