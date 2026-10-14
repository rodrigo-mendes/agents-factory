---
Full_Name: AWS SDK for Java 2.x - Amazon SES (SESv2)
Target_Version: 2.45.1
Release_Date: 2026-05-29
Support_Status: Active
Primary_Docs: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/home.html
Official_Repo: https://github.com/aws/aws-sdk-java-v2
Research_Date: 2026-06-02
Domain_Complexity: Standard
Research_Scope: Standard
---

# Executive Summary

This research establishes absolute, version-locked development standards and design guardrails for integrating Amazon Simple Email Service (SES) with Java-based enterprise architectures using the AWS SDK for Java v2 (version 2.45.1). Email communication is a business-critical event vector that directly exposes an organization to security vulnerabilities, reputation degradation, and delivery failures. By standardizing on AWS SDK version 2.45.1, development teams prevent library drift and maximize integration safety.

Central to Java 2.45.1 is the strategic split between the traditional AWS SES client and the modern `SesV2Client` program interfaces. While the legacy `SesClient` interface (built on `software.amazon.awssdk.services.ses`) provides an SDK v2 wrapper for the SES API v1 backend, the modern `SesV2Client` interface (built on `software.amazon.awssdk.services.sesv2`) provides full native support for modern SES v2 workflows. These modern features include contact list administration, custom verification email templates, advanced account-level and configuration-set-level suppression lists, Virtual Deliverability Manager (VDM) configurations, and the upgraded 40 MB envelope limit for raw MIME transfers. Therefore, this document mandates the use of `SesV2Client` as the operational baseline.

Domain complexity is classified as **Standard** because email integration spans multiple adjacent technical concerns: connection pool scaling (Apache HTTP for sync, Netty for async), security validation (SPF/DKIM/DMARC alignment), reputation enforcement (bounces, complaints, configuration sets), and document processing (constructing multi-part MIME messages using Jakarta Mail for attachments). This research synthesizes official AWS developer guides, release benchmarks, and operational standards into unambiguous, executable instructions to accelerate downstream skill creation.

# Input Validation

- **SYSTEM_OR_TECH_NAME**: AWS Java SDK SESv2 (specific, valid)
- **TARGET_VERSION**: 2.45.1 (specific, valid)
- **OFFICIAL_URL_IF_KNOWN**: https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/home.html
- **INTEGRATION_PARTNERS_LIST**: Jakarta Mail 2.1 (for multipart MIME generation), AWS KMS (for raw payload envelope encryption), IAM/STS (for secure identity assumption), JUnit 5/Mockito (for unit testing), Amazon SNS/SQS (for bounce/complaint webhook processing)

# Authority and Versioning

- **Primary authority**: AWS SDK for Java 2.x Developer Guide and Amazon SES API Service Reference (v2).
- **Version lock**: All implementation guidelines, dependencies, and imports within this research document are built exclusively for AWS SDK for Java 2.45.1.
- **Release pin**: aws-sdk-java-v2 release 2.45.1 dated 2026-05-29.
- **Version absolutism warning**: Do not combine legacy AWS SDK for Java 1.x (`com.amazonaws.services.simpleemail`) and 2.x (`software.amazon.awssdk.services.sesv2` or `software.amazon.awssdk.services.ses`) client classes. Mixing versions leads to classpath conflicts, compilation errors, dependency drift, and unpredictable runtime execution.

# Architectural Guardrails

### ✅ Mandatory Patterns

Pattern: Pin AWS SDK BOM and SESv2 modules to 2.45.1
- **Why**: Guarantees dependency alignment across all transitively loaded AWS services, preventing unexpected API regressions or binary mismatches.
- **Code**:
```xml
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>software.amazon.awssdk</groupId>
      <artifactId>bom</artifactId>
      <version>2.45.1</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>

<dependencies>
  <!-- Modern SES v2 Service Module -->
  <dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>sesv2</artifactId>
  </dependency>
  <!-- Security token module for assumption of roles -->
  <dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>sts</artifactId>
  </dependency>
</dependencies>
```
- **Source**: AWS SDK for Java 2.x Dependency Management Guide (Release 2.45.1).

