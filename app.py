import calendar
import os
import sys
import uuid
from datetime import date, datetime, timedelta

from flask import Flask, flash, redirect, render_template, request, session, url_for

# Đảm bảo đường dẫn gốc nằm trong sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from cassandra_config import to_py_date
from repository import BookingRepository, CustomerRepository, HotelRepository, RoomRepository
from services.dashboard_service import DashboardService

app = Flask(__name__)
app.secret_key = "cassandra_hotel_management_secret_key"

# Lazy-loaded singletons
_hotel_repo = None
_room_repo = None
_customer_repo = None
_booking_repo = None
_dashboard_service = None


def get_hotel_repo():
    global _hotel_repo
    if _hotel_repo is None:
        _hotel_repo = HotelRepository()
    return _hotel_repo


def get_room_repo():
    global _room_repo
    if _room_repo is None:
        _room_repo = RoomRepository()
    return _room_repo


def get_customer_repo():
    global _customer_repo
    if _customer_repo is None:
        _customer_repo = CustomerRepository()
    return _customer_repo


def get_booking_repo():
    global _booking_repo
    if _booking_repo is None:
        _booking_repo = BookingRepository()
    return _booking_repo


def get_dashboard_service():
    global _dashboard_service
    if _dashboard_service is None:
        _dashboard_service = DashboardService()
    return _dashboard_service


def _room_is_bookable(room):
    return str(room.get("status", "")).upper() == "AVAILABLE"


# ==========================================
# 1. DASHBOARD BÁO CÁO & THỐNG KÊ
# ==========================================
@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    service = get_dashboard_service()
    hotels = service.list_hotels()
    if not hotels:
        flash("Chưa có dữ liệu khách sạn. Hãy chạy `python seed_db.py` để nạp dữ liệu.", "warning")
        return render_template(
            "dashboard.html",
            active_page="dashboard",
            hotels=[],
            current_hotel=None,
            occ_today={"total_rooms": 0, "occupied": 0, "available": 0, "occupied_details": []},
            occ_rate=0.0,
            rev_month={"total_revenue": 0, "total_bookings": 0, "daily": []},
            status_summary={},
            target_date_str="2026-01-08",
            month=1,
            year=2026,
        )

    # Lấy params từ request
    hotel_id_str = request.args.get("hotel_id", str(hotels[0]["hotel_id"]))
    hotel_id = uuid.UUID(hotel_id_str) if isinstance(hotel_id_str, str) and "-" in hotel_id_str else hotel_id_str
    current_hotel = next((h for h in hotels if str(h["hotel_id"]) == str(hotel_id)), hotels[0])

    target_date_str = request.args.get("target_date", "2026-01-08")
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except Exception:
        target_date = date(2026, 1, 8)
        target_date_str = "2026-01-08"

    month = int(request.args.get("month", 1))
    year = int(request.args.get("year", 2026))

    # Tính toán số liệu
    occ_today = service.room_occupancy_on_date(current_hotel["hotel_id"], target_date)

    first_day = date(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    to_date_exclusive = date(year, month, last_day_num) + timedelta(days=1)
    occ_rate = service.occupancy_rate(current_hotel["hotel_id"], first_day, to_date_exclusive)
    rev_month = service.revenue_by_month(current_hotel["hotel_id"], year, month)
    status_summary, _ = service.room_status_summary(current_hotel["hotel_id"])

    # Chuyển đổi daily data sang định dạng json-serializable
    for item in rev_month.get("daily", []):
        if isinstance(item.get("date"), (date, datetime)):
            item["date"] = item["date"].strftime("%Y-%m-%d")

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        hotels=hotels,
        current_hotel=current_hotel,
        occ_today=occ_today,
        occ_rate=occ_rate,
        rev_month=rev_month,
        status_summary=status_summary,
        target_date_str=target_date_str,
        month=month,
        year=year,
    )


# ==========================================
# 2. PHÂN HỆ QUẢN TRỊ (ADMIN)
# ==========================================

# ----- Quản lý Khách sạn -----
@app.route("/admin/hotels")
def admin_hotels():
    hotel_repo = get_hotel_repo()
    hotels = hotel_repo.get_all()
    return render_template("admin/hotels.html", active_page="hotels", hotels=hotels)


