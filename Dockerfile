# 1. Usar uma imagem oficial do Python, versão leve (slim)
FROM python:3.10-slim

# 2. Definir a pasta de trabalho dentro do servidor do Google
WORKDIR /app

# 3. Copiar o arquivo de requisitos e instalar as bibliotecas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar os arquivos do nosso projeto (a API, o Modelo e o Scaler) para o servidor
COPY api_f1.py .
COPY motor_f1_graph/ motor_f1_graph/
COPY scaler_f1.pkl .

# 5. Expor a porta que o Cloud Run exige (Porta 8080)
EXPOSE 8080

# 6. O comando para ligar o servidor quando o contêiner nascer
CMD ["uvicorn", "api_f1:app", "--host", "0.0.0.0", "--port", "8080"]