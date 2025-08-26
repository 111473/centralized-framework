package com.testautomation.framework.utils;

import com.testautomation.framework.logger.LoggerWrapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.InputStream;

public class ConfigManager {

    private static final LoggerWrapper log = new LoggerWrapper(ConfigManager.class);

    private static final JsonNode rootNode;
    private static JsonNode selectedProjectNode;
    private static String currentProject;

    static {
        try (InputStream inputStream = ConfigManager.class.getClassLoader().getResourceAsStream("config.json")) {
            if (inputStream == null) {
                throw new RuntimeException("config.json not found in classpath.");
            }
            ObjectMapper mapper = new ObjectMapper();
            rootNode = mapper.readTree(inputStream);
            log.info("[CONFIG] config.json loaded successfully.");
        } catch (Exception e) {
            throw new RuntimeException("Failed to load config.json", e);
        }
    }

    /**
     * Set the active project configuration
     */
    public static void setProject(String projectName) {
        JsonNode projectsNode = rootNode.path("projects");
        JsonNode projectNode = projectsNode.path(projectName);

        if (projectNode.isMissingNode()) {
            throw new IllegalArgumentException("Project '" + projectName + "' not found in config.json.");
        }

        currentProject = projectName;
        selectedProjectNode = projectNode;
        log.info("[CONFIG] Active project set to: {}", projectName);
    }

    /**
     * Get a config value for the current project
     */
    public static String get(String key) {
        if (selectedProjectNode == null) {
            throw new IllegalStateException("[CONFIG] Project not set. Please call ConfigManager.setProject(projectName) first.");
        }

        JsonNode valueNode = selectedProjectNode.path(key);
        if (valueNode.isMissingNode()) {
            log.warn("[CONFIG] Key '{}' not found for project '{}'", key, currentProject);
            return null;
        }

        String value = valueNode.asText();
        log.info("[CONFIG] Retrieved key '{}' = '{}'", key, value);
        return value;
    }

    /**
     * Get a boolean config value
     */
    public static boolean getBoolean(String key) {
        String value = get(key);
        return value != null && Boolean.parseBoolean(value);
    }

    /**
     * Get the currently active project
     */
    public static String getCurrentProject() {
        return currentProject;
    }
}
