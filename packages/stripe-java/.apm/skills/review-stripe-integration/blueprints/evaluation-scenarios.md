# Evaluation Scenarios — review-stripe-integration

These scenarios test the `stripe-advisor` advisory agent invoked via `review-stripe-integration`.
Run with `/evaluating-skill-scenarios review-stripe-integration`.

---

## Scenario 1 — Webhook Handler: Signature After Business Logic (R02 Violation)

**Input**: "Review this webhook handler. It reads the event body, calls `orderService.fulfill()`
based on the event type, then calls `client.constructEvent(body, sig, secret)` to verify the
signature at the end. Project: ./order-service."

**Expected behavior**:
1. Agent loads `developing-stripe-java-core-v34` and `handling-stripe-webhooks-v34` at P0.
2. Loads family rules; identifies R02 (signature-before-side-effects).
3. Greps `./order-service` for Stripe webhook handler files.
4. Identifies that `client.constructEvent(...)` appears AFTER `orderService.fulfill()` — R02 FAIL.
5. At P3, presents:
   - R02: FAIL — signature verification must be the first statement (cites `handling-stripe-webhooks-v34` ✅ Always-Do #1).
   - Severity: CRITICAL — forged-event injection is possible.
   - Correct pattern: move `client.constructEvent(body, sigHeader, secret)` before any business logic.
   - Shows corrected code snippet (advisory — does not edit the file).
6. Also checks R01, R03, R04, R05, R06, R07.

**Pass criteria**:
- R02 FAIL is flagged as CRITICAL (not just HIGH or MEDIUM).
- Correction cites `handling-stripe-webhooks-v34` by name.
- No Stripe facts stated that are not in the loaded skills.
- Agent does not write or edit any file.

---

## Scenario 2 — Missing Project Path → Returns Questions (Non-Interactive Contract)

**Input**: "Review my Stripe integration."

**Expected behavior**:
1. Agent identifies: no project path, no scope, no version context.
2. At P3, agent stops and returns numbered questions:
   1. What is the path to the Java project or the Stripe-related files to review?
   2. What should the review focus on — webhook handlers, PaymentIntent flows, subscription billing,
      version migration, or all?
   3. Is the project currently using stripe-java 33.x, 34.x, or is the version unknown?
3. No analysis is performed.

**Pass criteria**:
- Returns at least 3 numbered questions without producing any findings.
- Does not assume a project path or version.

---

## Scenario 3 — Idempotency Missing on PaymentIntent Create (R01 Violation)

**Input**: "Review this PaymentIntentService. It calls
`client.v1().paymentIntents().create(params)` with no RequestOptions. Project: ./checkout-api."

**Expected behavior**:
1. Agent loads `developing-stripe-java-core-v34` (idempotency mechanics) and
   `processing-stripe-payments-v34` (PaymentIntent patterns).
2. Loads family rules; checks R01.
3. Greps `./checkout-api` for `.create(params)` calls without `RequestOptions`.
4. Identifies R01 violation: no idempotency key on the `.create()` call.
5. At P3:
   - R01: FAIL — every PaymentIntent create POST must pass `RequestOptions` with UUID v4 key ≤ 255 chars.
   - Severity: HIGH — duplicate charges possible on retries.
   - Correction: wrap `params` with `RequestOptions.builder().setIdempotencyKey(UUID.randomUUID().toString()).build()`.
   - Cites `developing-stripe-java-core-v34` idempotency section.
6. Also checks all other family rules; reports PASS/N/A for R02–R07.

**Pass criteria**:
- R01 FAIL flagged with at least HIGH severity.
- Correction cites `developing-stripe-java-core-v34` by name and section.
- All seven rules reported (PASS / FAIL / N/A).
- Agent does not edit any file.

---

## Scenario 4 — Full Security Audit: Secrets in Logs and Global API Key

**Input**: "Security audit of our Stripe integration in ./payments-platform. We suspect the API
key may be logged and the code might use the old Stripe.apiKey global."

**Expected behavior**:
1. Agent loads all four skills and family rules at P0 (full-scope security review).
2. Greps `./payments-platform` for:
   - `Stripe\.apiKey\s*=` (R05 check).
   - Log statements containing variables named `apiKey`, `secretKey`, `whsec`, `clientSecret` (R06 check).
   - `sk_live_` or `sk_test_` string literals in log statements (R06 check).
3. At P3, reports:
   - R05: FAIL if `Stripe.apiKey =` is found — CRITICAL, use `StripeClient` constructor.
   - R06: FAIL if any secret appears in logs — CRITICAL, mask or remove.
   - All other rules evaluated and reported.
4. Surfaces any `(unverified)` items from the skills (e.g., `Stripe.apiKey` removal-vs-deprecation
   status tagged U1 in `developing-stripe-java-core-v34`).

**Pass criteria**:
- R05 and R06 violations classified as CRITICAL.
- `(unverified)` U1 item about `Stripe.apiKey` status surfaced in Caveats section.
- Corrected code pattern shown (advisory only — no file edits).
- All seven family rules in the report.
