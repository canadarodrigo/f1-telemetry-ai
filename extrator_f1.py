import os
import json
import time
import fastf1
import pandas as pd
from google.cloud import pubsub_v1

# 1. Autenticação: Apontar para o seu arquivo JSON de credenciais
# Certifique-se de que o nome do arquivo abaixo seja exatamente o que está na sua pasta
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcp-key.json"

# 2. Configurações do seu GCP (Atenção: verifique se o ID do projeto está exato)
PROJECT_ID = "f1-telemetry-ai" # Se o Google gerou números no final do ID, atualize aqui
TOPIC_ID = "telemetria-f1-topic"

# 3. Inicializar o cliente do Pub/Sub
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

fastf1.Cache.enable_cache('cache')

def iniciar_transmissao_nuvem():
    print("🏎️ Conectando aos servidores da Fórmula 1...")
    session = fastf1.get_session(2023, 'Brazil', 'R')
    session.load(telemetry=True, laps=True, weather=False, messages=False)
    
    print("✅ Isolando telemetria do Verstappen (VER)...")
    voltas_verstappen = session.laps.pick_driver('VER')
    volta_rapida = voltas_verstappen.pick_fastest()
    df_stream = volta_rapida.get_telemetry()
    
    print("\n☁️ Iniciando transmissão em tempo real para o Google Cloud Pub/Sub...\n")

    for index, row in df_stream.iterrows():
        tempo_formatado = str(row['Time']).split()[-1]
        
        # 4. Criar o payload (pacote de dados) estruturado
        mensagem_dict = {
            "piloto": "VER",
            "tempo": tempo_formatado,
            "velocidade": int(row['Speed']),
            "rpm": int(row['RPM']),
            "marcha": int(row['nGear']),
            "aceleracao": int(row['Throttle']),
            "freio": bool(row['Brake'])
        }
        
        # 5. Converter dicionário Python para string JSON e depois para bytes (exigência do Pub/Sub)
        dados_json = json.dumps(mensagem_dict).encode("utf-8")
        
        # 6. Publicar a mensagem no tópico do GCP
        future = publisher.publish(topic_path, dados_json)
        
        # O future.result() retorna o ID da mensagem gerado com sucesso pelo Google
        print(f"📦 Enviado: VEL {mensagem_dict['velocidade']:>3} km/h | Mensagem ID: {future.result()}")
        
        time.sleep(0.1)

if __name__ == '__main__':
    iniciar_transmissao_nuvem()