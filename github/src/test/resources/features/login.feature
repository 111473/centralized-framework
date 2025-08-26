@selenium
Feature: Loan Account Login

  Scenario: Successful login
    Given user is on login page
    When user logs in with username "neilherbertagtuca@gmail.com" and password "F1R3F0x@73"
    Then user should be redirected to the dashboard
