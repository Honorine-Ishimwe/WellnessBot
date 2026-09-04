"""
Backend tests for WellnessBot.
Uses mocked OpenAI and database connections.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Set test environment variables before importing app
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"


class TestHealthEndpoint(unittest.TestCase):
    """Test the /health endpoint."""

    @patch("backend.init_db")
    def test_health_returns_ok(self, mock_init_db):
        from backend import app
        with app.test_client() as client:
            response = client.get("/health")
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["status"], "ok")


class TestChatEndpoint(unittest.TestCase):
    """Test the /chat endpoint."""

    @patch("backend.init_db")
    def setUp(self, mock_init_db):
        from backend import app
        self.app = app
        self.client = app.test_client()

    def test_chat_requires_auth(self):
        """Chat endpoint should return 401 without auth."""
        response = self.client.post(
            "/chat",
            data=json.dumps({"message": "hello"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    @patch("auth._verify_jwt")
    @patch("backend.query")
    @patch("backend.execute")
    @patch("backend.client")
    def test_chat_with_auth(self, mock_openai, mock_execute, mock_query, mock_verify):
        """Chat endpoint should return a reply when authenticated."""
        # Mock JWT verification
        mock_verify.return_value = {"user_id": 1, "email": "test@test.com"}

        # Mock DB queries
        mock_query.side_effect = [
            {"id": 1},  # INSERT conversation RETURNING id
            [],          # SELECT messages
        ]

        # Mock OpenAI response
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Hello! How are you? 💙"
        mock_openai.chat.completions.create.return_value = mock_completion

        response = self.client.post(
            "/chat",
            data=json.dumps({"message": "I'm feeling stressed"}),
            content_type="application/json",
            headers={"Authorization": "Bearer valid-token"},
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("reply", data)
        self.assertIn("conversation_id", data)

    def test_chat_empty_message(self):
        """Chat should handle empty messages gracefully."""
        with patch("auth._verify_jwt", return_value={"user_id": 1, "email": "t@t.com"}):
            response = self.client.post(
                "/chat",
                data=json.dumps({"message": ""}),
                content_type="application/json",
                headers={"Authorization": "Bearer valid-token"},
            )
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertIn("didn't catch that", data["reply"])


class TestInputValidation(unittest.TestCase):
    """Test input sanitization."""

    @patch("backend.init_db")
    def test_sanitize_strips_html(self, mock_init_db):
        from backend import sanitize_input
        result = sanitize_input("<script>alert('xss')</script>Hello")
        self.assertEqual(result, "alert('xss')Hello")

    @patch("backend.init_db")
    def test_sanitize_limits_length(self, mock_init_db):
        from backend import sanitize_input, MAX_MESSAGE_LENGTH
        long_input = "a" * 5000
        result = sanitize_input(long_input)
        self.assertEqual(len(result), MAX_MESSAGE_LENGTH)


class TestAuthEndpoint(unittest.TestCase):
    """Test the /auth/google endpoint."""

    @patch("backend.init_db")
    def setUp(self, mock_init_db):
        from backend import app
        self.app = app
        self.client = app.test_client()

    def test_google_auth_requires_credential(self):
        """Should return 400 without a credential."""
        response = self.client.post(
            "/auth/google",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("auth.id_token.verify_oauth2_token")
    @patch("auth.query")
    def test_google_auth_success(self, mock_query, mock_verify_token):
        """Should create user and return JWT on valid Google token."""
        mock_verify_token.return_value = {
            "sub": "google-123",
            "email": "test@gmail.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
        }

        # First query: find user (not found)
        # Second query: insert user (returns new user)
        mock_query.side_effect = [
            None,  # SELECT user (not found)
            {"id": 1, "email": "test@gmail.com", "display_name": "Test User", "avatar_url": "https://example.com/photo.jpg"},
        ]

        response = self.client.post(
            "/auth/google",
            data=json.dumps({"credential": "valid-google-token"}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], "test@gmail.com")


class TestConversationEndpoints(unittest.TestCase):
    """Test conversation CRUD endpoints."""

    @patch("backend.init_db")
    def setUp(self, mock_init_db):
        from backend import app
        self.app = app
        self.client = app.test_client()

    @patch("auth._verify_jwt")
    @patch("backend.query")
    def test_list_conversations(self, mock_query, mock_verify):
        """Should return user's conversations."""
        mock_verify.return_value = {"user_id": 1, "email": "t@t.com"}
        mock_query.return_value = []

        response = self.client.get(
            "/conversations",
            headers={"Authorization": "Bearer valid-token"},
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("conversations", data)

    @patch("auth._verify_jwt")
    @patch("backend.query")
    def test_get_conversation_not_found(self, mock_query, mock_verify):
        """Should return 404 for non-existent conversation."""
        mock_verify.return_value = {"user_id": 1, "email": "t@t.com"}
        mock_query.return_value = None  # conversation not found

        response = self.client.get(
            "/conversations/999",
            headers={"Authorization": "Bearer valid-token"},
        )
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
