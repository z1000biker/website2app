# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Java JDK for Android build tools
    openjdk-17-jdk \
    # Qt dependencies for PyQt6
    libgl1-mesa-glx \
    libxkbcommon0 \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libdbus-1-3 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libegl1 \
    # Other utilities
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/output

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set display for headless mode (optional, for CI/CD)
ENV QT_QPA_PLATFORM=offscreen

# Default command (can be overridden)
CMD ["python", "main.py"]

# Labels for container metadata
LABEL maintainer="Nikos Kontopoulos <sv1eex@hotmail.com>"
LABEL version="2.0.0"
LABEL description="WebSite to Android & iOS App Builder"
LABEL org.opencontainers.image.source="https://github.com/z1000biker/website2app"
