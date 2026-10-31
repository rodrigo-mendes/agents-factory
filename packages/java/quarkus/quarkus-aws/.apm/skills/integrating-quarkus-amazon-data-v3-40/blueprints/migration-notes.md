# Migration Notes

Back to [SKILL.md](../SKILL.md). Sources: https://github.com/quarkiverse/quarkus-amazon-services/releases and the parent POM 3.23.0, fetched 2026-10-28.

## From 3.22.x to 3.23.0

- Breaking changes: none listed in the 3.23.0 release notes.
- Dependency bumps listed: "bump quarkus.version from 3.39.2 to 3.40.0"; "bump software.amazon.awssdk:bom from 2.54.13 to 2.55.6".
- Line history for context: 3.22.0 (2026-09-07) Quarkus 3.38.1, SDK 2.51.4; 3.22.1 (2026-09-10) Quarkus 3.39.2, SDK 2.54.13; 3.23.0 (2026-10-01, "LTS") Quarkus 3.40.0, SDK 2.55.6. The years of these release dates are inferred (medium confidence, M9).

Upgrade steps from 3.22.x:

1. Move the application to Quarkus 3.40.x.
2. Set `quarkus-amazon-services-bom` to `3.23.0`.
3. Re-check HTTP-client artifacts against the `*-client.type` keys ([A2](./always-do-patterns.md#a2-http-client-artifact)).
4. Run the [Verification Loop](./verification-loop.md).

## SDK-level changes visible through the BOM

`Apache5HttpClient` "replaced `ApacheHttpClient` as the default synchronous client in version 2.46.0" and `ApacheHttpClient` is deprecated ([HTTP configuration](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/http-configuration.html)). Quarkiverse keeps its own default `sync-client.type=url`; it does not follow the SDK default.

## Not applicable: Quarkus 4 line

4.0.0.Beta1 breaking changes (Floci default, no container isolation, OpenTelemetry on by default, `quarkus-amazon-ce` renamed to `quarkus-amazon-costexplorer`): reject for 3.23.x.

## Compatibility matrix

| Dependency | Min | Max | Notes |
|---|---|---|---|
| Quarkus | 3.40.0 (build baseline) | 3.40.x | 3.40.1.1 runtime pairing (medium confidence); Quarkus 4 uses 4.0.0.Beta* and is out of scope |
| AWS SDK for Java 2.x | 2.55.6 | via BOM | imported by `quarkus-amazon-services-bom` |
| AWS CRT | 0.48.4 | via BOM | `software.amazon.awssdk.crt:aws-crt` managed by the BOM |
| Java | 17 (compiler source and target) | page not recorded | Lambda Java runtimes: see `developing-quarkus-amazon-lambda-v3-40` |
