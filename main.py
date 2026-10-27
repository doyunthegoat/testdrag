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
    page_title="대한민국 고속도로 커브길 시뮬레이터 & Secret Tetris",
    page_icon="🛣️",
    layout="wide"
)

st.title("🛣️ 대한민국 고속도로 커브길 주행 시뮬레이터")
st.caption("고속도로 기하구조 곡률 모델 및 노면 상태(빗길/빙판길)에 따른 원심력 이탈 시뮬레이션")

# 이스터에그 힌트 안내
st.info("💡 **Secret Easter Egg**: 키보드로 **`pass`** 단어를 연속으로 타이핑해보세요! 🎮 레트로 테트리스 게임이 열립니다.")

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
# 4. HTML5 Canvas 시뮬레이션 및 테트리스 이스터에그 융합
# =============================================================================
st.subheader("🎬 2D 고속도로 주행 시뮬레이션 (키보드로 'pass' 입력 시 테트리스 실행)")

sim_params = {
    "is_safe": bool(is_safe),
    "radius": int(radius),
    "user_speed": int(user_speed_kmh),
    "max_speed": float(v_max_kmh),
    "weather": weather_type
}

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
        overflow-x: hidden;
    }
    .btn-container { margin-bottom: 12px; display: flex; gap: 10px; }
    .start-btn {
        background: linear-gradient(135deg, #ff4b4b, #d32f2f);
        color: #ffffff;
        border: none;
        padding: 12px 28px;
        font-size: 16px;
        font-weight: 700;
        border-radius: 8px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
        transition: all 0.2s ease;
    }
    .start-btn:hover { transform: translateY(-2px); }
    .tetris-trigger-btn {
        background: linear-gradient(135deg, #8e44ad, #2980b9);
        color: #ffffff;
        border: none;
        padding: 12px 20px;
        font-size: 15px;
        font-weight: 600;
        border-radius: 8px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(142, 68, 173, 0.4);
        transition: all 0.2s ease;
    }
    .tetris-trigger-btn:hover { transform: translateY(-2px); }
    
    #simCanvas {
        background: #141c15;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.6);
    }

    /* ------------------------------------------------------------------ */
    /* Tetris Modal Overlay Styles */
    /* ------------------------------------------------------------------ */
    #tetrisModal {
        display: none;
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(8px);
        z-index: 9999;
        justify-content: center;
        align-items: center;
        flex-direction: column;
    }
    .tetris-container {
        background: #1e1e2f;
        padding: 24px;
        border-radius: 16px;
        border: 2px solid #8e44ad;
        box-shadow: 0 0 30px rgba(142, 68, 173, 0.6);
        display: flex;
        gap: 20px;
        position: relative;
    }
    .tetris-side {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        width: 140px;
    }
    .tetris-info-card {
        background: #2a2a40;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 10px;
    }
    .tetris-info-title { font-size: 12px; color: #a0a0c0; text-transform: uppercase; }
    .tetris-info-val { font-size: 22px; font-weight: bold; color: #00ffcc; margin-top: 4px; }
    
    #tetrisCanvas {
        background: #000000;
        border: 3px solid #333355;
        border-radius: 6px;
    }
    .close-modal-btn {
        position: absolute;
        top: -15px; right: -15px;
        background: #ff4b4b;
        color: white;
        border: none;
        width: 36px; height: 36px;
        border-radius: 50%;
        font-weight: bold;
        font-size: 18px;
        cursor: pointer;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .tetris-controls-hint {
        font-size: 12px;
        color: #8a8ab0;
        line-height: 1.6;
        margin-top: 10px;
        background: #141422;
        padding: 10px;
        border-radius: 6px;
    }
</style>
</head>
<body>

<div class="btn-container">
    <button class="start-btn" id="startBtn">▶️ 고속도로 주행 시뮬레이션 시작</button>
    <button class="tetris-trigger-btn" id="manualTetrisBtn">🎮 테트리스 열기 ('pass' 입력)</button>
</div>

<canvas id="simCanvas" width="820" height="480"></canvas>
<div id="cfgData" data-json="CONFIG_JSON_PLACEHOLDER" style="display:none;"></div>

<!-- =================================================================== -->
<!-- TETRIS EASTER EGG MODAL OVERLAY -->
<!-- =================================================================== -->
<div id="tetrisModal">
    <div class="tetris-container">
        <button class="close-modal-btn" id="closeTetrisBtn">✕</button>
        <div>
            <h2 style="color: #00ffcc; font-size: 20px; margin-bottom: 12px; text-align: center;">🕹️ SECRET TETRIS</h2>
            <canvas id="tetrisCanvas" width="240" height="400"></canvas>
        </div>
        <div class="tetris-side">
            <div>
                <div class="tetris-info-card">
                    <div class="tetris-info-title">SCORE</div>
                    <div class="tetris-info-val" id="tetrisScore">0</div>
                </div>
                <div class="tetris-info-card">
                    <div class="tetris-info-title">LINES</div>
                    <div class="tetris-info-val" id="tetrisLines">0</div>
                </div>
                <div class="tetris-info-card">
                    <div class="tetris-info-title">LEVEL</div>
                    <div class="tetris-info-val" id="tetrisLevel">1</div>
                </div>
            </div>
            
            <div class="tetris-controls-hint">
                <b>🎮 조작법:</b><br>
                • ◀ / ▶ : 좌우 이동<br>
                • ▲ : 블록 회전<br>
                • ▼ : 빨리 내리기<br>
                • Space : 즉시 하강<br>
                • P : 일시정지
            </div>
        </div>
    </div>
</div>

<script>
(function() {
    // ------------------------------------------------------------------
    // 1. 고속도로 시뮬레이션 로직
    // ------------------------------------------------------------------
    const rawData = document.getElementById("cfgData").getAttribute("data-json");
    let cfg;
    try {
        cfg = JSON.parse(rawData.replace(/&quot;/g, '"'));
    } catch(e) {
        cfg = { is_safe: true, radius: 80, user_speed: 80, max_speed: 100, weather: "dry" };
    }

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
        { x: 520, y: 70, r: 24 }, { x: 630, y: 150, r: 28 },
        { x: 680, y: 270, r: 26 }, { x: 650, y: 390, r: 30 },
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
        return { x, y, dx, dy, tangentAngle: Math.atan2(dy, dx) };
    }

    function drawTree(x, y, r) {
        ctx.fillStyle = "rgba(0,0,0,0.25)";
        ctx.beginPath();
        ctx.ellipse(x + 4, y + 4, r, r * 0.7, 0, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = cfg.weather === "ice" ? "#234033" : "#214e21";
        ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();

        ctx.fillStyle = cfg.weather === "ice" ? "#386350" : "#2e682e";
        ctx.beginPath(); ctx.arc(x - r*0.2, y - r*0.2, r * 0.65, 0, Math.PI * 2); ctx.fill();
    }

    function createSparks(x, y) {
        for (let i = 0; i < 6; i++) {
            sparks.push({
                x: x, y: y,
                vx: (Math.random() - 0.5) * 8, vy: (Math.random() - 0.5) * 8,
                life: 1.0, color: Math.random() > 0.5 ? "#f1c40f" : "#e67e22"
            });
        }
    }

    function renderSparks() {
        for (let i = sparks.length - 1; i >= 0; i--) {
            let p = sparks[i];
            p.x += p.vx; p.y += p.vy; p.life -= 0.06;
            if (p.life <= 0) { sparks.splice(i, 1); continue; }
            ctx.fillStyle = p.color; ctx.globalAlpha = p.life;
            ctx.beginPath(); ctx.arc(p.x, p.y, 3, 0, Math.PI * 2); ctx.fill();
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
        ctx.lineWidth = roadWidth + 10; ctx.strokeStyle = "#c0392b"; ctx.stroke();

        ctx.beginPath();
        ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, -Math.PI / 2, 0, false);
        ctx.lineWidth = roadWidth; ctx.strokeStyle = roadColor; ctx.stroke();

        if (cfg.weather === "rain") {
            ctx.save();
            ctx.lineWidth = roadWidth - 12; ctx.strokeStyle = "rgba(100, 150, 200, 0.18)";
            ctx.setLineDash([60, 40, 20, 50]);
            ctx.beginPath(); ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, -Math.PI / 2, 0, false); ctx.stroke();
            ctx.restore();

            rainRipples.forEach(rp => {
                ctx.strokeStyle = "rgba(200, 230, 255, " + (rp.alpha * 0.5) + ")";
                ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(rp.x, rp.y, rp.r, 0, Math.PI * 2); ctx.stroke();
                rp.r += 0.4; rp.alpha -= 0.015;
                if (rp.alpha <= 0) { rp.r = 1; rp.alpha = 0.8; rp.x = 200 + Math.random() * 450; rp.y = 80 + Math.random() * 300; }
            });
        }

        ctx.beginPath();
        ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, -Math.PI / 2, 0, false);
        ctx.lineWidth = 3; ctx.setLineDash([18, 16]); ctx.strokeStyle = "#f1c40f"; ctx.stroke(); ctx.setLineDash([]);

        const guardRx = radiusX + roadWidth / 2 + 4;
        const guardRy = radiusY + roadWidth / 2 + 4;
        ctx.beginPath();
        ctx.ellipse(centerX, centerY, guardRx, guardRy, 0, -Math.PI / 2, 0, false);
        ctx.lineWidth = 6; ctx.strokeStyle = "#95a5a6"; ctx.stroke();

        let carX, carY, carAngle;
        let isCollided = false;
        const slipPoint = 0.45;

        if (cfg.is_safe || p <= slipPoint) {
            const angle = -Math.PI / 2 + (Math.PI / 2) * p;
            const pt = getEllipsePoint(angle);
            carX = pt.x; carY = pt.y; carAngle = pt.tangentAngle;
        } else {
            const angle = -Math.PI / 2 + (Math.PI / 2) * slipPoint;
            const pt = getEllipsePoint(angle);
            const over = (p - slipPoint) * 380;
            let testX = pt.x + Math.cos(pt.tangentAngle) * over;
            let testY = pt.y + Math.sin(pt.tangentAngle) * over;

            let normDist = Math.pow((testX - centerX) / guardRx, 2) + Math.pow((testY - centerY) / guardRy, 2);
            if (normDist >= 0.96) {
                isCollided = true; carX = testX; carY = testY;
                carAngle = pt.tangentAngle + 0.35; createSparks(carX, carY);
            } else { carX = testX; carY = testY; carAngle = pt.tangentAngle; }
        }

        ctx.save();
        ctx.translate(carX, carY); ctx.rotate(carAngle);
        const carW = 46, carH = 24;
        ctx.fillStyle = isCollided ? "#e74c3c" : (cfg.is_safe ? "#2ecc71" : "#e67e22");
        if (ctx.roundRect) ctx.roundRect(-carW/2, -carH/2, carW, carH, 6);
        else ctx.rect(-carW/2, -carH/2, carW, carH);
        ctx.fill();
        ctx.restore();

        renderSparks();

        ctx.font = "bold 16px 'Segoe UI', sans-serif";
        if (isCollided) { ctx.fillStyle = "#e74c3c"; ctx.fillText("💥 외곽 가드레일 충돌 발생!", 20, 35); }
        else if (p > 0 && !cfg.is_safe && p > slipPoint) { ctx.fillStyle = "#e67e22"; ctx.fillText("⚠️ 원심력으로 도로 이탈 중...", 20, 35); }
        else if (p > 0) { ctx.fillStyle = "#2ecc71"; ctx.fillText("🏎️ 고속도로 코너링 중", 20, 35); }
        else { ctx.fillStyle = "#ffffff"; ctx.fillText("🏎️ 시뮬레이션 대기 중", 20, 35); }
    }

    function step() {
        if (!isRunning) return;
        progress += 0.003 + (cfg.user_speed / 150) * 0.007;
        if (progress > 1.25) { progress = 1.25; drawFrame(progress); isRunning = false; return; }
        drawFrame(progress);
        animId = requestAnimationFrame(step);
    }

    startBtn.addEventListener("click", function() {
        if (animId) cancelAnimationFrame(animId);
        sparks = []; progress = 0; isRunning = true; step();
    });

    drawFrame(0);

    // ------------------------------------------------------------------
    // 2. 키보드 'pass' 감지 이스터에그 엔진
    // ------------------------------------------------------------------
    let keyBuffer = "";
    window.addEventListener("keydown", function(e) {
        // 입력 태그 안에서의 키 타이핑은 무시
        if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

        keyBuffer += e.key.toLowerCase();
        if (keyBuffer.length > 10) keyBuffer = keyBuffer.slice(-10);

        if (keyBuffer.endsWith("pass")) {
            openTetrisModal();
            keyBuffer = "";
        }
    });

    document.getElementById("manualTetrisBtn").addEventListener("click", openTetrisModal);

    // ------------------------------------------------------------------
    // 3. 테트리스 게임 모달 및 물리 엔진
    // ------------------------------------------------------------------
    const tetrisModal = document.getElementById("tetrisModal");
    const closeTetrisBtn = document.getElementById("closeTetrisBtn");
    const tCanvas = document.getElementById("tetrisCanvas");
    const tCtx = tCanvas.getContext("2d");

    const COLS = 10, ROWS = 20, BLOCK_SIZE = 24;
    let board = [], score = 0, lines = 0, level = 1;
    let tetrisLoop = null, currentPiece = null, isTetrisGameOver = false, isPaused = false;

    const SHAPES = [
        [[1, 1, 1, 1]], // I
        [[1, 1], [1, 1]], // O
        [[0, 1, 0], [1, 1, 1]], // T
        [[1, 0, 0], [1, 1, 1]], // L
        [[0, 0, 1], [1, 1, 1]], // J
        [[0, 1, 1], [1, 1, 0]], // S
        [[1, 1, 0], [0, 1, 1]]  // Z
    ];
    const COLORS = ["#00f0f0", "#f0f000", "#a000f0", "#f0a000", "#0000f0", "#00f000", "#f00000"];

    function initBoard() {
        board = Array.from({ length: ROWS }, () => Array(COLS).fill(0));
    }

    function createPiece() {
        const idx = Math.floor(Math.random() * SHAPES.length);
        return {
            shape: SHAPES[idx],
            color: COLORS[idx],
            x: Math.floor(COLS / 2) - Math.ceil(SHAPES[idx][0].length / 2),
            y: 0
        };
    }

    function openTetrisModal() {
        tetrisModal.style.display = "flex";
        resetTetrisGame();
    }

    function closeTetrisModal() {
        tetrisModal.style.display = "none";
        if (tetrisLoop) clearInterval(tetrisLoop);
    }

    closeTetrisBtn.addEventListener("click", closeTetrisModal);

    function resetTetrisGame() {
        initBoard();
        score = 0; lines = 0; level = 1;
        isTetrisGameOver = false; isPaused = false;
        updateTetrisUI();
        currentPiece = createPiece();
        if (tetrisLoop) clearInterval(tetrisLoop);
        tetrisLoop = setInterval(updateTetrisFrame, 600 - (level * 40));
        drawTetris();
    }

    function updateTetrisUI() {
        document.getElementById("tetrisScore").innerText = score;
        document.getElementById("tetrisLines").innerText = lines;
        document.getElementById("tetrisLevel").innerText = level;
    }

    function collide(piece, offset) {
        const { shape, x, y } = piece;
        const ox = x + (offset.x || 0);
        const oy = y + (offset.y || 0);

        for (let r = 0; r < shape.length; r++) {
            for (let c = 0; c < shape[r].length; c++) {
                if (shape[r][c]) {
                    let newX = ox + c;
                    let newY = oy + r;
                    if (newX < 0 || newX >= COLS || newY >= ROWS) return true;
                    if (newY >= 0 && board[newY][newX]) return true;
                }
            }
        }
        return false;
    }

    function mergePiece() {
        const { shape, color, x, y } = currentPiece;
        for (let r = 0; r < shape.length; r++) {
            for (let c = 0; c < shape[r].length; c++) {
                if (shape[r][c] && y + r >= 0) {
                    board[y + r][x + c] = color;
                }
            }
        }
    }

    function clearLines() {
        let linesCleared = 0;
        for (let r = ROWS - 1; r >= 0; r--) {
            if (board[r].every(cell => cell !== 0)) {
                board.splice(r, 1);
                board.unshift(Array(COLS).fill(0));
                linesCleared++;
                r++;
            }
        }
        if (linesCleared > 0) {
            lines += linesCleared;
            score += linesCleared * 100 * level;
            level = Math.floor(lines / 5) + 1;
            updateTetrisUI();
            clearInterval(tetrisLoop);
            tetrisLoop = setInterval(updateTetrisFrame, Math.max(100, 600 - (level * 40)));
        }
    }

    function rotatePiece(piece) {
        const shape = piece.shape;
        const rotated = shape[0].map((_, i) => shape.map(row => row[i]).reverse());
        return { ...piece, shape: rotated };
    }

    function updateTetrisFrame() {
        if (isPaused || isTetrisGameOver) return;

        if (!collide(currentPiece, { y: 1 })) {
            currentPiece.y++;
        } else {
            mergePiece();
            clearLines();
            currentPiece = createPiece();
            if (collide(currentPiece, { y: 0 })) {
                isTetrisGameOver = true;
                clearInterval(tetrisLoop);
            }
        }
        drawTetris();
    }

    function drawTetris() {
        tCtx.clearRect(0, 0, tCanvas.width, tCanvas.height);

        // 보드 그리기
        for (let r = 0; r < ROWS; r++) {
            for (let c = 0; c < COLS; c++) {
                if (board[r][c]) {
                    tCtx.fillStyle = board[r][c];
                    tCtx.fillRect(c * BLOCK_SIZE, r * BLOCK_SIZE, BLOCK_SIZE - 1, BLOCK_SIZE - 1);
                }
            }
        }

        // 현재 조각 그리기
        if (currentPiece && !isTetrisGameOver) {
            tCtx.fillStyle = currentPiece.color;
            for (let r = 0; r < currentPiece.shape.length; r++) {
                for (let c = 0; c < currentPiece.shape[r].length; c++) {
                    if (currentPiece.shape[r][c]) {
                        tCtx.fillRect((currentPiece.x + c) * BLOCK_SIZE, (currentPiece.y + r) * BLOCK_SIZE, BLOCK_SIZE - 1, BLOCK_SIZE - 1);
                    }
                }
            }
        }

        if (isTetrisGameOver) {
            tCtx.fillStyle = "rgba(0,0,0,0.75)";
            tCtx.fillRect(0, 0, tCanvas.width, tCanvas.height);
            tCtx.fillStyle = "#ff4b4b";
            tCtx.font = "bold 22px 'Segoe UI'";
            tCtx.textAlign = "center";
            tCtx.fillText("GAME OVER", tCanvas.width / 2, tCanvas.height / 2 - 10);
            tCtx.fillStyle = "#ffffff";
            tCtx.font = "14px 'Segoe UI'";
            tCtx.fillText("'Space' 눌러 재시작", tCanvas.width / 2, tCanvas.height / 2 + 20);
        }
    }

    window.addEventListener("keydown", function(e) {
        if (tetrisModal.style.display !== "flex") return;

        if (isTetrisGameOver) {
            if (e.code === "Space") resetTetrisGame();
            return;
        }

        if (e.key.toLowerCase() === "p") {
            isPaused = !isPaused;
            return;
        }

        if (isPaused) return;

        if (e.key === "ArrowLeft") {
            if (!collide(currentPiece, { x: -1 })) currentPiece.x--;
            e.preventDefault();
        } else if (e.key === "ArrowRight") {
            if (!collide(currentPiece, { x: 1 })) currentPiece.x++;
            e.preventDefault();
        } else if (e.key === "ArrowDown") {
            if (!collide(currentPiece, { y: 1 })) currentPiece.y++;
            e.preventDefault();
        } else if (e.key === "ArrowUp") {
            const rot = rotatePiece(currentPiece);
            if (!collide(rot, { x: 0, y: 0 })) currentPiece = rot;
            e.preventDefault();
        } else if (e.code === "Space") {
            while (!collide(currentPiece, { y: 1 })) {
                currentPiece.y++;
            }
            updateTetrisFrame();
            e.preventDefault();
        }
        drawTetris();
    });
})();
</script>
</body>
</html>
"""

rendered_html = html_template.replace("CONFIG_JSON_PLACEHOLDER", json_data)
components.html(rendered_html, height=560)

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
