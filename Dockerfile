# Use Python 3.12 slim as base for a smaller footprint
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for OpenGL and Xvfb (Headless Rendering)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-dri \
    libgl1-mesa-glx \
    libgles2-mesa \
    libegl1-mesa \
    freeglut3-dev \
    mesa-utils \
    xvfb \
    python3-tk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . .

# Set the environment variable for ModernGL (Headless mode)
ENV MGL_WINDOW_BACKEND=headless

# Default command: Run the test suite to ensure stability
CMD ["python3", "-m", "pytest", "tests/test_engine.py", "-v"]
