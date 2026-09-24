import uuid
from decimal import Decimal
from cassandra_config import get_session


class RoomRepository:
    """Quản lý phòng - Bảng rooms_by_hotel"""

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
        self.update_status_stmt = self.session.prepare("""
            UPDATE rooms_by_hotel SET status = ?
            WHERE hotel_id = ? AND room_id = ?
        """)
        self.update_info_stmt = self.session.prepare("""
            UPDATE rooms_by_hotel 
            SET room_number = ?, room_type = ?, price = ?
            WHERE hotel_id = ? AND room_id = ?
        """)
        self.delete_stmt = self.session.prepare("""
            DELETE FROM rooms_by_hotel 
            WHERE hotel_id = ? AND room_id = ?
        """)

    def create(self, hotel_id, room_number, room_type, price, status="AVAILABLE"):
        h_id = uuid.UUID(str(hotel_id)) if isinstance(hotel_id, str) else hotel_id
        room_id = uuid.uuid4()
        dec_price = Decimal(str(price))
        self.session.execute(self.insert_stmt, (
            h_id, room_id, str(room_number), str(room_type), dec_price, str(status)
        ))
        return room_id

    def get_by_hotel(self, hotel_id):
        h_id = uuid.UUID(str(hotel_id)) if isinstance(hotel_id, str) else hotel_id
        rows = self.session.execute(self.select_by_hotel, (h_id,))
        return [dict(r._asdict()) for r in rows]

    def get_one(self, hotel_id, room_id):
        h_id = uuid.UUID(str(hotel_id)) if isinstance(hotel_id, str) else hotel_id
        r_id = uuid.UUID(str(room_id)) if isinstance(room_id, str) else room_id
        row = self.session.execute(self.select_one, (h_id, r_id)).one()
        return dict(row._asdict()) if row else None

    def update_info(self, hotel_id, room_id, room_number, room_type, price):
        h_id = uuid.UUID(str(hotel_id)) if isinstance(hotel_id, str) else hotel_id
        r_id = uuid.UUID(str(room_id)) if isinstance(room_id, str) else room_id
        dec_price = Decimal(str(price))
        self.session.execute(self.update_info_stmt, (
            str(room_number), str(room_type), dec_price, h_id, r_id
        ))

    def update_status(self, hotel_id, room_id, status):
        h_id = uuid.UUID(str(hotel_id)) if isinstance(hotel_id, str) else hotel_id
        r_id = uuid.UUID(str(room_id)) if isinstance(room_id, str) else room_id
        self.session.execute(self.update_status_stmt, (str(status), h_id, r_id))

    def delete(self, hotel_id, room_id):
        h_id = uuid.UUID(str(hotel_id)) if isinstance(hotel_id, str) else hotel_id
        r_id = uuid.UUID(str(room_id)) if isinstance(room_id, str) else room_id
        self.session.execute(self.delete_stmt, (h_id, r_id))

    def close(self):
        pass