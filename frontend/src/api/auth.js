/**
 * Auth API — authentication-related API calls.
 */

import { getApiUrl } from "./client";

const API_URL = getApiUrl();

/**
 * Send a Google credential to the backend for verification.
 * Returns { token, user } on success.
 *
 * @param {string} credential - Google ID token
 * @returns {Promise<{token: string, user: object}>}
 */
export async function googleLogin(credential) {
  const res = await fetch(`${API_URL}/auth/google`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ credential }),
  });

  if (!res.ok) {
    let errMessage = "Login failed";
    try {
      const data = await res.json();
      errMessage = data.error || errMessage;
    } catch {
      // ignore
    }
    throw new Error(errMessage);
  }

  return res.json();
}

/**
 * Get the current user's profile.
 *
 * @param {string} token - JWT token
 * @returns {Promise<{user: object}>}
 */
export async function getMe(token) {
  const res = await fetch(`${API_URL}/auth/me`, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    throw new Error("Failed to fetch profile");
  }

  return res.json();
}
