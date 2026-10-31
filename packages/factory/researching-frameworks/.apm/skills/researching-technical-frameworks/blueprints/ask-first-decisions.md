# Ask First Decisions — researching-technical-frameworks

Architectural crossroads that require clarification before starting a research task. Present the question, collect the answer, then proceed with the appropriate scope.

---

## Decision 1: Research Breadth — Minimal vs Standard vs Comprehensive

**Ask before starting any research task**:
> "What is the primary goal?
> A) Minimal — Single, focused pattern (e.g., 'async routes only')
> B) Standard — Complete skill covering all patterns (e.g., 'full FastAPI')
> C) Comprehensive — Framework change or version migration guide"

### Tradeoff Matrix

| Option | Scope | Time | Output Size | Best When |
|--------|-------|------|-------------|-----------|
| **Minimal** | Core patterns only, single concern | 1-2 hours | 5-10 pages | Single focused skill needed; tight deadline; well-understood technology |
| **Standard** | Full API surface + integrations | 4-6 hours | 15-25 pages | Complete skill required; team needs full reference; new technology adoption |
| **Comprehensive** | + Edge cases, migration guide, breaking changes | 8-12 hours | 30-50 pages | Framework version jump (e.g., FastAPI v0.99→v0.100); major API redesign |

### Decision Factors

- **Skill deadline**: Minimal if urgent, Comprehensive if planning ahead
- **Technology maturity**: New/beta → Standard or Comprehensive (docs change rapidly); stable GA → Minimal often sufficient
- **Integration partners**: 0-1 partners → Minimal; 3+ partners → Standard or Comprehensive
- **Migration requirement**: Breaking changes present → always Comprehensive

### Output Impact by Scope

```
Minimal  → research_FastAPI_AsyncRoutes_v0.100.md    (~8 pages)
Standard → research_FastAPI_v0.100.md                 (~20 pages)
Comprehensive → research_FastAPI_Migration_v0.99_to_v0.100.md  (~40 pages)
```

**Source**: [Researching Technical Frameworks](../SKILL.md)

---

## Decision 2: Cloud Provider — Terraform Research Targeting

**Ask when the technology is provider-specific IaC**:
> "Which cloud provider should Terraform research target?
> A) AWS — Largest ecosystem (200+ resources), most mature docs
> B) Google Cloud — Medium ecosystem (100+ resources), stable
> C) Azure — Medium ecosystem (120+ resources), stable
> D) Multi-Cloud — All providers + cross-cloud patterns (complex)"

### Tradeoff Matrix

| Option | Ecosystem | Provider Name | Maturity | Complexity | Documentation Quality |
|--------|-----------|---------------|----------|------------|----------------------|
| **AWS** | Largest (200+ resources) | `hashicorp/aws` | Most mature | High | Extensive, well-indexed |
| **Google Cloud** | Medium (100+ resources) | `hashicorp/google` | Stable | Medium | Good, some gaps in advanced features |
| **Azure** | Medium (120+ resources) | `hashicorp/azurerm` | Stable | Medium | Good, Azure docs required alongside Registry |
| **Multi-Cloud** | All above combined | Multiple | Variable | Very high | Complex — requires cross-referencing 3 providers |

### Decision Factors

- **Organization's cloud strategy**: Use the provider already in use
- **Documentation availability**: AWS has the densest official Terraform examples
- **Team expertise**: Match to team's existing cloud knowledge
- **Multi-region requirements**: Multi-cloud only if truly needed for the skill

### Research Scope Impact

```bash
# Single provider: researcher focuses on one provider's resource schemas
# registry.terraform.io/providers/hashicorp/aws/latest

# Multi-cloud: researcher must cross-reference 3 providers and document equivalences
# → Significantly increases research time (multiply estimated hours by 2-3x)
```

**Note**: If the skill is for a generic IaC pattern (e.g., "state management", "module design"), choose AWS as the reference provider and note that patterns are transferable to other providers with minor adjustments.

**Source**: [Terraform Registry Providers](https://registry.terraform.io/browse/providers)

---

## Decision 3: Research Depth — Gap-Filling Loop Strategy

**Ask when the caller has not supplied `depth` or `iterations`**:
> "How deep should this research go?
> A) quick — 1 source per section, no gap-filling. Fast results.
> B) standard — 2 sources for critical claims + changelog; gap loop up to MAX_ITERATIONS.
> C) deep — parallel sub-fetch per section + gap loop up to MAX_ITERATIONS + confidence scoring.
> D) exhaustive (default) — as deep + GitHub issues/RFCs scanned for caveats; every irresolvable gap documented."

### Tradeoff Matrix

| Option | Sources per Claim | Gap-Filling Loop | Changelog Fetch | Parallelism | Best When |
|--------|------------------|------------------|-----------------|-------------|-----------|
| **quick** | 1 primary | Disabled | No | No | Time-constrained spike; well-known stable tech |
| **standard** | 2 for Always-Do | Up to MAX_ITERATIONS | Yes | No | Normal skill authoring |
| **deep** | 2+ per claim | Up to MAX_ITERATIONS | Yes | Yes (Agent) | Wide API surface; many integrations |
| **exhaustive** | 2+ + community caveat scan | Up to MAX_ITERATIONS | Yes | Yes (Agent) | Security-critical; version migration; ambiguous docs |

### Decision Factors

- **Time available**: `quick` if urgent; `exhaustive` if quality matters more than speed
- **Security criticality**: Always `deep` or `exhaustive` for auth, encryption, secrets
- **Doc quality**: Sparse/beta docs → `exhaustive` (gap-loop catches more)
- **MAX_ITERATIONS**: Defaults to 5; lower for faster turnaround, higher for exhaustive coverage

### Iteration Limit Impact

```
iterations=1 → one pass; remaining gaps marked IRRESOLVABLE immediately
iterations=5 → default; balances coverage vs. time
iterations=10 → for deep dives on sparse-doc technologies
```

**Source**: [researching-technical-frameworks SKILL.md](../SKILL.md) — RESEARCH_DEPTH + MAX_ITERATIONS variables
