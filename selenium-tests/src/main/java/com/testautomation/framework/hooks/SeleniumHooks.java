package com.testautomation.framework.hooks;

import com.testautomation.framework.factory.SeleniumDriverFactory;
import com.testautomation.framework.logger.LoggerWrapper;
import com.testautomation.framework.utils.ConfigManager;
import com.testautomation.framework.utils.ProjectResolver;
import io.cucumber.java.Before;
import io.cucumber.java.After;

public class SeleniumHooks {

    private static final LoggerWrapper log = new LoggerWrapper(SeleniumHooks.class);

    @Before("@selenium")
    public void setupSeleniumDriver() {
        String project = ProjectResolver.resolveActiveProject();
        ConfigManager.setProject(project);

        SeleniumDriverFactory.initDriver();
        log.step("Selenium WebDriver initialized using SeleniumDriverFactory.");
    }

    @After("@selenium")
    public void tearDownDriver() {
        SeleniumDriverFactory.closeDriver();
        log.step("Selenium WebDriver closed and cleared via SeleniumDriverFactory.");
    }
}
