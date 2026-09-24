import uuid
from decimal import Decimal
from datetime import datetime
from cassandra_config import get_session


class HotelRepository:
    """Quản lý khách sạn - Bảng hotels & hotels_by_city (No ALLOW FILTERING)"""

    def __init__(self):
        self.cluster, self.session = get_session()
        self._prepare()

    def _prepare(self):
        self.insert_hotel = self.session.prepare("""
            INSERT INTO hotels 
            (hotel_id, name, address, city, phone, rating, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        self.insert_by_city = self.session.prepare("""
            INSERT INTO hotels_by_city
            (city, hotel_id, name, address, phone, rating)
            VALUES (?, ?, ?, ?, ?, ?)
        """)
        self.select_one = self.session.prepare("""
            SELECT * FROM hotels WHERE hotel_id = ?
        """)
        self.select_all = "SELECT * FROM hotels"
        self.select_by_city = self.session.prepare("""
            SELECT * FROM hotels_by_city WHERE city = ?
        """)
        self.delete_hotel = self.session.prepare("""
            DELETE FROM hotels WHERE hotel_id = ?
        """)
        self.delete_by_city = self.session.prepare("""
            DELETE FROM hotels_by_city WHERE city = ? AND hotel_id = ?
        """)

    def create(self, name, address, city, phone, rating=0.0):
        """Tạo khách sạn mới, ghi vào cả 2 bảng (denormalized)."""
        hotel_id = uuid.uuid4()
        now = datetime.now()
        rating_dec = Decimal(str(rating))

        self.session.execute(self.insert_hotel, (
            hotel_id, name, address, city, phone, rating_dec, now
        ))
        self.session.execute(self.insert_by_city, (
            city, hotel_id, name, address, phone, rating_dec
        ))
        return hotel_id

    def get_by_id(self, hotel_id):
        h_id = uuid.UUID(str(hotel_id)) if isinstance(hotel_id, str) else hotel_id
        row = self.session.execute(self.select_one, (h_id,)).one()
        return dict(row._asdict()) if row else None

    def get_all(self):
        rows = self.session.execute(self.select_all)
        return [dict(r._asdict()) for r in rows]

    def search_by_city(self, city):
        """Tìm kiếm khách sạn theo thành phố (Query trực tiếp partition key, không dùng ALLOW FILTERING)"""
        rows = self.session.execute(self.select_by_city, (city,))
        return [dict(r._asdict()) for r in rows]

    def update(self, hotel_id, name, address, city, phone, rating):
        h_id = uuid.UUID(str(hotel_id)) if isinstance(hotel_id, str) else hotel_id
        existing = self.get_by_id(h_id)
        rating_dec = Decimal(str(rating))
        created_at = existing.get("created_at") if existing else datetime.now()

        if existing and existing.get("city") and existing.get("city") != city:
            self.session.execute(self.delete_by_city, (existing["city"], h_id))

        self.session.execute(self.insert_hotel, (
            h_id, name, address, city, phone, rating_dec, created_at
        ))
        self.session.execute(self.insert_by_city, (
            city, h_id, name, address, phone, rating_dec
        ))

    def delete(self, hotel_id):
        h_id = uuid.UUID(str(hotel_id)) if isinstance(hotel_id, str) else hotel_id
        existing = self.get_by_id(h_id)
        if existing and existing.get("city"):
            self.session.execute(self.delete_by_city, (existing["city"], h_id))
        self.session.execute(self.delete_hotel, (h_id,))

    def close(self):
        pass

    def get_by_id_safe(self, hotel_id):
        return self.get_by_id(hotel_id)

    def update_safe(self, hotel_id, name, address, city, phone, rating):
        self.update(hotel_id, name, address, city, phone, float(rating))

    def delete_safe(self, hotel_id):
        self.delete(hotel_id)