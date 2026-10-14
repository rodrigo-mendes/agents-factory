package com.brx.functions.rr.restproxy.web;

import java.io.IOException;
import java.net.http.HttpTimeoutException;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.brx.functions.rr.restproxy.model.StoreResponse;
import com.fnproject.events.output.APIGatewayResponseEvent;

/**
 * Maps store-proxy exceptions to structured HTTP error responses. Preserves the full upstream
 * message (status codes, URLs) as the diagnostic {@code detalhe} — never strips it.
 */
public class ErrorMapper {

    private static final Logger log = LoggerFactory.getLogger(ErrorMapper.class);

    private final ResponseFactory responses;

    public ErrorMapper(ResponseFactory responses) {
        this.responses = responses;
    }

    public APIGatewayResponseEvent<StoreResponse> toResponse(Throwable e) {
        if (e instanceof HttpTimeoutException) {
            log.warn("Timeout during store proxy", e);
            return responses.error(504, StoreResponse.error("Gateway Timeout", e.getMessage()));
        }
        if (e instanceof IOException) {
            log.warn("IO error during store proxy", e);
            return fromIoException((IOException) e);
        }
        log.error("Unexpected error during store proxy", e);
        String detail = e.getClass().getName() + ": " + e.getMessage();
        return responses.error(500, StoreResponse.error("Internal server error", detail));
    }

    private APIGatewayResponseEvent<StoreResponse> fromIoException(IOException e) {
        String message = e.getMessage();

        if (message != null && message.contains("OAuth2 token request failed")) {
            return responses.error(503, StoreResponse.error("Service Unavailable", message));
        }

        if (message != null && message.startsWith("Falha na chamada HTTP:")) {
            String statusPart = message.substring("Falha na chamada HTTP:".length()).trim();
            int statusSeparator = statusPart.indexOf(" - ");
            if (statusSeparator > 0) {
                statusPart = statusPart.substring(0, statusSeparator).trim();
            }

            try {
                int downstreamStatus = Integer.parseInt(statusPart);
                if (downstreamStatus >= 400 && downstreamStatus <= 499) {
                    return responses.error(400, StoreResponse.error("Bad Request", message));
                }
                if (downstreamStatus >= 500) {
                    return responses.error(502, StoreResponse.error("Bad Gateway", message));
                }
            } catch (NumberFormatException ignored) {
                // Keep fallback behavior for malformed status format
            }

            return responses.error(502, StoreResponse.error(message, null));
        }

        if (message != null && message.startsWith("BrxServices HTTP error:")) {
            return responses.error(502, StoreResponse.error("Bad Gateway", message));
        }

        return responses.error(500, StoreResponse.error("Internal server error", null));
    }
}
