import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

st.set_page_config(page_title="F1 Telemetry AI", page_icon="🏎️", layout="wide")

# --- SELEÇÃO DE IDIOMA ---
idioma_selecionado = st.sidebar.radio("🌐 Language / Idioma:", ["🇧🇷 Português", "🇨🇦 English"])
is_pt = idioma_selecionado == "🇧🇷 Português"

t = {
    "titulo": "🏎️ IA de Previsão de Telemetria F1" if is_pt else "🏎️ F1 Telemetry Prediction AI",
    "subtitulo": "Ajuste os controles e veja a rede neural (LSTM) prevendo a inércia em tempo real." if is_pt else "Adjust controls and watch the neural network (LSTM) predict inertia in real-time.",
    "config_cloud": "⚙️ Conexão Cloud" if is_pt else "⚙️ Cloud Connection",
    "controles": "🕹️ Controles do Piloto" if is_pt else "🕹️ Driver Controls (Current)",
    "simule": "Simule a entrada na curva:" if is_pt else "Simulate corner entry:",
    "vel": "Velocidade (km/h)" if is_pt else "Speed (km/h)",
    "rpm": "Motor (RPM)" if is_pt else "Engine (RPM)",
    "marcha": "Marcha" if is_pt else "Gear",
    "acel": "Aceleração (G)" if is_pt else "Acceleration (G)",
    "status_ia": "Status do Motor IA" if is_pt else "AI Engine Status",
    "latencia": "ms" if is_pt else "ms",
    "vel_agora": "Sua Velocidade (Agora)" if is_pt else "Your Speed (Now)",
    "prev_futuro": "Previsão da IA (Futuro)" if is_pt else "AI Prediction (Future)",
    "ms_legenda": "Milissegundos" if is_pt else "Milliseconds",
    "limpar": "🔄 Limpar Dados / Reset Data" if is_pt else "🔄 Reset Data / Limpar Dados"
}

st.title(t["titulo"])
st.markdown(t["subtitulo"])

def resetar_dados():
    st.session_state["slider_vel"] = 170.0
    st.session_state["slider_rpm"] = 10500.0
    st.session_state["slider_marcha"] = 4.0
    st.session_state["slider_acel"] = -2.0
    if 'dados_historicos' in st.session_state:
        del st.session_state['dados_historicos']

if 'dados_historicos' not in st.session_state:
    st.session_state['dados_historicos'] = [
        {"velocidade": 315.0, "rpm": 11500.0, "marcha": 8.0, "aceleracao": -0.5},
        {"velocidade": 310.0, "rpm": 11300.0, "marcha": 8.0, "aceleracao": -1.2},
        {"velocidade": 302.0, "rpm": 11000.0, "marcha": 8.0, "aceleracao": -2.5},
        {"velocidade": 290.0, "rpm": 10500.0, "marcha": 7.0, "aceleracao": -3.8},
        {"velocidade": 275.0, "rpm": 12000.0, "marcha": 7.0, "aceleracao": -4.2},
        {"velocidade": 255.0, "rpm": 11500.0, "marcha": 6.0, "aceleracao": -4.5},
        {"velocidade": 230.0, "rpm": 10800.0, "marcha": 6.0, "aceleracao": -4.8},
        {"velocidade": 205.0, "rpm": 12200.0, "marcha": 5.0, "aceleracao": -4.5},
        {"velocidade": 185.0, "rpm": 11500.0, "marcha": 5.0, "aceleracao": -3.5},
    ]

with st.sidebar:
    st.header(t["config_cloud"])
    api_url = st.text_input("URL (GCP):", value="https://f1-telemetry-api-50878659952.us-central1.run.app/prever")
    
    st.markdown("---")
    st.header(t["controles"])
    
    vel_atual = st.slider(t["vel"], 50.0, 350.0, 170.0, step=1.0, key="slider_vel")
    rpm_atual = st.slider(t["rpm"], 5000.0, 13000.0, 10500.0, step=100.0, key="slider_rpm")
    marcha_atual = st.slider(t["marcha"], 1.0, 8.0, 4.0, step=1.0, key="slider_marcha")
    acel_atual = st.slider(t["acel"], -5.0, 2.0, -2.0, step=0.1, key="slider_acel")
    
    st.button(t["limpar"], type="secondary", use_container_width=True, on_click=resetar_dados)

ponto_dinamico = {"velocidade": vel_atual, "rpm": rpm_atual, "marcha": marcha_atual, "aceleracao": acel_atual}
janela_completa = st.session_state['dados_historicos'] + [ponto_dinamico]

