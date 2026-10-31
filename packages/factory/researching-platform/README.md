# researching-platform

15 platform-software research commands: the `researching-platform-software` router plus 14
specialized siblings (streaming brokers, RDBMS, document stores, caches, search engines, API
gateways, and more).

## This package installs as a whole — not by individual skill

All 14 siblings link `./blueprints/shared/` on the router (`researching-platform-software`) —
the 8-file output skeleton, research scope, reference-card template/example, cross-type modeling
principles, and the 3 deployment guides every sibling reuses. That shared content lives once, in
the router's own `blueprints/shared/`, by design (see `SKILL.md` for the rationale — it's the
correct owner because it already inventories these assets).

**Consequence:** `apm install --skill researching-rdbms` in isolation (without the router or its
siblings) will deploy a skill whose links into `../researching-platform-software/blueprints/shared/`
resolve to nothing. Install this package as a whole:

```bash
apm install --target claude ./packages/factory/researching-platform
```

not a hand-picked subset of its skills.

The router's own `SKILL.md` guards against exactly this at runtime — see "Verify the shared
assets exist before routing" in its ✅ Always Do, and Scenario 7 in
`researching-platform-software/blueprints/evaluation-scenarios.md` — but the cheaper fix is
simply not partial-installing this package in the first place.
