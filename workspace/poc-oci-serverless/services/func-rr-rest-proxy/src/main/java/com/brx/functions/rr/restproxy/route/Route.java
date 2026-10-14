package com.brx.functions.rr.restproxy.route;

/**
 * API Gateway route classification for the proxy. Resolution mirrors the original inline routing:
 * health/diag first, then any webhook path, otherwise the store create/update flow.
 */
public enum Route {
    HEALTH,
    WEBHOOK,
    STORE;

    public static Route resolve(String path) {
        if ("/health".equals(path) || "/diag".equals(path)) {
            return HEALTH;
        }
        if ("/webhook".equals(path) || "/item/webhook".equals(path)
                || (path != null && path.contains("webhook"))) {
            return WEBHOOK;
        }
        return STORE;
    }

    /** Reduces a full request URL to its last path segment (e.g. {@code /store/create} → {@code /create}). */
    public static String extractRoutePath(String fullPath) {
        if (fullPath == null || fullPath.isEmpty()) {
            return "/";
        }
        int lastSlash = fullPath.lastIndexOf('/');
        if (lastSlash <= 0) {
            return fullPath;
        }
        return fullPath.substring(lastSlash);
    }
}
