/**
 * useChat — custom hook for chat state management and API interaction.
 * Extracts all chat logic (send, stream, loading, errors) from ChatBox.
 */

import { useState, useRef, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { streamMessage as apiStreamMessage } from "../api/chat";
import { apiFetch } from "../api/client";

const DEFAULT_BOT_MESSAGE = {
  sender: "bot",
  text: "Hi there! How are you feeling today? Pick a mood below or just start typing.",
};

export default function useChat(conversationId, onConversationIdChange, initialMessages, initialMood) {
  const { token } = useAuth();
  const [messages, setMessages] = useState(initialMessages || [DEFAULT_BOT_MESSAGE]);
  const [selectedMood, setSelectedMood] = useState(initialMood || null);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const liveRegionRef = useRef(null);

  /**
   * Send a message using the streaming endpoint.
   * Falls back to non-streaming on error.
   */
  const sendMessage = useCallback(async (text, mood = selectedMood?.label || null) => {
    setMessages((prev) => [...prev, { sender: "user", text }]);
    setIsLoading(true);
    setStreamingText("");

    try {
      const res = await apiStreamMessage(text, mood, conversationId, token);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let fullReply = "";
      let newConvId = conversationId;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6).trim();

          if (data === "[DONE]") continue;

          try {
            const parsed = JSON.parse(data);

            if (parsed.conversation_id && !conversationId) {
              newConvId = parsed.conversation_id;
              onConversationIdChange?.(newConvId);
            }

            if (parsed.token) {
              fullReply += parsed.token;
              setStreamingText(fullReply);
            }

            if (parsed.error) {
              fullReply = parsed.error;
              setStreamingText(fullReply);
            }
          } catch {
            // Skip malformed JSON
          }
        }
      }

      // Streaming complete — add the full reply as a message
      if (fullReply) {
        setMessages((prev) => [...prev, { sender: "bot", text: fullReply }]);
        // Announce to screen readers
        if (liveRegionRef.current) {
          liveRegionRef.current.textContent = `WellnessBot says: ${fullReply}`;
        }
      }
    } catch (error) {
      console.error("Streaming error, falling back:", error);

      // Fallback to non-streaming endpoint
      try {
        const res = await apiFetch("/chat", {
          method: "POST",
          body: JSON.stringify({
            message: text,
            mood,
            conversation_id: conversationId,
          }),
        });
        const data = await res.json();
        setMessages((prev) => [...prev, { sender: "bot", text: data.reply }]);

        if (data.conversation_id && !conversationId) {
          onConversationIdChange?.(data.conversation_id);
        }
      } catch (fallbackError) {
        console.error("Fallback error:", fallbackError);
        setMessages((prev) => [
          ...prev,
          { sender: "bot", text: "Sorry, something went wrong. Please try again." },
        ]);
      }
    } finally {
      setIsLoading(false);
      setStreamingText("");
    }
  }, [conversationId, selectedMood, token, onConversationIdChange]);

  return {
    messages,
    setMessages,
    selectedMood,
    setSelectedMood,
    isLoading,
    streamingText,
    sendMessage,
    liveRegionRef,
  };
}
