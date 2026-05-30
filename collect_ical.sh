#!/bin/bash
set -e

# Démarrer Xvfb
export DISPLAY=:99
Xvfb :99 -screen 0 1280x800x24 -ac +extension GLX +render -noreset &
XVFB_PID=$!

# Attendre que Xvfb soit prêt
echo "⏳ Attente de Xvfb..."
for i in {1..10}; do
    if xdpyinfo -display :99 >/dev/null 2>&1; then
        echo "✅ Xvfb est prêt"
        break
    fi
    sleep 1
done

# Lancer le script Python
python collect_ical_urls.py "$@"

# Arrêter Xvfb
kill $XVFB_PID 2>/dev/null || true
