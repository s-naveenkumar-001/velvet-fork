"""DB-backed business logic. Every public function here is called from both
the LLM tool dispatcher (tool_schemas.py) and the direct JSON API (api.py),
so validation and behavior are identical no matter how a request arrives.

Convention: every function returns a plain JSON-serializable dict and never
raises for expected error conditions - it returns {"error": <code>,
"message": <text>} instead, plus an "http_status" hint that api.py can use
for the HTTP response (the LLM dispatcher just ignores that key).
"""

import random
import re
import string
from datetime import datetime, timedelta

from sqlalchemy import func

import restaurant_info
from db import SessionLocal
from db_models import Feedback, MenuItem, Order, OrderItem, Reservation, RestaurantTable

RESERVATION_STATUSES = {"confirmed", "cancelled", "completed", "no_show"}
ORDER_STATUSES = {"received", "preparing", "out_for_delivery", "delivered", "cancelled"}
ORDER_CANCELLABLE_STATUSES = {"received", "preparing"}

CODE_ALPHABET = "".join(c for c in string.ascii_uppercase + string.digits if c not in "0O1I")


def _error(code: str, message: str, http_status: int = 400) -> dict:
    return {"error": code, "message": message, "http_status": http_status}


def generate_confirmation_code(session) -> str:
    for _ in range(20):
        code = "".join(random.choices(CODE_ALPHABET, k=6))
        exists = (
            session.query(Reservation).filter_by(confirmation_code=code).first()
            or session.query(Order).filter_by(confirmation_code=code).first()
        )
        if not exists:
            return code
    raise RuntimeError("Could not generate a unique confirmation code")


def _validate_name(name) -> tuple[str | None, dict | None]:
    if not isinstance(name, str) or not name.strip() or not (2 <= len(name.strip()) <= 120):
        return None, _error("name_required", "Please provide a valid name.")
    return name.strip(), None


def _validate_phone(phone) -> tuple[str | None, dict | None]:
    if not isinstance(phone, str):
        return None, _error("invalid_phone", "Please provide a valid phone number.")
    digits = re.sub(r"[^\d+]", "", phone)
    digit_count = len(re.sub(r"\D", "", digits))
    if not (7 <= digit_count <= 15):
        return None, _error("invalid_phone", "Please provide a valid phone number.")
    return digits, None


def _validate_email(email) -> tuple[str | None, dict | None]:
    if email in (None, ""):
        return None, None
    if not isinstance(email, str) or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()):
        return None, _error("invalid_email", "Please provide a valid email address.")
    return email.strip(), None


def _validate_party_size(party_size) -> tuple[int | None, dict | None]:
    try:
        party_size = int(party_size)
    except (TypeError, ValueError):
        return None, _error("invalid_party_size", "Party size must be a whole number between 1 and 20.")
    if not (1 <= party_size <= 20):
        return None, _error("invalid_party_size", "Party size must be between 1 and 20.")
    return party_size, None


def _validate_reservation_time(reservation_time) -> tuple[datetime | None, dict | None]:
    try:
        dt = datetime.fromisoformat(str(reservation_time))
    except (TypeError, ValueError):
        return None, _error("invalid_time", "Please provide a date/time like 2026-07-25T19:00.")
    if dt <= datetime.now():
        return None, _error("invalid_time", "Reservation time must be in the future.")
    weekday = dt.strftime("%A").lower()
    hours = restaurant_info.HOURS.get(weekday)
    if not hours:
        return None, _error(
            "outside_operating_hours", f"We are closed on {weekday.capitalize()}.", http_status=409
        )
    open_t, close_t = hours
    if not (open_t <= dt.strftime("%H:%M") <= close_t):
        return None, _error(
            "outside_operating_hours",
            f"We are open {open_t}-{close_t} on {weekday.capitalize()}.",
            http_status=409,
        )
    return dt, None


def find_available_table(
    session,
    requested_start: datetime,
    party_size: int,
    duration_minutes: int = restaurant_info.RESERVATION_DURATION_MINUTES,
    exclude_reservation_id: int | None = None,
) -> RestaurantTable | None:
    requested_end = requested_start + timedelta(minutes=duration_minutes)
    candidates = (
        session.query(RestaurantTable)
        .filter(RestaurantTable.capacity >= party_size)
        .order_by(RestaurantTable.capacity.asc())
        .all()
    )
    for table in candidates:
        query = session.query(Reservation).filter(
            Reservation.table_id == table.id,
            Reservation.status != "cancelled",
            Reservation.start_time < requested_end,
        )
        if exclude_reservation_id:
            query = query.filter(Reservation.id != exclude_reservation_id)
        conflict = False
        for existing in query.all():
            existing_end = existing.start_time + timedelta(minutes=existing.duration_minutes)
            if existing.start_time < requested_end and existing_end > requested_start:
                conflict = True
                break
        if not conflict:
            return table
    return None


