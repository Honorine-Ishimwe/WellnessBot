/**
 * ChatBox — Main chat interface.
 * Pure UI component — all state and API logic lives in useChat hook.
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import useChat from "../hooks/useChat";
import "./chatBox.css";

const MOODS = [
  { label: "Stressed" },
  { label: "Sad" },
  { label: "Anxious" },
  { label: "Tired" },
  { label: "Motivated" },
];

export default function ChatBox({
  conversationId,
  onConversationIdChange,
  initialMessages,
  initialMood,
}) {
  const {
    messages,
    setMessages,
    selectedMood,
    setSelectedMood,
    isLoading,
    streamingText,
    sendMessage,
    liveRegionRef,
  } = useChat(conversationId, onConversationIdChange, initialMessages, initialMood);

  const [userInput, setUserInput] = useState("");
  const [showMoodPicker, setShowMoodPicker] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Reset state when props change (loading a different conversation)
  useEffect(() => {
    if (initialMessages) {
      setMessages(initialMessages);
    }
  }, [initialMessages, setMessages]);

  useEffect(() => {
    if (initialMood !== undefined) {
      setSelectedMood(initialMood);
    }
  }, [initialMood, setSelectedMood]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText]);

  // Show mood picker at start of new conversations
  const shouldShowMoodPicker = !selectedMood && messages.length <= 1 && !conversationId;

  const handleMoodSelect = (mood) => {
    setSelectedMood(mood);
    setShowMoodPicker(false);
    const moodMessage = `I'm feeling ${mood.label.toLowerCase()} right now.`;
    sendMessage(moodMessage, mood.label);
  };

  const handleMoodReselect = () => {
    setShowMoodPicker((prev) => !prev);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userInput.trim() || isLoading) return;
    const msg = userInput.trim();
    setUserInput("");
    sendMessage(msg);
    // Refocus input after send
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  /**
   * Export conversation as a text file.
   */
  const handleExport = useCallback(() => {
    const lines = messages.map((msg) => {
      const label = msg.sender === "bot" ? "WellnessBot" : "You";
      return `${label}: ${msg.text}`;
    });
    const content = lines.join("\n\n");
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `wellnessbot-chat-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [messages]);

  /**
   * Copy conversation to clipboard.
   */
  const handleCopy = useCallback(async () => {
    const lines = messages.map((msg) => {
      const label = msg.sender === "bot" ? "WellnessBot" : "You";
      return `${label}: ${msg.text}`;
    });
    try {
      await navigator.clipboard.writeText(lines.join("\n\n"));
      // Brief visual feedback could be added here
    } catch {
      console.error("Failed to copy to clipboard");
    }
  }, [messages]);

  return (
    <div className="chatbox-wrapper">
      {/* Screen reader live region */}
      <div
        ref={liveRegionRef}
        className="sr-only"
        aria-live="polite"
        aria-atomic="true"
      />

      <div className="chatbox">
        {/* Header */}
        <div className="chatbox-header">
          <div className="chatbox-header-dot" />
          <span className="chatbox-header-title">WellnessBot</span>
          {selectedMood && (
            <button
              className="chatbox-header-mood"
              onClick={handleMoodReselect}
              aria-label={`Current mood: ${selectedMood.label}. Click to change.`}
              title="Click to change mood"
            >
              {selectedMood.label}
            </button>
          )}
          <div className="chatbox-header-actions">
            <button
              id="export-btn"
              className="chatbox-header-action-btn"
              onClick={handleExport}
              aria-label="Export conversation"
              title="Download conversation"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            </button>
            <button
              id="copy-btn"
              className="chatbox-header-action-btn"
              onClick={handleCopy}
              aria-label="Copy conversation to clipboard"
              title="Copy to clipboard"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
              </svg>
            </button>
          </div>
          <span className="chatbox-header-status">● Online</span>
        </div>

        {/* Messages */}
        <div
          className="chatbox-messages"
          role="log"
          aria-label="Chat messages"
          aria-relevant="additions"
        >
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`chatbox-msg chatbox-msg--${msg.sender}`}
            >
              {msg.sender === "bot" && (
                <div className="chatbox-avatar" aria-hidden="true">W</div>
              )}
              <div className={`chatbox-bubble chatbox-bubble--${msg.sender}`}>
                {msg.text}
              </div>
            </div>
          ))}

          {/* Streaming text */}
          {isLoading && streamingText && (
            <div className="chatbox-msg chatbox-msg--bot">
              <div className="chatbox-avatar" aria-hidden="true">W</div>
              <div className="chatbox-bubble chatbox-bubble--bot chatbox-bubble--streaming">
                {streamingText}
                <span className="streaming-cursor" />
              </div>
            </div>
          )}

          {/* Typing indicator (only when streaming hasn't started) */}
          {isLoading && !streamingText && (
            <div className="chatbox-msg chatbox-msg--bot">
              <div className="chatbox-avatar" aria-hidden="true">W</div>
              <div className="chatbox-bubble chatbox-bubble--bot chatbox-typing">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            </div>
          )}

          {/* Mood picker — initial or re-selection */}
          {(shouldShowMoodPicker || showMoodPicker) && (
            <div className="chatbox-mood-picker" role="group" aria-label="Select your mood">
              <p className="chatbox-mood-label">How are you feeling?</p>
              <div className="chatbox-mood-buttons" role="radiogroup">
                {MOODS.map((mood) => (
                  <button
                    key={mood.label}
                    id={`mood-btn-${mood.label.toLowerCase()}`}
                    className={`chatbox-mood-btn ${selectedMood?.label === mood.label ? "chatbox-mood-btn--selected" : ""}`}
                    onClick={() => handleMoodSelect(mood)}
                    disabled={isLoading}
                    role="radio"
                    aria-checked={selectedMood?.label === mood.label}
                    aria-label={mood.label}
                  >
                    <span className="chatbox-mood-text">{mood.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Disclaimer */}
        <div className="chatbox-disclaimer" role="note">
          <svg className="chatbox-disclaimer-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>WellnessBot provides general wellness support only and is not a substitute for professional care.</span>
        </div>

        {/* Input */}
        <form className="chatbox-input" onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            id="chat-input"
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Share what's on your mind…"
            disabled={isLoading}
            autoComplete="off"
            aria-label="Type your message"
            maxLength={2000}
          />
          <button
            id="chat-send-btn"
            type="submit"
            disabled={isLoading || !userInput.trim()}
            aria-label="Send message"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}