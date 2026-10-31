#!/usr/bin/env python3
"""Inventory a proof of concept (back end and/or front end) for spec drafting.

Usage:
  python poc_inventory.py [--back <dir>] [--front <dir>] [--hint <stack>] [--json] [--out <file>]

Reads source files only; it never runs, builds or installs the POC. Detection is by regular
expressions over many stacks (JAX-RS, Spring, Express/Fastify/Nest, Flask/FastAPI, ASP.NET, Go,
Next.js route handlers and pages, React Router, Angular, Vue) plus OpenAPI files. Every finding
carries `file` (relative to its root, forward slashes) and `line`. Secret values are never
copied: a hard-coded secret is reported by file, line and kind only.

Output (JSON with --json or --out, a short summary otherwise):
  back:  openapi, endpoints, handlers, models, validations, errors, security, shortcuts, tests
  front: routes, api_calls, forms, states, shortcuts, tests
  cross: matched / front_only / back_only (front calls vs back endpoints)

Exit codes: 0 = inventory written, 2 = nothing detected (no endpoint, route, API call or
OpenAPI file), 1 = error (missing directory, no root given, unwritable --out).
Python 3.8+, standard library only.
"""
import argparse
import json
import os
import re
import sys

SKIP_DIRS = {
    "node_modules", "target", "build", "dist", ".next", ".nuxt", ".git", ".svn", ".idea",
    ".vscode", "venv", ".venv", "env", "__pycache__", "bin", "obj", "out", "coverage",
    ".gradle", ".mvn", "vendor", ".terraform", ".angular", ".turbo",
}
CODE_EXT = {
    ".java", ".kt", ".kts", ".scala", ".groovy", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
    ".py", ".cs", ".go", ".rb", ".php", ".vue", ".svelte", ".html",
}
SPEC_EXT = {".yaml", ".yml", ".json"}
CONFIG_EXT = {".properties", ".env", ".conf", ".toml", ".ini", ".config"}
HTTP_METHODS = ("GET", "POST", "PUT", "DELETE", "PATCH")
MAX_FILES_DEFAULT = 5000
MAX_BYTES_DEFAULT = 1000000

# --- back-end endpoint patterns -------------------------------------------------------------
RX_JAXRS_PATH = re.compile(r'@Path\(\s*"([^"]*)"')
RX_JAXRS_METHOD = re.compile(r'@(GET|POST|PUT|DELETE|PATCH)\b')
RX_SPRING_CLASS = re.compile(r'@RequestMapping\(\s*(?:value\s*=\s*|path\s*=\s*)?"([^"]*)"')
RX_SPRING_METHOD = re.compile(
    r'@(Get|Post|Put|Delete|Patch)Mapping(?:\(\s*(?:value\s*=\s*|path\s*=\s*)?"([^"]*)")?')
RX_NEST_CONTROLLER = re.compile(r"@Controller\(\s*['\"]([^'\"]*)['\"]")
RX_NEST_METHOD = re.compile(r"@(Get|Post|Put|Delete|Patch)\(\s*(?:['\"]([^'\"]*)['\"])?\s*\)")
RX_EXPRESS = re.compile(
    r"\b(?:app|router|server|fastify|api|routes|r)\.(get|post|put|delete|patch)\(\s*['\"`]([^'\"`]+)['\"`]")
RX_FLASK = re.compile(r"@\w+\.route\(\s*['\"]([^'\"]+)['\"](.*)")
RX_FASTAPI = re.compile(r"@\w+\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]")
RX_ASPNET_ROUTE = re.compile(r'\[Route\(\s*"([^"]*)"\s*\)\]')
RX_ASPNET_METHOD = re.compile(r'\[Http(Get|Post|Put|Delete|Patch)(?:\(\s*"([^"]*)"\s*\))?\]')
RX_GO = re.compile(r'\.(GET|POST|PUT|DELETE|PATCH)\(\s*"([^"]+)"')
RX_GO_HANDLEFUNC = re.compile(r'HandleFunc\(\s*"(?:(GET|POST|PUT|DELETE|PATCH)\s+)?([^"]+)"')
RX_NEXT_ROUTE_EXPORT = re.compile(r"export\s+(?:async\s+)?(?:function|const)\s+(GET|POST|PUT|DELETE|PATCH)\b")
RX_HANDLER = re.compile(
    r"(implements\s+RequestHandler|RequestStreamHandler|exports\.handler\s*=|export\s+(?:const|async function)\s+handler\b"
    r"|def\s+lambda_handler\(|@Funq\b|handleRequest\s*\()")

