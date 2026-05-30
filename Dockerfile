# ============================================================================
# Dockerfile pour Airbnb Scraper avec CloakBrowser
# ============================================================================
# Image de base: Python 3.11 slim
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Loft Algérie"
LABEL description="Airbnb Scraper avec CloakBrowser et API Next.js"
LABEL version="2.0.1"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV DISPLAY=:99

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    wget \
    git \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    xvfb \
    x11vnc \
    x11-utils \
    fluxbox \
    net-tools \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Installer noVNC (client web VNC)
RUN git clone --depth 1 https://github.com/novnc/noVNC.git /opt/noVNC && \
    git clone --depth 1 https://github.com/novnc/websockify.git /opt/noVNC/utils/websockify

# Créer le répertoire de travail
WORKDIR /app

# Copier les fichiers requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Installer Playwright et ses navigateurs
RUN pip install playwright && \
    playwright install chromium && \
    playwright install-deps chromium

# Pré-installer le binaire CloakBrowser (évite le timeout au runtime)
RUN python -m cloakbrowser install

# Copier les fichiers du scraper
COPY airbnb_scraper.py .
COPY airbnb_api_client.py .
COPY collect_ical_urls.py .
COPY ical_watcher.py .
COPY targeted_scraper.py .
COPY .env .

# Créer le répertoire de sortie
RUN mkdir -p /app/output

# Copier le script d'entrée
COPY entrypoint.sh .
COPY collect_ical.sh .
RUN chmod +x entrypoint.sh collect_ical.sh

# Exposer les ports VNC
EXPOSE 5900 6080

# Exposer le volume pour les données
VOLUME ["/app/output"]

# Commande par défaut
CMD ["./entrypoint.sh"]
