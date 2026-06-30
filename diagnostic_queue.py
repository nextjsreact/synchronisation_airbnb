"""
diagnostic_queue.py — Diagnostic de la sync_queue et détection des réservations perdues
========================================================================================
Vérifie l'état de la sync_queue et identifie les problèmes potentiels.

Usage :
    python diagnostic_queue.py
"""

import os
import sys
from datetime import datetime, timedelta, timezone

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

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def supabase_get(endpoint, params=""):
    """Requête GET à Supabase.HTTP"""
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}{params}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"   ❌ Erreur requête {endpoint}: {e}")
        return None


def check_queue_status():
    """Vérifie l'état de la sync_queue."""
    print("\n" + "=" * 60)
    print("   📋 ÉTAT DE LA SYNC_QUEUE")
    print("=" * 60)

    # Récupérer toutes les entrées avec leur statut
    entries = supabase_get("sync_queue", "?select=*&order=created_at.desc&limit=100")

    if entries is None:
        print("   ❌ Impossible de récupérer la queue")
        return

    if not entries:
        print("   ⚠️  La sync_queue est vide !")
        return

    # Compteur par statut
    status_counts = {}
    for entry in entries:
        status = entry.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"\n Attaché total d'entrées (100 dernières): {len(entries)}")
    print("\n   📊 Répartition par statut:")
    for status, count in sorted(status_counts.items()):
        emoji = {
            "pending": "⏳",
            "processing": "🔄",
            "done": "✅",
            "error": "❌",
        }.get(status, "❓")
        print(f"      {emoji} {status}: {count}")

    # Détails des entrées en erreur
    error_entries = [e for e in entries if e.get("status") == "error"]
    if error_entries:
        print(f"\n   ❌ ENTRÉES EN ERREUR ({len(error_entries)}):")
        for entry in error_entries[:5]:  # Limiter à 5
            print(f"      - ID {entry['id']}: listing {entry.get('listing_id')}")
            print(f"        Erreur: {entry.get('error_message', 'N/A')[:100]}")
            print(f"        Créé: {entry.get('created_at')}")

    # Entrées bloquées en processing depuis longtemps
    processing_entries = [e for e in entries if e.get("status") == "processing"]
    if processing_entries:
        print(f"\n   🔄 ENTRÉES BLOQUÉES EN 'PROCESSING' ({len(processing_entries)}):")
        for entry in processing_entries[:5]:
            print(f"      - ID {entry['id']}: listing {entry.get('listing_id')}")
            print(f"        Depuis: {entry.get('——processed_at', 'N/A')}")

    # Entrées pending depuis très longtemps
    pending_entries = [e for e in entries if e.get("status") == "pending"]
    if pending_entries:
        old_pending = [
            e for e in pending_entries
            if e.get("created_at") and datetime.fromisoformat(e["created_at"].replace("Z", "+00:00")) < datetime.now(timezone.utc) - timedelta(hours=1)
        ]
        if old_pending:
            print(f"\n   ⏳ ENTRÉES PENDING DEPUIS >1H ({len(old_pending)}):")
            for entry in old_pending[:5]:
                print(f"      - ID {entry['id']}: listing {entry.get('listing_id')}")
                print(f"        Créé: {entry.get('created_at')}")
                print(f"        Retry count: {entry.get('retry_count', 0)}")

    return entries


def check_recent_reservations():
    """Vérifie les réservations récentes dans Supabase."""
    print("\n" + "=" * 60)
    print("   📊 RÉSERVATIONS RÉCENTES DANS SUPABASE")
    print("=" * 60)

    # Réservations des dernières 24h
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    reservations = supabase_get(
        "reservations",
        f"?select=id,voyageur,date_arrivee,statut,scraped_at,listing_id&created_at=gte.{yesterday}&order=created_at.desc&limit=20"
    )

    if reservations is None:
        print("   ❌ Impossible de récupérer les réservations")
        return

    if not reservations:
        print("   ⚠️  Aucune réservation dans les dernières 24h !")
        return

    print(f"\n   ✅ {len(reservations)} réservations dans les dernières 24h:")
    for r in reservations[:10]:
        voyageur = r.get('voyageur', 'Unknown')
        print(f"      - {r.get('id')}: {voyageur} | "
              f"Arrivée: {r.get('date_arrivee')} | Statut: {r.get('statut')}")

    return reservations


def check_ical_hashes():
    """Vérifie les hashes iCal pour détecter les problèmes."""
    print("\n" + "=" * 60)
    print("   📅 ÉTAT DES ICAL HASHES")
    print("=" * 60)

    hashes = supabase_get("ical_hashes", "?select=*&order=checked_at.desc&limit=50")

    if hashes is None:
        print("   ❌ Impossible de récupérer les hashes")
        return

    if not hashes:
        print("   ⚠️  Aucun hash iCal trouvé !")
        return

    print(f"\n   📊 {len(hashes)} hashes iCal trouvés")

    # Vérifier les hashes non vérifiés depuis longtemps
    now = datetime.now(timezone.utc)
    old_hashes = []
    for h in hashes:
        checked_at = h.get("checked_at")
        if checked_at:
            try:
                checked_dt = datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
                if (now - checked_dt) > timedelta(hours=2):
                    old_hashes.append(h)
            except:
                pass

    if old_hashes:
        print(f"\n   ⚠️  {len(old_hashes)} hashes non vérifiés depuis >2h:")
        for h in old_hashes[:5]:
            print(f"      - Listing {h['listing_id']}: dernière vérif {h.get('checked_at', 'N/A')}")
    else:
        print("   ✅ Tous les hashes sont à jour (< 2h)")

    return hashes


def main():
    print("=" * 60)
    print("   🔍 DIAGNOSTIC SYNC_QUEUE & RÉSERVATIONS")
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. État de la queue
    check_queue_status()

    # 2. Réservations récentes
    check_recent_reservations()

    # 3. État des iCal
    check_ical_hashes()

    print("\n" + "=" * 60)
    print("   ✅ DIAGNOSTIC TERMINÉ")
    print("=" * 60)


if __name__ == "__main__":
    main()
