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
    global _global_cluster, _global_session, _tables_initialized

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
    print(f"[OK] Da ket noi Cassandra - keyspace: {KEYSPACE}")

    if not _tables_initialized:
        # Khởi tạo bảng 1 lần duy nhất lúc khởi động app
        session.execute("""
            CREATE TABLE IF NOT EXISTS rooms_by_hotel (
                hotel_id uuid,
                room_id uuid,
                room_number text,
                room_type text,
                price decimal,
                status text,
                PRIMARY KEY (hotel_id, room_id)
            )
        """)
        session.execute("""
            CREATE TABLE IF NOT EXISTS bookings_by_room (
                room_id uuid,
                check_in_date date,
                booking_id uuid,
                customer_id uuid,
                check_out_date date,
                status text,
                PRIMARY KEY (room_id, check_in_date)
            )
        """)
        session.execute("""
            CREATE TABLE IF NOT EXISTS bookings_by_customer (
                customer_id uuid,
                booking_date timestamp,
                booking_id uuid,
                room_id uuid,
                hotel_id uuid,
                status text,
                PRIMARY KEY (customer_id, booking_date)
            )
        """)
        session.execute("""
            CREATE TABLE IF NOT EXISTS bookings_by_date (
                booking_date date,
                hotel_id uuid,
                booking_id uuid,
                customer_id uuid,
                room_id uuid,
                status text,
                PRIMARY KEY ((booking_date, hotel_id), booking_id)
            )
        """)
        session.execute("""
            CREATE TABLE IF NOT EXISTS hotels (
                hotel_id uuid,
                name text,
                address text,
                city text,
                phone text,
                rating decimal,
                created_at timestamp,
                PRIMARY KEY (hotel_id)
            )
        """)
        session.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id uuid,
                full_name text,
                email text,
                phone text,
                id_number text,
                created_at timestamp,
                PRIMARY KEY (customer_id)
            )
        """)
        try:
            session.execute("ALTER TABLE customers ADD password_hash text")
        except Exception:
            pass
        session.execute("""
            CREATE TABLE IF NOT EXISTS customers_by_email (
                email text,
                customer_id uuid,
                full_name text,
                phone text,
                password_hash text,
                PRIMARY KEY (email)
            )
        """)
        try:
            session.execute("ALTER TABLE customers_by_email ADD password_hash text")
        except Exception:
            pass
        _tables_initialized = True

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