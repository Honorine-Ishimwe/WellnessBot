import React, { useState, useRef, useEffect } from "react";
import "./chatBox.css";

const MOODS = [
  { label: "Stressed", emoji: "😤" },
  { label: "Sad", emoji: "😢" },
  { label: "Anxious", emoji: "😰" },
  { label: "Tired", emoji: "😴" },
  { label: "Motivated", emoji: "💪" },
];

export default function ChatBox() {
  const [userInput, setUserInput] = useState("");
  const [selectedMood, setSelectedMood] = useState(null);
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hi there! 💙 How are you feeling today? Pick a mood below or just start typing." },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleMoodSelect = (mood) => {
    setSelectedMood(mood);
    // Auto-send a message when mood is picked
    const moodMessage = `I'm feeling ${mood.label.toLowerCase()} right now.`;
    sendMessage(moodMessage, mood.label);
  };

  const sendMessage = async (text, mood = selectedMood?.label || null) => {
    const updatedMessages = [...messages, { sender: "user", text }];
    setMessages(updatedMessages);
    setIsLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, mood, history: updatedMessages }),
      });

      const data = await response.json();
      setMessages((prev) => [...prev, { sender: "bot", text: data.reply }]);
    } catch (error) {
      console.error("Error:", error);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Sorry, something went wrong. Please try again. 💙" },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userInput.trim() || isLoading) return;
    const msg = userInput.trim();
    setUserInput("");
    sendMessage(msg);
  };

  // Show mood picker only if no mood has been selected yet
  const showMoodPicker = !selectedMood && messages.length <= 1;

  return (
    <div className="chatbox-wrapper">
      <div className="chatbox">
        {/* Header */}
        <div className="chatbox-header">
          <div className="chatbox-header-dot" />
          <span className="chatbox-header-title">WellnessBot</span>
          {selectedMood && (
            <span className="chatbox-header-mood">
              {selectedMood.emoji} {selectedMood.label}
            </span>
          )}
          <span className="chatbox-header-status">● Online</span>
        </div>

        {/* Messages */}
        <div className="chatbox-messages">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`chatbox-msg chatbox-msg--${msg.sender}`}
            >
              {msg.sender === "bot" && (
                <div className="chatbox-avatar">🧘</div>
              )}
              <div className={`chatbox-bubble chatbox-bubble--${msg.sender}`}>
                {msg.text}
              </div>
            </div>
          ))}

          {/* Mood picker */}
          {showMoodPicker && (
            <div className="chatbox-mood-picker">
              <p className="chatbox-mood-label">How are you feeling?</p>
              <div className="chatbox-mood-buttons">
                {MOODS.map((mood) => (
                  <button
                    key={mood.label}
                    id={`mood-btn-${mood.label.toLowerCase()}`}
                    className="chatbox-mood-btn"
                    onClick={() => handleMoodSelect(mood)}
                    disabled={isLoading}
                  >
                    <span className="chatbox-mood-emoji">{mood.emoji}</span>
                    <span className="chatbox-mood-text">{mood.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {isLoading && (
            <div className="chatbox-msg chatbox-msg--bot">
              <div className="chatbox-avatar">🧘</div>
              <div className="chatbox-bubble chatbox-bubble--bot chatbox-typing">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Disclaimer */}
        <div className="chatbox-disclaimer">
          ⚠️ WellnessBot is not a therapist or emergency service. For general wellness support only.
        </div>

        {/* Input */}
        <form className="chatbox-input" onSubmit={handleSubmit}>
          <input
            id="chat-input"
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Share what's on your mind…"
            disabled={isLoading}
            autoComplete="off"
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