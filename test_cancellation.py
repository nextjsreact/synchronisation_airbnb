"""
Test complet du flux annulation :
1. Trouve un listing avec 0 réservations confirmées
2. Crée une réservation fictive dans Supabase
3. Vérifie qu'elle est bien en base
4. Insère une entrée sync_queue pour ce listing
5. Attend (60s avec retries) que le scraper tourne
6. Vérifie que la réservation passe en cancelled + notification créée
7. Nettoie (supprime la résa et la notification)

Prérequis :
  - Docker à jour (targeted-scraper rebuildé)
  - Vercel à jour (cancel-check route déployée)
  - targeted-scraper DOIT tourner
  - pip install requests

Usage:
    python test_cancellation.py
"""
import os, sys, time, uuid
import requests
from datetime import datetime, timedelta

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

TEST_ID = None
notifs = []

def cleanup():
    if TEST_ID:
        try:
            requests.delete(
                f"{SUPABASE_URL}/rest/v1/reservations",
                params={"id": f"eq.{TEST_ID}"},
                headers=HEADERS,
                timeout=10,
            )
        except Exception:
            pass
    for n in notifs:
        try:
            requests.delete(
                f"{SUPABASE_URL}/rest/v1/airbnb_notifications",
                params={"id": f"eq.{n['id']}"},
                headers=HEADERS,
                timeout=10,
            )
        except Exception:
            pass

def req(method, path, **kwargs):
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", 15)
    return requests.request(method, f"{SUPABASE_URL}/rest/v1/{path}", **kwargs)

try:
    print("🔍 Listing libre (0 résa confirmée)...")
    lofts = req("GET", "lofts",
        params={"select": "id,name,airbnb_listing_id", "airbnb_listing_id": "not.is.null", "limit": 50}
    ).json()

    safe_listing = None
    for loft in lofts:
        existing = req("GET", "reservations",
            params={"select": "id", "loft_id": f"eq.{loft['id']}", "status": "in.(confirmed,pending)", "limit": 1}
        ).json()
        if not existing:
            safe_listing = loft
            break

    if not safe_listing:
        print("❌ Aucun listing sans réservation confirmée")
        sys.exit(1)

    LOFT_ID = safe_listing["id"]
    LISTING_ID = safe_listing["airbnb_listing_id"]
    LOFT_NAME = safe_listing["name"]
    print(f"✅ {LOFT_NAME} (loft={LOFT_ID}, airbnb={LISTING_ID})")

    # ── 1. Créer réservation ────────────────────────────────────
    code = f"TEST{uuid.uuid4().hex[:6].upper()}"
    today = datetime.now()
    payload = {
        "loft_id": LOFT_ID, "guest_name": "Test Annulation",
        "guest_count": 3,
        "guest_email": "test@example.com",
        "guest_nationality": "",
        "check_in_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
        "check_out_date": (today + timedelta(days=62)).strftime("%Y-%m-%d"),
        "total_amount": 30000, "currency_code": "DZD",
        "status": "confirmed", "source": "manual",
        "airbnb_confirmation_code": code,
    }

    print(f"\n📝 1. Création résa (code={code}, guest_count=3)")
    resp = req("POST", "reservations", json=payload)
    if resp.status_code not in (200, 201):
        print(f"❌ {resp.status_code} {resp.text[:200]}")
        sys.exit(1)
    res = resp.json()
    TEST_ID = res[0]["id"] if isinstance(res, list) else res.get("id")
    print(f"✅ id={TEST_ID}")

    # ── 2. Vérifier ─────────────────────────────────────────────
    print(f"\n🔎 2. Vérification...")
    r = req("GET", "reservations",
        params={"select": "id,guest_name,guest_count,status,airbnb_confirmation_code", "id": f"eq.{TEST_ID}"}
    ).json()[0]
    assert r["status"] == "confirmed"
    assert r["guest_count"] == 3
    assert r["airbnb_confirmation_code"] == code
    print(f"✅ status={r['status']}, guest_count={r['guest_count']}")

    # ── 3. sync_queue ───────────────────────────────────────────
    print(f"\n🔄 3. sync_queue...")
    resp = req("POST", "sync_queue", json={
        "listing_id": str(LISTING_ID), "status": "pending",
        "reason": "manual_test_cancellation",
    })
    if resp.status_code not in (200, 201):
        print(f"❌ {resp.status_code} {resp.text[:150]}")
        sys.exit(1)
    print(f"✅ listing {LISTING_ID} enqueued")

    # ── 4. Attente ──────────────────────────────────────────────
    print(f"\n⏳ 4. Attente scraper (60s, check/10s)...")
    cancelled = False
    for i in range(6):
        time.sleep(10)
        r = req("GET", "reservations",
            params={"select": "id,status,guest_count,cancelled_at,cancellation_reason", "id": f"eq.{TEST_ID}"}
        ).json()
        st = r[0]["status"] if r else "?"
        print(f"   [{i+1}/6] status={st}")
        if st == "cancelled":
            cancelled = True
            print(f"   guest_count={r[0].get('guest_count')}")
            print(f"   cancelled_at={r[0].get('cancelled_at')}")
            print(f"   reason={r[0].get('cancellation_reason')}")
            break

    if not cancelled:
        print(f"\n❌❌❌ ÉCHEC après 60s")
        print(f"   Vérifie: docker ps, docker logs targeted-scraper --tail 50")

    # ── 5. Notification ─────────────────────────────────────────
    print(f"\n🔔 5. Notification...")
    notifs = req("GET", "airbnb_notifications",
        params={"select": "id,type,title,message,metadata", "reservation_id": f"eq.{TEST_ID}",
                "order": "created_at.desc", "limit": 1}
    ).json()
    if notifs:
        m = notifs[0].get("metadata", {})
        print(f"   type={notifs[0]['type']}")
        print(f"   metadata.guest_count={m.get('guest_count')}")
        print(f"   ✅ guest_count OK" if m.get("guest_count") == 3 else f"   ⚠️  guest_count={m.get('guest_count')}")
    else:
        print(f"   ⚠️  Aucune notification")

finally:
    # ── 6. Nettoyage ────────────────────────────────────────────
    if TEST_ID or notifs:
        print(f"\n🧹 6. Nettoyage...")
        cleanup()
        print(f"   Fait")

print(f"\n{'='*50}")
print(f"{'✅✅✅ TEST RÉUSSI' if cancelled else '❌❌❌ ÉCHEC'}")
print(f"{'='*50}")
