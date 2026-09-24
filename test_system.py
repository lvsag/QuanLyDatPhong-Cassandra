import unittest
import uuid
from datetime import date
from decimal import Decimal

from cassandra_config import get_session
from repository import (
    BookingRepository,
    CustomerRepository,
    HotelRepository,
    RoomRepository,
)
from services.dashboard_service import DashboardService


class TestCassandraSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hotel_repo = HotelRepository()
        cls.customer_repo = CustomerRepository()
        cls.room_repo = RoomRepository()
        cls.booking_repo = BookingRepository()
        cls.dashboard_service = DashboardService()

        # Create test hotel
        cls.hotel_id = cls.hotel_repo.create("Test Hotel", "123 St", "Hồ Chí Minh", "0900000000", 4.5)
        # Create test customer
        cls.email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        cls.customer_id = cls.customer_repo.create("Test User", cls.email, "0901234567")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'hotel_id') and cls.hotel_id:
            cls.hotel_repo.delete(cls.hotel_id)
        if hasattr(cls, 'customer_id') and cls.customer_id:
            cls.customer_repo.delete(cls.customer_id)

    def test_01_booking_overlap_and_checkout_boundary(self):
        """Kiểm tra booking overlap và checkout boundary theo đúng section VII & XXXII."""
        room_id = self.room_repo.create(self.hotel_id, "101", "Deluxe", 100.0)

        # Baseline booking A: 05 -> 08
        c_in_a = date(2026, 5, 5)
        c_out_a = date(2026, 5, 8)
        ok_a, b_id_a, msg_a = self.booking_repo.create_booking(
            room_id, self.customer_id, self.hotel_id, c_in_a, c_out_a
        )
        self.assertTrue(ok_a, f"Baseline booking A 05->08 should succeed, got: {msg_a}")

        # Overlap B1: 06 -> 09 => FAIL
        ok_b1, _, _ = self.booking_repo.create_booking(
            room_id, self.customer_id, self.hotel_id, date(2026, 5, 6), date(2026, 5, 9)
        )
        self.assertFalse(ok_b1, "06->09 must FAIL due to overlap on 06, 07")

        # Checkout boundary B2: 08 -> 10 => SUCCESS
        ok_b2, b_id_b2, msg_b2 = self.booking_repo.create_booking(
            room_id, self.customer_id, self.hotel_id, date(2026, 5, 8), date(2026, 5, 10)
        )
        self.assertTrue(ok_b2, f"08->10 must SUCCESS, got: {msg_b2}")

        # Overlap B3: 04 -> 06 => FAIL
        ok_b3, _, _ = self.booking_repo.create_booking(
            room_id, self.customer_id, self.hotel_id, date(2026, 5, 4), date(2026, 5, 6)
        )
        self.assertFalse(ok_b3, "04->06 must FAIL due to overlap on 05")

        # Overlap B4: 04 -> 10 => FAIL
        ok_b4, _, _ = self.booking_repo.create_booking(
            room_id, self.customer_id, self.hotel_id, date(2026, 5, 4), date(2026, 5, 10)
        )
        self.assertFalse(ok_b4, "04->10 must FAIL due to overlap on 05, 06, 07")

        # Overlap B5: 06 -> 07 => FAIL
        ok_b5, _, _ = self.booking_repo.create_booking(
            room_id, self.customer_id, self.hotel_id, date(2026, 5, 6), date(2026, 5, 7)
        )
        self.assertFalse(ok_b5, "06->07 must FAIL due to overlap on 06")

        # Clean up
        self.booking_repo.cancel_booking(b_id_a)
        self.booking_repo.cancel_booking(b_id_b2)

    def test_02_cancel_state_transition(self):
        """Kiểm tra quy trình hủy đơn và idempotency (section XVIII & XXXII)."""
        room_id = self.room_repo.create(self.hotel_id, "102", "Deluxe", 100.0)

        ok, b_id, msg = self.booking_repo.create_booking(
            room_id, self.customer_id, self.hotel_id, date(2026, 6, 1), date(2026, 6, 3)
        )
        self.assertTrue(ok, f"Create booking failed: {msg}")

        # Hủy lần 1: CONFIRMED -> CANCELLED => SUCCESS
        c_ok1, c_msg1 = self.booking_repo.cancel_booking(b_id)
        self.assertTrue(c_ok1, f"Cancel 1st time should succeed, got: {c_msg1}")

        # Hủy lần 2: CANCELLED -> CANCELLED => FAIL
        c_ok2, c_msg2 = self.booking_repo.cancel_booking(b_id)
        self.assertFalse(c_ok2, f"Cancel 2nd time should fail, got: {c_msg2}")

    def test_03_email_uniqueness(self):
        """Kiểm tra email uniqueness sử dụng LWT (section XI & XXXII)."""
        unique_email = f"unique_{uuid.uuid4().hex[:8]}@example.com"
        # Lần 1: new email => SUCCESS
        c_id = self.customer_repo.create("User 1", unique_email, "0900000001")
        self.assertIsNotNone(c_id)

        # Lần 2: existing email => FAIL (raises ValueError)
        with self.assertRaises(ValueError):
            self.customer_repo.create("User 2", unique_email, "0900000002")

    def test_04_price_snapshot(self):
        """Kiểm tra snapshot giá phòng không bị ảnh hưởng khi giá phòng thay đổi (section XIX & XXXII)."""
        room_id = self.room_repo.create(self.hotel_id, "103", "Standard", 100.0)

        ok, b_id, _ = self.booking_repo.create_booking(
            room_id, self.customer_id, self.hotel_id, date(2026, 7, 10), date(2026, 7, 12)
        )
        self.assertTrue(ok)

        # Thay đổi giá phòng hiện tại lên 200
        self.room_repo.update_info(self.hotel_id, room_id, "103", "Standard", 200.0)

        # Đơn đặt phòng cũ phải giữ nguyên price_per_night = 100
        booking = self.booking_repo.get_booking_by_id(b_id)
        self.assertEqual(float(booking["price_per_night"]), 100.0)

        # Clean up
        self.booking_repo.cancel_booking(b_id)

    def test_05_dashboard_revenue_distribution(self):
        """Kiểm tra phân bổ doanh thu theo từng stay night (section XX, XXI & XXXII)."""
        room_id = self.room_repo.create(self.hotel_id, "104", "Suite", 100.0)

        ok, b_id, _ = self.booking_repo.create_booking(
            room_id, self.customer_id, self.hotel_id, date(2026, 1, 30), date(2026, 2, 3), price_per_night=100.0
        )
        self.assertTrue(ok)

        # Kiểm tra doanh thu đêm 01/30, 01/31, 02/01, 02/02
        rev_30 = self.dashboard_service.revenue_by_day(self.hotel_id, date(2026, 1, 30))
        rev_31 = self.dashboard_service.revenue_by_day(self.hotel_id, date(2026, 1, 31))
        rev_01 = self.dashboard_service.revenue_by_day(self.hotel_id, date(2026, 2, 1))
        rev_02 = self.dashboard_service.revenue_by_day(self.hotel_id, date(2026, 2, 2))
        rev_03 = self.dashboard_service.revenue_by_day(self.hotel_id, date(2026, 2, 3))  # Checkout day

        self.assertEqual(rev_30["revenue"], 100.0)
        self.assertEqual(rev_31["revenue"], 100.0)
        self.assertEqual(rev_01["revenue"], 100.0)
        self.assertEqual(rev_02["revenue"], 100.0)
        self.assertEqual(rev_03["revenue"], 0.0)  # Checkout date has 0 revenue for this booking

        # Clean up
        self.booking_repo.cancel_booking(b_id)


if __name__ == "__main__":
    unittest.main()
