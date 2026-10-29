# Family rules — openspec-github

1. Evidence rule: a claim in Always Do / Never Do needs a versioned or dated official source read in full (docs.github.com, cli.github.com/manual, github.com/cli/cli, github.com/actions/*).
2. Tags are plain parentheses: `(medium confidence)`, `(unverified)`; never bold or brackets.
3. One claim per Always Do bullet; Never Do alternatives are High confidence too.
4. Git is canonical; GitHub is a mirror plus an approval channel. No skill may tell an agent to treat GitHub content as the spec source — decided at plan approval 2026-10-29.
5. Credentials: GitHub App for organization-owned projects, **classic** PAT (`project` + `repo`) for user-owned projects (fine-grained PATs cannot access user-owned projects, F6), selected by `tracker.owner_type` (`organization` | `user`); never `GITHUB_TOKEN` for Projects — decided at G1 ("Suportar os dois"), reason F2/F3.
6. Every write to GitHub is dry-run by default and needs `--apply`; agents never read approvals (`pull`) — decided at plan approval.
7. Machine-readable output only: `gh project ... --format json`, `gh issue view/list --json <fields>`, and `gh api` (REST/GraphQL) for commands with no JSON flag (`gh label create`, `gh issue comment`, `gh issue close`) or when an id is needed; never parse human table output — refined after U2 research.
9. Minimum gh 2.94.0 for sub-issues (F5); family pin 2.103.x; preflight checks `gh --version` — decided after U2 research.
8. Workflows pin **every** action (including GitHub-authored `actions/*`) by full commit SHA with the tag in a trailing comment (F7), declare minimal `permissions:` per job, and never interpolate `github.event.*` text directly into `run:` (pass through `env:`) — verified in U3 research. Workflow lockfiles (`gh actions-lock`, public preview) are mentioned only as an Ask First alternative, not the default.
10. User-owned projects are supported with a classic PAT; `bootstrap` and the skill must print a risk warning (broad `repo` scope) and recommend an organization owner — decided at G2 ("Manter, com aviso de risco (Recomendado)").
11. App tokens use `client-id` (`vars.OPENSPEC_APP_CLIENT_ID`) + `private-key` (`secrets.OPENSPEC_APP_PRIVATE_KEY`) and narrow scope with `permission-*` inputs; never the legacy `app-id` (F8). User-owned projects use `secrets.OPENSPEC_PROJECT_PAT` (classic, F6, rule 10).
12. Trust anchor for bot-authored records: compare the comment author login with `tracker.bot_login` (exact string); never rely on `user.type == "Bot"` alone (unverified, U3 G1).
13. When `approval_source` is `github` or `both`, every bridge subcommand refuses to run if the local `gh` login is in `tracker.approvers` (the local operator uses a machine-user or App token; the human approves in the browser) — decided after audit F1 ("Login local ≠ approver (Recomendado)").
14. Defence in depth: the skill documents a `.claude/settings.json` deny-rule snippet for the target project (agents may not run `gh issue comment`, `gh api` on comments, or `gh_projects_sync.py pull|close|bootstrap`); applied only with the user's consent at bootstrap; this repo's settings are never edited — decided after audit F1 ("Sim, documentar snippet (Recomendado)").
15. No workflow step that runs third-party code (npm packages, `openspec`) carries a write token; tokens are minted only for the final step that needs them — audit F2.