Pattern: Prioritize SesV2Client over legacy SesClient
- **Why**: `SesV2Client` interacts with the highly optimized SES API v2, supporting essential modern routing features like custom MAIL FROM configurations, subscription management, VDM, and larger 40MB message limits.
- **Code**:
```java
import software.amazon.awssdk.services.sesv2.SesV2Client;

// Standardize throughout the application context
SesV2Client client = SesV2Client.builder()
    .region(Region.US_EAST_1)
    .credentialsProvider(DefaultCredentialsProvider.create())
    .build();
```
- **Source**: Amazon SES API v2 Developer Reference, AWS Java SDK 2.x Changelog.

Pattern: Set explicit Region and use DefaultCredentialsProvider
- **Why**: Enforces safe AWS identity resolution (IAM policies, instance profiles, or container task roles) without risk of credentials leaking. Eliminates ambient region resolution overhead.
- **Code**:
```java
SesV2Client sesV2Client = SesV2Client.builder()
    .region(Region.US_EAST_1)
    .credentialsProvider(DefaultCredentialsProvider.create())
    .build();
```
- **Source**: AWS Identity and Access Management (IAM) Best Practices.

Pattern: Treat clients as long-lived, thread-safe singletons with clean shutdown pools
- **Why**: Client instantiation initializes expensive internal HTTP connection pools (Apache for synchronous `SesV2Client`, Netty for asynchronous `SesV2AsyncClient`). Continuously recreating clients leaks TCP sockets and causes heavy handshakes.
- **Code**:
```java
public final class SesClientManager implements AutoCloseable {
  private static final SesV2Client INSTANCE = SesV2Client.builder()
      .region(Region.US_EAST_1)
      .credentialsProvider(DefaultCredentialsProvider.create())
      .build();

  public static SesV2Client getClient() {
    return INSTANCE;
  }

  @Override
  public void close() {
    INSTANCE.close();
    logger.info("SESv2 Client successfully shutdown.");
  }
}
```
- **Source**: AWS Client Reuse Optimization guidelines.

Pattern: Mandate Configuration Sets on all SendEmailRequests
- **Why**: Configuration Sets are the absolute foundation of SES observability. They bind email transactions to event destinations (like SNS or CloudWatch) for real-time tracking of sends, deliveries, bounces, and complaints. Without them, reputation changes are invisible.
- **Code**:
```java
SendEmailRequest request = SendEmailRequest.builder()
    .fromEmailAddress("noreply@company.com")
    .configurationSetName("Transactional-Config-Set") // MANDATORY for tracking
    .destination(Destination.builder().toAddresses("recipient@client.com").build())
    .content(EmailContent.builder()
        .simple(Message.builder()
            .subject(Content.builder().data("Account Registered").build())
            .body(Body.builder().html(Content.builder().data("<p>Welcome!</p>").build()).build())
            .build())
        .build())
    .build();
```
- **Source**: Amazon SES Configuration Sets Developer Guide.

Pattern: Build Raw Emails with Attachments using Jakarta Mail 2.1 via SdkBytes
- **Why**: Standard `SendEmailRequest` simple bodies do not support attachments. Complex multi-part attachments require compiling a MIME message, converting it to an array of bytes, and wrapping it in `SdkBytes` for a `RawMessage` block.
- **Code**:
```java
// Compile MIME message using Jakarta Mail
Session session = Session.getInstance(new Properties());
MimeMessage mimeMessage = new MimeMessage(session);
mimeMessage.setSubject("Your Monthly Invoice", "UTF-8");
mimeMessage.setFrom(new InternetAddress("billing@company.com"));
mimeMessage.setRecipients(jakarta.mail.Message.RecipientType.TO, InternetAddress.parse("client@customer.com"));

MimeMultipart multipart = new MimeMultipart("mixed");

// Add text/html body section
MimeBodyPart bodyPart = new MimeBodyPart();
bodyPart.setContent("<p>Please find details attached.</p>", "text/html; charset=utf-8");
multipart.addBodyPart(bodyPart);

// Add PDF file attachment segment
MimeBodyPart attachmentPart = new MimeBodyPart();
attachmentPart.setDataHandler(new DataHandler(new ByteArrayDataSource(pdfBytes, "application/pdf")));
attachmentPart.setFileName("invoice_1102.pdf");
multipart.addBodyPart(attachmentPart);

mimeMessage.setContent(multipart);

// Convert MIME message to output stream bytes and pass to SdkBytes
ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
mimeMessage.writeTo(outputStream);
SdkBytes rawBytes = SdkBytes.fromByteArray(outputStream.toByteArray());

RawMessage rawMessage = RawMessage.builder()
    .data(rawBytes)
    .build();

SendEmailRequest request = SendEmailRequest.builder()
    .fromEmailAddress("billing@company.com")
    .content(EmailContent.builder().raw(rawMessage).build())
    .configurationSetName("Transactional-Config-Set")
    .build();
```
- **Source**: Jakarta Mail Specification v2.1, Amazon SES Raw Message Transmission.

