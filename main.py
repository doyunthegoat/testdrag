import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# 0. Streamlit 페이지 설정
# =============================================================================
st.set_page_config(
    page_title="빗길·빙판길 커브길 안전 속도 시뮬레이터",
    page_icon="🌧️",
    layout="wide"
)

st.title("🌧️ 빗길·빙판길 커브길 주행 시뮬레이터")
st.caption("2D 애니메이션으로 보는 노면 상태 및 곡선 반경별 자동차 이탈 시뮬레이션")

st.markdown("---")

# =============================================================================
# 1. 입력 (Input) 단계: 사이드바 사용자 제어 환경
# =============================================================================
st.sidebar.header("⚙️ 도로 및 주행 환경 설정")

# 1-1. 날씨 및 노면 상태 선택
weather_option = st.sidebar.selectbox(
    "1. 날씨 및 노면 상태 선택",
    ["맑음 (건조한 노면, μ=0.8)", "비 (젖은 노면, μ=0.4)", "눈/빙판길 (μ=0.1)"]
)

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
    max_value=200,
    value=60,
    step=10,
    help="도로가 굽은 정도입니다. (20~50m: 급커브, 100m 이상: 완만한 커브)"
)

# 1-3. 차량 진입 속도 (v) 설정
user_speed_kmh = st.sidebar.slider(
    "3. 차량 진입 속도 (km/h)",
    min_value=20,
    max_value=150,
    value=70,
    step=5
)

# =============================================================================
# 2. 처리 (Processing) 단계: 물리학 공식 기반 제어 엔진
# =============================================================================
G = 9.8  # 중력가속도 (m/s²)

# 한계 안전 속도 v_max = √(μ · g · r) (km/h 단위 변환)
v_max_ms = np.sqrt(mu * G * radius)
v_max_kmh = float(v_max_ms * 3.6)

speed_diff = user_speed_kmh - v_max_kmh
is_safe = user_speed_kmh <= v_max_kmh

# =============================================================================
# 3. 출력 (Output) 단계: 대시보드 및 직관적 현황 카드
# =============================================================================
col1, col2, col3 = st.columns(3)

col1.metric("노면 마찰계수 (μ)", f"{mu}")
col2.metric("이 도로의 한계 안전 속도", f"{v_max_kmh:.1f} km/h")

if is_safe:
    col3.metric("주행 상태", "✅ 안전 코너링", f"{abs(speed_diff):.1f} km/h 여유", delta_color="normal")
    st.success(f"**[안전]** 진입 속도({user_speed_kmh} km/h)가 한계 속도({v_max_kmh:.1f} km/h) 이하입니다. 자동차가 도로를 벗어나지 않고 안전하게 회전합니다.")
else:
    col3.metric("주행 상태", "⚠️ 도로 이탈 (슬립)", f"{speed_diff:.1f} km/h 초과", delta_color="inverse")
    st.error(f"**[위험]** 진입 속도({user_speed_kmh} km/h)가 한계 속도({v_max_kmh:.1f} km/h)를 초과했습니다! 원심력이 마찰력보다 커서 차량이 바깥으로 튕겨 나갑니다.")

st.markdown("---")

# =============================================================================
# 4. 2D 주행 애니메이션 시각화 (Plotly Animation Frames)
# =============================================================================
st.subheader("🎬 2D 커브길 주행 애니메이션 시뮬레이션")
st.caption("아래 플레이 버튼(▶)을 누르면 차량의 움직임을 시뮬레이션할 수 있습니다.")

# 4-1. 도로 궤적 데이터 (90도 곡선)
theta = np.linspace(0, np.pi / 2, 60)
x_road = radius * np.cos(theta)
y_road = radius * np.sin(theta)

# 4-2. 애니메이션 프레임 생성
frames = []
total_steps = 40

# 이탈이 발생하는 위치 (커브 중간 지점 45도 부근)
slip_step = int(total_steps * 0.45)

for i in range(total_steps + 1):
    if is_safe or i <= slip_step:
        # 정상 주행 구간: 원형 궤적을 따라 이동
        angle = (np.pi / 2) * (i / total_steps)
        curr_x = radius * np.cos(angle)
        curr_y = radius * np.sin(angle)
        car_color = "#2ECC71"  # 초록색
        status_text = "🏎️ 안전 주행 중"
    else:
        # 이탈(슬립) 발생 구간: 이탈 시점에서의 접선 방향(원심력 방향)으로 직선 이동
        slip_angle = (np.pi / 2) * (slip_step / total_steps)
        start_x = radius * np.cos(slip_angle)
        start_y = radius * np.sin(slip_angle)
        
        # 접선 방향 벡터
        dx = -np.sin(slip_angle)
        dy = np.cos(slip_angle)
        
        over_step = i - slip_step
        curr_x = start_x + dx * (radius * 0.04 * over_step)
        curr_y = start_y + dy * (radius * 0.04 * over_step)
        car_color = "#E74C3C"  # 빨간색
        status_text = "💥 원심력으로 이탈 중!"

    # 각 프레임 데이터 추가
    frames.append(go.Frame(
        data=[
            go.Scatter(
                x=[curr_x],
                y=[curr_y],
                mode='markers+text',
                marker=dict(size=24, color=car_color, symbol='square'),
                text=[status_text],
                textposition="top right"
            )
        ],
        name=f"frame_{i}"
    ))

# 4-3. 기본 메인 피규어 생성 (초기 상태)
fig = go.Figure(
    data=[
        # 도로 중앙선
        go.Scatter(
            x=x_road, y=y_road,
            mode='lines',
            line=dict(color='gray', width=8, dash='dash'),
            name='도로 중앙선'
        ),
        # 초기 차량 위치 (출발점)
        go.Scatter(
            x=[x_road[0]], y=[y_road[0]],
            mode='markers+text',
            marker=dict(size=24, color="#2ECC71", symbol='square'),
            text=["🏎️ 대기 중"],
            textposition="top right",
            name='차량'
        )
    ],
    layout=go.Layout(
        xaxis=dict(title="X 좌표 (m)", range=[-15, radius + 40], zeroline=False),
        yaxis=dict(title="Y 좌표 (m)", range=[-15, radius + 40], zeroline=False),
        height=520,
        margin=dict(l=20, r=20, t=30, b=3
