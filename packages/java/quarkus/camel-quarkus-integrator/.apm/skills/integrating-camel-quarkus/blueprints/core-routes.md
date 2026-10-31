# Core Routes Blueprint

Back to [SKILL.md](../SKILL.md). Shared workflow, structure skill and boundaries live there; this file holds only the core-routes specialty.

## Specializations

1. **Scheduled routes**: periodic execution, polling, cleanup, batch triggers.
2. **Internal routing**: `direct:` endpoints between specialties, asynchronous hand-offs, content-based, header-based and predicate routing, filtering, aggregation.
3. **Bean and logging steps**: calls to Java/CDI beans and log output inside routes.

Coverage note (documented gaps: timer, aggregation): no installed skill documents timer or SEDA endpoints, scheduler extensions (cron-style scheduling) or the aggregation EIP options. Confirm extension names and options in the Camel Quarkus 3.40.x extension reference and Camel 4.22.x component pages, and tell the user these parts are (unverified) until then.

## Required Skills

| Need | Skill |
|---|---|
| Always | `developing-camel-quarkus-core-v3-40` (BOM, route discovery, `direct:`, error handling, health) |
| Always | `structuring-camel-quarkus-projects` (paths, naming) |
| `bean:`, `class:`, `@Handler` calls | `developing-camel-quarkus-bean-v3-40` |
| CDI beans, qualifiers, injection | `developing-quarkus-arc-v3-40` |
| Log steps, masking, MDC | `developing-camel-quarkus-log-v3-40` |

## What to Ask

- Schedule period and timezone, or the event that triggers the route.
- Routing conditions (by body field, by header, by predicate) and what happens to non-matching messages.
- Whether a flow step must reply synchronously to the caller or can be asynchronous.

## Ask First Decisions

| Decision | Why it matters | Source of the options |
|---|---|---|
| Error handling per route | Default `onException` does not redeliver; `handled(true)` hides the failure from the caller; dead letter channel redelivery defaults (unverified) | Ask First "Error handling" row in the core skill |
| Aggregation strategy and completion condition | No installed skill covers it; ask for the rule before writing code | User |
| Routes that need `@Inject` or `@ConfigProperty` | Only then does the `RouteBuilder` get `@ApplicationScoped` | Core skill, Always Do |
| Bean naming for `bean:` lookups | `@Identifier` + `@Unremovable` vs `@Named` | Core and bean skills, Ask First tables |

## Quality Standards

### ✅ Always Do

- **Unique, descriptive `routeId` on every route** (team convention).
- **Plain `extends RouteBuilder`**; add `@ApplicationScoped` only for `@Inject` or `@ConfigProperty` (core skill).
- **Externalize periods, conditions and endpoint names** into configuration, not literals (team convention).
- **Name each `direct:` endpoint after the flow step** and document the expected body type (team convention).

### ⚠️ Ask First

- **Schedule and timezone** before writing any timer route (documented gap, see the coverage note above).
- **Routing conditions** before writing content-based routing.
- **Aggregation rules** before writing any aggregator (documented gap, see the coverage note above).
- **CamelContext lifecycle**: "Need to control routes via the Camel API? Quarkus drives the lifecycle (core skill, Quick Reference Bootstrap) (medium confidence)."

### 🚫 Never Do

- **Never hardcode intervals or routing conditions.** Instead: configuration properties (team convention).
- **Never add `@ApplicationScoped` to a route that injects nothing.** Instead: plain `RouteBuilder`.
- **Never state timer, SEDA or aggregation option names as verified.** Instead: tag them unverified and confirm against the reference.
