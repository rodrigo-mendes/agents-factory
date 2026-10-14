package com.brx.functions.event.producer;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

import com.brx.functions.event.producer.client.StreamPublisher;
import com.brx.functions.event.producer.client.StreamPublisher.StreamPublishException;
import com.brx.functions.event.producer.model.ProducerResponse;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.output.APIGatewayResponseEvent;
import com.fnproject.fn.api.Headers;
import com.fnproject.fn.api.QueryParameters;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.junit.Before;
import org.junit.Test;
import org.mockito.ArgumentCaptor;
import org.mockito.Captor;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

public class EventProducerFunctionTest {

    @Mock
    private StreamPublisher publisher;

    @Captor
    private ArgumentCaptor<String> jsonCaptor;

    @Captor
    private ArgumentCaptor<String> keyCaptor;

    private EventProducerFunction function;
    private ObjectMapper objectMapper;

    @Before
    public void setUp() {
        MockitoAnnotations.openMocks(this);
        objectMapper = new ObjectMapper();
        function = new EventProducerFunction(objectMapper, publisher);
    }

    @Test
    public void testValidPublishReturns202WithEventId() throws Exception {
        String body = "{\"event_type\":\"order.created\",\"payload\":{\"orderId\":\"A1\"},"
                + "\"correlation_id\":\"corr-9\"}";
        APIGatewayResponseEvent<ProducerResponse> response = invoke("POST", body);

        assertEquals(Integer.valueOf(202), response.getStatus());
        ProducerResponse rb = response.getBody();
        assertEquals("accepted", rb.getStatus());
        assertEquals("event-stream", rb.getStream());
        assertNotNull("event_id must be generated", rb.getEventId());
        assertNotNull("transaction_id must be generated", rb.getTransactionId());
        assertTrue(rb.getElapsedMs() >= 0);
    }

    @Test
    public void testPublishedEnvelopeUsesEventTypeKeyAndCarriesTrace() throws Exception {
        String body = "{\"event_type\":\"order.created\",\"payload\":{\"orderId\":\"A1\"},"
                + "\"correlation_id\":\"corr-9\"}";
        APIGatewayResponseEvent<ProducerResponse> response = invoke("POST", body);
        assertEquals(Integer.valueOf(202), response.getStatus());

        verify(publisher).publish(keyCaptor.capture(), jsonCaptor.capture());
        // Partition key MUST be the event_type
        assertEquals("order.created", keyCaptor.getValue());

        // The published envelope must contain the generated ids and a trace node (present even when
        // the tracer is off — traceparent is null in test env, but the node exists in the contract).
        JsonNode envelope = objectMapper.readTree(jsonCaptor.getValue());
        assertEquals("order.created", envelope.get("event_type").asText());
        assertEquals("corr-9", envelope.get("correlation_id").asText());
        assertNotNull(envelope.get("event_id").asText());
        assertNotNull(envelope.get("transaction_id").asText());
        assertNotNull("timestamp must be set", envelope.get("timestamp").asText());
        assertTrue("trace field must be present in envelope", envelope.has("trace"));
        assertEquals(response.getBody().getEventId(), envelope.get("event_id").asText());
    }

    @Test
    public void testMissingEventTypeReturns400() throws Exception {
        String body = "{\"payload\":{\"orderId\":\"A1\"}}";
        APIGatewayResponseEvent<ProducerResponse> response = invoke("POST", body);

        assertEquals(Integer.valueOf(400), response.getStatus());
        assertEquals("Bad Request", response.getBody().getErro());
        verify(publisher, never()).publish(anyString(), anyString());
    }

    @Test
    public void testBlankBodyReturns400() throws Exception {
        APIGatewayResponseEvent<ProducerResponse> response = invoke("POST", "");

        assertEquals(Integer.valueOf(400), response.getStatus());
        assertEquals("Bad Request", response.getBody().getErro());
        verify(publisher, never()).publish(anyString(), anyString());
    }

