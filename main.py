import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# 0. Streamlit 페이지 설정
# =============================================================================
st.set_page_config(
    page_title="빗길·빙판길 커브길 안전 속도 안내기",
    page_icon="🌧️",
    layout="wide"
)

# 타이틀 및 개요
st.title("🌧️ 도로 상태 & 커브 곡선 반경별 안전 속도 안내기")
st.caption("물리학I 원운동의 구심력(F = m·v²/r)과 마찰력(F = μ·m·g) 원리를 활용한 실생활 교통안전 솔루션")

st.markdown("---")

# =============================================================================
# 1. 입력 (Input) 단계: 사이드바 사용자 제어 환경
# =============================================================================
st.sidebar.header("⚙️ 도로 및 주행 환경 설정")

# 1-1. 날씨 및 노면 상태 선택 (마찰계수 μ 결정)
weather_option = st.sidebar.selectbox(
    "1. 날씨 및 노면 상태 선택",
    ["맑음 (건조한 노면, μ=0.8)", "비 (젖은 노면, μ=0.4)", "눈/빙판길 (μ=0.1)"]
)

# 선택된 노면에 따른 마찰계수(μ) 매핑
if "맑음" in weather_option:
    mu = 0.8
elif "비" in weather_option:
    mu = 0.4
else:
    mu = 0.1

# 1-2. 곡선 반경 (r) 설정
radius = st.sidebar.slider(
    "2. 곡선 반경 r (m)",
    min_value=20,
    max_value=300,
    value=60,
    step=10,
    help="도로가 굽은 정도입니다. (20~50m: 급커브, 150m 이상: 완만한 커브)"
)

# 1-3. 차량 진입 속도 (v) 설정
user_speed_kmh = st.sidebar.slider(
    "3. 차량 진입 속도 (km/h)",
    min_value=10,
    max_value=150,
    value=60,
    step=5
)

# =============================================================================
# 2. 처리 (Processing) 단계: 물리학 공식 기반 제어 엔진
# =============================================================================
# 중력가속도 g (m/s²)
G = 9.8

# 2-1. 한계 안전 속도 계산: v_max = √(μ · g · r)  [m/s -> km/h 변환]
v_max_ms = np.sqrt(mu * G * radius)
v_max_kmh = float(v_max_ms * 3.6)

# 2-2. 속도 차이 계산 (사용자 진입 속도 - 한계 속도)
speed_diff = user_speed_kmh - v_max_kmh
is_safe = user_speed_kmh <= v_max_kmh

# =============================================================================
# 3. 출력 (Output) 단계: 대시보드, 경고 메시지, 2D 트랙, 분석 차트
# =============================================================================

# 3-1. 핵심 지표 카드로 현황 표시 (Metric Dashboard)
col1, col2, col3 = st.columns(3)

col1.metric(
    label="노면 마찰계수 (μ)",
    value=f"{mu}"
)

col2.metric(
    label="이 도로의 한계 안전 속도",
    value=f"{v_max_kmh:.1f} km/h"
)

if is_safe:
    col3.metric(
        label="주행 안전성 판정",
        value="✅ 안전 주행",
        delta=f"{abs(speed_diff):.1f} km/h 여유",
        delta_color="normal"
    )
else:
    col3.metric(
        label="주행 안전성 판정",
        value="⚠️ 이탈/슬립 위험!",
        delta=f"{speed_diff:.1f} km/h 초과",
        delta_color="inverse"
    )

# 3-2. 위험 판정 메시지 박스
if is_safe:
    st.success(
        f"**[안전]** 진입 속도({user_speed_kmh} km/h)가 한계 속도({v_max_kmh:.1f} km/h) 이하입니다. "
        "타이어의 마찰력이 원심력을 충분히 지탱하여 안전하게 코너를 통과합니다."
    )
else:
    st.error(
        f"**[경고]** 진입 속도({user_speed_kmh} km/h)가 한계 속도({v_max_kmh:.1f} km/h)를 초과했습니다! "
        "원심력이 최대 마찰력보다 커서 바깥쪽으로 미끄러질(슬립) 위험이 큽니다. 속도를 줄이세요."
    )

st.markdown("---")

# 3-3. 2D 커브길 주행 궤적 인터랙티브 시각화 (Plotly)
st.subheader("🔄 곡선 반경 및 차량 주행 궤적 시각화")

# 90도 곡선 도로 궤적 좌표 생성 (x = r*cos, y = r*sin)
theta = np.linspace(0, np.pi / 2, 100)
x_road = radius * np.cos(theta)
y_road = radius * np.sin(theta)

fig = go.Figure()

# ① 중앙선 도로 그리기
fig.add_trace(go.Scatter(
    x=x_road,
    y=y_road,
    mode='lines',
    line=dict(color='gray', width=6, dash='dash'),
    name='도로 중앙선'
))

# ② 차량 위치 설정 (커브 45도 지점)
car_angle = np.pi / 4
car_x = radius * np.cos(car_angle)
car_y = radius * np.sin(car_angle)

# ③ 속도 초과 여부에 따른 궤적 분기 처리
if is_safe:
    # 정상 주행 궤적 (초록색 점)
    fig.add_trace(go.Scatter(
        x=[car_x],
        y=[car_y],
        mode='markers+text',
        marker=dict(size=22, color='#2ECC71'),
        text=["🏎️ 정상 코너링"],
        textposition="top right",
        name='차량 위치'
    ))
else:
    # 이탈 궤적 (접선 방향 벡터 산출)
    tangent_x = car_x + (radius * 0.3) * (-np.sin(car_angle))
    tangent_y = car_y + (radius * 0.3) * (np.cos(car_angle))

    fig.add_trace(go.Scatter(
        x=[car_x, tangent_x],
        y=[car_y, tangent_y],
        mode='lines+markers+text',
        line=dict(color='#E74C3C', width=3, dash='dot'),
        marker=dict(size=[22, 12], color='#E74C3C'),
        text=["🏎️ 미끄러짐 발생", "💥 원심력 이탈"],
        textposition=["top left", "top right"],
        name='이탈 궤적'
    ))

fig.update_layout(
    xaxis=dict(title="X 좌표 (m)", range=[-10, radius + 40]),
    yaxis=dict(title="Y 좌표 (m)", range=[-10, radius + 40]),
    height=480,
    showlegend=False,
    margin=dict(l=20, r=20, t=30, b=30)
)

st.plotly_chart(fig, use_container_width=True)

# 3-4. 곡선 반경 및 노면별 안전 속도 비교 차트
st.subheader("📊 곡선 반경(r)에 따른 노면 상태별 한계 속도 비교")

r_range = np.linspace(10, 300, 100)
v_dry = np.sqrt(0.8 * G * r_range) * 3.6
v_wet = np.sqrt(0.4 * G * r_range) * 3.6
v_ice = np.sqrt(0.1 * G * r_range) * 3.6

df_chart = pd.DataFrame({
    "곡선 반경 r (m)": r_range,
    "맑음 (μ=0.8)": v_dry,
    "비 (μ=0.4)": v_wet,
    "눈/빙판 (μ=0.1)": v_ice
}).set_index("곡선 반경 r (m)")

st.line_chart(df_chart)
