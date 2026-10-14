package com.brx.functions.rr.restproxy.obs;

import java.util.logging.LogManager;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.bridge.SLF4JBridgeHandler;

/**
 * Installs the JUL → SLF4J bridge so {@code java.util.logging} output (FDK, OCI SDK) is routed
 * through Logback and emitted as structured JSON. Called once at class-load time.
 */
public final class LoggingBridge {

    private static final Logger log = LoggerFactory.getLogger(LoggingBridge.class);

    private LoggingBridge() {
    }

    public static void install() {
        try {
            LogManager.getLogManager().reset();
            SLF4JBridgeHandler.removeHandlersForRootLogger();
            SLF4JBridgeHandler.install();
            log.info("JUL-to-SLF4J bridge successfully installed");
        } catch (Exception e) {
            log.error("Failed to install JUL-to-SLF4J bridge: {}", e.getMessage());
        }
    }
}
