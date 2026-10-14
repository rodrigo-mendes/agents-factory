package com.brx.functions.rr.restproxy;

import java.net.http.HttpClient;
import java.time.Duration;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;

import com.brx.functions.rr.restproxy.client.BrxServicesClient;
import com.brx.functions.rr.restproxy.client.RmsClient;
import com.brx.functions.rr.restproxy.handler.ItemWebhookHandler;
import com.brx.functions.rr.restproxy.handler.StoreProxyHandler;
import com.brx.functions.rr.restproxy.model.ItemDescModel;
import com.brx.functions.rr.restproxy.model.StoreDescModel;
import com.brx.functions.rr.restproxy.model.StoreResponse;
import com.brx.functions.rr.restproxy.route.Route;
import com.brx.functions.rr.restproxy.service.OciSecretService;
import com.brx.functions.rr.restproxy.transform.StoreMapper;
import com.brx.functions.rr.restproxy.transform.XmlMarshaller;
import com.brx.functions.rr.restproxy.web.ErrorMapper;
import com.brx.functions.rr.restproxy.web.ResponseFactory;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fnproject.events.APIGatewayFunction;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.output.APIGatewayResponseEvent;
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;

import io.opentelemetry.api.trace.Span;
import io.opentelemetry.context.Scope;
import jakarta.xml.bind.JAXBContext;

/**
 * API Gateway entry point that proxies store and item data between Oracle RMS (source, JSON) and
 * BrxServices (destination, XML). This class is a thin dispatcher: cold-start init lives in
 * {@link #configure}, and each request is routed by {@link Route} to a dedicated handler. Metrics,
 * tracing and MDC correlation are managed here; business logic lives in the collaborators.
 *
 * <p>Both {@code configure} and {@code handler} read as a sequence of named steps; the mechanics of
 * each step live in the private helper methods below.
 */
public class RestProxyFunction extends APIGatewayFunction<String, StoreResponse> {

    private static final Logger log = LoggerFactory.getLogger(RestProxyFunction.class);
    private static final String API_VERSION = "1.0.0";

    private RmsClient rmsClient;
    private BrxServicesClient brxServicesClient;
    private ObjectMapper objectMapper;
    private JAXBContext jaxbContext;
    private String environment;
    private boolean coldStart = true;
    private String initError;

    // Collaborators (wired in configure() and in the test constructor)
    private ResponseFactory responses;
    private ErrorMapper errorMapper;
    private StoreProxyHandler storeHandler;
    private ItemWebhookHandler webhookHandler;

    public RestProxyFunction() {
    }

    // Package-private constructor for testing
    RestProxyFunction(RmsClient rmsClient, BrxServicesClient brxServicesClient,
                      ObjectMapper objectMapper, JAXBContext jaxbContext) {
        this.rmsClient = rmsClient;
        this.brxServicesClient = brxServicesClient;
        this.objectMapper = objectMapper;
        this.jaxbContext = jaxbContext;
        wireCollaborators();
    }

    // ── Cold-start initialization ────────────────────────────────────────────────────────────

