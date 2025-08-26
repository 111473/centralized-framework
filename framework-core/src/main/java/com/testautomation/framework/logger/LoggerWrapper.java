package com.testautomation.framework.logger;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LoggerWrapper {
    private final Logger logger;

    public LoggerWrapper(Class<?> clazz) {
        this.logger = LoggerFactory.getLogger(clazz);
    }

    public void info(String message) {
        logger.info("[INFO] {}", message);
    }

    public void info(String format, Object... args) {
        logger.info("[INFO] " + format, args);
    }

    public void debug(String message) {
        logger.debug("[DEBUG] {}", message);
    }

    public void debug(String format, Object... args) {
        logger.debug("[DEBUG] " + format, args);
    }

    public void warn(String message) {
        logger.warn("[WARN] {}", message);
    }

    public void warn(String format, Object... args) {
        logger.warn("[WARN] " + format, args);
    }

    public void error(String message, Throwable t) {
        logger.error("[ERROR] {}", message, t);
    }

    public void error(String format, Object... args) {
        logger.error("[ERROR] " + format, args);
    }

    public void step(String message) {
        logger.info("[STEP] {}", message);
    }

    public void step(String format, Object... args) {
        logger.info("[STEP] " + format, args);
    }

    public void testStart(String testName) {
        logger.info("[TEST_START] {}", testName);
    }

    public void assertLog(String message) {
        logger.info("[ASSERT] {}", message);
    }
}
