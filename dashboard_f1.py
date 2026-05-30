import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go # Usando Graph Objects para mais controle
from plotly.subplots import make_subplots
import time

# Configuração da página
st.set_page_config(page_title="F1 Telemetry AI", page_icon="🏎️", layout="wide")

# --- SELEÇÃO DE IDIOMA (BILINGUAL TOGGLE) ---
# Adicionado na barra lateral para limpar a interface principal
idioma_selecionado = st.sidebar.radio("🌐 Language / Idioma:", ["🇧🇷 Português", "🇨🇦 English"])
is_pt = idioma_selecionado == "🇧🇷 Português"

# --- DICIONÁRIO DE TRADUÇÕES ---
t = {
    "titulo": "🏎️ IA de Previsão de Telemetria F1" if is_pt else "🏎️ F1 Telemetry Prediction AI",
    "subtitulo": "Ajuste os controles e veja a rede neural (LSTM) prevendo a velocidade em tempo real." if is_pt else "Adjust controls and watch the neural network (LSTM) predict speed in real-time.",
    "config_cloud": "⚙️ Conexão Cloud" if is_pt else "⚙️ Cloud Connection",
    "controles": "🕹️ Controles do Piloto" if is_pt else "🕹️ Driver Controls (Current)",
    "simule": "Simule a entrada na curva:" if is_pt else "Simulate corner entry:",
    "vel": "Velocidade (km/h)" if is_pt else "Speed (km/h)",
    "rpm": "Motor (RPM)" if is_pt else "Engine (RPM)",
    "marcha": "Marcha" if is_pt else "Gear",
    "acel": "Aceleração (G)" if is_pt else "Acceleration (G)",
    "status_ia": "Status do Motor IA" if is_pt else "AI Engine Status",
    "latencia": "ms de latência" if is_pt else "ms latency",
    "vel_agora": "Sua Velocidade (Agora)" if is_pt else "Your Speed (Now)",
    "prev_futuro": "Previsão da IA (Futuro)" if is_pt else "AI Prediction (Future)",
    "tit_grafico": "📈 Telemetria da Janela de Análise (Frenagem)" if is_pt else "📈 Analysis Window Telemetry (Braking)",
    "ms": "Milissegundos" if is_pt else "Milliseconds",
    "erro_servidor": "⚠️ Servidor na nuvem indisponível." if is_pt else "⚠️ Cloud server unavailable.",
    "limpar": "🔄 Limpar Dados / Reset Data" if is_pt else "🔄 Reset Data / Limpar Dados",
    "limpando": "Deseja limpar os dados?" if is_pt else "Do you want to reset the data?"
}

st.title(t["titulo"])
st.markdown(t["subtitulo"])

# --- EXPLICAÇÃO DIDÁTICA (COMO FUNCIONA) ---
with st.expander("ℹ️ Entenda a Mágica: Passado, Presente e Futuro" if is_pt else "ℹ️ Understand the Magic: Past, Present, and Future"):
    if is_pt:
        st.markdown("""
        **Como a IA prevê a velocidade?**
        Redes Neurais LSTM não olham apenas para uma "foto" isolada do carro, elas assistem a um "filme" para entender a inércia.
        * ⏪ **O Passado (Memória):** O gráfico mostra 9 instantes anteriores de uma frenagem forte antes da curva.
        * 🕹️ **O Presente (Sua Ação):** Os controles laterais representam o que o piloto decidiu fazer neste exato milissegundo.
        * 🔮 **O Futuro (A Previsão):** A IA processa essa linha do tempo inteira e calcula qual será a velocidade do carro no próximo instante, considerando a física e a inércia da manobra.
        """)
    else:
        st.markdown("""
        **How does the AI predict speed?**
        LSTM Neural Networks don't just look at an isolated "photo" of the car; they watch a "movie" to understand inertia.
        * ⏪ **The Past (Memory):** The chart shows 9 previous instants of heavy braking before a corner.
        * 🕹️ **The Present (Your Action):** The side controls represent what the driver decided to do at this exact millisecond.
        * 🔮 **The Future (Prediction):** The AI processes this entire timeline and calculates what the car's speed will be in the very next instant, considering the physics and inertia of the maneuver.
        """)

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
# Usamos o SessionState para manter o ponto dinâmico entre recarregamentos
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

