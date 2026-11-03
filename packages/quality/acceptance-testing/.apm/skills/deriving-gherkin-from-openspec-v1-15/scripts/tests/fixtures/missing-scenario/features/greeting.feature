@change-greet
Feature: greeting

  @R1
  Rule: R1 Greet a known visitor

    Scenario: named visitor
      When the visitor opens the greeting with the name "Ana"
      Then the greeting is "Hello, Ana"
