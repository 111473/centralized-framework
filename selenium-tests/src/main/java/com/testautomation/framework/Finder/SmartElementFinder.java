package com.testautomation.framework.Finder;

import com.testautomation.framework.gpt.OpenAIServiceWrapper;
import com.testautomation.framework.smartlocator.LocatorLogWriter;
import org.openqa.selenium.*;

import java.util.Collections;
import java.util.List;

/**
 * SmartElementFinder: Attempts to heal failing locators using OpenAI.
 */
public class SmartElementFinder {

    private final WebDriver driver;
    private final String openAiApiKey;

    public SmartElementFinder(WebDriver driver) {
        this(driver, null);
    }

    public SmartElementFinder(WebDriver driver, String openAiApiKey) {
        this.driver = driver;
        this.openAiApiKey = (openAiApiKey != null && !openAiApiKey.isEmpty()) ? openAiApiKey : loadApiKey();
    }

    public WebElement findElement(List<Locator> locators) {
        for (Locator locator : locators) {
            try {
                return driver.findElement(buildBy(locator));
            } catch (NoSuchElementException ignored) {}
        }

        // If all locators failed, try GPT healing
        String failedLocator = locators.get(0).toString();
        String dom = driver.getPageSource();

        if (openAiApiKey == null || openAiApiKey.isEmpty()) {
            throw new RuntimeException("OpenAI API key is required for SmartElementFinder.");
        }

        OpenAIServiceWrapper gptAssistant = new OpenAIServiceWrapper(openAiApiKey);
        String suggestion = gptAssistant.suggestLocator(failedLocator, dom);

        LocatorLogWriter.logSuggestion(failedLocator, suggestion);
        System.out.printf("🧠 GPT suggestion for [%s]: %s%n", failedLocator, suggestion);

        try {
            By gptLocator = tryBuildByFromSuggestion(suggestion);
            return driver.findElement(gptLocator);
        } catch (Exception e) {
            throw new NoSuchElementException("All locators including GPT failed: " + failedLocator);
        }
    }

    public WebElement findElement(String type, String value) {
        return findElement(singletonLocator(type, value));
    }

    public static List<Locator> singletonLocator(String type, String value) {
        return Collections.singletonList(new Locator(type, value));
    }

    private By buildBy(Locator locator) {
        return switch (locator.type()) {
            case "id" -> By.id(locator.value());
            case "name" -> By.name(locator.value());
            case "css" -> By.cssSelector(locator.value());
            case "xpath" -> By.xpath(locator.value());
            case "class" -> By.className(locator.value());
            case "tag" -> By.tagName(locator.value());
            case "linkText" -> By.linkText(locator.value());
            case "partialLinkText" -> By.partialLinkText(locator.value());
            default -> throw new IllegalArgumentException("Unsupported locator type: " + locator.type());
        };
    }

    private By tryBuildByFromSuggestion(String suggestion) {
        String locator = suggestion.trim().replaceAll("[\"']", "");
        if (locator.contains("xpath") || locator.startsWith("//")) {
            return By.xpath(locator);
        }
        if (locator.contains("css") || locator.contains("#") || locator.contains(".")) {
            return By.cssSelector(locator);
        }
        throw new IllegalArgumentException("Could not parse GPT suggestion into a locator: " + suggestion);
    }

    private String loadApiKey() {
        String key = System.getenv("OPENAI_API_KEY");
        if (key == null || key.isEmpty()) {
            throw new IllegalStateException("OPENAI_API_KEY is not set. Please configure it as an environment variable.");
        }

        System.out.println("KEY>>>>:" + key);
        return key;
    }

    public record Locator(String type, String value) {
        @Override
        public String toString() {
            return type + "='" + value + "'";
        }
    }
}
