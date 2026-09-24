# 🏨 QuanLyDatPhong-Cassandra

Hệ thống Quản lý Đặt phòng Khách sạn NoSQL chuẩn **Query-First Architecture** sử dụng **Apache Cassandra** kết hợp **Flask Web Framework** (Admin Dashboard & Client Portal).

---

## 🏛️ Kiến trúc Data Modeling (Query-First NoSQL)

Hệ thống được thiết kế hoàn toàn theo nguyên tắc khuyến nghị của Apache Cassandra:

$$\text{BUSINESS OPERATION} \longrightarrow \text{ACCESS PATTERN} \longrightarrow \text{CQL QUERY} \longrightarrow \text{PRIMARY KEY} \longrightarrow \text{CASSANDRA TABLE}$$

* **Không có JOIN, không có FOREIGN KEY:** Toàn bộ dữ liệu được denormalize vào các Read Model phù hợp với từng Access Pattern.
* **Chống trùng phòng tuyệt đối bằng LWT Batch:** Sử dụng Paxos Lightweight Transactions (LWT) Conditional Batch (`IF NOT EXISTS`) trên cùng partition `room_id` cho từng đêm lưu trú (`stay_date`).
* **Không dùng ALLOW FILTERING:** Tất cả các truy vấn đều chỉ định chính xác Partition Key.
* **Snapshot Giá Phòng & Phân bổ Doanh Thu theo Stay Night:** Doanh thu được tính chuẩn xác theo từng đêm lưu trú thực tế thay vì cộng gộp vào ngày check-in. Giá phòng được snapshot tại thời điểm đặt, không bị thay đổi bởi biến động giá tương lai.

---

## 📊 Cấu trúc 9 Bảng Cassandra (`schema.cql`)

| STT | Bảng Cassandra | Partition Key | Clustering Key | Mục đích & Access Pattern |
|---|---|---|---|---|
| 1 | `hotels` | `hotel_id` | None | Tra cứu thông tin chi tiết khách sạn |
| 2 | `hotels_by_city` | `city` | `hotel_id` | Tìm kiếm khách sạn theo thành phố (Không dùng ALLOW FILTERING) |
| 3 | `rooms_by_hotel` | `hotel_id` | `room_id` | Quản lý danh sách và tình trạng phòng của từng khách sạn |
| 4 | `customers` | `customer_id` | None | Lưu trữ chi tiết hồ sơ khách hàng |
| 5 | `customers_by_email` | `email` | None | Đăng nhập & bảo đảm Email duy nhất với Paxos LWT `IF NOT EXISTS` |
| 6 | `bookings_by_id` | `booking_id` | None | Read Model chính xem chi tiết đơn đặt phòng bằng `timeuuid` |
| 7 | `bookings_by_customer` | `customer_id` | `booking_id` (DESC) | Lịch sử đơn đặt của khách hàng, sắp xếp theo thời gian mới nhất |
| 8 | `room_nights_by_room` | `room_id` | `stay_date` | Khóa từng đêm lưu trú của phòng — LWT Conditional Batch chống trùng lịch |
| 9 | `room_nights_by_hotel_date` | `(hotel_id, stay_date)` | `room_id` | Phục vụ Q10 Check-in, Occupancy, Doanh thu & Dashboard không N+1 query |

---

## 🌟 Tính năng chính

* **🌐 Client Portal (Khách hàng):**
  * Tra cứu phòng khả dụng theo khoảng ngày lưu trú `[check_in, check_out)`.
  * Đăng ký tài khoản (bảo đảm Email duy nhất bằng Paxos LWT) & đăng nhập an toàn.
  * Form đặt phòng tự động điền sẵn thông tin khách hàng đang đăng nhập.
  * Quản lý & hủy đơn đặt phòng cá nhân.

* **📊 Admin Dashboard (Quản trị viên):**
  * **📊 Thống kê KPIs:** Doanh thu phân bổ theo stay night, tỉ lệ lấp đầy phòng (Occupancy Rate), biểu đồ Chart.js trực quan.
  * **🏢 Quản lý Khách sạn & Buồng Phòng:** CRUD Khách sạn, Phòng, cập nhật tình trạng phòng real-time theo ngày được chọn.
  * **📅 Quản lý Đặt phòng & Lễ tân:** Xem danh sách check-in trong ngày, tạo đơn tại quầy (tự động lọc phòng trống), thực hiện Check-in / Check-out / Hủy phòng theo `booking_id`.
  * **👥 Quản lý Khách hàng:** Tra cứu thông tin và lịch sử đơn đặt của khách hàng.

---

## 📁 Cấu trúc Thư mục Dự án

