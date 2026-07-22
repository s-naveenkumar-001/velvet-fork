from datetime import datetime, timedelta

import tools
from db_models import Reservation, RestaurantTable


def _table(session, name):
    return session.query(RestaurantTable).filter_by(name=name).one()


def test_available_when_no_conflicting_reservation(db_session):
    start = datetime(2026, 8, 3, 19, 0)  # a Monday, within operating hours
    table = tools.find_available_table(db_session, start, party_size=2)
    assert table is not None
    assert table.capacity >= 2


def test_unavailable_when_overlapping_reservation_blocks_only_matching_table(db_session):
    # Both tables (capacity 2 and capacity 6) can fit party_size=2, so both
    # must be booked for the same slot before availability should report None.
    start = datetime(2026, 8, 3, 19, 0)
    for table_name in ("T-small", "T-large"):
        table = _table(db_session, table_name)
        db_session.add(
            Reservation(
                confirmation_code=f"ABC{table.id}",
                customer_name="Existing Guest",
                phone="5551234567",
                party_size=2,
                table_id=table.id,
                start_time=start,
                duration_minutes=90,
                status="confirmed",
            )
        )
    db_session.commit()

    # Overlaps the middle of the existing 90-minute reservations.
    conflicting_start = start + timedelta(minutes=30)
    table = tools.find_available_table(db_session, conflicting_start, party_size=2)
    assert table is None


def test_cancelled_reservation_does_not_block_availability(db_session):
    small = _table(db_session, "T-small")
    start = datetime(2026, 8, 3, 19, 0)
    db_session.add(
        Reservation(
            confirmation_code="CANC01",
            customer_name="Cancelled Guest",
            phone="5551234567",
            party_size=2,
            table_id=small.id,
            start_time=start,
            duration_minutes=90,
            status="cancelled",
        )
    )
    db_session.commit()

    table = tools.find_available_table(db_session, start + timedelta(minutes=30), party_size=2)
    assert table is not None
    assert table.id == small.id


def test_back_to_back_slots_do_not_overlap(db_session):
    small = _table(db_session, "T-small")
    start = datetime(2026, 8, 3, 19, 0)
    db_session.add(
        Reservation(
            confirmation_code="BACK01",
            customer_name="Earlier Guest",
            phone="5551234567",
            party_size=2,
            table_id=small.id,
            start_time=start,
            duration_minutes=90,
            status="confirmed",
        )
    )
    db_session.commit()

    # Starts exactly when the existing reservation's 90-minute hold ends.
    next_start = start + timedelta(minutes=90)
    table = tools.find_available_table(db_session, next_start, party_size=2)
    assert table is not None
    assert table.id == small.id


def test_party_size_exceeding_all_table_capacity_returns_none(db_session):
    start = datetime(2026, 8, 3, 19, 0)
    table = tools.find_available_table(db_session, start, party_size=99)
    assert table is None
