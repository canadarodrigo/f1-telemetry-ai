from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
import tensorflow as tf
import joblib
import os

app = FastAPI(
    title="Motor de Previsão de Telemetria F1",
    description="API de inferência com Grafo Computacional TF Puro",
    version="3.0.0"
)

infer_engine = None
scaler = None

print("⚙️ Inicializando Motor de Grafo Puro (SavedModel)...")

caminho_modelo = 'motor_f1_graph' # Agora apontamos para a pasta
caminho_scaler = 'scaler_f1.pkl'

if os.path.exists(caminho_modelo) and os.path.exists(caminho_scaler):
    try:
        # Carrega o grafo ignorando o Keras completamente
        modelo_puro = tf.saved_model.load(caminho_modelo)
        
        # Pega a "porta de entrada e saída" padrão do grafo matemático
        infer_engine = modelo_puro.signatures["serving_default"]
        
        scaler = joblib.load(caminho_scaler)
        print("✅ Motor carregado com sucesso na memória!")
    except Exception as e:
        print(f"❌ Erro crítico ao carregar grafo: {e}")
else:
    print("🚨 ALERTA: Pasta do modelo ou Scaler não encontrados.")

class PontoTelemetria(BaseModel):
    velocidade: float
    rpm: float
    marcha: float
    aceleracao: float

class JanelaTempo(BaseModel):
    pontos: List[PontoTelemetria] 

@app.post("/prever")
def prever_velocidade(janela: JanelaTempo):
    if infer_engine is None or scaler is None:
        raise HTTPException(status_code=503, detail="Motor indisponível.")

    if len(janela.pontos) != 10:
        raise HTTPException(status_code=400, detail="A LSTM exige exatamente 10 registros.")
    
    try:
        dados_brutos = np.array([[p.velocidade, p.rpm, p.marcha, p.aceleracao] for p in janela.pontos])
        dados_normalizados = scaler.transform(dados_brutos)
        
        # Prepara o tensor rígido do TensorFlow
        entrada_tensor = tf.constant([dados_normalizados], dtype=tf.float32)
        
        # Injeta no grafo. O resultado sai como um dicionário.
        resultado_grafo = infer_engine(entrada_tensor)
        
        # Pega o primeiro e único valor da saída
        previsao_normalizada = list(resultado_grafo.values())[0].numpy()
        
        matriz_reversao = np.zeros((1, 4))
        matriz_reversao[0, 0] = previsao_normalizada[0, 0]
        velocidade_prevista_kmh = scaler.inverse_transform(matriz_reversao)[0, 0]
        
        return {
            "status": "sucesso",
            "tecnologia": "TF SavedModel Graph",
            "velocidade_prevista_kmh": round(float(velocidade_prevista_kmh), 2)
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Erro de inferência: {str(e)}")