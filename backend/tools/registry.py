"""
Tool registry — defines tool schemas for OpenAI function calling
and dispatches tool executions.
"""

from backend.tools.wellness_tools import (
    search_knowledge_base,
    create_goal,
    get_goals,
    update_goal,
)

# ── OpenAI-format tool definitions ────────────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the curated wellness knowledge library for evidence-based "
                "information on sleep, hydration, mindfulness, nutrition, activity, "
                "and general wellness topics. Use this tool when the user asks for "
                "factual health/wellness advice, tips, or information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query describing what information to find.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of document chunks to retrieve (default 3).",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_goal",
            "description": (
                "Create and save a new wellness goal for the user. Use this when "
                "the user wants to set, track, or start a new health/wellness goal."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short descriptive name of the goal (e.g. 'Drink 8 glasses of water daily').",
                    },
                    "category": {
                        "type": "string",
                        "enum": ["sleep", "hydration", "mindfulness", "activity", "nutrition", "other"],
                        "description": "The wellness category this goal belongs to.",
                    },
                    "target_date": {
                        "type": "string",
                        "description": "Optional target date in YYYY-MM-DD format.",
                    },
                    "initial_progress": {
                        "type": "integer",
                        "description": "Initial progress percentage (0-100, default 0).",
                    },
                },
                "required": ["title", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_goals",
            "description": (
                "Retrieve the user's saved wellness goals. Use this when the user "
                "asks about their current goals, progress, or wants to review what "
                "they are working on."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "enum": ["active", "in_progress", "completed", "abandoned", "all"],
                        "description": "Filter goals by status (default 'active').",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of goals to return (default 5).",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_goal",
            "description": (
                "Update progress, status, or notes on an existing wellness goal. "
                "Use this when the user reports progress, wants to mark a goal as "
                "completed, or wants to add a note to a goal."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "integer",
                        "description": "The unique ID of the goal to update.",
                    },
                    "progress_pct": {
                        "type": "integer",
                        "description": "New progress percentage (0-100).",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "in_progress", "completed", "abandoned"],
                        "description": "New status for the goal.",
                    },
                    "update_notes": {
                        "type": "string",
                        "description": "Notes or reflections to add to the goal.",
                    },
                },
                "required": ["goal_id"],
            },
        },
    },
]


# ── Tool name → function mapping ──────────────────────

TOOL_MAP = {
    "search_knowledge_base": search_knowledge_base,
    "get_goals": get_goals,
    "create_goal": create_goal,
    "update_goal": update_goal,
}


def execute_tool(tool_name, arguments, user_id=None):
    """Execute a tool by name with the given arguments.

    user_id is injected server-side for all DB tools (never from the LLM).
    Returns a JSON-serializable result dict.
    """
    func = TOOL_MAP.get(tool_name)
    if func is None:
        return {"error": f"Unknown tool: {tool_name}"}

    # Inject user_id for tools that require it
    if tool_name in ("create_goal", "get_goals", "update_goal"):
        arguments["user_id"] = user_id

    try:
        return func(**arguments)
    except Exception as e:
        return {"error": str(e)}
