"""Idempotent seed data for the menu and restaurant tables. Run directly
(`python seed_data.py`) or import `seed()` after `db.init_db()`.
"""

from db import Base, SessionLocal, engine, init_db
from db_models import MenuItem, RestaurantTable

IMG = "https://images.unsplash.com/photo-{}?w=600&q=80&auto=format&fit=crop"

MENU_ITEMS = [
    # Pizza
    dict(name="Margherita Pizza", category="Pizza",
         description="Classic tomato, mozzarella, and fresh basil on a hand-tossed crust.",
         price=12.99, image_url=IMG.format("1574071318508-1cdbab80d002"),
         is_vegetarian=True, discount_pct=0, rating=4.7),
    dict(name="Pepperoni Pizza", category="Pizza",
         description="Loaded with spicy pepperoni and a blend of mozzarella cheeses.",
         price=14.99, image_url=IMG.format("1628840042765-356cda07504e"),
         discount_pct=10, rating=4.8),
    dict(name="Veggie Supreme Pizza", category="Pizza",
         description="Bell peppers, onions, mushrooms, olives, and sweet corn.",
         price=13.49, image_url=IMG.format("1571066811602-716837d681de"),
         is_vegetarian=True, is_vegan=True, discount_pct=15, rating=4.5),

    # Burger
    dict(name="Classic Cheeseburger", category="Burger",
         description="Beef patty, cheddar, lettuce, tomato, and house sauce.",
         price=9.99, image_url=IMG.format("1568901346375-23c9450c58cd"),
         discount_pct=0, rating=4.6),
    dict(name="Bacon Deluxe Burger", category="Burger",
         description="Double patty, crispy bacon, cheddar, and caramelized onions.",
         price=11.99, image_url=IMG.format("1553979459-d2229ba7433b"),
         discount_pct=10, rating=4.9),
    dict(name="Veggie Burger", category="Burger",
         description="House-made black bean patty, avocado, and chipotle mayo.",
         price=10.49, image_url=IMG.format("1520072959219-c595dc870360"),
         is_vegetarian=True, rating=4.4),

    # Drinks
    dict(name="Fresh Orange Juice", category="Drinks",
         description="Freshly squeezed orange juice, no added sugar.",
         price=4.49, image_url=IMG.format("1600271886742-f049cd451bba"),
         is_vegan=True, is_gluten_free=True, rating=4.6),
    dict(name="Classic Soda", category="Drinks",
         description="Ice-cold cola, lemon-lime, or root beer.",
         price=2.99, image_url=IMG.format("1544145945-f90425340c7e"),
         is_vegan=True, is_gluten_free=True, rating=4.2),
    dict(name="Chocolate Milkshake", category="Drinks",
         description="Rich chocolate milkshake topped with whipped cream.",
         price=5.49, image_url=IMG.format("1572490122747-3968b75cc699"),
         is_vegetarian=True, rating=4.7),

    # Sandwich
    dict(name="Club Sandwich", category="Sandwich",
         description="Triple-decker with turkey, bacon, lettuce, and tomato.",
         price=8.99, image_url=IMG.format("1553909489-cd47e0907980"),
         rating=4.5),
    dict(name="Grilled Cheese Sandwich", category="Sandwich",
         description="Melted three-cheese blend on toasted sourdough.",
         price=6.99, image_url=IMG.format("1528735602780-2552fd46c7af"),
         is_vegetarian=True, rating=4.3),
    dict(name="BLT Sandwich", category="Sandwich",
         description="Crispy bacon, lettuce, tomato, and garlic aioli.",
         price=7.99, image_url=IMG.format("1509722747041-616f39b57569"),
         discount_pct=5, rating=4.4),

    # Chicken
    dict(name="Fried Chicken Unlimited", category="Chicken",
         description="Crispy golden fried chicken, bottomless basket.",
         price=13.99, image_url=IMG.format("1562967916-eb82221dfb92"),
         discount_pct=15, rating=4.8),
    dict(name="Buffalo Chicken Wings", category="Chicken",
         description="Spicy buffalo wings served with ranch dip.",
         price=10.99, image_url=IMG.format("1608039755401-742074f0548d"),
         contains_nuts=False, rating=4.6),
    dict(name="Grilled Chicken Plate", category="Chicken",
         description="Herb-marinated grilled chicken breast with seasonal veggies.",
         price=12.49, image_url=IMG.format("1532550907401-a500c9a57435"),
         is_gluten_free=True, rating=4.5),

    # Noodles
    dict(name="Chicken Ramen", category="Noodles",
         description="Rich miso broth, soft-boiled egg, scallions, and chicken.",
         price=11.49, image_url=IMG.format("1591814468924-caf88d1232e1"),
         rating=4.7),
    dict(name="Pad Thai", category="Noodles",
         description="Stir-fried rice noodles with peanuts, egg, and tamarind sauce.",
         price=10.99, image_url=IMG.format("1559847844-5315695dadae"),
         contains_nuts=True, rating=4.6),
    dict(name="Vegetable Chow Mein", category="Noodles",
         description="Wok-tossed noodles with fresh seasonal vegetables.",
         price=9.49, image_url=IMG.format("1585032226651-759b368d7246"),
         is_vegetarian=True, is_vegan=True, discount_pct=5, rating=4.3),
]

RESTAURANT_TABLES = [
    dict(name="T1", capacity=2, location="window"),
    dict(name="T2", capacity=2, location="indoor"),
    dict(name="T3", capacity=4, location="indoor"),
    dict(name="T4", capacity=4, location="indoor"),
    dict(name="T5", capacity=4, location="patio"),
    dict(name="T6", capacity=6, location="indoor"),
    dict(name="T7", capacity=6, location="patio"),
    dict(name="T8", capacity=8, location="indoor"),
]


def seed():
    session = SessionLocal()
    try:
        if session.query(MenuItem).count() == 0:
            session.add_all(MenuItem(**item) for item in MENU_ITEMS)
        if session.query(RestaurantTable).count() == 0:
            session.add_all(RestaurantTable(**table) for table in RESTAURANT_TABLES)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
    seed()
    print("Database initialized and seeded.")
