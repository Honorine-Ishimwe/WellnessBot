"""
Chat service — agent orchestration engine for WellnessBot.

Handles message building, tool-calling agent loop, and conversation
orchestration. Upgraded from single-shot completion to an iterative
agent that can invoke tools (RAG search, goal CRUD) autonomously.

No Flask imports — pure Python logic.
"""

import re
import json

from openai import OpenAI, RateLimitError, AuthenticationError, APIError

from backend.config import (
    SYSTEM_PROMPT,
    MAX_MESSAGE_LENGTH,
    MAX_HISTORY_MESSAGES,
    OPENAI_MODEL,
    OPENAI_MAX_TOKENS,
    OPENAI_TEMPERATURE,
    OPENAI_PRESENCE_PENALTY,
    OPENAI_FREQUENCY_PENALTY,
    MAX_TOOL_ITERATIONS,
)
from backend.repositories import conversation_repo, message_repo
from backend.services import conversation_service
from backend.middleware.logging import logger
from backend.tools.registry import TOOL_DEFINITIONS, execute_tool
from backend.tools.safety import check_safety

# ── OpenAI client (singleton) ────────────────────────
_client = OpenAI()


# ── Agent system prompt (extends the base prompt) ────

AGENT_SYSTEM_PROMPT = (
    SYSTEM_PROMPT + "\n\n"
    "--- TOOL USAGE GUIDELINES ---\n"
    "You have access to wellness tools. Use them wisely:\n"
    "- Use 'search_knowledge_base' ONLY when the user asks for factual wellness "
    "advice, tips, or information that you should ground in evidence. Do NOT use "
    "it for casual greetings, emotional support, or simple conversation.\n"
    "- Use 'create_goal' when the user wants to set or track a new wellness goal.\n"
    "- Use 'get_goals' when the user asks about their current goals or progress.\n"
    "- Use 'update_goal' when the user reports progress or wants to change a goal.\n"
    "- For casual chat, emotional support, greetings, or questions you can answer "
    "from general knowledge, respond directly WITHOUT calling any tools.\n"
    "- When using search results, base your answer on the retrieved information. "
    "Do NOT invent facts or statistics not present in the results.\n"
    "- If search results come back empty, honestly say you don't have specific "
    "information on that topic rather than making something up.\n"
    "- If the user's request is ambiguous about which goal to update, ask for "
    "clarification before calling update_goal.\n"
    "- NEVER answer questions unrelated to health, wellness, or the user's "
    "well-being. Politely redirect to wellness topics.\n"
)


def sanitize_input(text):
    """Strip HTML tags and limit length."""
    cleaned = re.sub(r"<[^>]+>", "", text)
    return cleaned[:MAX_MESSAGE_LENGTH]


def build_messages(mood, history, user_message):
    """Build the OpenAI messages list from conversation context."""
    messages = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}]

    if mood:
        messages.append({
            "role": "system",
            "content": f"The user's current mood: {mood}. Tailor your tone to this.",
        })

    # Include conversation history (limit to last N messages)
    for msg in history[-MAX_HISTORY_MESSAGES:]:
        role = "assistant" if msg.get("sender") == "bot" else "user"
        messages.append({"role": role, "content": msg.get("text", "")})

    messages.append({"role": "user", "content": user_message})
    return messages


def handle_openai_error(e):
    """Return a user-friendly error message and HTTP status based on error type."""
    if isinstance(e, RateLimitError):
        logger.warning(f"OpenAI rate limit hit: {e}")
        return (
            "I need a moment to catch my breath. Please try again in a few seconds. 💙",
            429,
        )
    elif isinstance(e, AuthenticationError):
        logger.error(f"OpenAI authentication error: {e}")
        return (
            "I'm having some technical difficulties right now. Please try again later. 💙",
            503,
        )
    elif isinstance(e, APIError):
        logger.error(f"OpenAI API error: {e}")
        return (
            "Something went wrong on my end. Please try again in a moment. 💙",
            502,
        )
    else:
        logger.error(f"Unexpected error: {e}")
        return (
            "I'm having a little trouble connecting right now. Please try again in a moment. 💙",
            500,
        )


def _ensure_conversation(user_id, user_message, mood, conversation_id):
    """Get or create a conversation, update mood, and load history.

    Returns (conversation_id, history).
    This shared logic eliminates duplication between sync and streaming chat.
    """
    if not conversation_id:
        conversation_id = conversation_service.create(user_id, user_message, mood)
    elif mood:
        conversation_repo.update_mood(conversation_id, user_id, mood)

    history = message_repo.get_history(conversation_id)
    message_repo.save(conversation_id, "user", user_message)

    return conversation_id, history


