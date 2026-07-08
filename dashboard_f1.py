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
    "subtitulo": "Ajuste os controles e veja a rede neural (LSTM) prever se você consegue fazer a curva." if is_pt else "Adjust controls and watch the LSTM neural network predict if you can make the corner.",
    "controles": "🕹️ Controles do Piloto" if is_pt else "🕹️ Driver Controls",
    "vel": "Velocidade Atual (km/h)" if is_pt else "Current Speed (km/h)",
    "acel": "Pressão no Freio (G)" if is_pt else "Braking Pressure (G)",
    "vel_agora": "Sua Velocidade" if is_pt else "Your Speed",
    "prev_futuro": "Previsão da IA (Futuro)" if is_pt else "AI Prediction (Future)",
    "saiu_pista": "⚠️ ACIDENTE! Velocidade muito alta. A inércia jogou o carro para fora da pista!" if is_pt else "⚠️ CRASH! Speed too high. Inertia threw the car off the track!",
    "curva_ok": "✅ Traçado perfeito! O carro tangenciou o ápice." if is_pt else "✅ Perfect line! The car hit the apex.",
}

st.title(t["titulo"])
st.markdown(t["subtitulo"])

def resetar_dados():
    st.session_state["slider_vel"] = 170.0
    st.session_state["slider_rpm"] = 10500.0
    st.session_state["slider_marcha"] = 4.0
    st.session_state["slider_acel"] = -2.0

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
    api_url = st.text_input("URL (GCP):", value="https://f1-telemetry-api-50878659952.us-central1.run.app/prever")
    st.markdown("---")
    st.header(t["controles"])
    
    vel_atual = st.slider(t["vel"], 50.0, 350.0, 170.0, step=1.0, key="slider_vel")
    rpm_atual = st.slider("Motor (RPM)", 5000.0, 13000.0, 10500.0, step=100.0, key="slider_rpm")
    marcha_atual = st.slider("Marcha / Gear", 1.0, 8.0, 4.0, step=1.0, key="slider_marcha")
    acel_atual = st.slider(t["acel"], -5.0, 2.0, -2.0, step=0.1, key="slider_acel")
    
    st.button("🔄 Reset", type="secondary", use_container_width=True, on_click=resetar_dados)

ponto_dinamico = {"velocidade": vel_atual, "rpm": rpm_atual, "marcha": marcha_atual, "aceleracao": acel_atual}
janela_completa = st.session_state['dados_historicos'] + [ponto_dinamico]
df = pd.DataFrame(janela_completa)

# --- CHAMADA PARA A API ---
velocidade_prev = vel_atual
try:
    resposta = requests.post(api_url, json={"pontos": janela_completa})
    if resposta.status_code == 200:
        velocidade_prev = resposta.json().get("velocidade_prevista_kmh", vel_atual)
except:
    pass

st.markdown("---")
col1, col2 = st.columns(2)
col1.metric(t["vel_agora"], f"{vel_atual} km/h")
col2.metric(t["prev_futuro"], f"{velocidade_prev} km/h", delta=round(velocidade_prev - vel_atual, 2))

# --- COORDENADAS DO CIRCUITO (S DO SENNA SIMULADO) ---
# A reta principal e a entrada da curva à esquerda
track_x = [-100, -80, -60, -40, -20, 0, 15, 30, 50, 80]
track_y = [100, 100, 100, 100, 100, 95, 80, 50, 20, 10]

st.markdown("---")
col_grafico1, col_grafico2 = st.columns(2)

with col_grafico1:
    st.subheader("📊 Telemetria do Motor" if is_pt else "📊 Engine Telemetry")
    fig_linhas = make_subplots(specs=[[{"secondary_y": True}]])
    fig_linhas.add_trace(go.Scatter(x=df.index, y=df['rpm'], name='RPM', line=dict(color='#87CEEB', width=4)), secondary_y=False)
    fig_linhas.add_trace(go.Scatter(x=df.index, y=df['velocidade'], name='Velocidade', line=dict(color='#0056b3', width=4)), secondary_y=True)
    fig_linhas.update_layout(height=450, margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig_linhas, use_container_width=True)

with col_grafico2:
    st.subheader("🗺️ Visão do Circuito (GPS)" if is_pt else "🗺️ Circuit View (GPS)")
    fig_mapa = go.Figure()
    
    # 1. O ASFALTO (Linha grossa simulando a pista)
    fig_mapa.add_trace(go.Scatter(
        x=track_x, y=track_y, mode='lines', hoverinfo='skip', showlegend=False,
        line=dict(color='rgba(200, 200, 200, 0.4)', width=35, shape='spline')
    ))
    # Linha central tracejada
    fig_mapa.add_trace(go.Scatter(
        x=track_x, y=track_y, mode='lines', hoverinfo='skip', showlegend=False,
        line=dict(color='white', width=2, dash='dot', shape='spline')
    ))
    
    # Posição Presente (O Carro)
    px_atual = 10
    py_atual = 88
    
    # --- A FÍSICA DA INÉRCIA ---
    # Velocidade ideal para fazer o Ápice é ~140 km/h. 
    excesso_velocidade = max(0, velocidade_prev - 140)
    # Se passar de 210km/h, sai 100% da pista (understeer)
    fator_saida_pista = min(1.0, excesso_velocidade / 70.0) 
    
    # Vetor Ideal (Fazendo a curva) vs Vetor Tangente (Passando reto)
    curva_dx, curva_dy = 20, -35
    reto_dx, reto_dy = 35, -5
    
    dx_final = curva_dx * (1 - fator_saida_pista) + reto_dx * fator_saida_pista
    dy_final = curva_dy * (1 - fator_saida_pista) + reto_dy * fator_saida_pista
    
    futuro_x = px_atual + dx_final * (velocidade_prev / 130)
    futuro_y = py_atual + dy_final * (velocidade_prev / 130)
    
    # Desenhar Vetor de Inércia
    fig_mapa.add_trace(go.Scatter(
        x=[px_atual, futuro_x], y=[py_atual, futuro_y], mode='lines', 
        name='Traçado Projetado', line=dict(color='orange', width=2, dash='dash')
    ))
    
    # Ponto Presente
    fig_mapa.add_trace(go.Scatter(
        x=[px_atual], y=[py_atual], mode='markers+text', name='Presente', 
        text=["Ápice"], textposition="top center",
        marker=dict(color='#3498db', size=16, line=dict(color='white', width=2))
    ))

    # Ponto Futuro (IA)
    fig_mapa.add_trace(go.Scatter(
        x=[futuro_x], y=[futuro_y], mode='markers', name='Previsão (IA)', 
        marker=dict(color='#e74c3c', size=22, symbol='star', line=dict(color='yellow', width=2))
    ))

    # Estilizando o Mini-Mapa em "Modo Escuro" para parecer telemetria real
    fig_mapa.update_layout(
        height=450, margin=dict(l=0, r=0, t=30, b=0), 
        plot_bgcolor='#1e1e1e', paper_bgcolor='#1e1e1e', font=dict(color='white'),
        xaxis=dict(visible=False, showgrid=False, range=[-20, 80]), 
        yaxis=dict(visible=False, showgrid=False, range=[10, 110]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig_mapa, use_container_width=True)

    # --- ALERTA VISUAL DE SAÍDA DE PISTA ---
    if fator_saida_pista > 0.4:
        st.error(t["saiu_pista"])
    else:
        st.success(t["curva_ok"])