---

### ⚠️ Conditional Patterns

Decision: Synchronous SesV2Client vs Asynchronous SesV2AsyncClient
- **Options**: Synchronous `SesV2Client` (uses Apache HTTP client), Asynchronous `SesV2AsyncClient` (uses Netty non-blocking HTTP client).
- **Tradeoffs**:

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **SesV2Client** | Straightforward execution flow, ease of localized JUnit mocking, simplified thread tracking | Max throughput concurrency on high-load single-process runners | Service workers processing specific worker queues, cron jobs, classic Spring Boot synchronous controllers |
| **SesV2AsyncClient** | High-velocity scale, microservice event-loop integrations, minimal system thread overhead | Exception-trace traceability, sequential thread control, test orchestration complexity | Reactive servers (WebFlux, Quarkus), event-driven microservices processing high-velocity triggers |

- **Agent ask-first prompt**: "Which client execution architecture matches your software context? A synchronous SesV2Client running over Apache HTTP, or an asynchronous SesV2AsyncClient backed by Netty?"
- **Source**: AWS SDK for Java 2.x asynchronous processing reference.

Decision: Simple Content vs Templated Content vs Raw MIME Payload Sourcing
- **Options**:
  1. *Simple payload*: Define raw string / HTML blocks inline.
  2. *Templated payload*: Fetch templates from AWS and pass JSON data variables.
  3. *Raw MIME payload*: Assemble a custom MIME structure (used for attachments).
- **Tradeoffs**:

| Sourcing Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| **Simple** | Rapid deployment, plain transactional notices, basic HTML builders | Email marketing consistency, dynamic structural adjustments | System-level alerts, one-off password recovery links |
| **Templated** | Centralized template store on AWS, offloading design from code, localized variable parsing | Complex programmatic conditional structures in HTML, localized runtime template storage options | Cross-platform marketing campaigns, standard onboarding receipt formats |
| **Raw MIME** | Comprehensive MIME flexibility, multi-part document attachments, custom mail headers | Simplicity of code, higher raw memory consumption and processing times | Invoices with attached PDF files, calendar invitations, encrypted payloads |

- **Agent ask-first prompt**: "Which payload structure is required for your emails? Simple HTML bodies, AWS-hosted email templates, or raw MIME structures (necessary for files/attachments)?"
- **Source**: Amazon SES API sendEmail content schema.

---

### 🚫 Forbidden Patterns

Anti-Pattern: Hardcoding AWS API Access Keys in Sources
```java
// 🚫 WRONG - DO NOT DO THIS
SesV2Client client = SesV2Client.builder()
    .credentialsProvider(StaticCredentialsProvider.create(
        AwsBasicCredentials.create("AKIAIOSFODNN7EXAMPLE", "secretKey123")))
    .build();
```
- **Why**: Pushing credentials to source control is a highly severe security risk, leading to account takeover and unauthorized billing.
- **Instead**: Rely on AWS `DefaultCredentialsProvider.create()` to resolve permissions from environment variables, configuration files, or ECS/EKS task roles.
- **Impact**: Instantly compromises AWS safety boundaries, triggering immediate security credential rotation requirements and compliance failures.
- **Source**: AWS Identity and Access Management Security Best Practices.

