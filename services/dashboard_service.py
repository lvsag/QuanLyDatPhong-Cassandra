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

    def list_hotels(self):
        return self.hotel_repo.get_all()

    def get_hotel_rooms(self, hotel_id):
        return self.room_repo.get_by_hotel(hotel_id)

    def room_status_summary(self, hotel_id):
        rooms = self.room_repo.get_by_hotel(hotel_id)
        counter = Counter(r["status"] for r in rooms)
        return dict(counter), len(rooms)

    def room_occupancy_on_date(self, hotel_id, target_date):
        """
        Lấy tình trạng lấp đầy phòng THỰC TẾ tại 1 ngày từ read model `room_nights_by_hotel_date`.
        Không N+1 query.
        """
        t_date = to_py_date(target_date)
        rooms = self.room_repo.get_by_hotel(hotel_id)
        nights = self.booking_repo.get_room_nights_by_hotel_date(hotel_id, t_date)

        occupied_room_ids = set()
        occupied_details = []

        for n in nights:
            if n.get("status") in ["CONFIRMED", "CHECKED_IN"]:
                r_id = n.get("room_id")
                occupied_room_ids.add(r_id)
                occupied_details.append({
                    "room_number": n.get("room_number", ""),
                    "room_type": n.get("room_type", ""),
                    "booking_id": str(n.get("booking_id")),
                    "customer_id": str(n.get("customer_id")),
                    "customer_name": n.get("customer_name", ""),
                    "check_in_date": str(n.get("check_in_date")),
                    "check_out_date": str(n.get("check_out_date")),
                    "price_per_night": float(n.get("price_per_night", 0)),
                })

        total = len(rooms)
        occupied = len(occupied_room_ids)
        return {
            "total_rooms": total,
            "occupied": occupied,
            "available": max(0, total - occupied),
            "occupied_details": occupied_details,
        }

    def occupancy_rate(self, hotel_id, from_date, to_date_exclusive):
        """
        Tính tỉ lệ lấp đầy phòng trong 1 khoảng thời gian theo từng đêm lưu trú (stay night).
        """
        f_date = to_py_date(from_date)
        t_date = to_py_date(to_date_exclusive)
        rooms = self.room_repo.get_by_hotel(hotel_id)
        num_days = (t_date - f_date).days

        if num_days <= 0 or not rooms:
            return 0.0

        booked_room_nights = 0
        curr_d = f_date
        while curr_d < t_date:
            nights = self.booking_repo.get_room_nights_by_hotel_date(hotel_id, curr_d)
            booked_room_nights += sum(1 for n in nights if n.get("status") in ["CONFIRMED", "CHECKED_IN"])
            curr_d += timedelta(days=1)

        total_room_nights = len(rooms) * num_days
        return round(booked_room_nights / total_room_nights * 100, 1)

    def revenue_by_day(self, hotel_id, target_date):
        """
        Tính doanh thu một ngày theo từng đêm lưu trú (stay night) thực tế,
        dựa vào price_per_night snapshot.
        """
        t_date = to_py_date(target_date)
        nights = self.booking_repo.get_room_nights_by_hotel_date(hotel_id, t_date)

        total_revenue = 0.0
        confirmed_count = 0
        details = []

        for n in nights:
            if n.get("status") in ["CONFIRMED", "CHECKED_IN"]:
                price = float(n.get("price_per_night", 0))
                total_revenue += price
                confirmed_count += 1
                details.append({
                    "booking_id": str(n.get("booking_id")),
                    "room_id": str(n.get("room_id")),
                    "customer_id": str(n.get("customer_id")),
                    "customer_name": n.get("customer_name", ""),
                    "price_per_night": price,
                })

        return {
            "date": t_date,
            "bookings": confirmed_count,
            "revenue": total_revenue,
            "details": details,
        }

    def revenue_by_month(self, hotel_id, year, month):
        """
        Tính doanh thu theo tháng bằng cách phân bổ chính xác từng stay night.
        """
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
