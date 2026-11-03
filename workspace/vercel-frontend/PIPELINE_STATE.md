# Pipeline state — vercel-frontend

```yaml
slug: vercel-frontend
mode: new
current_phase: P3
reconstructed: false
rounds: 1
variant: reference-only aggregator (no authored skills; upstream skills pulled by APM git deps)
```

## Approvals
| Gate | Date | Scope approved | User words |
|---|---|---|---|
| G1 | 2026-10-29 | approach | "Vendorizar originais (Recommended)" — superseded by the plan comment below |
| G1 | 2026-10-29 | scope | "React/Next.js núcleo, Design e UI, Extras, AI SDK UI" |
| G1 | 2026-10-29 | approach (revised) | "seria posisvel somente fazer um bridge como fizemos com openspec ou até soemnte fazer referencia a skills oficiail em um repositorio agraggator do APM" -> plan approved via ExitPlanMode |
| G1 | 2026-10-29 | install mode | "Instalar tudo dos repos" (whole repos, no path:) |
| G2 | 2026-10-29 | drop 3 path-only skills | "Tirar do pacote (Recommended)" |
| G2 | 2026-10-29 | commit generated .claude/ skills | "Commitar" |
| G3 | 2026-10-29 | commits 1+2 only, workspace out | "Sem workspace" |

## Units
| Unit | Skill name | State |
|---|---|---|
| 1 | vercel-react-best-practices (pilot) | PLANNED |
| 2-16 | see provenance.md | PLANNED |

## Log
- 2026-10-29  P0  state created; references resolved (provenance.md)
- 2026-10-29  P4  apm.yml switched to 11 whole-repo deps (user: "Instalar tudo dos repos"); install pending (sandbox blocks clone)
- 2026-10-29  P3  execution-1: 6/11 repos OK (44 skills), 5 failed; skill-creator collision (see execution-1/RESULT.md)
- 2026-10-29  P3  git global core.longpaths before change: <unset>; set to true. UNDO: git config --global --unset core.longpaths
- 2026-10-29  P3  execution-2: 8 whole-repo OK (33 skills, no collisions); all 3 path: deps fail with 'clone configuration probe'
- 2026-10-29  P4  removed json-render, migration-skills, before-and-after from apm.yml (8 repos remain)
- 2026-10-29  P8  root-install-2 (17:57-18:22, 1482s): 7/8 whole-repo OK; vercel/ai fails (dirty cached checkout: local changes would be overwritten); 3 path: deps fail (probe). 20 skill dirs in .claude/skills
- 2026-10-29  P8  re-commented 3 path: deps; removed dirty APM cache checkout fdc98e4e70aebb2d (vercel/ai @48ab95d6); retry 3
- 2026-10-29  P8  root-install-3 (1409s): only vercel/ai fails, reproducible on a fresh clone (checkout 'local changes would be overwritten')
- 2026-10-29  P8  vercel/ai commented out (user: "Tirar do pacote (Recommended)"); retry 4 with 7 repos
- 2026-10-29  P8  install-4 still resolved vercel/ai (manifest read race); dry-run confirms 7 repos; retry 5
- 2026-10-29  P8  install-5 OK (1397s): 41 deps, 20 vercel skills in .claude/skills; lock updated
