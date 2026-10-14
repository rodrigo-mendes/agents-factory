package com.brx.serverless.handler;

import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

import com.brx.serverless.model.ApiResponse;
import com.fnproject.events.APIGatewayFunction;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.output.APIGatewayResponseEvent;
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.Headers;
import com.fnproject.fn.api.RuntimeContext;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.context.Scope;

public class ApiHandler extends APIGatewayFunction<String, ApiResponse> {

    private static final Logger log = LoggerFactory.getLogger(ApiHandler.class);

    private String environment;
    private boolean coldStart = true;
    private String initError;

    @Override
    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        super.configure(ctx);
        try {
            long start = System.currentTimeMillis();
            this.environment = ctx.getConfigurationByKey("ENVIRONMENT").orElse("dev");

            // Set up the Observability pipeline
            ObservabilityHelper.configure(ctx);

            long elapsed = System.currentTimeMillis() - start;
            log.info("ApiHandler COLD_START configuration completed in {}ms | env={} | memory={}MB",
                    elapsed,
                    environment,
                    ctx.getConfigurationByKey("FN_MEMORY").orElse("?"));
        } catch (Exception e) {
            this.initError = e.getClass().getName() + ": " + e.getMessage();
            log.error("COLD_START INIT FAILED: {}", initError, e);
        }
    }

    @Override
    public APIGatewayResponseEvent<ApiResponse> handler(APIGatewayRequestEvent<String> req) {
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

        APIGatewayResponseEvent<ApiResponse> responseEvent = null;
        int resolvedStatus = 500;

        String traceparent = req.getHeaders().get("traceparent").orElse(null);
        Span span = ObservabilityHelper.startSpan(method, path, traceparent);

        // Activate the SERVER span as current context so any future CLIENT child spans nest under it.
        try (Scope scope = span.makeCurrent()) {
            try {
                if ("/hello".equals(path)) {
                    responseEvent = handleHello();
                } else if ("/health".equals(path) || "/diag".equals(path)) {
                    responseEvent = handleHealth(isColdStartInvocation);
                } else {
                    responseEvent = error(404, "Route not found: " + path);
                }

                if (responseEvent != null && responseEvent.getBody() != null) {
                    resolvedStatus = responseEvent.getBody().getStatusCode();
                }
            } catch (IllegalArgumentException e) {
                log.warn("Payload pattern contract validation failed: {}", e.getMessage());
                responseEvent = error(400, e.getMessage());
                resolvedStatus = 400;
            } catch (Exception e) {
                log.error("Unhandled runtime exception encountered", e);
                responseEvent = error(500, "Internal server error");
                resolvedStatus = 500;
            } finally {
                long duration = System.currentTimeMillis() - start;

                // Emit metrics to OCI Monitoring Client
                ObservabilityHelper.postInvocation(path, method, isColdStartInvocation);
                ObservabilityHelper.postDuration(path, method, duration);
                if (resolvedStatus >= 400) {
                    ObservabilityHelper.postError(path, method, resolvedStatus);
                }

                ObservabilityHelper.endSpan(span, resolvedStatus);

                log.info("COMPLETE {} {} | status={} | elapsed={}ms", method, path, resolvedStatus, duration);

                // Populate metadata back to ApiResponse object
                if (responseEvent != null && responseEvent.getBody() != null) {
                    ApiResponse body = responseEvent.getBody();
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

    private APIGatewayResponseEvent<ApiResponse> handleHello() {
        return ok(ApiResponse.ok("Hello from OCI Functions (Java 17)! Environment: " + environment));
    }

    private APIGatewayResponseEvent<ApiResponse> handleHealth(boolean isColdStart) {
        java.util.Map<String, Object> diag = new java.util.LinkedHashMap<>();
        diag.put("status", "healthy");
        diag.put("environment", environment);
        diag.put("cold_start_active", isColdStart);
        return ok(ApiResponse.ok("FaaS Instance Diagnostic Trace", diag));
    }

    private String extractRoutePath(String fullPath) {
        if (fullPath == null || fullPath.isEmpty()) {
            return "/";
        }
        int lastSlash = fullPath.lastIndexOf('/');
        if (lastSlash <= 0) {
            return fullPath;
        }
        return fullPath.substring(lastSlash);
    }

    private APIGatewayResponseEvent<ApiResponse> ok(ApiResponse body) {
        return response(200, body);
    }

    private APIGatewayResponseEvent<ApiResponse> error(int status, String message) {
        return response(status, ApiResponse.error(status, message));
    }

    private APIGatewayResponseEvent<ApiResponse> response(int status, ApiResponse body) {
        return new APIGatewayResponseEvent.Builder<ApiResponse>()
                .statusCode(status)
                .headers(Headers.emptyHeaders()
                        .addHeader("Content-Type", "application/json"))
                .body(body)
                .build();
    }
}
