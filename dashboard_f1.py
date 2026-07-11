import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="F1 Telemetry AI", page_icon="🏎️", layout="wide")

# --- STREAMING_CHUNK:Configuring Language and Text ---
# --- SELEÇÃO DE IDIOMA ---
idioma_selecionado = st.sidebar.radio("🌐 Language / Idioma:", ["🇧🇷 Português", "🇨🇦 English"])
is_pt = idioma_selecionado == "🇧🇷 Português"

t = {
    "titulo": "🏎️ IA de Previsão e Anomalias F1" if is_pt else "🏎️ F1 Telemetry & Anomaly AI",
    "subtitulo": "Ajuste os controles para ver a rede neural prever o futuro e detectar degradações (anomalias)." if is_pt else "Adjust controls to see the neural network predict the future and detect degradations (anomalies).",
    "config_cloud": "⚙️ Conexão Cloud" if is_pt else "⚙️ Cloud Connection",
    "controles": "🕹️ Controles do Piloto" if is_pt else "🕹️ Driver Controls",
    "vel": "Velocidade Atual (km/h)" if is_pt else "Current Speed (km/h)",
    "acel": "Acelerador (%)" if is_pt else "Accelerator (%)",
    "status_ia": "Status do Motor IA" if is_pt else "AI Engine Status",
    "latencia": "ms" if is_pt else "ms",
    "vel_agora": "Sua Velocidade" if is_pt else "Your Speed",
    "prev_futuro": "Previsão da IA (Baseline)" if is_pt else "AI Prediction (Baseline)",
    "saiu_pista": "⚠️ ACIDENTE! Velocidade muito alta. A inércia jogou o carro para fora da pista!" if is_pt else "⚠️ CRASH! Speed too high. Inertia threw the car off the track!",
    "curva_ok": "✅ Traçado perfeito! O carro tangenciou o ápice." if is_pt else "✅ Perfect line! The car hit the apex.",
    "muito_lento": "⚠️ Muito lento! Você perdeu tempo na curva." if is_pt else "⚠️ Too slow! You lost time in the corner.",
    "limpar": "🔄 Limpar Dados / Reset Data" if is_pt else "🔄 Reset Data / Limpar Dados",
    "erro_residual": "Erro Residual (Desvio)" if is_pt else "Residual Error (Deviation)"
}

st.title(t["titulo"])
st.markdown(t["subtitulo"])

# --- STREAMING_CHUNK:Defining the Base History ---
# --- FUNÇÃO DE RESET ---
def resetar_dados():
    st.session_state["slider_vel"] = 170.0
    st.session_state["slider_rpm"] = 10500.0
    st.session_state["slider_marcha"] = 4.0
    st.session_state["slider_acel"] = 0.0 # Pé fora do acelerador na curva

# --- HISTÓRICO BASE (MOLDE DA CURVA DO VERSTAPPEN) ---
base_historico = [
    {"velocidade": 315.0, "rpm": 11500.0, "marcha": 8.0, "aceleracao": 100.0},
    {"velocidade": 310.0, "rpm": 11300.0, "marcha": 8.0, "aceleracao": 0.0},
    {"velocidade": 302.0, "rpm": 11000.0, "marcha": 8.0, "aceleracao": 0.0},
    {"velocidade": 290.0, "rpm": 10500.0, "marcha": 7.0, "aceleracao": 0.0},
    {"velocidade": 275.0, "rpm": 12000.0, "marcha": 7.0, "aceleracao": 0.0},
    {"velocidade": 255.0, "rpm": 11500.0, "marcha": 6.0, "aceleracao": 0.0},
    {"velocidade": 230.0, "rpm": 10800.0, "marcha": 6.0, "aceleracao": 0.0},
    {"velocidade": 205.0, "rpm": 12200.0, "marcha": 5.0, "aceleracao": 0.0},
    {"velocidade": 185.0, "rpm": 11500.0, "marcha": 5.0, "aceleracao": 0.0},
]

# --- STREAMING_CHUNK:Building the Sidebar ---
# --- BARRA LATERAL (CONTROLES) ---
with st.sidebar:
    st.header(t["config_cloud"])
    api_url = st.text_input("URL (GCP):", value="https://f1-telemetry-api-50878659952.us-central1.run.app/prever")
    
    st.markdown("---")
    st.header(t["controles"])
    
    vel_atual = st.slider(t["vel"], 50.0, 350.0, 170.0, step=1.0, key="slider_vel")
    rpm_atual = st.slider("Motor (RPM)", 5000.0, 13000.0, 10500.0, step=100.0, key="slider_rpm")
    marcha_atual = st.slider("Marcha / Gear", 1.0, 8.0, 4.0, step=1.0, key="slider_marcha")
    acel_atual = st.slider(t["acel"], 0.0, 100.0, 0.0, step=1.0, key="slider_acel")
    
    st.button(t["limpar"], type="secondary", use_container_width=True, on_click=resetar_dados)