# --- models and validation ------------------------------------------------------------------
RX_MODEL = re.compile(
    r"\b(?:class|record|interface|type|struct)\s+([A-Z]\w*(?:Request|Response|Dto|DTO|Entity|Model|Command|Event|Payload|Input|Output))\b")
RX_ENTITY_ANN = re.compile(r"@(Entity|Table|Document|DynamoDbBean)\b")
RX_CLASS_NAME = re.compile(r"\b(?:class|record)\s+([A-Z]\w*)")
RX_PYDANTIC = re.compile(r"class\s+([A-Z]\w*)\((?:BaseModel|Schema|SQLModel)\b")
RX_VALIDATION = re.compile(
    r"@(NotNull|NotBlank|NotEmpty|Size|Min|Max|Email|Pattern|Positive|PositiveOrZero|Negative|Past|Future|Valid)\b"
    r"|\bz\.(?:string|number|object|array|enum)\(\)(?:\.\w+\([^)]*\))*\.(min|max|email|regex|nonempty|positive)\("
    r"|\bJoi\.\w+\(\)\.(?:\w+\([^)]*\)\.)*(required|min|max|email|pattern)\("
    r"|\bField\([^)]*(min_length|max_length|ge|le|gt|lt|regex|pattern)\s*=")

# --- errors ---------------------------------------------------------------------------------
RX_ERRORS = [
    re.compile(r"\.status\(\s*([1-5]\d\d)\s*\)"),
    re.compile(r"Response\.status\(\s*(?:Response\.Status\.)?(\w+)"),
    re.compile(r"HTTPException\(\s*(?:status_code\s*=\s*)?([1-5]\d\d)"),
    re.compile(r"ResponseEntity\.(status\(\s*[1-5]\d\d|notFound|badRequest|noContent|unprocessableEntity)"),
    re.compile(r"\b(NotFound|BadRequest|Unauthorized|Forbidden|Conflict)(?:Exception|Error|Result)?\("),
    re.compile(r"\bhttp\.Status(\w+)"),
    re.compile(r"StatusCode\(\s*([1-5]\d\d)"),
    re.compile(r"WebApplicationException\([^)]*?([1-5]\d\d)"),
]

# --- security signals and POC shortcuts -----------------------------------------------------
RX_AUTH = re.compile(
    r"@(RolesAllowed|PreAuthorize|Secured|Authenticated|UseGuards)\b|\[Authorize\b|passport\.|jsonwebtoken|\bjwt\b"
    r"|['\"]Authorization['\"]|\bBearer\b|Depends\(\s*\w*auth", re.IGNORECASE)
RX_SECRET = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|client_secret|clientsecret|api[_-]?key|apikey|access[_-]?key|private[_-]?key|token)"
    r"\b[\"']?\s*[:=]\s*[\"']([^\"'\s$%{}<>]{6,})[\"']")
RX_SECRET_CONFIG = re.compile(
    r"(?i)^\s*[\w.\-]*(password|passwd|secret|api[_-]?key|apikey|access[_-]?key|private[_-]?key|token)"
    r"[\w.\-]*\s*[:=]\s*['\"]?([^\s'\"$%{}<>]{6,})")
RX_CORS_ANY = re.compile(
    r"(?i)cors\(\s*\)|origin\s*:\s*['\"]\*['\"]|Access-Control-Allow-Origin['\"]?\s*[,:=]\s*['\"]\*"
    r"|allowedOrigins?\(?\s*[=:(]?\s*['\"]\*|AllowAnyOrigin\(\)|cors\.origins\s*[=:]\s*['\"]?\*")
RX_PERMIT_ALL = re.compile(r"\bpermitAll\(\)|@PermitAll\b|\[AllowAnonymous\]|@Public\(\)")
RX_TODO = re.compile(r"(?://|#|/\*|<!--|\*)\s*(TODO|FIXME|HACK|XXX)\b")
RX_LOCALHOST = re.compile(r"['\"`]https?://(localhost|127\.0\.0\.1)(:\d+)?")

