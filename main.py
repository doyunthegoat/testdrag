import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 타이틀
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="1/4마일 드래그 레이스 시뮬레이터",
    page_icon="🏎️",
    layout="wide"
)

st.title("🏎️ 1/4마일(400m) 드래그 레이스 시뮬레이터")
st.caption("물리학I 등가속도 운동 공식(F=ma, s=1/2*a*t²) 및 뉴턴 운동 법칙을 활용한 가속 성능 시뮬레이션")

st.markdown("---")

# -----------------------------------------------------------------------------
# 2. 사이드바 - 차량 파라미터 입력 (사용자 컨트롤)
# -----------------------------------------------------------------------------
st.sidebar.header("🔴 CAR A (레드)")
hp_a = st.sidebar.slider("출력 (마력, hp)", 100, 1000, 200, step=10, key="hp_a")
weight_a = st.sidebar.slider("공차중량 (kg)", 800, 2500, 1400, step=50, key="w_a")

st.sidebar.markdown("---")

st.sidebar.header("🔵 CAR B (블루)")
hp_b = st.sidebar.slider("출력 (마력, hp)", 100, 1000, 500, step=10, key="hp_b")
weight_b = st.sidebar.slider("공차중량 (kg)", 800, 2500, 1800, step=50, key="w_b")

# -----------------------------------------------------------------------------
# 3. 물리학 기반 성능 계산 로직
# -----------------------------------------------------------------------------
# 1 마력(hp) = 745.7 W
# 마력 대 중량비 기반 가속도(m/s²) 계수 산출
acc_a = (hp_a * 745.7) / (weight_a * 15.0)
acc_b = (hp_b * 745.7) / (weight_b * 15.0)

# 제로백 (0 -> 100km/h = 27.78m/s) 도달 시간: t = v / a
zero100_a = 27.78 / acc_a
zero100_b = 27.78 / acc_b

# 400m 도달 시간 계산: s = 0.5 * a * t²  =>  t = √(2s / a)
t_400_a = np.sqrt(2 * 400 / acc_a)
t_400_b = np.sqrt(2 * 400 / acc_b)

# 400m 지점 통과 시 속도 (km/h): v = a * t
v_400_a = acc_a * t_400_a * 3.6
v_400_b = acc_b * t_400_b * 3.6

# 마력 대 중량비 (hp/ton)
p2w_a = (hp_a / weight_a) * 1000
p2w_b = (hp_b / weight_b) * 1000

# -----------------------------------------------------------------------------
# 4. 주요 성능 지표(Metric) 출력
# -----------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("🔴 CAR A 제로백", f"{zero100_a:.2f} 초", f"{p2w_a:.1f} hp/ton")
col2.metric("🔴 CAR A 400m 기록", f"{t_400_a:.2f} 초", f"통과속도 {v_400_a:.1f} km/h")

diff_zero100 = zero100_a - zero100_b
diff_t400 = t_400_a - t_400_b

col3.metric(
    "🔵 CAR B 제로백", 
    f"{zero100_b:.2f} 초", 
    f"{diff_zero100:+.2f}s (A 대비)",
    delta_color="inverse"
)
col4.metric(
    "🔵 CAR B 400m 기록", 
    f"{t_400_b:.2f} 초", 
    f"{diff_t400:+.2f}s (A 대비)",
    delta_color="inverse"
)

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. 실시간 트랙 애니메이션 시각화
# -----------------------------------------------------------------------------
st.subheader("🏁 400m 드래그 레이스 실시간 트랙")

race_button = st.button("🚀 RACE START !", use_container_width=True)
track_place = st.empty()

max_time = max(t_400_a, t_400_b)

def draw_track(pos_a, pos_b):
    """트랙 위 두 차량의 위치를 그려주는 함수"""
    fig = go.Figure()

    # CAR A (레드)
    fig.add_trace(go.Scatter(
        x=[pos_a], y=[1],
        mode='markers+text',
        marker=dict(size=26, color='#FF4B4B', symbol='square'),
        text=["🏎️ CAR A"], textposition="top center",
        name="CAR A"
    ))

    # CAR B (블루)
    fig.add_trace(go.Scatter(
        x=[pos_b], y=[0],
        mode='markers+text',
        marker=dict(size=26, color='#1C83E1', symbol='square'),
        text=["🚙 CAR B"], textposition="top center",
        name="CAR B"
    ))

    # 트랙 레이아웃 설정
    fig.update_layout(
        xaxis=dict(range=[-15, 430], title="이동 거리 (m)"),
        yaxis=dict(range=[-0.6, 1.6], showticklabels=False),
        height=280,
        margin=dict(l=20, r=20, t=30, b=30),
        showlegend=False,
        shapes=[
            # 출발선
            dict(type="line", x0=0, y0=-0.5, x1=0, y1=1.5, line=dict(color="gray", width=2)),
            # 결승선
