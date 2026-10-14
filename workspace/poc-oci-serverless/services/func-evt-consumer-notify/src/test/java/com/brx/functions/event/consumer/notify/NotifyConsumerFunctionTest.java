package com.brx.functions.event.consumer.notify;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.io.IOException;
import java.util.Date;
import java.util.List;

import org.junit.Before;
import org.junit.Test;
import org.mockito.ArgumentCaptor;
import org.mockito.Captor;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import com.brx.functions.common.obs.DomainEvent;
import com.brx.functions.event.consumer.notify.client.NotifyClient;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fnproject.events.input.ConnectorHubBatch;
import com.fnproject.events.input.sch.StreamingData;
import com.fnproject.fn.api.Headers;

public class NotifyConsumerFunctionTest {

    @Mock
    private NotifyClient notifyClient;

    @Captor
    private ArgumentCaptor<String> jsonCaptor;

    private NotifyConsumerFunction function;
    private ObjectMapper objectMapper;

    @Before
    public void setUp() {
        MockitoAnnotations.openMocks(this);
        objectMapper = new ObjectMapper();
        function = new NotifyConsumerFunction(objectMapper, notifyClient);
    }

    @Test
    public void testForwardsEachEventAndPreservesTrace() throws Exception {
        when(notifyClient.forward(anyString())).thenReturn("<ok/>");

        DomainEvent e = event("evt-1", "order.created",
                "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01", "state=1");
        function.handler(batchOf(e));

        verify(notifyClient, times(1)).forward(jsonCaptor.capture());
        // The forwarded JSON must carry the same trace context the producer injected — this is what
        // lets the consumer span re-parent onto the producer trace.
        String forwarded = jsonCaptor.getValue();
        DomainEvent roundTrip = objectMapper.readValue(forwarded, DomainEvent.class);
        assertEquals("order.created", roundTrip.event_type());
        assertEquals("00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
                roundTrip.trace.traceparent());
        assertEquals("state=1", roundTrip.trace.tracestate());
    }

    @Test
    public void testTraceparentIsReadFromEnvelope() throws Exception {
        when(notifyClient.forward(anyString())).thenReturn("<ok/>");
        // A record whose event carries a traceparent must be accepted and forwarded (span re-parents
        // onto that remote context; tracer is off in tests so we assert the read path works).
        DomainEvent e = event("evt-tp", "inventory.updated",
                "00-11111111111111111111111111111111-2222222222222222-01", null);
        function.handler(batchOf(e));
        verify(notifyClient, times(1)).forward(anyString());
    }

    @Test
    public void testIdempotencyDedupWithinBatch() throws Exception {
        when(notifyClient.forward(anyString())).thenReturn("<ok/>");

        DomainEvent first = event("dup-1", "order.created", null, null);
        DomainEvent duplicate = event("dup-1", "order.created", null, null); // same event_id

        function.handler(batchOf(first, duplicate));

        // Only the first is forwarded; the duplicate is deduped by event_id.
        verify(notifyClient, times(1)).forward(anyString());
    }

    @Test
    public void testIdempotencyDedupAcrossBatches() throws Exception {
        when(notifyClient.forward(anyString())).thenReturn("<ok/>");

        DomainEvent e = event("dup-across", "order.created", null, null);
        function.handler(batchOf(e));
        function.handler(batchOf(e)); // same JVM instance — dedup set persists

        verify(notifyClient, times(1)).forward(anyString());
    }

    @Test
    public void testPerRecordFailureThrowsRuntimeExceptionFor502() throws Exception {
        doThrow(new IOException("NotifyTarget HTTP error: 500"))
                .when(notifyClient).forward(anyString());

        DomainEvent e = event("fail-1", "order.created", null, null);
        try {
            function.handler(batchOf(e));
            org.junit.Assert.fail("Expected RuntimeException to signal 502 for SCH retry");
        } catch (RuntimeException ex) {
            assertTrue(ex.getMessage().contains("fail-1"));
        }
    }

    @Test
    public void testFailedEventIsRetryableAfterRollback() throws Exception {
        // First attempt fails (rolls back dedup); a subsequent retry with the same event succeeds.
        doThrow(new IOException("NotifyTarget HTTP error: 500"))
                .doReturn("<ok/>")
                .when(notifyClient).forward(anyString());

        DomainEvent e = event("retry-1", "order.created", null, null);
        try {
            function.handler(batchOf(e));
            org.junit.Assert.fail("first attempt should throw");
        } catch (RuntimeException ignored) {
            // expected
        }
        // retry — must NOT be deduped away, must be forwarded again
        function.handler(batchOf(e));
        verify(notifyClient, times(2)).forward(anyString());
    }

    // --- Helpers ---

    private DomainEvent event(String id, String type, String traceparent, String tracestate) {
        return new DomainEvent(id, type, null, "corr-" + id, "txn-" + id,
                "2026-07-21T00:00:00Z", new DomainEvent.Trace(traceparent, tracestate));
    }

    @SafeVarargs
    private ConnectorHubBatch<StreamingData<DomainEvent>> batchOf(DomainEvent... events) {
        List<StreamingData<DomainEvent>> records = new java.util.ArrayList<>();
        int offset = 0;
        for (DomainEvent e : events) {
            records.add(new StreamingData<>("event-stream", "0", e.event_type(), e,
                    String.valueOf(offset++), new Date()));
        }
        return new ConnectorHubBatch<>(records, Headers.emptyHeaders());
    }
}
