package com.brx.functions.event.producer.model;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * API Gateway response body for the event producer. On success carries the generated
 * {@code event_id}, an {@code accepted} status and the target stream; on error carries the
 * {@code erro}/{@code detalhe} diagnostic pair. Always includes {@code elapsed_ms} and the
 * cold-start marker for post-deploy diagnosis from the response alone.
 *
 * <p>The {@code diagnostic} variant (GET {@code /health} / {@code /diag}) reports init state,
 * function {@code version} and the CONFIGURATION KEY NAMES the function reads — never their values,
 * so secrets/OCIDs are not leaked through the health endpoint.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ProducerResponse {

    @JsonProperty("event_id")
    private String eventId;

    private String status;
    private String stream;

    @JsonProperty("transaction_id")
    private String transactionId;

    @JsonProperty("elapsed_ms")
    private long elapsedMs;

    @JsonProperty("cold_start")
    private Boolean coldStart;

    private String erro;
    private String detalhe;

    // Diagnostic-only fields (GET /health, /diag) — omitted from success/error bodies via NON_NULL.
    private String version;

    @JsonProperty("init_error")
    private String initError;

    @JsonProperty("config_keys")
    private List<String> configKeys;

    public static ProducerResponse accepted(String eventId, String transactionId, String stream) {
        ProducerResponse r = new ProducerResponse();
        r.eventId = eventId;
        r.transactionId = transactionId;
        r.status = "accepted";
        r.stream = stream;
        return r;
    }

    public static ProducerResponse error(String erro, String detalhe) {
        ProducerResponse r = new ProducerResponse();
        r.status = "erro";
        r.erro = erro;
        r.detalhe = detalhe;
        return r;
    }

    /**
     * Diagnostic body for GET {@code /health} / {@code /diag}. {@code status} is {@code healthy} when
     * init succeeded, {@code degraded} otherwise (with {@code init_error} populated). {@code configKeys}
     * are the config KEY NAMES only — never values (no secrets/OCIDs leak through the health endpoint).
     */
    public static ProducerResponse diagnostic(String initError, String version, List<String> configKeys) {
        ProducerResponse r = new ProducerResponse();
        r.status = initError == null ? "healthy" : "degraded";
        r.initError = initError;
        r.version = version;
        r.configKeys = configKeys;
        return r;
    }

    public String getEventId() { return eventId; }
    public String getStatus() { return status; }
    public String getStream() { return stream; }
    public String getTransactionId() { return transactionId; }
    public long getElapsedMs() { return elapsedMs; }
    public Boolean getColdStart() { return coldStart; }
    public String getErro() { return erro; }
    public String getDetalhe() { return detalhe; }
    public String getVersion() { return version; }
    public String getInitError() { return initError; }
    public List<String> getConfigKeys() { return configKeys; }

    public void setElapsedMs(long elapsedMs) { this.elapsedMs = elapsedMs; }
    public void setColdStart(Boolean coldStart) { this.coldStart = coldStart; }
}
