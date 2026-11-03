@change-add-x
Feature: greeting

  @R2
  Rule: R2 Greet in uppercase on request
    The system SHALL return the greeting in uppercase when the visitor asks for it.

    @happy
    Scenario: uppercase requested
      When the visitor opens the greeting with the name "Ana" and asks for uppercase
      Then the greeting is "HELLO, ANA"
      And the status is 200
