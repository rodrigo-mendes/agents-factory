package com.brx.functions.apifacade;

import com.brx.functions.apifacade.service.OciService;

/**
 * Shared mock holder for FnTestingRule classloader isolation.
 * The function detects this class via Class.forName during @FnConfiguration.
 */
public class MockOciServiceHolder {

    public static OciService ociService;
}
