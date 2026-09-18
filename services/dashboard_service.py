from collections import Counter
from datetime import date, timedelta

from cassandra_config import to_py_date
from repository import BookingRepository, HotelRepository, RoomRepository


class DashboardService:
    def __init__(self):
        self.hotel_repo = HotelRepository()
        self.room_repo = RoomRepository()
        self.booking_repo = BookingRepository()

    def close(self):
        pass

    # ---------- Danh sách khách sạn (dùng làm bộ lọc trên dashboard) ----------
    def list_hotels(self):
        return self.hotel_repo.get_all()

    # ---------- Thông tin chi tiết các phòng của khách sạn ----------
    def get_hotel_rooms(self, hotel_id):
        return self.room_repo.get_by_hotel(hotel_id)

    # ---------- Trạng thái phòng theo field tĩnh `status` ----------
    def room_status_summary(self, hotel_id):
        """Đếm phòng theo field `status` lưu trong rooms_by_hotel."""
        rooms = self.room_repo.get_by_hotel(hotel_id)
        counter = Counter(r["status"] for r in rooms)
        return dict(counter), len(rooms)

    # ---------- Trạng thái phòng THỰC TẾ tại 1 ngày, suy ra từ booking ----------
    def room_occupancy_on_date(self, hotel_id, target_date):
        t_date = to_py_date(target_date)
        rooms = self.room_repo.get_by_hotel(hotel_id)
        occupied_room_ids = set()
        occupied_details = []
        for room in rooms:
            bookings = self.booking_repo.get_bookings_by_room(room["room_id"])
            for b in bookings:
                if b.get("status") != "CONFIRMED":
                    continue
                c_in = to_py_date(b.get("check_in_date"))
                c_out = to_py_date(b.get("check_out_date"))
                if c_in and c_out and c_in <= t_date < c_out:
                    occupied_room_ids.add(room["room_id"])
                    occupied_details.append({
                        "room_number": room.get("room_number", ""),
                        "room_type": room.get("room_type", ""),
                        "booking_id": b.get("booking_id"),
                        "customer_id": b.get("customer_id"),
                        "check_in_date": str(c_in),
                        "check_out_date": str(c_out),
                    })
                    break
        total = len(rooms)
        occupied = len(occupied_room_ids)
        return {
            "total_rooms": total,
            "occupied": occupied,
            "available": total - occupied,
            "occupied_details": occupied_details,
        }

    # ---------- Tỉ lệ lấp đầy phòng trong 1 khoảng thời gian ----------
    def occupancy_rate(self, hotel_id, from_date, to_date_exclusive):
        f_date = to_py_date(from_date)
        t_date = to_py_date(to_date_exclusive)
        rooms = self.room_repo.get_by_hotel(hotel_id)
        num_days = (t_date - f_date).days
        if num_days <= 0 or not rooms:
            return 0.0

        booked_room_nights = 0
        for room in rooms:
            bookings = self.booking_repo.get_bookings_by_room(room["room_id"])
            for b in bookings:
                if b.get("status") != "CONFIRMED":
                    continue
                c_in = to_py_date(b.get("check_in_date"))
                c_out = to_py_date(b.get("check_out_date"))
                if not c_in or not c_out:
                    continue
                overlap_start = max(c_in, f_date)
                overlap_end = min(c_out, t_date)
                nights = (overlap_end - overlap_start).days
                if nights > 0:
                    booked_room_nights += nights

        total_room_nights = len(rooms) * num_days
        return round(booked_room_nights / total_room_nights * 100, 1)

    # ---------- Doanh thu 1 ngày cụ thể (theo ngày check-in) ----------
    def revenue_by_day(self, hotel_id, target_date):
        t_date = to_py_date(target_date)
        price_by_room = {r["room_id"]: r["price"] for r in self.room_repo.get_by_hotel(hotel_id)}
        bookings_today = self.booking_repo.get_bookings_by_date(t_date, hotel_id)

        total_revenue = 0.0
        confirmed_count = 0
        booking_list = []
        for b in bookings_today:
            if b.get("status") != "CONFIRMED":
                continue
            room_bookings = self.booking_repo.get_bookings_by_room(b["room_id"])
            match = next((rb for rb in room_bookings if rb["booking_id"] == b["booking_id"]), None)
            if not match:
                continue
            c_in = to_py_date(match["check_in_date"])
            c_out = to_py_date(match["check_out_date"])
            if not c_in or not c_out:
                continue
            nights = max(1, (c_out - c_in).days)
            price = float(price_by_room.get(b["room_id"], 0))
            rev = nights * price
            total_revenue += rev
            confirmed_count += 1
            booking_list.append({
                "booking_id": b["booking_id"],
                "room_id": b["room_id"],
                "customer_id": b["customer_id"],
                "nights": nights,
                "revenue": rev,
            })

        return {
            "date": t_date,
            "bookings": confirmed_count,
            "revenue": total_revenue,
            "details": booking_list,
        }

    # ---------- Doanh thu theo tháng (cộng dồn từng ngày trong tháng) ----------
    def revenue_by_month(self, hotel_id, year, month):
        first_day = date(year, month, 1)
        next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

        daily = []
        d = first_day
        while d < next_month:
            daily.append(self.revenue_by_day(hotel_id, d))
            d += timedelta(days=1)

        return {
            "year": year,
            "month": month,
            "total_revenue": sum(x["revenue"] for x in daily),
            "total_bookings": sum(x["bookings"] for x in daily),
            "daily": daily,
        }
