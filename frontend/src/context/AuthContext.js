/**
 * AuthContext — provides authentication state to the app.
 * API calls are delegated to api/auth.js.
 * Stores JWT in localStorage and wraps Google OAuth flow.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { googleLogin as apiGoogleLogin } from "../api/auth";
import { apiFetch } from "../api/client";

const AuthContext = createContext(null);

const TOKEN_KEY = "wellnessbot_token";
const USER_KEY = "wellnessbot_user";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem(USER_KEY);
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(false);

  const isAuthenticated = !!token && !!user;

  // Save / clear localStorage when state changes
  useEffect(() => {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(USER_KEY);
    }
  }, [user]);

  /**
   * Login with a Google credential (ID token).
   * Sends it to the backend which verifies and returns our JWT.
   */
  const loginWithGoogle = useCallback(async (credential) => {
    setLoading(true);
    try {
      const data = await apiGoogleLogin(credential);
      setToken(data.token);
      setUser(data.user);
      return data;
    } catch (err) {
      console.error("Login error:", err);
      if (err.name === "TypeError" && err.message.includes("fetch")) {
        throw new Error("Cannot connect to server. Please ensure the backend is running at http://127.0.0.1:5001");
      }
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Log out — clear token and user.
   */
  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  /**
   * Make an authenticated API request.
   * Automatically attaches the JWT and handles 401s.
   */
  const authFetch = useCallback(async (path, options = {}) => {
    const res = await apiFetch(path, options);

    // If token is expired, log out
    if (res.status === 401) {
      setToken(null);
      setUser(null);
    }

    return res;
  }, []);

  const value = {
    token,
    user,
    isAuthenticated,
    loading,
    loginWithGoogle,
    logout,
    authFetch,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
