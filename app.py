import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="ระดับน้ำคลองระพีพัฒน์",
    page_icon="🌊",
    layout="wide"
)

# --- Station Definitions & Thresholds (m MSL / ม.รทก.) ---
STATIONS = {
    "ประตูระบายน้ำพระศรีเสาวภาคย์ (ตอนบน)": {
        "warning_level": 4.20,
        "danger_level": 4.80,
        "bank_level": 5.00,
        "base_level": 3.40
    },
    "ประตูระบายน้ำพระอินทร์ราชา (ตอนล่าง)": {
        "warning_level": 3.80,
        "danger_level": 4.30,
        "bank_level": 4.60,
        "base_level": 2.90
    },
    "คลองระพีพัฒน์แยกตก (คลองหนึ่ง)": {
        "warning_level": 3.50,
        "danger_level": 4.00,
        "bank_level": 4.30,
        "base_level": 2.65
    }
}

# --- Data Simulation / Fetch Function ---
@st.cache_data(ttl=300)  # Refresh cache every 5 minutes
def load_water_data(station_name: str):
    """
    Fetch water level data. Currently mocked with realistic sinusoidal variation.
    Replace this block with requests.get() to NHC/Thaiwater or RID API when ready.
    """
    config = STATIONS[station_name]
    now = datetime.now()
    
    # Generate 24-hour historical records (hourly)
    times = [now - timedelta(hours=i) for i in reversed(range(24))]
    
    # Simulated readings fluctuating around the station's base level
    noise = np.sin(np.linspace(0, 3, 24)) * 0.3 + np.random.normal(0, 0.05, 24)
    readings = np.round(config["base_level"] + noise, 2)
    
    df = pd.DataFrame({
        "timestamp": times,
        "level": readings
    })
    return df

# --- UI Header ---
st.title("🌊 ระบบติดตามระดับน้ำ คลองระพีพัฒน์")
st.caption(f"อัปเดตข้อมูลอัตโนมัติ | เวลาปัจจุบัน: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# --- Station Selector ---
selected_station = st.selectbox(
    "เลือกสถานีตรวจวัด:",
    options=list(STATIONS.keys()),
    index=0
)

station_info = STATIONS[selected_station]
df_data = load_water_data(selected_station)

current_level = float(df_data["level"].iloc[-1])
previous_level = float(df_data["level"].iloc[-2])
level_delta = round(current_level - previous_level, 2)

# --- Status Evaluation ---
if current_level >= station_info["danger_level"]:
    status_text = "🚨 วิกฤต (ล้นตลิ่ง/อันตราย)"
    status_alert = st.error
elif current_level >= station_info["warning_level"]:
    status_text = "⚠️ เฝ้าระวัง (ระดับน้ำสูง)"
    status_alert = st.warning
else:
    status_text = "✅ สภาวะปกติ"
    status_alert = st.success

status_alert(f"**สถานะปัจจุบัน:** {status_text}")

# --- Metrics Row ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="ระดับน้ำปัจจุบัน",
        value=f"{current_level:.2f} ม.รทก.",
        delta=f"{level_delta:+.2f} ม. (1 ชม.)"
    )

with col2:
    st.metric(
        label="ระดับเตือนภัย (Warning)",
        value=f"{station_info['warning_level']:.2f} ม.รทก."
    )

with col3:
    st.metric(
        label="ระดับวิกฤต (Danger)",
        value=f"{station_info['danger_level']:.2f} ม.รทก."
    )

with col4:
    diff_to_danger = station_info["danger_level"] - current_level
    st.metric(
        label="ระยะห่างจากขีดวิกฤต",
        value=f"{diff_to_danger:.2f} ม.",
        delta_color="inverse"
    )

# --- 24-Hour Trend Chart (Plotly) ---
st.subheader("📈 แนวโน้มระดับน้ำย้อนหลัง 24 ชั่วโมง")

fig = go.Figure()

# Actual readings line
fig.add_trace(go.Scatter(
    x=df_data["timestamp"],
    y=df_data["level"],
    mode="lines+markers",
    name="ระดับน้ำ (ม.รทก.)",
    line=dict(color="#0284c7", width=3),
    marker=dict(size=6)
))

# Danger Threshold Line
fig.add_hline(
    y=station_info["danger_level"],
    line_dash="dash",
    line_color="#dc2626",
    annotation_text="ระดับวิกฤต",
    annotation_position="top left"
)

# Warning Threshold Line
fig.add_hline(
    y=station_info["warning_level"],
    line_dash="dot",
    line_color="#eab308",
    annotation_text="ระดับเฝ้าระวัง",
    annotation_position="bottom left"
)

fig.update_layout(
    xaxis_title="เวลา",
    yaxis_title="ระดับน้ำ (ม.รทก.)",
    hovermode="x unified",
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# --- Raw Data Table ---
with st.expander("🔍 ดูตารางข้อมูลดิบย้อนหลัง"):
    display_df = df_data.sort_values(by="timestamp", ascending=False).copy()
    display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    display_df.columns = ["วัน-เวลา", "ระดับน้ำ (ม.รทก.)"]
    st.dataframe(display_df, use_container_width=True)
