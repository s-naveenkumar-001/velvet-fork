"""Static restaurant facts. Single source of truth for grounding the chatbot
and rendering the website - extracted from the old intents.json canned
responses so no factual content was lost when the rule-based pipeline was
replaced.
"""

NAME = "Velvet Fork"

ADDRESS = "153 Williamson Plaza, Maggieberg, MT 09514"
PHONE = "+1 (062) 109-9222"
EMAIL = "info@velvetfork-restaurant.example"

HOURS = {
    "monday": ("08:00", "22:00"),
    "tuesday": ("16:00", "23:59"),
    "wednesday": ("08:00", "22:00"),
    "thursday": ("08:00", "22:00"),
    "friday": ("08:00", "22:00"),
    "saturday": ("10:00", "16:00"),
    "sunday": None,  # closed
}

HOURS_TEXT = (
    "Monday, Wednesday-Friday: 08:00 AM - 10:00 PM. "
    "Tuesday: 4:00 PM - Midnight. "
    "Saturday: 10:00 AM - 4:00 PM. "
    "Closed on Sunday."
)

LOYALTY_PROGRAM = (
    "Earn 1 point for every $10 spent. 100 points get you a free meal. "
    "Ask to enroll any time."
)

CURRENT_PROMOTIONS = (
    "50% off selected Burgers and Pizzas this week."
)

RESERVATION_DURATION_MINUTES = 90

POLICIES = (
    "Reservations hold a table for 90 minutes. "
    "Orders can be cancelled any time before they go out for delivery or are marked ready for pickup; "
    "once out for delivery or delivered/picked up, an order can no longer be cancelled. "
    "Please provide the confirmation code and phone number used at booking/ordering time to look up, "
    "modify, or cancel a reservation or order."
)

DIETARY_NOTES = (
    "We offer vegetarian, vegan, gluten-free, and nut-free options across the menu - "
    "use the dietary filter or ask the assistant to filter the menu for you."
)

INFO_TOPICS = {
    "hours": HOURS_TEXT,
    "location": ADDRESS,
    "contact": f"Phone: {PHONE}, Email: {EMAIL}",
    "promotions": CURRENT_PROMOTIONS,
    "loyalty_program": LOYALTY_PROGRAM,
    "policies": POLICIES,
}
