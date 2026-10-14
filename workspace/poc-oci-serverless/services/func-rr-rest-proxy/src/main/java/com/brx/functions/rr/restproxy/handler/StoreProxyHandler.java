package com.brx.functions.rr.restproxy.handler;

import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.brx.functions.rr.restproxy.client.BrxServicesClient;
import com.brx.functions.rr.restproxy.client.RmsClient;
import com.brx.functions.rr.restproxy.model.StoreDescModel;
import com.brx.functions.rr.restproxy.model.StoreRequest;
import com.brx.functions.rr.restproxy.model.StoreResponse;
import com.brx.functions.rr.restproxy.obs.TracedCall;
import com.brx.functions.rr.restproxy.transform.StoreMapper;
import com.brx.functions.rr.restproxy.transform.XmlMarshaller;
import com.brx.functions.rr.restproxy.web.ResponseFactory;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.output.APIGatewayResponseEvent;

/**
 * Handles the store create/update flow: resolve store id and operation, fetch store detail from
 * RMS, transform JSON → XML, and forward to BrxServices. Validation failures return a structured
 * response; downstream failures propagate to be mapped by the caller's {@code ErrorMapper}.
 */
public class StoreProxyHandler {

    private static final Logger log = LoggerFactory.getLogger(StoreProxyHandler.class);

    private final RmsClient rmsClient;
    private final BrxServicesClient brxServicesClient;
    private final StoreMapper storeMapper;
    private final XmlMarshaller xmlMarshaller;
    private final ObjectMapper objectMapper;
    private final ResponseFactory responses;

    public StoreProxyHandler(RmsClient rmsClient, BrxServicesClient brxServicesClient,
                             StoreMapper storeMapper, XmlMarshaller xmlMarshaller,
                             ObjectMapper objectMapper, ResponseFactory responses) {
        this.rmsClient = rmsClient;
        this.brxServicesClient = brxServicesClient;
        this.storeMapper = storeMapper;
        this.xmlMarshaller = xmlMarshaller;
        this.objectMapper = objectMapper;
        this.responses = responses;
    }

    public APIGatewayResponseEvent<StoreResponse> handle(APIGatewayRequestEvent<String> req,
                                                         String path, long startTime) throws Exception {
        // 1. Extract store_id from query param or request body
        String storeId = resolveStoreId(req);
        if (storeId == null || storeId.isBlank()) {
            return responses.error(400, StoreResponse.error("store_id is required", null));
        }

        // 2. Check credentials are available
        if (rmsClient == null) {
            return responses.error(500, StoreResponse.error("Function not initialized", "rmsClient is null"));
        }

        // 3. Determine operation from path
        String operacao = resolveOperation(path);
        String httpMethod = "update".equals(operacao) ? "PUT" : "POST";

        log.info("Processing store {} for storeId={}", operacao, storeId);

        // 4. Get store detail from RMS
        Map<String, Object> rmsData = fetchStoreDetail(storeId);

        // 5. Transform JSON -> StoreDescModel -> XML
        StoreDescModel model = storeMapper.map(rmsData);
        String xml = xmlMarshaller.marshal(model);

        // 6. Send XML to BrxServices
        sendToBrx(xml, operacao, httpMethod);

        // 7. Return success response
        long elapsed = System.currentTimeMillis() - startTime;
        return responses.ok(StoreResponse.success(operacao, storeId, elapsed));
    }

    /** Fetches the store detail from RMS, traced as a CLIENT child span. */
    private Map<String, Object> fetchStoreDetail(String storeId) throws Exception {
        return TracedCall.run("RMS.StoreDetail", "oracle-rms",
                () -> rmsClient.getStoreDetail(storeId));
    }

    /** Sends the store XML to BrxServices, traced as a CLIENT child span. */
    private void sendToBrx(String xml, String operacao, String httpMethod) throws Exception {
        String spanName = "update".equals(operacao) ? "BrxServices.StoreUpdate" : "BrxServices.StoreCreate";
        TracedCall.run(spanName, "brx-services", Map.of("http.method", httpMethod),
                () -> brxServicesClient.send(xml, httpMethod));
    }

    private String resolveStoreId(APIGatewayRequestEvent<String> req) {
        // Try query parameter first
        String queryParam = req.getQueryParameters().get("store").orElse(null);
        if (queryParam != null && !queryParam.isBlank()) {
            return queryParam;
        }
        // Fall back to request body
        try {
            String rawBody = req.getBody();
            if (rawBody != null && !rawBody.isBlank()) {
                StoreRequest body = objectMapper.readValue(rawBody, StoreRequest.class);
                return body != null ? body.getStoreId() : null;
            }
        } catch (Exception e) {
            log.warn("Failed to parse StoreRequest body for store_id: {}", e.getMessage());
        }
        return null;
    }

    private String resolveOperation(String path) {
        if (path != null && path.contains("/update")) {
            return "update";
        }
        return "create";
    }
}