Anti-Pattern: Executing Linear, Unthrottled Loops to Send Bulk Emails
```java
// 🚫 WRONG - DO NOT DO THIS
for (User user : list) {
  client.sendEmail(SendEmailRequest.builder()
      .fromEmailAddress("sales@company.com")
      .destination(Destination.builder().toAddresses(user.email()).build())
      .content(content)
      .build()); // Blocking, unthrottled loop
}
```
- **Why**: Amazon SES accounts have hard limits on the maximum sending rate (e.g., 14 emails per second). Rapidly pushing individual synchronous requests in an unthrottled loop will trigger API ThrottlingExceptions, dropping emails.
- **Instead**: Implement an explicit rate-limit mechanism (e.g., Token Bucket) or route sending events through a queue (like Amazon SQS or AWS Step Functions) that matches your SES account's maximum sending rate. Or use `sendBulkEmail` API.
- **Impact**: Thread pool exhaustion, immediate rate-limiting errors (`TooManyRequestsException`), and lost transaction deliveries.
- **Source**: Amazon SES Throttling and Sending Limits.

Anti-Pattern: Swallowing Throttling and Connection System Exceptions
```java
// 🚫 WRONG - DO NOT DO THIS
try {
  sesClient.sendEmail(request);
} catch (Exception e) {
  logger.error("Error occurred"); // Swallowing the exception, returning pseudo-200.
}
```
- **Why**: Swallowing exception classes like `LimitExceededException` or `SesV2Exception` prevents retry mechanics from firing, hiding transmission failures and leading to critical user data loss (e.g., lost MFA pins).
- **Instead**: Catch specific checked/unchecked AWS service exception bounds and trigger backoff retries, alerting mechanisms, or dead-letter queues (DLQ).
- **Impact**: Broken transaction processing cycles, untraceable data dropouts, and silent service degradation.
- **Source**: AWS SDK for Java Exception Handling best practices.

Anti-Pattern: Initiating Individual-Address Verification in Live Run Loops
```java
// 🚫 WRONG - DO NOT DO THIS
// Calling sesClient.createEmailIdentity(...) prior to every customer sendEmail call
```
- **Why**: Dynamic email identity verification is heavily rate-limited and intended exclusively for administrative tasks. In production, emails are sent from pre-verified root or sub-domains.
- **Instead**: Run identity and Easy DKIM configurations once via Infrastructure as Code (Terraform) on domains, enabling the Java runtime to immediately send emails without run-time domain checks.
- **Impact**: High operational latency, code bloat, and application thread lock due to API resource limit exhaustion.
- **Source**: Amazon SES Identity Verification guidelines.

Anti-Pattern: Pushing Raw Payloads exceeding 40 MB Envelope Limits
```java
// 🚫 WRONG - DO NOT DO THIS
// Compiling a RawMessage MIME block with a 50MB video file attachment
```
- **Why**: Amazon SES enforces a hard limit of 40 MB per raw MIME email message, including all base64-encoded attachment overheads. Trying to transmit heavier payloads will instantly fail.
- **Instead**: Restrict file sizes on upload, compress attachment bytes (ZIP format), or store large documents in Amazon S3 and include a secured presigned URL link inside the email body.
- **Impact**: Immediate client-side or service-side `MessageRejectedException` failures, memory spikes, and high heap contention.
- **Source**: Amazon Simple Email Service Service Quotas Reference.

---

# Migration Guide

## Breaking Changes (v1 to v2 SES Changes)

1. **Namespace Refactoring**: All Java imports must migrate from `com.amazonaws.services.simpleemail.*` to the modularized standard of `software.amazon.awssdk.services.sesv2.*`.
2. **Immutable POJO structures**: Builders replace open setters. For instance, `new SendEmailRequest()` now requires `SendEmailRequest.builder().build()`.
3. **Streamlined Model Parameter Methods**: Getter/Setter Hungarian style prefixes (e.g. `getMessageId()`) are simplified to modern field-matching getters (e.g. `messageId()`).
4. **Sending Payload Refactoring**: The client's payload mapping structure is changed:
   - In v1, email subject/body was passed via top-level `Message` parameters.
   - In v2, all formats (Simple, Templated, and Raw) are normalized under the unified `EmailContent` model.
