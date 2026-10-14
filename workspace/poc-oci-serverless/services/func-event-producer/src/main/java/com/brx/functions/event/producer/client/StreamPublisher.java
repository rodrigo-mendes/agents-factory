package com.brx.functions.event.producer.client;

import static java.nio.charset.StandardCharsets.UTF_8;

import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.oracle.bmc.streaming.StreamClient;
import com.oracle.bmc.streaming.model.PutMessagesDetails;
import com.oracle.bmc.streaming.model.PutMessagesDetailsEntry;
import com.oracle.bmc.streaming.model.PutMessagesResultEntry;
import com.oracle.bmc.streaming.requests.PutMessagesRequest;
import com.oracle.bmc.streaming.responses.PutMessagesResponse;

/**
 * Thin wrapper over the OCI Streaming {@link StreamClient} that publishes a single message with
 * {@code key = event_type} (partitioning) and {@code value = UTF-8 JSON bytes}, then verifies the
 * per-message result. HTTP 200 does NOT guarantee delivery — every {@link PutMessagesResultEntry}
 * is inspected and any {@code error} raises {@link StreamPublishException} so the caller maps it to
 * a 503 instead of silently losing the event.
 *
 * <p>The SDK/FDK handles base64 wire encoding; callers pass raw UTF-8 JSON bytes.
 */
public class StreamPublisher {

    private static final Logger log = LoggerFactory.getLogger(StreamPublisher.class);

    private final StreamClient streamClient;
    private final String streamId;

    public StreamPublisher(StreamClient streamClient, String streamId) {
        this.streamClient = streamClient;
        this.streamId = streamId;
    }

    /** Raised when the stream is unavailable or any message entry reports an error. */
    public static class StreamPublishException extends RuntimeException {
        public StreamPublishException(String message) {
            super(message);
        }

        public StreamPublishException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    /**
     * Publishes one message. Never Base64-encodes manually — passes UTF-8 bytes; the SDK encodes.
     *
     * @param key  partition key (the event type)
     * @param json the DomainEvent serialized as JSON
     * @throws StreamPublishException on transport failure or any per-message error entry
     */
    public void publish(String key, String json) {
        PutMessagesDetailsEntry entry = PutMessagesDetailsEntry.builder()
                .key(key.getBytes(UTF_8))
                .value(json.getBytes(UTF_8))
                .build();

        PutMessagesDetails details = PutMessagesDetails.builder()
                .messages(List.of(entry))
                .build();

        PutMessagesRequest request = PutMessagesRequest.builder()
                .streamId(streamId)
                .putMessagesDetails(details)
                .build();

        PutMessagesResponse response;
        try {
            response = streamClient.putMessages(request);
        } catch (Exception e) {
            throw new StreamPublishException("PutMessages call failed: "
                    + e.getClass().getName() + ": " + e.getMessage(), e);
        }

        // CRITICAL: HTTP 200 ≠ all messages succeeded. Inspect every per-message entry.
        int failed = 0;
        for (PutMessagesResultEntry resultEntry : response.getPutMessagesResult().getEntries()) {
            if (resultEntry.getError() != null) {
                failed++;
                log.error("Stream message publish failed: {} - {}",
                        resultEntry.getError(), resultEntry.getErrorMessage());
            }
        }
        if (failed > 0) {
            throw new StreamPublishException(failed + " message(s) failed to publish to stream");
        }
    }
}
