-- Schema keyspace hotel_booking
-- Thiết kế theo hướng query-first, xem docs/THIET_KE_CASSANDRA.md
-- Không đặt dấu chấm phẩy trong comment vì script tách lệnh theo dấu chấm phẩy

-- ============================================================
-- NHÓM DANH MỤC
-- ============================================================

-- Xem chi tiết khách sạn theo hotel_id
CREATE TABLE IF NOT EXISTS hotels (
    hotel_id   uuid,
    name       text,
    address    text,
    city       text,
    phone      text,
    rating     decimal,
    created_at timestamp,
    PRIMARY KEY (hotel_id)
);

-- Danh sách phòng của một khách sạn
-- Partition key: hotel_id, Clustering key: room_id
-- Cột status chỉ mô tả tình trạng vật lý của phòng (AVAILABLE hoặc MAINTENANCE)
-- Phòng có khách hay không được suy ra từ các bảng room_nights_*
CREATE TABLE IF NOT EXISTS rooms_by_hotel (
    hotel_id    uuid,
    room_id     uuid,
    room_number text,
    room_type   text,
    price       decimal,
    status      text,
    PRIMARY KEY ((hotel_id), room_id)
);

-- Xem chi tiết khách theo customer_id
CREATE TABLE IF NOT EXISTS customers (
    customer_id uuid,
    full_name   text,
    email       text,
    phone       text,
    id_number   text,
    created_at  timestamp,
    PRIMARY KEY (customer_id)
);

-- Đăng nhập, tìm khách theo email
-- Đồng thời là ràng buộc UNIQUE cho email (ghi bằng INSERT IF NOT EXISTS)
CREATE TABLE IF NOT EXISTS customers_by_email (
    email       text,
    customer_id uuid,
    full_name   text,
    phone       text,
    PRIMARY KEY (email)
);

-- ============================================================
-- NHÓM ĐẶT PHÒNG
-- ============================================================

-- Nguồn sự thật của một booking, tra theo booking_id
-- booking_id là timeuuid: vừa duy nhất vừa chứa thời điểm tạo
-- price_per_night là giá chốt tại thời điểm đặt, đổi giá phòng sau này không ảnh hưởng booking cũ
CREATE TABLE IF NOT EXISTS bookings_by_id (
    booking_id      timeuuid,
    customer_id     uuid,
    hotel_id        uuid,
    room_id         uuid,
    room_number     text,
    check_in_date   date,
    check_out_date  date,
    nights          int,
    price_per_night decimal,
    total_amount    decimal,
    status          text,
    created_at      timestamp,
    cancelled_at    timestamp,
    PRIMARY KEY (booking_id)
);

-- Lịch sử booking của khách, mới nhất trước
-- Partition key: customer_id, Clustering key: booking_id (timeuuid, DESC)
CREATE TABLE IF NOT EXISTS bookings_by_customer (
    customer_id    uuid,
    booking_id     timeuuid,
    hotel_id       uuid,
    room_id        uuid,
    room_number    text,
    check_in_date  date,
    check_out_date date,
    total_amount   decimal,
    status         text,
    PRIMARY KEY ((customer_id), booking_id)
) WITH CLUSTERING ORDER BY (booking_id DESC);

-- Lịch từng đêm của một phòng, đây là bảng CHỐNG TRÙNG LỊCH
-- Mỗi đêm ở là một dòng: (room_id, stay_date) là duy nhất
-- Đặt phòng = một conditional batch INSERT IF NOT EXISTS cho tất cả các đêm (cùng partition)
-- Một đêm được tính từ check_in_date đến trước check_out_date
CREATE TABLE IF NOT EXISTS room_nights_by_room (
    room_id        uuid,
    stay_date      date,
    booking_id     timeuuid,
    customer_id    uuid,
    check_in_date  date,
    check_out_date date,
    PRIMARY KEY ((room_id), stay_date)
);

-- Phòng nào của khách sạn nào đang có khách vào đêm nào
-- Phục vụ tìm phòng trống, dashboard (lấp đầy, doanh thu), danh sách khách đến trong ngày
-- Partition key: (hotel_id, stay_date) nên mỗi partition tối đa bằng số phòng của khách sạn
CREATE TABLE IF NOT EXISTS room_nights_by_hotel_date (
    hotel_id        uuid,
    stay_date       date,
    room_id         uuid,
    booking_id      timeuuid,
    customer_id     uuid,
    check_in_date   date,
    check_out_date  date,
    price_per_night decimal,
    PRIMARY KEY ((hotel_id, stay_date), room_id)
);
