"""OpenAI-format tool/function schemas exposed to the LLM, plus a name -> callable
dispatch table wired to the shared business logic in tools.py.
"""

import tools

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check whether a table is available for a given date/time and party size. Always call this before create_reservation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reservation_time": {"type": "string", "description": "ISO 8601 local datetime, e.g. 2026-07-25T19:00"},
                    "party_size": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "required": ["reservation_time", "party_size"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_reservation",
            "description": "Book a table. Only call after check_availability confirms a table is free and all required customer details have been collected from the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string"},
                    "phone": {"type": "string"},
                    "email": {"type": "string"},
                    "party_size": {"type": "integer", "minimum": 1, "maximum": 20},
                    "reservation_time": {"type": "string", "description": "ISO 8601 local datetime"},
                    "special_requests": {"type": "string"},
                },
                "required": ["customer_name", "phone", "party_size", "reservation_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "modify_reservation",
            "description": "Change the time/party size of an existing reservation. Requires the confirmation code and phone number used at booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirmation_code": {"type": "string"},
                    "phone": {"type": "string"},
                    "new_reservation_time": {"type": "string"},
                    "new_party_size": {"type": "integer"},
                    "new_special_requests": {"type": "string"},
                },
                "required": ["confirmation_code", "phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_reservation",
            "description": "Cancel an existing reservation. Requires confirmation code and phone number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirmation_code": {"type": "string"},
                    "phone": {"type": "string"},
                },
                "required": ["confirmation_code", "phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_reservation_status",
            "description": "Look up an existing reservation's details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirmation_code": {"type": "string"},
                    "phone": {"type": "string"},
                },
                "required": ["confirmation_code", "phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_menu",
            "description": "Get real, current menu items with prices and images. Never invent menu items or prices - always call this tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": ["Pizza", "Burger", "Drinks", "Sandwich", "Chicken", "Noodles"]},
                    "dietary_filter": {"type": "string", "enum": ["vegetarian", "vegan", "gluten_free", "nut_free"]},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "place_order",
            "description": "Place a food order for delivery or pickup.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string"},
                    "phone": {"type": "string"},
                    "email": {"type": "string"},
                    "order_type": {"type": "string", "enum": ["delivery", "pickup"]},
                    "delivery_address": {"type": "string", "description": "Required if order_type is delivery"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "menu_item_name": {"type": "string"},
                                "quantity": {"type": "integer", "minimum": 1, "maximum": 20},
                            },
                            "required": ["menu_item_name", "quantity"],
                        },
                    },
                    "notes": {"type": "string"},
                },
                "required": ["customer_name", "phone", "order_type", "items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Check the status of an existing order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirmation_code": {"type": "string"},
                    "phone": {"type": "string"},
                },
                "required": ["confirmation_code", "phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_order",
            "description": "Cancel an order. Only possible while status is 'received' or 'preparing'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirmation_code": {"type": "string"},
                    "phone": {"type": "string"},
                },
                "required": ["confirmation_code", "phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_feedback",
            "description": "Record customer feedback or a complaint.",
            "parameters": {
                "type": "object",
                "properties": {
                    "rating": {"type": "integer", "minimum": 1, "maximum": 5},
                    "comments": {"type": "string"},
                    "customer_name": {"type": "string"},
                    "email": {"type": "string"},
                    "related_order_code": {"type": "string"},
                },
                "required": ["rating", "comments"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_restaurant_info",
            "description": "Get factual restaurant info: hours, location, contact, current promotions, loyalty program, or policies. Never guess these facts - always call this tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "enum": ["hours", "location", "contact", "promotions", "loyalty_program", "policies"]},
                },
                "required": ["topic"],
            },
        },
    },
]

DISPATCH = {
    "check_availability": tools.check_availability,
    "create_reservation": tools.create_reservation,
    "modify_reservation": tools.modify_reservation,
    "cancel_reservation": tools.cancel_reservation,
    "get_reservation_status": tools.get_reservation_status,
    "get_menu": tools.get_menu,
    "place_order": tools.place_order,
    "get_order_status": tools.get_order_status,
    "cancel_order": tools.cancel_order,
    "submit_feedback": tools.submit_feedback,
    "get_restaurant_info": tools.get_restaurant_info,
}


def call_tool(name: str, arguments: dict) -> dict:
    fn = DISPATCH.get(name)
    if fn is None:
        return {"error": "unknown_tool", "message": f"No such tool: {name}"}
    try:
        return fn(**arguments)
    except TypeError as exc:
        return {"error": "invalid_arguments", "message": str(exc)}
    except Exception as exc:  # never let a tool crash the chat loop
        return {"error": "internal_error", "message": str(exc)}
