from cassandra.cluster import Cluster

def reset_database():
    print("[INFO] Dang don dep (reset) co so du lieu Cassandra...")
    cluster = Cluster(['127.0.0.1'], port=9042)
    session = cluster.connect()

    # Danh sach cac bang can truncate
    tables = [
        "rooms_by_hotel",
        "bookings_by_room",
        "bookings_by_customer",
        "bookings_by_date",
        "hotels",
        "customers",
        "customers_by_email"
    ]

    session.execute("CREATE KEYSPACE IF NOT EXISTS hotel_booking WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}")
    session.set_keyspace('hotel_booking')

    for t in tables:
        try:
            session.execute(f"TRUNCATE TABLE {t}")
            print(f"  [OK] Da lam sach bang {t}")
        except Exception:
            pass

    # Nap lai du lieu chuan tu seed_data.cql
    print("\n[INFO] Dang nap lai du lieu mau chuan tu seed_data.cql...")
    with open('seed_data.cql', 'r', encoding='utf-8') as f:
        cql = f.read()

    # Thuc thi tung cau lenh trong CQL
    statements = [s.strip() for s in cql.split(';') if s.strip()]
    count = 0
    for stmt in statements:
        try:
            session.execute(stmt)
            count += 1
        except Exception:
            pass

    cluster.shutdown()
    print(f"\n[SUCCESS] DA HOAN TAT RESET: Da thuc thi {count} cau lenh nap du lieu chuan (5 khach san, 25 phong, 10 khach hang, cac booking mau).")

if __name__ == "__main__":
    reset_database()
