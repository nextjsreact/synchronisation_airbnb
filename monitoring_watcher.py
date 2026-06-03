#!/usr/bin/env python3
"""
Monitoring watcher — alerte si aucune nouvelle reservation Airbnb n'est detectee
pendant 24h (par defaut).

Sortie:
- Ligne dans la table Supabase `system_alerts` (toujours)
- Email SMTP (si SMTP_HOST defini dans .env)
- Webhook Slack (si SLACK_WEBHOOK_URL defini dans .env)

Anti-spam: pas de nouvelle alerte pour le meme type <12h apres la derniere.
"""
import os
import sys
import time
import json
import smtplib
import requests
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM", "")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

POLL_INTERVAL_SEC = int(os.getenv("MONITORING_INTERVAL", "3600"))  # 1h par defaut
ALERT_THRESHOLD_HOURS = int(os.getenv("ALERT_THRESHOLD_HOURS", "24"))
ALERT_COOLDOWN_HOURS = int(os.getenv("ALERT_COOLDOWN_HOURS", "12"))

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[MONITORING] ERREUR: NEXT_PUBLIC_SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY manquant", flush=True)
    sys.exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


def supa_get(path: str) -> list:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json() if r.text else []


def supa_post(path: str, body: dict):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{path}", headers=HEADERS, json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def count_new_reservations(hours: int) -> int:
    """Compte les reservations Airbnb creees/modifiees dans les N dernieres heures."""
    # Format Z (UTC) sans microsecondes — plus compatible PostgREST
    threshold = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Utiliser params= pour que requests URL-encode correctement
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/reservations",
        params={
            "select": "id",
            "source": "eq.airbnb_scraper",
            "created_at": f"gte.{threshold}",
            "limit": 1,
        },
        headers={**HEADERS, "Prefer": "count=exact"},
        timeout=30,
    )
    r.raise_for_status()
    content_range = r.headers.get("content-range", "0/0")
    count = int(content_range.split("/")[-1])
    return count


def get_last_alert(alert_type: str) -> dict | None:
    """Recupere la derniere alerte du type donne."""
    rows = supa_get(
        f"system_alerts?type=eq.{alert_type}&order=created_at.desc&limit=1"
    )
    return rows[0] if rows else None


def insert_alert(alert_type: str, severity: str, title: str, message: str, metadata: dict) -> int:
    """Insere une alerte en base."""
    body = {
        "type": alert_type,
        "severity": severity,
        "title": title,
        "message": message,
        "metadata": metadata,
    }
    supa_post("system_alerts", body)
    print(f"   [ALERTE] {severity.upper()}: {title}", flush=True)
    return 1


def send_email(title: str, message: str) -> bool:
    """Envoie un email via SMTP si configure."""
    if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD and ALERT_EMAIL_TO):
        return False
    try:
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = f"[Airbnb Monitoring] {title}"
        msg["From"] = ALERT_EMAIL_FROM or SMTP_USER
        msg["To"] = ALERT_EMAIL_TO

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as srv:
            srv.starttls()
            srv.login(SMTP_USER, SMTP_PASSWORD)
            srv.send_message(msg)
        print(f"   [EMAIL] envoye a {ALERT_EMAIL_TO}", flush=True)
        return True
    except Exception as e:
        print(f"   [EMAIL] ERREUR: {e}", flush=True)
        return False


def send_slack(title: str, message: str) -> bool:
    """Envoie une notification Slack si le webhook est configure."""
    if not SLACK_WEBHOOK_URL:
        return False
    try:
        payload = {
            "text": f"*{title}*\n{message}",
        }
        r = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=15)
        r.raise_for_status()
        print(f"   [SLACK] envoye", flush=True)
        return True
    except Exception as e:
        print(f"   [SLACK] ERREUR: {e}", flush=True)
        return False


def notify_all(title: str, message: str):
    """Declenche tous les canaux de notification."""
    sent = 0
    if send_email(title, message):
        sent += 1
    if send_slack(title, message):
        sent += 1
    if sent == 0:
        print(f"   [NOTIFY] Aucun canal configure (table system_alerts uniquement)", flush=True)


def check_no_new_reservations():
    """Verifie qu'il y a eu des nouvelles reservations dans la fenetre."""
    print(f"   [CHECK] Comptage des reservations (seuil: {ALERT_THRESHOLD_HOURS}h)...", flush=True)
    count = count_new_reservations(ALERT_THRESHOLD_HOURS)
    print(f"   [CHECK] {count} reservation(s) Airbnb dans les dernieres {ALERT_THRESHOLD_HOURS}h", flush=True)

    if count > 0:
        return  # tout va bien

    # 0 reservation : verifier le cooldown
    last = get_last_alert("no_new_reservations")
    if last:
        last_ts = datetime.fromisoformat(last["created_at"].replace("Z", "+00:00"))
        age = datetime.now(timezone.utc) - last_ts
        if age < timedelta(hours=ALERT_COOLDOWN_HOURS):
            cooldown_left = timedelta(hours=ALERT_COOLDOWN_HOURS) - age
            print(
                f"   [COOLDOWN] Derniere alerte il y a {age.total_seconds() / 3600:.1f}h "
                f"(prochaine possible dans {cooldown_left.total_seconds() / 3600:.1f}h)",
                flush=True,
            )
            return

    # Declencher l'alerte
    title = f"Aucune nouvelle reservation Airbnb depuis {ALERT_THRESHOLD_HOURS}h"
    message = (
        f"Le systeme n'a detecte aucune nouvelle reservation Airbnb "
        f"(source=airbnb_scraper) depuis {ALERT_THRESHOLD_HOURS}h.\n\n"
        f"Causes possibles:\n"
        f"  - Airbnb bloque / login expire\n"
        f"  - targeted-scraper ou ical-watcher crashed\n"
        f"  - Tous les lofts reelement vides (verifier manuellement)\n\n"
        f"Action: docker compose -f D:\\Airbnb_transfer_v2\\docker-compose.sync.yml ps"
    )
    metadata = {
        "threshold_hours": ALERT_THRESHOLD_HOURS,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    insert_alert("no_new_reservations", "warning", title, message, metadata)
    notify_all(title, message)


def main():
    print("=" * 70, flush=True)
    print("   MONITORING WATCHER — Alertes Airbnb 24h", flush=True)
    print("=" * 70, flush=True)
    print(f"   Poll interval       : {POLL_INTERVAL_SEC}s", flush=True)
    print(f"   Alert threshold     : {ALERT_THRESHOLD_HOURS}h sans nouvelle resa", flush=True)
    print(f"   Alert cooldown      : {ALERT_COOLDOWN_HOURS}h (anti-spam)", flush=True)
    print(f"   Email notifications : {'actives' if SMTP_HOST else 'inactives'}", flush=True)
    print(f"   Slack notifications : {'actives' if SLACK_WEBHOOK_URL else 'inactives'}", flush=True)
    print("=" * 70, flush=True)

    # Check immediat au demarrage
    while True:
        try:
            check_no_new_reservations()
        except Exception as e:
            print(f"   [ERREUR] {e}", flush=True)

        print(f"   Prochain check dans {POLL_INTERVAL_SEC}s...", flush=True)
        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
