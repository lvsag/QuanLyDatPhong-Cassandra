
import calendar
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from dashboard_service import DashboardService

st.set_page_config(page_title="Dashboard Quản lý Khách sạn", page_icon="🏨", layout="wide")


@st.cache_resource
def get_service():
    return DashboardService()


service = get_service()

st.title("🏨 Dashboard Quản lý Đặt phòng (Cassandra)")

hotels = service.list_hotels()
if not hotels:
    st.warning("Chưa có dữ liệu khách sạn. Chạy `python seed_db.py` rồi tải lại trang.")
    st.stop()

# ----- Sidebar: bộ lọc -----
hotel_options = {f"{h['name']} — {h['city']}": h["hotel_id"] for h in hotels}
hotel_label = st.sidebar.selectbox("Khách sạn", list(hotel_options.keys()))
hotel_id = hotel_options[hotel_label]

st.sidebar.markdown("### Bộ lọc thời gian")
target_date = st.sidebar.date_input("Xem tình trạng phòng ngày", value=date(2026, 1, 8))
year = st.sidebar.number_input("Năm (doanh thu)", value=2026, step=1)
month = st.sidebar.number_input("Tháng (doanh thu)", value=1, min_value=1, max_value=12, step=1)

if st.sidebar.button("🔄 Làm mới dữ liệu"):
    st.cache_resource.clear()
    st.rerun()

# ----- Tính toán -----
occ_today = service.room_occupancy_on_date(hotel_id, target_date)

first_day = date(int(year), int(month), 1)
last_day_num = calendar.monthrange(int(year), int(month))[1]
to_date_exclusive = date(int(year), int(month), last_day_num) + timedelta(days=1)
occ_rate = service.occupancy_rate(hotel_id, first_day, to_date_exclusive)
rev_month = service.revenue_by_month(hotel_id, int(year), int(month))

# ----- Hàng 1: 4 chỉ số chính -----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tổng số phòng", occ_today["total_rooms"])
c2.metric(f"Phòng trống ({target_date})", occ_today["available"])
c3.metric("Tỉ lệ lấp đầy tháng", f"{occ_rate}%")
c4.metric("Doanh thu tháng", f"{rev_month['total_revenue']:,.0f}")

st.markdown("---")

left, right = st.columns(2)

with left:
    st.subheader(f"Trạng thái phòng ngày {target_date}")
    df_status = pd.DataFrame(
        {"Trạng thái": ["Đã đặt", "Trống"], "Số phòng": [occ_today["occupied"], occ_today["available"]]}
    ).set_index("Trạng thái")
    st.bar_chart(df_status)
    st.caption(
        "Tính từ dữ liệu booking thực tế (check_in_date ≤ ngày < check_out_date), "
        "không lấy field `status` tĩnh trong rooms_by_hotel — vì field đó không "
        "tự cập nhật khi có booking mới."
    )

with right:
    st.subheader(f"Doanh thu theo ngày — tháng {month}/{year}")
    df_daily = pd.DataFrame(rev_month["daily"])
    if not df_daily.empty and df_daily["revenue"].sum() > 0:
        df_daily = df_daily.set_index("date")[["revenue"]]
        st.bar_chart(df_daily)
    else:
        st.info("Chưa có booking nào trong tháng này (đổi năm/tháng ở sidebar — dữ liệu mẫu nằm ở 01/2026).")

st.markdown("---")
st.subheader("Thống kê trạng thái phòng (field `status` — Người 2 cập nhật khi check-in/out)")
status_summary, total_rooms = service.room_status_summary(hotel_id)
st.write(status_summary)
