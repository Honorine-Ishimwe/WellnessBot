/**
 * ConversationList — Sidebar showing past conversations.
 * Loads from /conversations API, supports loading and deleting conversations.
 */

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import "./conversationList.css";

export default function ConversationList({
  currentConversationId,
  onSelectConversation,
  onNewChat,
}) {
  const { authFetch, user, logout } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [isOpen, setIsOpen] = useState(false);

  const loadConversations = useCallback(async () => {
    try {
      const res = await authFetch("/conversations");
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations || []);
      }
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  }, [authFetch]);

  // Load on mount and when conversation changes
  useEffect(() => {
    loadConversations();
  }, [loadConversations, currentConversationId]);

  const handleDelete = async (e, convId) => {
    e.stopPropagation();
    if (!window.confirm("Delete this conversation?")) return;

    try {
      const res = await authFetch(`/conversations/${convId}`, { method: "DELETE" });
      if (res.ok) {
        setConversations((prev) => prev.filter((c) => c.id !== convId));
        if (convId === currentConversationId) {
          onNewChat();
        }
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  };

  const handleSelect = async (convId) => {
    try {
      const res = await authFetch(`/conversations/${convId}`);
      if (res.ok) {
        const data = await res.json();
        onSelectConversation(data.conversation, data.messages);
      }
    } catch (err) {
      console.error("Failed to load conversation:", err);
    }
    setIsOpen(false);
  };

  const formatDate = (isoString) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  return (
    <>
      {/* Toggle button */}
      <button
        id="sidebar-toggle"
        className={`sidebar-toggle ${isOpen ? "sidebar-toggle--open" : ""}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? "Close sidebar" : "Open conversation history"}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          {isOpen ? (
            <>
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </>
          ) : (
            <>
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </>
          )}
        </svg>
      </button>

      {/* Overlay */}
      {isOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`sidebar ${isOpen ? "sidebar--open" : ""}`}
        aria-label="Conversation history"
      >
        {/* User info */}
        {user && (
          <div className="sidebar-user">
            {user.avatar_url ? (
              <img
                src={user.avatar_url}
                alt={user.display_name}
                className="sidebar-user-avatar"
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="sidebar-user-avatar sidebar-user-avatar--fallback">
                {(user.display_name || user.email || "?")[0].toUpperCase()}
              </div>
            )}
            <div className="sidebar-user-info">
              <span className="sidebar-user-name">{user.display_name}</span>
              <span className="sidebar-user-email">{user.email}</span>
            </div>
            <button
              id="logout-btn"
              className="sidebar-logout-btn"
              onClick={logout}
              aria-label="Sign out"
              title="Sign out"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        )}

        {/* New Chat button */}
        <button
          id="new-chat-btn"
          className="sidebar-new-chat"
          onClick={() => { onNewChat(); setIsOpen(false); }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Chat
        </button>

        {/* Conversation list */}
        <div className="sidebar-conversations">
          {conversations.length === 0 ? (
            <p className="sidebar-empty">No conversations yet. Start chatting!</p>
          ) : (
            conversations.map((conv) => (
              <button
                key={conv.id}
                className={`sidebar-conv ${conv.id === currentConversationId ? "sidebar-conv--active" : ""}`}
                onClick={() => handleSelect(conv.id)}
              >
                <div className="sidebar-conv-header">
                  {conv.mood && (
                    <span className="sidebar-conv-mood-tag">{conv.mood}</span>
                  )}
                  <span className="sidebar-conv-title">{conv.title}</span>
                </div>
                <div className="sidebar-conv-footer">
                  <span className="sidebar-conv-date">{formatDate(conv.updated_at)}</span>
                  <button
                    className="sidebar-conv-delete"
                    onClick={(e) => handleDelete(e, conv.id)}
                    aria-label={`Delete conversation: ${conv.title}`}
                    title="Delete"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    </svg>
                  </button>
                </div>
              </button>
            ))
          )}
        </div>
      </aside>
    </>
  );
}
