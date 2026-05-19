---
description: 'Design OCI API Gateway strategy including routes, authentication, throttling, and CORS policies'
agent: oci-serverless-architect
argument-hint: 'API surface description, auth requirements, SLA expectations'
---

# Design API Gateway

**Skill**: `designing-oci-api-gateway`

## What this does

Designs the API Gateway strategy for a serverless architecture — route structure, authentication model, rate limiting, CORS, and deployment topology.

## Required information

1. **API surface**: Which paths and operations will be exposed? (list of endpoints)
2. **Consumers**: Who calls this API? (web frontend, mobile app, other services, third-party)
3. **Authentication requirements**: Auth model per route or global? (API Key, OAuth2, JWT, mutual TLS)
4. **Rate limiting**: Expected request volume? Per-client throttling needs?
5. **CORS**: Cross-origin access needed? From which domains?
6. **Versioning**: API versioning strategy? (path-based `/v1/`, header-based, query param)
7. **SLA expectations**: Latency budget, availability target

## What will be delivered

- Route structure design with auth and policy mapping
- Authentication model recommendation
- Rate limiting strategy
- CORS policy definition
- Gateway deployment topology (single vs multi-deployment)
- Implementation guidance with `@oci-terraform` for provisioning
