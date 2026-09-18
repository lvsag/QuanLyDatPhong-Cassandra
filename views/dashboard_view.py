import calendar
import os
import sys
from datetime import date, timedelta

import pandas as pd
import streamlit as st

# Đảm bảo đường dẫn gốc nằm trong sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.dashboard_service import DashboardService


def get_service():
    if "dashboard_service" not in st.session_state:
        st.session_state.dashboard_service = DashboardService()
    return st.session_state.dashboard_service


def render_dashboard():
    st.set_page_config(
        page_title="Hệ thống Quản lý Đặt phòng & Khách sạn",
        page_icon="🏨",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom styling
    st.markdown(
        """
        <style>
            .main-header {
                font-size: 2.2rem;
                font-weight: 700;
                color: #1E3A8A;
                margin-bottom: 0.5rem;
            }
            .sub-header {
                font-size: 1rem;
                color: #64748B;
                margin-bottom: 1.5rem;
            }
            .metric-card {
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                padding: 1.2rem;
                border-radius: 12px;
                border: 1px solid #cbd5e1;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="main-header">🏨 Dashboard Quản lý Khách sạn & Đặt phòng</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Hệ thống phân tích dữ liệu phân tán trên nền tảng Apache Cassandra</div>', unsafe_allow_html=True)

    try:
        service = get_service()
        hotels = service.list_hotels()
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối Cassandra: {e}")
        st.info("Vui lòng đảm bảo Cassandra đang chạy trên localhost:9042 và đã khởi tạo keyspace.")
        st.stop()

    if not hotels:
        st.warning("⚠️ Chưa có dữ liệu khách sạn trong hệ thống.")
        st.info("Hãy chạy kịch bản khởi tạo dữ liệu: `python seed_db.py` rồi nhấn làm mới.")
        st.stop()

    # ==================== SIDEBAR: BỘ LỌC ====================
    st.sidebar.image("https://img.icons8.com/isometric/100/hotel-check-in.png", width=70)
    st.sidebar.markdown("## ⚙️ Bộ lọc & Tùy chọn")

    hotel_options = {f"{h['name']} ({h['city']})": h["hotel_id"] for h in hotels}
    hotel_label = st.sidebar.selectbox("🏨 Chọn khách sạn:", list(hotel_options.keys()))
    hotel_id = hotel_options[hotel_label]

    # Lấy thông tin khách sạn đang chọn
    current_hotel = next((h for h in hotels if h["hotel_id"] == hotel_id), None)
    if current_hotel:
        st.sidebar.caption(
            f"📍 **Địa chỉ**: {current_hotel.get('address', '')}\n\n"
            f"⭐ **Đánh giá**: {current_hotel.get('rating', 0.0)}/5 | 📞 **SĐT**: {current_hotel.get('phone', '')}"
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 Thời gian phân tích")
    target_date = st.sidebar.date_input("Xem tình trạng phòng ngày:", value=date(2026, 1, 8))
    
    col_y, col_m = st.sidebar.columns(2)
    with col_y:
        year = st.number_input("Năm:", value=2026, min_value=2020, max_value=2030, step=1)
    with col_m:
        month = st.number_input("Tháng:", value=1, min_value=1, max_value=12, step=1)

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Làm mới dữ liệu", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

    # ==================== TÍNH TOÁN DỮ LIỆU ====================
    with st.spinner("Đang tính toán chỉ số từ Cassandra..."):
        occ_today = service.room_occupancy_on_date(hotel_id, target_date)

        first_day = date(int(year), int(month), 1)
        last_day_num = calendar.monthrange(int(year), int(month))[1]
        to_date_exclusive = date(int(year), int(month), last_day_num) + timedelta(days=1)
        occ_rate = service.occupancy_rate(hotel_id, first_day, to_date_exclusive)
        rev_month = service.revenue_by_month(hotel_id, int(year), int(month))

    # ==================== HÀNG 1: 4 CHỈ SỐ KPI CHÍNH ====================
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            label="Tổng số phòng",
            value=f"{occ_today['total_rooms']} phòng",
            help="Tổng số phòng thuộc khách sạn hiện tại"
        )
    with c2:
        st.metric(
            label=f"Phòng trống ({target_date.strftime('%d/%m/%Y')})",
            value=f"{occ_today['available']} phòng",
            delta=f"-{occ_today['occupied']} đã đặt" if occ_today['occupied'] > 0 else "Trống hoàn toàn",
            delta_color="normal" if occ_today['available'] > 0 else "inverse"
        )
    with c3:
        st.metric(
            label=f"Tỉ lệ lấp đầy (T{month}/{year})",
            value=f"{occ_rate}%",
            delta=f"{occ_rate}% tổng đêm-phòng",
            help="Tỉ lệ phòng có khách / Tổng số phòng có thể phục vụ trong tháng"
        )
    with c4:
        st.metric(
            label=f"Doanh thu (T{month}/{year})",
            value=f"{rev_month['total_revenue']:,.0f} đ",
            delta=f"{rev_month['total_bookings']} lượt booking",
            help="Tổng doanh thu từ các lượt check-in trong tháng"
        )

    st.markdown("---")

    # ==================== TABS NỘI DUNG ====================
    tab1, tab2, tab3 = st.tabs(["📊 Thống kê & Biểu đồ", "🛏️ Chi tiết phòng & Tình trạng", "📋 Danh sách phòng KS"])

    with tab1:
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader(f"📌 Tình trạng phòng ngày {target_date.strftime('%d/%m/%Y')}")
            df_status = pd.DataFrame(
                {
                    "Trạng thái": ["Đang có khách (Occupied)", "Còn trống (Available)"],
                    "Số lượng": [occ_today["occupied"], occ_today["available"]]
                }
            ).set_index("Trạng thái")
            st.bar_chart(df_status, color="#3B82F6")
            st.caption(
                "💡 **Nguyên lý:** Tính trực tiếp từ dữ liệu booking thực tế (check_in_date ≤ ngày < check_out_date), "
                "đảm bảo tính chính xác theo thời gian thực mà không phụ thuộc vào trạng thái tĩnh."
            )

        with col_right:
            st.subheader(f"📈 Doanh thu theo ngày — Tháng {month}/{year}")
            df_daily = pd.DataFrame(rev_month["daily"])
            if not df_daily.empty and df_daily["revenue"].sum() > 0:
                df_daily_chart = df_daily.copy()
                df_daily_chart["date_str"] = df_daily_chart["date"].apply(lambda d: d.strftime("%d/%m"))
                df_daily_chart = df_daily_chart.set_index("date_str")[["revenue"]]
                st.bar_chart(df_daily_chart, color="#10B981")
            else:
                st.info(f"Chưa có phát sinh doanh thu nào trong tháng {month}/{year}. Bạn có thể đổi sang Tháng 1/2026 để xem dữ liệu mẫu.")

    with tab2:
        st.subheader("📋 Phân bổ trạng thái phòng hiện tại (Status Snapshot)")
        status_summary, total_rooms = service.room_status_summary(hotel_id)
        
        col_st1, col_st2 = st.columns([1, 2])
        with col_st1:
            df_snap = pd.DataFrame(
                list(status_summary.items()),
                columns=["Trạng thái", "Số lượng"]
            )
            st.dataframe(df_snap, use_container_width=True, hide_index=True)
        with col_st2:
            st.caption(
                "Field `status` lưu tại bảng `rooms_by_hotel` đại diện cho trạng thái vận hành tức thời "
                "(Ví dụ: AVAILABLE, OCCUPIED, MAINTENANCE, CLEANING) do lễ tân/quản lý cập nhật."
            )

        if occ_today["occupied_details"]:
            st.markdown(f"#### 👥 Danh sách phòng đang ở vào ngày {target_date.strftime('%d/%m/%Y')}")
            df_occ_details = pd.DataFrame(occ_today["occupied_details"])
            st.dataframe(df_occ_details, use_container_width=True)
        else:
            st.info(f"Không có lượt khách nào đang lưu trú vào ngày {target_date.strftime('%d/%m/%Y')}.")

    with tab3:
        st.subheader(f"🏨 Toàn bộ danh sách phòng của {hotel_label}")
        rooms = service.get_hotel_rooms(hotel_id)
        if rooms:
            df_rooms = pd.DataFrame(rooms)
            display_cols = [c for c in ["room_number", "room_type", "price", "status", "room_id"] if c in df_rooms.columns]
            st.dataframe(df_rooms[display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có phòng nào được tạo cho khách sạn này.")


if __name__ == "__main__":
    render_dashboard()