# --- STREAMING_CHUNK:Anchoring History and API Call ---
# --- ANCORAGEM DO HISTÓRICO AO PRESENTE ---
shift_vel = vel_atual - 170.0
shift_rpm = rpm_atual - 10500.0

janela_completa = []
for pt in base_historico:
    janela_completa.append({
        "velocidade": max(0.0, pt["velocidade"] + shift_vel),
        "rpm": max(0.0, pt["rpm"] + shift_rpm),
        "marcha": pt["marcha"],
        "aceleracao": pt["aceleracao"]
    })

# Ponto atual do slider
ponto_dinamico = {"velocidade": vel_atual, "rpm": rpm_atual, "marcha": marcha_atual, "aceleracao": acel_atual}
janela_completa.append(ponto_dinamico)

df = pd.DataFrame(janela_completa)
df.index.name = "ms"

# --- CHAMADA PARA A API ---
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

# --- STREAMING_CHUNK:Anomaly Detection Logic ---
# --- AVALIAÇÃO DE MLOPS: DOMÍNIO DE TREINAMENTO (OOD) ---
is_ood = vel_atual < 100.0
if is_ood:
    st.warning("⚠️ **Aviso de MLOps (Out-of-Distribution):** Velocidade abaixo do limite de treinamento. Os neurônios ReLU desativaram e a IA está retornando o Viés (Bias) médio da pista (~175 km/h)." if is_pt else "⚠️ **MLOps Warning (Out-of-Distribution):** Speed below training limits. ReLU neurons died and AI is returning track average Bias (~175 km/h).")

# --- MOTOR DE ANOMALIAS (ERRO RESIDUAL) ---
# Calcula a diferença entre a velocidade real e o baseline (previsão) da IA
erro_residual = abs(vel_atual - velocidade_prev)

# Define os thresholds de anomalia
LIMIAR_ALERTA = 10.0
LIMIAR_CRITICO = 20.0

# --- STREAMING_CHUNK:Rendering the Metrics Panel ---
# --- PAINEL DE MÉTRICAS ---
st.markdown("---")
# Adicionamos uma coluna para o Erro Residual
col1, col2, col3, col4 = st.columns(4)
col1.metric(t["status_ia"], "Online 🟢" if sucesso_api else "Offline 🔴", f"{latencia_ms} {t['latencia']}")
col2.metric(t["vel_agora"], f"{vel_atual} km/h")
col3.metric(t["prev_futuro"], f"{velocidade_prev:.2f} km/h")
# Exibe o erro residual. Usamos delta_color="inverse" para que um erro MAIOR fique vermelho.
col4.metric(
    t["erro_residual"], 
    f"{erro_residual:.2f} km/h", 
    delta=f"{erro_residual:.2f} km/h", 
    delta_color="inverse"
)

# --- AVISOS DE ANOMALIA ---
if sucesso_api:
    if erro_residual > LIMIAR_CRITICO:
        st.error(f"🚨 **ANOMALIA CRÍTICA:** Desvio massivo de {erro_residual:.2f} km/h! Possível perda de tração ou anomalia severa de frenagem." if is_pt else f"🚨 **CRITICAL ANOMALY:** Massive deviation of {erro_residual:.2f} km/h! Possible loss of traction or severe braking anomaly.")
    elif erro_residual > LIMIAR_ALERTA:
        st.warning(f"⚠️ **Aviso de Degradação:** Desvio estatístico de {erro_residual:.2f} km/h detectado. Monitore o desgaste." if is_pt else f"⚠️ **Degradation Warning:** Statistical deviation of {erro_residual:.2f} km/h detected. Monitor wear.")
    else:
         st.success("✅ **Telemetria Normal:** Comportamento alinhado com o baseline do modelo." if is_pt else "✅ **Normal Telemetry:** Behavior aligned with model baseline.")


# --- STREAMING_CHUNK:Rendering the Charts and Map ---
# --- COORDENADAS DO CIRCUITO (ASFALTO E PASSADO) ---
track_x = [-100, -80, -60, -40, -20, 0, 15, 30, 50, 80]
track_y = [100, 100, 100, 100, 100, 95, 80, 50, 20, 10]

