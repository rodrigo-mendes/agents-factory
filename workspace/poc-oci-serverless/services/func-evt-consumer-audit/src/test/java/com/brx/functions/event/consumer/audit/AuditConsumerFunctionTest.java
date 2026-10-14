package com.brx.functions.event.consumer.audit;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;

import org.junit.Before;
import org.junit.Test;

import com.brx.functions.common.obs.DomainEvent;
import com.brx.functions.event.consumer.audit.AuditConsumerFunction.MetricSink;
import com.fnproject.events.input.ConnectorHubBatch;
import com.fnproject.events.input.sch.StreamingData;
import com.fnproject.fn.api.Headers;

public class AuditConsumerFunctionTest {

    /** Records every metric the handler emits so the test can assert names, values and dimensions. */
    private static final class RecordingSink implements MetricSink {
        record Metric(String name, double value, Map<String, String> dims) {
        }

        final List<Metric> metrics = new ArrayList<>();

        @Override
        public void post(String name, double value, Map<String, String> dimensions) {
            metrics.add(new Metric(name, value, dimensions));
        }
    }

    private RecordingSink sink;
    private AuditConsumerFunction function;

    @Before
    public void setUp() {
        sink = new RecordingSink();
        function = new AuditConsumerFunction(sink);
    }

    @Test
    public void testEmitsAuditProcessedAndLagMetrics() {
        // Event 2s in the past → lag ~2000ms, non-negative.
        String ts = Instant.now().minusSeconds(2).toString();
        DomainEvent e = event("a-1", "order.created", ts, null, null);

        function.handler(batchOf(e));

        RecordingSink.Metric processed = find(sink, "AuditEventProcessed");
        assertNotNull("AuditEventProcessed must be emitted", processed);
        assertEquals(1.0, processed.value(), 0.0001);
        assertEquals("order.created", processed.dims().get("event_type"));

        RecordingSink.Metric lag = find(sink, "EventConsumeLagMs");
        assertNotNull("EventConsumeLagMs must be emitted", lag);
        assertTrue("lag must be >= 0", lag.value() >= 0);
        assertEquals("func-evt-consumer-audit", lag.dims().get("consumer"));
        assertEquals("order.created", lag.dims().get("event_type"));
    }

    @Test
    public void testUnparseableTimestampSkipsLagButStillAudits() {
        DomainEvent e = event("a-2", "inventory.updated", "not-a-timestamp", null, null);

        function.handler(batchOf(e));

        assertNotNull(find(sink, "AuditEventProcessed"));
        // Lag metric is skipped when the timestamp cannot be parsed.
        org.junit.Assert.assertNull(find(sink, "EventConsumeLagMs"));
    }

    @Test
    public void testTraceparentIsReadFromEnvelope() {
        DomainEvent e = event("a-tp", "order.created", Instant.now().toString(),
                "00-11111111111111111111111111111111-2222222222222222-01", "vendor=x");
        function.handler(batchOf(e)); // must not throw; span re-parents onto remote context
        assertNotNull(find(sink, "AuditEventProcessed"));
    }

    @Test
    public void testIdempotencyDedup() {
        String ts = Instant.now().toString();
        DomainEvent first = event("dup-1", "order.created", ts, null, null);
        DomainEvent duplicate = event("dup-1", "order.created", ts, null, null);

        function.handler(batchOf(first, duplicate));

        long processedCount = sink.metrics.stream()
                .filter(m -> m.name().equals("AuditEventProcessed"))
                .count();
        assertEquals("duplicate event_id must be audited only once", 1, processedCount);
    }

    @Test
    public void testPerRecordFailureThrowsRuntimeExceptionFor502() {
        MetricSink throwing = (name, value, dims) -> {
            throw new RuntimeException("monitoring boom");
        };
        AuditConsumerFunction fn = new AuditConsumerFunction(throwing);

        DomainEvent e = event("fail-1", "order.created", Instant.now().toString(), null, null);
        try {
            fn.handler(batchOf(e));
            org.junit.Assert.fail("Expected RuntimeException to signal 502 for SCH retry");
        } catch (RuntimeException ex) {
            assertTrue(ex.getMessage().contains("fail-1"));
        }
    }

    // --- Helpers ---

    private static RecordingSink.Metric find(RecordingSink sink, String name) {
        return sink.metrics.stream().filter(m -> m.name().equals(name)).findFirst().orElse(null);
    }

    private DomainEvent event(String id, String type, String timestamp,
                              String traceparent, String tracestate) {
        return new DomainEvent(id, type, null, "corr-" + id, "txn-" + id,
                timestamp, new DomainEvent.Trace(traceparent, tracestate));
    }

    @SafeVarargs
    private ConnectorHubBatch<StreamingData<DomainEvent>> batchOf(DomainEvent... events) {
        List<StreamingData<DomainEvent>> records = new ArrayList<>();
        int offset = 0;
        for (DomainEvent e : events) {
            records.add(new StreamingData<>("event-stream", "0", e.event_type(), e,
                    String.valueOf(offset++), new Date()));
        }
        return new ConnectorHubBatch<>(records, Headers.emptyHeaders());
    }
}
