FROM debian:bullseye

# Atualiza o sistema e instala Firefox e dependências
RUN apt-get update -y && \
    apt-get install -y wget gnupg2 && \
    apt-get install -y firefox-esr python3 python3-pip

WORKDIR /app 

# Copia o arquivo de requisitos para o contêiner
COPY requirements.txt ./ 

# Instala as dependências do Python especificadas no requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt 

# Copia todo o código da aplicação para o contêiner
COPY . . 

# Expõe a porta 8000 para acesso externo
EXPOSE 8000 

# Comando para executar a aplicação usando uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