5. **Exception Tree Isolation**: System exceptions are renamed from `AmazonSimpleEmailServiceException` (v1) to `SesV2Exception` (v2).

## Upgrade Steps

1. Configure the project's build settings (Maven `pom.xml` / Gradle `build.gradle`) to import the `2.45.1` AWS SDK BOM, replacing `com.amazonaws:aws-java-sdk-ses` with modern `software.amazon.awssdk:sesv2`.
2. Find and refactor import blocks in Java files:
   - Replace any `com.amazonaws.services.simpleemail` with `software.amazon.awssdk.services.sesv2`.
3. Refactor client declaration routines from `AmazonSimpleEmailClientBuilder.standard()` to `SesV2Client.builder()`. Remove all hardcoded AWS secret keys.
4. Convert request blocks (`SendEmailRequest`) to include the modularized `EmailContent` builder pattern.
5. Setup a `ConfigurationSetName` attribute on every send request to preserve metrics-tracking pipelines.
6. Verify local test cases using Mockito structure changes.

## Compatibility Matrix

| Dependency | Minimum Version | Verified Stable | Actionable Pin |
|------------|-----------------|-----------------|----------------|
| **Java JRE/JDK** | 8 | 17 / 21 LTS | Exact compile-target matching |
| **AWS SDK v2 BOM** | 2.45.1 | 2.45.1 | `software.amazon.awssdk:bom` |
| **SESv2 Module** | 2.45.1 | 2.45.1 | `software.amazon.awssdk:sesv2` |
| **STS Module** | 2.45.1 | 2.45.1 | `software.amazon.awssdk:sts` |
| **Jakarta Mail API** | 2.1.0 | 2.1.3 | `jakarta.mail:jakarta.mail-api` |

---

# Implementation Blueprint

The following helper class, `SesEmailService`, is a production-ready, thread-safe gateway that encapsulates a long-lived synchronous `SesV2Client` (locked to version 2.45.1). It implements `AutoCloseable` to ensure clean shutdown of connection pools, handles simple HTML sending, templated sending, and raw sending with attachments using Jakarta Mail, and includes robust retries with backoff.

