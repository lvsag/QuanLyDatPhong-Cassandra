
# QuanLyDatPhong-Cassandra

Hệ thống Quản lý Đặt phòng Khách sạn sử dụng Cơ sở dữ liệu phân tán Apache Cassandra và Web Dashboard (Streamlit).

---

## 📁 Cấu trúc Thư mục Dự án

```text
QuanLyDatPhong/
│   cassandra_config.py      # Cấu hình kết nối, Keyspace & Schema Cassandra
│   seed_data.cql            # Dữ liệu mẫu ban đầu (CQL)
│   seed_db.py               # Kịch bản nạp dữ liệu mẫu vào Cassandra
│   db_check.py              # Script kiểm tra dữ liệu các bảng
│   inspect_schema.py        # Script xem cấu trúc chi tiết các bảng
│   main.py                  # Kịch bản chạy kiểm thử luồng nghiệp vụ trên Console
│   app.py                   # Entrypoint khởi chạy Web Dashboard
│   requirements.txt         # Thư viện phụ thuộc
│   README.md                # Tài liệu hướng dẫn
│
├── repository/              # Data Access Layer (DAL) - Thao tác trực tiếp với Cassandra
│   ├── __init__.py
│   ├── hotel_repository.py      # CRUD Khách sạn (bảng hotels)
│   ├── customer_repository.py   # CRUD Khách hàng (bảng customers, customers_by_email)
│   ├── room_repository.py       # CRUD Phòng (bảng rooms_by_hotel)
│   └── booking_repository.py    # Quản lý Đặt phòng & LWT chống trùng lịch (bookings_by_room, ...)
│
├── services/                # Business Logic Layer (BLL) - Xử lý nghiệp vụ & thống kê
│   ├── __init__.py
│   └── dashboard_service.py # Tính toán tỉ lệ lấp đầy, doanh thu theo ngày/tháng
│
└── views/                   # Presentation Layer (UI Web)
    ├── __init__.py
    └── dashboard_view.py    # Giao diện Web Dashboard (Streamlit, KPI, Charts, Tabs)
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy (Windows)

### 1. Kích hoạt môi trường ảo & cài thư viện

Code phần 1 — quản lý đặt phòng sử dụng Cassandra.

Nội dung:
- `cassandra_config.py`: cấu hình kết nối, tạo keyspace và bảng (safe `CREATE IF NOT EXISTS`).
- `repository/`: lớp truy cập dữ liệu cho hotels, customers, rooms, bookings.
- `seed_data.cql` và `seed_db.py`: kịch bản seed dữ liệu mẫu.
- `db_check.py`: kiểm tra nhanh các bảng và in mẫu dữ liệu.
- `main.py`: ví dụ chạy — in dữ liệu hiện có, tạo hotel/customer/room, tạo booking và in kết quả.

Hướng dẫn chạy (Windows):

1. Tạo venv Python 3.11 và cài dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Nạp dữ liệu mẫu (nếu chưa nạp)
```powershell
python seed_db.py
```

### 3. Khởi chạy Hệ thống Web Quản lý Đặt phòng (HTML/CSS & Flask)
```powershell
python app.py
```
*Trình duyệt sẽ mở tại `http://127.0.0.1:5000` bao gồm đầy đủ:*
- **📊 Dashboard Thống kê**: `http://127.0.0.1:5000/dashboard` (KPIs, biểu đồ Chart.js doanh thu & tỉ lệ phòng)
- **🏢 Quản lý Khách sạn (Admin)**: `http://127.0.0.1:5000/admin/hotels`
- **🚪 Quản lý Phòng & Trạng thái**: `http://127.0.0.1:5000/admin/rooms`
- **📅 Quản lý Đặt phòng & Check-in/Check-out**: `http://127.0.0.1:5000/admin/bookings`
- **👥 Quản lý Khách hàng & Tra cứu**: `http://127.0.0.1:5000/admin/customers`
- **🌐 Cổng Đặt phòng Khách hàng (Client Portal)**: `http://127.0.0.1:5000/client`
- **🔐 Đăng nhập / Đăng xuất khách hàng**: `http://127.0.0.1:5000/client/login` và `http://127.0.0.1:5000/client/logout`
- **🧾 Đơn đặt phòng của tôi**: yêu cầu đăng nhập tại `http://127.0.0.1:5000/client/my-bookings`

### Quy tắc phòng khả dụng

Client chỉ hiển thị và cho phép đặt phòng có trạng thái `AVAILABLE`. Các phòng `OCCUPIED`, `CLEANING` và `MAINTENANCE` bị ẩn khỏi danh sách; bước xác nhận cũng kiểm tra lại trạng thái để tránh đặt qua URL cũ.

### Tài khoản khách hàng

Khách hàng mới được tạo tài khoản khi hoàn tất đặt phòng và phiên đăng nhập được giữ trong session Flask. Với dữ liệu cũ trong `seed_data.cql`, có thể đăng nhập bằng email và số điện thoại tương ứng ở trường mật khẩu tạm thời. Schema tự bổ sung cột `password_hash` khi ứng dụng khởi động.

---

### 4. (Tùy chọn) Chạy giao diện Streamlit Dashboard cũ
```powershell
streamlit run views/dashboard_view.py
```
