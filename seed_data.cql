CREATE KEYSPACE IF NOT EXISTS hotel_booking
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE hotel_booking;

-- Bảng 1: Phòng theo khách sạn
CREATE TABLE IF NOT EXISTS rooms_by_hotel (
    hotel_id UUID,
    room_id UUID,
    room_number text,
    room_type text,
    price decimal,
    status text,
    PRIMARY KEY (hotel_id, room_id)
);

-- Bảng 2: Booking theo phòng (check trùng lịch)
CREATE TABLE IF NOT EXISTS bookings_by_room (
    room_id UUID,
    check_in_date date,
    booking_id UUID,
    customer_id UUID,
    check_out_date date,
    status text,
    PRIMARY KEY (room_id, check_in_date)
);

-- Bảng 3: Booking theo khách hàng
CREATE TABLE IF NOT EXISTS bookings_by_customer (
    customer_id UUID,
    booking_date timestamp,
    booking_id UUID,
    room_id UUID,
    hotel_id UUID,
    status text,
    PRIMARY KEY (customer_id, booking_date)
);

-- Bảng 4: Booking theo ngày (cho Dashboard)
CREATE TABLE IF NOT EXISTS hotel_booking.bookings_by_date (
    booking_date date,
    hotel_id UUID,
    booking_id UUID,
    customer_id UUID,
    room_id UUID,
    status text,
    PRIMARY KEY ((booking_date, hotel_id), booking_id)
);

-- Bảng 5: hotels
CREATE TABLE IF NOT EXISTS hotel_booking.hotels (
    hotel_id UUID,
    name text,
    address text,
    city text,
    phone text,
    rating decimal,
    created_at timestamp,
    PRIMARY KEY (hotel_id)
);

-- Bảng 6: customers
CREATE TABLE IF NOT EXISTS hotel_booking.customers (
    customer_id UUID,
    full_name text,
    email text,
    phone text,
    id_number text,
    created_at timestamp,
    PRIMARY KEY (customer_id)
);

-- Bảng 7: sử dụng để login
CREATE TABLE IF NOT EXISTS hotel_booking.customers_by_email (
    email text,
    customer_id UUID,
    full_name text,
    phone text,
    PRIMARY KEY (email)
);



-- HT1 = Sunrise Hotel (HCM)
INSERT INTO hotels (hotel_id, name, address, city, phone, rating, created_at) VALUES 
(00000000-0000-0000-0000-000000000001, 'Sunrise Hotel', '123 Nguyễn Huệ, Q1', 'Hồ Chí Minh', '0281234561', 4.5, toTimestamp(now()));

-- HT2 = Blue Ocean Resort (Đà Nẵng)
INSERT INTO hotels (hotel_id, name, address, city, phone, rating, created_at) VALUES 
(00000000-0000-0000-0000-000000000002, 'Blue Ocean Resort', '456 Trần Phú', 'Đà Nẵng', '0236123452', 4.8, toTimestamp(now()));

-- HT3 = Hanoi Pearl (Hà Nội)
INSERT INTO hotels (hotel_id, name, address, city, phone, rating, created_at) VALUES 
(00000000-0000-0000-0000-000000000003, 'Hanoi Pearl', '789 Hàng Bài, HK', 'Hà Nội', '0241234563', 4.2, toTimestamp(now()));

-- HT4 = Nha Trang Bay
INSERT INTO hotels (hotel_id, name, address, city, phone, rating, created_at) VALUES 
(00000000-0000-0000-0000-000000000004, 'Nha Trang Bay', '101 Trần Phú', 'Nha Trang', '0258123454', 4.6, toTimestamp(now()));

-- HT5 = Phu Quoc Sunset
INSERT INTO hotels (hotel_id, name, address, city, phone, rating, created_at) VALUES 
(00000000-0000-0000-0000-000000000005, 'Phu Quoc Sunset', '202 Bãi Trường', 'Phú Quốc', '0297123455', 4.9, toTimestamp(now()));


