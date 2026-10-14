# File Uploads — Camel Quarkus Platform HTTP 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md).

## Contents

- [Route](#route)
- [Quarkus body properties](#quarkus-body-properties)
- [Message shape](#message-shape)
- [Limits](#limits)
- [Checks](#checks)

## Route

The extension page shows uploads with `fileNameExtWhitelist` plus `httpMethodRestrict=POST`, read through `AttachmentMessage` ([extension page](https://camel.apache.org/camel-quarkus/3.40.x/reference/extensions/platform-http.html)).

```java
// Camel Quarkus 3.40.x
from("platform-http:/upload?httpMethodRestrict=POST&fileNameExtWhitelist=adoc,txt")
    .log("got ${header.CamelFileName} (${header.CamelFileLength} bytes)");
```

`fileNameExtWhitelist` has no default ([component page](https://camel.apache.org/components/4.22.x/platform-http-component.html)), so an endpoint without it accepts any file type.

## Quarkus body properties

The extension page tells you to review `quarkus.http.body.handle-file-uploads`, `quarkus.http.body.uploads-directory` and `quarkus.http.body.delete-uploaded-files-on-end`. Their defaults are (unverified) (the 3.40 all-config page did not render in the research). Set them explicitly.

```properties
# Quarkus 3.40; values are examples, not defaults
quarkus.http.body.handle-file-uploads=true
quarkus.http.body.uploads-directory=/var/app/uploads
quarkus.http.body.delete-uploaded-files-on-end=true
quarkus.http.limits.max-body-size=10240K
```

## Message shape

Since Camel 4.10, a single upload puts the file in the body and sets `CamelFileName`, `CamelFileContentType` and `CamelFileLength`. Multiple uploads set `CamelAttachmentsSize` ([component page](https://camel.apache.org/components/4.22.x/platform-http-component.html)). Code that relied on attachment-only access should be re-tested; see the [migration guide](./migration-guide.md).

## Limits

| Property | Default | Source |
|---|---|---|
| `quarkus.http.limits.max-body-size` | `10240K` | https://quarkus.io/version/3.40/guides/http-reference |
| `quarkus.http.limits.max-form-attribute-size` | `2048` | https://quarkus.io/version/3.40/guides/http-reference |
| `quarkus.http.limits.max-header-size` | `20K` | https://quarkus.io/version/3.40/guides/http-reference |

How `useStreaming=true` interacts with `max-body-size` and `useBodyHandler` is (unverified). With the Vert.x engine, Bearer token validation runs before the body handler, so unauthenticated requests are rejected before buffering or upload ([component page](https://camel.apache.org/components/4.22.x/platform-http-component.html)).

## Checks

```bash
# Representative; adapt the port; the 8080 default is (unverified)
curl -i -F file=@a.txt http://localhost:8080/upload      # whitelisted extension
curl -i -F file=@a.exe http://localhost:8080/upload      # expect rejection; exact status code (unverified)
```
