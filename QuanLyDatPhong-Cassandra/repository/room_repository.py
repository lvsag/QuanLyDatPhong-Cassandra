import uuid
from cassandra_config import get_session


class RoomRepository:
    """Quản lý phòng - bảng rooms_by_hotel"""

    def __init__(self):
        self.cluster, self.session = get_session()
        self._prepare()

    def _prepare(self):
        self.insert_stmt = self.session.prepare("""
            INSERT INTO rooms_by_hotel 
            (hotel_id, room_id, room_number, room_type, price, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """)
        self.select_by_hotel = self.session.prepare("""
            SELECT * FROM rooms_by_hotel WHERE hotel_id = ?
        """)
        self.select_one = self.session.prepare("""
            SELECT * FROM rooms_by_hotel 
            WHERE hotel_id = ? AND room_id = ?
        """)
        # use a distinct name for the prepared statement to avoid
        # shadowing the instance method `update_status`
        self.update_status_stmt = self.session.prepare("""
            UPDATE rooms_by_hotel SET status = ?
            WHERE hotel_id = ? AND room_id = ?
        """)
        self.delete_stmt = self.session.prepare("""
            DELETE FROM rooms_by_hotel 
            WHERE hotel_id = ? AND room_id = ?
        """)

    def create(self, hotel_id, room_number, room_type, price,
               status="AVAILABLE"):
        room_id = uuid.uuid4()
        self.session.execute(self.insert_stmt, (
            hotel_id, room_id, room_number, room_type, price, status
        ))
        return room_id

    def get_by_hotel(self, hotel_id):
        rows = self.session.execute(self.select_by_hotel, (hotel_id,))
        return [dict(r._asdict()) for r in rows]

    def get_one(self, hotel_id, room_id):
        row = self.session.execute(self.select_one, (hotel_id, room_id)).one()
        return dict(row._asdict()) if row else None

    def update_status(self, hotel_id, room_id, status):
        self.session.execute(self.update_status_stmt, (status, hotel_id, room_id))

    def delete(self, hotel_id, room_id):
        self.session.execute(self.delete_stmt, (hotel_id, room_id))

    def close(self):
        self.cluster.shutdown()