package com.testautomation.loanaccount.steps;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.testautomation.framework.logger.LoggerWrapper;
import com.testautomation.framework.manager.DriverManager;
import com.testautomation.framework.report.AllureReportManager;
import com.testautomation.loanaccount.pages.LoginPage;
import io.cucumber.java.en.*;
import io.qameta.allure.*;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;

import java.io.InputStream;

public class LoginSteps {

    private LoginPage loginPage;
    private static final LoggerWrapper log = new LoggerWrapper(LoginSteps.class);

    @Given("user is on login page")
    @Step("Navigate to login page")
    @Severity(SeverityLevel.CRITICAL)
    public void userIsOnLoginPage() {
        log.testStart("user is on login page");

        WebDriver driver = DriverManager.getSeleniumDriver();
        attachScreenshot("Login Page");

        String apiKey = loadOpenAiApiKey();
        if (apiKey == null || apiKey.isBlank()) {
            log.error("Missing OpenAI API key! Set 'OPENAI_API_KEY'.");
            throw new RuntimeException("OpenAI API key is required for SmartElementFinder.");
        }

        loginPage = new LoginPage(driver, apiKey);
        AllureReportManager.attachText("Page Load", "Navigated to GitHub login page");
        log.step("LoginPage with SmartElementFinder initialized");
    }

    @When("user logs in with username {string} and password {string}")
    @Step("User logs in with credentials")
    @Severity(SeverityLevel.CRITICAL)
    public void userLogsIn(String username, String password) {
        log.step("Attempting login with username: " + username);
        loginPage.login(username, password);
        AllureReportManager.attachText("Login Attempt", "Username: " + username);
    }

    @Then("user should be redirected to the dashboard")
    @Step("Validate dashboard")
    @Severity(SeverityLevel.NORMAL)
    public void userShouldBeRedirected() throws InterruptedException {
        Thread.sleep(2000);
        attachScreenshot("Dashboard");
        log.step("Dashboard page displayed");
    }

    private void attachScreenshot(String name) {
        WebDriver driver = DriverManager.getSeleniumDriver();

        if (driver == null) {
            log.error("WebDriver is null when trying to capture screenshot: " + name);
            return;
        }

        try {
            byte[] screenshot = ((TakesScreenshot) driver).getScreenshotAs(OutputType.BYTES);
            AllureReportManager.attachScreenshot(name, screenshot);
            log.info("Screenshot captured: " + name);
        } catch (Exception e) {
            log.error("Failed to capture screenshot: " + name + " due to " + e.getMessage());
        }
    }

    private String loadOpenAiApiKey() {
        String envKey = System.getenv("OPENAI_API_KEY");
        if (envKey != null && !envKey.isBlank()) return envKey;

        try (InputStream is = getClass().getClassLoader().getResourceAsStream("config.json")) {
            if (is != null) {
                ObjectMapper mapper = new ObjectMapper();
                JsonNode node = mapper.readTree(is);
                return node.path("openai_api_key").asText(null);
            }
        } catch (Exception e) {
            log.error("Error reading OpenAI API key: " + e.getMessage());
        }

        return null;
    }
}