    @Test
    public void testStreamingFailureReturns503() throws Exception {
        doThrow(new StreamPublishException("1 message(s) failed to publish to stream"))
                .when(publisher).publish(eq("order.created"), anyString());

        String body = "{\"event_type\":\"order.created\"}";
        APIGatewayResponseEvent<ProducerResponse> response = invoke("POST", body);

        assertEquals(Integer.valueOf(503), response.getStatus());
        assertEquals("Service Unavailable", response.getBody().getErro());
    }

    @Test
    public void testNonPostReturns405() throws Exception {
        APIGatewayResponseEvent<ProducerResponse> response =
                invoke("GET", "{\"event_type\":\"order.created\"}");

        assertEquals(Integer.valueOf(405), response.getStatus());
        assertEquals("Method Not Allowed", response.getBody().getErro());
        verify(publisher, never()).publish(anyString(), anyString());
    }

    @Test
    public void testMalformedJsonReturns500() throws Exception {
        // Not valid JSON — readTree throws → mapped to 500 (serialization/parse failure).
        APIGatewayResponseEvent<ProducerResponse> response = invoke("POST", "{not-json");

        assertEquals(Integer.valueOf(500), response.getStatus());
        assertEquals("Internal server error", response.getBody().getErro());
        verify(publisher, never()).publish(anyString(), anyString());
    }

    @Test
    public void testHealthReturns200WithVersionAndConfigKeyNamesNotValues() throws Exception {
        APIGatewayResponseEvent<ProducerResponse> response = invokePath("GET", "/health");

        assertEquals(Integer.valueOf(200), response.getStatus());
        ProducerResponse body = response.getBody();
        assertEquals("healthy", body.getStatus());
        assertNotNull("version must be reported", body.getVersion());
        assertNotNull("config key names must be reported", body.getConfigKeys());
        // Names, not values: the OCID/secret keys are present as NAMES only.
        assertTrue(body.getConfigKeys().contains("STREAM_OCID"));
        assertTrue(body.getConfigKeys().contains("APM_DATA_KEY"));
        // GET diag must not publish anything.
        verify(publisher, never()).publish(anyString(), anyString());
    }

    @Test
    public void testDiagAliasAlsoReturns200() throws Exception {
        APIGatewayResponseEvent<ProducerResponse> response = invokePath("GET", "/diag");
        assertEquals(Integer.valueOf(200), response.getStatus());
        assertEquals("healthy", response.getBody().getStatus());
    }

    @Test
    public void testHealthEndpointNeverPublishesEvenWithFullPrefix() throws Exception {
        // A gateway-prefixed path (…/events/health) must still be recognised as the diag path,
        // return 200 and never reach the publish path.
        APIGatewayResponseEvent<ProducerResponse> response =
                invokePath("GET", "/producer/events/health");
        assertEquals(Integer.valueOf(200), response.getStatus());
        assertEquals("healthy", response.getBody().getStatus());
        verify(publisher, never()).publish(anyString(), anyString());
    }

    // --- Helpers ---

    private APIGatewayResponseEvent<ProducerResponse> invoke(String method, String body) {
        return function.handler(request(method, body, "/events"));
    }

    private APIGatewayResponseEvent<ProducerResponse> invokePath(String method, String path) {
        return function.handler(request(method, path));
    }

    private APIGatewayRequestEvent<String> request(String method, String path) {
        return request(method, "", path);
    }

    private APIGatewayRequestEvent<String> request(String method, String body, String path) {
        return new APIGatewayRequestEvent<>(
                emptyParams(), body, method, path, Headers.emptyHeaders());
    }

    private QueryParameters emptyParams() {
        return new QueryParameters() {
            @Override
            public Optional<String> get(String k) { return Optional.empty(); }

            @Override
            public List<String> getValues(String k) { return Collections.emptyList(); }

            @Override
            public Map<String, List<String>> getAll() { return Collections.emptyMap(); }
        };
    }
}
