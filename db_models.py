from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_vegetarian: Mapped[bool] = mapped_column(Boolean, default=False)
    is_vegan: Mapped[bool] = mapped_column(Boolean, default=False)
    is_gluten_free: Mapped[bool] = mapped_column(Boolean, default=False)
    contains_nuts: Mapped[bool] = mapped_column(Boolean, default=False)
    discount_pct: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Numeric(2, 1), default=4.5)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    def original_price(self) -> float:
        price = float(self.price)
        if self.discount_pct:
            return round(price / (1 - self.discount_pct / 100), 2)
        return price

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "price": float(self.price),
            "original_price": self.original_price(),
            "image_url": self.image_url,
            "is_vegetarian": self.is_vegetarian,
            "is_vegan": self.is_vegan,
            "is_gluten_free": self.is_gluten_free,
            "contains_nuts": self.contains_nuts,
            "discount_pct": self.discount_pct,
            "rating": float(self.rating),
            "is_available": self.is_available,
        }


class RestaurantTable(Base):
    __tablename__ = "restaurant_tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String(30), default="indoor")


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    confirmation_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=True)
    party_size: Mapped[int] = mapped_column(Integer, nullable=False)
    table_id: Mapped[int] = mapped_column(ForeignKey("restaurant_tables.id"), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=90)
    status: Mapped[str] = mapped_column(String(20), default="confirmed")
    special_requests: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    table: Mapped["RestaurantTable"] = relationship()

    __table_args__ = (CheckConstraint("party_size > 0 AND party_size <= 20"),)

    def to_dict(self) -> dict:
        return {
            "confirmation_code": self.confirmation_code,
            "customer_name": self.customer_name,
            "phone": self.phone,
            "email": self.email,
            "party_size": self.party_size,
            "table_name": self.table.name if self.table else None,
            "start_time": self.start_time.isoformat(),
            "duration_minutes": self.duration_minutes,
            "status": self.status,
            "special_requests": self.special_requests,
        }


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    confirmation_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=True)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)
    delivery_address: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="received")
    total_amount: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "confirmation_code": self.confirmation_code,
            "customer_name": self.customer_name,
            "phone": self.phone,
            "email": self.email,
            "order_type": self.order_type,
            "delivery_address": self.delivery_address,
            "status": self.status,
            "total_amount": float(self.total_amount),
            "notes": self.notes,
            "items": [item.to_dict() for item in self.items],
        }


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    menu_item: Mapped["MenuItem"] = relationship()

    def to_dict(self) -> dict:
        return {
            "menu_item_name": self.menu_item.name if self.menu_item else None,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "line_total": round(self.quantity * float(self.unit_price), 2),
        }


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(120), nullable=True)
    email: Mapped[str] = mapped_column(String(120), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comments: Mapped[str] = mapped_column(Text, default="")
    related_order_code: Mapped[str] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5"),)
