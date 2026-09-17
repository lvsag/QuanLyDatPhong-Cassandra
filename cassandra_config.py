from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy

CASSANDRA_HOST = '127.0.0.1'
CASSANDRA_PORT = 9042
KEYSPACE = 'hotel_booking'


def get_session():
    """Tạo session kết nối vào keyspace hotel_booking."""
    cluster = Cluster(
        contact_points=[CASSANDRA_HOST],
        port=CASSANDRA_PORT,
    )
    # Connect without keyspace first so we can ensure keyspace exists
    session = cluster.connect()
    # Create keyspace if it doesn't exist (helps avoid failures when running app)
    session.execute(
        """
        CREATE KEYSPACE IF NOT EXISTS %s
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """ % KEYSPACE
    )
    # Now set the keyspace for the session
    session.set_keyspace(KEYSPACE)
    print(f"✅ Đã kết nối Cassandra - keyspace: {KEYSPACE}")
    # Ensure required tables exist so repositories can prepare statements
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
    # Ensure bookings_by_date uses a composite partition key (booking_date, hotel_id)
    # Create if not exists (do NOT drop existing data)
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
    session.execute("""
        CREATE TABLE IF NOT EXISTS customers_by_email (
            email text,
            customer_id uuid,
            full_name text,
            phone text,
            PRIMARY KEY (email)
        )
    """)
    return cluster, session


def close_session(cluster):
    """Đóng kết nối."""
    cluster.shutdown()
    print("🔌 Đã đóng kết nối Cassandra")