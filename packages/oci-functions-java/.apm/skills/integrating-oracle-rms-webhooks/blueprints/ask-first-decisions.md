# Ask First — RMS/MFCS Integration Decisions

## 1. Webhook mode: EVENT vs full PAYLOAD vs custom
| Option | Pros | Cons | When |
|-------|------|---------|--------|
| EVENT (`payload=N`) | Minimal traffic (Oracle recommended) | Consumer must fetch data (delta/by-id) | High volume; consumer already enriches |
| PAYLOAD full (`Y`) | No lookup needed | Large payload | All fields required and low volume |
| PAYLOAD custom (`Y`+`include=`) | Balanced | Must know fields in advance | Recommended default; enrich the rest by id |
→ Ask about expected volume and whether the destination needs the complete record.

## 2. Enrich by id vs trust the payload
- Enriching (`GET /{id}`) guarantees authoritative/current data, but adds 1 call per item.
- Trusting the custom payload is faster, but fields are limited to those in `include=`.
→ Ask: does the destination need fields beyond `include=`? Is the batch small? Is strong consistency required?

## 3. Listener auth (our function)
- **ANONYMOUS** API Gateway route: RMS calls directly; `credentialName` is still required by the config but the function ignores auth. Simple, POC-grade.
- Authenticated route (JWT/mTLS): more secure; requires RMS to send a valid credential (registered in the RMS wallet via `credentialName`).
→ Ask about the security posture / whether this is POC or production.

## 4. Webhook parameters (`webhooks/manage`)
- `intervalSeconds` (engine frequency), `pageLimit` (items per POST), `heartbeatIntervalHours`.
→ Ask about latency SLA vs invocation cost. Large batch + short interval = many invocations.

## 5. Synchronous vs asynchronous (large batches)
- Synchronous function (webhook→enrich→forward) is fine for small batches (tens of items).
- `pageLimit` up to 1000 + by-id enrichment → exceeds 60s. Use **Queue/Streaming/Connector Hub**: webhook only enqueues; worker drains and enriches.
→ Ask about the typical batch size.

## 6. Entity / coverage
- `item` validated ✅. Others (locations, diff*, tax*) follow the same pattern ◻️ but confirm the by-id path and payload shape per entity before generalising in production.
