from datetime import date, timedelta
from cassandra_config import get_session
from repository import (
    HotelRepository,
    CustomerRepository,
    RoomRepository,
    BookingRepository,
)

TABLES = [
    'hotels', 'customers', 'customers_by_email', 'rooms_by_hotel',
    'bookings_by_id', 'bookings_by_customer',
    'room_nights_by_room', 'room_nights_by_hotel_date',
]


def print_db_samples():
    cluster, session = get_session()
    print('\n=== DATABASE SAMPLES ===')
    for t in TABLES:
        try:
            cnt = session.execute(f"SELECT count(*) FROM {t}").one()[0]
            print(f"{t}: {cnt}")
            rows = session.execute(f"SELECT * FROM {t} LIMIT 3")
            for r in rows:
                print('  ', dict(r._asdict()))
        except Exception as e:
            print(f"{t}: error -> {e}")
    cluster.shutdown()


def main():
    print("\n===== TEST PHẦN 1 - CASSANDRA INFRA =====\n")

    # 1. Tạo khách sạn
    hotel_repo = HotelRepository()
    hotel_id = hotel_repo.create(
        name="Sunrise Hotel",
        address="123 Nguyễn Huệ, Q1",
        city="Hồ Chí Minh",
        phone="0281234567",
        rating=4.5
    )
    print(f"🏨 Tạo KS: {hotel_id}")

    # 2. Tạo khách hàng (email là duy nhất nên chạy lại thì dùng khách đã có)
    customer_repo = CustomerRepository()
    email = "nguyenvana@gmail.com"
    existing = customer_repo.get_by_email(email)
    if existing:
        customer_id = existing['customer_id']
        print(f"👤 Dùng lại KH: {customer_id}")
    else:
        customer_id = customer_repo.create(
            full_name="Nguyễn Văn A",
            email=email,
            phone="0901234567",
            id_number="012345678901"
        )
        print(f"👤 Tạo KH: {customer_id}")

    # Đăng ký trùng email phải bị từ chối
    try:
        customer_repo.create("Người khác", email.upper(), "0900000000")
        print("Test trùng email: ❌ lẽ ra phải bị từ chối")
    except ValueError as e:
        print(f"Test trùng email: ✅ {e}")

    # 3. Tạo phòng
    room_repo = RoomRepository()
    room_id = room_repo.create(
        hotel_id=hotel_id,
        room_number="101",
        room_type="Deluxe",
        price=150.0
    )
    print(f"🚪 Tạo phòng: {room_id}")

    # 4. Đặt phòng: ở 2 đêm [D+1, D+3)
    booking_repo = BookingRepository()
    check_in = date.today() + timedelta(days=1)
    check_out = date.today() + timedelta(days=3)

    success, booking_id, msg = booking_repo.create_booking(
        room_id=room_id,
        customer_id=customer_id,
        hotel_id=hotel_id,
        check_in_date=check_in,
        check_out_date=check_out
    )
    print(msg)

    # 5. Test LWT: đặt trùng hẳn khoảng ngày → phải fail
    _, _, msg2 = booking_repo.create_booking(
        room_id=room_id, customer_id=customer_id, hotel_id=hotel_id,
        check_in_date=check_in, check_out_date=check_out
    )
    print(f"Test trùng y hệt:      {msg2}")

    # 5b. Test GÁC NGÀY (check-in khác nhưng chồng lên): phải fail
    _, _, msg3 = booking_repo.create_booking(
        room_id=room_id, customer_id=customer_id, hotel_id=hotel_id,
        check_in_date=check_in + timedelta(days=1),
        check_out_date=check_out + timedelta(days=2)
    )
    print(f"Test gác ngày:         {msg3}")

    # 5c. Khách cũ trả phòng đúng ngày khách mới nhận phòng: hợp lệ
    _, _, msg4 = booking_repo.create_booking(
        room_id=room_id, customer_id=customer_id, hotel_id=hotel_id,
        check_in_date=check_out, check_out_date=check_out + timedelta(days=1)
    )
    print(f"Test nối tiếp ngày:    {msg4}")

    # 6. Tìm phòng trống
    print("\n🔎 Phòng trống của KS trong khoảng ngày trùng booking:")
    free = booking_repo.find_available_rooms(hotel_id, check_in, check_out)
    print(f"   Phòng 101 còn trống? {any(r['room_id'] == room_id for r in free)} (đã có khách nên phải là False)")

    # 7. Query kiểm tra
    print("\n📋 Phòng của KS:")
    for r in room_repo.get_by_hotel(hotel_id):
        print(f"   - {r['room_number']} ({r['room_type']}) - {r['status']}")

    print("\n📋 Booking của khách (mới nhất trước):")
    for b in booking_repo.get_bookings_by_customer(customer_id)[:5]:
        print(f"   - {b['booking_id']} | {b['check_in_date']} → {b['check_out_date']} | {b['status']}")

    print("\n📋 Khách check-in theo ngày (dashboard):")
    for b in booking_repo.get_bookings_by_date(check_in, hotel_id):
        print(f"   - {b['booking_id']} | room={b['room_id']}")

    # 8. Hủy booking rồi đặt lại đúng khoảng ngày đó
    _, msg_cancel = booking_repo.cancel_booking(booking_id=booking_id)
    print(f"\nHủy booking: {msg_cancel}")
    _, msg_again = booking_repo.cancel_booking(booking_id=booking_id)
    print(f"Hủy lần 2:   {msg_again}")
    _, _, msg5 = booking_repo.create_booking(
        room_id=room_id, customer_id=customer_id, hotel_id=hotel_id,
        check_in_date=check_in, check_out_date=check_out
    )
    print(f"Đặt lại sau khi hủy: {msg5}")

    # 9. Test lookup login
    print("\n🔐 Lookup khách theo email (dùng cho login):")
    c = customer_repo.get_by_email(email)
    if c:
        print(f"   Tìm thấy: {c['full_name']} - {c['customer_id']}")

    # Đóng kết nối
    hotel_repo.close()
    customer_repo.close()
    room_repo.close()
    booking_repo.close()


if __name__ == "__main__":
    main()
