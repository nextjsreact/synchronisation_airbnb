#!/bin/bash
set -e

# ── 1. Démarrer Xvfb (display virtuel) ─────────────────────
echo "🖥️  Démarrage du display virtuel (Xvfb)..."
export DISPLAY=:99
Xvfb :99 -screen 0 1280x800x24 -ac +extension GLX +render -noreset &
XVFB_PID=$!

# Attendre que Xvfb soit vraiment prêt
echo "⏳ Attente de Xvfb..."
for i in {1..10}; do
    if xdpyinfo -display :99 >/dev/null 2>&1; then
        echo "✅ Xvfb est prêt"
        break
    fi
    sleep 1
done

# ── 2. Démarrer fluxbox (window manager léger) ─────────────
echo "🪟  Démarrage du window manager (fluxbox)..."
fluxbox &
sleep 2

# ── 3. Démarrer x11vnc (serveur VNC) ───────────────────────
echo "📡 Démarrage du serveur VNC (x11vnc)..."
x11vnc -display :99 -forever -nopw -rfbport 5900 -shared &
sleep 2

# ── 4. Démarrer noVNC (client web VNC) ─────────────────────
echo "🌐 Démarrage de noVNC sur le port 6080..."
/opt/noVNC/utils/novnc_proxy --vnc localhost:5900 --listen 6080 &
sleep 2

echo ""
echo "═══════════════════════════════════════════════════════"
echo "   🔗 Interface VNC : http://localhost:6080"
echo "   🔗 VNC natif    : localhost:5900"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "🔍 Vérification de l'environnement..."
echo "   DISPLAY=$DISPLAY"
echo ""

# ── 5. Lancer le scraper (processus principal) ─────────────
python airbnb_scraper.py
