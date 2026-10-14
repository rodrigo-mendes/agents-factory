# Data Transformation Blueprint

Back to [SKILL.md](../SKILL.md). Shared workflow, structure skill and boundaries live there; this file holds only the transformation specialty.

Contents: [Specializations](#specializations), [Required Skills](#required-skills), [What to Ask](#what-to-ask), [Ask First Decisions](#ask-first-decisions), [Quality Standards](#quality-standards).

## Specializations

1. **XML and Java objects**: JAXB marshal and unmarshal, XSD validation.
2. **XML stylesheets**: XSLT transformations (XML to XML or text).
3. **Mapping logic**: field mapping and business rules in Java beans.

Coverage note: no installed skill covers CSV, Excel, standalone JSON marshalling or generic format libraries. JSON binding inside REST DSL is covered by `developing-camel-quarkus-rest-v3-40`. For anything else, say it is not documented, ask whether to proceed, and offer `/researching-technical-frameworks`.

## Required Skills

| Need | Skill |
|---|---|
| Always | `developing-camel-quarkus-core-v3-40`, `structuring-camel-quarkus-projects` |
| Java objects to or from XML, XSD validation | `developing-camel-quarkus-jaxb-v3-40` |
| Stylesheet transformation | `developing-camel-quarkus-xslt-v3-40` |
| Mapping in Java beans | `developing-camel-quarkus-bean-v3-40`, `developing-quarkus-arc-v3-40` |
| JSON binding on REST endpoints | `developing-camel-quarkus-rest-v3-40` |

## What to Ask

- Input and output formats, and whether an XSD or stylesheet already exists.
- Validation rules and what happens to invalid input (reject, dead letter, log and skip).
- Maximum document size and whether native mode is a target.
- Whether all stylesheets are trusted, and whether any template or header can come from outside.

## Ask First Decisions

| Decision | Options | Source |
|---|---|---|
| JAXB vs jacksonxml | XSD-driven vs Jackson-annotated POJOs | Ask First in the JAXB skill |
| `contextPath` as package vs class | XJC output vs hand-written root | Ask First in the JAXB skill |
| `xslt` vs `xslt-saxon` | Xalan with documented hardening vs XSLT 3.0 features | Ask First in the XSLT skill |
| Large XML | Whole document vs tokenized streaming | Ask First in the JAXB skill |
| Dynamic templates | Fixed `classpath:` templates vs runtime-loaded | Ask First in the XSLT skill |
| Strict wrong-type handling | Pass-through vs fail fast | Ask First in the JAXB skill |

## Quality Standards

### ✅ Always Do

- **Set `contextPath` on every `JaxbDataFormat`** (JAXB skill, Always Do).
- **List every XSLT template in `quarkus.camel.xslt.sources`** and use `classpath:` URIs for native (XSLT skill, Always Do).
- **Validate input before transforming**, and log what was rejected and why (team convention).
- **Keep transformation routes free of I/O**: they receive and return a body through `direct:` (team convention).

### ⚠️ Ask First

- **Validation rules** and the handling of invalid input.
- **Output schema** when the target format is not fixed.
- **Native mode**: reflection registration for classes that JAXB creates through an `ObjectFactory`.

### 🚫 Never Do

- **Never lose data silently in a transformation.** Instead: log or route rejected records (team convention).
- **Never disable XSLT secure processing for untrusted templates.** Instead: leave `quarkus.camel.xslt.features` unset (XSLT skill).
- **Never use `xslt:file:` or `xslt:http:` in a native build.** Instead: `classpath:` templates.
- **Never describe JAXB as a JSON solution.** Instead: use the REST skill's JSON binding or declare the gap.
