package com.testautomation.framework.listeners;

import com.testautomation.framework.report.AllureReportManager;
import org.testng.*;

public class TestListener implements ITestListener {

    @Override
    public void onTestFailure(ITestResult result) {
        AllureReportManager.attachText("Test Failure", "Failed test: " + result.getName());

        try {
            Object testInstance = result.getInstance();
            Class<?> clazz = testInstance.getClass().getSuperclass();

            if (clazz.getDeclaredField("page") != null) {
                // Playwright Page object
                Object pageObj = clazz.getDeclaredField("page").get(testInstance);
                if (pageObj instanceof com.microsoft.playwright.Page) {
                    com.microsoft.playwright.Page page = (com.microsoft.playwright.Page) pageObj;
                    byte[] screenshot = page.screenshot(new com.microsoft.playwright.Page.ScreenshotOptions().setFullPage(true));
                    AllureReportManager.attachScreenshot("Playwright Failure - " + result.getName(), screenshot);
                }
            } else if (clazz.getDeclaredField("driver") != null) {
                // Selenium WebDriver
                Object driverObj = clazz.getDeclaredField("driver").get(testInstance);
                if (driverObj instanceof org.openqa.selenium.TakesScreenshot) {
                    byte[] screenshot = ((org.openqa.selenium.TakesScreenshot) driverObj)
                            .getScreenshotAs(org.openqa.selenium.OutputType.BYTES);
                    AllureReportManager.attachScreenshot("Selenium Failure - " + result.getName(), screenshot);
                }
            }
        } catch (Exception e) {
            AllureReportManager.attachText("Listener Exception", e.getMessage());
        }
    }

    @Override
    public void onTestStart(ITestResult result) {
        AllureReportManager.attachText("Test Start", "Starting test: " + result.getName());
    }
}
