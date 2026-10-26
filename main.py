import html
import json
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# =============================================================================
# 0. Streamlit 페이지 설정
# =============================================================================
st.set_page_config(
    page_title="대한민국 고속도로 커브길 안전 속도 시뮬레이터",
    page_icon="🛣️",
    layout="wide"
)

st.title("🛣️ 대한민국 고속도로 커브길 주행 시뮬레이터")
st.caption("고속도로 기하구조 곡률 모델 및 노면 상태(빗길/빙판길)에 따른 원심력 이탈 시뮬레이션")

st.markdown("---")

# =============================================================================
# 1. 입력 (Input) 단계: 사이드바 사용자 제어 환경
# =============================================================================
st.sidebar.header("⚙️ 도로 및 주행 환경 설정")

# 1-1. 날씨 및 노면 상태 선택
weather_option = st.sidebar.selectbox(
    "1. 날씨 및 노면 상태 선택",
    ["맑음 (건조한 노면, μ=0.8)", "비 (젖은 노면/수막현상, μ=0.4)", "눈/빙판길 (블랙아이스, μ=0.1)"]
)

if "맑음" in weather_option:
    mu = 0.8
    weather_type = "dry"
elif "비" in weather_option:
    mu = 0.4
    weather_type = "rain"
else:
    mu = 0.1
    weather_type = "ice"

# 1-2. 곡선 반경 (r) 설정
radius = st.sidebar.slider(
    "2. 곡선 반경 r (m)",
    min_value=20,
    max_value=200,
    value=80,
    step=10,
    help="대한민국 고속도로 설계기준 곡선반경입니다. (20~50m: 나들목/램프 급커브, 100m~200m: 본선 커브)"
)

# 1-3. 차량 진입 속도 (v) 설정
user_speed_kmh = st.sidebar.slider(
    "3. 차량 진입 속도 (km/h)",
    min_value=20,
    max_value=150,
    value=80,
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
# 4. HTML5 Canvas 시뮬레이션 (JSON 이스케이프 파싱 오류 100% 차단)
# =============================================================================
st.subheader("🎬 2D 고속도로 커브길 주행 시뮬레이션")

sim_params = {
    "is_safe": bool(is_safe),
    "radius": int(radius),
    "user_speed": int(user_speed_kmh),
    "max_speed": float(v_max_kmh),
    "weather": weather_type
}

# 파이썬 f-string과 HTML/JS 간 특수문자 충돌을 원천 차단하는 표준 주입 방식
json_data = html.escape(json.dumps(sim_params))

html_template = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        background-color: #0e1117;
        font-family: 'Segoe UI', system-ui, sans-serif;
        color: #ffffff;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 10px;
    }
    .btn-container { margin-bottom: 12px; }
    .start-btn {
        background: linear-gradient(135deg, #ff4b4b, #d32f2f);
        color: #ffffff;
        border: none;
        padding: 12px 32px;
        font-size: 17px;
        font-weight: 700;
        border-radius: 8px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
        transition: all 0.2s ease;
    }
    .start-btn:hover { transform: translateY(-2px); }
    #simCanvas {
        background: #141c15;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.6);
    }
</style>
</head>
<body>

<div class="btn-container">
    <button class="start-btn" id="startBtn">▶️ 고속도로 주행 시뮬레이션 시작</button>
</div>
<canvas id="simCanvas" width="820" height="480"></canvas>

<div id="cfgData" data-json="CONFIG_JSON_PLACEHOLDER" style="display:none;"></div>

