# Bootstrap and credentials

Orchestrator procedure; an agent never runs `bootstrap`. Back to [SKILL.md](../SKILL.md).

## Contents

- [Choose the credential path](#choose-the-credential-path)
- [Organization project: GitHub App](#organization-project-github-app)
- [User project: classic PAT](#user-project-classic-pat)
- [Bootstrap steps](#bootstrap-steps)
- [Deny rules for the target project](#deny-rules-for-the-target-project)
- [Local use](#local-use)

## Choose the credential path

`tracker.owner_type` selects the path (family rule 5, decided at G1 "Suportar os dois"):

| owner_type | Credential | Why | Source (read 2026-10-29) |
|---|---|---|---|
| `organization` | GitHub App installation token | recommended for organization projects; `GITHUB_TOKEN` cannot access projects | [Actions automation page](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions) |
| `user` | classic PAT, scopes `project` and `repo` | fine-grained PATs are not supported for user-owned projects (a listed, "not permanent" gap) | [PAT docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) |

Never `GITHUB_TOKEN` for Projects. Risk accepted at G2 ("Manter, com aviso de risco"): `bootstrap`
and every `owner_type: user` run print the broad-`repo`-scope warning, and an organization owner is recommended.

## Organization project: GitHub App

1. Create an App installed on the repository with **organization** projects read and write (repository
   projects permission is not enough), plus read access to pull requests and issues for project
   automation (F9), and issues write for the gate workflow.
2. For the archive workflow add contents write and pull-requests write ((unverified), register R11).
3. Store the App client id as variable `OPENSPEC_APP_CLIENT_ID` and the private key as secret
   `OPENSPEC_APP_PRIVATE_KEY`; the workflows use `actions/create-github-app-token` with `client-id`
   and narrow the token with `permission-*` inputs.
4. Set `OPENSPEC_BOT_LOGIN` to the App's bot login (form `name[bot]`, medium confidence); quote it in
   YAML. It must not be listed in `approvers`.

## User project: classic PAT

1. Use a **machine user** that can reach the repository; create a classic PAT with `project` and `repo`.
2. Store it as secret `OPENSPEC_PROJECT_PAT`; set `OPENSPEC_OWNER_TYPE` to `user`.
3. Set `OPENSPEC_BOT_LOGIN` to the machine user's login (not an approver).
4. Re-evaluate moving the project to an organization whenever fine-grained PATs gain user-project support.

## Bootstrap steps

1. Copy `assets/github.template.yaml` to `openspec/github-tracker.yaml` and fill `kind`, `owner`,
   `owner_type`, `project_number`, `repo`; keep `approval_source: chat` until the user chooses otherwise.
2. Dry-run: `gh_projects_sync.py bootstrap <repo> --change <id> --profile <yaml>` lists the missing
   fields (Stage, Kind, Change, Gate) and labels as `PLAN` lines.
3. Ask First, then apply with `--apply [--vendor] [--install-workflows]`. `--vendor` copies the five
   scripts of this skill, the five handoff-core scripts and the profile (as `handoff-profile.yaml`) into
   the `.github` directory's `openspec-github` subfolder, writes `MANIFEST.sha256` (CRLF-normalised
   hashes) and records `vendor: {version, sha256}`. `--install-workflows` also needs `--vendor`.
4. Add the Status option Blocked in the project settings if `bootstrap` warns that it is missing.
5. Set the repository variables and secrets from [workflows](./workflows.md#repository-settings).
6. Set `GH_TOKEN` to a machine-user token (an App installation token cannot read its login, so the preflight
   refuses it outside Actions; App tokens only inside Actions) whose login is **not** in `approvers`, ideally the
   `bot_login` identity (objects created by another login are not adopted by later runner pushes, register R8).
   With `approval_source` `github` or `both` every subcommand reads the token's login and exits 1 when it is an
   approver (family rule 13). Then `push` dry-run, `push --apply`, `status` (expect exit 0).
7. Before relying on gates, run the live smoke test: one `/approve` on a test change (typed in the browser by
   an approver), confirm the Stage `updatedAt` check passes (register R1).
8. Ask First: offer the deny rules below for the **target** project (this repository's settings are never edited).

## Deny rules for the target project

Defence in depth (family rule 14), applied only with the user's consent, in the target project's
`.claude/settings.json`:

```json
{
  "permissions": {
    "deny": [
      "Bash(gh issue comment:*)",
      "Bash(gh api *comments*)",
      "Bash(python *gh_projects_sync.py pull*)",
      "Bash(python *gh_projects_sync.py close*)",
      "Bash(python *gh_projects_sync.py bootstrap*)"
    ]
  }
}
```

The exact matcher syntax (prefix `:*` versus space-star, wildcard placement) is (medium confidence), register
R19: check the Claude Code settings documentation for the installed version and test that a denied command
is actually blocked. Deny rules do not replace the agent prompt limits or the login check.

## Local use

- Local `gh` needs a token matching `owner_type` in `GH_TOKEN`; `gh auth status` must succeed; the login must not be an approver (see step 6).
- `<repo-root>` is optional (default: the current directory); `--profile` is required (the error hints at it).
- A local gh older than 2.94.0 (for example 2.93.0) fails the preflight on purpose; upgrade to 2.103.x.
- Vendored copies cannot install workflows (the templates live next to the skill, not in the vendor folder).
