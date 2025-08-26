package com.testautomation.framework.factory;

import com.testautomation.framework.logger.LoggerWrapper;
import com.testautomation.framework.manager.DriverManager;
import com.testautomation.framework.utils.ConfigManager;
import io.github.bonigarcia.wdm.WebDriverManager;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.edge.EdgeDriver;
import org.openqa.selenium.firefox.FirefoxDriver;

public class SeleniumDriverFactory {

    private static final LoggerWrapper log = new LoggerWrapper(SeleniumDriverFactory.class);

    private static final String FIREFOX = "firefox";
    private static final String EDGE = "edge";
    private static final String CHROME = "chrome";

    public static void initDriver() {
        if (DriverManager.getSeleniumDriver() != null) {
            log.info("Selenium WebDriver already initialized for this thread.");
            return;
        }

        String browser = ConfigManager.get("browser").toLowerCase();
        String baseUrl = ConfigManager.get("baseUrl");
        boolean isHeadless = ConfigManager.getBoolean("headless");

        WebDriver driver;

        log.info("Initializing Selenium WebDriver for browser: {}", browser);

        switch (browser) {
            case FIREFOX:
                WebDriverManager.firefoxdriver().setup();
                driver = new FirefoxDriver();
                log.info("FirefoxDriver initialized.");
                break;

            case EDGE:
                WebDriverManager.edgedriver().setup();
                driver = new EdgeDriver();
                log.info("EdgeDriver initialized.");
                break;

            case CHROME:
            default:
                WebDriverManager.chromedriver().setup();
                ChromeOptions options = getChromeOptions(isHeadless);
                driver = new ChromeDriver(options);
                log.info("ChromeDriver initialized.");
                break;
        }

        DriverManager.setSeleniumDriver(driver);

        driver.get(baseUrl);
        log.step("Navigated to base URL: {}", baseUrl);

        driver.manage().window().maximize();
        log.step("Browser window maximized.");
    }

    private static ChromeOptions getChromeOptions(boolean isHeadless) {
        ChromeOptions options = new ChromeOptions();
        options.setExperimentalOption("useAutomationExtension", false);
        options.setExperimentalOption("excludeSwitches", new String[]{"enable-automation"});
        options.addArguments("--remote-allow-origins=*");

        if (isHeadless) {
            options.addArguments("--headless=new");
            options.addArguments("--disable-gpu");
            options.addArguments("--disable-dev-shm-usage");
            options.addArguments("--window-size=1920,1080");
            log.info("Chrome headless mode enabled.");
        }

        return options;
    }

    public static void closeDriver() {
        WebDriver driver = DriverManager.getSeleniumDriver();
        if (driver != null) {
            try {
                driver.quit();
                log.info("WebDriver quit successfully.");
            } catch (Exception e) {
                log.error("Failed to quit WebDriver: {}", e.getMessage());
            }
        }
        DriverManager.clearAll();  // Centralized cleanup for thread-local instances
        log.info("Selenium WebDriver resources cleared for this thread.");
    }
}
