@change-greet
Feature: greeting
  Greet a visitor by name.

  @R1
  Rule: R1 Greet a known visitor
    The system SHALL greet a visitor by the given name.

    @happy
    Scenario: named visitor
      When the visitor opens the greeting with the name "Ana"
      Then the greeting is "Hello, Ana"
