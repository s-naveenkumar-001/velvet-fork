import os
import tempfile

import pytest

# Must be set before any project module (which reads env at import time) is imported.
_fd, _TEST_DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"
os.environ.setdefault("OPENROUTER_API_KEY", "")

import app as flask_app_module  # noqa: E402
from db import SessionLocal, init_db  # noqa: E402
from db_models import Feedback, MenuItem, Order, OrderItem, Reservation, RestaurantTable  # noqa: E402

init_db()


def _clear_all(session):
    for model in (OrderItem, Order, Reservation, Feedback, MenuItem, RestaurantTable):
        session.query(model).delete()
    session.commit()


@pytest.fixture()
def db_session():
    session = SessionLocal()
    _clear_all(session)
    session.add_all(
        [
            MenuItem(
                name="Test Pizza",
                category="Pizza",
                price=10.0,
                image_url="http://example.com/pizza.jpg",
            ),
            MenuItem(
                name="Test Burger",
                category="Burger",
                price=8.0,
                image_url="http://example.com/burger.jpg",
            ),
        ]
    )
    session.add_all(
        [
            RestaurantTable(name="T-small", capacity=2, location="indoor"),
            RestaurantTable(name="T-large", capacity=6, location="indoor"),
        ]
    )
    session.commit()
    yield session
    session.close()
    cleanup = SessionLocal()
    _clear_all(cleanup)
    cleanup.close()
    SessionLocal.remove()


@pytest.fixture()
def client(db_session):
    flask_app_module.app.config.update(TESTING=True)
    with flask_app_module.app.test_client() as test_client:
        yield test_client
