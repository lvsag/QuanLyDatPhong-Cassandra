from cassandra.cluster import Cluster

cluster = Cluster(['127.0.0.1'], port=9042)
session = cluster.connect('hotel_booking')

rows = session.execute(
    "SELECT column_name, kind, position, type FROM system_schema.columns "
    "WHERE keyspace_name='hotel_booking' AND table_name='bookings_by_date'"
)
print('columns for bookings_by_date:')
for r in rows:
    print(r)

rows2 = session.execute(
    "SELECT * FROM system_schema.tables WHERE keyspace_name='hotel_booking' AND table_name='bookings_by_date'"
)
print('\ntable info:')
for r in rows2:
    print(r)

cluster.shutdown()
