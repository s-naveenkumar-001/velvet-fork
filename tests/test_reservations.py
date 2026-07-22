GOOD_TIME = "2026-08-03T19:00"  # Monday, within 08:00-22:00 operating hours


def test_create_reservation_success_returns_confirmation_code(client):
    resp = client.post(
        "/api/reservations",
        json={
            "customer_name": "Jane Doe",
            "phone": "555-111-2222",
            "party_size": 2,
            "reservation_time": GOOD_TIME,
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert len(data["confirmation_code"]) == 6
    assert data["status"] == "confirmed"


def test_create_reservation_missing_name_returns_400_name_required(client):
    resp = client.post(
        "/api/reservations",
        json={"customer_name": "", "phone": "555-111-2222", "party_size": 2, "reservation_time": GOOD_TIME},
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "name_required"


def test_create_reservation_conflicting_time_returns_409_no_availability(client):
    # Both tables (capacity 2 and 6) get booked for the same slot, so a third
    # request for the same time/party size has nothing left to assign.
    for phone_suffix in ("1111", "2222"):
        resp = client.post(
            "/api/reservations",
            json={
                "customer_name": "Guest",
                "phone": f"555-000-{phone_suffix}",
                "party_size": 2,
                "reservation_time": GOOD_TIME,
            },
        )
        assert resp.status_code == 201

    resp = client.post(
        "/api/reservations",
        json={
            "customer_name": "Guest",
            "phone": "555-000-3333",
            "party_size": 2,
            "reservation_time": GOOD_TIME,
        },
    )
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "no_availability"


def test_cancel_reservation_wrong_phone_returns_404(client):
    create = client.post(
        "/api/reservations",
        json={"customer_name": "Jane Doe", "phone": "555-111-2222", "party_size": 2, "reservation_time": GOOD_TIME},
    )
    code = create.get_json()["confirmation_code"]

    resp = client.post(f"/api/reservations/{code}/cancel", json={"phone": "555-999-9999"})
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "not_found"


def test_cancel_reservation_success_sets_status_cancelled(client):
    create = client.post(
        "/api/reservations",
        json={"customer_name": "Jane Doe", "phone": "555-111-2222", "party_size": 2, "reservation_time": GOOD_TIME},
    )
    code = create.get_json()["confirmation_code"]

    resp = client.post(f"/api/reservations/{code}/cancel", json={"phone": "555-111-2222"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "cancelled"

    again = client.post(f"/api/reservations/{code}/cancel", json={"phone": "555-111-2222"})
    assert again.status_code == 409
    assert again.get_json()["error"] == "already_cancelled"


def test_modify_reservation_changes_party_size(client):
    create = client.post(
        "/api/reservations",
        json={"customer_name": "Jane Doe", "phone": "555-111-2222", "party_size": 2, "reservation_time": GOOD_TIME},
    )
    code = create.get_json()["confirmation_code"]

    resp = client.patch(
        f"/api/reservations/{code}", json={"phone": "555-111-2222", "new_party_size": 6}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["party_size"] == 6
    assert data["table_name"] == "T-large"
