# Dependabot configuration

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Dependabot alerts, security updates and version updates are available on every plan, public and private.

Contents: [dependabot.yml](#dependabotyml) | [Behaviour](#behaviour) | [Ecosystem notes](#ecosystem-notes)

## dependabot.yml

One file at `.github/dependabot.yml` covering every ecosystem in the repository. Adjust directories to the real layout.

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: github-actions
    directories: ["/", "/.github/actions/*/*"]
    schedule: { interval: weekly }
    groups:
      actions-minor-patch: { patterns: ["*"], update-types: [minor, patch] }
  - package-ecosystem: maven
    directory: "/services/api"
    schedule: { interval: weekly }
    groups:
      maven-minor-patch: { patterns: ["*"], update-types: [minor, patch] }
  - package-ecosystem: gradle
    directory: "/services/worker"
    schedule: { interval: weekly }
  - package-ecosystem: npm
    directory: "/apps/web"
    schedule: { interval: weekly }
    groups:
      npm-dev: { dependency-type: development, update-types: [minor, patch] }
  - package-ecosystem: terraform
    directories: ["/infra/modules/*", "/infra/envs/*"]
    schedule: { interval: weekly }
  - package-ecosystem: docker
    directories: ["/services/*", "/apps/web"]
    schedule: { interval: weekly }
```

Source: https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference (2026-10-30).

## Behaviour

| Topic | Fact | Source |
|---|---|---|
| Location | the file lives in the `.github` directory of the repository | options reference |
| GitHub Actions | `directory: "/"` makes Dependabot search `/.github/workflows` and root `action.yml`; reusable workflows are also updated | keeping actions up to date |
| Ecosystem values | `github-actions`, `maven`, `gradle`, `npm` (also pnpm and yarn), `terraform`, `docker` | options reference |
| Globbing | `directories` supports globbing and `*` | options reference |
| Groups | combine matching updates in one pull request; first matching group wins; `update-types` accepts `minor`, `patch`, `major` | options reference |
| Limits | `open-pull-requests-limit` defaults to five per entry | options reference |
| Cooldown | a default 3-day cooldown applies to version updates, not to security updates | options reference |
| Private registries | by default only dependencies in publicly accessible registries are updated; declare `registries` for private ones | options reference |

Keeping actions up to date: https://docs.github.com/en/code-security/dependabot/working-with-dependabot/keeping-your-actions-up-to-date-with-dependabot (2026-10-30).

## Ecosystem notes

- SHA pins: Dependabot updates the semver in the trailing `# vX` comment when it updates a SHA-pinned action (medium confidence); the only statement is a 2022-10-31 changelog older than 12 months. Keep the `# vX` comment on every pin so it works. Changelog: https://github.blog/changelog/2022-10-31-dependabot-now-updates-comments-in-github-actions-workflows-referencing-action-versions/
- The `/.github/actions/*/*` glob matches the family composite-action layout `.github/actions/<domain>/<name>`; the exact depth is (medium confidence) because the docs confirm globbing, not this layout.
- Terraform: Dependabot lists support for Terraform up to 1.15.x while the family pins Terraform 1.17.1; modules using newer syntax may be skipped or mis-parsed (unverified). Watch the Dependabot logs and fall back to manual provider bumps.
- Dependabot pull requests pass through the same PR gate as any other change; they are not auto-merged by this skill.
- `trivy-action` and `checkov-action` pins are updated like any other action, but each update must be checked against the Trivy advisories before merge.
- Grouping reduces pull request volume; start with minor and patch groups and leave major updates ungrouped.
- Dependabot security updates open pull requests for vulnerable dependencies; they do not replace the Trivy gate, which also covers images and IaC.
