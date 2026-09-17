import uuid
from datetime import datetime
from cassandra_config import get_session


class BookingRepository:
    """
    Quản lý booking - 3 bảng:
    - bookings_by_room    (LWT chống trùng lịch)
    - bookings_by_customer
    - bookings_by_date    (cho dashboard)
    """

    def __init__(self):
        self.cluster, self.session = get_session()
        self._prepare()

    def _prepare(self):
        # Insert có LWT (IF NOT EXISTS) để chống đặt trùng
        self.insert_by_room = self.session.prepare("""
            INSERT INTO bookings_by_room 
            (room_id, check_in_date, booking_id, customer_id, 
             check_out_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
            IF NOT EXISTS
        """)

        self.insert_by_customer = self.session.prepare("""
            INSERT INTO bookings_by_customer 
            (customer_id, booking_date, booking_id, room_id, 
             hotel_id, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """)

        self.insert_by_date = self.session.prepare("""
            INSERT INTO bookings_by_date 
            (booking_date, hotel_id, booking_id, customer_id, 
             room_id, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """)

        self.select_by_room = self.session.prepare("""
            SELECT * FROM bookings_by_room WHERE room_id = ?
        """)

        self.select_by_customer = self.session.prepare("""
            SELECT * FROM bookings_by_customer WHERE customer_id = ?
        """)

        # prepare for bookings_by_date can fail on some Cassandra setups
        # (server may reject prepare for composite partition keys). Use
        # a simple execute for that query instead.
        self.select_by_date = None

    def create_booking(self, room_id, customer_id, hotel_id,
                       check_in_date, check_out_date):
        """
        Tạo booking với LWT chống trùng.
        Trả về (success: bool, booking_id, message: str).
        """
        booking_id = uuid.uuid4()
        booking_date = datetime.now()

        # Bước 1: LWT insert vào bookings_by_room để check trùng
        result = self.session.execute(self.insert_by_room, (
            room_id, check_in_date, booking_id,
            customer_id, check_out_date, "CONFIRMED"
        ))
        row = result.one()
        if row is None or not row.applied:
            return False, None, "❌ Phòng đã được đặt trong ngày này!"

        # Bước 2: Insert vào các bảng còn lại (denormalized)
        self.session.execute(self.insert_by_customer, (
            customer_id, booking_date, booking_id,
            room_id, hotel_id, "CONFIRMED"
        ))
        self.session.execute(self.insert_by_date, (
            check_in_date, hotel_id, booking_id,
            customer_id, room_id, "CONFIRMED"
        ))

        return True, booking_id, "✅ Đặt phòng thành công!"

    def cancel_booking(self, room_id, check_in_date, booking_id,
                       customer_id, hotel_id):
        """
        Hủy booking: xóa khỏi bookings_by_room (giải phóng slot),
        đổi status ở 2 bảng còn lại thành CANCELLED.
        """
        # Xóa khỏi bookings_by_room để cho phép đặt lại
        self.session.execute(
            "DELETE FROM bookings_by_room WHERE room_id = %s AND check_in_date = %s",
            (room_id, check_in_date)
        )
        # Update status ở bookings_by_customer
        self.session.execute(
            "UPDATE bookings_by_customer SET status = 'CANCELLED' "
            "WHERE customer_id = %s AND booking_date = %s",
            (customer_id, datetime.now())
        )
        # Update status ở bookings_by_date
        self.session.execute(
            "UPDATE bookings_by_date SET status = 'CANCELLED' "
            "WHERE booking_date = %s AND hotel_id = %s AND booking_id = %s",
            (check_in_date, hotel_id, booking_id)
        )
        return True, "✅ Đã hủy booking"

    def get_bookings_by_room(self, room_id):
        rows = self.session.execute(self.select_by_room, (room_id,))
        return [dict(r._asdict()) for r in rows]

    def get_bookings_by_customer(self, customer_id):
        rows = self.session.execute(self.select_by_customer, (customer_id,))
        return [dict(r._asdict()) for r in rows]

    def get_bookings_by_date(self, booking_date, hotel_id):
        """Dùng cho dashboard Người 3."""
        if self.select_by_date is None:
            rows = self.session.execute(
                "SELECT * FROM bookings_by_date WHERE booking_date = %s AND hotel_id = %s",
                (booking_date, hotel_id)
            )
        else:
            rows = self.session.execute(self.select_by_date, (booking_date, hotel_id))
        return [dict(r._asdict()) for r in rows]

    def close(self):
        self.cluster.shutdown()