-- customers
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000001, 'Nguyễn Văn An', 'an.nguyen@gmail.com', '0901111111', '001234567801', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000002, 'Trần Thị Bình', 'binh.tran@gmail.com', '0902222222', '001234567802', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000003, 'Lê Minh Cường', 'cuong.le@gmail.com', '0903333333', '001234567803', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000004, 'Phạm Thu Dung', 'dung.pham@gmail.com', '0904444444', '001234567804', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000005, 'Hoàng Văn Em', 'em.hoang@gmail.com', '0905555555', '001234567805', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000006, 'Vũ Thị Phương', 'phuong.vu@gmail.com', '0906666666', '001234567806', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000007, 'Đặng Quốc Giang', 'giang.dang@gmail.com', '0907777777', '001234567807', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000008, 'Bùi Thị Hoa', 'hoa.bui@gmail.com', '0908888888', '001234567808', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000009, 'Đỗ Minh Khánh', 'khanh.do@gmail.com', '0909999999', '001234567809', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000010, 'Ngô Thị Lan', 'lan.ngo@gmail.com', '0910111111', '001234567810', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000011, 'Trịnh Văn Minh', 'minh.trinh@gmail.com', '0911222222', '001234567811', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000012, 'Lý Thị Ngọc', 'ngoc.ly@gmail.com', '0912333333', '001234567812', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000013, 'Phan Văn Oanh', 'oanh.phan@gmail.com', '0913444444', '001234567813', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000014, 'Dương Thị Phúc', 'phuc.duong@gmail.com', '0914555555', '001234567814', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000015, 'Cao Văn Quang', 'quang.cao@gmail.com', '0915666666', '001234567815', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000016, 'Lâm Thị Rosa', 'rosa.lam@gmail.com', '0916777777', '001234567816', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000017, 'Tạ Văn Sơn', 'son.ta@gmail.com', '0917888888', '001234567817', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000018, 'Mai Thị Tuyết', 'tuyet.mai@gmail.com', '0918999999', '001234567818', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000019, 'Hồ Văn Uy', 'uy.ho@gmail.com', '0920111111', '001234567819', toTimestamp(now()));
INSERT INTO customers (customer_id, full_name, email, phone, id_number, created_at) VALUES 
(10000000-0000-0000-0000-000000000020, 'Đinh Thị Vân', 'van.dinh@gmail.com', '0921222222', '001234567820', toTimestamp(now()));

-- customers_by_email (dùng cho login)
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('an.nguyen@gmail.com', 10000000-0000-0000-0000-000000000001, 'Nguyễn Văn An', '0901111111');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('binh.tran@gmail.com', 10000000-0000-0000-0000-000000000002, 'Trần Thị Bình', '0902222222');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('cuong.le@gmail.com', 10000000-0000-0000-0000-000000000003, 'Lê Minh Cường', '0903333333');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('dung.pham@gmail.com', 10000000-0000-0000-0000-000000000004, 'Phạm Thu Dung', '0904444444');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('em.hoang@gmail.com', 10000000-0000-0000-0000-000000000005, 'Hoàng Văn Em', '0905555555');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('phuong.vu@gmail.com', 10000000-0000-0000-0000-000000000006, 'Vũ Thị Phương', '0906666666');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('giang.dang@gmail.com', 10000000-0000-0000-0000-000000000007, 'Đặng Quốc Giang', '0907777777');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('hoa.bui@gmail.com', 10000000-0000-0000-0000-000000000008, 'Bùi Thị Hoa', '0908888888');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('khanh.do@gmail.com', 10000000-0000-0000-0000-000000000009, 'Đỗ Minh Khánh', '0909999999');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('lan.ngo@gmail.com', 10000000-0000-0000-0000-000000000010, 'Ngô Thị Lan', '0910111111');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('minh.trinh@gmail.com', 10000000-0000-0000-0000-000000000011, 'Trịnh Văn Minh', '0911222222');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('ngoc.ly@gmail.com', 10000000-0000-0000-0000-000000000012, 'Lý Thị Ngọc', '0912333333');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('oanh.phan@gmail.com', 10000000-0000-0000-0000-000000000013, 'Phan Văn Oanh', '0913444444');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('phuc.duong@gmail.com', 10000000-0000-0000-0000-000000000014, 'Dương Thị Phúc', '0914555555');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('quang.cao@gmail.com', 10000000-0000-0000-0000-000000000015, 'Cao Văn Quang', '0915666666');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('rosa.lam@gmail.com', 10000000-0000-0000-0000-000000000016, 'Lâm Thị Rosa', '0916777777');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('son.ta@gmail.com', 10000000-0000-0000-0000-000000000017, 'Tạ Văn Sơn', '0917888888');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('tuyet.mai@gmail.com', 10000000-0000-0000-0000-000000000018, 'Mai Thị Tuyết', '0918999999');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('uy.ho@gmail.com', 10000000-0000-0000-0000-000000000019, 'Hồ Văn Uy', '0920111111');
INSERT INTO customers_by_email (email, customer_id, full_name, phone) VALUES ('van.dinh@gmail.com', 10000000-0000-0000-0000-000000000020, 'Đinh Thị Vân', '0921222222');


-- KS HT1 (Sunrise) - P1 đến P6
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

-- KS HT2 (Blue Ocean) - P7 đến P12
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000002, 20000000-0000-0000-0000-000000000007, '101', 'Standard', 120, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000002, 20000000-0000-0000-0000-000000000008, '102', 'Standard', 120, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000002, 20000000-0000-0000-0000-000000000009, '201', 'Deluxe', 180, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000002, 20000000-0000-0000-0000-000000000010, '202', 'Deluxe', 180, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000002, 20000000-0000-0000-0000-000000000011, '301', 'Suite', 300, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000002, 20000000-0000-0000-0000-000000000012, '302', 'Suite', 300, 'AVAILABLE');

