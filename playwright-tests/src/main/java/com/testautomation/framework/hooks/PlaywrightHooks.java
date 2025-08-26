package com.testautomation.framework.hooks;

import com.microsoft.playwright.Page;
import com.testautomation.framework.factory.PlaywrightFactory;
import com.testautomation.framework.logger.LoggerWrapper;
import com.testautomation.framework.manager.DriverManager;
import com.testautomation.framework.report.AllureReportManager;
import com.testautomation.framework.utils.ConfigManager;
import com.testautomation.framework.utils.ProjectResolver;
import io.cucumber.java.*;
import io.qameta.allure.Attachment;

public class PlaywrightHooks {

    private static final LoggerWrapper log = new LoggerWrapper(PlaywrightHooks.class);

    @Before("@playwright")
    public void setUp() {
        String project = ProjectResolver.resolveActiveProject();
        ConfigManager.setProject(project);  // ✅ Fixes the IllegalStateException

        PlaywrightFactory.initBrowser();
        log.step("[HOOK] Playwright browser initialized.");
    }

    @After("@playwright")
    public void tearDown() {
        PlaywrightFactory.closeBrowser();
        log.step("[HOOK] Playwright browser closed.");
    }

    @AfterStep("@playwright")
    public void captureScreenshotOnFailure(Scenario scenario) {
        if (scenario.isFailed()) {
            try {
                Page page = DriverManager.getPage();
                byte[] screenshot = page.screenshot(new Page.ScreenshotOptions().setFullPage(true));
                attachScreenshot(scenario.getName(), screenshot);
                log.warn("Captured screenshot for failed scenario: {}", scenario.getName());
            } catch (Exception e) {
                log.error("Error capturing screenshot: {}", e.getMessage());
            }
        }
    }

    @Attachment(value = "{screenshotName}", type = "image/png")
    private byte[] attachScreenshot(String screenshotName, byte[] screenshot) {
        AllureReportManager.attachScreenshot(screenshotName, screenshot);
        return screenshot;
    }
}
