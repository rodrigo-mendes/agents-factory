package com.brx.functions.event.consumer.notify.client.http;

import java.io.IOException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpTimeoutException;
import java.util.logging.Logger;

/**
 * Reusable HTTP send-with-retry engine shared by the REST clients.
 *
 * <p>Behavior (identical across clients): up to {@link #MAX_RETRIES} retries (3 sends total),
 * exponential backoff of {@code 2^attempt * 1000ms} on 5xx and on {@link HttpTimeoutException},
 * and success/failure handling delegated to a {@link ResponseHandler} so each client keeps its
 * own success mapping and its own exact exception messages.
 */
public class HttpRetryExecutor {

    private static final Logger LOG = Logger.getLogger(HttpRetryExecutor.class.getName());
    private static final int MAX_RETRIES = 2;

    private final HttpClient httpClient;
    private final String serviceName;

    public HttpRetryExecutor(HttpClient httpClient, String serviceName) {
        this.httpClient = httpClient;
        this.serviceName = serviceName;
    }

    /**
     * Maps an HTTP response to a client-specific result or failure. Implementations own the
     * success extraction and the exact non-2xx exception message.
     */
    public interface ResponseHandler<T> {
        /** Invoked on a 2xx response; may throw when the body cannot be parsed. */
        T onSuccess(HttpResponse<String> response) throws IOException;

        /** Builds the exception thrown on a non-retryable non-2xx (or 5xx after retries). */
        IOException onFailure(HttpResponse<String> response);
    }

    public <T> T execute(HttpRequest request, ResponseHandler<T> handler)
            throws IOException, InterruptedException {
        IOException lastException = null;

        for (int attempt = 0; attempt <= MAX_RETRIES; attempt++) {
            try {
                HttpResponse<String> response = httpClient.send(request,
                        HttpResponse.BodyHandlers.ofString());
                int status = response.statusCode();

                if (status >= 200 && status < 300) {
                    return handler.onSuccess(response);
                }

                if (status >= 500 && attempt < MAX_RETRIES) {
                    backoff(attempt, "status " + status);
                    continue;
                }

                throw handler.onFailure(response);

            } catch (HttpTimeoutException e) {
                if (attempt < MAX_RETRIES) {
                    backoff(attempt, "timeout");
                    lastException = new IOException(serviceName + " timeout after retries", e);
                } else {
                    throw new HttpTimeoutException(
                            serviceName + " timeout after " + MAX_RETRIES + " retries");
                }
            }
        }

        throw lastException != null ? lastException
                : new IOException(serviceName + " request failed after retries");
    }

    private void backoff(int attempt, String reason) throws InterruptedException {
        long backoffMs = (long) Math.pow(2, attempt) * 1000;
        LOG.warning(serviceName + " " + reason + ", retry " + (attempt + 1)
                + " after " + backoffMs + "ms");
        Thread.sleep(backoffMs);
    }
}
