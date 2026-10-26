import json
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
# 3. 출력 (Output) 단계: 대시보드 및 현황 카드
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
# 4. HTML5 Canvas 기반 60FPS 자동차 매끄러운 2D 애니메이션 Component
# =============================================================================
st.subheader("🎬 2D 커브길 주행 시뮬레이션")

# JS 전달용 데이터 팩
sim_params = {
    "is_safe": bool(is_safe),
    "radius": int(radius),
    "user_speed": int(user_speed_kmh),
    "max_speed": float(v_max_kmh)
}

canvas_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        margin: 0;
        padding: 0;
        background-color: #0e1117;
        font-family: 'Segoe UI', sans-serif;
        color: #ffffff;
        display: flex;
        flex-direction: column;
        align-items: center;
    }}
    #controls {{
        margin-bottom: 12px;
        display: flex;
        gap: 15px;
    }}
    .btn {{
        background-color: #ff4b4b;
        color: white;
        border: none;
        padding: 10px 24px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        transition: background 0.2s;
    }}
    .btn:hover {{
        background-color: #d33838;
    }}
    canvas {{
        background: #1e222b;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }}
</style>
</head>
<body>

<div id="controls">
    <button class="btn" onclick="startSimulation()">▶️ 시뮬레이션 시작</button>
</div>
<canvas id="simCanvas" width="800" height="420"></canvas>

<script>
const config = {json.dumps(sim_params)};
const canvas = document.getElementById("simCanvas");
const ctx = canvas.getContext("2d");

let animId = null;
let progress = 0;
let isAnimating = false;

// 트랙 매개변수 설정
const centerX = 150;
const centerY = 370;
const trackR = 240; // 화면 맞춤형 고정 반지름 비율

function drawScene(carProgress) {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 1. 아스팔트 커브 도로 그리기
    ctx.beginPath();
    ctx.arc(centerX, centerY, trackR, -Math.PI / 2, 0, false);
    ctx.lineWidth = 60;
    ctx.strokeStyle = "#343a40";
    ctx.stroke();

    // 2. 도로 중앙선 (황색 점선)
    ctx.beginPath();
    ctx.arc(centerX, centerY, trackR, -Math.PI / 2, 0, false);
    ctx.lineWidth = 3;
    ctx.setLineDash([12, 10]);
    ctx.strokeStyle = "#f1c40f";
    ctx.stroke();
    ctx.setLineDash([]); // 원복

    // 3. 자동차 위치 및 회전 각도 수치 계산
    let carX, carY, carAngle;
    let isSlipped = false;
    const slipPoint = 0.5; // 커브 중간 지점에서 슬립 발생

    if (config.is_safe || carProgress <= slipPoint) {{
        // 정상 궤적 (원형 가속)
        const angle = -Math.PI / 2 + (Math.PI / 2) * carProgress;
        carX = centerX + trackR * Math.cos(angle);
        carY = centerY + trackR * Math.sin(angle);
        carAngle = angle + Math.PI / 2; // 진행 방향 접선 각도
    }} else {{
        // 원심력 이탈 궤적 (접선 직선 진행)
        isSlipped = true;
        const angle = -Math.PI / 2 + (Math.PI / 2) * slipPoint;
        const startX = centerX + trackR * Math.cos(angle);
        const startY = centerY + trackR * Math.sin(angle);
        const tangentAngle = angle + Math.PI / 2;

        const over = (carProgress - slipPoint) * 350;
        carX = startX + Math.cos(tangentAngle) * over;
        carY = startY + Math.sin(tangentAngle) * over;
        carAngle = tangentAngle;
    }}

    // 4. 자동차 그래픽 랜더링 (차량 형상 직접 그리기)
    ctx.save();
    ctx.translate(carX, carY);
    ctx.rotate(carAngle);

    // 차체 그리기 (세단 스타일)
    const carWidth = 42;
    const carHeight = 22;

    // 바퀴 4개
    ctx.fillStyle = "#111";
    ctx.fillRect(-carWidth/2 + 6, -carHeight/2 - 3, 10, 4);
    ctx.fillRect(carWidth/2 - 16, -carHeight/2 - 3, 10, 4);
    ctx.fillRect(-carWidth/2 + 6, carHeight/2 - 1, 10, 4);
    ctx.fillRect(carWidth/2 - 16, carHeight/2 - 1, 10, 4);

    // 차체 보디 (안전: 초록/파랑, 슬립: 빨강)
    ctx.fillStyle = isSlipped ? "#e74c3c" : "#2ecc71";
    ctx.beginPath();
    ctx.roundRect(-carWidth/2, -carHeight/2, carWidth, carHeight, 6);
    ctx.fill();

    // 차량 유리창 (Front/Rear Windshield)
    ctx.fillStyle = "#2c3e50";
    ctx.beginPath();
    ctx.roundRect(-carWidth/6, -carHeight/2 + 3, carWidth/3, carHeight - 6, 3);
    ctx.fill();

    // 헤드라이트 (진행 방향)
    ctx.fillStyle = "#f39c12";
    ctx.fillRect(carWidth/2 - 2, -carHeight/2 + 3, 3, 4);
    ctx.fillRect(carWidth/2 - 2, carHeight/2 - 7, 3, 4);

    ctx.restore();

    // 5. 상태 안내 텍스트 표시
    ctx.font = "bold 16px 'Segoe UI', sans-serif";
    if (isSlipped) {{
        ctx.fillStyle = "#e74c3c";
        ctx.fillText("💥 원심력으로 도로 이탈 발생!", 20, 40);
    }} else if (carProgress > 0) {{
        ctx.fillStyle = "#2ecc71";
        ctx.fillText("🏎️ 안전하게 코너링 중", 20, 40);
    }} else {{
        ctx.fillStyle = "#aaaaaa";
        ctx.fillText("🏎️ 시뮬레이션 대기 중", 20, 40);
    }}
}}

function animate() {{
    if (!isAnimating) return;
    
    // 주행 속도에 비례한 애니메이션 속도 제어
    const speedFactor = 0.003 + (config.user_speed / 150) * 0.008;
    progress += speedFactor;

    if (progress > 1.2) {{
        isAnimating = false;
        return;
    }}

    drawScene(Math.min(progress, 1.2));
    animId = requestAnimationFrame(animate);
}}

function startSimulation() {{
    if (animId) cancelAnimationFrame(animId);
    progress = 0;
    isAnimating = true;
    animate();
}}

// 초기 화면 렌더링
drawScene(0);
</script>
</body>
</html>
"""

components.html(canvas_html, height=480)

st.markdown("---")

# =============================================================================
# 5. 도로 조건별 안전 속도 비교 차트
# =============================================================================
st.subheader("📊 곡선 반경(r)에 따른 노면 상태별 안전 속도 비교")

r_range = np.linspace(10, 200, 100)
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
