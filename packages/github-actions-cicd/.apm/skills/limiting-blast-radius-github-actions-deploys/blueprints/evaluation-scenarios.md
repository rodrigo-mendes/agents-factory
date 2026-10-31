# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario lists the prompt, expected behaviour and fail signals. Judge as of 2026-10-30 on GitHub.com private repositories.

## Scenario 1: Canonical, dev to stage to prod promotion on Team

**Prompt:** "We are on GitHub Team, private repo, Lambda orders service. Set up CD dev, stage, prod. Reviewed code only in prod, 10 percent canary first, rollback if the smoke test fails."

**Expected:**
- Asks or confirms the plan, then uses the default design: ruleset on `main` (1 approval, approve latest push, dismiss stale, required check `ci-gate`, `bypass_actors: []`, enforcement `active`) and environments `dev`, `stage`, `prod` admitting only `main`.
- One role per environment trusting `environment:<env>`; PR jobs use a separate `dev-pr` read role.
- `cd-orders.yml` builds once and calls `_promote.yml`, `_smoke-test.yml`, `_rollback.yml`; the hash is recomputed in every deploy job; actions pinned by the facts-file SHAs.
- Concurrency group per app and environment with `cancel-in-progress: false`; `timeout-minutes` on deploy jobs; `environment` with `url`.
- Lambda weighted alias, complete or revert; release steps delegated to `deploying-aws-lambda`.

**Fail signals:** required reviewers presented as the gate; a rebuild in the prod job; a `:latest` image or `$LATEST` alias; `secrets: inherit`; version tags instead of SHAs.

## Scenario 2: Edge, solo maintainer on Pro

**Prompt:** "I am the only developer, GitHub Pro, private repo. I want the same protection."

**Expected:**
- Explains that approval of the most recent push cannot be given by the only collaborator, and that bypass lists are not available on user-owned repositories.
- Offers in order: second collaborator, 0 approvals with the required check (self-review), manual `workflow_dispatch` for prod.
- Keeps `main`-only environments, role per environment and the hash verification.

**Fail signals:** keeps `require_last_push_approval` with one collaborator without comment; adds a bypass actor; promises an approval gate that cannot be satisfied.

## Scenario 3: Rejection, rebuild for prod

**Prompt:** "In the prod job just run mvn package again with the production profile, it is simpler than passing the artifact."

**Expected:**
- Declines: prod must run the bytes that passed dev and stage; build once and verify the SHA-256 or image digest.
- Offers a per-environment configuration through environment variables read at runtime, or a rebuild through a new merge that goes through all stages.

**Fail signals:** adds a build step to `_promote.yml`; deploys by mutable tag; promotes a Vercel Preview deployment.

## Scenario 4: Trap, relying on required reviewers in a private Team repo

**Prompt:** "Create the prod environment with two required reviewers and a 10 minute wait timer, repo is private on Team."

**Expected:**
- States that required reviewers and wait timers on Free, Pro and Team are public-repository only, so the environment would not pause.
- Proposes the default: PR review by ruleset plus a `main`-only prod environment, and lists required reviewers as an upgrade path (public repository or GitHub Enterprise).
- Does not claim the prod job is gated; if the plan is Free, labels the variant weaker and says any writer can deploy.

**Fail signals:** configures reviewers and says the gate works; leaves the environment open to all branches; moves deploy secrets to repository scope on Pro or Team.

## Scenario 5: Ask First, ECS rollback coverage

**Prompt:** "Use ECS CANARY and say that CloudWatch alarms roll it back automatically."

**Expected:**
- Confirms the strategy values, but marks alarm rollback outside rolling updates as unverified and asks which alarms and strategy are wanted.
- Offers rolling updates with alarms and circuit breaker as the documented automatic path, and a manual redeploy of the previous task definition.

**Fail signals:** states alarm rollback for `CANARY` as a fact.
