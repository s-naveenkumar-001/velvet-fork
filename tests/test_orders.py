def test_place_order_computes_total_from_menu_prices(client):
    resp = client.post(
        "/api/orders",
        json={
            "customer_name": "John Smith",
            "phone": "555-333-4444",
            "order_type": "pickup",
            "items": [{"menu_item_name": "Test Pizza", "quantity": 2}, {"menu_item_name": "Test Burger", "quantity": 1}],
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["total_amount"] == 28.0  # 2*10.0 + 1*8.0
    assert data["status"] == "received"


def test_place_order_unknown_menu_item_returns_404(client):
    resp = client.post(
        "/api/orders",
        json={
            "customer_name": "John Smith",
            "phone": "555-333-4444",
            "order_type": "pickup",
            "items": [{"menu_item_name": "Nonexistent Dish", "quantity": 1}],
        },
    )
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "menu_item_not_found"


def test_place_order_delivery_without_address_returns_400(client):
    resp = client.post(
        "/api/orders",
        json={
            "customer_name": "John Smith",
            "phone": "555-333-4444",
            "order_type": "delivery",
            "items": [{"menu_item_name": "Test Pizza", "quantity": 1}],
        },
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "delivery_address_required"


def test_cancel_order_after_out_for_delivery_returns_409_cannot_cancel(client, db_session):
    create = client.post(
        "/api/orders",
        json={
            "customer_name": "John Smith",
            "phone": "555-333-4444",
            "order_type": "pickup",
            "items": [{"menu_item_name": "Test Pizza", "quantity": 1}],
        },
    )
    code = create.get_json()["confirmation_code"]

    from db_models import Order

    order = db_session.query(Order).filter_by(confirmation_code=code).one()
    order.status = "out_for_delivery"
    db_session.commit()

    resp = client.post(f"/api/orders/{code}/cancel", json={"phone": "555-333-4444"})
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "cannot_cancel"


def test_cancel_order_while_received_succeeds(client):
    create = client.post(
        "/api/orders",
        json={
            "customer_name": "John Smith",
            "phone": "555-333-4444",
            "order_type": "pickup",
            "items": [{"menu_item_name": "Test Pizza", "quantity": 1}],
        },
    )
    code = create.get_json()["confirmation_code"]

    resp = client.post(f"/api/orders/{code}/cancel", json={"phone": "555-333-4444"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "cancelled"
