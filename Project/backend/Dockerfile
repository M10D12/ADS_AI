
FROM python:3.12-slim

# Define o diretório de trabalho
WORKDIR /app

# Evita que o Python guarde ficheiros .pyc e buffer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala dependências do sistema 
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências 
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o restante código
COPY . /app/

# Expõe a porta do Django
EXPOSE 8000

# Comando para correr o servidor
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
