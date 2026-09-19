# QuanLyDatPhong-Cassandra

Quản lý đặt phòng khách sạn bằng Cassandra.

Thiết kế bảng, khóa và luồng ghi được giải thích trong [`docs/THIET_KE_CASSANDRA.md`](docs/THIET_KE_CASSANDRA.md).

Nội dung:
- `schema.cql`: định nghĩa keyspace/bảng (nguồn duy nhất, `CREATE IF NOT EXISTS`). `cassandra_config.py` tự nạp file này khi kết nối.
- `cassandra_config.py`: cấu hình kết nối, tạo keyspace và bảng.
- `repository/`: lớp truy cập dữ liệu cho hotels, customers, rooms, bookings, và `dashboard_service.py` tính số liệu dashboard.
- `seed_data.cql` và `seed_db.py`: dữ liệu mẫu (khách sạn, khách, phòng bằng CQL; booking nạp bằng Python qua `BookingRepository`).
- `db_check.py`: kiểm tra nhanh các bảng và in mẫu dữ liệu.
- `inspect_schema.py`: in partition key / clustering key của tất cả các bảng.
- `main.py`: ví dụ chạy — tạo hotel/customer/room, đặt phòng, thử trùng lịch, hủy và đặt lại.

Hướng dẫn chạy (Windows):

1. Tạo venv Python 3.11 và cài dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Nạp dữ liệu mẫu:

```powershell
python seed_db.py
```

Nếu DB đang ở schema cũ (còn bảng `bookings_by_room` / `bookings_by_date`), chạy với `--reset`. Lệnh này **xóa keyspace `hotel_booking`** rồi tạo lại:

```powershell
python seed_db.py --reset
```

3. Chạy ứng dụng demo:

```powershell
python main.py
```
