@change-greet
Feature: greeting

  @req-greet-a-known-visitor
  Rule: Greet a known visitor

    Scenario: Named   Visitor
      When the visitor opens the greeting with the name "Ana"
      Then the greeting is "Hello, Ana"
