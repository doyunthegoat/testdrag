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
    col3.metric("주행 상태", "⚠️ 도로 이탈 (충돌)", f"{speed_diff:.1f} km/h 초과", delta_color="inverse")
    st.error(f"**[위험]** 진입 속도({user_speed_kmh} km/h)가 한계 속도({v_max_kmh:.1f} km/h)를 초과했습니다! 원심력에 의해 외곽 가드레일과 충돌합니다.")

st.markdown("---")

# =============================================================================
# 4. HTML5 Canvas 기반 가드레일/나무/충돌 스파크 애니메이션 Component
# =============================================================================
st.subheader("🎬 2D 커브길 주행 시뮬레이션")

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
        background: #19231a; /* 주변 잔디밭 색상 */
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }}
</style>
</head>
<body>

<div id="controls">
    <button class="btn" onclick="startSimulation()">▶️ 시뮬레이션 시작</button>
</div>
<canvas id="simCanvas" width="800" height="450"></canvas>

<script>
const config = {json.dumps(sim_params)};
const canvas = document.getElementById("simCanvas");
const ctx = canvas.getContext("2d");

let animId = null;
let progress = 0;
let isAnimating = false;
let sparks = [];

// 트랙 매개변수
const centerX = 120;
const centerY = 400;
const trackR = 250;
const roadWidth = 70;

// 고정 나무 위치 배열
const trees = [
    {{ x: 420, y: 80, r: 22 }},
    {{ x: 490, y: 150, r: 26 }},
    {{ x: 530, y: 240, r: 24 }},
    {{ x: 520, y: 340, r: 28 }},
    {{ x: 70, y: 80, r: 20 }},
    {{ x: 280, y: 300, r: 18 }}
];

// 나무 그리기
function drawTree(x, y, r) {{
    // 그림자
    ctx.fillStyle = "rgba(0,0,0,0.25)";
    ctx.beginPath();
    ctx.ellipse(x + 5, y + 5, r, r * 0.7, 0, 0, Math.PI * 2);
    ctx.fill();

    // 나뭇잎
    ctx.fillStyle = "#2d5a27";
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#3a7233";
    ctx.beginPath();
    ctx.arc(x - r*0.2, y - r*0.2, r * 0.65, 0, Math.PI * 2);
    ctx.fill();
}}

// 스파크 이펙트 관리
function createSparks(x, y) {{
    for (let i = 0; i < 8; i++) {{
        sparks.push({{
            x: x,
            y: y,
            vx: (Math.random() - 0.5) * 8,
            vy: (Math.random() - 0.5) * 8,
            life: 1.0,
            color: Math.random() > 0.5 ? "#f1c40f" : "#e67e22"
        }});
    }}
}}

function updateAndDrawSparks() {{
    for (let i = sparks.length - 1; i >= 0; i--) {{
        let p = sparks[i];
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.05;

        if (p.life <= 0) {{
            sparks.splice(i, 1);
            continue;
        }}

        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.life;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1.0;
    }}
}}

