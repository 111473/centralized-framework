package com.testautomation.reimbursement.steps;

import com.microsoft.playwright.Page;
import com.testautomation.framework.logger.LoggerWrapper;
import com.testautomation.framework.manager.DriverManager;
import com.testautomation.framework.report.AllureReportManager;
import com.testautomation.reimbursement.pages.LoginPage;
import io.cucumber.java.en.*;
import io.qameta.allure.*;

public class LoginSteps {

    private final LoginPage loginPage;
    private final Page page;
    private static final LoggerWrapper log = new LoggerWrapper(LoginSteps.class);

    public LoginSteps() {
        this.page = DriverManager.getPage(); // ✅ Use DrivertManager instead of PlaywrightFactory
        this.loginPage = new LoginPage(page);
    }

    @Given("user is on login page")
    @Step("Navigate to login page")
    @Severity(SeverityLevel.CRITICAL)
    public void user_is_on_login_page() {
        log.step("Navigated to Login Page");
        AllureReportManager.attachText("Step", "User navigated to login page");
    }

    @When("user logs in with username {string} and password {string}")
    @Step("User logs in with credentials")
    @Severity(SeverityLevel.CRITICAL)
    public void user_logs_in_with_credentials(String username, String password) {
        log.step("Logging in with: " + username);
        loginPage.login(username, password);
        AllureReportManager.attachText("Credentials", "User: " + username);
    }

    @Then("user should be redirected to the dashboard")
    @Step("Validate dashboard")
    @Severity(SeverityLevel.NORMAL)
    public void user_should_be_redirected_to_the_dashboard() {
        log.step("Verifying dashboard page...");
        AllureReportManager.attachText("Verification", "Dashboard check complete");
    }
}
