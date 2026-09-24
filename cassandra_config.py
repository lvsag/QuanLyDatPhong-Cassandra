from datetime import date, datetime
from cassandra.cluster import Cluster

CASSANDRA_HOST = '127.0.0.1'
CASSANDRA_PORT = 9042
KEYSPACE = 'hotel_booking'

# Global Connection Singleton
_global_cluster = None
_global_session = None
_tables_initialized = False


def to_py_date(val):
    """Chuyển đổi cassandra.util.Date hoặc chuỗi thành datetime.date chuẩn của Python."""
    if val is None:
        return None
    if isinstance(val, date) and type(val) is date:
        return val
    if hasattr(val, 'date') and callable(val.date):
        return val.date()
    if hasattr(val, 'year') and hasattr(val, 'month') and hasattr(val, 'day'):
        return date(val.year, val.month, val.day)
    try:
        return datetime.strptime(str(val), "%Y-%m-%d").date()
    except Exception:
        return val


def get_session():
    """Tạo hoặc tái sử dụng session kết nối vào keyspace hotel_booking (Singleton Connection Pool)."""
    global _global_cluster, _global_session

    if _global_session is not None and not _global_session.is_shutdown:
        return _global_cluster, _global_session

    _global_cluster = Cluster(
        contact_points=[CASSANDRA_HOST],
        port=CASSANDRA_PORT
    )
    session = _global_cluster.connect()

    # Tạo keyspace nếu chưa tồn tại
    session.execute(
        """
        CREATE KEYSPACE IF NOT EXISTS %s
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """ % KEYSPACE
    )
    session.set_keyspace(KEYSPACE)

    _global_session = session
    return _global_cluster, _global_session


def close_session(cluster=None):
    """Đóng kết nối Cassandra toàn cục khi shutdown ứng dụng."""
    global _global_cluster, _global_session
    if _global_cluster:
        _global_cluster.shutdown()
        _global_cluster = None
        _global_session = None
        print("[OK] Da dong ket noi Cassandra")