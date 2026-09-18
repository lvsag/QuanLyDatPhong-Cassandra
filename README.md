
# 🏨 QuanLyDatPhong-Cassandra

Hệ thống Quản lý Đặt phòng Khách sạn sử dụng **Apache Cassandra** (Cơ sở dữ liệu NoSQL phân tán) kết hợp với **Flask Web Dashboard** & **Client Portal**.

---

## 🌟 Tính năng chính

- **Quản lý Đặt phòng (Booking & LWT):** Đặt phòng thời gian thực, tự động tính tổng tiền, hỗ trợ chống trùng lịch với Lightweight Transactions (LWT) trong Cassandra.
- **Client Portal (Cổng Khách hàng):** 
  - Xem danh sách phòng khả dụng (`AVAILABLE`).
  - Đăng ký, đăng nhập tài khoản khách hàng.
  - Đặt phòng trực tuyến và quản lý đơn đặt phòng cá nhân.
- **Admin Dashboard (Trang Quản trị):**
  - **📊 Thống kê KPIs:** Tổng doanh thu, tỉ lệ lấp đầy phòng, biểu đồ trực quan (Chart.js).
  - **🏢 Quản lý Khách sạn & Phòng:** CRUD Khách sạn, Phòng, cập nhật trạng thái phòng (`AVAILABLE`, `OCCUPIED`, `CLEANING`, `MAINTENANCE`).
  - **📅 Quản lý Đặt phòng:** Xem danh sách, thực hiện Check-in, Check-out, Hủy phòng.
  - **👥 Quản lý Khách hàng:** Tra cứu thông tin và lịch sử khách hàng.

---

## 📁 Cấu trúc Thư mục Dự án

```text
QuanLyDatPhong/
│   app.py                   # Main Flask App & Route Handlers
│   cassandra_config.py      # Cấu hình kết nối, Keyspace & Schema Cassandra
│   seed_data.cql            # Dữ liệu mẫu Cassandra (CQL)
│   seed_db.py               # Script nạp dữ liệu mẫu vào Cassandra
│   db_check.py              # Script kiểm tra dữ liệu các bảng
│   inspect_schema.py        # Script xem cấu trúc bảng trong Cassandra
│   main.py                  # Script kiểm thử luồng nghiệp vụ trên Console
│   requirements.txt         # Thư viện phụ thuộc Python
│   README.md                # Tài liệu hướng dẫn
│
├── repository/              # Data Access Layer (DAL) - Thao tác với Cassandra
│   ├── hotel_repository.py      # Thao tác bảng hotels
│   ├── customer_repository.py   # Thao tác bảng customers, customers_by_email
│   ├── room_repository.py       # Thao tác bảng rooms_by_hotel
│   └── booking_repository.py    # Thao tác bảng bookings_by_room (LWT)
│
├── services/                # Business Logic Layer (BLL)
│   └── dashboard_service.py # Tính toán tỉ lệ lấp đầy, doanh thu theo ngày/tháng
│
├── static/                  # File tĩnh Web (CSS, JS, Custom Styles)
├── templates/               # Giao diện HTML (Jinja2 Templates - Admin & Client)
└── views/                   # Giao diện phụ trợ / Streamlit View
    └── dashboard_view.py    # (Tùy chọn) Giao diện Streamlit Dashboard cũ
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy (Windows)

### 1. Kích hoạt môi trường ảo & cài đặt thư viện

```powershell
# Tạo môi trường ảo Python 3.11
py -3.11 -m venv .venv

# Kích hoạt môi trường ảo
.\.venv\Scripts\Activate.ps1

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### 2. Nạp dữ liệu mẫu vào Cassandra (Seed Database)

*Đảm bảo dịch vụ Cassandra đã khởi chạy và sẵn sàng kết nối tại localhost:9042.*

```powershell
python seed_db.py
```

### 3. Khởi chạy Ứng dụng Web (Flask Application)

```powershell
python app.py
```

Sau khi chạy thành công, truy cập trình duyệt tại: **`http://127.0.0.1:5000`**

Các đường dẫn chính:
- **📊 Admin Dashboard:** `http://127.0.0.1:5000/dashboard`
- **🏢 Quản lý Khách sạn:** `http://127.0.0.1:5000/admin/hotels`
- **🚪 Quản lý Phòng:** `http://127.0.0.1:5000/admin/rooms`
- **📅 Quản lý Đặt phòng:** `http://127.0.0.1:5000/admin/bookings`
- **👥 Quản lý Khách hàng:** `http://127.0.0.1:5000/admin/customers`
- **🌐 Client Portal (Khách hàng):** `http://127.0.0.1:5000/client`
- **🧾 Đơn đặt của tôi:** `http://127.0.0.1:5000/client/my-bookings`

---

## ⚙️ Quy tắc Hệ thống & Lưu ý

1. **Quy tắc Phòng khả dụng (Available Rooms):**
   - Phía Client chỉ hiển thị và cho phép đặt các phòng có trạng thái `AVAILABLE`.
   - Các phòng ở trạng thái `OCCUPIED`, `CLEANING`, hoặc `MAINTENANCE` sẽ tự động bị ẩn khỏi giao diện đặt phòng của khách hàng.

2. **Xác thực Khách hàng & Bảo mật:**
   - Khách hàng mới khi đặt phòng sẽ được tự động khởi tạo tài khoản.
   - Mật khẩu khách hàng được mã hóa `password_hash` an toàn trong Cassandra.
   - Với dữ liệu mẫu ban đầu (`seed_data.cql`), có thể đăng nhập bằng **Email** và sử dụng **Số điện thoại** làm mật khẩu tạm thời.

3. **Công cụ phụ trợ (Tùy chọn):**
   - Chạy test console: `python main.py`
   - Chạy Streamlit dashboard cũ: `streamlit run views/dashboard_view.py`

