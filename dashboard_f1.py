import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="F1 Telemetry AI - Interlagos", page_icon="🏎️", layout="wide")

# --- UI TRANSLATIONS ---
idioma_selecionado = st.sidebar.radio("🌐 Language / Idioma:", ["🇧🇷 Português", "🇨🇦 English"])
is_pt = idioma_selecionado == "🇧🇷 Português"

t = {
    "titulo": "🏎️ IA de Previsão F1: O Desafio do 'S do Senna'" if is_pt else "🏎️ F1 Prediction AI: The 'Senna S' Challenge",
    "subtitulo": "Cenário: Max Verstappen | Interlagos 2023. Você está a 330 km/h. Assuma os controles e tente fazer a curva." if is_pt else "Scenario: Max Verstappen | Interlagos 2023. You are at 330 km/h. Take the controls and try to make the corner.",
    "controles": "🕹️ Controles da Frenagem" if is_pt else "🕹️ Braking Controls",
    "vel": "Redução Alvo (km/h)" if is_pt else "Target Speed (km/h)",
    "acel": "Acelerador (%)" if is_pt else "Throttle (%)",
    "status_ia": "Status do Motor IA" if is_pt else "AI Engine Status",
    "prev_futuro": "Velocidade no Ápice (LSTM)" if is_pt else "Apex Speed (LSTM)",
    "saiu_pista": "⚠️ ACIDENTE! Velocidade no ápice muito alta (>160 km/h). A inércia jogou o carro para a área de escape!" if is_pt else "⚠️ CRASH! Apex speed too high (>160 km/h). Inertia threw the car into the runoff area!",
    "curva_ok": "✅ Tangência perfeita! Você sobreviveu ao S do Senna." if is_pt else "✅ Perfect apex! You survived the Senna S.",
    "muito_lento": "⚠️ Muito lento! Você perdeu o *momentum* da corrida." if is_pt else "⚠️ Too slow! You lost race momentum.",
}

st.title(t["titulo"])
st.markdown(f"**{t['subtitulo']}**")

# --- INTERLAGOS 2023 APPROACH (FIXED HISTORY) ---
# The extreme high-speed approach down the pit straight before braking.
approach_history = [
    {"velocidade": 320.0, "rpm": 11800.0, "marcha": 8.0, "aceleracao": 100.0},
    {"velocidade": 325.0, "rpm": 12000.0, "marcha": 8.0, "aceleracao": 100.0},
    {"velocidade": 328.0, "rpm": 12200.0, "marcha": 8.0, "aceleracao": 100.0},
    {"velocidade": 330.0, "rpm": 12300.0, "marcha": 8.0, "aceleracao": 100.0},
    {"velocidade": 331.0, "rpm": 12400.0, "marcha": 8.0, "aceleracao": 100.0},
    {"velocidade": 331.0, "rpm": 12400.0, "marcha": 8.0, "aceleracao": 100.0},
    {"velocidade": 331.0, "rpm": 12400.0, "marcha": 8.0, "aceleracao": 100.0},
    {"velocidade": 331.0, "rpm": 12400.0, "marcha": 8.0, "aceleracao": 100.0},
    {"velocidade": 331.0, "rpm": 12400.0, "marcha": 8.0, "aceleracao": 100.0},
]

# --- SIDEBAR: DRIVER INPUT ---
with st.sidebar:
    st.header(t["controles"])
    st.markdown("📍 **Ponto de Frenagem: 100m**" if is_pt else "📍 **Braking Board: 100m**")
    
    vel_atual = st.slider(t["vel"], 80.0, 330.0, 140.0, step=1.0)
    rpm_atual = st.slider("Motor (RPM)", 5000.0, 13000.0, 10500.0, step=100.0)
    marcha_atual = st.slider("Marcha / Gear", 1.0, 8.0, 3.0, step=1.0)
    acel_atual = st.slider(t["acel"], 0.0, 100.0, 0.0, step=1.0)
    
    api_url = st.text_input("GCP Endpoint:", value="http://127.0.0.1:8000/prever")

# --- CONSTRUCT PAYLOAD ---
janela_completa = approach_history.copy()
ponto_dinamico = {"velocidade": vel_atual, "rpm": rpm_atual, "marcha": marcha_atual, "aceleracao": acel_atual}
janela_completa.append(ponto_dinamico)

df = pd.DataFrame(janela_completa)
df.index.name = "ms"

# --- API CALL ---
inicio = time.time()
velocidade_prev = vel_atual
sucesso_api = False

