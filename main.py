from datetime import date, timedelta
from cassandra_config import get_session
from repository import (
    HotelRepository,
    CustomerRepository,
    RoomRepository,
    BookingRepository,
)


def print_db_samples():
    cluster, session = get_session()
    tables = [
        'hotels', 'customers', 'customers_by_email',
        'rooms_by_hotel', 'bookings_by_room', 'bookings_by_customer', 'bookings_by_date'
    ]
    print('\n=== DATABASE SAMPLES ===')
    for t in tables:
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

    # 2. Tạo khách hàng
    customer_repo = CustomerRepository()
    customer_id = customer_repo.create(
        full_name="Nguyễn Văn A",
        email="nguyenvana@gmail.com",
        phone="0901234567",
        id_number="012345678901"
    )
    print(f"👤 Tạo KH: {customer_id}")

    # 3. Tạo phòng
    room_repo = RoomRepository()
    room_id = room_repo.create(
        hotel_id=hotel_id,
        room_number="101",
        room_type="Deluxe",
        price=150.0
    )
    print(f"🚪 Tạo phòng: {room_id}")

    # 4. Đặt phòng
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

    # 5. Test LWT: đặt trùng ngày → phải fail
    success2, _, msg2 = booking_repo.create_booking(
        room_id=room_id,
        customer_id=customer_id,
        hotel_id=hotel_id,
        check_in_date=check_in,  # trùng ngày
        check_out_date=check_out
    )
    print(f"Test trùng lịch: {msg2}")

    # 6. Query kiểm tra
    print("\n📋 Phòng của KS:")
    for r in room_repo.get_by_hotel(hotel_id):
        print(f"   - {r['room_number']} ({r['room_type']}) - {r['status']}")

    print("\n📋 Booking của khách:")
    for b in booking_repo.get_bookings_by_customer(customer_id):
        print(f"   - {b['booking_id']} | {b['status']}")

    print("\n📋 Booking theo ngày (dashboard):")
    for b in booking_repo.get_bookings_by_date(check_in, hotel_id):
        print(f"   - {b['booking_id']} | room={b['room_id']}")

    # 7. Test login lookup
    print("\n🔐 Lookup khách theo email (dùng cho login):")
    c = customer_repo.get_by_email("nguyenvana@gmail.com")
    if c:
        print(f"   Tìm thấy: {c['full_name']} - {c['customer_id']}")

    # Đóng kết nối
    hotel_repo.close()
    customer_repo.close()
    room_repo.close()
    booking_repo.close()


if __name__ == "__main__":
    main()