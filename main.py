import base64
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
# 4. HTML5 Canvas 시뮬레이션 (Base64 하드코딩 방식으로 문자열 파싱 오류 원천 차단)
# =============================================================================
st.subheader("🎬 2D 고속도로 커브길 주행 시뮬레이션")

sim_params = {
    "is_safe": bool(is_safe),
    "radius": int(radius),
    "user_speed": int(user_speed_kmh),
    "max_speed": float(v_max_kmh),
    "weather": weather_type
}

# HTML/JS 코드 전문의 Base64 인코딩 데이터 (f-string 따옴표 에러 완전 차단)
b64_html_template = "PCFE T0NUWVBFIGh0bWw+Cmh0bWw+Cj headPgo8bWV0YSBjaGFyc2V0PSJ1dGYtOCI+CjxzdHlsZT4KICAgICogeyBib3gtc2l6aW5nOiBib3JkZXItYm94OyBtYXJnaW46IDA7IHBhZGRpbmc6IDA7IH0KICAgIGJvZHkgeyBiYWNrZ3JvdW5kLWNvbG9yOiAjMGUxMTE3OyBmb250LWZhbWlseTogc2Fucy1zZXJpZjsgY29sb3I6ICNmZmY7IGRpc3BsYXk6IGZsZXg7IGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47IGFsaWduLWl0ZW1zOiBjZW50ZXI7IHBhZGRpbmctdG9wOiAxMHB4OyB9CiAgICAuYnRuLWNvbnRhaW5lciB7IG1hcmdpbi1ib3R0b206IDEycHg7IH0KICAgIC5zdGFydC1idG4gewogICAgICAgIGJhY2tncm91bmQ6IGxpbmVhci1ncmFkaWVudCgxMzVkZWcsICNmZjRiNGIsIC1kMzJmMmYpOwogICAgICAgIGNvbG9yOiAjZmZmOwogICAgICAgIGJvcmRlcjogbm9uZTsKICAgICAgICBwYWRkaW5nOiAxMnB4IDMycHg7CiAgICAgICAgZm9udC1zaXplOiAxN3B4OwogICAgICAgIGZvbnQtd2VpZ2h0OiA3MDA7CiAgICAgICAgYm9yZGVyLXJhZGl1czogOHB4OwogICAgICAgIGN1cnNvcjogcG9pbnRlcjsKICAgICAgICBib3gtc2hhZG93OiAwIDRweCAxMnB4IHJnYmEoMjU1LCA3NSwgNzUsIDAuNCk7CiAgICB9CiAgICAuc3RhcnQtYnRuOmhvdmVyIHsgdHJhbnNmb3JtOiB0cmFuc2xhdGVZKC0ycHgpOyB9CiAgICAjc2ltQ2FudmFzIHsgYmFja2dyb3VuZDogIzE0MWMxNTsgYm9yZGVyLXJhZGl1czogMTJweDsgYm94LXNoYWRvdzogMCA4cHggMjRweCByZ2JhKDAsMCwwLDAuNik7IH0KPC9zdHlsZT4KPC9oZWFkPgo8Ym9keT4KPGRpdiBjbGFzcz0iYnRuLWNvbnRhaW5lciI+PGJ1dHRvbiBjbGFzcz0ic3RhcnQtYnRuIiBpZD0ic3RhcnRCdG4iPlLsoS3qso3EroTrm4wg7K287ZW0IHNpbXVsYXRpb24gc3RhcnQ8L2J1dHRvbj48L2Rpdj4KPGNhbnZhcyBpZD0ic2ltQ2FudmFzIiB3aWR0aD0iODIwIiBoZWlnaHQ9IjQ4MCI+PC9jYW52YXM+CjxzY3JpcHQ+CihmdW5jdGlvbigpIHsKICAgIGNvbnN0IGNmZyA9IF9fQ0ZHX0pTT05fXzsKICAgIGNvbnN0IGNhbnZhcyA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJzaW1DYW52YXMiKTsKICAgIGNvbnN0IGN0eCA9IGNhbnZhcy5nZXRDb250ZXh0KCIyZCIpOwogICAgY29uc3Qgc3RhcnRCdG4gPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgic3RhcnRCdG4iKTsKCiAgICBsZXQgYW5pbUlkID0gbnVsbCwgcHJvZ3Jlc3MgPSAwLCBpc1J1bm5pbmcgPSBmYWxzZSwgc3BhcmtzID0gW10sIHJhaW5SaXBwbGVzID0gW107CiAgICBjb25zdCBtaW5SID0gMjAsIG1heFIgPSAyMDAsIG5vcm1SID0gKGNmZy5yYWRpdXMgLSBtaW5SKSAvIChtYXhSIC0gbWluUik7CiAgICBjb25zdCByYWRpdXNYID0gMjIwICsgbm9ybVIgKiAzMjAsIHJhZGl1c1kgPSAzODAgLSBub3JtUiAqIDQwOwogICAgY29uc3QgY2VudGVyWCA9IDQwIC0gbm9ybVIgKiA4MCwgY2VudGVyWSA9IDQ1MCArIG5vcm1SIDogNjAsIHJvYWRXaWR0aCA9IDg1OwogICAgY29uc3QgdHJlZXMgPSBbI3s1MjAsNzAsMjR9LCN7NjMwLDE1MCwyOH0sI3s2ODAsMjcwLDI2fSwjezY1MCwzOTAsMzB9LCN7OTAsNjAsMjB9XTsKICAgIGZvcihsZXQgaT0wO2k8MTI7aSsrKSB7IHJhaW5SaXBwbGVzLnB1c2goe3g6MjAwK01hdGgucmFuZG9tKCkqNDUwLCB5OjgwK01hdGgucmFuZG9tKCkqMzAwLCByOk1hdGgucmFuZG9tKCkqOCwgYWxwaGE6TWF0aC5yYW5kb20oKX0pOyB9CgogICAgZnVuY3Rpb24gZ2V0RWxsaXBzZVBvaW50KGFuZ2xlKSB7CiAgICAgICAgY29uc3QgeCA9IGNlbnRlclggKyByYWRpdXNYICogTWF0aC5jb3MoYW5nbGUpOwogICAgICAgIGNvbnN0IHkgPSBjZW50ZXJZICsgcmFkaXVzWSAqIE1hdGguY29zKGFuZ2xlKTsKICAgICAgICByZXR1cm4geyB4LCB5LCBkeDogLXJhZGl1c1ggKiBNYXRoLnNpbihhbmdsZSksIGR5OiByYWRpdXNZICogTWF0aC5jb3MoYW5nbGUpLCB0YW5nZW50QW5nbGU6IE1hdGguYXRhbjIocmFkaXVzWSAqIE1hdGguY29zKGFuZ2xlKSwgLXJhZGl1c1ggKiBNYXRoLnNpbihhbmdsZSkpIH07CiAgICB9CgogICAgZnVuY3Rpb24gZHJhd1RyZWUoeCwgeSwgcikgewogICAgICAgIGN0eC5maWxsU3R5bGUgPSAicmdiYSgwLDAsMCwwLjI1KSI7IGN0eC5iZWdpblBhdGgoKTsgY3R4LmVsbGlwc2UoeCs0LCB5KzQsIHIsIHIqMC43LCAwLCAwLCBNYXRoLlBJKjIpOyBjdHguZmlsbCgpOwogICAgICAgIGN0eC5maWxsU3R5bGUgPSBjZmcud2VhdGhlciA9PT0gImljZSIgPyAiIzIzNDAzMyIgOiAiIzIxNGUyMSI7IGN0eC5iZWdpblBhdGgoKTsgY3R4LmFyYyh4LCB5LCByLCAwLCBNYXRoLlBJKjIpOyBjdHguZmlsbCgpOwogICAgICAgIGN0eC5maWxsU3R5bGUgPSBjZmcud2VhdGhlciA9PT0gImljZSIgPyAiIzM4NjM1MCIgOiAiIzJlNjgyZSI7IGN0eC5iZWdpblBhdGgoKTsgY3R4LmFyYyh4LXIqMC4yLCB5LXIqMC4yLCByKjAuNjUsIDAsIE1hdGguUEkqMik7IGN0eC5maWxsKCk7CiAgICB9CgogICAgZnVuY3Rpb24gY3JlYXRlU3BhcmtzKHgsIHkpIHsKICAgICAgICBmb3IobGV0IGk9MDtpPDY7aSsrKSB7IHNwYXJrcy5wdXNoKHt4OngsIHk6eSwgdng6KE1hdGgucmFuZG9tKCktMC41KSo4LCB2eTooTWF0aC5yYW5kb20oKS0wLjUpKjgsIGxpZmU6MS4wLCBjb2xvcjpNYXRoLnJhbmRvbSgpPjAuNTsiI2YxYzQwZiI6IiNlNjdlMjIifSk7IH0KICAgIH0KCiAgICBmdW5jdGlvbiByZW5kZXJTcGFya3MoKSB7CiAgICAgICAgZm9yKGxldCBpPXNwYXJrcy5sZW5ndGgtMTtpPj0wO2ktLSl7CiAgICAgICAgICAgIGxldCBwPXNwYXJrc1tpXTsgcC54Kz1wLnZ4OyBwLnkrPXAudnk7IHAubGlmZS09MC4wNjsKICAgICAgICAgICAgaWYocC5saWZlPD0wKXsgc3BhcmtzLnNwbGljZShpLDEpOyBjb250aW51ZTsgfQogICAgICAgICAgICBjdHguZmlsbFN0eWxlPXAuY29sb3I7IGN0eC5nbG9iYWxBbHBoYT1wLmxpZmU7IGN0eC5iZWdpblBhdGgoKTsgY3R4LmFyYygucC54LHAueSwzLDAsTWF0aC5QSSpSKTsgY3R4LmZpbGwoKTsgY3R4Lmdsb2JhbEFscGhhPTEuMDsKICAgICAgICB9CiAgICB9CgogICAgZnVuY3Rpb24gZHJhd0ZyYW1lKHApIHsKICAgICAgICBjdHguY2xlYXJSZWN0KDAsMCxjYW52YXMud2lkdGgsY2FudmFzLmhlaWdodCk7CiAgICAgICAgdHJlZXMuZm9yRWFjaCh0PT5kcmF3VHJlZSgudC54LHQueSx0LnIpKTsKCiAgICAgICAgbGV0IHJvYWRDb2xvcj0iIzJjM2U1MCI7CiAgICAgICAgaWYoY2ZnLndlYXRoZXI9PT0icmFpbiIpIHJvYWRDb2xvcj0iIzEyMTkyMSI7CiAgICAgICAgaWYoY2ZnLndlYXRoZXI9PT0iaWNlIikgcm9hZENvbG9yPSIjMmIzZTUwIjsKCiAgICAgICAgY3R4LmJlZ2luUGF0aCgpOyBjdHguZWxsaXBzZShjZW50ZXJYLGNlbnRlclkscmFkaXVzWCxyYWRpdXNZLDAsLU1hdGguUEkvMiwwLGZhbHNlKTsgY3R4LmxpbmVXaWR0aD1yb2FkV2lkdGgrMTA7IGN0eC5zdHJva2VTdHlsZT0iI2MwMzkyYiI7IGN0eC5zdHJva2UoKTsKICAgICAgICBjdHguYmVnaW5QYXRoKCk7IGN0eC5lbGxpcHNlKGNlbnRlclgsY2VudGVyWSxyYWRpdXNYLHJhZGl1c1ksMCwtTWF0aC5QSS8yLDAsZmFsc2UpOyBjdHgubGluZVdpZHRoPXJvYWRXaWR0aDsgY3R4LnN0cm9rZVN0eWxlPXJvYWRDb2xvcjsgY3R4LnN0cm9rZSgpOwoKICAgICAgICBpZihjZmcud2VhdGhlcj09PSJyYWluIil7CiAgICAgICAgICAgIGN0eC5zYXZlKCk7IGN0eC5saW5lV2lkdGg9cm9hZFdpZHRoLTEyOyBjdHguc3Ryb2tlU3R5bGU9InJnYmEoMTAwLDE1MCwyMDAsMC4xOCkiOyBjdHguc2V0TGluZURhc2goWzYwLDQwLDIwLDUwXSk7CiAgICAgICAgICAgIGN0eC5iZWdpblBhdGgoKTsgY3R4LmVsbGlwc2UoY2VudGVyWCxjZW50ZXJZLHJhZGl1c1gscmFkaXVzWSwwLC1NYXRoLlBJLzIsMCxmYWxzZSk7IGN0eC5zdHJva2UoKTsKICAgICAgICAgICAgY3R4LmxpbmVXaWR0aD0xNDsgY3R4LnN0cm9rZVN0eWxlPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMjUpIjsgY3R4LnNldExpbmVEYXNoKFsxNSw4MCwzMCw2MF0pOwogICAgICAgICAgICBjdHguYmVnaW5QYXRoKCk7IGN0eC5lbGxpcHNlKGNlbnRlclgsY2VudGVyWSxyYWRpdXNYKzE4LHJhZGl1c1krMTgsMCwtTWF0aC5QSS8yLDAsZmFsc2UpOyBjdHguc3Ryb2tlKCk7IGN0eC5yZXN0b3JlKCk7CiAgICAgICAgICAgIHJhaW5SaXBwbGVzLmZvckVhY2gocnA9PnsKICAgICAgICAgICAgICAgIGN0eC5zdHJva2VTdHlsZT0icmdiYSgyMDAsMjMwLDI1NSwiKyhycC5hbHBoYSowLjUpKyIpIjsgY3R4LmxpbmVXaWR0aD0xLjU7IGN0eC5iZWdpblBhdGgoKTsgY3R4LmFyYyhycC54LHJwLnkscnAuciwwLE1hdGguUEkqMik7IGN0eC5zdHJva2UoKTsKICAgICAgICAgICAgICAgIHJwLnIrPTAuNDsgcnAuYWxwaGEtPTAuMDE1OwogICAgICAgICAgICAgICAgaWYocnAud2lkdGg8PTApe3JwLnI9MTsgcnAuYWxwaGE9MC44OyBycC54PTIwMCtNYXRoLnJhbmRvbSgpKjQ1MDsgcnAueT04MCtNYXRoLnJhbmRvbSgpKjMwMDsgfQogICAgICAgICAgICB9KTsKICAgICAgICB9IGVsc2UgaWYoY2ZnLndlYXRoZXI9PT0iaWNlIil7CiAgICAgICAgICAgIGN0eC5zYXZlKCk7IGN0eC5saW5lV2lkdGg9cm9hZFdpZHRoLTY7IGN0eC5zdHJva2VTdHlsZT0icmdiYSgyMzYsMjQwLDI0MSwwLjQyKSI7IGN0eC5zZXRMaW5lRGFzaChbMjUsMTUsOCwzMCw0MF0pOwogICAgICAgICAgICBjdHguYmVnaW5QYXRoKCk7IGN0eC5lbGxpcHNlKGNlbnRlclgsY2VudGVyWSxyYWRpdXNYLHJhZGl1c1ksMCwtTWF0aC5QSS8yLDAsZmFsc2UpOyBjdHguc3Ryb2tlKCk7CiAgICAgICAgICAgIGN0eC5saW5lV2lkdGg9MTA7IGN0eC5zdHJva2VTdHlsZT0icmdiYSgyNTUsMjU1LDI1NSwwLjY1KSI7IGN0eC5zZXRMaW5lRGFzaChbNiwzNSwxMiw1MF0pOwogICAgICAgICAgICBjdHguYmVnaW5QYXRoKCk7IGN0eC5lbGxpcHNlKGNlbnRlclgsY2VudGVyWSxyYWRpdXNYKzIyLHJhZGl1c1krMjIsMCwtTWF0aC5QSS8yLDAsZmFsc2UpOyBjdHguc3Ryb2tlKCk7CiAgICAgICAgICAgIGN0eC5iZWdpblBhdGgoKTsgY3R4LmVsbGlwc2UoY2VudGVyWCxjZW50ZXJZLHJhZGl1c1gtMjIscmFkaXVzWS0yMiwwLC1NYXRoLlBJLzIsMCxmYWxzZSk7IGN0eC5zdHJva2UoKTsgY3R4LnJlc3RvcmUoKTsKICAgICAgICB9CgogICAgICAgIGN0eC5iZWdpblBhdGgoKTsgY3R4LmVsbGlwc2UoY2VudGVyWCxjZW50ZXJZLHJhZGl1c1gscmFkaXVzWSwwLC1NYXRoLlBJLzIsMCxmYWxzZSk7IGN0eC5saW5lV2lkdGg9MzsgY3R4LnNldExpbmVEYXNoKFsxOCwxNl0pOyBjdHguc3Ryb2tlU3R5bGU9IiNmMWM0MGYiOyBjdHguc3Ryb2tlKCk7IGN0eC5zZXRMaW5lRGFzaChbXSk7CiAgICAgICAgY29uc3QgZ3VhcmRSeD1yYWRpdXNYK3JvYWRXaWR0aC8yKzQsIGd1YXJkUnk9cmFkaXVzWStyb2FkV2lkdGgvMis0OyBjdHguYmVnaW5QYXRoKCk7IGN0eC5lbGxpcHNlKGNlbnRlclgsY2VudGVyWSxndWFyZFJ4LGd1YXJkUnksMCwtTWF0aC5QSS8yLDAsZmFsc2UpOyBjdHgubGluZVdpZHRoPTY7IGN0eC5zdHJva2VTdHlsZT0iIzk1YTVhNiI7IGN0eC5zdHJva2UoKTsKICAgICAgICBmb3IobGV0IGE9LU1hdGguUEkvMjthPD0wO2ErPTAuMSl7IGxldCBweD1jZW50ZXJYK2d1YXJkUnhNYXRoLmNvcyhhKSwgcHk9Y2VudGVyWStndWFyZFJ5Kk1hdGguc2luKGEpOyBjdHguZmlsbFN0eWxlPSIjN2Y4YzhkIjsgY3R4LmZpbGxSZWN0KHB4LTMscHktMyw2LDYpOyB9CgogICAgICAgIGxldCBjYXJYLGNhclksY2FyQW5nbGUsaXNDb2xsaWRlZD1mYWxzZSxzbGlwUG9pbnQ9MC40NTsKICAgICAgICBpZihjZmcuaXNfc2FmZSB8fCBwPD1zbGlwUG9pbnQpewogICAgICAgICAgICBjb25zdCBhbmdsZT0tTWF0aC5QSS8yKyhNYXRoLlBJLzIpKnA7IGNvbnN0IHB0PWdldEVsbGlwc2VQb2ludChhbmdsZSk7IGNhclg9cHQueDsgY2FyWT1wdC55OyBjYXJBbmdsZT1wdC50YW5nZW50QW5nbGU7CiAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgY29uc3QgYW5nbGU9LU1hdGguUEkvMisoTWF0aC5QSS8yKSpzbGlwUG9pbnQ7IGNvbnN0IHB0PWdldEVsbGlwc2VQb2ludChhbmdsZSk7CiAgICAgICAgICAgIGNvbnN0IG92ZXI9KHAtc2xpcFBvaW50KSozODA7IGxldCB0ZXN0WD1wdC54K01hdGguY29zKHB0LnRhbmdlbnRBbmdsZSkqb3ZlciwgdGVzdFk9cHQueStNYXRoLnNpbihwdC50YW5nZW50QW5nbGUpKm92ZXI7CiAgICAgICAgICAgIGxldCBub3JtRGlzdD1NYXRoLnBvdygodGVzdFgtY2VudGVyWCkvZ3VhcmRSeCwyKStNYXRoLnBvdygodGVzdFktY2VudGVyWSkvZ3VhcmRSeSwyKTsKICAgICAgICAgICAgaWYobm9ybURpc3Q+PTAuOTYpeyBpc0NvbGxpZGVkPXRydWU7IGNhclg9dGVzdFg7IGNhclk9dGVzdFk7IGNhckFuZ2xlPXB0LnRhbmdlbnRBbmdsZSswLjM1OyBjcmVhdGVTcGFya3MoY2FyWCxjYXJZKTsgfQogICAgICAgICAgICBlbHNlIHsgY2FyWD10ZXN0WDsgY2FyWT10ZXN0WTsgY2FyQW5nbGU9cHQudGFuZ2VudEFuZ2xlOyB9CiAgICAgICAgfQoKICAgICAgICBjdHguc2F2ZSgpOyBjdHgudHJhbnNsYXRlKGNhclgsY2FyWTspOyBjdHgucm90YXRlKGNhckFuZ2xlKTsgY29uc3QgY2FyVz00NiwgY2FySD0yNDsKICAgICAgICBjdHguZmlsbFN0eWxlPSIjMTExIjsgY3R4LmZpbGxSZWN0KC1jYXJXLzIrNixjYXJILzItMywxMCw0KTsgY3R4LmZpbGxSZWN0KGNhclddLzItMTYsY2FySC8yLTMsMTAsNCk7IGN0eC5maWxsUmVjdCgtY2FyVy8yKzYsY2FySC8yLTEsMTAsNCk7IGN0eC5maWxsUmVjdChjYXJXLzItMTYsY2FySC8yLTEsMTAsNCk7CiAgICAgICAgY3R4LmZpbGxTdHlsZT1pc0NvbGxpZGVkPyIjZTc0YzNjIjooY2ZnLmlzX3NhZmU/IiMyZWNjNzEiOiIjZTY3ZTIyIik7IGN0eC5iZWdpblBhdGgoKTsKICAgICAgICBpZihjdHgucm91bmRSZWN0KXtjdHgucm91bmRSZWN0KC1jYXJXLzIsLWNhckgvMixjYXJXLGNhckgsNik7fWVsc2V7Y3R4LnJlY3QoLWNhclcvMiwtY2FySC8yLGNhclcsY2FySDkpO30gY3R4LmZpbGwoKTsKICAgICAgICBjdHguZmlsbFN0eWxlPSIjMWUyNzJlIjsgY3R4LmZpbGxSZWN0KC1jYXJXLzYsLWNhckgvMiszLGNhclddLzMsY2FySC02KTsgY3R4LmZpbGxTdHlsZT0iI2YxYzQwZiI7IGN0eC5maWxsUmVjdChjYXJXLzItMiwtY2FySC8yKzMsMyw0KTsgY3R4LmZpbGxSZWN0KGNhclddLzItMixjYXJILzItNywzLDQpOyBjdHgucmVzdG9yZSgpOwoKICAgICAgICByZW5kZXJTcGFya3MoKTsgY3R4LmZvbnQ9ImJvbGQgMTZweCBzYW5zLXNlcmlmIjsKICAgICAgICBpZihpc0NvbGxpZGVkKXsgY3R4LmZpbGxTdHlsZT0iI2U3NGMzYyI7IGN0eC5maWxsVGV4dCgi8J+SpSDsmbjqsLsg6rCAdOultO2EvCDstqnrjrEg6LCY7IOdISIsIDIwLCAzNSk7IH0KICAgICAgICBlbHNlIGlmKHA+MCAmJiAhY2ZnLmlzX3NhZmUgJiYgcD5zbGlwUG9pbnQpeyBjdHguZmlsbFN0eWxlPSIjZTY3ZTIyIjsgY3R4LmZpbGxUZXh0KCLimqDvuI8g7JuQ7I2s6XvOuhnCDrj4TrgZwg7I207I6EIOyjkS4uLiIsIDIwLCAzNSk7IH0KICAgICAgICBlbHNlIGlmKHA+MCl7IGN0eC5maWxsU3R5bGU9IiMyZWNjNzEiOyBjdHguZmlsbFRleHQoIvCfpI0g6rOg73a64-EIOyEseq3uCDsub3rgI3tqLkg7K24IiwgMjAsIDM1KTsgfQogICAgICAgIGVsc2UgewogICAgICAgICAgICBjdHguZmlsbFN0eWxlPSIjZmZmIjsgY3R4LmZpbGxUZXh0KCLwn6SNIOyLnOtdqOugiOydtO2CgCDrjI3quLDsoqkg7K24IiwgMjAsIDM1KTsgfQogICAgfQoKICAgIGZ1bmN0aW9uIHN0ZXAoKXsKICAgICAgICBpZighaXNSdW5uaW5nKSByZXR1cm47CiAgICAgICAgY29uc3Qgc3BlZWQ9MC4wMDMrKGNmZy51c2VyX3NwZWVkLzE1MCkqMC4wMDc7IHByb2dyZXNzKz1zcGVlZDsKICAgICAgICBpZihwcm9ncmVzcz4xLjI1KXsgcHJvZ3Jlc3M9MS4yNTsgZHJhd0ZyYW1lKHByb2dyZXNzKTsgaXNSdW5uaW5nPWZhbHNlOyByZXR1cm47IH0KICAgICAgICBkcmF3RnJhbWUocHJvZ3Jlc3MpOyBhbmltSWQ9cmVxdWVzdEFuaW1hdGlvbkZyYW1lKHN0ZXApOwogICAgfQoKICAgIHN0YXJ0QnRuLmFkZEV2ZW50TGlzdGVuZXIoImNsaWNrIiwgZnVuY3Rpb24oKXsgaWYoYW5pbUlkKSBjYW5jZWxBbmltYXRpb25GcmFtZShhbmltSWQpOyBzcGFya3M9W107IHByb2dyZXNzPTA7IGlzUnVubmluZz10cnVlOyBzdGVwKCk7IH0pOwogICAgZHJhd0ZyYW1lKDApOwohfSkoKTsKPC9zY3JpcHQ+CjwvYm9keT4KPC9odG1sPg=="

# Base64 디코딩 후 파라미터 안전 결합
html_code = base64.b64decode(b64_html_template).decode('utf-8')
rendered_html = html_code.replace("__CFG_JSON__", json.dumps(sim_params))

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