@app.route("/admin/hotels/create", methods=["POST"])
def admin_create_hotel():
    name = request.form.get("name")
    address = request.form.get("address")
    city = request.form.get("city")
    phone = request.form.get("phone")
    rating = float(request.form.get("rating", 4.5))

    hotel_repo = get_hotel_repo()
    hotel_id = hotel_repo.create(name, address, city, phone, rating)
    flash(f"Đã thêm thành công khách sạn '{name}' (ID: {hotel_id})", "success")
    return redirect(url_for("admin_hotels"))


@app.route("/admin/hotels/<hotel_id>/update", methods=["POST"])
def admin_update_hotel(hotel_id):
    name = request.form.get("name")
    address = request.form.get("address")
    city = request.form.get("city")
    phone = request.form.get("phone")
    rating = float(request.form.get("rating", 4.5))

    hotel_repo = get_hotel_repo()
    hotel_repo.update_safe(hotel_id, name, address, city, phone, rating)
    flash(f"Đã cập nhật thông tin khách sạn '{name}'", "success")
    return redirect(url_for("admin_hotels"))


@app.route("/admin/hotels/<hotel_id>/delete", methods=["POST"])
def admin_delete_hotel(hotel_id):
    hotel_repo = get_hotel_repo()
    hotel_repo.delete_safe(hotel_id)
    flash("Đã xóa khách sạn thành công khỏi Cassandra.", "info")
    return redirect(url_for("admin_hotels"))


# ----- Quản lý Phòng -----
@app.route("/admin/rooms")
def admin_rooms():
    hotel_repo = get_hotel_repo()
    room_repo = get_room_repo()
    hotels = hotel_repo.get_all()
    if not hotels:
        flash("Chưa có khách sạn nào trong hệ thống!", "warning")
        return render_template("admin/rooms.html", active_page="rooms", hotels=[], current_hotel=None, rooms=[])

    hotel_id_str = request.args.get("hotel_id", str(hotels[0]["hotel_id"]))
    current_hotel = next((h for h in hotels if str(h["hotel_id"]) == hotel_id_str), hotels[0])
    rooms = room_repo.get_by_hotel(current_hotel["hotel_id"])

    return render_template(
        "admin/rooms.html",
        active_page="rooms",
        hotels=hotels,
        current_hotel=current_hotel,
        rooms=rooms,
    )


@app.route("/admin/rooms/create", methods=["POST"])
def admin_create_room():
    hotel_id = request.form.get("hotel_id")
    room_number = request.form.get("room_number")
    room_type = request.form.get("room_type")
    price = float(request.form.get("price", 1000000))
    status = request.form.get("status", "AVAILABLE")

    room_repo = get_room_repo()
    room_id = room_repo.create(hotel_id, room_number, room_type, price, status)
    flash(f"Đã tạo thành công phòng {room_number} ({room_type}) - ID: {room_id}", "success")
    return redirect(url_for("admin_rooms", hotel_id=hotel_id))


@app.route("/admin/rooms/update-status", methods=["POST"])
def admin_update_room_status():
    hotel_id = request.form.get("hotel_id")
    room_id = request.form.get("room_id")
    status = request.form.get("status")

    room_repo = get_room_repo()
    room_repo.update_status(hotel_id, room_id, status)
    flash(f"Đã cập nhật trạng thái phòng sang: {status}", "success")
    return redirect(url_for("admin_rooms", hotel_id=hotel_id))


@app.route("/admin/rooms/update-info", methods=["POST"])
def admin_update_room_info():
    hotel_id = request.form.get("hotel_id")
    room_id = request.form.get("room_id")
    room_number = request.form.get("room_number")
    room_type = request.form.get("room_type")
    price = float(request.form.get("price"))

    room_repo = get_room_repo()
    room_repo.update_info(hotel_id, room_id, room_number, room_type, price)
    flash(f"Đã cập nhật thông tin phòng {room_number}", "success")
    return redirect(url_for("admin_rooms", hotel_id=hotel_id))


@app.route("/admin/rooms/delete/<hotel_id>/<room_id>", methods=["POST"])
def admin_delete_room(hotel_id, room_id):
    room_repo = get_room_repo()
    room_repo.delete(hotel_id, room_id)
    flash("Đã xóa phòng khỏi khách sạn.", "info")
    return redirect(url_for("admin_rooms", hotel_id=hotel_id))


