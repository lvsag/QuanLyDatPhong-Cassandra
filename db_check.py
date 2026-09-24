from cassandra_config import get_session

cluster, session = get_session()

tables = [
    'hotels',
    'hotels_by_city',
    'customers',
    'customers_by_email',
    'rooms_by_hotel',
    'bookings_by_id',
    'bookings_by_customer',
    'room_nights_by_room',
    'room_nights_by_hotel_date'
]

print("===== CASSANDRA DATABASE SUMMARY =====")
for t in tables:
    try:
        count_row = session.execute(f"SELECT count(*) FROM {t}").one()
        count = count_row[0] if count_row is not None else 'unknown'
        print(f"Bảng '{t}': {count} rows")
    except Exception as e:
        print(f"Bảng '{t}': ERROR -> {e}")

cluster.shutdown()
