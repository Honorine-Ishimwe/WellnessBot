/**
 * API Client — shared fetch wrapper for all API calls.
 * Centralizes base URL, auth headers, and error handling.
 */

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:5001";
const TOKEN_KEY = "wellnessbot_token";

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  constructor(status, data) {
    super(data?.error || `HTTP ${status}`);
    this.status = status;
    this.data = data;
  }
}

/**
 * Get the stored auth token.
 */
function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Make an authenticated API request.
 * Automatically attaches JWT and Content-Type headers.
 *
 * @param {string} path - API path (e.g., "/chat")
 * @param {object} options - Fetch options (method, body, headers, etc.)
 * @returns {Promise<Response>}
 */
export async function apiFetch(path, options = {}) {
  const token = getToken();

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  return res;
}

/**
 * Make an authenticated API request and parse JSON.
 * Throws ApiError on non-OK responses.
 *
 * @param {string} path - API path
 * @param {object} options - Fetch options
 * @returns {Promise<any>} Parsed JSON response
 */
export async function apiJson(path, options = {}) {
  const res = await apiFetch(path, options);

  if (!res.ok) {
    let data = {};
    try {
      data = await res.json();
    } catch {
      // ignore parse errors
    }
    throw new ApiError(res.status, data);
  }

  return res.json();
}

/**
 * Get the raw API URL (for streaming endpoints that need direct fetch).
 */
export function getApiUrl() {
  return API_URL;
}

export { TOKEN_KEY };
