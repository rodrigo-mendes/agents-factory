package com.brx.functions.rr.restproxy;

import java.io.IOException;
import java.net.http.HttpTimeoutException;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import org.junit.Before;
import org.junit.Test;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import org.mockito.Mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import org.mockito.MockitoAnnotations;

import com.brx.functions.rr.restproxy.client.BrxServicesClient;
import com.brx.functions.rr.restproxy.client.RmsClient;
import com.brx.functions.rr.restproxy.model.ItemDescModel;
import com.brx.functions.rr.restproxy.model.StoreDescModel;
import com.brx.functions.rr.restproxy.model.StoreRequest;
import com.brx.functions.rr.restproxy.model.StoreResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.output.APIGatewayResponseEvent;
import com.fnproject.fn.api.Headers;
import com.fnproject.fn.api.QueryParameters;

import jakarta.xml.bind.JAXBContext;

public class RestProxyFunctionTest {

    @Mock
    private RmsClient rmsClient;

    @Mock
    private BrxServicesClient brxServicesClient;

    private RestProxyFunction function;
    private ObjectMapper objectMapper;

    @Before
    public void setUp() throws Exception {
        MockitoAnnotations.openMocks(this);
        objectMapper = new ObjectMapper();
        JAXBContext jaxbContext = JAXBContext.newInstance(StoreDescModel.class, ItemDescModel.class);
        function = new RestProxyFunction(rmsClient, brxServicesClient, objectMapper, jaxbContext);
    }

    @Test
    public void testStoreCreateSuccess() throws Exception {
        when(rmsClient.getStoreDetail("1234")).thenReturn(sampleRmsData());
        when(brxServicesClient.send(anyString(), eq("POST"))).thenReturn("<ok/>");

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                new StoreRequest(), queryParams("store", "1234"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(200), response.getStatus());
        StoreResponse body = response.getBody();
        assertEquals("sucesso", body.getStatus());
        assertEquals("create", body.getOperacao());
        assertEquals("1234", body.getStoreId());
        assertTrue(body.getElapsedMs() >= 0);
        verify(brxServicesClient).send(anyString(), eq("POST"));
    }

    @Test
    public void testStoreUpdateSuccess() throws Exception {
        when(rmsClient.getStoreDetail("5678")).thenReturn(sampleRmsData());
        when(brxServicesClient.send(anyString(), eq("PUT"))).thenReturn("<ok/>");

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/update",
                new StoreRequest(), queryParams("store", "5678"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(200), response.getStatus());
        StoreResponse body = response.getBody();
        assertEquals("sucesso", body.getStatus());
        assertEquals("update", body.getOperacao());
        assertEquals("5678", body.getStoreId());
        verify(brxServicesClient).send(anyString(), eq("PUT"));
    }

