# Extraction heuristics

Back to [SKILL.md](../SKILL.md). What `poc_inventory.py` detects and what the `poc-spec-extractor` agent
does with it. The stack names below are **detection patterns only**; nothing in this package assumes a
stack, and requirements never name one.

## Contents

- [Order of trust](#order-of-trust)
- [Back end](#back-end)
- [Front end](#front-end)
- [Cross check](#cross-check)
- [What the script never does](#what-the-script-never-does)
- [When detection misses](#when-detection-misses)

## Order of trust

1. **OpenAPI / Swagger file** (`openapi:` or `swagger:` key) - the primary source of endpoints when present.
2. **Code** - routes, handlers, models, validations, error statuses.
3. **Tests** - test names become scenario candidates; a behaviour covered by a test gets `confidence: high`.
4. **Front end** - screens and calls; a behaviour seen only here gets `confidence: low`.

## Back end

| Inventory key | Detected from (examples, not a closed list) |
|---|---|
| `openapi[]` | `*.yaml`, `*.yml`, `*.json` with an `openapi`/`swagger` key; `paths` and HTTP methods read line by line (YAML) or parsed (JSON) |
| `endpoints[]` | JAX-RS `@Path` + `@GET`/`@POST`...; Spring `@RequestMapping` + `@GetMapping`...; Express/Fastify-like `app.get(...)`, `router.post(...)`; Nest `@Controller` + `@Get()`; Flask `@x.route(..., methods=[...])`; FastAPI `@x.get(...)`; ASP.NET `[Route]` + `[HttpGet]`; Go `r.GET(...)`, `HandleFunc("GET /x")`; Next.js `app/**/route.ts` exports and `pages/api/**` |
| `handlers[]` | serverless or function entry points (`RequestHandler`, `exports.handler`, `lambda_handler`, `@Funq`, `handleRequest(`) - events without an HTTP path |
| `models[]` | types named `*Request`, `*Response`, `*Dto`, `*Entity`, `*Model`, `*Command`, `*Event`, `*Payload`, `*Input`, `*Output`; classes under `@Entity`/`@Table`/`@Document`; pydantic models |
| `validations[]` | Bean Validation (`@NotNull`, `@Size`...), zod, Joi, pydantic `Field(...)` constraints |
| `errors[]` | explicit HTTP statuses (`.status(404)`, `Response.status(...)`, `HTTPException(...)`, `ResponseEntity.notFound`, `NotFound(...)`, `http.StatusX`) |
| `security[]` | auth signals (`@RolesAllowed`, `@PreAuthorize`, `[Authorize]`, JWT/Bearer, guards) |
| `shortcuts[]` | see [POC shortcuts](poc-shortcuts.md) |
| `tests[]` | `@Test` methods (with `@DisplayName` when present), `it(...)`/`test(...)`, `def test_*`, `func Test*` |

Config files (`.properties`, `.env*`, `.toml`, `.ini`, `.conf`) are scanned for shortcuts only.

## Front end

| Inventory key | Detected from |
|---|---|
| `routes[]` | Next.js `app/**/page.*` (route groups `(x)` and slots `@x` removed) and `pages/**`; `<Route path=...>`; `path: '...'` inside a router config (React Router, Angular, Vue) |
| `api_calls[]` | `fetch(url, { method })`, `axios.get(...)`, `http.post(...)`, `this.http.get<T>(...)`, `api.x(...)`, `client.x(...)` |
| `forms[]` | `<form`, `useForm(`, `FormGroup`, `onSubmit=`, `(ngSubmit)`, `@submit` |
| `states[]` | one entry per file and kind: `loading`, `error`, `empty`, `forbidden` |
| `shortcuts[]`, `tests[]` | same rules as the back end |

## Cross check

`cross` exists only when both roots are given. Paths are normalised: lower case, no scheme/host/query,
a leading `${BASE}` removed, and every parameter segment (`{id}`, `:id`, `[id]`, `<id>`, `${id}`) becomes `{}`.

- `matched` - same method (or `ANY`) and same path; a suffix match is accepted and flagged `match: suffix`
  (for example the front calls `/api/orders`, the back declares `/orders` under a base path).
- `front_only` - a call with no endpoint: the endpoint lives elsewhere, is missing, or the call is dead.
  **Always a question.**
- `back_only` - an endpoint no screen calls: an admin or machine API, or dead code. **Always a question.**

## What the script never does

It never executes, builds, installs or imports POC code; it skips `node_modules`, `target`, `build`,
`dist`, `.next`, `.git`, virtual environments and hidden folders; it skips files over `--max-bytes`
(default 1 MB) and stops after `--max-files` per root (default 5000), counting skips in `skipped_files`;
it never copies a secret value.

## When detection misses

Regular expressions miss some styles (routes built from variables, code-generated clients, routers in
config files of an unknown format). The agent then:

1. reads the entry points it can find (main class, `index.*`, `app.*`, router files) and adds what it
   sees with `confidence: medium` or `low`;
2. lists the gap in `questions.md` ("routes are built dynamically in `x:12`; which paths exist?");
3. returns `needs-input` only when nothing at all was found.