```java
package com.example.ses;

import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.core.SdkBytes;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.sesv2.SesV2Client;
import software.amazon.awssdk.services.sesv2.model.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import jakarta.mail.Message;
import jakarta.mail.Session;
import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeBodyPart;
import jakarta.mail.internet.MimeMessage;
import jakarta.mail.internet.MimeMultipart;
import jakarta.mail.util.ByteArrayDataSource;
import jakarta.activation.DataHandler;

import java.io.ByteArrayOutputStream;
import java.util.Objects;
import java.util.Properties;

/**
 * Thread-safe client manager exposing helper routines for Amazon SESv2 API interaction.
 */
public final class SesEmailService implements AutoCloseable {
  private static final Logger logger = LoggerFactory.getLogger(SesEmailService.class);
  private static final int MAX_RETRIES = 3;

  private final SesV2Client sesV2Client;
  private final String defaultConfigurationSet;

  /**
   * Constructs the service with a dedicated AWS region and default configuration set.
   *
   * @param region AWS Region.
   * @param defaultConfigurationSet Optional Configuration Set name to apply.
   */
  public SesEmailService(Region region, String defaultConfigurationSet) {
    Objects.requireNonNull(region, "Region selection cannot be null.");
    this.sesV2Client = SesV2Client.builder()
        .region(region)
        .credentialsProvider(DefaultCredentialsProvider.create())
        .build();
    this.defaultConfigurationSet = defaultConfigurationSet;
    logger.info("SesEmailService successfully initialized in region: {}", region.id());
  }

  /**
   * Helper routine to send a standard HTML email.
   *
   * @param from Sender email address.
   * @param to Recipient email address.
   * @param subject Subject line.
   * @param htmlBody Content body in HTML format.
   * @return String containing AWS-generated Message ID.
   */
  public String sendSimpleEmail(String from, String to, String subject, String htmlBody) {
    Objects.requireNonNull(from, "Sender details cannot be null.");
    Objects.requireNonNull(to, "Recipient details cannot be null.");
    Objects.requireNonNull(subject, "Subject line cannot be null.");
    Objects.requireNonNull(htmlBody, "HTML content body cannot be null.");

    SendEmailRequest request = SendEmailRequest.builder()
        .fromEmailAddress(from)
        .destination(Destination.builder().toAddresses(to).build())
        .configurationSetName(defaultConfigurationSet)
        .content(EmailContent.builder()
            .simple(software.amazon.awssdk.services.sesv2.model.Message.builder()
                .subject(Content.builder().data(subject).charset("UTF-8").build())
                .body(Body.builder()
                    .html(Content.builder().data(htmlBody).charset("UTF-8").build())
                    .build())
                .build())
            .build())
        .build();

    return executeSendWithRetries(request);
  }

  /**
   * Helper routine to send a templated email.
   *
   * @param from Sender email address.
   * @param to Recipient email address.
   * @param templateName Identifier of pre-stored SES email template.
   * @param templateData JSON string representing dynamic template context values.
   * @return String containing AWS-generated Message ID.
   */
  public String sendTemplatedEmail(String from, String to, String templateName, String templateData) {
    Objects.requireNonNull(from, "Sender details cannot be null.");
    Objects.requireNonNull(to, "Recipient details cannot be null.");
    Objects.requireNonNull(templateName, "Template name cannot be null.");
    Objects.requireNonNull(templateData, "Template data JSON cannot be null.");

    Template template = Template.builder()
        .templateName(templateName)
        .templateData(templateData)
        .build();

    SendEmailRequest request = SendEmailRequest.builder()
        .fromEmailAddress(from)
        .destination(Destination.builder().toAddresses(to).build())
        .configurationSetName(defaultConfigurationSet)
        .content(EmailContent.builder().template(template).build())
        .build();

    return executeSendWithRetries(request);
  }

  /**
   * Helper routine to compile and send a raw MIME message with a file attachment.
   *
   * @param from Sender email address.
   * @param to Recipient email address.
   * @param subject Subject line.
   * @param textBody Plain body content.
   * @param fileBytes Binary array of the attachment.
   * @param fileName Name of the file visible in mail.
   * @param fileMimeType Mimetype classification of attachment (e.g. "application/pdf").
   * @return String containing AWS-generated Message ID.
   */
  public String sendEmailWithAttachment(String from, String to, String subject, String textBody,
                                        byte[] fileBytes, String fileName, String fileMimeType) {
    Objects.requireNonNull(from, "Sender details cannot be null.");
    Objects.requireNonNull(to, "Recipient details cannot be null.");
    Objects.requireNonNull(subject, "Subject line cannot be null.");
    Objects.requireNonNull(fileBytes, "Attachment byte array cannot be null.");
    Objects.requireNonNull(fileName, "Filename cannot be null.");
    Objects.requireNonNull(fileMimeType, "Mimetype classification cannot be null.");

    try {
      Session session = Session.getInstance(new Properties());
      MimeMessage mimeMessage = new MimeMessage(session);
      mimeMessage.setSubject(subject, "UTF-8");
      mimeMessage.setFrom(new InternetAddress(from));
      mimeMessage.setRecipients(Message.RecipientType.TO, InternetAddress.parse(to));

      MimeMultipart multipart = new MimeMultipart("mixed");

      // Set readable text message part
      MimeBodyPart textPart = new MimeBodyPart();
      textPart.setText(textBody != null ? textBody : "", "UTF-8");
      multipart.addBodyPart(textPart);

      // Set attachment file part
      MimeBodyPart attachmentPart = new MimeBodyPart();
      attachmentPart.setDataHandler(new DataHandler(new ByteArrayDataSource(fileBytes, fileMimeType)));
      attachmentPart.setFileName(fileName);
      multipart.addBodyPart(attachmentPart);

      mimeMessage.setContent(multipart);

      ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
      mimeMessage.writeTo(outputStream);
      SdkBytes rawBytes = SdkBytes.fromByteArray(outputStream.toByteArray());

      RawMessage rawMessage = RawMessage.builder()
          .data(rawBytes)
          .build();

      SendEmailRequest request = SendEmailRequest.builder()
          .fromEmailAddress(from)
          .configurationSetName(defaultConfigurationSet)
          .content(EmailContent.builder().raw(rawMessage).build())
          .build();

      return executeSendWithRetries(request);
    } catch (Exception e) {
      logger.error("Failed to construct raw MIME email with attachment", e);
      throw new RuntimeException("MIME compilation failed", e);
    }
  }

  /**
   * Executes the send call with jittered exponential backoff.
   */
  private String executeSendWithRetries(SendEmailRequest request) {
    int attempts = 0;
    while (true) {
      try {
        attempts++;
        SendEmailResponse response = sesV2Client.sendEmail(request);
        logger.debug("Email successfully transmitted. Returned ID: {}", response.messageId());
        return response.messageId();
      } catch (TooManyRequestsException | LimitExceededException e) {
        if (attempts >= MAX_RETRIES) {
          logger.error("Retry exhaustion: failed sending email due to SES throttling limits.", e);
          throw e;
        }
        long backoffMs = (long) Math.pow(2, attempts) * 100 + (long) (Math.random() * 50);
        logger.warn("SES rate limit hit. Backing off for {} ms and retrying (Attempt {} of {})...",
            backoffMs, attempts, MAX_RETRIES);
        try {
          Thread.sleep(backoffMs);
        } catch (InterruptedException ie) {
          Thread.currentThread().interrupt();
          throw new RuntimeException("Thread interrupted during email sending throttle backoff", ie);
        }
      } catch (SesV2Exception e) {
        logger.error("AWS SESv2 Service Exception encountered during sending pipeline", e);
        throw e;
      }
    }
  }

  @Override
  public void close() {
    if (sesV2Client != null) {
      sesV2Client.close();
      logger.info("Internal SesV2Client connection resource closed down gracefully.");
    }
  }
}
```

