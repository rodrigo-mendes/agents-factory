package com.brx.functions.event.consumer.notify.client;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

import com.brx.functions.event.consumer.notify.client.http.HttpRetryExecutor;
import com.brx.functions.event.consumer.notify.client.http.HttpRetryExecutor.ResponseHandler;

/**
 * Forwards the event JSON to the downstream notify target via HTTP POST, reusing the same
 * retry/backoff engine ({@link HttpRetryExecutor}) as the reference REST proxy. The target is a
 * plain echo endpoint in the POC; this class only owns the request shape and success/failure
 * mapping — the retry loop is shared.
 */
public class NotifyClient {

    private final HttpRetryExecutor retryExecutor;
    private final String targetUrl;
    private final Duration timeout;

    public NotifyClient(HttpClient httpClient, String targetUrl, long timeoutMs) {
        this.targetUrl = targetUrl;
        this.timeout = Duration.ofMillis(timeoutMs);
        this.retryExecutor = new HttpRetryExecutor(httpClient, "NotifyTarget");
    }

    /** POSTs the event JSON and returns the response body. */
    public String forward(String json) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(targetUrl))
                .header("Content-Type", "application/json")
                .timeout(timeout)
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();

        return retryExecutor.execute(request, JSON_RESPONSE_HANDLER);
    }

    private static final ResponseHandler<String> JSON_RESPONSE_HANDLER = new ResponseHandler<>() {
        @Override
        public String onSuccess(HttpResponse<String> response) {
            return response.body();
        }

        @Override
        public IOException onFailure(HttpResponse<String> response) {
            return new IOException("NotifyTarget HTTP error: " + response.statusCode());
        }
    };
}
