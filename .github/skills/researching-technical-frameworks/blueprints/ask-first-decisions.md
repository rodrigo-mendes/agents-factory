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

**Source**: [Technical Framework Researcher Prompt](../../prompts/technical-framework-researcher.prompt.md)

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

## Decision 3: Research Depth and Iteration Trade-off

### When this decision arises
When the user invokes a research command without specifying `RESEARCH_DEPTH` or `MAX_ITERATIONS`.
Present this decision before starting research so the user can calibrate quality vs time.

### Tradeoff matrix

| RESEARCH_DEPTH | Approx. time | Quality level | When to choose |
|---|---|---|---|
| `quick` | ~5 min | Overview only — no gap-loop, no triangulation | Spike, POC, already-known tech |
| `standard` | ~15 min | Production baseline — gap-loop active, single-source OK | Most new integrations |
| `deep` | ~30 min | High confidence — triangulation required, gap-loop active | Security-critical, complex migrations |
| `exhaustive` | ~60 min | Maximum confidence — parallel investigation (simulated), full triangulation | Greenfield architecture decisions |

### Default
If the user does not specify, use `exhaustive` (default per P1.parse). Ask only if there are
signs the user wants a quick answer (short question, spike context, "just a quick look").

### Ask-First format
> "I'll use **exhaustive** depth (≈60 min, maximum confidence) by default.
> If you'd prefer faster results at lower confidence:
> - `standard` — ~15 min, production baseline
> - `quick` — ~5 min, overview only
>
> Reply with your preferred depth or 'proceed' to use exhaustive."