    @Override
    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        super.configure(ctx);
        try {
            long start = System.currentTimeMillis();
            this.environment = ctx.getConfigurationByKey("ENVIRONMENT").orElse("dev");
            ObservabilityHelper.configure(ctx);

            // Wrap cold-start init in its own INTERNAL root span so the Vault fetch in
            // loadOAuthSecrets nests under it (there is no request span yet at configure time).
            Span coldStart = ObservabilityHelper.startRootSpan("ColdStart func-rr-rest-proxy");
            try (Scope scope = coldStart.makeCurrent()) {
                this.objectMapper = new ObjectMapper();

                ProxyConfig config = readProxyConfig(ctx);
                HttpClient httpClient = buildHttpClient();

                OAuthCredentials credentials = loadOAuthSecrets(config.clientIdOcid(), config.clientSecretOcid());
                if (initError == null) { // skip client wiring when Vault retrieval failed
                    this.rmsClient = new RmsClient(httpClient, objectMapper,
                            config.sourceBaseUrl(), config.oauthTokenUrl(), config.oauthScope(),
                            credentials.clientId(), credentials.clientSecret(), config.timeoutMs());
                    this.brxServicesClient = new BrxServicesClient(httpClient, config.destinationBaseUrl(), config.timeoutMs());
                    this.jaxbContext = createJaxbContext();

                    wireCollaborators();
                    logColdStartComplete(ctx, start);
                }
                ObservabilityHelper.endSpan(coldStart, initError == null ? 200 : 500);
            } catch (Exception e) {
                ObservabilityHelper.endSpan(coldStart, e);
                throw e;
            }
        } catch (Exception e) {
            recordInitFailure(e);
        }
    }

    private ProxyConfig readProxyConfig(RuntimeContext ctx) {
        String sourceBaseUrl = ctx.getConfigurationByKey("STORE_SOURCE_BASE_URL")
                .orElseThrow(() -> new IllegalStateException("STORE_SOURCE_BASE_URL is required"));
        String destinationBaseUrl = ctx.getConfigurationByKey("STORE_DESTINATION_BASE_URL")
                .orElseThrow(() -> new IllegalStateException("STORE_DESTINATION_BASE_URL is required"));
        String oauthTokenUrl = ctx.getConfigurationByKey("STORE_OAUTH_TOKEN_URL")
                .orElseThrow(() -> new IllegalStateException("STORE_OAUTH_TOKEN_URL is required"));
        String oauthScope = ctx.getConfigurationByKey("STORE_OAUTH_SCOPE")
                .orElseThrow(() -> new IllegalStateException("STORE_OAUTH_SCOPE is required"));
        String clientIdOcid = ctx.getConfigurationByKey("STORE_OAUTH_CLIENT_ID_OCID").orElse("");
        String clientSecretOcid = ctx.getConfigurationByKey("STORE_OAUTH_CLIENT_SECRET_OCID").orElse("");
        long timeoutMs = Long.parseLong(ctx.getConfigurationByKey("STORE_TIMEOUT_MS").orElse("10000"));
        return new ProxyConfig(sourceBaseUrl, destinationBaseUrl, oauthTokenUrl, oauthScope,
                clientIdOcid, clientSecretOcid, timeoutMs);
    }

    private HttpClient buildHttpClient() {
        return HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(5))
                .build();
    }

    /**
     * Loads OAuth credentials from Vault. Returns blank credentials (with a warning) when the OCIDs
     * are not configured; on a Vault failure it sets {@link #initError} and returns {@code null} so
     * the caller aborts initialization.
     */
    private OAuthCredentials loadOAuthSecrets(String clientIdOcid, String clientSecretOcid) {
        if (clientIdOcid.isBlank() || clientSecretOcid.isBlank()) {
            log.warn("OAuth secret OCIDs not configured — external API calls will fail");
            return new OAuthCredentials(null, null);
        }

        Span vaultSpan = ObservabilityHelper.startChildSpan("Vault.GetSecret");
        vaultSpan.setAttribute("peer.service", "oci-vault");
        try {
            OciSecretService secretService = new OciSecretService();
            // Do NOT record secret OCIDs or values on the span — only load timing/status.
            String clientId = secretService.getSecret(clientIdOcid);
            String clientSecret = secretService.getSecret(clientSecretOcid);
            ObservabilityHelper.endSpan(vaultSpan, (Throwable) null);
            log.info("OAuth secrets loaded successfully from Vault");
            return new OAuthCredentials(clientId, clientSecret);
        } catch (Exception e) {
            ObservabilityHelper.endSpan(vaultSpan, e);
            log.error("Failed to load OAuth secrets from Vault (degraded state): {}", e.getMessage(), e);
            this.initError = "Vault secret retrieval failed: "
                    + e.getClass().getName() + ": " + e.getMessage();
            return null;
        }
    }

    private JAXBContext createJaxbContext() {
        try {
            return JAXBContext.newInstance(StoreDescModel.class, ItemDescModel.class);
        } catch (Exception e) {
            log.error("Failed to create JAXB context: {}", e.getMessage(), e);
            return null;
        }
    }

    private void logColdStartComplete(RuntimeContext ctx, long startMs) {
        long elapsed = System.currentTimeMillis() - startMs;
        log.info("RestProxyFunction COLD_START configuration completed in {}ms | env={} | memory={}MB",
                elapsed,
                environment,
                ctx.getConfigurationByKey("FN_MEMORY").orElse("?"));
    }

    private void recordInitFailure(Exception e) {
        this.initError = e.getClass().getName() + ": " + e.getMessage();
        log.error("COLD_START INIT FAILED: {}", initError, e);
    }

    /** Builds the request-handling collaborators from the initialized clients and codecs. */
    private void wireCollaborators() {
        StoreMapper storeMapper = new StoreMapper();
        XmlMarshaller xmlMarshaller = new XmlMarshaller(jaxbContext);
        this.responses = new ResponseFactory();
        this.errorMapper = new ErrorMapper(responses);
        this.storeHandler = new StoreProxyHandler(rmsClient, brxServicesClient,
                storeMapper, xmlMarshaller, objectMapper, responses);
        this.webhookHandler = new ItemWebhookHandler(rmsClient, brxServicesClient,
                xmlMarshaller, objectMapper, responses);
    }

    // ── Request handling ─────────────────────────────────────────────────────────────────────

    @Override
    public APIGatewayResponseEvent<StoreResponse> handler(APIGatewayRequestEvent<String> req) {
        long startTime = System.currentTimeMillis();
        RequestContext rc = beginRequest(req);

        if (initError != null) {
            log.error("Aborting invocation due to prior initialization failure: {}", initError);
            MDC.clear();
            return responses().error(500, StoreResponse.error("Function initialization failed", initError));
        }

        APIGatewayResponseEvent<StoreResponse> response = null;
        int resolvedStatus = 500;

        String traceparent = req.getHeaders().get("traceparent").orElse(null);
        Span span = ObservabilityHelper.startSpan(rc.method(), rc.path(), traceparent);

        // Activate the SERVER span as current context so downstream CLIENT spans opened by TracedCall
        // (RMS.*, BrxServices.*) nest under it instead of becoming orphan roots.
        try (Scope scope = span.makeCurrent()) {
            try {
                response = dispatch(rc, req, startTime);
                resolvedStatus = statusOf(response, 200);
                return response;

            } catch (Exception e) {
                response = errorMapper.toResponse(e);
                resolvedStatus = statusOf(response, 500);
                return response;

            } finally {
                long duration = System.currentTimeMillis() - startTime;
                recordTelemetry(rc, span, resolvedStatus, duration);
                populateResponseMetadata(response, duration, rc.coldStart());
                MDC.clear(); // protect warm executions from stale correlation context
            }
        }
    }

    /** Extracts correlation identifiers, primes the MDC, flips the cold-start flag, logs INVOKE. */
    private RequestContext beginRequest(APIGatewayRequestEvent<String> req) {
        String method = req.getMethod();
        String path = Route.extractRoutePath(req.getRequestUrl());
        String opcRequestId = req.getHeaders().get("opc-request-id")
                .orElseGet(() -> UUID.randomUUID().toString());

        boolean isColdStartInvocation = coldStart;
        coldStart = false; // subsequent invocations on this JVM are warm

        MDC.put("opcRequestId", opcRequestId);
        MDC.put("route", path);
        MDC.put("method", method);
        MDC.put("coldStart", String.valueOf(isColdStartInvocation));

        log.info("INVOKE {} {} | opcRequestId={} | coldStart={}", method, path, opcRequestId, isColdStartInvocation);
        return new RequestContext(method, path, opcRequestId, isColdStartInvocation);
    }

    private APIGatewayResponseEvent<StoreResponse> dispatch(RequestContext rc,
            APIGatewayRequestEvent<String> req, long startTime) throws Exception {
        switch (Route.resolve(rc.path())) {
            case HEALTH:
                return handleHealth(rc.coldStart());
            case WEBHOOK:
                return webhookHandler.handle(req, startTime);
            case STORE:
            default:
                return storeHandler.handle(req, rc.path(), startTime);
        }
    }

    /** Emits synchronous telemetry to OCI Monitoring, closes the server span, logs COMPLETE. */
    private void recordTelemetry(RequestContext rc, Span span, int status, long durationMs) {
        ObservabilityHelper.postInvocation(rc.path(), rc.method(), rc.coldStart());
        ObservabilityHelper.postDuration(rc.path(), rc.method(), durationMs);
        if (status >= 400) {
            ObservabilityHelper.postError(rc.path(), rc.method(), status);
        }
        ObservabilityHelper.endSpan(span, status);
        log.info("COMPLETE {} {} | status={} | elapsed={}ms", rc.method(), rc.path(), status, durationMs);
    }

    private void populateResponseMetadata(APIGatewayResponseEvent<StoreResponse> response,
            long durationMs, boolean coldStart) {
        if (response != null && response.getBody() != null) {
            StoreResponse body = response.getBody();
            body.setElapsedMs(durationMs);
            body.setColdStart(coldStart);
            body.setApiVersion(API_VERSION);
        }
    }

    private APIGatewayResponseEvent<StoreResponse> handleHealth(boolean isColdStart) {
        StoreResponse body = StoreResponse.success("health", "none", 0);
        body.setColdStart(isColdStart);
        body.setApiVersion(API_VERSION);
        return responses().ok(body);
    }

    private static int statusOf(APIGatewayResponseEvent<StoreResponse> response, int fallback) {
        return response != null && response.getStatus() != null ? response.getStatus() : fallback;
    }

    /** Lazily provides a ResponseFactory so early error paths work even if wiring was skipped. */
    private ResponseFactory responses() {
        if (responses == null) {
            responses = new ResponseFactory();
        }
        return responses;
    }

    // ── Value holders ────────────────────────────────────────────────────────────────────────

    /** Cold-start configuration read from {@link RuntimeContext}. */
    private record ProxyConfig(String sourceBaseUrl, String destinationBaseUrl, String oauthTokenUrl,
                               String oauthScope, String clientIdOcid, String clientSecretOcid,
                               long timeoutMs) {
    }

    /** OAuth client credentials loaded from Vault (both null when not configured). */
    private record OAuthCredentials(String clientId, String clientSecret) {
    }

    /** Per-invocation correlation context. */
    private record RequestContext(String method, String path, String opcRequestId, boolean coldStart) {
    }
}
