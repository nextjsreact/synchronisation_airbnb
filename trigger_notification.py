"""
Crée une notification de test dans Supabase pour voir dans l'UI.

Usage:
    python trigger_notification.py new          # notification création
    python trigger_notification.py cancelled    # notification annulation
    python trigger_notification.py updated      # notification modification
"""
import os, sys, uuid
import requests
from datetime import datetime

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL",
    "https://mhngbluefyucoesgcjoy.supabase.co")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1obmdibHVlZnl1Y29lc2djam95Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjEzMTcyMiwiZXhwIjoyMDYxNzA3NzIyfQ.GWP_COePfH8YlwuEX7zRc55U5p4XSlCJE5hJehGIurw")

HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

notif_type = sys.argv[1] if len(sys.argv) > 1 else "new"
if notif_type not in ("new", "cancelled", "updated", "conflict", "error"):
    print(f"Type invalide: {notif_type}")
    print("Types: new, cancelled, updated, conflict, error")
    sys.exit(1)

# Chercher un loft pour la notification
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/lofts",
    params={"select": "id,name", "limit": 1},
    headers=HEADERS,
)
loft = resp.json()[0]
loft_id = loft["id"]
loft_name = loft["name"]

# Chercher une réservation existante pour ce loft
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/reservations",
    params={
        "select": "id,guest_name,guest_count,check_in_date,check_out_date,total_amount",
        "loft_id": f"eq.{loft_id}",
        "limit": 1,
        "order": "created_at.desc",
    },
    headers=HEADERS,
)
existing = resp.json()

if existing:
    r = existing[0]
else:
    # Créer une fausse résa
    code = f"NOTIF{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "loft_id": loft_id, "guest_name": "Test Notification",
        "guest_count": 2, "guest_email": "", "guest_nationality": "",
        "check_in_date": "2026-07-01", "check_out_date": "2026-07-03",
        "total_amount": 25000, "currency_code": "DZD",
        "status": "confirmed", "source": "manual",
        "airbnb_confirmation_code": code,
    }
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/reservations",
        headers=HEADERS, json=payload,
    )
    r = resp.json()
    if isinstance(r, list):
        r = r[0]

reservation_id = r["id"]
guest_name = r.get("guest_name", "?")
guest_count = r.get("guest_count", 0)
check_in = r.get("check_in_date", "?")
check_out = r.get("check_out_date", "?")
total = r.get("total_amount", 0)

titles = {
    "new": f"Nouvelle réservation - {loft_name}",
    "cancelled": f"Réservation annulée - {loft_name}",
    "updated": f"Réservation modifiée - {loft_name}",
    "conflict": f"Conflit de dates - {loft_name}",
    "error": f"Erreur de synchronisation - {loft_name}",
}

messages = {
    "new": f"{guest_name} ({guest_count} pers.) — {check_in} → {check_out} — {total:,.0f} DZD",
    "cancelled": f"{guest_name} a annulé ({check_in} → {check_out})",
    "updated": f"{guest_name} — dates modifiées ({check_in} → {check_out})",
    "conflict": f"Chevauchement détecté pour {guest_name} ({check_in} → {check_out})",
    "error": f"Erreur lors du sync de {guest_name} ({check_in} → {check_out})",
}

notif = {
    "reservation_id": reservation_id,
    "loft_id": loft_id,
    "type": notif_type,
    "title": titles[notif_type],
    "message": messages[notif_type],
    "metadata": {
        "guest_name": guest_name,
        "guest_count": guest_count,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "total_amount": total,
    },
}

print(f"🔔 Création notification type='{notif_type}'...")
print(f"   Réservation: {guest_name} ({reservation_id})")
print(f"   Guest count: {guest_count}")
print(f"   Title: {notif['title']}")
print(f"   Message: {notif['message']}")

resp = requests.post(
    f"{SUPABASE_URL}/rest/v1/airbnb_notifications",
    headers=HEADERS,
    json=notif,
)

if resp.status_code in (200, 201):
    print(f"✅ Notification créée ! Regarde l'UI 🎉")
else:
    print(f"❌ Échec: {resp.status_code} {resp.text[:150]}")
