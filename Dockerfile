FROM python:3.11-slim

# System-level dependencies for UI testing and OpenGL rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    xvfb \
    libgl1-mesa-glx \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["bash"]
