package com.brx.functions.rr.restproxy.client;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import java.util.logging.Logger;

import com.brx.functions.rr.restproxy.ObservabilityHelper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import io.opentelemetry.api.trace.Span;

/**
 * OAuth2 Client Credentials token provider with hot-function caching.
 *
 * <p>Thread-safe: the token is cached in volatile fields and acquisition is {@code synchronized}
 * to prevent concurrent token requests. The token is proactively refreshed
 * {@link #REFRESH_SKEW_SECONDS} before expiry.
 */
class OAuth2TokenProvider {

    private static final Logger LOG = Logger.getLogger(OAuth2TokenProvider.class.getName());
    private static final int REFRESH_SKEW_SECONDS = 60;
    private static final long DEFAULT_EXPIRES_IN_SECONDS = 3600;

    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;
    private final String tokenUrl;
    private final String scope;
    private final String clientId;
    private final String clientSecret;
    private final Duration timeout;

    private volatile String cachedToken;
    private volatile Instant tokenExpiresAt = Instant.MIN;

    OAuth2TokenProvider(HttpClient httpClient, ObjectMapper objectMapper, String tokenUrl,
                        String scope, String clientId, String clientSecret, Duration timeout) {
        this.httpClient = httpClient;
        this.objectMapper = objectMapper;
        this.tokenUrl = tokenUrl;
        this.scope = scope;
        this.clientId = clientId;
        this.clientSecret = clientSecret;
        this.timeout = timeout;
    }

    synchronized String getToken() throws IOException, InterruptedException {
        if (cachedToken != null
                && Instant.now().plusSeconds(REFRESH_SKEW_SECONDS).isBefore(tokenExpiresAt)) {
            return cachedToken;
        }

        LOG.info("Acquiring new OAuth2 token from IDCS");

        String credentials = Base64.getEncoder().encodeToString(
                (clientId + ":" + clientSecret).getBytes());
        String body = "grant_type=client_credentials&scope=" + scope;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(tokenUrl))
                .header("Content-Type", "application/x-www-form-urlencoded")
                .header("Authorization", "Basic " + credentials)
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .timeout(timeout)
                .build();

        // CLIENT child span for the OAuth2 token acquisition. No credentials/tokens recorded.
        Span span = ObservabilityHelper.startChildSpan("RMS.OAuthToken");
        span.setAttribute("peer.service", "idcs-oauth");
        span.setAttribute("http.method", "POST");
        try {
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            span.setAttribute("http.status_code", response.statusCode());

            if (response.statusCode() != 200) {
                throw new IOException(
                        "OAuth2 token request failed with status: " + response.statusCode());
            }

            JsonNode json = objectMapper.readTree(response.body());
            JsonNode accessTokenNode = json.get("access_token");
            JsonNode expiresInNode = json.get("expires_in");
            if (accessTokenNode == null) {
                throw new IOException("OAuth2 response missing access_token field");
            }
            cachedToken = accessTokenNode.asText();
            long expiresIn = expiresInNode != null ? expiresInNode.asLong() : DEFAULT_EXPIRES_IN_SECONDS;
            tokenExpiresAt = Instant.now().plusSeconds(expiresIn);

            ObservabilityHelper.endSpan(span, (Throwable) null);
            LOG.info("OAuth2 token acquired, expires in " + expiresIn + "s");
            return cachedToken;
        } catch (IOException | InterruptedException | RuntimeException e) {
            ObservabilityHelper.endSpan(span, e);
            throw e;
        }
    }

    void invalidate() {
        this.cachedToken = null;
        this.tokenExpiresAt = Instant.MIN;
    }
}
