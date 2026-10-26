import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="Drag Race Simulator", page_icon="🏎️", layout="wide")

st.title("🏎️ 1/4마일(400m) 드래그 레이스 시뮬레이터")
st.caption("물리학I 등가속도 운동 공식(F=ma, s=1/2*a*t^2)을 이용한 가속 성능 비교")

st.markdown("---")

# 2. 사이드바 - 두 차량의 제원 설정 (사용자 입력)
st.sidebar.header("🚗 CAR A (레드)")
hp_a = st.sidebar.slider("출력 (마력, hp)", 100, 1000, 200, step=10, key="hp_a")
weight_a = st.sidebar.slider("공차중량 (kg)", 800, 2500, 1500, step=50, key="w_a")

st.sidebar.markdown("---")

st.sidebar.header("🚙 CAR B (블루)")
hp_b = st.sidebar.slider("출력 (마력, hp)", 100, 1000, 500, step=10, key="hp_b")
weight_b = st.sidebar.slider("공차중량 (kg)", 800, 2500, 1800, step=50, key="w_b")

# 3. 물리 계산 로직 (물리학I 수준)
# 1 마력(hp) ≈ 745.7 Watt (J/s)
# 단순화된 평균 가속도 계산: F_avg = Power / v_avg (또는 마력 대비 중량비 기준 물리 모델 적용)
# 고교 수준 가속도 간이 모델: a = (Power_kW * 1000) / (m * target_v_avg)
# 여기서는 직관적 이해를 위해 '마력/중량 비율' 기반 평균 가속도(m/s^2)를 산출합니다.

acc_a = (hp_a * 745.7) / (weight_a * 15.0)  # Car A 평균 가속도 (m/s^2)
acc_b = (hp_b * 745.7) / (weight_b * 15.0)  # Car B 평균 가속도 (m/s^2)

# 제로백 (0 -> 100km/h = 27.78m/s) 계산: t = v / a
zero100_a = 27.78 / acc_a
zero100_b = 27.78 / acc_b

# 400m 도달 시간 계산: s = 0.5 * a * t^2  =>  t = sqrt(2s / a)
t_400_a = np.sqrt(2 * 400 / acc_a)
t_400_b = np.sqrt(2 * 400 / acc_b)

# 4. 주요 성능 지표(Metric) 출력
col1, col2, col3, col4 = st.columns(4)

col1.metric("🔴 CAR A 제로백", f"{zero100_a:.2f} 초")
col2.metric("🔴 CAR A 400m 기록", f"{t_400_a:.2f} 초")
col3.metric("🔵 CAR B 제로백", f"{zero100_b:.2f} 초", delta=f"{zero100_a - zero100_b:.2f}s", delta_color="inverse")
col4.metric("🔵 CAR B 400m 기록", f"{t_400_b:.2f} 초", delta=f"{t_400_a - t_400_b:.2f}s", delta_color="inverse")

st.markdown("---")

# 5. 레이스 트랙 애니메이션 시각화
st.subheader("🏁 400m 드래그 레이스 실시간 트랙")

race_button = st.button("🚀 RACE START !", use_container_width=True)

track_place = st.empty()

# 레이스 시작 버튼을 누르거나 기본 상태일 때 그래프 그리기
max_time = max(t_400_a, t_400_b)

if race_button:
    # 시간 흐름에 따른 애니메이션 연출
    steps = 30
    for i in range(steps + 1):
        current_t = (max_time / steps) * i
        
        # 이동 거리 계산 (s = 0.5 * a * t^2), 단 400m 상한선
        pos_a = min(400.0, 0.5 * acc_a * (current_t ** 2))
        pos_b = min(400.0, 0.5 * acc_b * (current_t ** 2))
        
        fig = go.Figure()
        
        # CAR A (레드) 위치
        fig.add_trace(go.Scatter(
            x=[pos_a], y=[1],
            mode='markers+text',
            marker=dict(size=25, color='red', symbol='square'),
            text=["🏎️ CAR A"], textposition="top center",
            name="CAR A"
        ))
        
        # CAR B (블루) 위치
        fig.add_trace(go.Scatter(
            x=[pos_b], y=[0],
            mode='markers+text',
            marker=dict(size=25, color='blue', symbol='square'),
            text=["🚙 CAR B"], textposition="top center",
            name="CAR B"
        ))
        
        # 트랙 디자인 설정
        fig.update_layout(
            xaxis=dict(range=[-10, 430], title="거리 (미터, m)"),
            yaxis=dict(range=[-0.5, 1.5], showticklabels=False),
            height=300,
            showlegend=False,
            shapes=[
                # 결승선 라인 (400m)
                dict(type="line", x0=400, y0=-0.5, x1=400, y1=1.5, line=dict(color="black", width=4, dash="dash"))
            ]
        )
        
        track_place.plotly_chart(fig, use_container_width=True)
        time.sleep(0.05)

else:
    # 정지 상태 기본 트랙 표시
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0], y=[1], mode='markers+text', marker=dict(size=25, color='red'), text=["🏎️ CAR A"], textposition="top center"))
    fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers+text', marker=dict(size=25, color='blue'), text=["🚙 CAR B"], textposition="top center"))
    fig.update_layout(
        xaxis=dict(range=[-10, 430], title="거리 (미터, m)"),
        yaxis=dict(range=[-0.5, 1.5], showticklabels=False),
        height=300,
        showlegend=False,
        shapes=[dict(type="line", x0=400, y0=-0.5, x1=400, y1=1.5, line=dict(color="black", width=4, dash="dash"))]
    )
    track_place.plotly_chart(fig, use_container_width=True)

# 6. 속도-시간 그래프 (물리학I 핵심 그래프)
st.subheader("📈 시간에 따른 속도 변화 (v-t 그래프)")

t_vals = np.linspace(0, max_time, 100)
v_a_vals = np.minimum(acc_a * t_vals * 3.6, np.sqrt(2 * acc_a * 400) * 3.6) # km/h 변환
v_b_vals = np.minimum(acc_b * t_vals * 3.6, np.sqrt(2 * acc_b * 400) * 3.6)

df_graph = pd.DataFrame({
    "시간 (초)": t_vals,
    "CAR A 속도 (km/h)": v_a_vals,
    "CAR B 속도 (km/h)": v_b_vals
}).set_index("시간 (초)")

st.line_chart(df_graph)
