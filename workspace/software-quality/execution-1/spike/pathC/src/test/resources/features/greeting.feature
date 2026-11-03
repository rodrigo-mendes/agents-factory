@change-add-greeting
Feature: Greeting

  Rule: R1 The system SHALL greet a named visitor

    @R1 @happy
    Scenario: Valid name
      When the visitor asks for a greeting for "ana"
      Then the response status is 200
      And the response body is "hello dr. ana"

    @R1 @negative
    Scenario: Name too long
      When the visitor asks for a greeting for "abcdefghijklmnopqrstuvwxyz"
      Then the response status is 400
