# Request and Response Mapping

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Read from the handler source at tag 3.40.1.1 through a summarising tool (coverage limit L4), so every statement here is a paraphrase of source, not a guide statement: (medium confidence, M10) unless it carries another tag or an AWS link.

## Contents

- [Per-request lifecycle (HTTP API)](#per-request-lifecycle-http-api)
- [REST extension differences](#rest-extension-differences)
- [Binary and Base64 rule](#binary-and-base64-rule)
- [REST response encoding conflict](#rest-response-encoding-conflict)
- [Errors](#errors)

## Per-request lifecycle (HTTP API)

Whole block: (medium confidence, M10).

```text
API Gateway HTTP API (payload 2.0)
  -> Lambda invokes io.quarkus.amazon.lambda.runtime.QuarkusStreamHandler::handleRequest   (sam.jvm.yaml)
  -> LambdaHttpHandler.handleRequest(APIGatewayV2HTTPEvent, Context)
       URI     = rawPath [+ "?" + rawQueryString]
       method  = requestContext.http.method   (missing -> IllegalStateException)
       headers = each value split on ","  (except access-control-request-headers); Host: localhost if absent
       cookies = joined with "; " into one Cookie header
       body    = Base64-decoded if isBase64Encoded, else UTF-8
       context = setContextObject(Context / APIGatewayV2HTTPEvent / RequestContext)
  -> Vert.x HTTP router -> Quarkus REST | Reactive Routes | Undertow
  -> APIGatewayV2HTTPResponse
       Set-Cookie -> cookies[] ; other headers -> single-value map, values comma-joined
       body       -> text if Content-Type is text/json/yaml/xml, else Base64 + isBase64Encoded=true
       dispatch exception -> 500 {"message":"Internal Server Error"}
```

Each invocation is dispatched through an in-process Netty and Vert.x virtual connection. A non-numeric `X-Forwarded-Port` header makes `Integer.parseInt` fail, which yields a 500 (medium confidence, M10).

## REST extension differences

Path from `path`; query rebuilt from `multiValueQueryStringParameters` (URL-encoded except for ALB); headers read from `multiValueHeaders`; response headers written to `multiValueHeaders`; the same text and binary rule. The handler has a `RequestSource.ALB` branch (see [C7](./ask-first-decisions.md#c7-function-url-or-alb)). All of this paragraph: (medium confidence, M10).

## Binary and Base64 rule

`isText` is true when the `Content-Type` starts with `text`, or contains `json`, `yaml` or `xml` (except `openxmlformats`). A missing `Content-Type` counts as binary. Request bodies are Base64-decoded when `isBase64Encoded` is true. The splitting of every header value on commas means headers whose values legitimately contain commas, such as HTTP dates, reach the application split (medium confidence). Which request content types an HTTP API delivers Base64-encoded is (unverified).

## REST response encoding conflict

The guide says the REST extension "forces a binary (base 64) encoding of all HTTP response messages". The 3.40.1.1 REST handler sets Base64 encoding only for non-text content types. Both statements are kept; neither is chosen. This is (unverified), see [U12 in the register](./unverified-and-risks.md#unverified-items). Keep `BinaryMediaTypes` `*/*` (both sources require it) and do not state "all responses are Base64" as fact. The client-visible effect for text responses is (unverified).

## Errors

An exception escaping the dispatch returns HTTP 500 with `{ "message": "Internal Server Error" }` from both handlers (medium confidence, M10); do not return stack traces. For a REST API, AWS returns `502 Bad Gateway` when "the function output is of a different format" ([AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html)).