-- KS HT3 (Hanoi Pearl) - P13 đến P18
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000003, 20000000-0000-0000-0000-000000000013, '101', 'Standard', 90, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000003, 20000000-0000-0000-0000-000000000014, '102', 'Standard', 90, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000003, 20000000-0000-0000-0000-000000000015, '201', 'Deluxe', 140, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000003, 20000000-0000-0000-0000-000000000016, '202', 'Deluxe', 140, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000003, 20000000-0000-0000-0000-000000000017, '301', 'Suite', 220, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000003, 20000000-0000-0000-0000-000000000018, '302', 'Suite', 220, 'AVAILABLE');

-- KS HT4 (Nha Trang Bay) - P19 đến P24
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000004, 20000000-0000-0000-0000-000000000019, '101', 'Standard', 110, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000004, 20000000-0000-0000-0000-000000000020, '102', 'Standard', 110, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000004, 20000000-0000-0000-0000-000000000021, '201', 'Deluxe', 160, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000004, 20000000-0000-0000-0000-000000000022, '202', 'Deluxe', 160, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000004, 20000000-0000-0000-0000-000000000023, '301', 'Suite', 280, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000004, 20000000-0000-0000-0000-000000000024, '302', 'Suite', 280, 'AVAILABLE');

-- KS HT5 (Phu Quoc Sunset) - P25 đến P30
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000005, 20000000-0000-0000-0000-000000000025, '101', 'Standard', 130, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000005, 20000000-0000-0000-0000-000000000026, '102', 'Standard', 130, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000005, 20000000-0000-0000-0000-000000000027, '201', 'Deluxe', 190, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000005, 20000000-0000-0000-0000-000000000028, '202', 'Deluxe', 190, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000005, 20000000-0000-0000-0000-000000000029, '301', 'Suite', 350, 'AVAILABLE');
INSERT INTO rooms_by_hotel (hotel_id, room_id, room_number, room_type, price, status) VALUES 
(00000000-0000-0000-0000-000000000005, 20000000-0000-0000-0000-000000000030, '302', 'Suite', 350, 'AVAILABLE');


INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000001, '2026-01-05', 30000000-0000-0000-0000-000000000001, 10000000-0000-0000-0000-000000000001, '2026-01-08', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000002, '2026-01-06', 30000000-0000-0000-0000-000000000002, 10000000-0000-0000-0000-000000000002, '2026-01-09', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000003, '2026-01-07', 30000000-0000-0000-0000-000000000003, 10000000-0000-0000-0000-000000000003, '2026-01-10', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000005, '2026-01-08', 30000000-0000-0000-0000-000000000004, 10000000-0000-0000-0000-000000000004, '2026-01-12', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000007, '2026-01-05', 30000000-0000-0000-0000-000000000005, 10000000-0000-0000-0000-000000000005, '2026-01-09', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000008, '2026-01-10', 30000000-0000-0000-0000-000000000006, 10000000-0000-0000-0000-000000000006, '2026-01-14', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000009, '2026-01-06', 30000000-0000-0000-0000-000000000007, 10000000-0000-0000-0000-000000000007, '2026-01-10', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000011, '2026-01-12', 30000000-0000-0000-0000-000000000008, 10000000-0000-0000-0000-000000000008, '2026-01-16', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000013, '2026-01-05', 30000000-0000-0000-0000-000000000009, 10000000-0000-0000-0000-000000000009, '2026-01-08', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000014, '2026-01-09', 30000000-0000-0000-0000-000000000010, 10000000-0000-0000-0000-000000000010, '2026-01-13', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000015, '2026-01-11', 30000000-0000-0000-0000-000000000011, 10000000-0000-0000-0000-000000000011, '2026-01-15', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000017, '2026-01-08', 30000000-0000-0000-0000-000000000012, 10000000-0000-0000-0000-000000000012, '2026-01-12', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000019, '2026-01-06', 30000000-0000-0000-0000-000000000013, 10000000-0000-0000-0000-000000000013, '2026-01-10', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000020, '2026-01-10', 30000000-0000-0000-0000-000000000014, 10000000-0000-0000-0000-000000000014, '2026-01-14', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000021, '2026-01-13', 30000000-0000-0000-0000-000000000015, 10000000-0000-0000-0000-000000000015, '2026-01-17', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000023, '2026-01-07', 30000000-0000-0000-0000-000000000016, 10000000-0000-0000-0000-000000000016, '2026-01-11', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000025, '2026-01-05', 30000000-0000-0000-0000-000000000017, 10000000-0000-0000-0000-000000000017, '2026-01-09', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000026, '2026-01-11', 30000000-0000-0000-0000-000000000018, 10000000-0000-0000-0000-000000000018, '2026-01-15', 'CONFIRMED');
INSERT INTO bookings_by_room (room_id, check_in_date, booking_id, customer_id, check_out_date, status) VALUES 
(20000000-0000-0000-0000-000000000027, '2026-01-14', 30000000-0000-0000-0000-000000000019, 10000000-0000-0000-0000-000000000019, '2026-01-18', 'CONFIRMED');
