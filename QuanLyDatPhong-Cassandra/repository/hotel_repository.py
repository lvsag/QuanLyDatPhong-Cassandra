import uuid
from datetime import datetime, timezone
from cassandra_config import get_session


class HotelRepository:
    """Quản lý khách sạn - bảng hotels"""

    def __init__(self):
        self.cluster, self.session = get_session()
        self._prepare()

    def _prepare(self):
        self.insert_stmt = self.session.prepare("""
            INSERT INTO hotels 
            (hotel_id, name, address, city, phone, rating, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        self.select_one = self.session.prepare("""
            SELECT * FROM hotels WHERE hotel_id = ?
        """)
        self.select_all = "SELECT * FROM hotels"
        self.update_stmt = self.session.prepare("""
            UPDATE hotels SET name = ?, address = ?, city = ?, 
                              phone = ?, rating = ?
            WHERE hotel_id = ?
        """)
        self.delete_stmt = self.session.prepare("""
            DELETE FROM hotels WHERE hotel_id = ?
        """)

    def create(self, name, address, city, phone, rating=0.0):
        """Tạo khách sạn mới, trả về hotel_id."""
        hotel_id = uuid.uuid4()
        self.session.execute(self.insert_stmt, (
            hotel_id, name, address, city, phone,
            rating, datetime.now(timezone.utc)
        ))
        return hotel_id

    def get_by_id(self, hotel_id):
        row = self.session.execute(self.select_one, (hotel_id,)).one()
        return dict(row._asdict()) if row else None

    def get_all(self):
        rows = self.session.execute(self.select_all)
        return [dict(r._asdict()) for r in rows]

    def update(self, hotel_id, name, address, city, phone, rating):
        self.session.execute(self.update_stmt, (
            name, address, city, phone, rating, hotel_id
        ))

    def delete(self, hotel_id):
        self.session.execute(self.delete_stmt, (hotel_id,))

    def close(self):
        self.cluster.shutdown()