def _find_reservation(session, confirmation_code, phone):
    phone_clean, err = _validate_phone(phone)
    if err:
        return None, err
    reservation = (
        session.query(Reservation)
        .filter(func.upper(Reservation.confirmation_code) == str(confirmation_code).strip().upper())
        .first()
    )
    if not reservation or re.sub(r"\D", "", reservation.phone) != re.sub(r"\D", "", phone_clean):
        return None, _error("not_found", "No reservation found for that confirmation code and phone.", 404)
    return reservation, None


def _find_order(session, confirmation_code, phone):
    phone_clean, err = _validate_phone(phone)
    if err:
        return None, err
    order = (
        session.query(Order)
        .filter(func.upper(Order.confirmation_code) == str(confirmation_code).strip().upper())
        .first()
    )
    if not order or re.sub(r"\D", "", order.phone) != re.sub(r"\D", "", phone_clean):
        return None, _error("not_found", "No order found for that confirmation code and phone.", 404)
    return order, None


# --- Reservations -----------------------------------------------------------

def check_availability(reservation_time, party_size) -> dict:
    session = SessionLocal()
    try:
        dt, err = _validate_reservation_time(reservation_time)
        if err:
            return err
        size, err = _validate_party_size(party_size)
        if err:
            return err
        table = find_available_table(session, dt, size)
        return {"available": table is not None, "table_name": table.name if table else None}
    finally:
        session.close()


def create_reservation(
    customer_name, phone, reservation_time, party_size, email=None, special_requests=""
) -> dict:
    session = SessionLocal()
    try:
        name, err = _validate_name(customer_name)
        if err:
            return err
        phone_clean, err = _validate_phone(phone)
        if err:
            return err
        email_clean, err = _validate_email(email)
        if err:
            return err
        size, err = _validate_party_size(party_size)
        if err:
            return err
        dt, err = _validate_reservation_time(reservation_time)
        if err:
            return err

        table = find_available_table(session, dt, size)
        if not table:
            return _error("no_availability", "No tables available for that time and party size.", 409)

        reservation = Reservation(
            confirmation_code=generate_confirmation_code(session),
            customer_name=name,
            phone=phone_clean,
            email=email_clean,
            party_size=size,
            table_id=table.id,
            start_time=dt,
            special_requests=(special_requests or "").strip(),
        )
        session.add(reservation)
        session.commit()
        session.refresh(reservation)
        return reservation.to_dict()
    finally:
        session.close()


def modify_reservation(
    confirmation_code, phone, new_reservation_time=None, new_party_size=None, new_special_requests=None
) -> dict:
    session = SessionLocal()
    try:
        reservation, err = _find_reservation(session, confirmation_code, phone)
        if err:
            return err
        if reservation.status == "cancelled":
            return _error("already_cancelled", "This reservation was already cancelled.", 409)

        new_time = reservation.start_time
        if new_reservation_time is not None:
            new_time, err = _validate_reservation_time(new_reservation_time)
            if err:
                return err
        new_size = reservation.party_size
        if new_party_size is not None:
            new_size, err = _validate_party_size(new_party_size)
            if err:
                return err

        table = find_available_table(
            session, new_time, new_size, exclude_reservation_id=reservation.id
        )
        if not table:
            return _error("no_availability", "No tables available for the new time and party size.", 409)

        reservation.start_time = new_time
        reservation.party_size = new_size
        reservation.table_id = table.id
        if new_special_requests is not None:
            reservation.special_requests = new_special_requests.strip()
        session.commit()
        session.refresh(reservation)
        return reservation.to_dict()
    finally:
        session.close()


def cancel_reservation(confirmation_code, phone) -> dict:
    session = SessionLocal()
    try:
        reservation, err = _find_reservation(session, confirmation_code, phone)
        if err:
            return err
        if reservation.status == "cancelled":
            return _error("already_cancelled", "This reservation was already cancelled.", 409)
        reservation.status = "cancelled"
        session.commit()
        return {"confirmation_code": reservation.confirmation_code, "status": "cancelled"}
    finally:
        session.close()


def get_reservation_status(confirmation_code, phone) -> dict:
    session = SessionLocal()
    try:
        reservation, err = _find_reservation(session, confirmation_code, phone)
        if err:
            return err
        return reservation.to_dict()
    finally:
        session.close()


# --- Menu ---------------------------------------------------------------

def get_menu(category=None, dietary_filter=None) -> dict:
    session = SessionLocal()
    try:
        query = session.query(MenuItem).filter(MenuItem.is_available.is_(True))
        if category:
            query = query.filter(func.lower(MenuItem.category) == str(category).lower())
        if dietary_filter:
            flag_map = {
                "vegetarian": MenuItem.is_vegetarian,
                "vegan": MenuItem.is_vegan,
                "gluten_free": MenuItem.is_gluten_free,
                "nut_free": MenuItem.contains_nuts.is_(False),
            }
            column = flag_map.get(dietary_filter)
            if column is None:
                return _error("invalid_dietary_filter", "Unknown dietary filter.")
            query = query.filter(column.is_(True) if dietary_filter != "nut_free" else column)
        items = query.all()
        return {"items": [item.to_dict() for item in items]}
    finally:
        session.close()


