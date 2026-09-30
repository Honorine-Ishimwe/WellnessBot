/**
 * Conversations API — conversation CRUD API calls.
 */

import { apiFetch, apiJson } from "./client";

/**
 * List all conversations for the current user.
 *
 * @returns {Promise<Array>} Array of conversation objects
 */
export async function listConversations() {
  const data = await apiJson("/conversations");
  return data.conversations || [];
}

/**
 * Get a conversation with all its messages.
 *
 * @param {number} conversationId
 * @returns {Promise<{conversation: object, messages: Array}>}
 */
export async function getConversation(conversationId) {
  return apiJson(`/conversations/${conversationId}`);
}

/**
 * Delete a conversation.
 *
 * @param {number} conversationId
 * @returns {Promise<Response>}
 */
export async function deleteConversation(conversationId) {
  const res = await apiFetch(`/conversations/${conversationId}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    throw new Error(`Failed to delete conversation: HTTP ${res.status}`);
  }

  return res;
}
