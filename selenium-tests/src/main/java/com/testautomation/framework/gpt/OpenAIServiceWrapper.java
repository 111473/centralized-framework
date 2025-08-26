package com.testautomation.framework.gpt;

import com.theokanning.openai.service.OpenAiService;
import com.theokanning.openai.completion.chat.*;

import java.util.List;

public class OpenAIServiceWrapper {

    private final OpenAiService service;

    public OpenAIServiceWrapper(String apiKey) {
        this.service = new OpenAiService(apiKey);
    }

    public String suggestLocator(String failedLocator, String htmlSource) {
        String prompt = String.format("""
            A Selenium test failed using this locator: %s

            Here is the current page HTML source:

            %s

            Based on the structure, suggest a working XPath or CSS selector to locate the same element. Only return the locator string. No explanation.
            """, failedLocator, htmlSource);

        ChatMessage systemMsg = new ChatMessage("system", "You are a Selenium test assistant.");
        ChatMessage userMsg = new ChatMessage("user", prompt);

        ChatCompletionRequest chatRequest = ChatCompletionRequest.builder()
                .model("gpt-4o")
                .messages(List.of(systemMsg, userMsg))
                .temperature(0.5)
                .maxTokens(150)
                .build();

        ChatCompletionResult result = service.createChatCompletion(chatRequest);
        return result.getChoices().get(0).getMessage().getContent().trim();
    }
}