---

# Quality Control

## Self-Validation & Verification Commands

Developers can run regional configuration checks using the AWS CLI and compile tests using Maven.

```bash
# 1. Inspect regional SES account sending statistics and verification state
aws sesv2 get-account --region us-east-1

# 2. Check configuration state of a critical sending domain
aws sesv2 get-email-identity --email-identity mycompany.com --region us-east-1

# 3. List all registered Configuration Sets in the active region
aws sesv2 list-configuration-sets --region us-east-1

# 4. Trigger localized compilation verify suite on maven setup
mvn clean test-compile
```

## Unit Testing and Mocking Blueprint

Testing must rely upon isolated, Mockito-driven framework patterns. Since the client request calls are immutable, use an `ArgumentCaptor` to inspect request parameters and guarantee correctness without needing a live connection to AWS.

```java
package com.example.ses;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.mockito.Mockito;
import software.amazon.awssdk.services.sesv2.SesV2Client;
import software.amazon.awssdk.services.sesv2.model.SendEmailRequest;
import software.amazon.awssdk.services.sesv2.model.SendEmailResponse;

import java.lang.reflect.Field;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class SesEmailServiceTest {

  private SesV2Client mockClient;
  private SesEmailService sesEmailService;
  private static final String CONFIG_SET = "Transactional-Config";

  @BeforeEach
  void setUp() throws Exception {
    mockClient = mock(SesV2Client.class);
    sesEmailService = new SesEmailService(software.amazon.awssdk.regions.Region.US_EAST_1, CONFIG_SET);

    // Swap the internal client field with the mock client using reflection for testing
    Field clientField = SesEmailService.class.getDeclaredField("sesV2Client");
    clientField.setAccessible(true);
    clientField.set(sesEmailService, mockClient);
  }

  @Test
  void testSendSimpleEmail_Success() {
    // Arrange Mock
    SendEmailResponse expectedResponse = SendEmailResponse.builder()
        .messageId("msg-uuid-9923812")
        .build();
    when(mockClient.sendEmail(any(SendEmailRequest.class))).thenReturn(expectedResponse);

    // Act
    String messageId = sesEmailService.sendSimpleEmail(
        "sender@test.com", "recipient@test.com", "Hello Subject", "<h1>Body</h1>"
    );

    // Assert Output
    assertEquals("msg-uuid-9923812", messageId);

    // Verify Builder Request Arguments
    ArgumentCaptor<SendEmailRequest> captor = ArgumentCaptor.forClass(SendEmailRequest.class);
    verify(mockClient, times(1)).sendEmail(captor.capture());

    SendEmailRequest capturedReq = captor.getValue();
    assertEquals("sender@test.com", capturedReq.fromEmailAddress());
    assertEquals(CONFIG_SET, capturedReq.configurationSetName());
    assertEquals("recipient@test.com", capturedReq.destination().toAddresses().get(0));
    assertEquals("Hello Subject", capturedReq.content().simple().subject().data());
  }
}
```

