import os

from cassandra.cluster import Cluster

CASSANDRA_HOST = '127.0.0.1'
CASSANDRA_PORT = 9042
KEYSPACE = 'hotel_booking'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(BASE_DIR, 'schema.cql')

# Các bảng của thiết kế cũ. Nếu còn thấy chúng trong keyspace nghĩa là DB đang ở schema cũ
# (khóa chính của bảng Cassandra không sửa được nên phải tạo lại)
LEGACY_TABLES = {'bookings_by_room', 'bookings_by_date'}

_schema_ready = False


def load_cql_statements(path):
    """Đọc file .cql, bỏ dòng comment, tách thành từng câu lệnh."""
    with open(path, 'r', encoding='utf-8') as f:
        lines = [ln for ln in f.read().splitlines() if not ln.strip().startswith('--')]
    return [s.strip() for s in '\n'.join(lines).split(';') if s.strip()]


def ensure_schema(session):
    """Tạo bảng từ schema.cql (CREATE IF NOT EXISTS). Chỉ chạy 1 lần cho mỗi tiến trình."""
    global _schema_ready
    if _schema_ready:
        return

    rows = session.execute(
        "SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s",
        (KEYSPACE,),
    )
    legacy = LEGACY_TABLES & {r.table_name for r in rows}
    if legacy:
        raise RuntimeError(
            f"Keyspace '{KEYSPACE}' đang dùng schema cũ (còn bảng: {', '.join(sorted(legacy))}). "
            "Chạy `python seed_db.py --reset` để xóa và tạo lại theo schema mới."
        )

    for stmt in load_cql_statements(SCHEMA_FILE):
        session.execute(stmt)
    _schema_ready = True


def get_session():
    """Tạo session kết nối vào keyspace hotel_booking (tự tạo keyspace và bảng nếu chưa có)."""
    cluster = Cluster(
        contact_points=[CASSANDRA_HOST],
        port=CASSANDRA_PORT,
    )
    try:
        # Kết nối không chỉ định keyspace trước để đảm bảo keyspace tồn tại
        session = cluster.connect()
        session.execute(
            """
            CREATE KEYSPACE IF NOT EXISTS %s
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
            """ % KEYSPACE
        )
        session.set_keyspace(KEYSPACE)
        ensure_schema(session)
    except Exception:
        cluster.shutdown()
        raise
    print(f"✅ Đã kết nối Cassandra - keyspace: {KEYSPACE}")
    return cluster, session


def close_session(cluster):
    """Đóng kết nối."""
    cluster.shutdown()
    print("🔌 Đã đóng kết nối Cassandra")