# --- FUNÇÃO DE RESET (CALLBACK) ---
# Esta função roda isolada antes da tela ser redesenhada
def resetar_dados():
    st.session_state["slider_vel"] = 170.0
    st.session_state["slider_rpm"] = 10500.0
    st.session_state["slider_marcha"] = 4.0
    st.session_state["slider_acel"] = -2.0
    if 'dados_historicos' in st.session_state:
        del st.session_state['dados_historicos']

# --- BARRA LATERAL (CONTROLES E API) ---
with st.sidebar:
    st.markdown("---")
    st.header(t["config_cloud"])
    api_url = st.text_input("URL (GCP):", value="https://f1-telemetry-api-50878659952.us-central1.run.app/prever")
    
    st.markdown("---")
    st.header(t["controles"])
    st.markdown(t["simule"])
    
    # Os controles continuam conectados ao session_state através da 'key'
    vel_atual = st.slider(t["vel"], 50.0, 350.0, 170.0, step=1.0, key="slider_vel")
    rpm_atual = st.slider(t["rpm"], 5000.0, 13000.0, 10500.0, step=100.0, key="slider_rpm")
    marcha_atual = st.slider(t["marcha"], 1.0, 8.0, 4.0, step=1.0, key="slider_marcha")
    acel_atual = st.slider(t["acel"], -5.0, 2.0, -2.0, step=0.1, key="slider_acel")

    st.markdown("---")
    # O botão agora aciona a função pelo parâmetro on_click
    st.button(t["limpar"], type="secondary", use_container_width=True, on_click=resetar_dados)
        
# --- PREPARAÇÃO DOS DADOS ---
# Cria a janela completa (9 fixos + 1 dinâmico)
ponto_dinamico = {
    "velocidade": vel_atual, 
    "rpm": rpm_atual, 
    "marcha": marcha_atual, 
    "aceleracao": acel_atual
}
janela_completa = st.session_state['dados_historicos'] + [ponto_dinamico]

# --- REQUISIÇÃO PARA A NUVEM ---
payload = {"pontos": janela_completa}
inicio = time.time()
velocidade_prev = vel_atual # Valor padrão caso falhe

try:
    resposta = requests.post(api_url, json=payload)
    latencia_ms = round((time.time() - inicio) * 1000)
    
    if resposta.status_code == 200:
        dados_retorno = resposta.json()
        velocidade_prev = dados_retorno.get("velocidade_prevista_kmh")
        st.success(f"{t['status_ia']}: Online 🟢 ({latencia_ms} {t['latencia']})")
    else:
        st.error(f"❌ Erro HTTP {resposta.status_code}")
except Exception as e:
    st.error(t["erro_servidor"])

# --- PAINEL DE MÉTRICAS SUPERIORES ---
st.markdown("---")
col1, col2, col3 = st.columns(3)
col1.metric(t["vel_agora"], f"{vel_atual} km/h")
col2.metric(t["prev_futuro"], f"{velocidade_prev} km/h", delta=round(velocidade_prev - vel_atual, 2))
col3.metric(t["marcha"], int(marcha_atual))

# --- GRÁFICO VISUAL (Drs Duplo Y) ---
st.markdown("---")
st.subheader(t["tit_grafico"])

# --- GERANDO COORDENADAS ESPACIAIS (GPS Simulado: S do Senna) ---
# Valores de X virando para a esquerda, e Y reduzindo (descendo a reta)
df["X"] = [0, 0, 0, -2, -8, -18, -32, -50, -72, -100]
df["Y"] = [500, 440, 380, 320, 260, 205, 155, 110, 70, 35]

