# Non-interactive use and Windows (gh 2.103.x)

Back to [SKILL.md](../SKILL.md). Sources fetched 2026-10-29.

## Environment for scripts

```bash
export GH_TOKEN="$TOKEN"
export GH_PROMPT_DISABLED=1      # any value disables prompting
export NO_COLOR=1
export GH_NO_UPDATE_NOTIFIER=1   # the update notice goes to stderr
```

Source: https://cli.github.com/manual/gh_help_environment

- Always pass every required flag: `--title` plus `--body` or `--body-file` for `gh issue create`, `--owner` for projects, `-R owner/repo` for repository commands.
- What gh prints and returns in a non-TTY when a prompt would be needed is (unverified); never rely on it. See [register](./unverified-and-risks.md#unverified-4).
- Do not use `--web` or `--editor`; they open external programs. Source: https://cli.github.com/manual/gh_issue_create

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | failure |
| 2 | cancelled |
| 4 | authentication required |

Source: https://cli.github.com/manual/gh_help_exit-codes

## Python runner (representative; adapt to your environment)

```python
# gh 2.103.x: non-interactive runner with a serial, backoff-aware retry loop
import json, os, subprocess, time

ENV = {**os.environ, "GH_PROMPT_DISABLED": "1", "NO_COLOR": "1", "GH_NO_UPDATE_NOTIFIER": "1"}

def gh(*args, parse_json=True, mutating=False, retries=5):
    delay = 60                                    # docs: otherwise wait at least one minute
    for attempt in range(retries):
        p = subprocess.run(["gh", *args], capture_output=True, text=True, env=ENV, encoding="utf-8")
        if p.returncode == 0:
            if mutating:
                time.sleep(1)                     # docs: at least 1 s between mutative requests
            return json.loads(p.stdout) if parse_json and p.stdout.strip() else p.stdout
        if p.returncode == 4:                     # authentication required
            raise RuntimeError("gh auth required: " + p.stderr)
        if "rate limit" in p.stderr.lower() and attempt < retries - 1:   # stderr wording: (unverified)
            time.sleep(delay); delay *= 2; continue
        raise RuntimeError(f"gh {' '.join(args)} failed ({p.returncode}): {p.stderr}")
```

- Pass arguments as a list, never as a shell string; this avoids quoting differences between PowerShell, cmd and bash.
- For precise waits, run the call with `gh api -i` and read `retry-after` and `x-ratelimit-reset`.
- Write multi-line bodies to a file and use `--body-file` (file or `-` for stdin).

## Testing without GitHub

- Substitute the `gh` executable with a PATH shim that returns canned JSON and exit codes 0, 1 and 4, or inject the `subprocess.run` callable. No real calls in unit tests.
- This is generic engineering practice; no official gh mocking guidance was found (unverified).

```python
def fake_run(args, **kw):
    class P: returncode = 0; stdout = '{"id":"PVTI_x"}'; stderr = ""
    return P()
```

## Windows notes

- PowerShell: quote arguments that include `{owner}` or `{repo}` placeholders. Source: https://cli.github.com/manual/gh_api
- Default config directory on Windows is `$AppData/GitHub CLI` unless `GH_CONFIG_DIR` or `XDG_CONFIG_HOME` is set. Source: https://cli.github.com/manual/gh_help_environment
- Install or upgrade with the official WinGet package, then open a new terminal window because the installer changes PATH:

```powershell
winget upgrade --id GitHub.cli --source winget
gh --version      # expect gh version 2.103.x
```

Source: https://github.com/cli/cli/blob/trunk/docs/install_windows.md


## Verification commands (representative)

```bash
gh --version
gh auth status --json hosts --jq '.hosts'
gh api graphql -f query='{viewer{login}}'
gh project field-list 7 --owner my-org -L 100 --format json --jq '.fields[] | {id,name,type}'
gh project item-list 7 --owner my-org -L 1000 --format json --jq '.totalCount'
gh api repos/my-org/repo/issues/100/sub_issues --jq 'length'
```

These were not executed during research; the `.fields[]` and `.totalCount` paths are (medium confidence), see [register](./unverified-and-risks.md#medium-confidence-7).
