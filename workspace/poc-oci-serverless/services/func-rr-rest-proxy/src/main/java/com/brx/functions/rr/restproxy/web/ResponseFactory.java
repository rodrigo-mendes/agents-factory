package com.brx.functions.rr.restproxy.web;

import com.brx.functions.rr.restproxy.model.StoreResponse;
import com.fnproject.events.output.APIGatewayResponseEvent;
import com.fnproject.fn.api.Headers;

/**
 * Centralized builder for API Gateway responses (same pattern as ApiFacadeFunction). Always sets
 * {@code Content-Type: application/json}.
 */
public class ResponseFactory {

    public APIGatewayResponseEvent<StoreResponse> ok(StoreResponse body) {
        return response(200, body);
    }

    public APIGatewayResponseEvent<StoreResponse> error(int status, StoreResponse body) {
        return response(status, body);
    }

    public APIGatewayResponseEvent<StoreResponse> response(int status, StoreResponse body) {
        return new APIGatewayResponseEvent.Builder<StoreResponse>()
                .statusCode(status)
                .headers(Headers.emptyHeaders()
                        .addHeader("Content-Type", "application/json"))
                .body(body)
                .build();
    }
}
