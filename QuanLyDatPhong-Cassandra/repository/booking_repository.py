from datetime import date, datetime, timedelta, timezone

from cassandra.query import BatchStatement, BatchType
from cassandra.util import datetime_from_uuid1, uuid_from_time

from cassandra_config import get_session

CONFIRMED = "CONFIRMED"
CANCELLED = "CANCELLED"

# Giới hạn số đêm của một booking. Mỗi đêm là 1 dòng ở 2 bảng room_nights_*,
# giới hạn này giữ cho batch ghi không quá lớn
MAX_NIGHTS = 30

# Các cột kiểu date: driver trả về cassandra.util.Date, đổi sang datetime.date cho dễ so sánh
_DATE_COLUMNS = ("stay_date", "check_in_date", "check_out_date")


def _to_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return value.date()  # cassandra.util.Date


def _row_to_dict(row):
    data = dict(row._asdict())
    for col in _DATE_COLUMNS:
        if col in data:
            data[col] = _to_date(data[col])
    return data


class BookingRepository:
    """
    Quản lý đặt phòng, gồm 4 bảng:

    - room_nights_by_room       (mỗi đêm của mỗi phòng là 1 dòng, dùng LWT để chống trùng lịch)
    - bookings_by_id            (chi tiết booking, nguồn sự thật)
    - bookings_by_customer      (lịch sử booking của khách)
    - room_nights_by_hotel_date (phòng nào có khách vào đêm nào, phục vụ tìm phòng trống và dashboard)

    Ghi: khóa các đêm bằng LWT trước, thành công mới ghi các bảng còn lại.
    Hủy: đổi trạng thái, xóa các bảng đọc, cuối cùng mới nhả khóa các đêm.
    Nếu lỗi giữa chừng, phòng có thể bị giữ chỗ dư chứ không bao giờ bị đặt trùng.
    """

    def __init__(self):
        self.cluster, self.session = get_session()
        self._prepare()

    def _prepare(self):
        p = self.session.prepare

        # ----- Tra cứu để kiểm tra khóa liên kết (Cassandra không có FOREIGN KEY) -----
        self.select_room = p("""
            SELECT room_number, price, status FROM rooms_by_hotel
            WHERE hotel_id = ? AND room_id = ?
        """)
        self.select_rooms_of_hotel = p("""
            SELECT * FROM rooms_by_hotel WHERE hotel_id = ?
        """)
        self.select_customer = p("""
            SELECT customer_id FROM customers WHERE customer_id = ?
        """)

        # ----- room_nights_by_room: khóa / nhả từng đêm -----
        self.lock_night = p("""
            INSERT INTO room_nights_by_room
            (room_id, stay_date, booking_id, customer_id, check_in_date, check_out_date)
            VALUES (?, ?, ?, ?, ?, ?)
            IF NOT EXISTS
        """)
        # Chỉ nhả đêm nếu đêm đó đúng là của booking này
        self.release_night = p("""
            DELETE FROM room_nights_by_room
            WHERE room_id = ? AND stay_date = ?
            IF booking_id = ?
        """)
        self.select_nights_by_room = p("""
            SELECT * FROM room_nights_by_room WHERE room_id = ?
        """)

        # ----- bookings_by_id -----
        self.insert_booking = p("""
            INSERT INTO bookings_by_id
            (booking_id, customer_id, hotel_id, room_id, room_number,
             check_in_date, check_out_date, nights, price_per_night,
             total_amount, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        self.select_booking = p("""
            SELECT * FROM bookings_by_id WHERE booking_id = ?
        """)
        # LWT: chỉ hủy được booking đang CONFIRMED, chống hủy 2 lần
        self.mark_cancelled = p("""
            UPDATE bookings_by_id SET status = 'CANCELLED', cancelled_at = ?
            WHERE booking_id = ?
            IF status = 'CONFIRMED'
        """)

        # ----- bookings_by_customer -----
        self.insert_by_customer = p("""
            INSERT INTO bookings_by_customer
            (customer_id, booking_id, hotel_id, room_id, room_number,
             check_in_date, check_out_date, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        self.update_by_customer_status = p("""
            UPDATE bookings_by_customer SET status = ?
            WHERE customer_id = ? AND booking_id = ?
        """)
        self.select_by_customer = p("""
            SELECT * FROM bookings_by_customer WHERE customer_id = ?
        """)

        # ----- room_nights_by_hotel_date -----
        self.insert_stay = p("""
            INSERT INTO room_nights_by_hotel_date
            (hotel_id, stay_date, room_id, booking_id, customer_id,
             check_in_date, check_out_date, price_per_night)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """)
        self.delete_stay = p("""
            DELETE FROM room_nights_by_hotel_date
            WHERE hotel_id = ? AND stay_date = ? AND room_id = ?
        """)
        self.select_stays = p("""
            SELECT * FROM room_nights_by_hotel_date
            WHERE hotel_id = ? AND stay_date = ?
        """)

    # ------------------------------------------------------------------
    # Ghi
    # ------------------------------------------------------------------
    def create_booking(self, room_id, customer_id, hotel_id,
                       check_in_date, check_out_date, booking_id=None):
        """
        Tạo booking. Trả về (success: bool, booking_id, message: str).

        Ngày ở tính theo nửa khoảng [check_in, check_out): khách trả phòng
        ngày X và khách khác nhận phòng ngày X là hợp lệ.
        """
        check_in = _to_date(check_in_date)
        check_out = _to_date(check_out_date)
        nights = (check_out - check_in).days
        if nights < 1:
            return False, None, "❌ Ngày check-out phải sau ngày check-in ít nhất 1 ngày"
        if nights > MAX_NIGHTS:
            return False, None, f"❌ Mỗi booking tối đa {MAX_NIGHTS} đêm"

        # Kiểm tra khóa liên kết ở tầng ứng dụng
        room = self.session.execute(self.select_room, (hotel_id, room_id)).one()
        if room is None:
            return False, None, "❌ Phòng không tồn tại trong khách sạn này"
        if room.status == "MAINTENANCE":
            return False, None, "❌ Phòng đang bảo trì"
        if self.session.execute(self.select_customer, (customer_id,)).one() is None:
            return False, None, "❌ Khách hàng không tồn tại"

        if booking_id is None:
            booking_id = uuid_from_time(datetime.now(timezone.utc))
        created_at = datetime_from_uuid1(booking_id)

        price = room.price
        total = price * nights
        stay_dates = [check_in + timedelta(days=i) for i in range(nights)]

        # Bước 1: khóa TẤT CẢ các đêm bằng 1 conditional batch (cùng partition room_id).
        # Chỉ cần 1 đêm đã có người giữ thì cả batch không được áp dụng
        lock = BatchStatement()
        for d in stay_dates:
            lock.add(self.lock_night, (room_id, d, booking_id, customer_id, check_in, check_out))
        result = self.session.execute(lock)
        if not result.was_applied:
            taken = sorted({
                _to_date(r.stay_date) for r in result
                if getattr(r, "stay_date", None) is not None
            })
            detail = f" (trùng đêm: {', '.join(d.isoformat() for d in taken)})" if taken else ""
            return False, None, "❌ Phòng đã có người đặt trong khoảng ngày này" + detail

        # Bước 2: ghi các bảng đọc trong 1 LOGGED batch (khác partition nhưng được đảm bảo ghi đủ)
        try:
            batch = BatchStatement(batch_type=BatchType.LOGGED)
            batch.add(self.insert_booking, (
                booking_id, customer_id, hotel_id, room_id, room.room_number,
                check_in, check_out, nights, price, total, CONFIRMED, created_at
            ))
            batch.add(self.insert_by_customer, (
                customer_id, booking_id, hotel_id, room_id, room.room_number,
                check_in, check_out, total, CONFIRMED
            ))
            for d in stay_dates:
                batch.add(self.insert_stay, (
                    hotel_id, d, room_id, booking_id, customer_id,
                    check_in, check_out, price
                ))
            self.session.execute(batch)
        except Exception:
            # Nhả các đêm vừa khóa để phòng không bị giữ oan
            self._release_nights(room_id, stay_dates, booking_id)
            raise

        return True, booking_id, "✅ Đặt phòng thành công!"

    def cancel_booking(self, room_id=None, check_in_date=None, booking_id=None,
                       customer_id=None, hotel_id=None):
        """
        Hủy booking. Chỉ cần booking_id, các tham số còn lại được giữ để code
        gọi theo chữ ký cũ không bị vỡ và không còn được sử dụng
        (thông tin đầy đủ được đọc từ bookings_by_id).
        Trả về (success: bool, message: str).
        """
        if booking_id is None:
            raise ValueError("cancel_booking cần booking_id")

        booking = self.session.execute(self.select_booking, (booking_id,)).one()
        if booking is None:
            return False, "❌ Không tìm thấy booking"

        # Bước 1: lật trạng thái bằng LWT, chỉ một lần hủy được thành công
        applied = self.session.execute(
            self.mark_cancelled, (datetime.now(timezone.utc), booking_id)
        ).one().applied
        if not applied:
            return False, "❌ Booking đã bị hủy trước đó"

        check_in = _to_date(booking.check_in_date)
        stay_dates = [check_in + timedelta(days=i) for i in range(booking.nights)]

        # Bước 2: dọn các bảng đọc
        batch = BatchStatement(batch_type=BatchType.LOGGED)
        batch.add(self.update_by_customer_status, (CANCELLED, booking.customer_id, booking_id))
        for d in stay_dates:
            batch.add(self.delete_stay, (booking.hotel_id, d, booking.room_id))
        self.session.execute(batch)

        # Bước 3: cuối cùng mới nhả khóa các đêm để phòng được bán lại
        self._release_nights(booking.room_id, stay_dates, booking_id)
        return True, "✅ Đã hủy booking"

    def _release_nights(self, room_id, stay_dates, booking_id):
        # Nhả từng đêm bằng câu lệnh có điều kiện (IF booking_id = ?)
        # nên không bao giờ xóa nhầm đêm của booking khác
        for d in stay_dates:
            self.session.execute(self.release_night, (room_id, d, booking_id))

    # ------------------------------------------------------------------
    # Đọc
    # ------------------------------------------------------------------
    def get_booking(self, booking_id):
        """Chi tiết 1 booking theo booking_id."""
        row = self.session.execute(self.select_booking, (booking_id,)).one()
        return _row_to_dict(row) if row else None

    def get_bookings_by_customer(self, customer_id):
        """Lịch sử booking của khách, mới nhất trước."""
        rows = self.session.execute(self.select_by_customer, (customer_id,))
        result = []
        for r in rows:
            d = _row_to_dict(r)
            # booking_id là timeuuid nên lấy lại được thời điểm đặt
            d["booking_date"] = datetime_from_uuid1(d["booking_id"])
            result.append(d)
        return result

    def get_bookings_by_room(self, room_id):
        """Các booking đang giữ phòng (CONFIRMED), theo thứ tự thời gian."""
        rows = self.session.execute(self.select_nights_by_room, (room_id,))
        bookings = {}
        for r in rows:
            if r.booking_id not in bookings:
                bookings[r.booking_id] = {
                    "room_id": r.room_id,
                    "booking_id": r.booking_id,
                    "customer_id": r.customer_id,
                    "check_in_date": _to_date(r.check_in_date),
                    "check_out_date": _to_date(r.check_out_date),
                    "status": CONFIRMED,
                }
        return list(bookings.values())

    def get_stays_on_date(self, hotel_id, stay_date):
        """Các phòng của khách sạn đang có khách vào đêm stay_date (1 partition)."""
        rows = self.session.execute(self.select_stays, (hotel_id, _to_date(stay_date)))
        return [_row_to_dict(r) for r in rows]

    def get_bookings_by_date(self, booking_date, hotel_id):
        """Các booking check-in vào ngày booking_date tại khách sạn (danh sách khách đến)."""
        booking_date = _to_date(booking_date)
        result = []
        for s in self.get_stays_on_date(hotel_id, booking_date):
            if s["check_in_date"] == booking_date:
                result.append({
                    "booking_date": booking_date,
                    "hotel_id": hotel_id,
                    "booking_id": s["booking_id"],
                    "customer_id": s["customer_id"],
                    "room_id": s["room_id"],
                    "check_in_date": s["check_in_date"],
                    "check_out_date": s["check_out_date"],
                    "status": CONFIRMED,
                })
        return result

    def find_available_rooms(self, hotel_id, check_in_date, check_out_date):
        """
        Tìm phòng còn trống trong [check_in, check_out).
        Chỉ để gợi ý, kết quả cuối cùng vẫn do create_booking quyết định
        (có thể có người đặt trước trong lúc bạn đang chọn).
        """
        check_in = _to_date(check_in_date)
        check_out = _to_date(check_out_date)
        nights = (check_out - check_in).days
        if nights < 1 or nights > MAX_NIGHTS:
            raise ValueError(f"Khoảng ngày phải từ 1 đến {MAX_NIGHTS} đêm")

        occupied = set()
        for i in range(nights):
            for s in self.get_stays_on_date(hotel_id, check_in + timedelta(days=i)):
                occupied.add(s["room_id"])

        rooms = self.session.execute(self.select_rooms_of_hotel, (hotel_id,))
        return [
            dict(r._asdict()) for r in rooms
            if r.room_id not in occupied and r.status != "MAINTENANCE"
        ]

    def close(self):
        self.cluster.shutdown()
