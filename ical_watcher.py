"""
ical_watcher.py — Surveillance légère des calendriers iCal
==========================================================
Service sans navigateur qui poll les URLs iCal toutes les 5 minutes,
détecte les changements de hash, et pousse dans sync_queue.

Dépendances :
    pip install requests python-dotenv

Usage :
    python ical_watcher.py
"""

import hashlib
import os
import re
import sys
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

# Forcer UTF-8 sur Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# ── Configuration ─────────────────────────────────────────
SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or "https://zlpzuyctjhajdwlxzdzk.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpscHp1eWN0amhhamR3bHh6ZHprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMjc0NiwiZXhwIjoyMDk0Njc4NzQ2fQ.Hi6BTLkyPN-3ax18N9ssbOmTBtl-tdNoOVz4gHMMMLE"
POLL_INTERVAL = int(os.environ.get("ICAL_POLL_INTERVAL", "300"))  # 5 min

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


# ============================================================
# SUPABASE HELPERS
# ============================================================

def get_active_ical_configs():
    """Récupère les configs iCal actives depuis property_sync_config."""
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/property_sync_config"
            f"?select=loft_id,ical_url_airbnb,lofts!inner(airbnb_listing_id)"
            f"&is_active=eq.true",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        configs = resp.json()
        result = []
        for c in configs:
            ical_url = c.get("ical_url_airbnb", "")
            listing_id = ""
            lofts = c.get("lofts")
            if lofts and isinstance(lofts, dict):
                listing_id = lofts.get("airbnb_listing_id", "")
            if ical_url and listing_id:
                result.append({
                    "loft_id": c["loft_id"],
                    "listing_id": listing_id,
                    "ical_url": ical_url,
                })
        return result
    except Exception as e:
        print(f"   Erreur lecture configs: {e}")
        return []


def get_existing_hashes():
    """Récupère les hashes iCal existants."""
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/ical_hashes?select=listing_id,hash",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        return {h["listing_id"]: h["hash"] for h in resp.json()}
    except Exception as e:
        print(f"   Erreur lecture hashes: {e}")
        return {}


def upsert_hash(listing_id, new_hash):
    """Insère ou met à jour le hash iCal."""
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "listing_id": listing_id,
        "hash": new_hash,
        "checked_at": now,
        "changed_at": now,
    }
    try:
        # Essayer update d'abord
        resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/ical_hashes?listing_id=eq.{listing_id}",
            json=payload,
            headers=HEADERS,
            timeout=15,
        )
        if resp.status_code == 200 and resp.json():
            return
        # Sinon insert
        requests.post(
            f"{SUPABASE_URL}/rest/v1/ical_hashes",
            json=payload,
            headers=HEADERS,
            timeout=15,
        )
    except Exception as e:
        print(f"   Erreur upsert hash {listing_id}: {e}")


def update_checked_at(listing_id):
    """Met à jour seulement checked_at (pas de changement)."""
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/ical_hashes?listing_id=eq.{listing_id}",
            json={"checked_at": now},
            headers=HEADERS,
            timeout=15,
        )
    except Exception:
        pass


def push_to_queue(listing_id):
    """Pousse un listing dans la sync_queue."""
    payload = {
        "listing_id": listing_id,
        "status": "pending",
        "reason": "ical_change",
        "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/sync_queue",
            json=payload,
            headers=HEADERS,
            timeout=15,
        )
        return resp.status_code in (200, 201)
    except Exception as e:
        print(f"   Erreur push queue {listing_id}: {e}")
        return False


# ============================================================
# ICAL PROCESSING
# ============================================================

def fetch_ical(url):
    """Fetch le contenu d'un fichier iCal via HTTP."""
    try:
        resp = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; iCalWatcher/1.0)"
        })
        if resp.status_code == 200:
            return resp.text
        print(f"      HTTP {resp.status_code} pour {url[:60]}...")
        return None
    except requests.Timeout:
        print(f"      Timeout pour {url[:60]}...")
        return None
    except Exception as e:
        print(f"      Erreur fetch: {e}")
        return None


def compute_ical_hash(content):
    """Calcule le SHA256 du contenu iCal en retirant DTSTAMP."""
    if not content:
        return None
    # Retirer DTSTAMP (change à chaque export même si le contenu est identique)
    cleaned = re.sub(r"DTSTAMP:[^\n\r]*\r?\n?", "", content)
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


# ============================================================
# BOUCLE PRINCIPALE
# ============================================================

def check_all_icals():
    """Vérifie tous les calendriers iCal et détecte les changements."""
    configs = get_active_ical_configs()
    if not configs:
        print("   Aucune config iCal active")
        return 0

    existing_hashes = get_existing_hashes()
    changes = 0

    for cfg in configs:
        listing_id = cfg["listing_id"]
        ical_url = cfg["ical_url"]

        content = fetch_ical(ical_url)
        if content is None:
            continue

        new_hash = compute_ical_hash(content)
        if new_hash is None:
            continue

        old_hash = existing_hashes.get(listing_id)

        if old_hash is None:
            # Premier hash — on stocke, pas de queue
            upsert_hash(listing_id, new_hash)
            print(f"   [{listing_id}] Premier hash enregistre")
        elif old_hash != new_hash:
            # Changement detecte !
            upsert_hash(listing_id, new_hash)
            if push_to_queue(listing_id):
                print(f"   [{listing_id}] CHANGEMENT detecte -> sync_queue")
                changes += 1
            else:
                print(f"   [{listing_id}] Changement detecte mais echec queue")
        else:
            # Pas de changement
            update_checked_at(listing_id)

    return changes


def main():
    print("=" * 55)
    print("   iCal Watcher — Surveillance des calendriers")
    print(f"   Intervalle : {POLL_INTERVAL}s")
    print(f"   Supabase   : {SUPABASE_URL[:40]}...")
    print("=" * 55)

    cycle = 0
    while True:
        cycle += 1
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n--- Cycle {cycle} ({now}) ---")

        try:
            changes = check_all_icals()
            if changes:
                print(f"   {changes} changement(s) detecte(s)")
            else:
                print(f"   Aucun changement")
        except Exception as e:
            print(f"   ERREUR cycle: {e}")

        print(f"   Prochain check dans {POLL_INTERVAL}s...")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
