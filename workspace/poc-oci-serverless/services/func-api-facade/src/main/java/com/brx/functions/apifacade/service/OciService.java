package com.brx.functions.apifacade.service;

/**
 * Interface para operações de serviços OCI (Vault + Object Storage).
 * Permite mock em testes unitários sem dependência de SDK classes.
 */
public interface OciService {

    String getSecret(String secretId);

    void putObject(String bucketName, String objectName, String data);
}
