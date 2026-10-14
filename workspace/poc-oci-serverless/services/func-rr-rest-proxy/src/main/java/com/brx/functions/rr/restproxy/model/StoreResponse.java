package com.brx.functions.rr.restproxy.model;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class StoreResponse {

    private String status;
    private String operacao;

    @JsonProperty("store_id")
    private String storeId;

    @JsonProperty("elapsed_ms")
    private long elapsedMs;

    @JsonProperty("cold_start")
    private boolean coldStart;

    @JsonProperty("api_version")
    private String apiVersion;

    private String erro;
    private String detalhe;

    // Webhook fields (Items Integration)
    @JsonProperty("total_processed")
    private Integer totalProcessed;

    @JsonProperty("success_count")
    private Integer successCount;

    @JsonProperty("failure_count")
    private Integer failureCount;

    private String message;
    private List<String> errors;

    public StoreResponse() {
    }

    public static StoreResponse success(String operacao, String storeId, long elapsedMs) {
        StoreResponse response = new StoreResponse();
        response.status = "sucesso";
        response.operacao = operacao;
        response.storeId = storeId;
        response.elapsedMs = elapsedMs;
        return response;
    }

    public static StoreResponse error(String erro, String detalhe) {
        StoreResponse response = new StoreResponse();
        response.status = "erro";
        response.erro = erro;
        response.detalhe = detalhe;
        return response;
    }

    public static StoreResponse webhookSuccess(int total, int success, long elapsedMs) {
        StoreResponse response = new StoreResponse();
        response.status = "sucesso";
        response.operacao = "webhook-items";
        response.totalProcessed = total;
        response.successCount = success;
        response.failureCount = total - success;
        response.elapsedMs = elapsedMs;
        response.message = "Processamento do webhook concluído";
        return response;
    }

    public static StoreResponse webhookError(String erro, String detalhe, List<String> errors) {
        StoreResponse response = new StoreResponse();
        response.status = "erro";
        response.erro = erro;
        response.detalhe = detalhe;
        response.message = erro;
        response.errors = errors;
        return response;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getOperacao() {
        return operacao;
    }

    public void setOperacao(String operacao) {
        this.operacao = operacao;
    }

    public String getStoreId() {
        return storeId;
    }

    public void setStoreId(String storeId) {
        this.storeId = storeId;
    }

    public long getElapsedMs() {
        return elapsedMs;
    }

    public void setElapsedMs(long elapsedMs) {
        this.elapsedMs = elapsedMs;
    }

    public boolean isColdStart() {
        return coldStart;
    }

    public void setColdStart(boolean coldStart) {
        this.coldStart = coldStart;
    }

    public String getApiVersion() {
        return apiVersion;
    }

    public void setApiVersion(String apiVersion) {
        this.apiVersion = apiVersion;
    }

    public String getErro() {
        return erro;
    }

    public void setErro(String erro) {
        this.erro = erro;
    }

    public String getDetalhe() {
        return detalhe;
    }

    public void setDetalhe(String detalhe) {
        this.detalhe = detalhe;
    }

    public Integer getTotalProcessed() {
        return totalProcessed;
    }

    public void setTotalProcessed(Integer totalProcessed) {
        this.totalProcessed = totalProcessed;
    }

    public Integer getSuccessCount() {
        return successCount;
    }

    public void setSuccessCount(Integer successCount) {
        this.successCount = successCount;
    }

    public Integer getFailureCount() {
        return failureCount;
    }

    public void setFailureCount(Integer failureCount) {
        this.failureCount = failureCount;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public List<String> getErrors() {
        return errors;
    }

    public void setErrors(List<String> errors) {
        this.errors = errors;
    }
}