st.markdown("---")
    
# --- DIVIDINDO A TELA EM DUAS COLUNAS ---
col_grafico1, col_grafico2 = st.columns(2)

# COLUNA ESQUERDA: O GRÁFICO DE TELEMETRIA (Linhas)
with col_grafico1:
    st.subheader("📊 Telemetria do Motor" if is_pt else "📊 Engine Telemetry")
    fig_linhas = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Linha do RPM (Eixo Principal)
    fig_linhas.add_trace(go.Scatter(x=df.index, y=df['rpm'], name='RPM', line=dict(color='red', width=3)), secondary_y=False)
    # Linha da Velocidade (Eixo Secundário)
    fig_linhas.add_trace(go.Scatter(x=df.index, y=df['velocidade'], name='Velocidade' if is_pt else 'Speed', line=dict(color='blue', width=3)), secondary_y=True)
    
    fig_linhas.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor="rgba(0,0,0,0)")
    fig_linhas.update_yaxes(title_text="RPM", secondary_y=False)
    fig_linhas.update_yaxes(title_text="km/h", secondary_y=True)
    st.plotly_chart(fig_linhas, use_container_width=True)

# COLUNA DIREITA: O GRÁFICO ESPACIAL (Mini-Mapa GPS)
with col_grafico2:
    st.subheader("🗺️ Visão do Circuito (GPS)" if is_pt else "🗺️ Circuit View (GPS)")
    fig_mapa = go.Figure()
    
    # Traçado Passado (9 pontos)
    fig_mapa.add_trace(go.Scatter(
        x=df["X"][:9], y=df["Y"][:9], 
        mode='lines+markers', name='Passado' if is_pt else 'Past', 
        line=dict(color='gray', dash='dot', width=2),
        marker=dict(size=8, color='gray')
    ))
    
    # Ponto Atual (10º ponto - Onde o piloto está agora)
    fig_mapa.add_trace(go.Scatter(
        x=[df["X"].iloc[9]], y=[df["Y"].iloc[9]], 
        mode='markers', name='Presente' if is_pt else 'Present', 
        marker=dict(color='blue', size=14, line=dict(color='white', width=2))
    ))

    # A Mágica: Projetando o Futuro no mapa se a IA já calculou a previsão
    if prever and resposta and resposta.status_code == 200:
        previsao_velocidade = resposta.json()['previsao'][0][0]
        # Calculamos a próxima coordenada da curva matematicamente
        futuro_x = df["X"].iloc[9] - 35
        futuro_y = df["Y"].iloc[9] - 25
        
        # Se a previsão for alta (acima de 160 km/h), o carro vai mais longe. Se for baixa, freia antes.
        fator_inercia = previsao_velocidade / 150.0 
        
        fig_mapa.add_trace(go.Scatter(
            x=[futuro_x * fator_inercia], y=[futuro_y], 
            mode='markers', name='Futuro (IA)' if is_pt else 'Future (AI)', 
            marker=dict(color='red', size=18, symbol='star', line=dict(color='yellow', width=2))
        ))

    # Ocultando os eixos numéricos para parecer um mapa real
    fig_mapa.update_layout(
        height=400, margin=dict(l=0, r=0, t=30, b=0), 
        plot_bgcolor="rgba(0,0,0,0.05)",
        xaxis=dict(visible=False, showgrid=False), 
        yaxis=dict(visible=False, showgrid=False)
    )
    st.plotly_chart(fig_mapa, use_container_width=True)

# --- TABELA DE DADOS BRUTOS (OPCIONAL PARA AUDITORIA) ---
st.markdown("---")
with st.expander("🔎 Ver Matriz de Dados Enviada para a IA" if is_pt else "🔎 View Raw Data Matrix Sent to AI"):
    # Reordenando as colunas para ficar mais elegante na tabela
    df_exibicao = df[["velocidade", "rpm", "marcha", "aceleracao"]]
    st.dataframe(df_exibicao, use_container_width=True)