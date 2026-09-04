import React, { useState, useCallback, useEffect } from "react";
import "./App.css";
import { useAuth } from "./context/AuthContext";
import AuthScreen from "./components/authScreen";
import WelcomeMessage from "./components/welcomeMessage";
import ChatBox from "./components/chatBox";
import ConversationList from "./components/conversationList";

function App() {
  const { isAuthenticated } = useAuth();

  // ── Theme state ────────────────────────────────────
  const [darkMode, setDarkMode] = useState(() => {
    const stored = localStorage.getItem("wellnessbot_theme");
    if (stored) return stored === "dark";
    return typeof window !== "undefined" && typeof window.matchMedia === "function"
      ? window.matchMedia("(prefers-color-scheme: dark)").matches
      : false;
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("wellnessbot_theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  // ── Conversation state ─────────────────────────────
  const [conversationId, setConversationId] = useState(null);
  const [chatMessages, setChatMessages] = useState(null);
  const [chatMood, setChatMood] = useState(null);
  const [chatKey, setChatKey] = useState(0); // force re-mount on new chat

  const handleNewChat = useCallback(() => {
    setConversationId(null);
    setChatMessages(null);
    setChatMood(null);
    setChatKey((k) => k + 1);
  }, []);

  const handleSelectConversation = useCallback((conversation, messages) => {
    setConversationId(conversation.id);
    setChatMood(conversation.mood ? { label: conversation.mood, emoji: "" } : null);
    setChatMessages(
      messages.map((m) => ({ sender: m.sender, text: m.text }))
    );
    setChatKey((k) => k + 1);
  }, []);

  const handleConversationIdChange = useCallback((newId) => {
    setConversationId(newId);
  }, []);

  // ── Not authenticated → show sign-in ───────────────
  if (!isAuthenticated) {
    return (
      <div className={`app-root ${darkMode ? "dark" : ""}`}>
        <div className="bubbles">
          <div className="bubble" style={{ left: "10%", animationDuration: "12s", animationDelay: "0s" }} />
          <div className="bubble" style={{ left: "30%", animationDuration: "15s", animationDelay: "2s" }} />
          <div className="bubble" style={{ left: "50%", animationDuration: "10s", animationDelay: "4s" }} />
          <div className="bubble" style={{ left: "70%", animationDuration: "14s", animationDelay: "1s" }} />
          <div className="bubble" style={{ left: "85%", animationDuration: "11s", animationDelay: "3s" }} />
        </div>

        <button
          id="theme-toggle"
          className="theme-toggle"
          onClick={() => setDarkMode((d) => !d)}
          aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
          title={darkMode ? "Light mode" : "Dark mode"}
        >
          {darkMode ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          )}
        </button>

        <AuthScreen />
      </div>
    );
  }

  // ── Authenticated → show app ───────────────────────
  return (
    <div className={`app-root ${darkMode ? "dark" : ""}`}>
      {/* Skip to content — accessibility */}
      <a href="#chat-input" className="skip-to-content">
        Skip to chat
      </a>

      <div className="bubbles">
        <div className="bubble" style={{ left: "10%", animationDuration: "12s", animationDelay: "0s" }} />
        <div className="bubble" style={{ left: "30%", animationDuration: "15s", animationDelay: "2s" }} />
        <div className="bubble" style={{ left: "50%", animationDuration: "10s", animationDelay: "4s" }} />
        <div className="bubble" style={{ left: "70%", animationDuration: "14s", animationDelay: "1s" }} />
        <div className="bubble" style={{ left: "85%", animationDuration: "11s", animationDelay: "3s" }} />
        <div className="bubble" style={{ left: "20%", animationDuration: "16s", animationDelay: "5s" }} />
        <div className="bubble" style={{ left: "60%", animationDuration: "13s", animationDelay: "6s" }} />
      </div>

      {/* Theme toggle */}
      <button
        id="theme-toggle"
        className="theme-toggle"
        onClick={() => setDarkMode((d) => !d)}
        aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
        title={darkMode ? "Light mode" : "Dark mode"}
      >
        {darkMode ? (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="5" />
            <line x1="12" y1="1" x2="12" y2="3" />
            <line x1="12" y1="21" x2="12" y2="23" />
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
            <line x1="1" y1="12" x2="3" y2="12" />
            <line x1="21" y1="12" x2="23" y2="12" />
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
          </svg>
        ) : (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
        )}
      </button>

      {/* Conversation sidebar */}
      <ConversationList
        currentConversationId={conversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
      />

      <main className="page" role="main">
        <section className="left" aria-label="Welcome">
          <WelcomeMessage />
        </section>
        <section className="right" aria-label="Chat">
          <ChatBox
            key={chatKey}
            conversationId={conversationId}
            onConversationIdChange={handleConversationIdChange}
            initialMessages={chatMessages}
            initialMood={chatMood}
          />
        </section>
      </main>
    </div>
  );
}

export default App;