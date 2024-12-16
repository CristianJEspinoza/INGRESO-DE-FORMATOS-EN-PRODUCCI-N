FROM python:3.11.9-slim

WORKDIR /home/app

COPY requirements.txt .

# Instala dependencias del sistema y la versión parcheada de wkhtmltopdf
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    fontconfig \
    wget && \
    # Descarga e instala libssl1.1 manualmente usando dpkg - Necesario para ver header y footer en el pdf creado con wkhtmltopdf
    wget http://ftp.us.debian.org/debian/pool/main/o/openssl/libssl1.1_1.1.1n-0+deb10u3_amd64.deb && \
    dpkg -i libssl1.1_1.1.1n-0+deb10u3_amd64.deb || apt-get -f install -y && \
    rm libssl1.1_1.1.1n-0+deb10u3_amd64.deb && \
    # Descarga e instala la versión parcheada de wkhtmltopdf
    wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb && \
    dpkg -i wkhtmltox_0.12.6-1.buster_amd64.deb || apt-get -f install -y && \
    rm wkhtmltox_0.12.6-1.buster_amd64.deb && \
    # Configura caché de fuentes y limpia archivos temporales
    fc-cache -f -v && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 5000

CMD gunicorn --bind 0.0.0.0:5000 --log-level=debug --access-logfile=- app:app

