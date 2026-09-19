from collections import Counter
from datetime import date, timedelta

from repository import HotelRepository, RoomRepository, BookingRepository


class DashboardService:
    def __init__(self):
        self.hotel_repo = HotelRepository()
        self.room_repo = RoomRepository()
        self.booking_repo = BookingRepository()

    def close(self):
        self.hotel_repo.close()
        self.room_repo.close()
        self.booking_repo.close()

    # ---------- Danh sách khách sạn (dùng làm bộ lọc trên dashboard) ----------
    def list_hotels(self):
        return self.hotel_repo.get_all()

    # ---------- Trạng thái vật lý của phòng theo field tĩnh `status` ----------
    def room_status_summary(self, hotel_id):
        """Đếm phòng theo field `status` lưu trong rooms_by_hotel (tình trạng vật lý
        như AVAILABLE / MAINTENANCE, do lễ tân cập nhật thủ công)."""
        rooms = self.room_repo.get_by_hotel(hotel_id)
        counter = Counter(r["status"] for r in rooms)
        return dict(counter), len(rooms)

    # ---------- Phòng có khách hay không tại 1 ngày, suy ra từ booking ----------
    def room_occupancy_on_date(self, hotel_id, target_date):
        """Field `status` không tự đổi khi có booking mới, nên số phòng có khách
        được đếm từ room_nights_by_hotel_date (1 partition cho (hotel, ngày))."""
        total = len(self.room_repo.get_by_hotel(hotel_id))
        stays = self.booking_repo.get_stays_on_date(hotel_id, target_date)
        occupied = len({s["room_id"] for s in stays})
        return {"total_rooms": total, "occupied": occupied, "available": total - occupied}

    # ---------- Tỉ lệ lấp đầy phòng trong 1 khoảng thời gian ----------
    def occupancy_rate(self, hotel_id, from_date, to_date_exclusive):
        """occupancy% = tổng số đêm-phòng đã đặt / tổng số đêm-phòng có thể bán,
        trong khoảng [from_date, to_date_exclusive)."""
        total_rooms = len(self.room_repo.get_by_hotel(hotel_id))
        num_days = (to_date_exclusive - from_date).days
        if num_days <= 0 or total_rooms == 0:
            return 0.0

        booked_room_nights = 0
        d = from_date
        while d < to_date_exclusive:
            booked_room_nights += len(self.booking_repo.get_stays_on_date(hotel_id, d))
            d += timedelta(days=1)

        return round(booked_room_nights / (total_rooms * num_days) * 100, 1)

    # ---------- Doanh thu 1 ngày cụ thể (theo đêm lưu trú) ----------
    def revenue_by_day(self, hotel_id, target_date):
        stays = self.booking_repo.get_stays_on_date(hotel_id, target_date)
        return {
            "date": target_date,
            # số booking check-in vào ngày này (giữ nghĩa như bản cũ)
            "bookings": sum(1 for s in stays if s["check_in_date"] == target_date),
            "occupied_rooms": len(stays),
            "revenue": sum(float(s["price_per_night"]) for s in stays),
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
