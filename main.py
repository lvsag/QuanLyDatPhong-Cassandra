import uuid
from datetime import date
from cassandra_config import get_session
from repository import (
    HotelRepository,
    CustomerRepository,
    RoomRepository,
    BookingRepository,
)


def main():
    print("\n===== TEST CASSANDRA INFRASTRUCTURE & REPOSITORIES =====\n")

    hotel_repo = HotelRepository()
    customer_repo = CustomerRepository()
    room_repo = RoomRepository()
    booking_repo = BookingRepository()

    # 1. Lấy khách sạn test
    TEST_HOTEL_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
    hotel = hotel_repo.get_by_id(TEST_HOTEL_ID)
    print(f"[OK] Khách sạn: {hotel.get('name') if hotel else 'Not found'}")

    # 2. Khách hàng test
    customer = customer_repo.get_by_email("an.nguyen@gmail.com")
    customer_id = customer["customer_id"] if customer else customer_repo.create("Nguyễn Văn Test", "test.user@gmail.com", "0909090909")
    print(f"[OK] Khách hàng: {customer_id}")

    # 3. Phòng test
    rooms = room_repo.get_by_hotel(TEST_HOTEL_ID)
    room_id = rooms[0]["room_id"]
    print(f"[OK] Phòng: {rooms[0]['room_number']} (ID: {room_id})")

    # 4. Đặt phòng test
    check_in = date(2026, 12, 1)
    check_out = date(2026, 12, 5)

    success, booking_id, msg = booking_repo.create_booking(
        room_id=room_id,
        customer_id=customer_id,
        hotel_id=TEST_HOTEL_ID,
        check_in_date=check_in,
        check_out_date=check_out
    )
    print(f"Đặt phòng test (2026-12-01 -> 2026-12-05): {msg}")

    # 5. Test LWT chống trùng lịch (04 -> 06, trùng ngày 05)
    success2, _, msg2 = booking_repo.create_booking(
        room_id=room_id,
        customer_id=customer_id,
        hotel_id=TEST_HOTEL_ID,
        check_in_date=date(2026, 12, 4),
        check_out_date=date(2026, 12, 6)
    )
    print(f"Test Overlap LWT (trùng 05/12): {msg2} (Expected: Fail)")

    # 6. Test Checkout Boundary (05 -> 08, đặt từ 05/12)
    success3, b_id3, msg3 = booking_repo.create_booking(
        room_id=room_id,
        customer_id=customer_id,
        hotel_id=TEST_HOTEL_ID,
        check_in_date=date(2026, 12, 5),
        check_out_date=date(2026, 12, 8)
    )
    print(f"Test Checkout Boundary (đặt từ 05/12 khi booking trước checkout 05/12): {msg3} (Expected: Success)")

    # 7. Dọn dẹp booking test
    if success and booking_id:
        booking_repo.cancel_booking(booking_id)
        print("  - Đã dọn dẹp booking 1.")
    if success3 and b_id3:
        booking_repo.cancel_booking(b_id3)
        print("  - Đã dọn dẹp booking 3.")

    hotel_repo.close()
    customer_repo.close()
    room_repo.close()
    booking_repo.close()

    print("\n===== TEST MAIN.PY HOÀN TẤT THÀNH CÔNG =====")


if __name__ == "__main__":
    main()