def _run_agent_loop(messages, user_id):
    """Run the iterative agent loop: call LLM → execute tools → re-call LLM.

    Returns the final assistant reply text.
    Raises on OpenAI errors (caller handles).
    """
    for iteration in range(MAX_TOOL_ITERATIONS + 1):
        response = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=OPENAI_TEMPERATURE,
            presence_penalty=OPENAI_PRESENCE_PENALTY,
            frequency_penalty=OPENAI_FREQUENCY_PENALTY,
        )

        choice = response.choices[0]

        # If no tool calls, we have the final response
        if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
            return choice.message.content.strip() if choice.message.content else ""

        # Append assistant message with tool calls
        messages.append(choice.message)

        # Execute each tool call and append results
        for tool_call in choice.message.tool_calls:
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}

            logger.info(f"[Agent] Tool call: {tool_name}({json.dumps(arguments)[:200]})")

            result = execute_tool(tool_name, arguments, user_id=user_id)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, default=str),
            })

            logger.info(f"[Agent] Tool result: {json.dumps(result, default=str)[:200]}")

    # If we exhausted iterations, do one final call without tools
    logger.warning("[Agent] Max tool iterations reached, forcing final response")
    response = _client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        max_tokens=OPENAI_MAX_TOKENS,
        temperature=OPENAI_TEMPERATURE,
    )
    return response.choices[0].message.content.strip() if response.choices[0].message.content else ""


def process_message(user_id, user_message, mood, conversation_id):
    """
    Process a chat message synchronously via the agent loop.
    Returns (reply, conversation_id, error_status).
    """
    # Safety check first
    safety_response, safety_type = check_safety(user_message)
    if safety_response:
        if not conversation_id:
            conversation_id = conversation_service.create(user_id, user_message, mood)
        message_repo.save(conversation_id, "user", user_message)
        message_repo.save(conversation_id, "bot", safety_response)
        logger.info(f"[Safety] {safety_type} escalation triggered")
        return safety_response, conversation_id, None

    conversation_id, history = _ensure_conversation(
        user_id, user_message, mood, conversation_id
    )

    messages = build_messages(mood, history, user_message)

    try:
        reply = _run_agent_loop(messages, user_id)
    except Exception as e:
        reply, status = handle_openai_error(e)
        return reply, conversation_id, status

    message_repo.save(conversation_id, "bot", reply)
    return reply, conversation_id, None


def stream_message(user_id, user_message, mood, conversation_id):
    """
    Generator that processes tool calls synchronously, then streams
    the final response tokens via SSE.
    """
    # Safety check first
    safety_response, safety_type = check_safety(user_message)
    if safety_response:
        if not conversation_id:
            conversation_id = conversation_service.create(user_id, user_message, mood)
        message_repo.save(conversation_id, "user", user_message)
        message_repo.save(conversation_id, "bot", safety_response)
        logger.info(f"[Safety] {safety_type} escalation triggered (stream)")
        yield f"data: {json.dumps({'conversation_id': conversation_id})}\n\n"
        yield f"data: {json.dumps({'token': safety_response})}\n\n"
        yield "data: [DONE]\n\n"
        return

    conversation_id, history = _ensure_conversation(
        user_id, user_message, mood, conversation_id
    )

    messages = build_messages(mood, history, user_message)

    # Send conversation_id first
    yield f"data: {json.dumps({'conversation_id': conversation_id})}\n\n"

    # Run tool calls synchronously (non-streaming) until we reach the final response
    try:
        for iteration in range(MAX_TOOL_ITERATIONS):
            response = _client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                max_tokens=OPENAI_MAX_TOKENS,
                temperature=OPENAI_TEMPERATURE,
                presence_penalty=OPENAI_PRESENCE_PENALTY,
                frequency_penalty=OPENAI_FREQUENCY_PENALTY,
            )

            choice = response.choices[0]

            if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
                # No more tool calls — stream this response as tokens
                # But this was a non-streaming call, so send the content as one chunk
                if choice.message.content:
                    full_text = choice.message.content.strip()
                    yield f"data: {json.dumps({'token': full_text})}\n\n"
                    message_repo.save(conversation_id, "bot", full_text)
                yield "data: [DONE]\n\n"
                return

            # Process tool calls
            messages.append(choice.message)
            for tool_call in choice.message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                logger.info(f"[Agent/Stream] Tool call: {tool_name}")
                result = execute_tool(tool_name, arguments, user_id=user_id)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str),
                })

        # After tool iterations, do final streaming call
        full_reply = []
        stream = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=OPENAI_TEMPERATURE,
            presence_penalty=OPENAI_PRESENCE_PENALTY,
            frequency_penalty=OPENAI_FREQUENCY_PENALTY,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                token = delta.content
                full_reply.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"

        complete_text = "".join(full_reply)
        if complete_text:
            try:
                message_repo.save(conversation_id, "bot", complete_text)
            except Exception as e:
                logger.error(f"Failed to save bot reply: {e}")

    except Exception as e:
        error_msg, _ = handle_openai_error(e)
        yield f"data: {json.dumps({'error': error_msg})}\n\n"

    yield "data: [DONE]\n\n"
