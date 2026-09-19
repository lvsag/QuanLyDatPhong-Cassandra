"""In khóa chính (partition key / clustering key) của tất cả các bảng để kiểm tra thiết kế."""
from cassandra.cluster import Cluster

cluster = Cluster(['127.0.0.1'], port=9042)
session = cluster.connect('hotel_booking')

rows = session.execute(
    "SELECT table_name, column_name, kind, position, type FROM system_schema.columns "
    "WHERE keyspace_name = 'hotel_booking'"
)

tables = {}
for r in rows:
    tables.setdefault(r.table_name, []).append(r)

for name in sorted(tables):
    cols = tables[name]
    pk = sorted((c for c in cols if c.kind == 'partition_key'), key=lambda c: c.position)
    ck = sorted((c for c in cols if c.kind == 'clustering'), key=lambda c: c.position)
    print(f"\n{name}")
    print("  partition key :", ", ".join(c.column_name for c in pk))
    print("  clustering key:", ", ".join(c.column_name for c in ck) or "(không có)")
    others = [c.column_name for c in cols if c.kind == 'regular']
    print("  cột thường    :", ", ".join(sorted(others)))

cluster.shutdown()
