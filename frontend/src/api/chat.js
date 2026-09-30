/**
 * Chat API — chat-related API calls.
 */

import { apiFetch, getApiUrl } from "./client";

/**
 * Send a chat message (non-streaming).
 *
 * @param {string} message - User message text
 * @param {string|null} mood - Current mood label
 * @param {number|null} conversationId - Existing conversation ID
 * @returns {Promise<{reply: string, conversation_id: number}>}
 */
export async function sendMessage(message, mood = null, conversationId = null) {
  const res = await apiFetch("/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      mood,
      conversation_id: conversationId,
    }),
  });

  return res.json();
}

/**
 * Send a chat message with streaming (SSE).
 * Returns the raw Response object so the caller can read the stream.
 *
 * @param {string} message - User message text
 * @param {string|null} mood - Current mood label
 * @param {number|null} conversationId - Existing conversation ID
 * @param {string} token - JWT token (needed for direct fetch)
 * @returns {Promise<Response>}
 */
export async function streamMessage(message, mood = null, conversationId = null, token = null) {
  const API_URL = getApiUrl();

  const res = await fetch(`${API_URL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify({
      message,
      mood,
      conversation_id: conversationId,
    }),
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  return res;
}
