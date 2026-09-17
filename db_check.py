from cassandra_config import get_session

cluster, session = get_session()

tables = [
    'hotels',
    'customers',
    'customers_by_email',
    'rooms_by_hotel',
    'bookings_by_room',
    'bookings_by_customer',
    'bookings_by_date'
]

for t in tables:
    try:
        count_row = session.execute(f"SELECT count(*) FROM {t}").one()
        count = count_row[0] if count_row is not None else 'unknown'
        print(f"{t}: count={count}")
        rows = session.execute(f"SELECT * FROM {t} LIMIT 5")
        for r in rows:
            print('  ', dict(r._asdict()))
    except Exception as e:
        print(f"{t}: ERROR -> {e}")

cluster.shutdown()
