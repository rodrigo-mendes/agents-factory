# Runners, Python scripts and offline linting (GitHub.com Actions, as of 2026-10-29)

Back to [SKILL.md](../SKILL.md). Sources fetched 2026-10-29.

## Hosted runner image

- `ubuntu-latest` is Ubuntu 24.04; image 20261026.354.1 ships GitHub CLI 2.103.2 and Python 3.12.3 (medium confidence: read from the runner-images list through research, not re-fetched).
- Images update weekly, so the preinstalled gh version moves without a repository change; the latest gh release (2.103.3) can be newer than the image.
- A `-latest` migration "is gradual and happens over 1-2 months"; pin `ubuntu-24.04` to avoid surprise migrations.
- Self-hosted runners must run Actions Runner v2.327.1 or newer for Node 24 actions.

Source: https://github.com/actions/runner-images ; https://github.com/cli/cli/releases

## gh in a job

```yaml
- name: Preflight
  env:
    GH_TOKEN: ${{ steps.app-token.outputs.token }}
  run: |
    gh --version        # expect 2.103.x; at least 2.94.0 for sub-issue flags
```

"GitHub CLI is preinstalled on all GitHub-hosted runners" and "you must set an environment variable called `GH_TOKEN`". Source: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-github-cli

## Python script reading the event from env

```yaml
- uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0   # v7.1.0
  with:
    python-version: '3.12'
- name: Handle comment
  env:
    GH_TOKEN: ${{ steps.app-token.outputs.token }}
    COMMENT_BODY: ${{ github.event.comment.body }}
    COMMENT_ID: ${{ github.event.comment.id }}
    ISSUE_NUMBER: ${{ github.event.issue.number }}
  run: python3 tools/handle_comment.py
```

```python
import os
body = os.environ["COMMENT_BODY"]          # untrusted text: parse strictly, never pass to a shell
issue = int(os.environ["ISSUE_NUMBER"])    # reject non-numeric values
```

- Python 3.12.3 is already the image default, so `setup-python` is only needed to pin a different version.
- Log the comment id and URL for audit; never log tokens.

Source: https://github.com/actions/setup-python/releases ; https://docs.github.com/en/actions/reference/security/secure-use

## Testing the handler without the network

```bash
# representative; the handler must read env and call gh through an injectable runner
export COMMENT_BODY='/approve' ISSUE_NUMBER=42 COMMENT_ID=1 GH_TOKEN=dummy
python3 -m pytest tests -q
```

Use a captured payload in the GitHub.com shape of 2026-10.

## Offline linting

| Tool | Owner | Class | Use |
|---|---|---|---|
| actionlint | `rhysd` (individual) | community, not official GitHub | syntax, expression types, `with:` inputs, shellcheck on `run:`, injection detection |
| act | `nektos` organization | community, no official GitHub endorsement found | runs workflows locally in Docker; differences from hosted runners are not listed on its README (unverified) |
| `gh actions-lock` | GitHub, per changelog | official, public preview | generates the workflow lockfile (medium confidence: preview) |

```bash
actionlint          # expected: no output, exit 0
```

Both community tools are optional aids, never a substitute for the checks in [security hardening](./security-hardening.md#verification-commands). Ask before adding them to CI. Sources: https://github.com/rhysd/actionlint ; https://github.com/nektos/act ; https://github.blog/changelog/2026-10-14-github-actions-workflow-lockfiles-in-public-preview/

## Production notes

- Always set `timeout-minutes`; the default is 360.
- App tokens last 1 hour; mint again in long jobs.
- Record `gh --version` in logs to explain behaviour changes after a weekly image update.
