package com.testautomation.reimbursement.pages;

import com.microsoft.playwright.Page;

public class LoginPage {

    private final Page page;

    private final String usernameField = "[name='login']";
    private final String passwordField = "[name='password']";
    private final String loginButton = "[name='commit']";

    public LoginPage(Page page) {
        this.page = page;
    }

    public void login(String username, String password) {
        page.fill(usernameField, username);
        page.fill(passwordField, password);
        page.click(loginButton);
    }

    public boolean isOnDashboard() {
        return page.url().contains("/dashboard");
    }
}