# ----- Quản lý Đặt phòng & Check-in / Check-out -----
@app.route("/admin/bookings")
def admin_bookings():
    hotel_repo = get_hotel_repo()
    room_repo = get_room_repo()
    customer_repo = get_customer_repo()
    booking_repo = get_booking_repo()

    hotels = hotel_repo.get_all()
    if not hotels:
        flash("Chưa có khách sạn nào trong hệ thống!", "warning")
        return render_template(
            "admin/bookings.html",
            active_page="bookings",
            hotels=[],
            current_hotel=None,
            bookings=[],
            rooms=[],
            target_date_str="2026-01-08",
        )

    hotel_id_str = request.args.get("hotel_id", str(hotels[0]["hotel_id"]))
    current_hotel = next((h for h in hotels if str(h["hotel_id"]) == hotel_id_str), hotels[0])

    target_date_str = request.args.get("target_date", "2026-01-08")
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except Exception:
        target_date = date(2026, 1, 8)
        target_date_str = "2026-01-08"

    bookings_raw = booking_repo.get_bookings_by_date(target_date, current_hotel["hotel_id"])
    rooms = room_repo.get_by_hotel(current_hotel["hotel_id"])
    room_map = {str(r["room_id"]): r for r in rooms}

    # Bổ sung thông tin phòng và khách hàng
    bookings = []
    for b in bookings_raw:
        item = dict(b)
        item["room_info"] = room_map.get(str(b["room_id"]))
        cust = customer_repo.get_by_id(b["customer_id"])
        item["customer_info"] = cust
        bookings.append(item)

    return render_template(
        "admin/bookings.html",
        active_page="bookings",
        hotels=hotels,
        current_hotel=current_hotel,
        bookings=bookings,
        rooms=rooms,
        target_date_str=target_date_str,
    )


