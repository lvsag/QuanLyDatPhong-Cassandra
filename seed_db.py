from datetime import date
from cassandra.cluster import Cluster
from cassandra_config import CASSANDRA_HOST, CASSANDRA_PORT, KEYSPACE
from repository import BookingRepository


def reset_database():
    print("[INFO] Dang don dep (reset) keyspace Cassandra...")
    cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
    session = cluster.connect()

    # Drop keyspace cu de dam bao xoa sach schema cu
    session.execute(f"DROP KEYSPACE IF EXISTS {KEYSPACE}")
    print(f"  [OK] Da DROP KEYSPACE IF EXISTS {KEYSPACE}")

    # Doc va thuc thi DDL tu schema.cql
    print("[INFO] Dang khoi tao Schema moi tu schema.cql...")
    with open('schema.cql', 'r', encoding='utf-8') as f:
        schema_cql = f.read()

    for stmt in [s.strip() for s in schema_cql.split(';') if s.strip()]:
        session.execute(stmt)
    print("  [OK] Da tao thanh cong 9 bang theo thiet ke query-first.")

    # Nap du lieu mau tu seed_data.cql
    print("[INFO] Dang nap du lieu mau tu seed_data.cql...")
    with open('seed_data.cql', 'r', encoding='utf-8') as f:
        seed_cql = f.read()

    for stmt in [s.strip() for s in seed_cql.split(';') if s.strip()]:
        session.execute(stmt)
    print("  [OK] Da nap danh sach khach san, phong, va khach hang mau.")

    cluster.shutdown()

    # Tao cac booking mau thong qua BookingRepository de tao dong bo tat ca denormalized tables
    print("[INFO] Dang tao cac booking mau dong bo tat ca Read Models...")
    booking_repo = BookingRepository()

    sample_bookings = [
        # (room_id, customer_id, hotel_id, check_in, check_out)
        ("20000000-0000-0000-0000-000000000001", "10000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000001", date(2026, 1, 5), date(2026, 1, 8)),
        ("20000000-0000-0000-0000-000000000002", "10000000-0000-0000-0000-000000000002", "00000000-0000-0000-0000-000000000001", date(2026, 1, 6), date(2026, 1, 9)),
        ("20000000-0000-0000-0000-000000000003", "10000000-0000-0000-0000-000000000003", "00000000-0000-0000-0000-000000000001", date(2026, 1, 7), date(2026, 1, 10)),
        ("20000000-0000-0000-0000-000000000007", "10000000-0000-0000-0000-000000000004", "00000000-0000-0000-0000-000000000002", date(2026, 1, 5), date(2026, 1, 9)),
        ("20000000-0000-0000-0000-000000000019", "10000000-0000-0000-0000-000000000005", "00000000-0000-0000-0000-000000000004", date(2026, 1, 6), date(2026, 1, 10)),
        # Multi-month booking test (2026-01-30 to 2026-02-03)
        ("20000000-0000-0000-0000-000000000004", "10000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000001", date(2026, 1, 30), date(2026, 2, 3)),
    ]

    for r_id, c_id, h_id, c_in, c_out in sample_bookings:
        ok, b_id, msg = booking_repo.create_booking(r_id, c_id, h_id, c_in, c_out)
        if ok:
            print(f"  [OK] Da tao booking {b_id} ({c_in} -> {c_out})")
        else:
            print(f"  [FAIL] Loi tao booking: {msg}")

    booking_repo.close()
    print("\n[SUCCESS] DA HOAN TAT SEED DATABASE!")


if __name__ == "__main__":
    reset_database()
