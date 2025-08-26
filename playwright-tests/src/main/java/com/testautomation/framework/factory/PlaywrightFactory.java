package com.testautomation.framework.factory;

import com.microsoft.playwright.*;
import com.testautomation.framework.logger.LoggerWrapper;
import com.testautomation.framework.manager.DriverManager;
import com.testautomation.framework.utils.ConfigManager;

// Updated PlaywrightFactory.java (cleaner)
public class PlaywrightFactory {

    private static final LoggerWrapper log = new LoggerWrapper(PlaywrightFactory.class);

    public static void initBrowser() {
        if (DriverManager.getPage() != null) {
            log.info("Playwright already initialized for this thread.");
            return;
        }

        Playwright playwright = Playwright.create();
        DriverManager.setPlaywright(playwright);

        String browserType = ConfigManager.get("browser").toLowerCase();
        boolean isHeadless = ConfigManager.getBoolean("headless");
        String baseUrl = ConfigManager.get("baseUrl");

        BrowserType.LaunchOptions options = new BrowserType.LaunchOptions().setHeadless(isHeadless);
        Browser browser = switch (browserType) {
            case "firefox" -> playwright.firefox().launch(options);
            case "webkit" -> playwright.webkit().launch(options);
            default -> playwright.chromium().launch(options);
        };
        log.info("{} browser launched", browserType);

        DriverManager.setBrowser(browser);

        BrowserContext context = browser.newContext(new Browser.NewContextOptions().setViewportSize(1920, 1080));
        DriverManager.setContext(context);

        Page page = context.newPage();
        DriverManager.setPage(page);

        if (baseUrl != null && !baseUrl.isEmpty()) {
            page.navigate(baseUrl);
            log.step("Navigated to base URL: {}", baseUrl);
        }
    }

    public static void closeBrowser() {
        if (DriverManager.getPage() != null) DriverManager.getPage().close();
        if (DriverManager.getContext() != null) DriverManager.getContext().close();
        if (DriverManager.getBrowser() != null) DriverManager.getBrowser().close();
        if (DriverManager.getPlaywright() != null) DriverManager.getPlaywright().close();

        DriverManager.clearAll();
        log.info("Playwright resources closed and cleared for this thread.");
    }
}
