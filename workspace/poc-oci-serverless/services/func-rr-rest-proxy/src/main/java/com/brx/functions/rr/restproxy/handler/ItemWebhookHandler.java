package com.brx.functions.rr.restproxy.handler;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.brx.functions.rr.restproxy.client.BrxServicesClient;
import com.brx.functions.rr.restproxy.client.RmsClient;
import com.brx.functions.rr.restproxy.model.ItemDescModel;
import com.brx.functions.rr.restproxy.model.ItemWebhookPayload.ItemDetails;
import com.brx.functions.rr.restproxy.model.StoreRequest;
import com.brx.functions.rr.restproxy.model.StoreResponse;
import com.brx.functions.rr.restproxy.obs.TracedCall;
import com.brx.functions.rr.restproxy.transform.XmlMarshaller;
import com.brx.functions.rr.restproxy.web.ResponseFactory;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.output.APIGatewayResponseEvent;

/**
 * Handles the item webhook flow. Supports two modes: a direct items array in the payload, or an
 * EVENT-only payload where items are fetched from RMS as a delta between {@code since}/{@code before}.
 * Each item is transformed to XML and forwarded to BrxServices; per-item failures are collected and
 * reported as a Multi-Status (207) partial result.
 *
 * <p>{@code handle} reads as: validate body → resolve items → forward items → build response. The
 * mechanics of each step live in the private helpers below.
 */
public class ItemWebhookHandler {

    private static final Logger log = LoggerFactory.getLogger(ItemWebhookHandler.class);
    private static final Duration DEFAULT_DELTA_WINDOW = Duration.ofMinutes(10);

    private final RmsClient rmsClient;
    private final BrxServicesClient brxServicesClient;
    private final XmlMarshaller xmlMarshaller;
    private final ObjectMapper objectMapper;
    private final ResponseFactory responses;

    public ItemWebhookHandler(RmsClient rmsClient, BrxServicesClient brxServicesClient,
                              XmlMarshaller xmlMarshaller, ObjectMapper objectMapper,
                              ResponseFactory responses) {
        this.rmsClient = rmsClient;
        this.brxServicesClient = brxServicesClient;
        this.xmlMarshaller = xmlMarshaller;
        this.objectMapper = objectMapper;
        this.responses = responses;
    }

    public APIGatewayResponseEvent<StoreResponse> handle(APIGatewayRequestEvent<String> req, long startTime) {
        log.info("Processing item webhook...");

        String rawBody = req.getBody();
        if (rawBody == null || rawBody.isBlank()) {
            return emptyBodyError();
        }

        StoreRequest body;
        try {
            body = objectMapper.readValue(rawBody, StoreRequest.class);
        } catch (Exception e) {
            log.error("Failed to parse webhook JSON payload", e);
            return invalidJsonError(e);
        }
        if (body == null) {
            return emptyBodyError();
        }

        List<String> errors = new ArrayList<>();
        try {
            List<ItemDetails> items = resolveInlineItems(body);

            // EVENT-only mode: no items in the payload — fetch a delta from RMS.
            if (items == null || items.isEmpty()) {
                log.info("No items in payload, checking Option 1: EVENT-only mode");
                if (rmsClient == null) {
                    return notInitializedError();
                }
                items = fetchDeltaItems(resolveSince(body), resolveBefore(body), items);
            }

            int total = 0;
            int success = 0;
            if (items != null) {
                total = items.size();
                success = forwardItems(items, errors);
            }

            long elapsed = System.currentTimeMillis() - startTime;
            if (errors.isEmpty()) {
                return responses.ok(StoreResponse.webhookSuccess(total, success, elapsed));
            }
            return responses.error(207, StoreResponse.webhookError(
                    "Multi-Status / Partial failures", "Processed: " + success + "/" + total, errors));

        } catch (Exception e) {
            log.error("Failed to process item webhook", e);
            errors.add(e.getClass().getName() + ": " + e.getMessage());
            return responses.error(500, StoreResponse.webhookError("internal_error", e.getMessage(), errors));
        }
    }

    /**
     * Resolves items delivered inline in the webhook body, supporting both shapes: a top-level
     * {@code items} array and the RMS PAYLOAD envelope that nests them under {@code payload.items}.
     * Returns null/empty when neither carries items, so the caller falls back to the EVENT delta.
     */
    private List<ItemDetails> resolveInlineItems(StoreRequest body) {
        List<ItemDetails> items = body.getItems();
        if ((items == null || items.isEmpty()) && body.getPayload() != null) {
            items = body.getPayload().getItems();
        }
        return items;
    }

