@change-greet
Feature: greeting

  @R1
  Rule: R1 Greet a known visitor

    Scenario: named visitor
      When the visitor opens the greeting with the name "Ana"
      Then the greeting is "Hello, Ana"

  @R9
  Rule: R9 Unknown rule

    Scenario: invented behaviour
      When the visitor does something
      Then something happens

  Rule: Untagged rule

    Scenario: no requirement tag
      When the visitor waits
      Then nothing happens
