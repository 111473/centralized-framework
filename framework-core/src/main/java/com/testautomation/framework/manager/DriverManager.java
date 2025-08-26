package com.testautomation.framework.manager;

import org.openqa.selenium.WebDriver;
import com.microsoft.playwright.*;

public class DriverManager {

    // ===== Selenium Driver Management =====
    private static final ThreadLocal<WebDriver> seleniumDriver = new ThreadLocal<>();

    public static WebDriver getSeleniumDriver() {
        return seleniumDriver.get();
    }

    public static void setSeleniumDriver(WebDriver driver) {
        seleniumDriver.set(driver);
    }

    public static void removeSeleniumDriver() {
        try {
            if (seleniumDriver.get() != null) {
                seleniumDriver.get().quit();
            }
        } catch (Exception e) {
            // Optionally log error
        } finally {
            seleniumDriver.remove();
        }
    }

    // ===== Playwright Management =====
    private static final ThreadLocal<Playwright> playwrightThread = new ThreadLocal<>();
    private static final ThreadLocal<Browser> browserThread = new ThreadLocal<>();
    private static final ThreadLocal<BrowserContext> contextThread = new ThreadLocal<>();
    private static final ThreadLocal<Page> pageThread = new ThreadLocal<>();

    public static Playwright getPlaywright() {
        return playwrightThread.get();
    }

    public static void setPlaywright(Playwright playwright) {
        playwrightThread.set(playwright);
    }

    public static Browser getBrowser() {
        return browserThread.get();
    }

    public static void setBrowser(Browser browser) {
        browserThread.set(browser);
    }

    public static BrowserContext getContext() {
        return contextThread.get();
    }

    public static void setContext(BrowserContext context) {
        contextThread.set(context);
    }

    public static Page getPage() {
        return pageThread.get();
    }

    public static void setPage(Page page) {
        pageThread.set(page);
    }

    public static void removePlaywright() {
        try {
            if (pageThread.get() != null) pageThread.get().close();
            if (contextThread.get() != null) contextThread.get().close();
            if (browserThread.get() != null) browserThread.get().close();
            if (playwrightThread.get() != null) playwrightThread.get().close();
        } catch (Exception e) {
            // Optionally log error
        } finally {
            pageThread.remove();
            contextThread.remove();
            browserThread.remove();
            playwrightThread.remove();
        }
    }

    // ===== Unified Clear Method =====
    public static void clearAll() {
        removeSeleniumDriver();
        removePlaywright();
    }
}
