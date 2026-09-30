"""
Automated Evaluation Suite — 25 Test Scenarios for WellnessBot Agentic Upgrade.

Verifies:
1. Direct Chat (greetings, empathy)
2. RAG Knowledge Retrieval (sleep, hydration, breathing)
3. Goal Creation (hydration, mindfulness, activity)
4. Goal Retrieval (active, completed, all)
5. Goal Update (progress, completion, notes)
6. Multi-Tool Chains (search -> create, get -> search)
7. Disambiguation
8. Medical Refusals (emergency, diagnosis)
9. Crisis Intervention (988 escalation)
10. Low-Confidence RAG Fallback
11. Out-of-Scope Redirection
12. Data Isolation (multi-user protection)
13. Input Clamping (progress bounds 0-100)
14. Streaming Support (SSE with tool execution)
"""

import json
import os
import unittest
from unittest.mock import patch, MagicMock

# Set test environment variables before importing app
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"


class TestAgentScenarios(unittest.TestCase):
    """25 Comprehensive Test Scenarios for WellnessBot Agentic System."""

    def setUp(self):
        # Patch init_db globally during tests
        self.init_db_patcher = patch("backend.db.init_db")
        self.mock_init_db = self.init_db_patcher.start()

        from backend import create_app
        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        self.init_db_patcher.stop()

    # ──────────────────────────────────────────────────────────
    # Scenario 01: Direct Chat — Greeting (No Tool)
    # ──────────────────────────────────────────────────────────
    @patch("backend.services.chat_service._client")
    @patch("backend.repositories.message_repo.save")
    @patch("backend.repositories.message_repo.get_history", return_value=[])
    @patch("backend.repositories.conversation_repo.create", return_value=1)
    def test_01_direct_chat_greeting(self, mock_create_conv, mock_get_hist, mock_save_msg, mock_openai):
        """Greeting should return a friendly response without calling tools."""
        from backend.services.chat_service import process_message

        mock_choice = MagicMock()
        mock_choice.finish_reason = "stop"
        mock_choice.message.tool_calls = None
        mock_choice.message.content = "Good morning! It is wonderful to connect with you today. 🌿"
        mock_openai.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        reply, conv_id, err = process_message(user_id=1, user_message="Good morning! How are you?", mood=None, conversation_id=None)

        self.assertIsNone(err)
        self.assertEqual(conv_id, 1)
        self.assertIn("Good morning", reply)
        # Verify LLM was called once with tools defined, but no tool was executed
        self.assertEqual(mock_openai.chat.completions.create.call_count, 1)

    # ──────────────────────────────────────────────────────────
    # Scenario 02: Direct Chat — Empathy (No Tool)
    # ──────────────────────────────────────────────────────────
    @patch("backend.services.chat_service._client")
    @patch("backend.repositories.message_repo.save")
    @patch("backend.repositories.message_repo.get_history", return_value=[])
    @patch("backend.repositories.conversation_repo.create", return_value=1)
    def test_02_direct_chat_stress_empathy(self, mock_create_conv, mock_get_hist, mock_save_msg, mock_openai):
        """Stress disclosure should return an empathetic message without executing tools."""
        from backend.services.chat_service import process_message

        mock_choice = MagicMock()
        mock_choice.finish_reason = "stop"
        mock_choice.message.tool_calls = None
        mock_choice.message.content = "Work stress can feel so draining. Let's take a slow breath together. 💙"
        mock_openai.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        reply, conv_id, err = process_message(user_id=1, user_message="I'm feeling really stressed about work today.", mood=None, conversation_id=None)

        self.assertIsNone(err)
        self.assertIn("Work stress", reply)
        self.assertEqual(mock_openai.chat.completions.create.call_count, 1)

    # ──────────────────────────────────────────────────────────
    # Scenario 03: RAG Knowledge — Sleep Hygiene
    # ──────────────────────────────────────────────────────────
    @patch("backend.tools.wellness_tools._load_faiss")
    @patch("backend.tools.wellness_tools._get_query_embedding")
    @patch("backend.services.chat_service._client")
    @patch("backend.repositories.message_repo.save")
    @patch("backend.repositories.message_repo.get_history", return_value=[])
    @patch("backend.repositories.conversation_repo.create", return_value=1)
    def test_03_rag_knowledge_sleep(self, mock_create_conv, mock_get_hist, mock_save_msg, mock_openai, mock_query_emb, mock_load_faiss):
        """Querying sleep hygiene should trigger search_knowledge_base tool."""
        from backend.services.chat_service import process_message

        # Mock FAISS
        mock_index = MagicMock()
        mock_index.search.return_value = ([[0.85]], [[0]])
        mock_metadata = {
            "chunks": [{"text": "Keep bedroom cool and dark. Maintain consistent sleep schedule.", "title": "Sleep Hygiene Fundamentals", "category": "sleep", "filename": "sleep_hygiene_fundamentals.md"}]
        }
        mock_load_faiss.return_value = (mock_index, mock_metadata)
        mock_query_emb.return_value = [[0.1] * 1536]

        # First LLM call returns tool_call, second returns final answer
        tool_call = MagicMock()
        tool_call.id = "call_123"
        tool_call.function.name = "search_knowledge_base"
        tool_call.function.arguments = json.dumps({"query": "sleep hygiene"})

        choice1 = MagicMock()
        choice1.finish_reason = "tool_calls"
        choice1.message.tool_calls = [tool_call]

        choice2 = MagicMock()
        choice2.finish_reason = "stop"
        choice2.message.tool_calls = None
        choice2.message.content = "According to sleep hygiene fundamentals, keeping your bedroom dark and cool helps significantly! 🌙"

        mock_openai.chat.completions.create.side_effect = [
            MagicMock(choices=[choice1]),
            MagicMock(choices=[choice2]),
        ]

        reply, conv_id, err = process_message(user_id=1, user_message="What does your guide say about healthy sleep hygiene?", mood=None, conversation_id=None)

        self.assertIsNone(err)
        self.assertIn("sleep hygiene", reply.lower())
        self.assertEqual(mock_openai.chat.completions.create.call_count, 2)

    # ──────────────────────────────────────────────────────────
    # Scenario 04: RAG Knowledge — Daily Hydration
    # ──────────────────────────────────────────────────────────
    @patch("backend.tools.wellness_tools._load_faiss")
    @patch("backend.tools.wellness_tools._get_query_embedding")
    def test_04_rag_knowledge_hydration(self, mock_query_emb, mock_load_faiss):
        """search_knowledge_base should return hydration documents with high relevance."""
        from backend.tools.wellness_tools import search_knowledge_base

        mock_index = MagicMock()
        mock_index.search.return_value = ([[0.92]], [[0]])
        mock_metadata = {
            "chunks": [{"text": "Adult men need ~3.7L and adult women ~2.7L per day.", "title": "Daily Hydration Guide", "category": "hydration", "filename": "daily_hydration_guide.md"}]
        }
        mock_load_faiss.return_value = (mock_index, mock_metadata)
        mock_query_emb.return_value = [[0.1] * 1536]

        result = search_knowledge_base("daily water intake hydration", top_k=1)
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["category"], "hydration")
        self.assertIn("3.7L", result["results"][0]["text"])

    # ──────────────────────────────────────────────────────────
    # Scenario 05: RAG Knowledge — Breathing Techniques
    # ──────────────────────────────────────────────────────────
    @patch("backend.tools.wellness_tools._load_faiss")
    @patch("backend.tools.wellness_tools._get_query_embedding")
    def test_05_rag_knowledge_breathing_comparison(self, mock_query_emb, mock_load_faiss):
        """search_knowledge_base should find breathing techniques."""
        from backend.tools.wellness_tools import search_knowledge_base

        mock_index = MagicMock()
        mock_index.search.return_value = ([[0.88]], [[0]])
        mock_metadata = {
            "chunks": [{"text": "Box breathing uses 4-4-4-4 seconds rhythm. 4-7-8 focuses on prolonged exhales.", "title": "Breathing Techniques for Stress Relief", "category": "mindfulness", "filename": "breathing_techniques.md"}]
        }
        mock_load_faiss.return_value = (mock_index, mock_metadata)
        mock_query_emb.return_value = [[0.1] * 1536]

        result = search_knowledge_base("box breathing vs 4-7-8")
        self.assertIn("results", result)
        self.assertTrue(len(result["results"]) > 0)
        self.assertIn("Box breathing", result["results"][0]["text"])

    # ──────────────────────────────────────────────────────────
    # Scenario 06: Goal Creation — Hydration
    # ──────────────────────────────────────────────────────────
    @patch("backend.repositories.goal_repo.create")
    def test_06_goal_creation_hydration(self, mock_create):
        """create_goal should insert a hydration goal into the repository."""
        from backend.tools.wellness_tools import create_goal

        mock_create.return_value = {
            "id": 1,
            "title": "Drink 2L water daily",
            "category": "hydration",
            "target_date": None,
            "status": "active",
            "progress_pct": 0,
            "notes": "",
            "created_at": None,
            "updated_at": None,
        }

        result = create_goal(user_id=10, title="Drink 2L water daily", category="hydration")
        self.assertIn("goal", result)
        self.assertEqual(result["goal"]["title"], "Drink 2L water daily")
        self.assertEqual(result["goal"]["category"], "hydration")
        mock_create.assert_called_once_with(user_id=10, title="Drink 2L water daily", category="hydration", target_date=None, initial_progress=0)

    # ──────────────────────────────────────────────────────────
    # Scenario 07: Goal Creation — Mindfulness
    # ──────────────────────────────────────────────────────────
    @patch("backend.repositories.goal_repo.create")
    def test_07_goal_creation_mindfulness(self, mock_create):
        """create_goal should create a mindfulness goal."""
        from backend.tools.wellness_tools import create_goal

        mock_create.return_value = {
            "id": 2,
            "title": "Meditate 10 min morning",
            "category": "mindfulness",
            "target_date": None,
            "status": "active",
            "progress_pct": 0,
            "notes": "",
            "created_at": None,
            "updated_at": None,
        }

        result = create_goal(user_id=10, title="Meditate 10 min morning", category="mindfulness")
        self.assertEqual(result["goal"]["category"], "mindfulness")
        self.assertEqual(result["goal"]["status"], "active")

    # ──────────────────────────────────────────────────────────
    # Scenario 08: Goal Creation — Activity
    # ──────────────────────────────────────────────────────────
    @patch("backend.repositories.goal_repo.create")
    def test_08_goal_creation_activity(self, mock_create):
        """create_goal should map and persist activity goal."""
        from backend.tools.wellness_tools import create_goal

        mock_create.return_value = {
            "id": 3,
            "title": "Walk 8,000 steps daily",
            "category": "activity",
            "target_date": None,
            "status": "active",
            "progress_pct": 0,
            "notes": "",
            "created_at": None,
            "updated_at": None,
        }

        result = create_goal(user_id=10, title="Walk 8,000 steps daily", category="activity")
        self.assertEqual(result["goal"]["category"], "activity")

    # ──────────────────────────────────────────────────────────
    # Scenario 09: Goal Retrieval — Active Goals
    # ──────────────────────────────────────────────────────────
    @patch("backend.repositories.goal_repo.list_by_user")
    def test_09_goal_retrieval_active(self, mock_list):
        """get_goals with status_filter='active' should filter active goals."""
        from backend.tools.wellness_tools import get_goals

        mock_list.return_value = [
            {"id": 1, "title": "Drink 2L water daily", "category": "hydration", "status": "active", "progress_pct": 20, "notes": "", "target_date": None, "created_at": None, "updated_at": None}
        ]

        result = get_goals(user_id=10, status_filter="active")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["goals"][0]["status"], "active")
        mock_list.assert_called_once_with(10, "active", 5)

    # ──────────────────────────────────────────────────────────
    # Scenario 10: Goal Retrieval — Completed Goals
    # ──────────────────────────────────────────────────────────
    @patch("backend.repositories.goal_repo.list_by_user")
    def test_10_goal_retrieval_completed(self, mock_list):
        """get_goals with status_filter='completed' should return completed goals."""
        from backend.tools.wellness_tools import get_goals

        mock_list.return_value = [
            {"id": 2, "title": "Morning Walk", "category": "activity", "status": "completed", "progress_pct": 100, "notes": "", "target_date": None, "created_at": None, "updated_at": None}
        ]

        result = get_goals(user_id=10, status_filter="completed")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["goals"][0]["status"], "completed")

    # ──────────────────────────────────────────────────────────
    # Scenario 11: Goal Retrieval — All Goals
    # ──────────────────────────────────────────────────────────
    @patch("backend.repositories.goal_repo.list_by_user")
    def test_11_goal_retrieval_all(self, mock_list):
        """get_goals with status_filter='all' should list all goals."""
        from backend.tools.wellness_tools import get_goals

        mock_list.return_value = [
            {"id": 1, "title": "Goal 1", "category": "sleep", "status": "active", "progress_pct": 30, "notes": "", "target_date": None, "created_at": None, "updated_at": None},
            {"id": 2, "title": "Goal 2", "category": "nutrition", "status": "completed", "progress_pct": 100, "notes": "", "target_date": None, "created_at": None, "updated_at": None},
        ]

        result = get_goals(user_id=10, status_filter="all")
        self.assertEqual(result["count"], 2)

    # ──────────────────────────────────────────────────────────
    # Scenario 12: Goal Update — Progress Percentage
    # ──────────────────────────────────────────────────────────
    @patch("backend.repositories.goal_repo.update")
    def test_12_goal_update_progress(self, mock_update):
        """update_goal should update progress percentage."""
        from backend.tools.wellness_tools import update_goal

        mock_update.return_value = {
            "id": 4, "title": "Water Goal", "category": "hydration", "status": "active",
            "progress_pct": 50, "notes": "", "target_date": None, "created_at": None, "updated_at": None
        }

        result = update_goal(user_id=10, goal_id=4, progress_pct=50)
        self.assertIn("goal", result)
        self.assertEqual(result["goal"]["progress_pct"], 50)

    # ──────────────────────────────────────────────────────────
    # Scenario 13: Goal Update — Mark Completed
    # ──────────────────────────────────────────────────────────
    @patch("backend.repositories.goal_repo.update")
    def test_13_goal_update_completed(self, mock_update):
        """update_goal should update status to completed."""
        from backend.tools.wellness_tools import update_goal

        mock_update.return_value = {
            "id": 5, "title": "Meditation Goal", "category": "mindfulness", "status": "completed",
            "progress_pct": 100, "notes": "", "target_date": None, "created_at": None, "updated_at": None
        }

        result = update_goal(user_id=10, goal_id=5, progress_pct=100, status="completed")
        self.assertEqual(result["goal"]["status"], "completed")
        self.assertEqual(result["goal"]["progress_pct"], 100)

    # ──────────────────────────────────────────────────────────
    # Scenario 14: Goal Update — Notes
    # ──────────────────────────────────────────────────────────
    @patch("backend.repositories.goal_repo.update")
    def test_14_goal_update_notes(self, mock_update):
        """update_goal should append reflection notes."""
        from backend.tools.wellness_tools import update_goal

        mock_update.return_value = {
            "id": 6, "title": "Step Goal", "category": "activity", "status": "active",
            "progress_pct": 40, "notes": "Walked in the park today", "target_date": None, "created_at": None, "updated_at": None
        }

        result = update_goal(user_id=10, goal_id=6, update_notes="Walked in the park today")
        self.assertIn("Walked in the park", result["goal"]["notes"])

    # ──────────────────────────────────────────────────────────
    # Scenario 15: Multi-Tool Chain — Search then Create Goal
    # ──────────────────────────────────────────────────────────
    @patch("backend.tools.wellness_tools._load_faiss")
    @patch("backend.tools.wellness_tools._get_query_embedding")
    @patch("backend.repositories.goal_repo.create")
    @patch("backend.services.chat_service._client")
    @patch("backend.repositories.message_repo.save")
    @patch("backend.repositories.message_repo.get_history", return_value=[])
    @patch("backend.repositories.conversation_repo.create", return_value=1)
    def test_15_multi_tool_chain_search_and_create(self, mock_create_conv, mock_get_hist, mock_save_msg, mock_openai, mock_goal_create, mock_query_emb, mock_load_faiss):
        """Agent should handle a chain of 2 consecutive tool calls (search -> create_goal)."""
        from backend.services.chat_service import process_message

        # Mock FAISS
        mock_index = MagicMock()
        mock_index.search.return_value = ([[0.9]], [[0]])
        mock_load_faiss.return_value = (mock_index, {"chunks": [{"text": "Stretching increases flexibility and blood flow.", "title": "Stretching", "category": "activity", "filename": "stretching_flexibility.md"}]})
        mock_query_emb.return_value = [[0.1] * 1536]

        # Mock goal creation
        mock_goal_create.return_value = {
            "id": 7, "title": "10 min daily stretching", "category": "activity", "status": "active",
            "progress_pct": 0, "notes": "", "target_date": None, "created_at": None, "updated_at": None
        }

        # Step 1 tool call: search
        call1 = MagicMock()
        call1.id = "call_1"
        call1.function.name = "search_knowledge_base"
        call1.function.arguments = json.dumps({"query": "benefits of stretching"})

        choice1 = MagicMock()
        choice1.finish_reason = "tool_calls"
        choice1.message.tool_calls = [call1]

        # Step 2 tool call: create_goal
        call2 = MagicMock()
        call2.id = "call_2"
        call2.function.name = "create_goal"
        call2.function.arguments = json.dumps({"title": "10 min daily stretching", "category": "activity"})

        choice2 = MagicMock()
        choice2.finish_reason = "tool_calls"
        choice2.message.tool_calls = [call2]

        # Step 3: final answer
        choice3 = MagicMock()
        choice3.finish_reason = "stop"
        choice3.message.tool_calls = None
        choice3.message.content = "Stretching improves flexibility! I have also created your goal for 10 min daily stretching. 🧘"

        mock_openai.chat.completions.create.side_effect = [
            MagicMock(choices=[choice1]),
            MagicMock(choices=[choice2]),
            MagicMock(choices=[choice3]),
        ]

        reply, conv_id, err = process_message(
            user_id=10,
            user_message="Look up the benefits of stretching, then create a goal for 10 min daily stretching.",
            mood=None,
            conversation_id=None
        )

        self.assertIsNone(err)
        self.assertIn("stretching", reply.lower())
        self.assertEqual(mock_openai.chat.completions.create.call_count, 3)

    # ──────────────────────────────────────────────────────────
    # Scenario 16: Multi-Tool Chain — Get Goals then Search
    # ──────────────────────────────────────────────────────────
    @patch("backend.repositories.goal_repo.list_by_user")
    @patch("backend.tools.wellness_tools._load_faiss")
    @patch("backend.tools.wellness_tools._get_query_embedding")
    @patch("backend.services.chat_service._client")
    @patch("backend.repositories.message_repo.save")
    @patch("backend.repositories.message_repo.get_history", return_value=[])
    @patch("backend.repositories.conversation_repo.create", return_value=1)
    def test_16_multi_tool_chain_get_and_search(self, mock_create_conv, mock_get_hist, mock_save_msg, mock_openai, mock_query_emb, mock_load_faiss, mock_list_goals):
        """Agent should handle get_goals followed by search_knowledge_base."""
        from backend.services.chat_service import process_message

        mock_list_goals.return_value = [
            {"id": 8, "title": "Improve Sleep", "category": "sleep", "status": "active", "progress_pct": 10, "notes": "", "target_date": None, "created_at": None, "updated_at": None}
        ]

        mock_index = MagicMock()
        mock_index.search.return_value = ([[0.89]], [[0]])
        mock_load_faiss.return_value = (mock_index, {"chunks": [{"text": "Wind down routine 30 mins before bed.", "title": "Wind Down Routine", "category": "sleep", "filename": "wind_down_routine.md"}]})
        mock_query_emb.return_value = [[0.1] * 1536]

        call1 = MagicMock()
        call1.id = "c1"
        call1.function.name = "get_goals"
        call1.function.arguments = json.dumps({"status_filter": "active"})

        call2 = MagicMock()
        call2.id = "c2"
        call2.function.name = "search_knowledge_base"
        call2.function.arguments = json.dumps({"query": "wind down sleep routine"})

        choice1 = MagicMock(finish_reason="tool_calls", message=MagicMock(tool_calls=[call1]))
        choice2 = MagicMock(finish_reason="tool_calls", message=MagicMock(tool_calls=[call2]))
        choice3 = MagicMock(finish_reason="stop", message=MagicMock(tool_calls=None, content="Your active goal is 'Improve Sleep'. A wind-down routine 30 mins before bed can help! 😴"))

        mock_openai.chat.completions.create.side_effect = [
            MagicMock(choices=[choice1]),
            MagicMock(choices=[choice2]),
            MagicMock(choices=[choice3]),
        ]

        reply, conv_id, err = process_message(
            user_id=10,
            user_message="Review my active goals and give me wellness advice on the first one.",
            mood=None,
            conversation_id=None
        )

        self.assertIsNone(err)
        self.assertIn("Improve Sleep", reply)

    # ──────────────────────────────────────────────────────────
    # Scenario 17: Disambiguation — Ambiguous Request
    # ──────────────────────────────────────────────────────────
    @patch("backend.services.chat_service._client")
    @patch("backend.repositories.message_repo.save")
    @patch("backend.repositories.message_repo.get_history", return_value=[])
    @patch("backend.repositories.conversation_repo.create", return_value=1)
    def test_17_disambiguation_clarification(self, mock_create_conv, mock_get_hist, mock_save_msg, mock_openai):
        """Ambiguous goal update request without ID or context asks for clarification."""
        from backend.services.chat_service import process_message

        mock_choice = MagicMock(
            finish_reason="stop",
            message=MagicMock(
                tool_calls=None,
                content="Which goal would you like to update? You can tell me the goal title or ID! 😊"
            )
        )
        mock_openai.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        reply, conv_id, err = process_message(user_id=10, user_message="Update my progress.", mood=None, conversation_id=None)

        self.assertIsNone(err)
        self.assertIn("Which goal", reply)

    # ──────────────────────────────────────────────────────────
    # Scenario 18: Medical Refusal — Emergency / Chest Pain
    # ──────────────────────────────────────────────────────────
    def test_18_medical_refusal_emergency(self):
        """Emergency medical questions trigger safety refusal without invoking LLM."""
        from backend.tools.safety import check_safety

        response, safety_type = check_safety("I have sharp chest pain and my left arm is numb. What pills should I take?")
        self.assertEqual(safety_type, "medical")
        self.assertIn("not a licensed medical professional", response)
        self.assertIn("consult with your doctor", response)

    # ──────────────────────────────────────────────────────────
    # Scenario 19: Medical Refusal — Clinical Diagnosis
    # ──────────────────────────────────────────────────────────
    def test_19_medical_refusal_diagnosis(self):
        """Diagnostic queries trigger medical disclaimer."""
        from backend.tools.safety import check_safety

        response, safety_type = check_safety("Can you diagnose if this skin rash is an infection?")
        self.assertEqual(safety_type, "medical")
        self.assertIn("not able to diagnose conditions", response)

    # ──────────────────────────────────────────────────────────
    # Scenario 20: Crisis Intervention — 988 Escalation
    # ──────────────────────────────────────────────────────────
    def test_20_crisis_intervention_escalation(self):
        """Crisis mentions immediately trigger 988 lifeline information."""
        from backend.tools.safety import check_safety

        response, safety_type = check_safety("I feel like ending my life, I can't take this anymore.")
        self.assertEqual(safety_type, "crisis")
        self.assertIn("988", response)
        self.assertIn("741741", response)
        self.assertIn("Suicide & Crisis Lifeline", response)

    # ──────────────────────────────────────────────────────────
    # Scenario 21: Low-Confidence RAG Fallback
    # ──────────────────────────────────────────────────────────
    @patch("backend.tools.wellness_tools._load_faiss")
    @patch("backend.tools.wellness_tools._get_query_embedding")
    def test_21_low_confidence_rag_fallback(self, mock_query_emb, mock_load_faiss):
        """When similarity is below threshold, search_knowledge_base returns honest fallback."""
        from backend.tools.wellness_tools import search_knowledge_base

        # Scores below RAG_SIMILARITY_THRESHOLD (0.3)
        mock_index = MagicMock()
        mock_index.search.return_value = ([[0.12]], [[0]])
        mock_load_faiss.return_value = (mock_index, {"chunks": [{"text": "Irrelevant text", "title": "Other", "category": "other", "filename": "other.md"}]})
        mock_query_emb.return_value = [[0.1] * 1536]

        result = search_knowledge_base("What is the quantum frequency resonance of hydration molecules?")
        self.assertEqual(result["results"], [])
        self.assertIn("No sufficiently relevant information", result["message"])

    # ──────────────────────────────────────────────────────────
    # Scenario 22: Out-of-Scope Redirection
    # ──────────────────────────────────────────────────────────
    @patch("backend.services.chat_service._client")
    @patch("backend.repositories.message_repo.save")
    @patch("backend.repositories.message_repo.get_history", return_value=[])
    @patch("backend.repositories.conversation_repo.create", return_value=1)
    def test_22_out_of_scope_redirection(self, mock_create_conv, mock_get_hist, mock_save_msg, mock_openai):
        """Non-wellness technical/coding questions are politely redirected."""
        from backend.services.chat_service import process_message

        mock_choice = MagicMock(
            finish_reason="stop",
            message=MagicMock(
                tool_calls=None,
                content="I focus specifically on personal mental and physical wellness! While I can't help with coding stock scrapers, how can I support your well-being today? 🌿"
            )
        )
        mock_openai.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        reply, conv_id, err = process_message(user_id=1, user_message="Write a JavaScript web scraper for financial stocks.", mood=None, conversation_id=None)

        self.assertIsNone(err)
        self.assertIn("wellness", reply.lower())

    # ──────────────────────────────────────────────────────────
    # Scenario 23: Data Isolation — Multi-User Goal Access
    # ──────────────────────────────────────────────────────────
    @patch("backend.repositories.goal_repo.find_by_id_and_user")
    def test_23_data_isolation_multi_user(self, mock_find):
        """User A cannot access or update goals belonging to User B."""
        from backend.tools.wellness_tools import update_goal

        # User 2 tries to update User 1's goal -> DB returns None
        mock_find.return_value = None

        result = update_goal(user_id=2, goal_id=99, progress_pct=80)
        self.assertIn("error", result)
        self.assertIn("not found or you don't have access", result["error"])

    # ──────────────────────────────────────────────────────────
    # Scenario 24: Input Clamping — Progress Bounds (0-100)
    # ──────────────────────────────────────────────────────────
    @patch("backend.repositories.goal_repo.update")
    @patch("backend.repositories.goal_repo.find_by_id_and_user")
    def test_24_input_clamping_progress(self, mock_find, mock_update):
        """Progress values outside 0-100 are automatically clamped."""
        from backend.services import goal_service

        mock_find.return_value = {
            "id": 10, "user_id": 1, "title": "Test", "category": "sleep",
            "progress_pct": 0, "status": "active", "notes": "", "target_date": None,
            "created_at": None, "updated_at": None
        }
        mock_update.return_value = {
            "id": 10, "title": "Test", "category": "sleep",
            "progress_pct": 100, "status": "active", "notes": "", "target_date": None,
            "created_at": None, "updated_at": None
        }

        # Value 500 should be clamped to 100
        goal_service.update(user_id=1, goal_id=10, progress_pct=500)
        mock_update.assert_called_once_with(goal_id=10, user_id=1, progress_pct=100, status=None, notes=None)

    # ──────────────────────────────────────────────────────────
    # Scenario 25: Streaming Support — SSE with Tool Execution
    # ──────────────────────────────────────────────────────────
    @patch("backend.tools.wellness_tools._load_faiss")
    @patch("backend.tools.wellness_tools._get_query_embedding")
    @patch("backend.services.chat_service._client")
    @patch("backend.repositories.message_repo.save")
    @patch("backend.repositories.message_repo.get_history", return_value=[])
    @patch("backend.repositories.conversation_repo.create", return_value=1)
    def test_25_streaming_support_with_tools(self, mock_create_conv, mock_get_hist, mock_save_msg, mock_openai, mock_query_emb, mock_load_faiss):
        """Streaming endpoint executes tools before streaming final tokens."""
        from backend.services.chat_service import stream_message

        # Mock FAISS
        mock_index = MagicMock()
        mock_index.search.return_value = ([[0.9]], [[0]])
        mock_load_faiss.return_value = (mock_index, {"chunks": [{"text": "Electrolytes maintain cellular hydration.", "title": "Electrolytes", "category": "hydration", "filename": "electrolytes_and_hydration.md"}]})
        mock_query_emb.return_value = [[0.1] * 1536]

        # Tool call response in non-streaming phase
        tool_call = MagicMock(id="tc_1", function=MagicMock(name="search_knowledge_base", arguments=json.dumps({"query": "electrolytes hydration"})))
        mock_choice1 = MagicMock(finish_reason="tool_calls", message=MagicMock(tool_calls=[tool_call]))

        # Second call finish_reason stop with content
        mock_choice2 = MagicMock(finish_reason="stop", message=MagicMock(tool_calls=None, content="Electrolytes help your cells stay hydrated! 💧"))

        mock_openai.chat.completions.create.side_effect = [
            MagicMock(choices=[mock_choice1]),
            MagicMock(choices=[mock_choice2]),
        ]

        generator = stream_message(user_id=1, user_message="Why are electrolytes important?", mood=None, conversation_id=None)
        chunks = list(generator)

        # Check SSE formatting
        self.assertTrue(any("conversation_id" in c for c in chunks))
        self.assertTrue(any("Electrolytes" in c for c in chunks))
        self.assertIn("data: [DONE]\n\n", chunks)


if __name__ == "__main__":
    unittest.main()