function drawScene(carProgress) {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 1. 잔디밭 및 나무 렌더링
    trees.forEach(t => drawTree(t.x, t.y, t.r));

    // 2. 아스팔트 갓길 및 도로 베이스
    ctx.beginPath();
    ctx.arc(centerX, centerY, trackR, -Math.PI / 2, 0, false);
    ctx.lineWidth = roadWidth + 8;
    ctx.strokeStyle = "#e74c3c"; // 경계석 (빨강/흰색 번갈아 표시는 외곽선으로 대체)
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(centerX, centerY, trackR, -Math.PI / 2, 0, false);
    ctx.lineWidth = roadWidth;
    ctx.strokeStyle = "#2c3e50"; // 메인 아스팔트
    ctx.stroke();

    // 3. 도로 중앙선 (황색 점선)
    ctx.beginPath();
    ctx.arc(centerX, centerY, trackR, -Math.PI / 2, 0, false);
    ctx.lineWidth = 3;
    ctx.setLineDash([14, 12]);
    ctx.strokeStyle = "#f1c40f";
    ctx.stroke();
    ctx.setLineDash([]);

    // 4. 외곽 가드레일 (외곽 곡선)
    const guardR = trackR + roadWidth / 2 + 3;
    ctx.beginPath();
    ctx.arc(centerX, centerY, guardR, -Math.PI / 2, 0, false);
    ctx.lineWidth = 5;
    ctx.strokeStyle = "#bdc3c7"; // 금속 가드레일
    ctx.stroke();

    // 가드레일 지지대 기둥
    for (let a = -Math.PI / 2; a <= 0; a += 0.15) {{
        let px = centerX + guardR * Math.cos(a);
        let py = centerY + guardR * Math.sin(a);
        ctx.fillStyle = "#7f8c8d";
        ctx.fillRect(px - 2, py - 2, 5, 5);
    }}

    // 5. 자동차 위치 및 물리 상태 계산
    let carX, carY, carAngle;
    let isCollided = false;
    const slipPoint = 0.45;
    const guardCrashR = trackR + roadWidth / 2 - 10; // 가드레일 충돌 지점

    if (config.is_safe || carProgress <= slipPoint) {{
        // 정상 코너링
        const angle = -Math.PI / 2 + (Math.PI / 2) * carProgress;
        carX = centerX + trackR * Math.cos(angle);
        carY = centerY + trackR * Math.sin(angle);
        carAngle = angle + Math.PI / 2;
    }} else {{
        // 이탈 진행
        const angle = -Math.PI / 2 + (Math.PI / 2) * slipPoint;
        const startX = centerX + trackR * Math.cos(angle);
        const startY = centerY + trackR * Math.sin(angle);
        const tangentAngle = angle + Math.PI / 2;

        const over = (carProgress - slipPoint) * 320;
        let testX = startX + Math.cos(tangentAngle) * over;
        let testY = startY + Math.sin(tangentAngle) * over;

        // 가드레일 충돌 검사 (중심으로부터의 거리)
        let dist = Math.hypot(testX - centerX, testY - centerY);
        if (dist >= guardCrashR) {{
            isCollided = true;
            // 충돌 지점에 고정
            let crashAngle = Math.atan2(testY - centerY, testX - centerX);
            carX = centerX + guardCrashR * Math.cos(crashAngle);
            carY = centerY + guardCrashR * Math.sin(crashAngle);
            carAngle = tangentAngle + 0.3; // 충돌로 차체가 살짝 돌아감
            createSparks(carX, carY);
        }} else {{
            carX = testX;
            carY = testY;
            carAngle = tangentAngle;
        }}
    }}

    // 6. 자동차 그리기
    ctx.save();
    ctx.translate(carX, carY);
    ctx.rotate(carAngle);

    const carWidth = 44;
    const carHeight = 22;

    // 타이어
    ctx.fillStyle = "#111";
    ctx.fillRect(-carWidth/2 + 6, -carHeight/2 - 3, 10, 4);
    ctx.fillRect(carWidth/2 - 16, -carHeight/2 - 3, 10, 4);
    ctx.fillRect(-carWidth/2 + 6, carHeight/2 - 1, 10, 4);
    ctx.fillRect(carWidth/2 - 16, carHeight/2 - 1, 10, 4);

    // 차체
    ctx.fillStyle = isCollided ? "#e74c3c" : (config.is_safe ? "#2ecc71" : "#e67e22");
    ctx.beginPath();
    ctx.roundRect(-carWidth/2, -carHeight/2, carWidth, carHeight, 6);
    ctx.fill();

    // 루프 & 유릿창
    ctx.fillStyle = "#1e272e";
    ctx.beginPath();
    ctx.roundRect(-carWidth/6, -carHeight/2 + 3, carWidth/3, carHeight - 6, 3);
    ctx.fill();

    // 헤드라이트
    ctx.fillStyle = "#f1c40f";
    ctx.fillRect(carWidth/2 - 2, -carHeight/2 + 3, 3, 4);
    ctx.fillRect(carWidth/2 - 2, carHeight/2 - 7, 3, 4);

    ctx.restore();

    // 7. 파티클 이펙트 업데이트
    updateAndDrawSparks();

    // 8. 텍스트 지표
    ctx.font = "bold 16px 'Segoe UI', sans-serif";
    if (isCollided) {{
        ctx.fillStyle = "#e74c3c";
        ctx.fillText("💥 가드레일 충돌 발생!", 20, 40);
    }} else if (carProgress > 0 && !config.is_safe && carProgress > slipPoint) {{
        ctx.fillStyle = "#e67e22";
        ctx.fillText("⚠️ 원심력으로 이탈 중...", 20, 40);
    }} else if (carProgress > 0) {{
        ctx.fillStyle = "#2ecc71";
        ctx.fillText("🏎️ 안전하게 코너링 중", 20, 40);
    }} else {{
        ctx.fillStyle = "#ffffff";
        ctx.fillText("🏎️ 시뮬레이션 대기 중", 20, 40);
    }}
}}

function animate() {{
    if (!isAnimating) return;
    
    const speedFactor = 0.003 + (config.user_speed / 150) * 0.007;
    progress += speedFactor;

    if (progress > 1.2) {{
        // 충돌 상태면 스파크만 조금 더 연출 후 종료
        if (sparks.length === 0) {{
            isAnimating = false;
            return;
        }}
    }}

    drawScene(Math.min(progress, 1.2));
    animId = requestAnimationFrame(animate);
}}

function startSimulation() {{
    if (animId) cancelAnimationFrame(animId);
    sparks = [];
    progress = 0;
    isAnimating = true;
    animate();
}}

// 초기 화면
drawScene(0);
</script>
</body>
</html>
"""

components.html(canvas_html, height=500)

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
