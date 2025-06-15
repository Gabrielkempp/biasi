# Use uma imagem Python oficial como base
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de requirements primeiro (para aproveitar o cache do Docker)
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os arquivos da aplicação
COPY . .

# Cria diretório para as páginas se não existir
RUN mkdir -p pages

# Expõe a porta que o Streamlit usa
EXPOSE 8501

# Comando para executar a aplicação
CMD ["streamlit", "run", "Inicio.py", "--server.port=8501", "--server.address=0.0.0.0"]