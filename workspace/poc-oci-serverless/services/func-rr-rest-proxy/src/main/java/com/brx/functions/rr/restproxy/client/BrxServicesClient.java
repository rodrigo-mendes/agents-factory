package com.brx.functions.rr.restproxy.client;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

import com.brx.functions.rr.restproxy.client.http.HttpRetryExecutor;
import com.brx.functions.rr.restproxy.client.http.HttpRetryExecutor.ResponseHandler;

/**
 * HTTP client for the BrxServices XML API. Wraps XML payloads in POST/PUT requests and
 * delegates HTTP retry to {@link HttpRetryExecutor}.
 */
public class BrxServicesClient {

    private final HttpRetryExecutor retryExecutor;
    private final String destinationBaseUrl;
    private final Duration timeout;

    public BrxServicesClient(HttpClient httpClient, String destinationBaseUrl, long timeoutMs) {
        this.destinationBaseUrl = destinationBaseUrl;
        this.timeout = Duration.ofMillis(timeoutMs);
        this.retryExecutor = new HttpRetryExecutor(httpClient, "BrxServices");
    }

    public String send(String xml, String httpMethod) throws IOException, InterruptedException {
        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(destinationBaseUrl))
                .header("Content-Type", "application/xml")
                .timeout(timeout);

        if ("PUT".equalsIgnoreCase(httpMethod)) {
            builder.PUT(HttpRequest.BodyPublishers.ofString(xml));
        } else {
            builder.POST(HttpRequest.BodyPublishers.ofString(xml));
        }

        return retryExecutor.execute(builder.build(), XML_RESPONSE_HANDLER);
    }

    private static final ResponseHandler<String> XML_RESPONSE_HANDLER = new ResponseHandler<>() {
        @Override
        public String onSuccess(HttpResponse<String> response) {
            return response.body();
        }

        @Override
        public IOException onFailure(HttpResponse<String> response) {
            return new IOException("BrxServices HTTP error: " + response.statusCode());
        }
    };
}
