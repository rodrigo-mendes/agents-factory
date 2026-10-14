package com.brx.functions.rr.restproxy.obs;

import java.util.Map;
import java.util.concurrent.Callable;

import com.brx.functions.rr.restproxy.ObservabilityHelper;

import io.opentelemetry.api.trace.Span;

/**
 * Wraps a downstream call in a CLIENT child span, collapsing the repeated
 * start-span / try / end-span(null) / catch / end-span(error) / rethrow boilerplate into one place.
 * The original exception is always rethrown unchanged so callers can classify it by type.
 */
public final class TracedCall {

    private TracedCall() {
    }

    public static <T> T run(String spanName, String peerService, Callable<T> call) throws Exception {
        return run(spanName, peerService, Map.of(), call);
    }

    public static <T> T run(String spanName, String peerService,
                            Map<String, String> attributes, Callable<T> call) throws Exception {
        Span span = ObservabilityHelper.startChildSpan(spanName);
        span.setAttribute("peer.service", peerService);
        attributes.forEach(span::setAttribute);
        try {
            T result = call.call();
            ObservabilityHelper.endSpan(span, (Throwable) null);
            return result;
        } catch (Exception e) {
            ObservabilityHelper.endSpan(span, e);
            throw e;
        }
    }
}
