import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Motor de Previsão de Telemetria F1", layout="wide")

# --- SIDEBAR: CONFIGURAÇÕES E CONTROLES ---
st.sidebar.title("🏎️ Controles do Piloto")

# Conexão com a API no GCP (ou local)
st.sidebar.markdown("### ⚙️ Conexão Cloud")
api_url = st.sidebar.text_input(
    "URL da API (Cloud Run ou Local):", 
    value="https://f1-telemetry-api-50878659952.us-central1.run.app/prever" # Substitua pela sua URL do GCP
)

st.sidebar.markdown("### 🕹️ Controles")
velocidade_atual = st.sidebar.slider("Velocidade Atual (km/h)", 0.0, 350.0, 155.0)
rpm_atual = st.sidebar.slider("Motor (RPM)", 0.0, 15000.0, 9900.0)
marcha_atual = st.sidebar.slider("Marcha / Gear", 1.0, 8.0, 3.0, step=1.0)
acelerador_atual = st.sidebar.slider("Acelerador (%)", 0.0, 100.0, 0.0)

# Botão de reset (apenas visual para manter a estrutura)
if st.sidebar.button("🔄 Limpar Dados / Reset Data"):
    st.rerun()

# --- SIMULAÇÃO DA JANELA DE TEMPO (10ms) ---
# A LSTM exige 10 registros. Aqui criamos a matriz para enviar no payload.
pontos_telemetria = []
for i in range(10):
    pontos_telemetria.append({
        "velocidade": velocidade_atual,
        "rpm": rpm_atual,
        "marcha": marcha_atual,
        "aceleracao": acelerador_atual
    })

payload = {"pontos": pontos_telemetria}

# --- REQUISIÇÃO PARA A API ---
previsao_ia = None
status_api = "Offline 🔴"

try:
    response = requests.post(api_url, json=payload)
    if response.status_code == 200:
        dados_api = response.json()
        previsao_ia = dados_api.get("velocidade_prevista_kmh", 0.0)
        status_api = "Online 🟢"
    else:
        status_api = f"Erro {response.status_code} 🔴"
except Exception as e:
    status_api = "Falha de Conexão 🔴"

# --- INTERFACE PRINCIPAL ---
st.title("Sistema de Manutenção Preditiva e Telemetria F1")

# Métricas Principais
col_status, col_vel, col_prev = st.columns(3)
col_status.metric("Status do Motor IA", status_api)
col_vel.metric("Sua Velocidade", f"{velocidade_atual:.1f} km/h")

if previsao_ia is not None:
    col_prev.metric("Previsão da IA (Futuro)", f"{previsao_ia:.2f} km/h")
    
    st.divider()

    # --- NOVA CAMADA: MOTOR DE ANOMALIAS ---
    st.markdown("### 🔍 Motor de Detecção de Anomalias (Erro Residual)")
    
    # 1. Calcula o Erro Residual
    erro_residual = abs(velocidade_atual - previsao_ia)

    # 2. Thresholds de Segurança (em km/h)
    LIMIAR_ALERTA = 10.0
    LIMIAR_CRITICO = 20.0

    # 3. Classificação e Exibição de Métricas
    ca1, ca2, ca3 = st.columns(3)
    ca1.metric(label="Velocidade Sensor (Real)", value=f"{velocidade_atual:.1f} km/h")
    ca2.metric(label="Previsão LSTM (Baseline)", value=f"{previsao_ia:.2f} km/h")
    ca3.metric(
        label="Erro Residual (Desvio)", 
        value=f"{erro_residual:.2f} km/h",
        delta=f"{erro_residual:.2f} km/h",
        delta_color="inverse" # Maior erro = Vermelho
    )

    # 4. Disparo do Alerta na Tela
    if erro_residual <= LIMIAR_ALERTA:
        st.success("✅ **Telemetria Normal:** Comportamento do carro alinhado com o padrão da volta ideal (Baseline).")
    elif erro_residual <= LIMIAR_CRITICO:
        st.warning(f"⚠️ **Aviso de Degradação:** Desvio estatístico de {erro_residual:.2f} km/h detectado. Monitore o desgaste dos pneus.")
    else:
        st.error(f"🚨 **ANOMALIA CRÍTICA:** Desvio massivo de {erro_residual:.2f} km/h! Possível perda de tração ou anomalia severa de frenagem detectada no sistema.")

    st.divider()

    # --- GRÁFICO DE TELEMETRIA (Visualização do Histórico) ---
    st.markdown("### 📊 Gráfico de Telemetria do Motor")
    
    # Criando dados fictícios para o gráfico apenas para ilustrar o momento atual
    df_grafico = pd.DataFrame(pontos_telemetria)
    df_grafico['ms'] = range(10)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_grafico['ms'], y=df_grafico['rpm'], mode='lines+markers', name='RPM', yaxis='y1', line=dict(color='lightblue')))
    fig.add_trace(go.Scatter(x=df_grafico['ms'], y=df_grafico['velocidade'], mode='lines+markers', name='Velocidade', yaxis='y2', line=dict(color='darkblue', width=3)))

    fig.update_layout(
        yaxis=dict(title='RPM', side='left', showgrid=False),
        yaxis2=dict(title='Velocidade (km/h)', side='right', overlaying='y', showgrid=True),
        xaxis=dict(title='Tempo (ms)'),
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("⚠️ O modelo não retornou uma previsão. Verifique se a API está online e configurada corretamente na barra lateral.")