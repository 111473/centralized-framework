package com.testautomation.framework.report;

import io.qameta.allure.Allure;
import io.qameta.allure.Attachment;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;

public class AllureReportManager {

    // ─────────────────────────────────────────────────────────────
    // Annotation-based Attachments: Clean and structured
    // ─────────────────────────────────────────────────────────────

    @Attachment(value = "{name}", type = "text/plain")
    public static String attachText(String name, String message) {
        return message;
    }

    @Attachment(value = "{name}", type = "text/html")
    public static String attachHtml(String name, String html) {
        return html;
    }

    @Attachment(value = "{name}", type = "application/json")
    public static String attachJson(String name, String json) {
        return json;
    }

    // ─────────────────────────────────────────────────────────────
    // Stream-based Attachments: For screenshots or dynamic content
    // ─────────────────────────────────────────────────────────────

    public static void attachScreenshot(String name, byte[] screenshotBytes) {
        Allure.addAttachment(name, "image/png", new ByteArrayInputStream(screenshotBytes), "png");
    }

    public static void attachCsv(String name, String csvContent) {
        Allure.addAttachment(name, "text/csv", new ByteArrayInputStream(csvContent.getBytes(StandardCharsets.UTF_8)), "csv");
    }

    public static void attachXml(String name, String xmlContent) {
        Allure.addAttachment(name, "application/xml", new ByteArrayInputStream(xmlContent.getBytes(StandardCharsets.UTF_8)), "xml");
    }

    public static void attachPdf(String name, byte[] pdfBytes) {
        Allure.addAttachment(name, "application/pdf", new ByteArrayInputStream(pdfBytes), "pdf");
    }
}
