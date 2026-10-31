# Integration Patterns — researching-technical-frameworks

When researching **any** SDK or client library that connects to an external service, capture the
concerns below — regardless of language, vendor, or protocol. This blueprint is **technology-agnostic**:
it defines *what to document*, not a specific vendor's API. In a real research document, replace every
`[PLACEHOLDER]` with the actual target technology and paste **verified, version-pinned** code from the
official docs.

> **Do not hardcode one vendor here.** This is a research template. Vendor-specific code belongs in the
> `research_[TECH]_v[VERSION].md` output, not in this generic guidance.

---

## Generic Integration Template

For any SDK or client library, document each concern:

```markdown
## Integration: [SDK_NAME] v[VERSION] + [EXTERNAL_SERVICE]

### Auth / Credentials
- How credentials are supplied: env var / secret manager / SDK config object / OIDC
- Never hardcode. Use placeholders:
  [SDK]_API_KEY=<from-secret-manager>

### Retry Policy
- Built-in retry: yes/no; which status codes/conditions trigger it
- Configurable parameters: max_attempts, backoff_strategy, timeout_ms
- Retryable vs. terminal errors (e.g., rate-limit retryable; validation terminal)

### Webhook / Callback Handling (if applicable)
- Signature verification: algorithm + header name ([e.g., HMAC-SHA256 via X-<Vendor>-Signature])
- Idempotency: event dedup strategy (store event ID before processing)
- Event ordering: guaranteed vs. best-effort; how to handle out-of-order delivery

### Idempotency
- Client-side idempotency key: how to generate and pass
- Server-side enforcement: enforced by API, or advisory?
- Safe retry window: how long the server retains the key ([e.g., N hours])

### Error Taxonomy
| Error Class      | Retryable | Action                        |
|------------------|-----------|-------------------------------|
| Rate limit       | Yes       | Exponential backoff + jitter  |
| Auth failure     | No        | Fail fast, alert ops          |
| Timeout          | Yes       | Retry with idempotency key    |
| Validation       | No        | Fix request, do not retry     |
```

---

## Version Pinning — Applies to Every Scheme

Version-absolutism holds no matter how the technology numbers its releases. Capture both the **SDK/library
version** and, if separate, the **wire/API version** — they are independent and must each be pinned.

| Scheme | Example shape | Research rule |
|--------|---------------|---------------|
| SemVer | `MAJOR.MINOR.PATCH` | Pin exact line; treat other majors as separate research |
| Date-versioned | `YYYY-MM-DD[.codename]` | Pin the exact string; `"latest"` is never acceptable |
| Rolling / channel | `stable` / `lts` / `edge` | Resolve to the concrete build at research time; record it |

```markdown
## Version Block (every code example must carry it)
# [TECH] [SDK_VERSION] — wire/API [API_VERSION if separate]
# DO NOT mix with other versions. Breaking from [PREVIOUS]: [list if applicable]
# Source: [OFFICIAL_CHANGELOG_URL] (checked [DATE])
```

⚠️ **Do not conflate an SDK version with an API/wire version.** An older SDK cannot legitimately pin a
newer service API version, and vice versa — if you see that pairing in a draft, it's a version-conflation
error. Confirm both against the same official release notes.

---

## Illustrative Skeleton (language-neutral pseudocode)

Use this shape when demonstrating the pattern in a research doc, then replace with **official,
version-pinned code** for the target SDK. The point is the *sequence of guardrails*, not any one vendor.

```text
# [TECH] [VERSION] — pseudocode illustration only; replace with verified SDK code
client = SDK.newClient(secret = env("[SDK]_SECRET"))     # credential from env/secret manager
client.setApiVersion("[PINNED_API_VERSION]")             # pin wire version if the SDK exposes one

result = client.action(params, opts{ idempotencyKey: key })   # idempotency on state-changing calls

on RateLimitError:  retry with exponential backoff + jitter    # retryable
on AuthError:       fail fast, alert                           # terminal
on ValidationError: fix request, do not retry                  # terminal

# Webhook/callback path:
event = client.verifySignature(rawBody, signatureHeader, env("[SDK]_WEBHOOK_SECRET"))  # verify FIRST
if seenBefore(event.id): return 200                     # dedup before side effects
process(event)
```

**When writing the real research document**, source each line from the vendor's official docs and note
whether the recommended client style is instance-based or static, whether signature verification is a
static helper or an instance method, and flag any deprecated pattern you were tempted to copy.

---

## Research Checklist for SDK Integrations

Before finalizing an SDK integration section in a research document:

- [ ] Credential injection documented (env var or secret manager — not hardcoded)?
- [ ] Retry policy: retryable vs. terminal errors listed?
- [ ] Idempotency key: generation strategy + server retention window stated?
- [ ] Webhook/callback signature verification example present (if applicable)?
- [ ] SDK version **and** separate API/wire version both pinned in every code comment?
- [ ] Version scheme (semver / date / channel) identified and enforced?
- [ ] No SDK-version ↔ API-version conflation?
- [ ] Recommended client style (instance vs. static) confirmed against official docs — deprecated patterns avoided?
- [ ] Error taxonomy table present with retryable column?
