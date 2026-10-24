FROM python:3.11-slim

# libvlc is needed by python-vlc for motion/audio recording.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libvlc-dev \
        vlc-plugin-base \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 4000/tcp: camera registration, status and control
# 5000/tcp: REST API
EXPOSE 4000 5000

CMD ["python3", "server.py"]
