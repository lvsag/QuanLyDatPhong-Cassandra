"""
Nạp dữ liệu mẫu.

    python seed_db.py           # tạo bảng (nếu chưa có) và nạp dữ liệu mẫu
    python seed_db.py --reset   # XÓA keyspace hotel_booking, tạo lại theo schema.cql rồi nạp

Cần --reset khi đang có DB theo schema cũ, vì khóa chính của bảng Cassandra không sửa được.
"""
import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from cassandra.cluster import Cluster
from cassandra.util import uuid_from_time

from cassandra_config import (
    CASSANDRA_HOST, CASSANDRA_PORT, KEYSPACE,
    get_session, load_cql_statements,
)
from repository import BookingRepository

SEED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_data.cql")

# (số thứ tự, room, customer, check_in, check_out) — cùng 19 booking của bản cũ
SEED_BOOKINGS = [
    (1, 1, 1, "2026-01-05", "2026-01-08"),
    (2, 2, 2, "2026-01-06", "2026-01-09"),
    (3, 3, 3, "2026-01-07", "2026-01-10"),
    (4, 5, 4, "2026-01-08", "2026-01-12"),
    (5, 7, 5, "2026-01-05", "2026-01-09"),
    (6, 8, 6, "2026-01-10", "2026-01-14"),
    (7, 9, 7, "2026-01-06", "2026-01-10"),
    (8, 11, 8, "2026-01-12", "2026-01-16"),
    (9, 13, 9, "2026-01-05", "2026-01-08"),
    (10, 14, 10, "2026-01-09", "2026-01-13"),
    (11, 15, 11, "2026-01-11", "2026-01-15"),
    (12, 17, 12, "2026-01-08", "2026-01-12"),
    (13, 19, 13, "2026-01-06", "2026-01-10"),
    (14, 20, 14, "2026-01-10", "2026-01-14"),
    (15, 21, 15, "2026-01-13", "2026-01-17"),
    (16, 23, 16, "2026-01-07", "2026-01-11"),
    (17, 25, 17, "2026-01-05", "2026-01-09"),
    (18, 26, 18, "2026-01-11", "2026-01-15"),
    (19, 27, 19, "2026-01-14", "2026-01-18"),
]


def room_uuid(n):
    return UUID(f"20000000-0000-0000-0000-{n:012d}")


def customer_uuid(n):
    return UUID(f"10000000-0000-0000-0000-{n:012d}")


def seed_booking_id(n, check_in):
    """timeuuid cố định theo số thứ tự → chạy lại seed không tạo booking trùng.
    Giả lập booking được đặt trước ngày check-in 7 ngày."""
    created = datetime.combine(check_in - timedelta(days=7), time(9, 0), tzinfo=timezone.utc)
    return uuid_from_time(created, node=n, clock_seq=n)


def reset_keyspace():
    cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
    session = cluster.connect()
    session.execute(f"DROP KEYSPACE IF EXISTS {KEYSPACE}")
    cluster.shutdown()
    print(f"🗑️  Đã xóa keyspace {KEYSPACE}")


def main():
    if "--reset" in sys.argv:
        reset_keyspace()

    # get_session() tự tạo keyspace và các bảng trong schema.cql
    cluster, session = get_session()

    # 1. Danh mục: hotels, customers, customers_by_email, rooms_by_hotel
    for stmt in load_cql_statements(SEED_FILE):
        try:
            session.execute(stmt)
        except Exception as e:
            print('ERROR executing:', stmt[:80].replace('\n', ' '), '...', e)

    # 2. Booking: đi qua BookingRepository để mọi bảng booking đồng bộ với nhau
    hotel_of_room = {r.room_id: r.hotel_id
                     for r in session.execute("SELECT hotel_id, room_id FROM rooms_by_hotel")}
    cluster.shutdown()

    repo = BookingRepository()
    ok = 0
    for n, room_n, customer_n, check_in, check_out in SEED_BOOKINGS:
        room_id = room_uuid(room_n)
        check_in_d = date.fromisoformat(check_in)
        success, _, msg = repo.create_booking(
            room_id=room_id,
            customer_id=customer_uuid(customer_n),
            hotel_id=hotel_of_room[room_id],
            check_in_date=check_in_d,
            check_out_date=date.fromisoformat(check_out),
            booking_id=seed_booking_id(n, check_in_d),
        )
        ok += success
        if not success:
            print(f"  booking #{n}: {msg}")
    repo.close()

    print(f"Done ({ok}/{len(SEED_BOOKINGS)} booking mới được nạp)")


if __name__ == "__main__":
    main()