---

# Production Readiness

## Operational Checklists & SLA Boundaries

1. **Daily Sending Quota & Throttle Management**:
   - Every SES account has a daily quota (emails per 24 hours) and a send rate limit (emails per second).
   - If rate limits are exceeded, SES throws `LimitExceededException` or `TooManyRequestsException`.
   - Production systems must implement rate limiting on the client side (e.g., using SQS/SES architecture or bucket-rate algorithms) to stay within account limits and smoothly handle spikes.
2. **Reputation Monitoring Alarm thresholds**:
   - Maintain a bounce rate below **5%** (SES warning threshold is 5%, and a bounce rate >= 10% can lead to account suspension).
   - Maintain a complaint rate below **0.1%** (complaints >= 0.5% will likely pause sending capabilities immediately).
   - Connect SES configuration sets to an SNS topic that triggers real-time CRM updates, immediately removing or flags invalid bouncing addresses.
3. **DKIM and DMARC Infrastructure Alignments**:
   - Set up custom MAIL FROM domains to ensure SPF alignments pass.
   - Deploy Easy DKIM with mandatory **2048-bit** keys (the 2024 security baseline).
   - Configure DMARC DNS policies (`_dmarc.yourdomain.com`) in sequential phases: `p=none` (monitoring), `p=quarantine` (soft enforcement), and finally `p=reject` (full secure block).
4. **Transport Layer Security Requirements**:
   - Enforce TLS (RequireTls options inside configuration sets settings) to ensure all messages are fully encrypted in transit to the receiving mail server.
5. **Payload Size Restrictions**:
   - Validate attachment size on files before processing MIME arrays into JVM heap. Keep raw messages safely below the **40 MB** API limit.

---

# Source Bibliography

- **AWS SDK for Java 2.x API Reference**: [Amazon SESv2 API](https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/sesv2/package-summary.html) (Published: 2026-05-29).
- **AWS SDK for Java Developer Guide**: [Configuring Credential Sourcing](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/credentials.html) (Published: 2026-04-12).
- **Amazon SESv2 Service Reference Checklist**: [Controlling Outbound Throttling](https://docs.aws.amazon.com/ses/latest/dg/control-sending-volume.html) (Published: 2026-05-18).
- **Google / Yahoo Bulk Email Sender Standards**: [DKIM/DMARC Multi-domain Alignment Rules](https://support.google.com/a/answer/81126) (Published: 2024-02-15).

---

# Agent Operation Notes

### High Confidence (Process Automatically)
- Standard HTML transmission pipelines.
- Direct integration mapping with Jakarta Mail 2.1 via byte processing arrays.
- Swapping SDK clients with long-lived singletons utilizing default regional environments.
- Enforcing Configuration Sets across simple and custom raw payloads.

### Medium Confidence (Verify architecture with User)
- Moving from legacy `SesClient` setups (SDK v1 wrappers) to modern `SesV2Client` structures in larger pre-existing codebases.
- Dynamic variable parsing structures for HTML templates vs rendering template engine on client app nodes.

### Low Confidence (Must query User)
- Implementing massive bulk email workflows that require complex distributed schedulers or custom multi-node throttle brokers.
- Managing inbound processing flows (Mail Manager integration) with custom MX gateways, email archival routines, or third-party add-ons.
