package com.brx.functions.rr.restproxy.model;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public class StoreRequest {

    @JsonProperty("store_id")
    private String storeId;

    // Webhook fields (Items Integration)
    private String event;
    private String since;
    private String before;
    private List<ItemWebhookPayload.ItemDetails> items;
    // RMS PAYLOAD-mode envelope nests items under "payload": {"items": [...]}
    private ItemWebhookPayload payload;

    public StoreRequest() {
    }

    public StoreRequest(String storeId) {
        this.storeId = storeId;
    }

    public String getStoreId() {
        return storeId;
    }

    public void setStoreId(String storeId) {
        this.storeId = storeId;
    }

    public String getEvent() {
        return event;
    }

    public void setEvent(String event) {
        this.event = event;
    }

    public String getSince() {
        return since;
    }

    public void setSince(String since) {
        this.since = since;
    }

    public String getBefore() {
        return before;
    }

    public void setBefore(String before) {
        this.before = before;
    }

    public List<ItemWebhookPayload.ItemDetails> getItems() {
        return items;
    }

    public void setItems(List<ItemWebhookPayload.ItemDetails> items) {
        this.items = items;
    }

    public ItemWebhookPayload getPayload() {
        return payload;
    }

    public void setPayload(ItemWebhookPayload payload) {
        this.payload = payload;
    }
}
