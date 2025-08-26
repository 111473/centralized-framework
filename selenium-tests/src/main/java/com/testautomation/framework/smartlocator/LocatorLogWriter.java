package com.testautomation.framework.smartlocator;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class LocatorLogWriter {

    private static final String LOG_FILE_PATH = "locator-suggestions.json";

    public static void logSuggestion(String failedLocator, String suggestion) {
        ObjectMapper mapper = new ObjectMapper();
        ObjectNode node = mapper.createObjectNode();
        node.put("failedLocator", failedLocator);
        node.put("suggestedLocator", suggestion);
        node.put("timestamp", System.currentTimeMillis());

        try (FileWriter writer = new FileWriter(new File(LOG_FILE_PATH), true)) {
            writer.write(mapper.writeValueAsString(node));
            writer.write(System.lineSeparator());
        } catch (IOException e) {
            System.err.println("Failed to write suggestion log: " + e.getMessage());
        }
    }
}