    // ── Item resolution (EVENT-only delta) ─────────────────────────────────────────────────────

    private String resolveSince(StoreRequest body) {
        String since = body.getSince();
        if (since == null || since.isBlank()) {
            since = Instant.now().minus(DEFAULT_DELTA_WINDOW).toString();
            log.info("since parameter missing, defaulted to: {}", since);
        }
        return since;
    }

    private String resolveBefore(StoreRequest body) {
        String before = body.getBefore();
        if (before == null || before.isBlank()) {
            before = Instant.now().toString();
            log.info("before parameter missing, defaulted to: {}", before);
        }
        return before;
    }

    /**
     * Fetches the item delta from RMS. Returns {@code current} unchanged when the delta response has
     * no {@code items} key, preserving the original null/empty behavior.
     */
    private List<ItemDetails> fetchDeltaItems(String since, String before, List<ItemDetails> current)
            throws Exception {
        log.info("Fetching items delta from RMS since {} before {}", since, before);
        Map<String, Object> deltaResult = TracedCall.run("RMS.ItemsDelta", "oracle-rms",
                () -> rmsClient.getItemsDelta(since, before));
        return mapRawItems(deltaResult, current);
    }

    @SuppressWarnings("unchecked")
    private List<ItemDetails> mapRawItems(Map<String, Object> deltaResult, List<ItemDetails> current) {
        if (deltaResult == null || !deltaResult.containsKey("items")) {
            return current;
        }
        List<Map<String, Object>> rawItems = (List<Map<String, Object>>) deltaResult.get("items");
        List<ItemDetails> items = new ArrayList<>();
        if (rawItems != null) {
            for (Map<String, Object> map : rawItems) {
                items.add(toItemDetails(map));
            }
        }
        return items;
    }

    private ItemDetails toItemDetails(Map<String, Object> map) {
        ItemDetails item = new ItemDetails();
        item.setItem(str(map, "item"));
        item.setItemDescription(str(map, "itemDescription"));
        item.setStatus(str(map, "status"));
        item.setAction(str(map, "action"));
        return item;
    }

    private static String str(Map<String, Object> map, String key) {
        Object value = map.get(key);
        return value != null ? String.valueOf(value) : null;
    }

    // ── Item forwarding ────────────────────────────────────────────────────────────────────────

    /** Forwards each item to BrxServices, collecting per-item failures. Returns the success count. */
    private int forwardItems(List<ItemDetails> items, List<String> errors) {
        log.info("Processing {} items from webhook/delta...", items.size());
        int success = 0;
        for (ItemDetails detail : items) {
            try {
                forwardItem(detail);
                success++;
            } catch (Exception e) {
                String errorMsg = "Item " + detail.getItem() + " failed: " + e.getMessage();
                log.warn(errorMsg);
                errors.add(errorMsg);
            }
        }
        return success;
    }

    private void forwardItem(ItemDetails detail) throws Exception {
        if (detail.getItem() == null || detail.getItem().isBlank()) {
            throw new IllegalArgumentException("item identifier is required");
        }

        ItemDescModel itemModel = new ItemDescModel(
                detail.getItem(),
                detail.getItemDescription(),
                detail.getStatus(),
                detail.getAction());

        String xml = xmlMarshaller.marshal(itemModel);
        String httpMethod = resolveItemHttpMethod(detail.getAction());

        TracedCall.run("BrxServices.PostItem", "brx-services", Map.of("http.method", httpMethod),
                () -> brxServicesClient.send(xml, httpMethod));
    }

    private String resolveItemHttpMethod(String action) {
        if ("delete".equalsIgnoreCase(action)) {
            return "DELETE";
        }
        if ("update".equalsIgnoreCase(action)) {
            return "PUT";
        }
        return "POST";
    }

    // ── Error responses ────────────────────────────────────────────────────────────────────────

    private APIGatewayResponseEvent<StoreResponse> emptyBodyError() {
        return responses.error(400, StoreResponse.webhookError(
                "payload_error", "Request body is empty", List.of("Body must not be null")));
    }

    private APIGatewayResponseEvent<StoreResponse> invalidJsonError(Exception e) {
        return responses.error(400, StoreResponse.webhookError(
                "payload_error", "Invalid JSON format: " + e.getMessage(), List.of(e.getMessage())));
    }

    private APIGatewayResponseEvent<StoreResponse> notInitializedError() {
        return responses.error(500, StoreResponse.webhookError(
                "Function not initialized", "rmsClient is null", List.of("rmsClient is null")));
    }
}