<script>
(function() {
    const rawData = document.getElementById("cfgData").getAttribute("data-json");
    const cfg = JSON.parse(rawData.replace(/&quot;/g, '"'));

    const canvas = document.getElementById("simCanvas");
    const ctx = canvas.getContext("2d");
    const startBtn = document.getElementById("startBtn");

    let animId = null;
    let progress = 0;
    let isRunning = false;
    let sparks = [];
    let rainRipples = [];

    const minR = 20, maxR = 200;
    const normR = (cfg.radius - minR) / (maxR - minR);

    const radiusX = 220 + normR * 320;
    const radiusY = 380 - normR * 40;
    
    const centerX = 40 - normR * 80;
    const centerY = 450 + normR * 60;
    const roadWidth = 85;

    const trees = [
        { x: 520, y: 70, r: 24 },
        { x: 630, y: 150, r: 28 },
        { x: 680, y: 270, r: 26 },
        { x: 650, y: 390, r: 30 },
        { x: 90, y: 60, r: 20 }
    ];

    for(let i=0; i<12; i++) {
        rainRipples.push({
            x: 200 + Math.random() * 450,
            y: 80 + Math.random() * 300,
            r: Math.random() * 8,
            alpha: Math.random()
        });
    }

    function getEllipsePoint(angle) {
        const x = centerX + radiusX * Math.cos(angle);
        const y = centerY + radiusY * Math.sin(angle);
        const dx = -radiusX * Math.sin(angle);
        const dy = radiusY * Math.cos(angle);
        const tangentAngle = Math.atan2(dy, dx);
        return { x, y, dx, dy, tangentAngle };
    }

    function drawTree(x, y, r) {
        ctx.fillStyle = "rgba(0,0,0,0.25)";
        ctx.beginPath();
        ctx.ellipse(x + 4, y + 4, r, r * 0.7, 0, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = cfg.weather === "ice" ? "#234033" : "#214e21";
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = cfg.weather === "ice" ? "#386350" : "#2e682e";
        ctx.beginPath();
        ctx.arc(x - r*0.2, y - r*0.2, r * 0.65, 0, Math.PI * 2);
        ctx.fill();
    }

    function createSparks(x, y) {
        for (let i = 0; i < 6; i++) {
            sparks.push({
                x: x, y: y,
                vx: (Math.random() - 0.5) * 8,
                vy: (Math.random() - 0.5) * 8,
                life: 1.0,
                color: Math.random() > 0.5 ? "#f1c40f" : "#e67e22"
            });
        }
    }

    function renderSparks() {
        for (let i = sparks.length - 1; i >= 0; i--) {
            let p = sparks[i];
            p.x += p.vx;
            p.y += p.vy;
            p.life -= 0.06;

            if (p.life <= 0) {
                sparks.splice(i, 1);
                continue;
            }

            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.life;
            ctx.beginPath();
            ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1.0;
        }
    }

    function drawFrame(p) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        trees.forEach(t => drawTree(t.x, t.y, t.r));

        let roadColor = "#2c3e50";
        if (cfg.weather === "rain") roadColor = "#121921";
        if (cfg.weather === "ice") roadColor = "#2b3e50";

        ctx.beginPath();
        ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, -Math.PI / 2, 0, false);
        ctx.lineWidth = roadWidth + 10;
        ctx.strokeStyle = "#c0392b";
        ctx.stroke();

        ctx.beginPath();
        ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, -Math.PI / 2, 0, false);
        ctx.lineWidth = roadWidth;
        ctx.strokeStyle = roadColor;
        ctx.stroke();

        if (cfg.weather === "rain") {
            ctx.save();
            ctx.lineWidth = roadWidth - 12;
            ctx.strokeStyle = "rgba(100, 150, 200, 0.18)";
            ctx.setLineDash([60, 40, 20, 50]);
            ctx.beginPath();
            ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, -Math.PI / 2, 0, false);
            ctx.stroke();

            ctx.lineWidth = 14;
            ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
            ctx.setLineDash([15, 80, 30, 60]);
            ctx.beginPath();
            ctx.ellipse(centerX, centerY, radiusX + 18, radiusY + 18, 0, -Math.PI / 2, 0, false);
            ctx.stroke();
            ctx.restore();

            rainRipples.forEach(rp => {
                ctx.strokeStyle = "rgba(200, 230, 255, " + (rp.alpha * 0.5) + ")";
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.arc(rp.x, rp.y, rp.r, 0, Math.PI * 2);
                ctx.stroke();

                rp.r += 0.4;
                rp.alpha -= 0.015;
                if (rp.alpha <= 0) {
                    rp.r = 1;
                    rp.alpha = 0.8;
                    rp.x = 200 + Math.random() * 450;
                    rp.y = 80 + Math.random() * 300;
                }
            });

        } else if (cfg.weather === "ice") {
            ctx.save();
            ctx.lineWidth = roadWidth - 6;
            ctx.strokeStyle = "rgba(236, 240, 241, 0.42)";
            ctx.setLineDash([25, 15, 8, 30, 40]);
            ctx.beginPath();
            ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, -Math.PI / 2, 0, false);
            ctx.stroke();

            ctx.lineWidth = 10;
            ctx.strokeStyle = "rgba(255, 255, 255, 0.65)";
            ctx.setLineDash([6, 35, 12, 50]);
            ctx.beginPath();
            ctx.ellipse(centerX, centerY, radiusX + 22, radiusY + 22, 0, -Math.PI / 2, 0, false);
            ctx.stroke();
            ctx.beginPath();
            ctx.ellipse(centerX, centerY, radiusX - 22, radiusY - 22, 0, -Math.PI / 2, 0, false);
            ctx.stroke();
            ctx.restore();
        }

        ctx.beginPath();
        ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, -Math.PI / 2, 0, false);
        ctx.lineWidth = 3;
        ctx.setLineDash([18, 16]);
        ctx.strokeStyle = "#f1c40f";
        ctx.stroke();
        ctx.setLineDash([]);

        const guardRx = radiusX + roadWidth / 2 + 4;
        const guardRy = radiusY + roadWidth / 2 + 4;
        ctx.beginPath();
        ctx.ellipse(centerX, centerY, guardRx, guardRy, 0, -Math.PI / 2, 0, false);
        ctx.lineWidth = 6;
        ctx.strokeStyle = "#95a5a6";
        ctx.stroke();

        for (let a = -Math.PI / 2; a <= 0; a += 0.1) {
            let px = centerX + guardRx * Math.cos(a);
            let py = centerY + guardRy * Math.sin(a);
            ctx.fillStyle = "#7f8c8d";
            ctx.fillRect(px - 3, py - 3, 6, 6);
        }

        let carX, carY, carAngle;
        let isCollided = false;
        const slipPoint = 0.45;

        if (cfg.is_safe || p <= slipPoint) {
            const angle = -Math.PI / 2 + (Math.PI / 2) * p;
            const pt = getEllipsePoint(angle);
            carX = pt.x;
            carY = pt.y;
            carAngle = pt.tangentAngle;
        } else {
            const angle = -Math.PI / 2 + (Math.PI / 2) * slipPoint;
            const pt = getEllipsePoint(angle);

            const over = (p - slipPoint) * 380;
            let testX = pt.x + Math.cos(pt.tangentAngle) * over;
            let testY = pt.y + Math.sin(pt.tangentAngle) * over;

            let normDist = Math.pow((testX - centerX) / guardRx, 2) + Math.pow((testY - centerY) / guardRy, 2);
            if (normDist >= 0.96) {
                isCollided = true;
                carX = testX;
                carY = testY;
                carAngle = pt.tangentAngle + 0.35;
                createSparks(carX, carY);
            } else {
                carX = testX;
                carY = testY;
                carAngle = pt.tangentAngle;
            }
        }

        ctx.save();
        ctx.translate(carX, carY);
        ctx.rotate(carAngle);

        const carW = 46, carH = 24;
        ctx.fillStyle = "#111";
        ctx.fillRect(-carW/2 + 6, -carH/2 - 3, 10, 4);
        ctx.fillRect(carW/2 - 16, -carH/2 - 3, 10, 4);
        ctx.fillRect(-carW/2 + 6, carH/2 - 1, 10, 4);
        ctx.fillRect(carW/2 - 16, carH/2 - 1, 10, 4);

        ctx.fillStyle = isCollided ? "#e74c3c" : (cfg.is_safe ? "#2ecc71" : "#e67e22");
        ctx.beginPath();
        if (ctx.roundRect) {
            ctx.roundRect(-carW/2, -carH/2, carW, carH, 6);
        } else {
            ctx.rect(-carW/2, -carH/2, carW, carH);
        }
        ctx.fill();

        ctx.fillStyle = "#1e272e";
        ctx.fillRect(-carW/6, -carH/2 + 3, carW/3, carH - 6);

        ctx.fillStyle = "#f1c40f";
        ctx.fillRect(carW/2 - 2, -carH/2 + 3, 3, 4);
        ctx.fillRect(carW/2 - 2, carH/2 - 7, 3, 4);

        ctx.restore();

        renderSparks();

        ctx.font = "bold 16px 'Segoe UI', sans-serif";
        if (isCollided) {
            ctx.fillStyle = "#e74c3c";
            ctx.fillText("💥 외곽 가드레일 충돌 발생!", 20, 35);
        } else if (p > 0 && !cfg.is_safe && p > slipPoint) {
            ctx.fillStyle = "#e67e22";
            ctx.fillText("⚠️ 원심력으로 도로 이탈 중...", 20, 35);
        } else if (p > 0) {
            ctx.fillStyle = "#2ecc71";
            ctx.fillText("🏎️ 고속도로 코너링 중", 20, 35);
        } else {
            ctx.fillStyle = "#ffffff";
            ctx.fillText("🏎️ 시뮬레이션 대기 중", 20, 35);
        }
    }

    function step() {
        if (!isRunning) return;
        
        const speed = 0.003 + (cfg.user_speed / 150) * 0.007;
        progress += speed;

        if (progress > 1.25) {
            progress = 1.25;
            drawFrame(progress);
            isRunning = false;
            return;
        }

        drawFrame(progress);
        animId = requestAnimationFrame(step);
    }

    startBtn.addEventListener("click", function() {
        if (animId) cancelAnimationFrame(animId);
        sparks = [];
        progress = 0;
        isRunning = true;
        step();
    });

    drawFrame(0);
})();
</script>
</body>
</html>
"""

rendered_html = html_template.replace("CONFIG_JSON_PLACEHOLDER", json_data)
components.html(rendered_html, height=540)

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
