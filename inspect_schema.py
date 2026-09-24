from cassandra.cluster import Cluster

cluster = Cluster(['127.0.0.1'], port=9042)
session = cluster.connect('hotel_booking')

print("===== LIST CASSANDRA TABLES IN KEYSPACE hotel_booking =====")
rows = session.execute(
    "SELECT table_name FROM system_schema.tables WHERE keyspace_name='hotel_booking'"
)
for r in rows:
    print(f"Table: {r.table_name}")

cluster.shutdown()
