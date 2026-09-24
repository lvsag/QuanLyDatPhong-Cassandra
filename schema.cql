-- ============================================================
-- SCHEMA DDL CASSANDRA CHUẨN DỰA TRÊN QUERY-FIRST MODELING
-- System: QuanLyDatPhong-Cassandra
-- Keyspace: hotel_booking
-- ============================================================

CREATE KEYSPACE IF NOT EXISTS hotel_booking
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE hotel_booking;

-- Bảng 1: hotels (Thông tin cơ bản về khách sạn)
CREATE TABLE IF NOT EXISTS hotels (
    hotel_id uuid,
    name text,
    address text,
    city text,
    phone text,
    rating decimal,
    created_at timestamp,
    PRIMARY KEY (hotel_id)
);

-- Bảng 2: hotels_by_city (Tra cứu khách sạn theo thành phố - Không dùng ALLOW FILTERING)
CREATE TABLE IF NOT EXISTS hotels_by_city (
    city text,
    hotel_id uuid,
    name text,
    address text,
    phone text,
    rating decimal,
    PRIMARY KEY (city, hotel_id)
);

-- Bảng 3: rooms_by_hotel (Danh sách phòng của từng khách sạn)
CREATE TABLE IF NOT EXISTS rooms_by_hotel (
    hotel_id uuid,
    room_id uuid,
    room_number text,
    room_type text,
    price decimal,
    status text,
    PRIMARY KEY (hotel_id, room_id)
);

-- Bảng 4: customers (Thông tin chi tiết khách hàng)
CREATE TABLE IF NOT EXISTS customers (
    customer_id uuid,
    full_name text,
    email text,
    phone text,
    id_number text,
    created_at timestamp,
    password_hash text,
    PRIMARY KEY (customer_id)
);

-- Bảng 5: customers_by_email (Xác thực login & bảo đảm email unique với LWT)
CREATE TABLE IF NOT EXISTS customers_by_email (
    email text,
    customer_id uuid,
    full_name text,
    phone text,
    password_hash text,
    PRIMARY KEY (email)
);

-- Bảng 6: bookings_by_id (Read model chính để tra cứu chi tiết booking theo booking_id)
CREATE TABLE IF NOT EXISTS bookings_by_id (
    booking_id timeuuid,
    customer_id uuid,
    hotel_id uuid,
    room_id uuid,
    check_in_date date,
    check_out_date date,
    booking_date timestamp,
    price_per_night decimal,
    total_amount decimal,
    status text,
    PRIMARY KEY (booking_id)
);

-- Bảng 7: bookings_by_customer (Lịch sử booking của khách hàng, xếp theo thứ tự mới nhất)
CREATE TABLE IF NOT EXISTS bookings_by_customer (
    customer_id uuid,
    booking_id timeuuid,
    hotel_id uuid,
    room_id uuid,
    check_in_date date,
    check_out_date date,
    booking_date timestamp,
    price_per_night decimal,
    total_amount decimal,
    status text,
    PRIMARY KEY (customer_id, booking_id)
) WITH CLUSTERING ORDER BY (booking_id DESC);

-- Bảng 8: room_nights_by_room (Đêm lưu trú của phòng - LWT conditional batch chống trùng lịch)
CREATE TABLE IF NOT EXISTS room_nights_by_room (
    room_id uuid,
    stay_date date,
    booking_id timeuuid,
    customer_id uuid,
    hotel_id uuid,
    check_in_date date,
    check_out_date date,
    price_per_night decimal,
    status text,
    PRIMARY KEY (room_id, stay_date)
);

-- Bảng 9: room_nights_by_hotel_date (Phục vụ Q10 Check-in, Occupancy, Revenue & Dashboard)
CREATE TABLE IF NOT EXISTS room_nights_by_hotel_date (
    hotel_id uuid,
    stay_date date,
    room_id uuid,
    booking_id timeuuid,
    customer_id uuid,
    check_in_date date,
    check_out_date date,
    price_per_night decimal,
    status text,
    customer_name text,
    room_number text,
    room_type text,
    PRIMARY KEY ((hotel_id, stay_date), room_id)
);
