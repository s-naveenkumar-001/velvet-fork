"""Direct JSON API - the reservation form, menu "Add to Cart"/checkout flow,
and feedback form all call these endpoints directly (no LLM involved), while
the chatbot reaches the same business logic through tool_schemas.call_tool.
Both paths share tools.py, so behavior is identical either way.
"""

from flask import Blueprint, jsonify, request

import restaurant_info
import tools

api = Blueprint("api", __name__, url_prefix="/api")


def _respond(result: dict, success_status: int = 200):
    if "error" in result:
        return jsonify({"error": result["error"], "message": result["message"]}), result.get(
            "http_status", 400
        )
    return jsonify(result), success_status


@api.get("/menu")
def get_menu():
    result = tools.get_menu(
        category=request.args.get("category"), dietary_filter=request.args.get("dietary")
    )
    return _respond(result)


@api.get("/restaurant-info")
def get_restaurant_info():
    topic = request.args.get("topic")
    if topic is None:
        return jsonify(
            {
                "name": restaurant_info.NAME,
                "address": restaurant_info.ADDRESS,
                "phone": restaurant_info.PHONE,
                "email": restaurant_info.EMAIL,
                **restaurant_info.INFO_TOPICS,
            }
        )
    return _respond(tools.get_restaurant_info(topic))


@api.get("/reservations/availability")
def reservation_availability():
    result = tools.check_availability(
        request.args.get("reservation_time"), request.args.get("party_size")
    )
    return _respond(result)


@api.post("/reservations")
def create_reservation():
    payload = request.get_json(silent=True) or {}
    result = tools.create_reservation(
        customer_name=payload.get("customer_name"),
        phone=payload.get("phone"),
        reservation_time=payload.get("reservation_time"),
        party_size=payload.get("party_size"),
        email=payload.get("email"),
        special_requests=payload.get("special_requests", ""),
    )
    return _respond(result, success_status=201)


@api.get("/reservations/<code>")
def get_reservation(code):
    result = tools.get_reservation_status(code, request.args.get("phone"))
    return _respond(result)


@api.patch("/reservations/<code>")
def modify_reservation(code):
    payload = request.get_json(silent=True) or {}
    result = tools.modify_reservation(
        confirmation_code=code,
        phone=payload.get("phone"),
        new_reservation_time=payload.get("new_reservation_time"),
        new_party_size=payload.get("new_party_size"),
        new_special_requests=payload.get("new_special_requests"),
    )
    return _respond(result)


@api.post("/reservations/<code>/cancel")
def cancel_reservation(code):
    payload = request.get_json(silent=True) or {}
    result = tools.cancel_reservation(code, payload.get("phone"))
    return _respond(result)


@api.post("/orders")
def place_order():
    payload = request.get_json(silent=True) or {}
    result = tools.place_order(
        customer_name=payload.get("customer_name"),
        phone=payload.get("phone"),
        order_type=payload.get("order_type"),
        items=payload.get("items"),
        email=payload.get("email"),
        delivery_address=payload.get("delivery_address"),
        notes=payload.get("notes", ""),
    )
    return _respond(result, success_status=201)


@api.get("/orders/<code>")
def get_order(code):
    result = tools.get_order_status(code, request.args.get("phone"))
    return _respond(result)


@api.post("/orders/<code>/cancel")
def cancel_order(code):
    payload = request.get_json(silent=True) or {}
    result = tools.cancel_order(code, payload.get("phone"))
    return _respond(result)


@api.post("/feedback")
def submit_feedback():
    payload = request.get_json(silent=True) or {}
    result = tools.submit_feedback(
        rating=payload.get("rating"),
        comments=payload.get("comments"),
        customer_name=payload.get("customer_name"),
        email=payload.get("email"),
        related_order_code=payload.get("related_order_code"),
    )
    return _respond(result, success_status=201)