try:
    resposta = requests.post(api_url, json={"pontos": janela_completa})
    if resposta.status_code == 200:
        velocidade_prev = resposta.json().get("velocidade_prevista_kmh", vel_atual)
        sucesso_api = True
except:
    pass

# --- METRICS & ANOMALY LOGIC ---
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
col1.metric(t["status_ia"], "Online 🟢" if sucesso_api else "Offline 🔴")
col2.metric("Approaching Speed", "331.0 km/h")
col3.metric("Your Input (Braking)", f"{vel_atual} km/h")
col4.metric(t["prev_futuro"], f"{velocidade_prev:.1f} km/h", delta=round(velocidade_prev - vel_atual, 2))

# --- TRACK MAPPING (SENNA S) ---
# Coordinates adjusted specifically to mimic the sharp left-hand dive of Turn 1 at Interlagos
track_x = [-50, -30, -10, 0, 5, 10, 15, 30, 50, 70]
track_y = [100, 100, 100, 95, 85, 65, 45, 30, 20, 15]

df["X"] = [-150, -130, -110, -90, -70, -50, -30, -20, -10, 0]
df["Y"] = [100, 100, 100, 100, 100, 100, 100, 100, 100, 95]

st.markdown("---")
col_grafico1, col_grafico2 = st.columns(2)

with col_grafico1:
    st.subheader("📊 Telemetry: High-Speed Approach")
    fig_linhas = make_subplots(specs=[[{"secondary_y": True}]])
    fig_linhas.add_trace(go.Scatter(x=df.index, y=df['rpm'], name='RPM', line=dict(color='#87CEEB', width=4)), secondary_y=False)
    fig_linhas.add_trace(go.Scatter(x=df.index, y=df['velocidade'], name='Speed', line=dict(color='#0056b3', width=4)), secondary_y=True)
    fig_linhas.update_layout(height=450, margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig_linhas, use_container_width=True)

with col_grafico2:
    st.subheader("🗺️ Interlagos GPS - Turn 1")
    fig_mapa = go.Figure()
    
    # Track limits
    fig_mapa.add_trace(go.Scatter(x=track_x, y=track_y, mode='lines', hoverinfo='skip', showlegend=False, line=dict(color='rgba(200, 200, 200, 0.4)', width=40, shape='spline')))
    fig_mapa.add_trace(go.Scatter(x=track_x, y=track_y, mode='lines', hoverinfo='skip', showlegend=False, line=dict(color='white', width=2, dash='dot', shape='spline')))
    
    # Approach Trajectory
    fig_mapa.add_trace(go.Scatter(x=df["X"][:9], y=df["Y"][:9], mode='lines+markers', name='Approach', line=dict(color='lightgray', width=3), marker=dict(size=6)))
    
    # Physics Overlay: The 160 km/h limit for the Senna S
    px_atual, py_atual = df["X"].iloc[9], df["Y"].iloc[9]
    excesso_velocidade = max(0, velocidade_prev - 160)
    fator_saida_pista = min(1.0, excesso_velocidade / 30.0) 
    
    curva_dx, curva_dy = 15, -40
    reto_dx, reto_dy = 40, -5
    
    dx_final = curva_dx * (1 - fator_saida_pista) + reto_dx * fator_saida_pista
    dy_final = curva_dy * (1 - fator_saida_pista) + reto_dy * fator_saida_pista
    
    futuro_x = px_atual + dx_final * (velocidade_prev / 150)
    futuro_y = py_atual + dy_final * (velocidade_prev / 150)
    
    fig_mapa.add_trace(go.Scatter(x=[px_atual, futuro_x], y=[py_atual, futuro_y], mode='lines', name='LSTM Projection', line=dict(color='orange', width=2, dash='dash')))
    fig_mapa.add_trace(go.Scatter(x=[px_atual], y=[py_atual], mode='markers+text', name='Braking Point', text=["Turn-in"], textposition="top center", marker=dict(color='#3498db', size=16)))
    fig_mapa.add_trace(go.Scatter(x=[futuro_x], y=[futuro_y], mode='markers', name='Apex Prediction', marker=dict(color='#e74c3c', size=22, symbol='star')))

    fig_mapa.update_layout(height=450, margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='#1e1e1e', paper_bgcolor='#1e1e1e', font=dict(color='white'), xaxis=dict(visible=False), yaxis=dict(visible=False), legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig_mapa, use_container_width=True)

    if velocidade_prev > 160:
        st.error(t["saiu_pista"])
    elif velocidade_prev < 125:
        st.warning(t["muito_lento"])
    else:
        st.success(t["curva_ok"])