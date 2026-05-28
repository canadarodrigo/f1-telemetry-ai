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

# Cria a estrutura do gráfico com dois eixos Y
fig = make_subplots(specs=[[{"secondary_y": True}]])

df = pd.DataFrame(janela_completa)
df.index.name = t["ms"]

# Adiciona a linha de RPM no Eixo Y Principal (Esquerdo)
fig.add_trace(
    go.Scatter(x=df.index, y=df['rpm'], name=t["rpm"], mode='lines+markers', line=dict(color='#87CEEB')), # Azul Claro
    secondary_y=False,
)

# Adiciona a linha de Velocidade no Eixo Y Secundário (Direito)
fig.add_trace(
    go.Scatter(x=df.index, y=df['velocidade'], name=t["vel"], mode='lines+markers', line=dict(color='#0056b3')), # Azul Escuro
    secondary_y=True,
)

# Configurações dos eixos e título
fig.update_layout(
    title_text="",
    xaxis_title=t["ms"],
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# Define o título do eixo Y principal (Esquerdo)
fig.update_yaxes(title_text=t["rpm"], secondary_y=False)

# Define o título do eixo Y secundário (Direito)
fig.update_yaxes(title_text=t["vel"], secondary_y=True)

# Exibe o gráfico no Streamlit
st.plotly_chart(fig, use_container_width=True)