def _resolve_menu_item(session, name_or_id):
    if isinstance(name_or_id, int) or (isinstance(name_or_id, str) and name_or_id.isdigit()):
        return session.get(MenuItem, int(name_or_id))
    return (
        session.query(MenuItem)
        .filter(func.lower(MenuItem.name) == str(name_or_id).strip().lower())
        .first()
    )


# --- Orders ---------------------------------------------------------------

def place_order(
    customer_name, phone, order_type, items, email=None, delivery_address=None, notes=""
) -> dict:
    session = SessionLocal()
    try:
        name, err = _validate_name(customer_name)
        if err:
            return err
        phone_clean, err = _validate_phone(phone)
        if err:
            return err
        email_clean, err = _validate_email(email)
        if err:
            return err
        if order_type not in ("delivery", "pickup"):
            return _error("invalid_order_type", "order_type must be 'delivery' or 'pickup'.")
        if order_type == "delivery" and not (delivery_address and str(delivery_address).strip()):
            return _error("delivery_address_required", "Please provide a delivery address.")
        if not items or not isinstance(items, list):
            return _error("invalid_items", "Please include at least one item.")

        resolved = []
        for entry in items:
            menu_item_ref = entry.get("menu_item_name") or entry.get("menu_item_id")
            quantity = entry.get("quantity")
            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                return _error("invalid_quantity", f"Invalid quantity for {menu_item_ref!r}.")
            if not (1 <= quantity <= 20):
                return _error("invalid_quantity", f"Quantity for {menu_item_ref!r} must be 1-20.")
            menu_item = _resolve_menu_item(session, menu_item_ref)
            if not menu_item or not menu_item.is_available:
                return _error(
                    "menu_item_not_found", f"Menu item not found: {menu_item_ref!r}.", 404
                )
            resolved.append((menu_item, quantity))

        order = Order(
            confirmation_code=generate_confirmation_code(session),
            customer_name=name,
            phone=phone_clean,
            email=email_clean,
            order_type=order_type,
            delivery_address=(delivery_address or "").strip() or None,
            notes=(notes or "").strip(),
        )
        total = 0.0
        for menu_item, quantity in resolved:
            unit_price = float(menu_item.price)
            total += unit_price * quantity
            order.items.append(
                OrderItem(menu_item_id=menu_item.id, quantity=quantity, unit_price=unit_price)
            )
        order.total_amount = round(total, 2)

        session.add(order)
        session.commit()
        session.refresh(order)
        return order.to_dict()
    finally:
        session.close()


def get_order_status(confirmation_code, phone) -> dict:
    session = SessionLocal()
    try:
        order, err = _find_order(session, confirmation_code, phone)
        if err:
            return err
        return order.to_dict()
    finally:
        session.close()


def cancel_order(confirmation_code, phone) -> dict:
    session = SessionLocal()
    try:
        order, err = _find_order(session, confirmation_code, phone)
        if err:
            return err
        if order.status not in ORDER_CANCELLABLE_STATUSES:
            return _error(
                "cannot_cancel",
                f"Order cannot be cancelled once it is '{order.status}'.",
                409,
            )
        order.status = "cancelled"
        session.commit()
        return {"confirmation_code": order.confirmation_code, "status": "cancelled"}
    finally:
        session.close()


# --- Feedback ---------------------------------------------------------------

def submit_feedback(rating, comments, customer_name=None, email=None, related_order_code=None) -> dict:
    session = SessionLocal()
    try:
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            return _error("invalid_rating", "Rating must be a whole number from 1 to 5.")
        if not (1 <= rating <= 5):
            return _error("invalid_rating", "Rating must be between 1 and 5.")
        if not comments or not str(comments).strip():
            return _error("comments_required", "Please include a short comment.")
        email_clean, err = _validate_email(email)
        if err:
            return err

        feedback = Feedback(
            customer_name=(customer_name or "").strip() or None,
            email=email_clean,
            rating=rating,
            comments=str(comments).strip(),
            related_order_code=(related_order_code or "").strip() or None,
        )
        session.add(feedback)
        session.commit()
        return {"status": "received", "message": "Thank you for your feedback!"}
    finally:
        session.close()


# --- Restaurant info ---------------------------------------------------------

def get_restaurant_info(topic=None) -> dict:
    if topic is None:
        return {
            "name": restaurant_info.NAME,
            "address": restaurant_info.ADDRESS,
            "phone": restaurant_info.PHONE,
            "email": restaurant_info.EMAIL,
            **restaurant_info.INFO_TOPICS,
        }
    text = restaurant_info.INFO_TOPICS.get(topic)
    if text is None:
        return _error("invalid_topic", "Unknown info topic.")
    return {"topic": topic, "text": text}
