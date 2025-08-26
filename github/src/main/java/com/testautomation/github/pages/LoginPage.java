package com.testautomation.github.pages;

import com.testautomation.framework.Finder.SmartElementFinder;
import com.testautomation.framework.Finder.SmartElementFinder.Locator;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

import java.util.List;

/**
 * LoginPage – Represents the login page of the Loan Account app.
 * Uses SmartElementFinder to enable GPT-based locator healing.
 */
public class LoginPage {

    private final WebDriver driver;
    private final SmartElementFinder finder;

    // Locators defined for healing attempts
    private final List<Locator> usernameLocators = List.of(
            new Locator("id", "UserName"),
            new Locator("name", "login"),
            new Locator("css", "input[name='login']")
    );

    private final List<Locator> passwordLocators = List.of(
            new Locator("id", "Password_00"),
            new Locator("name", "password_00"),
            new Locator("css", "input[type='password_00']")
    );

    private final List<Locator> loginButtonLocators = List.of(
            new Locator("id", "btnLogin"),
            new Locator("name", "commit"),
            new Locator("css", "input[type='submit']")
    );

    public LoginPage(WebDriver driver, String apiKey) {
        this.driver = driver;
        this.finder = new SmartElementFinder(driver, apiKey);
    }

    public void login(String username, String password) {
        WebElement usernameField = finder.findElement(usernameLocators);
        WebElement passwordField = finder.findElement(passwordLocators);
        WebElement loginButton = finder.findElement(loginButtonLocators);

        usernameField.clear();
        usernameField.sendKeys(username);

        passwordField.clear();
        passwordField.sendKeys(password);

        loginButton.click();
    }

    public String getTitle() {
        return driver.getTitle();
    }

    public boolean isLoginButtonDisplayed() {
        try {
            return finder.findElement(loginButtonLocators).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }
}
