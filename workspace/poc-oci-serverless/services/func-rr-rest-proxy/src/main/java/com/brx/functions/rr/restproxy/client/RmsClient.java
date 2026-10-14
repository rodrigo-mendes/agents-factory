package com.brx.functions.rr.restproxy.client;

import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;

import com.brx.functions.rr.restproxy.client.http.HttpRetryExecutor;
import com.brx.functions.rr.restproxy.client.http.HttpRetryExecutor.ResponseHandler;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * HTTP client for the Oracle RMS REST API (JSON). Delegates OAuth2 token management to
 * {@link OAuth2TokenProvider} and HTTP retry to {@link HttpRetryExecutor}; this class only
 * builds RMS endpoints and maps responses.
 */
public class RmsClient {

    private final OAuth2TokenProvider tokenProvider;
    private final HttpRetryExecutor retryExecutor;
    private final ObjectMapper objectMapper;
    private final String sourceBaseUrl;
    private final Duration timeout;

    public RmsClient(HttpClient httpClient, ObjectMapper objectMapper,
                     String sourceBaseUrl, String oauthTokenUrl, String oauthScope,
                     String clientId, String clientSecret, long timeoutMs) {
        this.objectMapper = objectMapper;
        this.sourceBaseUrl = sourceBaseUrl;
        this.timeout = Duration.ofMillis(timeoutMs);
        this.tokenProvider = new OAuth2TokenProvider(httpClient, objectMapper, oauthTokenUrl,
                oauthScope, clientId, clientSecret, timeout);
        this.retryExecutor = new HttpRetryExecutor(httpClient, "RMS");
    }

    public String getAccessToken() throws IOException, InterruptedException {
        return tokenProvider.getToken();
    }

    public Map<String, Object> getStoreDetail(String storeId) throws IOException, InterruptedException {
        String token = getAccessToken();
        String url = sourceBaseUrl + "/services/private/Store/storeDetail?store=" + storeId;
        return fetchJson(url, token);
    }

    public Map<String, Object> getItemsDelta(String since, String before)
            throws IOException, InterruptedException {
        String token = getAccessToken();
        // MerchIntegrations is a SIBLING of RmsReSTServices, not a child: swap the trailing
        // path segment instead of appending under sourceBaseUrl (…/RmsReSTServices/Merch… → 404).
        String merchBase = sourceBaseUrl.replace("/RmsReSTServices", "/MerchIntegrations");
        StringBuilder url = new StringBuilder(
                merchBase + "/services/foundation/item?limit=1000");
        appendEncodedParam(url, "since", since);
        appendEncodedParam(url, "before", before);
        return fetchJson(url.toString(), token);
    }

    private Map<String, Object> fetchJson(String url, String token)
            throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Authorization", "Bearer " + token)
                .header("Accept", "application/json")
                .GET()
                .timeout(timeout)
                .build();
        return retryExecutor.execute(request, jsonResponseHandler);
    }

    private static void appendEncodedParam(StringBuilder url, String name, String value) {
        if (value != null && !value.isBlank()) {
            url.append('&').append(name).append('=')
                    .append(URLEncoder.encode(value, StandardCharsets.UTF_8));
        }
    }

    private final ResponseHandler<Map<String, Object>> jsonResponseHandler =
            new ResponseHandler<>() {
                @Override
                @SuppressWarnings("unchecked")
                public Map<String, Object> onSuccess(java.net.http.HttpResponse<String> response)
                        throws IOException {
                    return objectMapper.readValue(response.body(), Map.class);
                }

                @Override
                public IOException onFailure(java.net.http.HttpResponse<String> response) {
                    return new IOException("Falha na chamada HTTP: " + response.statusCode()
                            + (response.body() != null ? " - " + response.body() : ""));
                }
            };

    // Visible for testing
    void invalidateToken() {
        tokenProvider.invalidate();
    }
}
