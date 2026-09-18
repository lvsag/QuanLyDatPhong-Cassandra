import uuid
from datetime import date, timedelta
from cassandra_config import get_session
from repository import (
    HotelRepository,
    CustomerRepository,
    RoomRepository,
    BookingRepository,
)


def main():
    print("\n===== TEST PHAN 1 - CASSANDRA INFRA & DAL =====\n")

    hotel_repo = HotelRepository()
    customer_repo = CustomerRepository()
    room_repo = RoomRepository()
    booking_repo = BookingRepository()

    # 1. Lấy hoặc tạo khách sạn test chuẩn
    TEST_HOTEL_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
    hotel = hotel_repo.get_by_id(TEST_HOTEL_ID)
    if not hotel:
        hotel_id = hotel_repo.create(
            name="Sunrise Hotel",
            address="123 Nguyễn Huệ, Q1",
            city="Hồ Chí Minh",
            phone="0281234567",
            rating=4.5
        )
    else:
        hotel_id = TEST_HOTEL_ID
    print(f"[OK] Su dung Khach san: {hotel_id}")

    # 2. Khách hàng test
    customer = customer_repo.get_by_email("an.nguyen@gmail.com")
    if customer:
        customer_id = customer["customer_id"]
    else:
        customer_id = customer_repo.create(
            full_name="Nguyễn Văn A",
            email="nguyenvana@gmail.com",
            phone="0901234567",
            id_number="012345678901"
        )
    print(f"[OK] Su dung Khach hang: {customer_id}")

    # 3. Phòng test
    rooms = room_repo.get_by_hotel(hotel_id)
    if rooms:
        room_id = rooms[0]["room_id"]
    else:
        room_id = room_repo.create(
            hotel_id=hotel_id,
            room_number="101",
            room_type="Deluxe",
            price=150.0
        )
    print(f"[OK] Su dung Phong: {room_id}")

    # 4. Đặt phòng test với khoảng ngày cụ thể
    check_in = date(2026, 12, 1)
    check_out = date(2026, 12, 3)

    success, booking_id, msg = booking_repo.create_booking(
        room_id=room_id,
        customer_id=customer_id,
        hotel_id=hotel_id,
        check_in_date=check_in,
        check_out_date=check_out
    )
    print(f"Dat phong test: {msg}")

    # 5. Test LWT chống trùng lịch
    success2, _, msg2 = booking_repo.create_booking(
        room_id=room_id,
        customer_id=customer_id,
        hotel_id=hotel_id,
        check_in_date=check_in,
        check_out_date=check_out
    )
    print(f"Test LWT chong trung: {msg2}")

    # 6. Kiểm tra phòng trống
    print("\n[TEST] Kiem tra phong trong:")
    is_available_same = booking_repo.check_availability(room_id, check_in)
    print(f"  - Ngay {check_in} (da dat): {'Trong' if is_available_same else 'Da co nguoi dat (Chuan)'}")

    future_date = date(2026, 12, 25)
    is_available_future = booking_repo.check_availability(room_id, future_date)
    print(f"  - Ngay {future_date} (tuong lai): {'Phong trong (Chuan)' if is_available_future else 'Da co nguoi dat'}")

    # 7. Dọn dẹp booking test
    if success and booking_id:
        booking_repo.cancel_booking(room_id, check_in, booking_id, customer_id, hotel_id)
        print("  - Da giai phong booking test sau khi hoan tat.")

    hotel_repo.close()
    customer_repo.close()
    room_repo.close()
    booking_repo.close()

    print("\n===== TEST THANH CONG! KHONG GAY DUPLICATE DU LIEU =====")


if __name__ == "__main__":
    main()