df["X"] = [-130, -110, -90, -70, -50, -30, -10, 0, 5, 10]
df["Y"] = [100, 100, 100, 100, 100, 100, 98, 95, 92, 88]

st.markdown("---")
col_grafico1, col_grafico2 = st.columns(2)

# --- GRÁFICO 1: TELEMETRIA (LINHAS) ---
with col_grafico1:
    st.subheader("📊 Telemetria do Motor" if is_pt else "📊 Engine Telemetry")
    fig_linhas = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig_linhas.add_trace(go.Scatter(x=df.index, y=df['rpm'], name='RPM', line=dict(color='#87CEEB', width=4)), secondary_y=False)
    fig_linhas.add_trace(go.Scatter(x=df.index, y=df['velocidade'], name='Velocidade', line=dict(color='#0056b3', width=4)), secondary_y=True)
    
    fig_linhas.update_layout(height=450, margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig_linhas, use_container_width=True)

# --- GRÁFICO 2: MAPA GPS SIMULADO ---
with col_grafico2:
    st.subheader("🗺️ Visão do Circuito (GPS)" if is_pt else "🗺️ Circuit View (GPS)")
    fig_mapa = go.Figure()
    
    fig_mapa.add_trace(go.Scatter(
        x=track_x, y=track_y, mode='lines', hoverinfo='skip', showlegend=False,
        line=dict(color='rgba(200, 200, 200, 0.4)', width=35, shape='spline')
    ))
    fig_mapa.add_trace(go.Scatter(
        x=track_x, y=track_y, mode='lines', hoverinfo='skip', showlegend=False,
        line=dict(color='white', width=2, dash='dot', shape='spline')
    ))
    
    fig_mapa.add_trace(go.Scatter(
        x=df["X"][:9], y=df["Y"][:9], mode='lines+markers', name='Passado', 
        line=dict(color='lightgray', width=3), marker=dict(size=6, color='gray')
    ))
    
    px_atual = df["X"].iloc[9]
    py_atual = df["Y"].iloc[9]
    
    excesso_velocidade = max(0, velocidade_prev - 165)
    fator_saida_pista = min(1.0, excesso_velocidade / 35.0) 
    
    curva_dx, curva_dy = 20, -35
    reto_dx, reto_dy = 35, -5
    
    dx_final = curva_dx * (1 - fator_saida_pista) + reto_dx * fator_saida_pista
    dy_final = curva_dy * (1 - fator_saida_pista) + reto_dy * fator_saida_pista
    
    futuro_x = px_atual + dx_final * (velocidade_prev / 160)
    futuro_y = py_atual + dy_final * (velocidade_prev / 160)
    
    fig_mapa.add_trace(go.Scatter(
        x=[px_atual, futuro_x], y=[py_atual, futuro_y], mode='lines', 
        name='Traçado Projetado', line=dict(color='orange', width=2, dash='dash')
    ))
    
    fig_mapa.add_trace(go.Scatter(
        x=[px_atual], y=[py_atual], mode='markers+text', name='Presente', 
        text=["Ápice"], textposition="top center",
        marker=dict(color='#3498db', size=16, line=dict(color='white', width=2))
    ))

    fig_mapa.add_trace(go.Scatter(
        x=[futuro_x], y=[futuro_y], mode='markers', name='Previsão (IA)', 
        marker=dict(color='#e74c3c', size=22, symbol='star', line=dict(color='yellow', width=2))
    ))

    fig_mapa.update_layout(
        height=450, margin=dict(l=0, r=0, t=30, b=0), 
        plot_bgcolor='#1e1e1e', paper_bgcolor='#1e1e1e', font=dict(color='white'),
        xaxis=dict(visible=False, showgrid=False, range=[-20, 80]), 
        yaxis=dict(visible=False, showgrid=False, range=[10, 110]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig_mapa, use_container_width=True)

    # --- ALERTAS FÍSICOS (Antigos) ---
    # Mantivemos os alertas de inércia originais abaixo do gráfico para manter o comportamento anterior.
    if velocidade_prev > 165:
        st.error(t["saiu_pista"])
    elif velocidade_prev < 155:
        st.warning(t["muito_lento"])
    else:
        st.success(t["curva_ok"])

# --- STREAMING_CHUNK:Rendering the Data Audit Expandable ---
# --- TABELA DE AUDITORIA ---
st.markdown("---")
with st.expander("🔎 Ver Matriz de Dados Enviada para a IA" if is_pt else "🔎 View Raw Data Matrix"):
    st.dataframe(df[["velocidade", "rpm", "marcha", "aceleracao"]], use_container_width=True)