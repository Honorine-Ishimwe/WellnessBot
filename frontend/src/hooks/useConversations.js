/**
 * useConversations — custom hook for conversation list state management.
 * Extracts API calls and state from ConversationList component.
 */

import { useState, useCallback } from "react";
import {
  listConversations,
  getConversation,
  deleteConversation,
} from "../api/conversations";

export default function useConversations() {
  const [conversations, setConversations] = useState([]);

  const load = useCallback(async () => {
    try {
      const data = await listConversations();
      setConversations(data);
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  }, []);

  const select = useCallback(async (convId) => {
    try {
      const data = await getConversation(convId);
      return data;
    } catch (err) {
      console.error("Failed to load conversation:", err);
      return null;
    }
  }, []);

  const remove = useCallback(async (convId) => {
    try {
      await deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      return true;
    } catch (err) {
      console.error("Failed to delete conversation:", err);
      return false;
    }
  }, []);

  return {
    conversations,
    loadConversations: load,
    selectConversation: select,
    removeConversation: remove,
  };
}