df = pd.DataFrame(janela_completa)
df.index.name = t["ms_legenda"]

# --- API ---
inicio = time.time()
velocidade_prev = vel_atual
sucesso_api = False
latencia_ms = 0

try:
    resposta = requests.post(api_url, json={"pontos": janela_completa})
    latencia_ms = round((time.time() - inicio) * 1000)
    if resposta.status_code == 200:
        velocidade_prev = resposta.json().get("velocidade_prevista_kmh", vel_atual)
        sucesso_api = True
except:
    pass

col1, col2, col3 = st.columns(3)
col1.metric(t["status_ia"], "Online 🟢" if sucesso_api else "Offline 🔴", f"{latencia_ms} {t['latencia']}")
col2.metric(t["vel_agora"], f"{vel_atual} km/h")
col3.metric(t["prev_futuro"], f"{velocidade_prev} km/h", delta=round(velocidade_prev - vel_atual, 2))

# --- COORDENADAS DO CIRCUITO (S DO SENNA) ---
df["X"] = [0, -5, -15, -28, -45, -65, -88, -112, -135, -155]
df["Y"] = [500, 460, 420, 380, 340, 300, 260, 220, 180, 140]

st.markdown("---")
col_grafico1, col_grafico2 = st.columns(2)

with col_grafico1:
    st.subheader("📊 Telemetria do Motor" if is_pt else "📊 Engine Telemetry")
    fig_linhas = make_subplots(specs=[[{"secondary_y": True}]])
    fig_linhas.add_trace(go.Scatter(x=df.index, y=df['rpm'], name='RPM', line=dict(color='#87CEEB', width=3)), secondary_y=False)
    fig_linhas.add_trace(go.Scatter(x=df.index, y=df['velocidade'], name=t['vel'], line=dict(color='#0056b3', width=3)), secondary_y=True)
    fig_linhas.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_linhas, use_container_width=True)

with col_grafico2:
    st.subheader("🗺️ Visão do Circuito (GPS)" if is_pt else "🗺️ Circuit View (GPS)")
    fig_mapa = go.Figure()
    
    # Rastro Passado
    fig_mapa.add_trace(go.Scatter(
        x=df["X"][:9], y=df["Y"][:9], mode='lines+markers', name='Passado', 
        line=dict(color='lightgray', width=3), marker=dict(size=6, color='gray')
    ))
    
    # Coordenadas do Presente
    px_atual = df["X"].iloc[9]
    py_atual = df["Y"].iloc[9]
    
    # Coordenadas do Futuro Amplificadas (Sensível ao Slider de Aceleração e Velocidade)
    # Transforma a aceleração de -5.0 a +2.0 em um multiplicador de distância dramático
    intensidade_inercia = ((acel_atual + 5) / 7.0) * 1.5 + (velocidade_prev / 200.0)
    distancia_projetada = 20 + (35 * intensidade_inercia)
    
    futuro_x = px_atual - (distancia_projetada * 0.7)
    futuro_y = py_atual - (distancia_projetada * 1.0)
    
    # 1. A LINHA DE CONEXÃO (Vetor de Inércia)
    fig_mapa.add_trace(go.Scatter(
        x=[px_atual, futuro_x], y=[py_atual, futuro_y], mode='lines', 
        name='Vetor' if is_pt else 'Vector', 
        line=dict(color='orange', width=2, dash='dot')
    ))
    
    # 2. Ponto Presente
    fig_mapa.add_trace(go.Scatter(
        x=[px_atual], y=[py_atual], mode='markers', name='Presente', 
        marker=dict(color='#0056b3', size=16, line=dict(color='white', width=2))
    ))

    # 3. Ponto Futuro (Estrela)
    fig_mapa.add_trace(go.Scatter(
        x=[futuro_x], y=[futuro_y], mode='markers', name='Futuro (IA)', 
        marker=dict(color='red', size=22, symbol='star', line=dict(color='yellow', width=2))
    ))

    fig_mapa.update_layout(
        height=400, margin=dict(l=0, r=0, t=30, b=0), 
        xaxis=dict(visible=False, showgrid=False, range=[-250, 20]), 
        yaxis=dict(visible=False, showgrid=False, range=[50, 520]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_mapa, use_container_width=True)

st.markdown("---")
with st.expander("🔎 Ver Matriz de Dados Enviada para a IA" if is_pt else "🔎 View Raw Data Matrix"):
    st.dataframe(df[["velocidade", "rpm", "marcha", "aceleracao"]], use_container_width=True)