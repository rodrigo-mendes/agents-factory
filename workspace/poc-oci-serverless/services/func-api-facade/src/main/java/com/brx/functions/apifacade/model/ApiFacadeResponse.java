package com.brx.functions.apifacade.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public class ApiFacadeResponse {

    @JsonProperty("status_code")
    private int statusCode;

    private String message;

    private Object data;

    @JsonProperty("elapsed_ms")
    private long elapsedMs;

    @JsonProperty("cold_start")
    private boolean coldStart;

    @JsonProperty("api_version")
    private String apiVersion;

    public ApiFacadeResponse() {
    }

    public ApiFacadeResponse(int statusCode, String message, Object data) {
        this.statusCode = statusCode;
        this.message = message;
        this.data = data;
    }

    public static ApiFacadeResponse ok(String message) {
        return new ApiFacadeResponse(200, message, null);
    }

    public static ApiFacadeResponse ok(String message, Object data) {
        return new ApiFacadeResponse(200, message, data);
    }

    public static ApiFacadeResponse error(int statusCode, String message) {
        return new ApiFacadeResponse(statusCode, message, null);
    }

    public int getStatusCode() {
        return statusCode;
    }

    public void setStatusCode(int statusCode) {
        this.statusCode = statusCode;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public Object getData() {
        return data;
    }

    public void setData(Object data) {
        this.data = data;
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
}
