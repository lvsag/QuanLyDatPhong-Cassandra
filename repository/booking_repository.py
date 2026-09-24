import uuid
from decimal import Decimal
from datetime import datetime, date, timedelta
from cassandra.query import BatchStatement, BatchType
from cassandra_config import get_session, to_py_date


class BookingRepository:
    """
    Quản lý Đặt phòng & Read Models theo NoSQL Query-First Architecture:
    - bookings_by_id (Source/Read model theo booking_id)
    - bookings_by_customer (Lịch sử khách hàng xếp theo timeuuid)
    - room_nights_by_room (LWT Paxos Conditional Batch chống trùng phòng)
    - room_nights_by_hotel_date (Báo cáo dashboard, occupancy, revenue, Q10 check-in)
    """

    def __init__(self):
        self.cluster, self.session = get_session()
        self._prepare()

    def _prepare(self):
        # 1. Lock room night với LWT IF NOT EXISTS
        self.insert_room_night_lwt = self.session.prepare("""
            INSERT INTO room_nights_by_room 
            (room_id, stay_date, booking_id, customer_id, hotel_id, 
             check_in_date, check_out_date, price_per_night, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            IF NOT EXISTS
        """)

        # 2. Insert read models
        self.insert_booking_by_id = self.session.prepare("""
            INSERT INTO bookings_by_id 
            (booking_id, customer_id, hotel_id, room_id, check_in_date, 
             check_out_date, booking_date, price_per_night, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        self.insert_booking_by_customer = self.session.prepare("""
            INSERT INTO bookings_by_customer 
            (customer_id, booking_id, hotel_id, room_id, check_in_date, 
             check_out_date, booking_date, price_per_night, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        self.insert_room_night_by_hotel_date = self.session.prepare("""
            INSERT INTO room_nights_by_hotel_date 
            (hotel_id, stay_date, room_id, booking_id, customer_id, 
             check_in_date, check_out_date, price_per_night, status, 
             customer_name, room_number, room_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        # 3. Queries
        self.select_by_id = self.session.prepare("""
            SELECT * FROM bookings_by_id WHERE booking_id = ?
        """)

        self.select_by_customer = self.session.prepare("""
            SELECT * FROM bookings_by_customer WHERE customer_id = ?
        """)

        self.select_room_night = self.session.prepare("""
            SELECT * FROM room_nights_by_room WHERE room_id = ? AND stay_date = ?
        """)

        self.select_room_nights_by_hotel_date = self.session.prepare("""
            SELECT * FROM room_nights_by_hotel_date WHERE hotel_id = ? AND stay_date = ?
        """)

        # 4. LWT Conditional Updates & Deletions
        self.cancel_lwt_booking_by_id = self.session.prepare("""
            UPDATE bookings_by_id SET status = 'CANCELLED'
            WHERE booking_id = ?
            IF status = 'CONFIRMED'
        """)

        self.update_booking_customer_status = self.session.prepare("""
            UPDATE bookings_by_customer SET status = ?
            WHERE customer_id = ? AND booking_id = ?
        """)

        self.delete_room_night = self.session.prepare("""
            DELETE FROM room_nights_by_room WHERE room_id = ? AND stay_date = ?
        """)

        self.delete_hotel_date_night = self.session.prepare("""
            DELETE FROM room_nights_by_hotel_date 
            WHERE hotel_id = ? AND stay_date = ? AND room_id = ?
        """)

    def _get_stay_dates(self, check_in_date, check_out_date):
        """Trả về danh sách các đêm lưu trú [check_in_date, check_out_date)."""
        c_in = to_py_date(check_in_date)
        c_out = to_py_date(check_out_date)
        curr = c_in
        res = []
        while curr < c_out:
            res.append(curr)
            curr += timedelta(days=1)
        return res

    def check_room_available(self, room_id, check_in_date, check_out_date):
        """Kiểm tra xem phòng có bị trùng lịch đêm nào trong [check_in_date, check_out_date) không."""
        r_id = uuid.UUID(str(room_id)) if isinstance(room_id, str) else room_id
        stay_dates = self._get_stay_dates(check_in_date, check_out_date)
        for s_date in stay_dates:
            row = self.session.execute(self.select_room_night, (r_id, s_date)).one()
            if row and row.status in ["CONFIRMED", "CHECKED_IN"]:
                return False
        return True

    def create_booking(self, room_id, customer_id, hotel_id, check_in_date, check_out_date,
                       price_per_night=None, customer_name=None, room_number=None, room_type=None):
        """
        Tạo đơn đặt phòng bằng Paxos LWT Single-Partition Conditional Batch.
        Mọi stay_date của booking thuộc cùng partition `room_id`.
        Snapshot giá phòng và thông tin khách tại thời điểm đặt.
        """
        r_id = uuid.UUID(str(room_id)) if isinstance(room_id, str) else room_id
        c_id = uuid.UUID(str(customer_id)) if isinstance(customer_id, str) else customer_id
        h_id = uuid.UUID(str(hotel_id)) if isinstance(hotel_id, str) else hotel_id

        c_in = to_py_date(check_in_date)
        c_out = to_py_date(check_out_date)

        if c_out <= c_in:
            return False, None, "❌ Ngày Check-out phải sau ngày Check-in ít nhất 1 ngày!"

        stay_dates = self._get_stay_dates(c_in, c_out)
        nights = len(stay_dates)

        # Lấy thông tin bổ sung để snapshot nếu chưa có
        if price_per_night is None or room_number is None or room_type is None:
            r_row = self.session.execute(
                "SELECT room_number, room_type, price FROM rooms_by_hotel WHERE hotel_id = %s AND room_id = %s",
                (h_id, r_id)
            ).one()
            if r_row:
                room_number = room_number or r_row.room_number
                room_type = room_type or r_row.room_type
                price_per_night = price_per_night or r_row.price
            else:
                price_per_night = price_per_night or Decimal("100.0")

        if customer_name is None:
            c_row = self.session.execute("SELECT full_name FROM customers WHERE customer_id = %s", (c_id,)).one()
            customer_name = c_row.full_name if c_row else "Khách hàng"

        price_dec = Decimal(str(price_per_night))
        total_amount = price_dec * nights
        booking_id = uuid.uuid1()  # TimeUUID
        booking_date = datetime.now()

        # BƯỚC 1: Paxos LWT Conditional Batch khóa các đêm của room_id
        batch = BatchStatement(batch_type=BatchType.LOGGED)
        for s_date in stay_dates:
            batch.add(self.insert_room_night_lwt, (
                r_id, s_date, booking_id, c_id, h_id, c_in, c_out, price_dec, "CONFIRMED"
            ))

        res = self.session.execute(batch)
        row = res.one()
        if row is None or not row.applied:
            return False, None, "❌ Phòng đã có người đặt trong khoảng thời gian này!"

        # BƯỚC 2: Ghi dữ liệu vào các Read Models denormalized
        self.session.execute(self.insert_booking_by_id, (
            booking_id, c_id, h_id, r_id, c_in, c_out, booking_date, price_dec, total_amount, "CONFIRMED"
        ))

        self.session.execute(self.insert_booking_by_customer, (
            c_id, booking_id, h_id, r_id, c_in, c_out, booking_date, price_dec, total_amount, "CONFIRMED"
        ))

        for s_date in stay_dates:
            self.session.execute(self.insert_room_night_by_hotel_date, (
                h_id, s_date, r_id, booking_id, c_id, c_in, c_out, price_dec, "CONFIRMED",
                str(customer_name), str(room_number), str(room_type)
            ))

        return True, booking_id, "✅ Đặt phòng thành công!"

    def get_booking_by_id(self, booking_id):
        b_id = uuid.UUID(str(booking_id)) if isinstance(booking_id, str) else booking_id
        row = self.session.execute(self.select_by_id, (b_id,)).one()
        if not row:
            return None
        d = dict(row._asdict())
        d["check_in_date"] = to_py_date(d.get("check_in_date"))
        d["check_out_date"] = to_py_date(d.get("check_out_date"))
        return d

    def get_bookings_by_customer(self, customer_id):
        c_id = uuid.UUID(str(customer_id)) if isinstance(customer_id, str) else customer_id
        rows = self.session.execute(self.select_by_customer, (c_id,))
        res = []
        for r in rows:
            d = dict(r._asdict())
            d["check_in_date"] = to_py_date(d.get("check_in_date"))
            d["check_out_date"] = to_py_date(d.get("check_out_date"))
            res.append(d)
        return res

    def get_room_nights_by_hotel_date(self, hotel_id, stay_date):
        h_id = uuid.UUID(str(hotel_id)) if isinstance(hotel_id, str) else hotel_id
        s_date = to_py_date(stay_date)
        rows = self.session.execute(self.select_room_nights_by_hotel_date, (h_id, s_date))
        res = []
        for r in rows:
            d = dict(r._asdict())
            d["stay_date"] = to_py_date(d.get("stay_date"))
            d["check_in_date"] = to_py_date(d.get("check_in_date"))
            d["check_out_date"] = to_py_date(d.get("check_out_date"))
            res.append(d)
        return res

    def cancel_booking(self, booking_id):
        """
        Hủy booking dựa theo booking_id duy nhất:
        1. Kiểm tra trạng thái CONFIRMED
        2. Chuyển trạng thái LWT ở bookings_by_id sang CANCELLED
        3. Cập nhật status ở bookings_by_customer
        4. Xóa khóa các đêm lưu trú trong room_nights_by_room & room_nights_by_hotel_date
        """
        booking = self.get_booking_by_id(booking_id)
        if not booking:
            return False, "❌ Không tìm thấy đơn đặt phòng!"

        if booking["status"] != "CONFIRMED":
            return False, f"❌ Đơn đặt phòng hiện ở trạng thái '{booking['status']}', không thể hủy!"

        b_id = booking["booking_id"]
        c_id = booking["customer_id"]
        h_id = booking["hotel_id"]
        r_id = booking["room_id"]
        c_in = booking["check_in_date"]
        c_out = booking["check_out_date"]

        # LWT conditional update trên bookings_by_id
        res = self.session.execute(self.cancel_lwt_booking_by_id, (b_id,))
        row = res.one()
        if row is None or not row.applied:
            return False, "❌ Đơn đặt phòng đã bị chuyển trạng thái hoặc đã bị hủy trước đó!"

        # Update status ở bookings_by_customer
        self.session.execute(self.update_booking_customer_status, ("CANCELLED", c_id, b_id))

        # Giải phóng các đêm lưu trú khỏi room_nights_by_room & room_nights_by_hotel_date
        stay_dates = self._get_stay_dates(c_in, c_out)
        for s_date in stay_dates:
            self.session.execute(self.delete_room_night, (r_id, s_date))
            self.session.execute(self.delete_hotel_date_night, (h_id, s_date, r_id))

        return True, "✅ Hủy đơn đặt phòng thành công!"

    def update_booking_status(self, booking_id, new_status):
        """Cập nhật trạng thái booking (ví dụ: CHECKED_IN, CHECKED_OUT)."""
        booking = self.get_booking_by_id(booking_id)
        if not booking:
            return False, "❌ Không tìm thấy đơn đặt phòng"

        b_id = booking["booking_id"]
        c_id = booking["customer_id"]
        h_id = booking["hotel_id"]
        r_id = booking["room_id"]
        c_in = booking["check_in_date"]
        c_out = booking["check_out_date"]

        # Update status ở bookings_by_id & bookings_by_customer
        self.session.execute(
            "UPDATE bookings_by_id SET status = %s WHERE booking_id = %s",
            (new_status, b_id)
        )
        self.session.execute(self.update_booking_customer_status, (new_status, c_id, b_id))

        # Update status ở room_nights
        stay_dates = self._get_stay_dates(c_in, c_out)
        for s_date in stay_dates:
            self.session.execute(
                "UPDATE room_nights_by_room SET status = %s WHERE room_id = %s AND stay_date = %s",
                (new_status, r_id, s_date)
            )
            self.session.execute(
                "UPDATE room_nights_by_hotel_date SET status = %s WHERE hotel_id = %s AND stay_date = %s AND room_id = %s",
                (new_status, h_id, s_date, r_id)
            )

        return True, f"✅ Đã cập nhật trạng thái đơn đặt phòng sang {new_status}"

    def close(self):
        pass