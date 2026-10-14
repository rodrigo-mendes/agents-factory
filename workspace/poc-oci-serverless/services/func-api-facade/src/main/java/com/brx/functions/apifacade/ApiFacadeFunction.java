package com.brx.functions.apifacade;

import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

import com.brx.functions.apifacade.model.ApiFacadeRequest;
import com.brx.functions.apifacade.model.ApiFacadeResponse;
import com.brx.functions.apifacade.service.OciService;
import com.brx.functions.apifacade.service.OciServiceClient;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fnproject.events.APIGatewayFunction;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.output.APIGatewayResponseEvent;
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.Headers;
import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.model.BmcException;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.context.Scope;

public class ApiFacadeFunction extends APIGatewayFunction<String, ApiFacadeResponse> {

    private static final Logger log = LoggerFactory.getLogger(ApiFacadeFunction.class);
    private static final ObjectMapper objectMapper = new ObjectMapper();

    private String environment;
    private boolean coldStart = true;
    private String initError;
    OciService ociClient; // package-private for test injection

    @Override
    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        super.configure(ctx);
        try {
            long start = System.currentTimeMillis();
            this.environment = ctx.getConfigurationByKey("ENVIRONMENT").orElse("dev");

            // Set up the Observability pipeline (JUL-to-SLF4J, Monitoring client, etc.)
            ObservabilityHelper.configure(ctx);

            if (this.ociClient == null) {
                this.ociClient = loadOciClient();
            }

            long elapsed = System.currentTimeMillis() - start;
            log.info("ApiFacade COLD_START configuration completed in {}ms | env={} | memory={}MB",
                    elapsed,
                    environment,
                    ctx.getConfigurationByKey("FN_MEMORY").orElse("?"));
        } catch (Exception e) {
            this.initError = e.getClass().getName() + ": " + e.getMessage();
            log.error("COLD_START INIT FAILED: {}", initError, e);
        }
    }

    private OciService loadOciClient() {
        try {
            Class<?> holder = Class.forName("com.brx.functions.apifacade.MockOciServiceHolder");
            return (OciService) holder.getField("ociService").get(null);
        } catch (ClassNotFoundException e) {
            // Production path — no mock available
        } catch (Exception e) {
            log.warn("Mock carrier locator load failure: {}", e.getMessage());
        }

        try {
            return new OciServiceClient();
        } catch (Exception e) {
            log.warn("OCI SDK ServiceClient bypassed init: {}", e.getMessage());
            return null;
        }
    }

    @Override
    public APIGatewayResponseEvent<ApiFacadeResponse> handler(APIGatewayRequestEvent<String> req) {
        long start = System.currentTimeMillis();
        String method = req.getMethod();
        String path = extractRoutePath(req.getRequestUrl());

        // Context correlation for logging
        String opcRequestId = req.getHeaders().get("opc-request-id").orElseGet(() -> UUID.randomUUID().toString());
        MDC.put("opcRequestId", opcRequestId);
        MDC.put("route", path);
        MDC.put("method", method);
        MDC.put("coldStart", String.valueOf(coldStart));

        boolean isColdStartInvocation = coldStart;
        coldStart = false; // Mark subsequent warm invokers

        log.info("INVOKE {} {} | opcRequestId={} | coldStart={}", method, path, opcRequestId, isColdStartInvocation);

        if (initError != null) {
            log.error("Aborting invocation due to prior initialization failure: {}", initError);
            MDC.clear();
            return error(500, "Function initialization failed: " + initError);
        }

        APIGatewayResponseEvent<ApiFacadeResponse> responseEvent = null;
        int resolvedStatus = 500;

        String traceparent = req.getHeaders().get("traceparent").orElse(null);
        Span span = ObservabilityHelper.startSpan(method, path, traceparent);

        // Activate the SERVER span as the current context so downstream CLIENT child spans
        // (Vault.GetSecret, ObjectStorage.PutObject) nest under it instead of becoming orphan roots.
        try (Scope scope = span.makeCurrent()) {
            try {
                switch (path) {
                    case "/hello":
                        responseEvent = handleHello(req);
                        break;
                    case "/secret":
                        responseEvent = handleSecret(req);
                        break;
                    case "/store":
                        responseEvent = handleStore(req);
                        break;
                    case "/health":
                    case "/diag":
                        responseEvent = handleHealth(isColdStartInvocation);
                        break;
                    default:
                        responseEvent = error(404, "Route not found: " + path);
                }
                if (responseEvent != null && responseEvent.getBody() != null) {
                    resolvedStatus = responseEvent.getBody().getStatusCode();
                }
            } catch (IllegalArgumentException e) {
                log.warn("Payload pattern contract validation failed: {}", e.getMessage());
                responseEvent = error(400, e.getMessage());
                resolvedStatus = 400;
            } catch (BmcException e) {
                log.warn("OCI Service call failed | status={} | opcRequestId={} | message={}",
                        e.getStatusCode(), e.getOpcRequestId(), e.getMessage());

                if (e.isTimeout() || e.getStatusCode() >= 500 || e.getStatusCode() == 429) {
                    responseEvent = error(503, "Service temporarily unavailable");
                    resolvedStatus = 503;
                } else {
                    responseEvent = error(e.getStatusCode(), e.getMessage());
                    resolvedStatus = e.getStatusCode();
                }
            } catch (Exception e) {
                log.error("Unhandled runtime exception encountered", e);
                responseEvent = error(500, "Internal server error");
                resolvedStatus = 500;
            } finally {
                long duration = System.currentTimeMillis() - start;

                // Emit synchronous telemetry metrics to OCI Monitoring Client
                ObservabilityHelper.postInvocation(path, method, isColdStartInvocation);
                ObservabilityHelper.postDuration(path, method, duration);
                if (resolvedStatus >= 400) {
                    ObservabilityHelper.postError(path, method, resolvedStatus);
                }

                ObservabilityHelper.endSpan(span, resolvedStatus);

                log.info("COMPLETE {} {} | status={} | elapsed={}ms", method, path, resolvedStatus, duration);

                // Populate metadata back to ApiFacadeResponse object
                if (responseEvent != null && responseEvent.getBody() != null) {
                    ApiFacadeResponse body = responseEvent.getBody();
                    body.setElapsedMs(duration);
                    body.setColdStart(isColdStartInvocation);
                    body.setApiVersion("1.0.0");
                }

                // Cleanup MDC correlation context to protect warm executions
                MDC.clear();
            }
        }

        return responseEvent;
    }

    private APIGatewayResponseEvent<ApiFacadeResponse> handleHello(APIGatewayRequestEvent<String> req) {
        log.debug("Handling hello invocation with method: {}", req.getMethod());
        return ok(ApiFacadeResponse.ok("Hello from API Facade (Java 17)! Environment: " + environment));
    }

    private APIGatewayResponseEvent<ApiFacadeResponse> handleHealth(boolean isColdStart) {
        java.util.Map<String, Object> diag = new java.util.LinkedHashMap<>();
        diag.put("status", "healthy");
        diag.put("environment", environment);
        diag.put("cold_start_active", isColdStart);
        diag.put("oci_client_ready", ociClient != null);
        return ok(ApiFacadeResponse.ok("FaaS Instance Diagnostic Trace", diag));
    }

    /**
     * Extracts the route-level path from the full request URL.
     * The API Gateway forwards the full path (e.g. "/v1/facade/hello").
     * This strips any deployment prefix and application prefix, returning "/hello".
     */
    private String extractRoutePath(String fullPath) {
        if (fullPath == null || fullPath.isEmpty()) {
            return "/";
        }
        // Find the last path segment starting with "/" (e.g. "/hello" from "/v1/facade/hello")
        int lastSlash = fullPath.lastIndexOf('/');
        if (lastSlash <= 0) {
            return fullPath;
        }
        return fullPath.substring(lastSlash);
    }

    private APIGatewayResponseEvent<ApiFacadeResponse> handleSecret(APIGatewayRequestEvent<String> req) {
        if (!"POST".equals(req.getMethod())) {
            return error(405, "Method not allowed");
        }

        String rawBody = req.getBody();
        ApiFacadeRequest body = null;
        if (rawBody != null && !rawBody.isBlank()) {
            try {
                if (rawBody.trim().startsWith("\"")) {
                    rawBody = objectMapper.readValue(rawBody, String.class);
                }
                body = objectMapper.readValue(rawBody, ApiFacadeRequest.class);
            } catch (Exception e) {
                log.warn("Failed to parse request body: {}", e.getMessage());
                return error(400, "Invalid JSON payload: " + e.getMessage());
            }
        }

        if (body == null || body.getResourceId() == null || body.getResourceId().isEmpty()) {
            return error(400, "Field 'resource_id' is required for action 'secret'");
        }
        if (ociClient == null) {
            return error(503, "OCI services unavailable");
        }

        long startCall = System.currentTimeMillis();
        Span downstream = ObservabilityHelper.startChildSpan("Vault.GetSecret");
        downstream.setAttribute("peer.service", "oci-vault-secrets");
        String secretValue;
        try {
            secretValue = ociClient.getSecret(body.getResourceId());
        } finally {
            ObservabilityHelper.endSpan(downstream);
        }
        long callElapsed = System.currentTimeMillis() - startCall;
        log.info("OCI_CALL secrets | status=200 | elapsed={}ms", callElapsed);

        return ok(ApiFacadeResponse.ok("Secret retrieved successfully", secretValue));
    }

    private APIGatewayResponseEvent<ApiFacadeResponse> handleStore(APIGatewayRequestEvent<String> req) {
        if (!"POST".equals(req.getMethod())) {
            return error(405, "Method not allowed");
        }

        String rawBody = req.getBody();
        ApiFacadeRequest body = null;
        if (rawBody != null && !rawBody.isBlank()) {
            try {
                if (rawBody.trim().startsWith("\"")) {
                    rawBody = objectMapper.readValue(rawBody, String.class);
                }
                body = objectMapper.readValue(rawBody, ApiFacadeRequest.class);
            } catch (Exception e) {
                log.warn("Failed to parse request body: {}", e.getMessage());
                return error(400, "Invalid JSON payload: " + e.getMessage());
            }
        }

        if (body == null || body.getBucketName() == null || body.getBucketName().isEmpty()
                || body.getObjectName() == null || body.getObjectName().isEmpty()) {
            return error(400, "Fields 'bucket_name' and 'object_name' are required");
        }
        if (ociClient == null) {
            return error(503, "OCI services unavailable");
        }

        long startCall = System.currentTimeMillis();
        Span downstream = ObservabilityHelper.startChildSpan("ObjectStorage.PutObject");
        downstream.setAttribute("peer.service", "oci-object-storage");
        try {
            ociClient.putObject(
                    body.getBucketName(),
                    body.getObjectName(),
                    body.getData() != null ? body.getData() : ""
            );
        } finally {
            ObservabilityHelper.endSpan(downstream);
        }
        long callElapsed = System.currentTimeMillis() - startCall;
        log.info("OCI_CALL PutObject | status=200 | elapsed={}ms", callElapsed);

        return ok(ApiFacadeResponse.ok("Object stored successfully"));
    }

    private APIGatewayResponseEvent<ApiFacadeResponse> ok(ApiFacadeResponse body) {
        return response(200, body);
    }

    private APIGatewayResponseEvent<ApiFacadeResponse> error(int status, String message) {
        return response(status, ApiFacadeResponse.error(status, message));
    }

    private APIGatewayResponseEvent<ApiFacadeResponse> response(int status, ApiFacadeResponse body) {
        return new APIGatewayResponseEvent.Builder<ApiFacadeResponse>()
                .statusCode(status)
                .headers(Headers.emptyHeaders()
                        .addHeader("Content-Type", "application/json"))
                .body(body)
                .build();
    }
}