```text
QuanLyDatPhong/
│   schema.cql               # Nguồn DDL duy nhất chứa định nghĩa 9 bảng Cassandra
│   seed_data.cql            # Dữ liệu mẫu Cassandra (Hotels, Rooms, Customers)
│   seed_db.py               # Script reset database & nạp dữ liệu mẫu chuẩn đồng bộ
│   cassandra_config.py      # Cấu hình Singleton Connection Pool & Date Converters
│   app.py                   # Main Flask Web Application & Controllers
│   test_system.py           # Bộ Unit Tests tự động kiểm tra 5 điều kiện hệ thống
│   main.py                  # Script kiểm thử luồng nghiệp vụ trên Console
│   db_check.py              # Script kiểm tra số lượng dòng và dữ liệu các bảng
│   inspect_schema.py        # Script kiểm tra danh sách bảng trong Cassandra
│   requirements.txt         # Thư viện phụ thuộc Python
│   README.md                # Tài liệu hướng dẫn
│
├── repository/              # Data Access Layer (DAL) - Thao tác Cassandra
│   ├── hotel_repository.py      # Thao tác bảng hotels & hotels_by_city
│   ├── customer_repository.py   # Thao tác bảng customers & customers_by_email (LWT)
│   ├── room_repository.py       # Thao tác bảng rooms_by_hotel
│   └── booking_repository.py    # Thao tác bookings_by_id, room_nights_by_room (LWT Batch)
│
├── services/                # Business Logic Layer (BLL)
│   └── dashboard_service.py # Tính toán Occupancy, Revenue phân bổ theo stay night
│
├── static/                  # File tĩnh Web (CSS, JS, Custom Styles)
└── templates/               # Giao diện HTML (Jinja2 Templates - Admin & Client)
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy (Windows)

### 1. Kích hoạt môi trường ảo & Cài đặt thư viện

```powershell
# Tạo môi trường ảo Python 3.11
py -3.11 -m venv .venv

# Kích hoạt môi trường ảo
.\.venv\Scripts\Activate.ps1

# Cài đặt thư viện cần thiết
pip install -r requirements.txt
```

### 2. Khởi tạo & Nạp dữ liệu vào Cassandra (Reset Database)

*Đảm bảo dịch vụ Cassandra đã khởi chạy và sẵn sàng kết nối tại `127.0.0.1:9042`.*

```powershell
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe seed_db.py
```

### 3. Khởi chạy Ứng dụng Web (Flask Application)

```powershell
.\.venv\Scripts\python.exe app.py
```

Sau khi chạy thành công, truy cập trình duyệt tại: **`http://127.0.0.1:5000`**

Các đường dẫn chính:
* **📊 Admin Dashboard:** `http://127.0.0.1:5000/dashboard`
* **🏢 Quản lý Khách sạn:** `http://127.0.0.1:5000/admin/hotels`
* **🚪 Quản lý Phòng:** `http://127.0.0.1:5000/admin/rooms`
* **📅 Quản lý Đặt phòng:** `http://127.0.0.1:5000/admin/bookings`
* **👥 Quản lý Khách hàng:** `http://127.0.0.1:5000/admin/customers`
* **🌐 Client Portal (Khách hàng):** `http://127.0.0.1:5000/client`
* **🧾 Đơn đặt của tôi:** `http://127.0.0.1:5000/client/my-bookings`

---

## 🧪 Chạy Kiểm thử Tự động (Unit Tests)

Dự án đi kèm bộ kiểm thử tự động [`test_system.py`](file:///d:/Cassandra/QuanLyDatPhong/test_system.py) bắt buộc kiểm tra 5 kịch bản cốt lõi:
1. **Booking Overlap & Checkout Boundary:** Kiểm tra chống trùng lịch cho các khoảng ngày đè nhau và cho phép nhận phòng đúng ngày checkout của đơn trước.
2. **Cancel State Transition:** Kiểm tra quy trình hủy đơn theo `booking_id` và tính Idempotency (không cho hủy 2 lần).
3. **Email Uniqueness:** Kiểm tra từ chối đăng ký tài khoản trùng Email bằng LWT.
4. **Price Snapshot:** Kiểm tra biến động giá phòng tương lai không ảnh hưởng đến doanh thu của booking cũ.
5. **Revenue Distribution:** Kiểm tra phân bổ doanh thu theo từng đêm lưu trú (stay night).

Chạy lệnh kiểm thử:
```powershell
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe -m unittest test_system.py
```

---

## ⚙️ Các Công cụ Phụ trợ

* **Kiểm tra dữ liệu các bảng:** `python db_check.py`
* **Kiểm tra danh sách bảng:** `python inspect_schema.py`
* **Kiểm thử Console nhanh:** `python main.py`
