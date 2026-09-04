/**
 * AuthScreen — Full-screen sign-in page with Google OAuth button.
 * Shown when the user is not authenticated.
 */

import React, { useState } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "../context/AuthContext";
import "./authScreen.css";

export default function AuthScreen() {
  const { loginWithGoogle, loading } = useAuth();
  const [error, setError] = useState(null);

  const handleSuccess = async (credentialResponse) => {
    setError(null);
    try {
      await loginWithGoogle(credentialResponse.credential);
    } catch (err) {
      console.error("Google login failed:", err);
      setError(err.message || "Failed to sign in. Please try again.");
    }
  };

  const handleError = () => {
    console.error("Google Sign-In was unsuccessful");
    setError("Google sign-in was cancelled or failed. Please try again.");
  };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <h1 className="auth-title">WellnessBot</h1>
        <p className="auth-subtitle">
          Your safe space for emotional support
        </p>

        <div className="auth-features">
          <div className="auth-feature">
            <span>Talk about how you feel</span>
          </div>
          <div className="auth-feature">
            <span>Get personalized coping strategies</span>
          </div>
          <div className="auth-feature">
            <span>Revisit past conversations</span>
          </div>
          <div className="auth-feature">
            <span>Private &amp; secure with auto-delete</span>
          </div>
        </div>

        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}

        <div className="auth-google-btn-wrapper">
          {loading ? (
            <div className="auth-loading">Signing in…</div>
          ) : (
            <GoogleLogin
              onSuccess={handleSuccess}
              onError={handleError}
              theme="outline"
              size="large"
              text="continue_with"
              shape="pill"
              width="300"
            />
          )}
        </div>

        <p className="auth-disclaimer">
          Not a substitute for professional mental health care.
          <br />
          Conversations auto-delete after 30 days.
        </p>
      </div>
    </div>
  );
}
