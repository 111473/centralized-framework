package com.testautomation.framework.utils;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.InputStream;

public class ProjectResolver {

    private static final String DEFAULT_PROJECT = "loan-account";
    private static final String RUNTIME_FILE = "runtime.json";

    public static String resolveActiveProject() {
        // First check system property override
        String project = System.getProperty("project");
        if (project != null && !project.isEmpty()) {
            return project;
        }

        try (InputStream is = ProjectResolver.class.getClassLoader().getResourceAsStream(RUNTIME_FILE)) {
            if (is != null) {
                ObjectMapper mapper = new ObjectMapper();
                JsonNode root = mapper.readTree(is);

                project = root.path("activeProject").asText();
                if (project == null || project.isEmpty()) {
                    throw new IllegalStateException("Missing 'activeProject' in runtime.json.");
                }

                JsonNode projects = root.path("projects");
                if (!projects.has(project)) {
                    throw new IllegalArgumentException("Project '" + project + "' not found in 'projects' block.");
                }

                return project;
            } else {
                throw new RuntimeException("runtime.json not found in classpath.");
            }
        } catch (Exception e) {
            throw new RuntimeException("Failed to resolve active project", e);
        }
    }

    public static String resolveTestTypeForProject(String project) {
        try (InputStream is = ProjectResolver.class.getClassLoader().getResourceAsStream(RUNTIME_FILE)) {
            if (is != null) {
                ObjectMapper mapper = new ObjectMapper();
                JsonNode root = mapper.readTree(is);
                return root.path("projects").path(project).path("testType").asText();
            }
        } catch (Exception e) {
            throw new RuntimeException("Unable to determine test type for project: " + project, e);
        }
        return null;
    }
}
