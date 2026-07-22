"""Conversation orchestration: builds the system prompt, runs the OpenRouter
tool-calling loop, and executes tool calls against the shared business logic
in tools.py via tool_schemas.call_tool.
"""

import json
import uuid

import flask

import config
import restaurant_info
import tool_schemas
from llm_client import get_client

BOT_NAME = "Aether"
MAX_TOOL_ITERATIONS = 5
MAX_HISTORY_MESSAGES = 30

# In-memory, per-process conversation store keyed by a UUID kept in the
# signed Flask session cookie. Full tool-calling message arrays are too big
# for a cookie, and this project has no other persistence requirement for
# chat history, so a process-local dict is enough - it resets on restart.
CONVERSATIONS: dict[str, list[dict]] = {}

SYSTEM_PROMPT = f"""You are {BOT_NAME}, the friendly AI customer care assistant for {restaurant_info.NAME}, a restaurant. \
Be warm, concise, and helpful.

Grounding rules:
- Never invent menu items, prices, hours, or policies. Always call get_menu or get_restaurant_info to get real, current data before answering factual questions.
- Before calling create_reservation or place_order, make sure you have collected all required details from the user by asking follow-up questions. Never guess or fabricate customer details.
- Any time a user wants to modify, cancel, or check the status of an existing reservation or order, you must have both their confirmation code and phone number before calling the tool. Ask for both if either is missing.
- Before finalizing a booking or order, summarize the details back to the user and ask for confirmation. After a successful create_reservation or place_order call, clearly state the confirmation code and tell the user to save it for later lookups, changes, or cancellations.
- Whenever you list two or more menu items (e.g. after calling get_menu, or answering "what's on the menu"), format them as a GitHub-flavored Markdown table with columns: Name | Price | Category | Dietary. Do not describe multiple items as prose or a bulleted list - always use a Markdown table for multi-item menu listings. A single item mentioned in passing does not need a table.

Known facts (you may state these directly without a tool call, but call get_restaurant_info for anything not listed here):
- Address: {restaurant_info.ADDRESS}
- Phone: {restaurant_info.PHONE}
- Hours: {restaurant_info.HOURS_TEXT}
- Reservations hold a table for {restaurant_info.RESERVATION_DURATION_MINUTES} minutes.
- {restaurant_info.POLICIES}
- {restaurant_info.DIETARY_NOTES}
"""


def get_or_create_session_id() -> str:
    if "chat_session_id" not in flask.session:
        flask.session["chat_session_id"] = str(uuid.uuid4())
    return flask.session["chat_session_id"]


def _trim(history: list[dict]) -> None:
    if len(history) > MAX_HISTORY_MESSAGES:
        history[:] = [history[0]] + history[-(MAX_HISTORY_MESSAGES - 1):]


def _message_to_dict(msg) -> dict:
    entry = {"role": "assistant", "content": msg.content}
    if msg.tool_calls:
        entry["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.function.name, "arguments": call.function.arguments},
            }
            for call in msg.tool_calls
        ]
    return entry


def _run_completion(client, model: str, history: list[dict]):
    return client.chat.completions.create(
        model=model,
        messages=history,
        tools=tool_schemas.TOOLS,
        tool_choice="auto",
    )


def get_response(session_id: str, user_message: str) -> str:
    history = CONVERSATIONS.setdefault(session_id, [{"role": "system", "content": SYSTEM_PROMPT}])
    history.append({"role": "user", "content": user_message})

    if not config.OPENROUTER_API_KEY:
        fallback = (
            "The AI assistant isn't configured yet - an OPENROUTER_API_KEY is missing. "
            "Please set one in your .env file (see .env.example)."
        )
        history.append({"role": "assistant", "content": fallback})
        _trim(history)
        return fallback

    try:
        client = get_client()
    except Exception:
        fallback = "I'm having trouble reaching our systems right now. Please try again shortly."
        history.append({"role": "assistant", "content": fallback})
        _trim(history)
        return fallback
    model = config.OPENROUTER_MODEL

    for _ in range(MAX_TOOL_ITERATIONS):
        try:
            response = _run_completion(client, model, history)
        except Exception:
            if model != config.OPENROUTER_FALLBACK_MODEL:
                model = config.OPENROUTER_FALLBACK_MODEL
                try:
                    response = _run_completion(client, model, history)
                except Exception:
                    fallback = (
                        "I'm having trouble reaching our systems right now. "
                        "Please try again shortly, or call us directly."
                    )
                    history.append({"role": "assistant", "content": fallback})
                    _trim(history)
                    return fallback
            else:
                fallback = (
                    "I'm having trouble reaching our systems right now. "
                    "Please try again shortly, or call us directly."
                )
                history.append({"role": "assistant", "content": fallback})
                _trim(history)
                return fallback

        msg = response.choices[0].message
        if not msg.tool_calls:
            history.append({"role": "assistant", "content": msg.content})
            _trim(history)
            return msg.content or "..."

        history.append(_message_to_dict(msg))
        for call in msg.tool_calls:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
            result = tool_schemas.call_tool(call.function.name, arguments)
            history.append(
                {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, default=str)}
            )

    fallback = "I'm having trouble completing that right now - could you try rephrasing, or contact us directly?"
    history.append({"role": "assistant", "content": fallback})
    _trim(history)
    return fallback
