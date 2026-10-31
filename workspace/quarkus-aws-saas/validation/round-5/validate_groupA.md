# Round 5 VALIDATE — group A (saved by orchestrator from the inline report, 2026-10-28)

| Skill | HIGH | MED | LOW | Score |
|---|---|---|---|---|
| developing-quarkus-amazon-lambda-v3-40 | 0 | 1 | 1 | 97.0 |
| developing-quarkus-amazon-lambda-http-v3-40 | 0 | 2 | 2 | 94.0 |
| securing-quarkus-lambda-cognito-v3-40 | 0 | 1 | 1 | 97.0 |
| integrating-quarkus-amazon-data-v3-40 | 0 | 3 | 2 | 91.5 |
| testing-quarkus-amazon-lambda-v3-40 | 1 | 2 | 3 | 87.5 |

- lambda M: ask-first:17 native build RAM 4-8 GB from partly read page untagged. L: SKILL.md:50 two claims.
- http M: SKILL.md:80 Never Do ✅ carries "(medium confidence)" → pointer only. M: cors.enabled default false / origins no default (L5 coverage) untagged. L: two URLs; ✅ leans on medium.
- cognito M: option-b defaults (forced-jwk-refresh 10M, resolve-early, cache-size, ttl, roles.source), SmallRye 60/30 min, deny-unannotated default false — summarised pages, untagged. L: Always Do caveat/conditional.
- data M: SKILL.md:109 unversioned guide URL. M: migration-notes:9 year-inferred dates untagged (M9). M: Dev Services image defaults untagged (L1/M10). L: I-class; two claims.
- testing H: Never Do "port keys the guide does not document" rests on medium/absence (M9; family fact 24 Medium) + hard guard grep. M: "Call real AWS" Never Do justified by a quote that doesn't forbid it (family policy). M: localstack:4.13 default untagged. L: scenario mapping row ids; two URLs; Quick Reference reconstructed code untagged.
