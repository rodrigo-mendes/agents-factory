# Tag notation and registers

Back to [SKILL.md](../../SKILL.md).

## Notation

- Plain parentheses: `(medium confidence)`, `(unverified)`. No bold, no brackets.
- A row with no page says `page not recorded` (never `none`, never a relative path).
- Severity wording in headings uses low|moderate|high, never the bare word "medium" (collides with confidence tags).

## Register (`blueprints/unverified-and-risks.md`)

Sections: `Version-lifetime risk`, unverified (U1..), irresolvable (I1..), medium (M1..), coverage limits (L1..), `Tag to register mapping`, `Source Bibliography`.

| Rule | Check |
|---|---|
| IDs are exactly `U1`, `I1`, `M1`, `L1` | no `U-1`, `MC1` variants |
| Header counts equal the listed items | script or manual count |
| Every tag used anywhere in the skill has a row in `Tag to register mapping` (columns: `Tag text used in the skill`, `Where`, `Register id`) | grep tags vs mapping |
| Facts that cannot be resolved from documentation are listed once, as U-ids with a note | no parallel class that contradicts the text tag |

## Mechanical help

`scripts/normalize_tags.py <dir> --write` rewrites bold/bracket variants to plain parentheses (idempotent). `scripts/verify_skill.py` checks headings, links, anchors, residues.
