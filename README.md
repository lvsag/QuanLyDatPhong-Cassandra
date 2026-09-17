<<<<<<< HEAD
# QuanLyDatPhong-Cassandra
=======
# QuanLyDatPhong (Cassandra)

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

2. Nếu cần nạp dữ liệu mẫu:

```powershell
python seed_db.py
```

3. Chạy ứng dụng demo:

```powershell
python main.py
```

>>>>>>> 5126c8a (code phần 1)
