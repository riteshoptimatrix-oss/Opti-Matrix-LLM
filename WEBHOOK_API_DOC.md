# Opti Matrix LLM API - Webhook Integration Guide

This document outlines how to connect any third-party Chatbot Builder platform (e.g., ManyChat, Dialogflow, Make, Voiceflow, Botpress) to the custom Opti Matrix LLM backend using an HTTP API Webhook.

## Overview
The LLM backend exposes a REST API endpoint that accepts a user's message, processes the intent, and returns the AI-generated answer. The chatbot builder simply needs to make an HTTP `POST` request to this endpoint whenever a user sends a message, and map the returned response back to the user.

---

## 1. Webhook Endpoint Details

- **Method:** `POST`
- **URL:** `https://<YOUR_DOMAIN_OR_NGROK>/ask` 
*(Note to Server Admin: Replace `<YOUR_DOMAIN_OR_NGROK>` with your live production URL or ngrok URL for local testing).*
- **Headers:**
  - `Content-Type: application/json`

---

## 2. Request Setup (JSON Payload)

Configure the "API Request" or "Webhook" node in the chatbot builder to send the following JSON body. 

You must map the variables from your chatbot platform (e.g., the user's message and their phone number/user ID) to the `question` and `session_id` fields.

```json
{
  "question": "{{user_message_variable}}",
  "session_id": "{{user_id_or_phone_number_variable}}"
}
```

### Request Parameters
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `question` | String | **Yes** | The actual text message sent by the user (e.g., "What are your services?"). |
| `session_id` | String | Optional (Recommended)| A unique identifier for the user or chat session (e.g., WhatsApp phone number). This is used by the LLM to remember chat history context. |

---

## 3. Response Handling (JSON Response)

If the request is successful, the LLM API will respond with an `HTTP 200 OK` status and a JSON payload structured like this:

```json
{
  "intent": "contact_sales",
  "answer": "You can reach out to our sales team at sales@optimatrix.com",
  "confidence": 0.95,
  "matched": true,
  "suggested_questions": [
    "What is your pricing?",
    "Do you offer custom development?"
  ]
}
```

### Mapping the Response in the Chatbot Builder
To send the AI's reply back to the user, you need to extract the `answer` variable from the JSON response.

1. **Extract Answer**: Parse the JSON response and map the `answer` key to a variable in your chatbot flow (e.g., `{{api_response.answer}}`).
2. **Display Message**: Add a "Send Message" block immediately after the Webhook block, and output the extracted `answer` variable to the user.
3. *(Optional)* **Suggested Questions**: If your chatbot platform supports Quick Replies or Buttons, you can map the array inside `suggested_questions` to render dynamic quick reply buttons below the text.

---

## 4. Error Handling & Fallbacks

It is recommended to set up a fallback condition in your chatbot builder in case the API request fails (e.g., server downtime or timeout).

- **Condition:** If HTTP Status Code `!= 200`
- **Fallback Message:** *"I'm currently undergoing maintenance. Please contact our support directly or try again later."*

## Example: Make.com / Integromat Setup
1. Add an **HTTP -> Make a request** module.
2. Set URL to the `/ask` endpoint.
3. Set Method to `POST`.
4. Set Body type to `Raw` and Content type to `JSON (application/json)`.
5. In the Request content, write `{"question": "1. Message Text", "session_id": "1. Sender Phone"}` (mapping the data pills from your trigger).
6. Check "Parse response".
7. In the next module (e.g., WhatsApp -> Send a Message), map the `answer` output from the HTTP module into the message body.