    @Test
    public void testStoreCreateMissingId() {
        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                new StoreRequest(), emptyParams());

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(400), response.getStatus());
        assertEquals("store_id is required", response.getBody().getErro());
    }

    @Test
    public void testStoreOAuth2Failure() throws Exception {
        when(rmsClient.getStoreDetail("1234"))
                .thenThrow(new IOException("OAuth2 token request failed with status: 401"));

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                new StoreRequest(), queryParams("store", "1234"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(503), response.getStatus());
        assertEquals("Service Unavailable", response.getBody().getErro());
    }

    @Test
    public void testStoreRmsTimeout() throws Exception {
        when(rmsClient.getStoreDetail("1234"))
                .thenThrow(new HttpTimeoutException("RMS timeout"));

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                new StoreRequest(), queryParams("store", "1234"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(504), response.getStatus());
        assertEquals("Gateway Timeout", response.getBody().getErro());
    }

    @Test
    public void testStoreRms5xx() throws Exception {
        when(rmsClient.getStoreDetail("1234"))
            .thenThrow(new IOException("Falha na chamada HTTP: 500 - {\"message\":\"RMS unavailable\"}"));

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                new StoreRequest(), queryParams("store", "1234"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(502), response.getStatus());
        assertEquals("Bad Gateway", response.getBody().getErro());
        assertEquals("Falha na chamada HTTP: 500 - {\"message\":\"RMS unavailable\"}", response.getBody().getDetalhe());
        }

        @Test
        public void testStoreRms4xxMapsToBadRequest() throws Exception {
        when(rmsClient.getStoreDetail("1234"))
            .thenThrow(new IOException("Falha na chamada HTTP: 400 - {\"message\":\"Invalid Store. 1234\"}"));

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
            new StoreRequest(), queryParams("store", "1234"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(400), response.getStatus());
        assertEquals("Bad Request", response.getBody().getErro());
        assertEquals("Falha na chamada HTTP: 400 - {\"message\":\"Invalid Store. 1234\"}", response.getBody().getDetalhe());
    }

    @Test
    public void testStoreBrxServicesTimeout() throws Exception {
        when(rmsClient.getStoreDetail("1234")).thenReturn(sampleRmsData());
        when(brxServicesClient.send(anyString(), eq("POST")))
                .thenThrow(new HttpTimeoutException("BrxServices timeout"));

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                new StoreRequest(), queryParams("store", "1234"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(504), response.getStatus());
        assertEquals("Gateway Timeout", response.getBody().getErro());
    }

    @Test
    public void testStoreBrxServices5xx() throws Exception {
        when(rmsClient.getStoreDetail("1234")).thenReturn(sampleRmsData());
        when(brxServicesClient.send(anyString(), eq("POST")))
                .thenThrow(new IOException("BrxServices HTTP error: 500"));

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                new StoreRequest(), queryParams("store", "1234"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(502), response.getStatus());
        assertEquals("Bad Gateway", response.getBody().getErro());
    }

    @Test
    public void testStoreIdFromRequestBody() throws Exception {
        when(rmsClient.getStoreDetail("9999")).thenReturn(sampleRmsData());
        when(brxServicesClient.send(anyString(), eq("POST"))).thenReturn("<ok/>");

        StoreRequest bodyReq = new StoreRequest("9999");
        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                bodyReq, emptyParams());

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(200), response.getStatus());
        assertEquals("9999", response.getBody().getStoreId());
    }

    // ===== HTTP Method validation =====

    @Test
    public void testStoreCreateGetMethodStillProcesses() throws Exception {
        // Handler doesn't enforce POST — routes by path only
        when(rmsClient.getStoreDetail("1234")).thenReturn(sampleRmsData());
        when(brxServicesClient.send(anyString(), eq("POST"))).thenReturn("<ok/>");

        APIGatewayRequestEvent<String> req = buildRequest("GET", "/store/create",
                new StoreRequest(), queryParams("store", "1234"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        // Note: handler does not restrict HTTP methods, so GET proceeds
        assertEquals(Integer.valueOf(200), response.getStatus());
    }

    // ===== Store ID edge cases =====

    @Test
    public void testStoreIdEmptyString() {
        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                new StoreRequest(""), emptyParams());

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(400), response.getStatus());
        assertEquals("store_id is required", response.getBody().getErro());
    }

    @Test
    public void testStoreIdWhitespaceOnly() {
        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                new StoreRequest("   "), emptyParams());

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(400), response.getStatus());
        assertEquals("store_id is required", response.getBody().getErro());
    }

    @Test
    public void testStoreIdQueryParamPriority() throws Exception {
        // Query param takes priority over body
        when(rmsClient.getStoreDetail("from-query")).thenReturn(sampleRmsData());
        when(brxServicesClient.send(anyString(), eq("POST"))).thenReturn("<ok/>");

        StoreRequest bodyReq = new StoreRequest("from-body");
        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                bodyReq, queryParams("store", "from-query"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(200), response.getStatus());
        assertEquals("from-query", response.getBody().getStoreId());
    }

    @Test
    public void testStoreIdNonNumeric() throws Exception {
        // Non-numeric store IDs are allowed (it's a string)
        when(rmsClient.getStoreDetail("ABC-123")).thenReturn(sampleRmsData());
        when(brxServicesClient.send(anyString(), eq("POST"))).thenReturn("<ok/>");

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                new StoreRequest(), queryParams("store", "ABC-123"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(200), response.getStatus());
        assertEquals("ABC-123", response.getBody().getStoreId());
    }

    // ===== Unknown route =====

    @Test
    public void testUnknownRouteDefaultsToCreate() throws Exception {
        // resolveOperation: if path doesn't contain "/store/update", defaults to "create"
        when(rmsClient.getStoreDetail("1234")).thenReturn(sampleRmsData());
        when(brxServicesClient.send(anyString(), eq("POST"))).thenReturn("<ok/>");

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/unknown",
                new StoreRequest(), queryParams("store", "1234"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(200), response.getStatus());
        assertEquals("create", response.getBody().getOperacao());
        verify(brxServicesClient).send(anyString(), eq("POST"));
    }

    // ===== IOException edge cases =====

    @Test
    public void testStoreGenericIoException() throws Exception {
        when(rmsClient.getStoreDetail("1234"))
                .thenThrow(new IOException("Connection reset"));

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                new StoreRequest(), queryParams("store", "1234"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(500), response.getStatus());
        assertEquals("Internal server error", response.getBody().getErro());
    }

    @Test
    public void testStoreUnexpectedException() throws Exception {
        when(rmsClient.getStoreDetail("1234"))
                .thenThrow(new RuntimeException("Unexpected null pointer"));

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/store/create",
                new StoreRequest(), queryParams("store", "1234"));

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(500), response.getStatus());
        assertEquals("Internal server error", response.getBody().getErro());
    }

    // ===== Webhook (Phase 2) tests =====

    @Test
    public void testItemWebhookPayloadSuccess() throws Exception {
        when(brxServicesClient.send(anyString(), eq("POST"))).thenReturn("<ok/>");

        StoreRequest webhookBody = new StoreRequest();
        com.brx.functions.rr.restproxy.model.ItemWebhookPayload.ItemDetails item1 = new com.brx.functions.rr.restproxy.model.ItemWebhookPayload.ItemDetails();
        item1.setItem("itemA");
        item1.setItemDescription("Test Item A");
        item1.setStatus("A");
        item1.setAction("insert");

        com.brx.functions.rr.restproxy.model.ItemWebhookPayload.ItemDetails item2 = new com.brx.functions.rr.restproxy.model.ItemWebhookPayload.ItemDetails();
        item2.setItem("itemB");
        item2.setItemDescription("Test Item B");
        item2.setStatus("I");
        item2.setAction("update");

        webhookBody.setItems(List.of(item1, item2));

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/item/webhook",
                webhookBody, emptyParams());

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(200), response.getStatus());
        StoreResponse body = response.getBody();
        assertEquals("sucesso", body.getStatus());
        assertEquals("webhook-items", body.getOperacao());
        assertEquals(Integer.valueOf(2), body.getTotalProcessed());
        assertEquals(Integer.valueOf(2), body.getSuccessCount());
        verify(brxServicesClient).send(anyString(), eq("POST"));
        verify(brxServicesClient).send(anyString(), eq("PUT"));
    }

    @Test
    public void testItemWebhookEventOnlySuccess() throws Exception {
        String since = "2026-06-08T15:00:00Z";
        String before = "2026-06-08T15:10:00Z";

        Map<String, Object> deltaResult = new HashMap<>();
        Map<String, Object> itemMap = new HashMap<>();
        itemMap.put("item", "itemDelta");
        itemMap.put("itemDescription", "Delta Description");
        itemMap.put("status", "A");
        itemMap.put("action", "insert");
        deltaResult.put("items", List.of(itemMap));

        when(rmsClient.getItemsDelta(since, before)).thenReturn(deltaResult);
        when(brxServicesClient.send(anyString(), eq("POST"))).thenReturn("<ok/>");

        StoreRequest webhookBody = new StoreRequest();
        webhookBody.setSince(since);
        webhookBody.setBefore(before);

        APIGatewayRequestEvent<String> req = buildRequest("POST", "/item/webhook",
                webhookBody, emptyParams());

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(200), response.getStatus());
        StoreResponse body = response.getBody();
        assertEquals("sucesso", body.getStatus());
        assertEquals(Integer.valueOf(1), body.getTotalProcessed());
        assertEquals(Integer.valueOf(1), body.getSuccessCount());
        verify(rmsClient).getItemsDelta(since, before);
        verify(brxServicesClient).send(anyString(), eq("POST"));
    }

    @Test
    public void testItemWebhookNullBodyError() throws Exception {
        APIGatewayRequestEvent<String> req = buildRequest("POST", "/item/webhook",
                null, emptyParams());

        APIGatewayResponseEvent<StoreResponse> response = function.handler(req);

        assertEquals(Integer.valueOf(400), response.getStatus());
        assertEquals("payload_error", response.getBody().getErro());
    }

    // --- Helper methods ---

    private APIGatewayRequestEvent<String> buildRequest(String method, String path,
                                                              StoreRequest body,
                                                              QueryParameters params) {
        String jsonBody = null;
        if (body != null) {
            try {
                jsonBody = objectMapper.writeValueAsString(body);
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }
        return new APIGatewayRequestEvent<>(params, jsonBody, method, path, Headers.emptyHeaders());
    }

    private QueryParameters queryParams(String key, String value) {
        return new QueryParameters() {
            @Override
            public Optional<String> get(String k) {
                return key.equals(k) ? Optional.of(value) : Optional.empty();
            }

            @Override
            public List<String> getValues(String k) {
                return key.equals(k) ? List.of(value) : Collections.emptyList();
            }

            @Override
            public Map<String, List<String>> getAll() {
                return Map.of(key, List.of(value));
            }
        };
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

    private Map<String, Object> sampleRmsData() {
        Map<String, Object> data = new HashMap<>();
        data.put("store", 1234);
        data.put("storeType", "W");
        data.put("storeName", "Loja Centro SP");
        data.put("storeName10", "Centro SP");
        data.put("storeName3", "CSP");
        data.put("add1", "Rua Principal 100");
        data.put("add2", "Andar 2");
        data.put("city", "Sao Paulo");
        data.put("state", "SP");
        data.put("countryId", "BR");
        data.put("post", "01001-000");
        data.put("storeClass", "A");
        data.put("storeOpenDate", "2023-06-15");
        data.put("contactPhone", "11999999999");
        data.put("stockholdingInd", "Y");
        data.put("channelId", 1);
        data.put("district", 10);
        data.put("transferZone", 5);
        data.put("defaultWh", 100);
        data.put("startOrderDays", 3);
        data.put("currencyCode", "BRL");
        data.put("lang", 12);
        data.put("timezoneName", "America/Sao_Paulo");
        return data;
    }
}