# --- tests ----------------------------------------------------------------------------------
RX_TEST_ANN = re.compile(r"@(Test|ParameterizedTest)\b|\[(Fact|Test|Theory|TestMethod)\]")
RX_METHOD_NAME = re.compile(r"\b(?:void|async\s+Task|Task|public\s+void|fun)\s+(\w+)\s*\(")
RX_TEST_NAMED = re.compile(r"\b(?:it|test)\(\s*['\"`]([^'\"`]+)['\"`]")
RX_PY_TEST = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)\s*\(")
RX_GO_TEST = re.compile(r"^func\s+(Test\w+)\s*\(")
RX_DISPLAY = re.compile(r'@DisplayName\(\s*"([^"]+)"')

# --- front end ------------------------------------------------------------------------------
RX_RR_ROUTE = re.compile(r"<Route\b[^>]*\bpath\s*=\s*[{]?\s*['\"`]([^'\"`]+)['\"`]")
RX_PATH_KEY = re.compile(r"\bpath\s*:\s*['\"`]([^'\"`]*)['\"`]")
RX_ROUTER_HINT = re.compile(r"createBrowserRouter|createRouter|RouterModule|Routes\b|VueRouter|routes\s*[:=]")
RX_FETCH = re.compile(r"\bfetch\(\s*([`'\"])(.+?)\1")
RX_FETCH_METHOD = re.compile(r"method\s*:\s*['\"`](GET|POST|PUT|DELETE|PATCH)['\"`]", re.IGNORECASE)
RX_CLIENT_CALL = re.compile(
    r"\b(?:axios|http|httpClient|this\.http|api|client|\$http|ky|request)\.(get|post|put|delete|patch)"
    r"(?:<[^>()]*>)?\(\s*([`'\"])(.+?)\2", re.IGNORECASE)
RX_FORM = re.compile(r"<form\b|useForm\(|\bFormGroup\b|\bFormBuilder\b|onSubmit\s*=|\(ngSubmit\)|@submit")
RX_STATES = [
    ("loading", re.compile(r"\b(isLoading|loading|isPending|isFetching|Spinner|Skeleton)\b")),
    ("error", re.compile(r"\b(isError|error\s*&&|\.error\b|ErrorBoundary|catch\s*\()")),
    ("empty", re.compile(r"\.length\s*===?\s*0|\bisEmpty\b|\bno\s+\w+\s+(?:found|yet)\b", re.IGNORECASE)),
    ("forbidden", re.compile(r"\b(403|401|forbidden|unauthori[sz]ed|not\s+allowed)\b", re.IGNORECASE)),
]

PARAM_SEG = re.compile(r"^(\{[^}]*\}|:[^/]+|\[[^\]]*\]|<[^>]*>|\$\{[^}]*\}|\*+)$")


class InventoryError(Exception):
    pass


def _walk(root, max_files, max_bytes):
    files, skipped = [], 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(filenames):
            ext = os.path.splitext(name)[1].lower()
            if ext not in CODE_EXT and ext not in SPEC_EXT and ext not in CONFIG_EXT and not name.startswith(".env"):
                continue
            path = os.path.join(dirpath, name)
            try:
                if os.path.getsize(path) > max_bytes:
                    skipped += 1
                    continue
            except OSError:
                continue
            if len(files) >= max_files:
                skipped += 1
                continue
            files.append(path)
    return files, skipped


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def _rel(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


def _join(*parts):
    segs = []
    for part in parts:
        if part:
            segs.extend(s for s in part.strip().split("/") if s)
    return "/" + "/".join(segs)


def normalize_path(path):
    """Lower-case path with parameter segments as {} and no query, scheme, host or base var."""
    p = path.strip()
    p = re.sub(r"^\$\{[^}]*\}", "", p)
    p = re.sub(r"^\w+\s*\+\s*['\"`]?", "", p) if p and p[0].isalpha() and "+" in p else p
    p = re.sub(r"^https?://[^/]+", "", p)
    p = p.split("?")[0].split("#")[0]
    segs = [s for s in p.split("/") if s]
    out = ["{}" if PARAM_SEG.match(s) else s.lower() for s in segs]
    return "/" + "/".join(out)


def _is_test_path(rel):
    low = rel.lower()
    return ("/test/" in "/" + low or "/tests/" in "/" + low or "__tests__" in low
            or re.search(r"(\.|_)(test|spec)\.\w+$", low) is not None or re.search(r"(^|/)test_\w+\.py$", low) is not None
            or re.search(r"Tests?\.(java|kt|cs)$", rel) is not None or low.endswith("_test.go"))


def _is_mock_path(rel):
    low = rel.lower()
    return re.search(r"(^|/)(mocks?|fakes?|stubs?|fixtures?|seed|dummy)(/|\.|_)", low) is not None


# --- OpenAPI --------------------------------------------------------------------------------
def _openapi_endpoints(rel, text):
    eps = []
    head = text[:2000]
    if not re.search(r"['\"]?(openapi|swagger)['\"]?\s*:", head):
        return None
    if rel.lower().endswith(".json"):
        try:
            doc = json.loads(text)
        except ValueError:
            return []
        for path, ops in (doc.get("paths") or {}).items():
            for method in (ops or {}):
                if method.upper() in HTTP_METHODS:
                    eps.append({"method": method.upper(), "path": path, "file": rel, "line": 0,
                                "source": "openapi"})
        return eps
    in_paths, cur_path, path_indent = False, None, None
    for no, line in enumerate(text.splitlines(), 1):
        if re.match(r"^paths\s*:\s*$", line):
            in_paths = True
            continue
        if in_paths and re.match(r"^\S", line):
            in_paths = False
        if not in_paths:
            continue
        m = re.match(r"^(\s+)['\"]?(/[^'\":]*)['\"]?\s*:\s*$", line)
        if m and (path_indent is None or len(m.group(1)) == path_indent):
            path_indent, cur_path = len(m.group(1)), m.group(2)
            continue
        m = re.match(r"^\s+(get|post|put|delete|patch)\s*:\s*$", line, re.IGNORECASE)
        if m and cur_path:
            eps.append({"method": m.group(1).upper(), "path": cur_path, "file": rel, "line": no,
                        "source": "openapi"})
    return eps


# --- back end -------------------------------------------------------------------------------
def _endpoints_from_code(rel, text, lines):
    eps = []
    low = rel.lower()
    # Next.js route handlers: app/**/route.(ts|js) and pages/api/**
    m = re.search(r"(?:^|/)app/(.*?)/?route\.(?:ts|js|mjs|tsx|jsx)$", rel)
    if m is not None or re.search(r"(?:^|/)app/route\.(?:ts|js)$", rel):
        seg = m.group(1) if m else ""
        path = _join(*[s for s in seg.split("/") if not (s.startswith("(") and s.endswith(")"))])
        for no, line in enumerate(lines, 1):
            mm = RX_NEXT_ROUTE_EXPORT.search(line)
            if mm:
                eps.append({"method": mm.group(1), "path": path, "file": rel, "line": no,
                            "source": "nextjs-route"})
        return eps
    m = re.search(r"(?:^|/)pages/(api/.*)\.(?:ts|js)$", rel)
    if m:
        path = _join(re.sub(r"/index$", "", m.group(1)))
        return [{"method": "ANY", "path": path, "file": rel, "line": 1, "source": "nextjs-pages-api"}]

    class_path = ""
    seen_class = False
    pending = None  # (method, line_no, method_path)
    for no, line in enumerate(lines, 1):
        stripped = line.strip()
        # JAX-RS / Spring / ASP.NET class-level prefixes
        if not seen_class:
            for rx in (RX_JAXRS_PATH, RX_SPRING_CLASS, RX_ASPNET_ROUTE, RX_NEST_CONTROLLER):
                mm = rx.search(stripped)
                if mm and not RX_JAXRS_METHOD.search(stripped):
                    class_path = mm.group(1)
            if re.search(r"\b(class|record|interface)\s+\w+", stripped):
                seen_class = True
                continue
        # JAX-RS method: @GET with @Path on a nearby line
        mm = RX_JAXRS_METHOD.search(stripped)
        if mm and seen_class:
            pending = [mm.group(1), no, ""]
            continue
        if pending is not None:
            pm = RX_JAXRS_PATH.search(stripped)
            if pm:
                pending[2] = pm.group(1)
                continue
            if stripped.startswith("@") or not stripped:
                continue
            eps.append({"method": pending[0], "path": _join(class_path, pending[2]), "file": rel,
                        "line": pending[1], "source": "jax-rs", "handler": _method_name(stripped)})
            pending = None
            continue
        mm = RX_SPRING_METHOD.search(stripped)
        if mm:
            eps.append({"method": mm.group(1).upper(), "path": _join(class_path, mm.group(2) or ""),
                        "file": rel, "line": no, "source": "spring"})
            continue
        mm = RX_NEST_METHOD.search(stripped)
        if mm and low.endswith(".ts"):
            eps.append({"method": mm.group(1).upper(), "path": _join(class_path, mm.group(2) or ""),
                        "file": rel, "line": no, "source": "nest"})
            continue
        mm = RX_ASPNET_METHOD.search(stripped)
        if mm:
            eps.append({"method": mm.group(1).upper(), "path": _join(class_path, mm.group(2) or ""),
                        "file": rel, "line": no, "source": "aspnet"})
            continue
        if low.endswith(".py"):
            mm = RX_FASTAPI.search(stripped)
            if mm:
                eps.append({"method": mm.group(1).upper(), "path": _join(mm.group(2)), "file": rel,
                            "line": no, "source": "fastapi"})
                continue
            mm = RX_FLASK.search(stripped)
            if mm:
                methods = re.findall(r"['\"](GET|POST|PUT|DELETE|PATCH)['\"]", mm.group(2), re.IGNORECASE)
                for meth in (methods or ["GET"]):
                    eps.append({"method": meth.upper(), "path": _join(mm.group(1)), "file": rel,
                                "line": no, "source": "flask"})
                continue
        if low.endswith(".go"):
            mm = RX_GO.search(stripped)
            if mm:
                eps.append({"method": mm.group(1), "path": _join(mm.group(2)), "file": rel, "line": no,
                            "source": "go"})
                continue
            mm = RX_GO_HANDLEFUNC.search(stripped)
            if mm:
                eps.append({"method": mm.group(1) or "ANY", "path": _join(mm.group(2)), "file": rel,
                            "line": no, "source": "go"})
                continue
        if os.path.splitext(low)[1] in (".js", ".mjs", ".cjs", ".ts"):
            for mm in RX_EXPRESS.finditer(stripped):
                eps.append({"method": mm.group(1).upper(), "path": _join(mm.group(2)), "file": rel,
                            "line": no, "source": "express-like"})
    return eps


def _method_name(line):
    m = re.search(r"(\w+)\s*\(", line)
    return m.group(1) if m else ""


def _scan_back(root, files):
    out = {k: [] for k in ("openapi", "endpoints", "handlers", "models", "validations", "errors",
                           "security", "shortcuts", "tests")}
    for path in files:
        rel = _rel(root, path)
        text = _read(path)
        if text is None:
            continue
        ext = os.path.splitext(rel)[1].lower()
        if ext in SPEC_EXT:
            eps = _openapi_endpoints(rel, text)
            if eps is not None:
                out["openapi"].append({"file": rel, "operations": len(eps)})
                out["endpoints"].extend(eps)
            else:
                _scan_shortcuts(rel, text.splitlines(), out["shortcuts"], secrets_only=True)
            continue
        lines = text.splitlines()
        if ext in CONFIG_EXT or os.path.basename(rel).startswith(".env"):
            _scan_shortcuts(rel, lines, out["shortcuts"], config=True)
            continue
        if _is_test_path(rel):
            out["tests"].extend(_scan_tests(rel, lines))
            continue
        out["endpoints"].extend(_endpoints_from_code(rel, text, lines))
        entity_pending = False
        for no, line in enumerate(lines, 1):
            if RX_HANDLER.search(line):
                out["handlers"].append({"file": rel, "line": no, "signal": RX_HANDLER.search(line).group(0).strip()})
            if RX_ENTITY_ANN.search(line):
                entity_pending = True
            mm = RX_MODEL.search(line) or RX_PYDANTIC.search(line)
            if mm:
                out["models"].append({"name": mm.group(1), "file": rel, "line": no})
                entity_pending = False
            elif entity_pending:
                cm = RX_CLASS_NAME.search(line)
                if cm:
                    out["models"].append({"name": cm.group(1), "file": rel, "line": no, "entity": True})
                    entity_pending = False
            for vm in RX_VALIDATION.finditer(line):
                rule = next(g for g in vm.groups() if g)
                out["validations"].append({"rule": rule, "file": rel, "line": no})
            for rx in RX_ERRORS:
                em = rx.search(line)
                if em:
                    out["errors"].append({"status": em.group(1), "file": rel, "line": no})
                    break
            am = RX_AUTH.search(line)
            if am:
                out["security"].append({"signal": am.group(0).strip("'\" "), "file": rel, "line": no})
        _scan_shortcuts(rel, lines, out["shortcuts"])
    out["endpoints"] = _dedupe(out["endpoints"], ("method", "path", "file", "line"))
    return out


def _scan_shortcuts(rel, lines, sink, secrets_only=False, config=False):
    if not secrets_only and not config and _is_mock_path(rel):
        sink.append({"kind": "mock-data", "file": rel, "line": 1})
    for no, line in enumerate(lines, 1):
        sm = RX_SECRET.search(line) or (RX_SECRET_CONFIG.search(line) if config else None)
        if sm and not re.search(r"(?i)(example|changeme|placeholder|dummy|xxx+|\*\*\*)", sm.group(2)):
            sink.append({"kind": "hardcoded-secret", "name": sm.group(1).lower(), "file": rel, "line": no})
        if secrets_only:
            continue
        if config:
            if RX_CORS_ANY.search(line):
                sink.append({"kind": "cors-wildcard", "file": rel, "line": no})
            continue
        if RX_CORS_ANY.search(line):
            sink.append({"kind": "cors-wildcard", "file": rel, "line": no})
        if RX_PERMIT_ALL.search(line):
            sink.append({"kind": "permit-all", "file": rel, "line": no})
        tm = RX_TODO.search(line)
        if tm:
            sink.append({"kind": "todo", "marker": tm.group(1), "file": rel, "line": no,
                         "text": line.strip()[:160]})
        if RX_LOCALHOST.search(line):
            sink.append({"kind": "localhost-url", "file": rel, "line": no})


def _scan_tests(rel, lines):
    tests, pending, display = [], None, None
    for no, line in enumerate(lines, 1):
        dm = RX_DISPLAY.search(line)
        if dm:
            display = dm.group(1)
        if RX_TEST_ANN.search(line):
            pending = no
            continue
        if pending is not None:
            mm = RX_METHOD_NAME.search(line)
            if mm:
                tests.append({"name": display or mm.group(1), "file": rel, "line": no})
                pending, display = None, None
            continue
        for rx in (RX_TEST_NAMED, RX_PY_TEST, RX_GO_TEST):
            mm = rx.search(line)
            if mm:
                tests.append({"name": mm.group(1), "file": rel, "line": no})
                break
    return tests


# --- front end ------------------------------------------------------------------------------
def _route_from_file(rel):
    m = re.search(r"(?:^|/)app/(.*?)/?page\.(?:tsx|jsx|ts|js|mdx)$", rel) or \
        re.search(r"(?:^|/)app/()page\.(?:tsx|jsx|ts|js|mdx)$", rel)
    if m:
        segs = [s for s in m.group(1).split("/") if s and not (s.startswith("(") and s.endswith(")"))
                and not s.startswith("@")]
        return _join(*segs), "nextjs-app"
    m = re.search(r"(?:^|/)pages/(?!api/)(.*)\.(?:tsx|jsx|ts|js|vue)$", rel)
    if m and not re.search(r"(^|/)_(app|document|error)$", m.group(1)):
        return _join(re.sub(r"(^|/)index$", "", m.group(1))), "file-pages"
    return None, None


def _scan_front(root, files):
    out = {k: [] for k in ("routes", "api_calls", "forms", "states", "shortcuts", "tests")}
    for path in files:
        rel = _rel(root, path)
        ext = os.path.splitext(rel)[1].lower()
        if ext in SPEC_EXT:
            continue
        text = _read(path)
        if text is None:
            continue
        lines = text.splitlines()
        if ext in CONFIG_EXT or os.path.basename(rel).startswith(".env"):
            _scan_shortcuts(rel, lines, out["shortcuts"], config=True)
            continue
        if _is_test_path(rel):
            out["tests"].extend(_scan_tests(rel, lines))
            continue
        route, source = _route_from_file(rel)
        if route is not None:
            out["routes"].append({"path": route, "file": rel, "line": 1, "source": source})
        router_file = RX_ROUTER_HINT.search(text) is not None
        seen_state = set()
        for no, line in enumerate(lines, 1):
            for mm in RX_RR_ROUTE.finditer(line):
                out["routes"].append({"path": mm.group(1), "file": rel, "line": no, "source": "router"})
            if router_file and not RX_RR_ROUTE.search(line):
                for mm in RX_PATH_KEY.finditer(line):
                    out["routes"].append({"path": "/" + mm.group(1).lstrip("/"), "file": rel, "line": no,
                                          "source": "router-config"})
            for mm in RX_FETCH.finditer(line):
                window = " ".join(lines[no - 1:no + 4])
                meth = RX_FETCH_METHOD.search(window)
                out["api_calls"].append({"method": meth.group(1).upper() if meth else "GET",
                                         "path": mm.group(2), "file": rel, "line": no, "client": "fetch"})
            for mm in RX_CLIENT_CALL.finditer(line):
                out["api_calls"].append({"method": mm.group(1).upper(), "path": mm.group(3), "file": rel,
                                         "line": no, "client": "http-client"})
            if RX_FORM.search(line):
                out["forms"].append({"file": rel, "line": no, "signal": RX_FORM.search(line).group(0)})
            for kind, rx in RX_STATES:
                if kind not in seen_state and rx.search(line):
                    seen_state.add(kind)
                    out["states"].append({"kind": kind, "file": rel, "line": no})
        _scan_shortcuts(rel, lines, out["shortcuts"])
    out["routes"] = _dedupe(out["routes"], ("path", "file", "line"))
    out["api_calls"] = [c for c in out["api_calls"] if "/" in c["path"]]
    return out


# --- cross check ----------------------------------------------------------------------------
def cross_check(endpoints, api_calls):
    index = {}
    for ep in endpoints:
        index.setdefault(normalize_path(ep["path"]), []).append(ep)
    used = set()
    matched, front_only = [], []
    for call in api_calls:
        norm = normalize_path(call["path"])
        hits = _match(norm, call["method"], index)
        if hits:
            for key, ep in hits:
                used.add(id(ep))
            key, ep = hits[0]
            matched.append({"method": call["method"], "path": norm, "front": "%s:%d" % (call["file"], call["line"]),
                            "back": "%s:%d" % (ep["file"], ep["line"]), "match": "exact" if key == norm else "suffix"})
        else:
            front_only.append({"method": call["method"], "path": norm, "front": "%s:%d" % (call["file"], call["line"])})
    back_only = [{"method": ep["method"], "path": normalize_path(ep["path"]), "back": "%s:%d" % (ep["file"], ep["line"])}
                 for eps in index.values() for ep in eps if id(ep) not in used]
    return {"matched": matched, "front_only": front_only, "back_only": back_only}


def _match(norm, method, index):
    def method_ok(ep):
        return method in ("ANY", "") or ep["method"] in ("ANY", "") or ep["method"] == method
    exact = [(norm, ep) for ep in index.get(norm, []) if method_ok(ep)]
    if exact:
        return exact
    out = []
    for key, eps in index.items():
        if key != "/" and (norm.endswith(key) or key.endswith(norm)) and norm != "/":
            out.extend((key, ep) for ep in eps if method_ok(ep))
    return out


def _dedupe(items, keys):
    seen, out = set(), []
    for it in items:
        k = tuple(it.get(x) for x in keys)
        if k not in seen:
            seen.add(k)
            out.append(it)
    return out


# --- main -----------------------------------------------------------------------------------
def build_inventory(back=None, front=None, hint=None, max_files=MAX_FILES_DEFAULT, max_bytes=MAX_BYTES_DEFAULT):
    if not back and not front:
        raise InventoryError("give at least one of --back or --front")
    inv = {"version": 1, "hint": hint or "", "back": None, "front": None, "skipped_files": 0}
    for name, root in (("back", back), ("front", front)):
        if not root:
            continue
        if not os.path.isdir(root):
            raise InventoryError("%s is not a directory: %s" % (name, root))
        files, skipped = _walk(root, max_files, max_bytes)
        inv["skipped_files"] += skipped
        data = _scan_back(root, files) if name == "back" else _scan_front(root, files)
        data["root"] = os.path.abspath(root).replace(os.sep, "/")
        data["files_scanned"] = len(files)
        inv[name] = data
    endpoints = inv["back"]["endpoints"] if inv["back"] else []
    calls = inv["front"]["api_calls"] if inv["front"] else []
    inv["cross"] = cross_check(endpoints, calls) if (inv["back"] and inv["front"]) else None
    inv["counts"] = {
        "endpoints": len(endpoints),
        "openapi_files": len(inv["back"]["openapi"]) if inv["back"] else 0,
        "routes": len(inv["front"]["routes"]) if inv["front"] else 0,
        "api_calls": len(calls),
        "tests": (len(inv["back"]["tests"]) if inv["back"] else 0) + (len(inv["front"]["tests"]) if inv["front"] else 0),
        "shortcuts": (len(inv["back"]["shortcuts"]) if inv["back"] else 0)
        + (len(inv["front"]["shortcuts"]) if inv["front"] else 0),
        "front_only": len(inv["cross"]["front_only"]) if inv["cross"] else 0,
        "back_only": len(inv["cross"]["back_only"]) if inv["cross"] else 0,
    }
    return inv


def is_empty(inv):
    c = inv["counts"]
    return c["endpoints"] == 0 and c["routes"] == 0 and c["api_calls"] == 0 and c["openapi_files"] == 0


def summary(inv):
    c = inv["counts"]
    lines = ["endpoints=%d openapi_files=%d routes=%d api_calls=%d tests=%d shortcuts=%d front_only=%d back_only=%d"
             % (c["endpoints"], c["openapi_files"], c["routes"], c["api_calls"], c["tests"], c["shortcuts"],
                c["front_only"], c["back_only"])]
    if inv["cross"]:
        for item in inv["cross"]["front_only"]:
            lines.append("FRONT_ONLY: %s %s (%s)" % (item["method"], item["path"], item["front"]))
        for item in inv["cross"]["back_only"]:
            lines.append("BACK_ONLY: %s %s (%s)" % (item["method"], item["path"], item["back"]))
    for side in ("back", "front"):
        if inv[side]:
            for s in inv[side]["shortcuts"]:
                if s["kind"] != "todo":
                    lines.append("SHORTCUT: %s %s:%d (%s)" % (s["kind"], s["file"], s["line"], side))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="poc_inventory.py",
        description="Inventory a POC back end and/or front end for spec drafting (read-only). "
                    "Exit 0 = ok, 2 = nothing detected, 1 = error.")
    ap.add_argument("--back", help="back-end source directory of the POC")
    ap.add_argument("--front", help="front-end source directory of the POC")
    ap.add_argument("--hint", help="free-text stack hint, recorded only (e.g. 'spring + angular')")
    ap.add_argument("--json", action="store_true", help="print the full JSON inventory to stdout")
    ap.add_argument("--out", help="also write the JSON inventory to this file")
    ap.add_argument("--max-files", type=int, default=MAX_FILES_DEFAULT, help="files scanned per root")
    ap.add_argument("--max-bytes", type=int, default=MAX_BYTES_DEFAULT, help="skip files larger than this")
    args = ap.parse_args(argv)
    try:
        inv = build_inventory(args.back, args.front, args.hint, args.max_files, args.max_bytes)
    except InventoryError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 1
    payload = json.dumps(inv, indent=2, ensure_ascii=False)
    if args.out:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(payload + "\n")
        except OSError as exc:
            sys.stderr.write("error: cannot write %s: %s\n" % (args.out, exc))
            return 1
    print(payload if args.json else summary(inv))
    if is_empty(inv):
        sys.stderr.write("nothing detected: no endpoint, route, API call or OpenAPI file\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