@app.route("/admin/bookings/create", methods=["POST"])
def admin_create_booking():
    hotel_id_str = request.form.get("hotel_id")
    room_id_str = request.form.get("room_id")
    check_in_str = request.form.get("check_in_date")
    check_out_str = request.form.get("check_out_date")

    full_name = request.form.get("full_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    id_number = request.form.get("id_number", "")

    hotel_id = uuid.UUID(hotel_id_str)
    room_id = uuid.UUID(room_id_str)
    check_in_date = datetime.strptime(check_in_str, "%Y-%m-%d").date()
    check_out_date = datetime.strptime(check_out_str, "%Y-%m-%d").date()

    if check_out_date <= check_in_date:
        flash("Ngày Check-out phải sau ngày Check-in ít nhất 1 ngày!", "error")
        return redirect(url_for("admin_bookings", hotel_id=hotel_id_str, target_date=check_in_str))

    # Tìm hoặc tạo khách hàng
    customer_repo = get_customer_repo()
    existing_cust = customer_repo.get_by_email(email)
    if existing_cust:
        customer_id = existing_cust["customer_id"]
    else:
        customer_id = customer_repo.create(full_name, email, phone, id_number)

    # Đặt phòng với LWT
    booking_repo = get_booking_repo()
    success, booking_id, msg = booking_repo.create_booking(
        room_id=room_id,
        customer_id=customer_id,
        hotel_id=hotel_id,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
    )

    if success:
        flash(f"{msg} (Mã Booking: {booking_id})", "success")
    else:
        flash(f"Không thể đặt phòng: {msg}", "error")

    return redirect(url_for("admin_bookings", hotel_id=hotel_id_str, target_date=check_in_str))


@app.route("/admin/bookings/update-status", methods=["POST"])
def admin_update_booking_status():
    room_id_str = request.form.get("room_id")
    check_in_str = request.form.get("check_in_date")
    status = request.form.get("status")
    hotel_id_str = request.form.get("hotel_id", "")

    room_id = uuid.UUID(room_id_str) if isinstance(room_id_str, str) else room_id_str
    check_in_date = datetime.strptime(check_in_str, "%Y-%m-%d").date() if isinstance(check_in_str, str) else check_in_str

    booking_repo = get_booking_repo()
    booking_repo.update_booking_status(room_id, check_in_date, status)

    # Đồng bộ trạng thái phòng trong rooms_by_hotel
    if hotel_id_str:
        room_repo = get_room_repo()
        if status == "CHECKED_IN":
            room_repo.update_status(hotel_id_str, room_id_str, "OCCUPIED")
        elif status == "CHECKED_OUT":
            room_repo.update_status(hotel_id_str, room_id_str, "CLEANING")

    flash(f"Đã cập nhật trạng thái đơn đặt phòng sang: {status}", "success")
    return redirect(request.referrer or url_for("admin_bookings"))


@app.route("/admin/bookings/cancel", methods=["POST"])
def admin_cancel_booking():
    room_id = uuid.UUID(request.form.get("room_id"))
    booking_id = uuid.UUID(request.form.get("booking_id"))
    customer_id = uuid.UUID(request.form.get("customer_id"))
    hotel_id = uuid.UUID(request.form.get("hotel_id"))
    check_in_str = request.form.get("check_in_date")
    check_in_date = datetime.strptime(check_in_str, "%Y-%m-%d").date()

    booking_repo = get_booking_repo()
    booking_repo.cancel_booking(room_id, check_in_date, booking_id, customer_id, hotel_id)

    # Trả phòng về trạng thái sẵn sàng khi hủy booking
    room_repo = get_room_repo()
    room_repo.update_status(hotel_id, room_id, "AVAILABLE")

    flash("Đã hủy đơn đặt phòng và giải phóng slot phòng trên Cassandra!", "info")
    return redirect(request.referrer or url_for("admin_bookings"))


# ----- Quản lý Khách hàng -----
@app.route("/admin/customers")
def admin_customers():
    customer_repo = get_customer_repo()
    booking_repo = get_booking_repo()

    # Query all customers
    cluster, session = customer_repo.cluster, customer_repo.session
    rows = session.execute("SELECT * FROM customers")
    customers = [dict(r._asdict()) for r in rows]

    search_email = request.args.get("search_email", "").strip()
    searched_customer = None
    customer_bookings = []
    if search_email:
        searched_customer = customer_repo.get_by_email(search_email)
        if searched_customer:
            customer_bookings = booking_repo.get_bookings_by_customer(searched_customer["customer_id"])

    return render_template(
        "admin/customers.html",
        active_page="customers",
        customers=customers,
        search_email=search_email,
        searched_customer=searched_customer,
        customer_bookings=customer_bookings,
    )


# ==========================================
# 3. PHÂN HỆ KHÁCH HÀNG (CLIENT PORTAL)
# ==========================================
@app.route("/client")
def client_index():
    hotel_repo = get_hotel_repo()
    room_repo = get_room_repo()
    booking_repo = get_booking_repo()

    hotels = hotel_repo.get_all()
    if not hotels:
        flash("Chưa có khách sạn nào được kích hoạt.", "warning")
        return render_template(
            "client/index.html",
            active_page="client_index",
            hotels=[],
            current_hotel=None,
            available_rooms=[],
            check_in_str="2026-01-08",
            check_out_str="2026-01-10",
        )

    selected_hotel_id = request.args.get("hotel_id", str(hotels[0]["hotel_id"]))
    current_hotel = next((h for h in hotels if str(h["hotel_id"]) == selected_hotel_id), hotels[0])

    check_in_str = request.args.get("check_in_date", "2026-01-08")
    check_out_str = request.args.get("check_out_date", "2026-01-10")

    try:
        check_in = datetime.strptime(check_in_str, "%Y-%m-%d").date()
        check_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()
    except Exception:
        check_in = date(2026, 1, 8)
        check_out = date(2026, 1, 10)
        check_in_str = "2026-01-08"
        check_out_str = "2026-01-10"

    all_rooms = room_repo.get_by_hotel(current_hotel["hotel_id"])

    # Lọc phòng thực sự trống trong khoảng [check_in, check_out)
    available_rooms = []
    for r in all_rooms:
        if not _room_is_bookable(r):
            continue
        bookings = booking_repo.get_bookings_by_room(r["room_id"])
        is_free = True
        for b in bookings:
            if b.get("status") != "CONFIRMED":
                continue
            b_in = to_py_date(b.get("check_in_date"))
            b_out = to_py_date(b.get("check_out_date"))
            if b_in and b_out and max(b_in, check_in) < min(b_out, check_out):
                is_free = False
                break
        if is_free:
            available_rooms.append(r)

    return render_template(
        "client/index.html",
        active_page="client_index",
        hotels=hotels,
        current_hotel=current_hotel,
        selected_hotel_id=selected_hotel_id,
        available_rooms=available_rooms,
        check_in_str=check_in_str,
        check_out_str=check_out_str,
    )


@app.route("/client/book")
def client_book_form():
    hotel_id_str = request.args.get("hotel_id")
    room_id_str = request.args.get("room_id")
    check_in_str = request.args.get("check_in", "2026-01-08")
    check_out_str = request.args.get("check_out", "2026-01-10")

    hotel_repo = get_hotel_repo()
    room_repo = get_room_repo()

    hotel = hotel_repo.get_by_id_safe(hotel_id_str)
    room = room_repo.get_one(hotel_id_str, room_id_str)

    if not hotel or not room:
        flash("Không tìm thấy thông tin khách sạn hoặc phòng.", "error")
        return redirect(url_for("client_index"))

    if not _room_is_bookable(room):
        flash("Phòng này hiện không sẵn sàng để đặt. Vui lòng chọn phòng khác.", "error")
        return redirect(url_for("client_index", hotel_id=hotel_id_str, check_in_date=check_in_str, check_out_date=check_out_str))

    try:
        check_in = datetime.strptime(check_in_str, "%Y-%m-%d").date()
        check_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()
        nights = max(1, (check_out - check_in).days)
    except Exception:
        nights = 1

    total_price = float(room.get("price", 0)) * nights

    return render_template(
        "client/book_form.html",
        hotel=hotel,
        room=room,
        check_in_str=check_in_str,
        check_out_str=check_out_str,
        nights=nights,
        total_price=total_price,
    )


@app.route("/client/book/confirm", methods=["POST"])
def client_confirm_booking():
    hotel_id_str = request.form.get("hotel_id")
    room_id_str = request.form.get("room_id")
    check_in_str = request.form.get("check_in_date")
    check_out_str = request.form.get("check_out_date")

    full_name = request.form.get("full_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    id_number = request.form.get("id_number", "")

    hotel_id = uuid.UUID(hotel_id_str)
    room_id = uuid.UUID(room_id_str)
    check_in_date = datetime.strptime(check_in_str, "%Y-%m-%d").date()
    check_out_date = datetime.strptime(check_out_str, "%Y-%m-%d").date()

    room = get_room_repo().get_one(hotel_id, room_id)
    if not room or not _room_is_bookable(room):
        flash("Phòng vừa được cập nhật trạng thái và không còn nhận đặt phòng.", "error")
        return redirect(url_for("client_index", hotel_id=hotel_id_str, check_in_date=check_in_str, check_out_date=check_out_str))

    customer_repo = get_customer_repo()
    existing_cust = customer_repo.get_by_email(email)
    if existing_cust:
        customer_id = existing_cust["customer_id"]
    else:
        customer_id = customer_repo.create(full_name, email, phone, id_number)

    booking_repo = get_booking_repo()
    success, booking_id, msg = booking_repo.create_booking(
        room_id=room_id,
        customer_id=customer_id,
        hotel_id=hotel_id,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
    )

    if success:
        session["customer_id"] = str(customer_id)
        session["customer_email"] = email
        session["customer_name"] = full_name
        flash(f"🎉 Chúc mừng quý khách {full_name}! Đặt phòng thành công. Mã Booking: {booking_id}", "success")
        return redirect(url_for("client_my_bookings"))
    else:
        flash(f"Rất tiếc: {msg} Vui lòng chọn khoảng ngày hoặc phòng khác.", "error")
        return redirect(url_for("client_index", hotel_id=hotel_id_str))


@app.route("/client/my-bookings")
def client_my_bookings():
    if not session.get("customer_email"):
        return redirect(url_for("client_login", next=url_for("client_my_bookings")))

    search_email = session["customer_email"]
    customer_repo = get_customer_repo()
    booking_repo = get_booking_repo()
    hotel_repo = get_hotel_repo()
    room_repo = get_room_repo()

    customer = None
    bookings = []
    if search_email:
        customer = customer_repo.get_by_email(search_email)
        if customer:
            raw_bookings = booking_repo.get_bookings_by_customer(customer["customer_id"])
            for b in raw_bookings:
                item = dict(b)
                hotel = hotel_repo.get_by_id_safe(b["hotel_id"])
                item["hotel_name"] = hotel["name"] if hotel else str(b["hotel_id"])
                room = room_repo.get_one(b["hotel_id"], b["room_id"])
                item["room_info"] = f"Phòng {room['room_number']} ({room['room_type']})" if room else str(b["room_id"])

                # Tìm check_in_date từ room bookings để phục vụ hủy
                room_bookings = booking_repo.get_bookings_by_room(b["room_id"])
                rb_match = next((rb for rb in room_bookings if rb["booking_id"] == b["booking_id"]), None)
                if rb_match:
                    item["check_in_date"] = rb_match["check_in_date"]
                else:
                    item["check_in_date"] = None

                bookings.append(item)

    return render_template(
        "client/my_bookings.html",
        search_email=search_email,
        customer=customer,
        bookings=bookings,
    )


@app.route("/client/my-bookings/cancel", methods=["POST"])
def client_cancel_booking():
    email = request.form.get("email")
    room_id = uuid.UUID(request.form.get("room_id"))
    booking_id = uuid.UUID(request.form.get("booking_id"))
    customer_id = uuid.UUID(request.form.get("customer_id"))
    hotel_id = uuid.UUID(request.form.get("hotel_id"))
    check_in_str = request.form.get("check_in_date")
    check_in_date = datetime.strptime(check_in_str, "%Y-%m-%d").date()

    if str(customer_id) != str(session.get("customer_id")):
        flash("Phiên đăng nhập không hợp lệ.", "error")
        return redirect(url_for("client_login"))

    booking_repo = get_booking_repo()
    booking_repo.cancel_booking(room_id, check_in_date, booking_id, customer_id, hotel_id)
    flash("Quý khách đã hủy đơn đặt phòng thành công. Slot phòng đã được mở lại!", "info")
    return redirect(url_for("client_my_bookings"))


@app.route("/client/login", methods=["GET", "POST"])
def client_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        customer = get_customer_repo().verify_login(email, password)
        if customer:
            session["customer_id"] = str(customer["customer_id"])
            session["customer_email"] = email
            session["customer_name"] = customer.get("full_name", "")
            next_url = request.form.get("next") or url_for("client_index")
            return redirect(next_url if next_url.startswith("/") else url_for("client_index"))
        flash("Email hoặc mật khẩu không đúng.", "error")

    return render_template("client/login.html", next_url=request.args.get("next", ""))


@app.route("/client/register", methods=["GET", "POST"])
def client_register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([full_name, email, phone, password]):
            flash("Vui lòng nhập đầy đủ thông tin.", "error")
            return render_template("client/register.html")

        if password != confirm_password:
            flash("Mật khẩu xác nhận không khớp.", "error")
            return render_template("client/register.html")

        customer_repo = get_customer_repo()
        existing = customer_repo.get_by_email(email)
        if existing:
            flash("Email này đã được đăng ký. Vui lòng đăng nhập.", "error")
            return redirect(url_for("client_login"))

        customer_id = customer_repo.create(full_name, email, phone, password=password)
        session["customer_id"] = str(customer_id)
        session["customer_email"] = email
        session["customer_name"] = full_name
        flash(f"🎉 Chào mừng {full_name}! Tài khoản đã được tạo thành công.", "success")
        return redirect(url_for("client_index"))

    return render_template("client/register.html")


@app.route("/client/logout")
def client_logout():
    session.pop("customer_id", None)
    session.pop("customer_email", None)
    session.pop("customer_name", None)
    flash("Bạn đã đăng xuất khỏi tài khoản.", "info")
    return redirect(url_for("client_index"))


if __name__ == "__main__":
    print("🚀 Đang khởi chạy Hệ thống Web Quản lý Đặt phòng Khách sạn (Cassandra + Flask)...")
    print("👉 Mở trình duyệt tại: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
