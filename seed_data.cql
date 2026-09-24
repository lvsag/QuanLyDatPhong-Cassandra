
CREATE KEYSPACE IF NOT EXISTS hotel_booking
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE hotel_booking;

-- Bảng 1: hotels
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

-- Bảng 2: hotels_by_city
CREATE TABLE IF NOT EXISTS hotels_by_city (
    city text,
    hotel_id uuid,
    name text,
    address text,
    phone text,
    rating decimal,
    PRIMARY KEY (city, hotel_id)
);

-- Bảng 3: rooms_by_hotel
CREATE TABLE IF NOT EXISTS rooms_by_hotel (
    hotel_id uuid,
    room_id uuid,
    room_number text,
    room_type text,
    price decimal,
    status text,
    PRIMARY KEY (hotel_id, room_id)
);

-- Bảng 4: customers
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

-- Bảng 5: customers_by_email
CREATE TABLE IF NOT EXISTS customers_by_email (
    email text,
    customer_id uuid,
    full_name text,
    phone text,
    password_hash text,
    PRIMARY KEY (email)
);

-- Bảng 6: bookings_by_id
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

-- Bảng 7: bookings_by_customer
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

-- Bảng 8: room_nights_by_room
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

-- Bảng 9: room_nights_by_hotel_date
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

-- ------------------------------------------------------------
-- INSERT KHÁCH SẠN (hotels & hotels_by_city)
-- ------------------------------------------------------------
INSERT INTO hotels (hotel_id, name, address, city, phone, rating, created_at) VALUES 
(00000000-0000-0000-0000-000000000001, 'Sunrise Hotel', '123 Nguyễn Huệ, Q1', 'Hồ Chí Minh', '0281234561', 4.5, toTimestamp(now()));
INSERT INTO hotels_by_city (city, hotel_id, name, address, phone, rating) VALUES 
('Hồ Chí Minh', 00000000-0000-0000-0000-000000000001, 'Sunrise Hotel', '123 Nguyễn Huệ, Q1', '0281234561', 4.5);

INSERT INTO hotels (hotel_id, name, address, city, phone, rating, created_at) VALUES 
(00000000-0000-0000-0000-000000000002, 'Blue Ocean Resort', '456 Trần Phú', 'Đà Nẵng', '0236123452', 4.8, toTimestamp(now()));
INSERT INTO hotels_by_city (city, hotel_id, name, address, phone, rating) VALUES 
('Đà Nẵng', 00000000-0000-0000-0000-000000000002, 'Blue Ocean Resort', '456 Trần Phú', '0236123452', 4.8);

INSERT INTO hotels (hotel_id, name, address, city, phone, rating, created_at) VALUES 
(00000000-0000-0000-0000-000000000003, 'Hanoi Pearl', '789 Hàng Bài, HK', 'Hà Nội', '0241234563', 4.2, toTimestamp(now()));
INSERT INTO hotels_by_city (city, hotel_id, name, address, phone, rating) VALUES 
('Hà Nội', 00000000-0000-0000-0000-000000000003, 'Hanoi Pearl', '789 Hàng Bài, HK', '0241234563', 4.2);

INSERT INTO hotels (hotel_id, name, address, city, phone, rating, created_at) VALUES 
(00000000-0000-0000-0000-000000000004, 'Nha Trang Bay', '101 Trần Phú', 'Nha Trang', '0258123454', 4.6, toTimestamp(now()));
INSERT INTO hotels_by_city (city, hotel_id, name, address, phone, rating) VALUES 
('Nha Trang', 00000000-0000-0000-0000-000000000004, 'Nha Trang Bay', '101 Trần Phú', '0258123454', 4.6);

INSERT INTO hotels (hotel_id, name, address, city, phone, rating, created_at) VALUES 
(00000000-0000-0000-0000-000000000005, 'Phu Quoc Sunset', '202 Bãi Trường', 'Phú Quốc', '0297123455', 4.9, toTimestamp(now()));
INSERT INTO hotels_by_city (city, hotel_id, name, address, phone, rating) VALUES 
('Phú Quốc', 00000000-0000-0000-0000-000000000005, 'Phu Quoc Sunset', '202 Bãi Trường', '0297123455', 4.9);

-- ------------------------------------------------------------
-- INSERT KHÁCH HÀNG (customers & customers_by_email)
-- ------------------------------------------------------------
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000001, 'Nguyễn Văn An', 'an.nguyen@gmail.com', '0901111111', '001234567801', toTimestamp(now()));
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('an.nguyen@gmail.com', 10000000-0000-0000-0000-000000000001, 'Nguyễn Văn An', '0901111111');

INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000002, 'Trần Thị Bình', 'binh.tran@gmail.com', '0902222222', '001234567802', toTimestamp(now()));
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('binh.tran@gmail.com', 10000000-0000-0000-0000-000000000002, 'Trần Thị Bình', '0902222222');

INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000003, 'Lê Minh Cường', 'cuong.le@gmail.com', '0903333333', '001234567803', toTimestamp(now()));
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('cuong.le@gmail.com', 10000000-0000-0000-0000-000000000003, 'Lê Minh Cường', '0903333333');

INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000004, 'Phạm Thu Dung', 'dung.pham@gmail.com', '0904444444', '001234567804', toTimestamp(now()));
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('dung.pham@gmail.com', 10000000-0000-0000-0000-000000000004, 'Phạm Thu Dung', '0904444444');

INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000005, 'Hoàng Văn Em', 'em.hoang@gmail.com', '0905555555', '001234567805', toTimestamp(now()));
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('em.hoang@gmail.com', 10000000-0000-0000-0000-000000000005, 'Hoàng Văn Em', '0905555555');

-- ------------------------------------------------------------
-- INSERT PHÒNG (rooms_by_hotel)
-- ------------------------------------------------------------
-- KS HT1 (Sunrise Hotel - HCM)
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000001, 20000000-0000-0000-0000-000000000001, '101', 'Standard', 100, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000001, 20000000-0000-0000-0000-000000000002, '102', 'Standard', 100, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000001, 20000000-0000-0000-0000-000000000003, '201', 'Deluxe', 150, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000001, 20000000-0000-0000-0000-000000000004, '202', 'Deluxe', 150, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000001, 20000000-0000-0000-0000-000000000005, '301', 'Suite', 250, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000001, 20000000-0000-0000-0000-000000000006, '302', 'Suite', 250, 'AVAILABLE');

-- KS HT2 (Blue Ocean - Đà Nẵng)
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000002, 20000000-0000-0000-0000-000000000007, '101', 'Standard', 120, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000002, 20000000-0000-0000-0000-000000000008, '102', 'Standard', 120, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000002, 20000000-0000-0000-0000-000000000009, '201', 'Deluxe', 180, 'AVAILABLE');

-- KS HT3 (Hanoi Pearl)
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000003, 20000000-0000-0000-0000-000000000013, '101', 'Standard', 90, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000003, 20000000-0000-0000-0000-000000000014, '102', 'Standard', 90, 'AVAILABLE');

-- KS HT4 (Nha Trang Bay)
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000004, 20000000-0000-0000-0000-000000000019, '101', 'Standard', 110, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000004, 20000000-0000-0000-0000-000000000020, '102', 'Standard', 110, 'AVAILABLE');

-- KS HT5 (Phu Quoc Sunset)
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000005, 20000000-0000-0000-0000-000000000025, '101', 'Standard', 130, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000005, 20000000-0000-0000-0000-000000000026, '102', 'Standard', 130, 'AVAILABLE');
