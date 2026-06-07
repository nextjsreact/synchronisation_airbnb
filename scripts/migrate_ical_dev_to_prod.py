"""
Migration dev → prod : URLs iCal Airbnb
========================================
Copie les URLs iCal depuis dev (source de vérité) vers prod :
  1. dev.property_sync_config.ical_url_airbnb  →  prod.lofts.airbnb_ical_url
  2. dev.property_sync_config.ical_url_airbnb  →  prod.property_sync_config (nouvelles lignes)
  3. dev.lofts.airbnb_ical_url (lofts dev SANS config) → prod.lofts.airbnb_ical_url + config

DÉCISIONS UTILISATEUR (validées) :
  - Baya (e934921b-dcbd-4f2b-811a-6cff08ffed28) : PRÉSERVER URL PROD (option Y)
  - Olympe (c74d6bf8-7efc-4c69-b542-6ff0ca317af7) : SKIP — pas de source dev
  - URL factice ".../ical/test.ics" (Golf view) : SKIP
  - URLs dev sans token (?t=, ?s=) : OK, on copie

GARANTIES :
  - Idempotent (peut être rejoué)
  - Skip Baya (préserve prod) et Olympe (pas de source)
  - Skip URLs factices
  - Vérifie que les 2 JWT pointent vers des projets DIFFÉRENTS
  - Vérifie que la clé PROD a ref = mhngbluefyucoesgcjoy
  - Mode --dry-run pour tester sans rien modifier
  - Confirmation interactive "GO PROD" avant écriture
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path

import requests

PROD_EXPECTED_REF = "mhngbluefyucoesgcjoy"
PRESERVE_PROD_IDS = {"e934921b-dcbd-4f2b-811a-6cff08ffed28"}  # Baya
SKIP_NO_SOURCE_IDS = {"c74d6bf8-7efc-4c69-b542-6ff0ca317af7"}  # Olympe
FAKE_URLS = {"https://www.airbnb.com/calendar/ical/test.ics"}


def load_env_file(path: str) -> dict:
    env = {}
    p = Path(path)
    if not p.exists():
        return env
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def decode_jwt_ref(token: str) -> str:
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64)).get("ref", "")
    except Exception:
        return ""


def rest_get(url, headers, params=None):
    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def rest_patch(url, headers, body):
    r = requests.patch(url, headers=headers, json=body, timeout=30)
    return r.status_code, r.text[:200]


def rest_post(url, headers, body):
    h = {**headers, "Prefer": "return=minimal"}
    r = requests.post(url, headers=h, json=body, timeout=30)
    return r.status_code, r.text[:200]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev-env", default=".env")
    ap.add_argument("--prod-env", default=".env.production")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args()

    dev_env = load_env_file(args.dev_env)
    prod_env = load_env_file(args.prod_env)
    dev_cfg = {
        "url": dev_env.get("NEXT_PUBLIC_SUPABASE_URL"),
        "key": dev_env.get("SUPABASE_SERVICE_ROLE_KEY"),
    }
    prod_cfg = {
        "url": prod_env.get("NEXT_PUBLIC_SUPABASE_URL"),
        "key": prod_env.get("SUPABASE_SERVICE_ROLE_KEY"),
    }
    if os.environ.get("DEV_SUPABASE_URL"):
        dev_cfg["url"] = os.environ["DEV_SUPABASE_URL"]
    if os.environ.get("DEV_SUPABASE_SERVICE_ROLE_KEY"):
        dev_cfg["key"] = os.environ["DEV_SUPABASE_SERVICE_ROLE_KEY"]
    if os.environ.get("PROD_SUPABASE_URL"):
        prod_cfg["url"] = os.environ["PROD_SUPABASE_URL"]
    if os.environ.get("PROD_SUPABASE_SERVICE_ROLE_KEY"):
        prod_cfg["key"] = os.environ["PROD_SUPABASE_SERVICE_ROLE_KEY"]

    if not all(dev_cfg.values()) or not all(prod_cfg.values()):
        print("❌ Config manquante. Fournis NEXT_PUBLIC_SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY")
        print(f"   dans {args.dev_env} (dev) et {args.prod_env} (prod)")
        print("   OU via env shell : DEV_SUPABASE_URL / DEV_SUPABASE_SERVICE_ROLE_KEY / PROD_*")
        sys.exit(1)

    dev_ref = decode_jwt_ref(dev_cfg["key"])
    prod_ref = decode_jwt_ref(prod_cfg["key"])
    print(f"🔍 DEV  ref: {dev_ref}  → {dev_cfg['url']}")
    print(f"🔍 PROD ref: {prod_ref}  → {prod_cfg['url']}")
    if dev_ref == prod_ref:
        print("❌ ERREUR CRITIQUE : DEV et PROD ont la même ref. Abandon.")
        sys.exit(1)
    if prod_ref != PROD_EXPECTED_REF:
        print(f"❌ ERREUR : la clé PROD ne pointe pas vers {PROD_EXPECTED_REF} (ref = {prod_ref})")
        sys.exit(1)

    dev_h = {"apikey": dev_cfg["key"], "Authorization": f"Bearer {dev_cfg['key']}"}
    prod_h = {"apikey": prod_cfg["key"], "Authorization": f"Bearer {prod_cfg['key']}"}

    print("\n📥 DEV : lecture property_sync_config + lofts...")
    dev_configs = rest_get(
        f"{dev_cfg['url']}/rest/v1/property_sync_config",
        dev_h, {"select": "loft_id,ical_url_airbnb,is_active", "ical_url_airbnb": "not.is.null"},
    )
    dev_config_by_loft = {c["loft_id"]: c for c in dev_configs if c.get("ical_url_airbnb")}
    print(f"  ✅ {len(dev_config_by_loft)} configs dev avec URL")

    dev_lofts = rest_get(
        f"{dev_cfg['url']}/rest/v1/lofts",
        dev_h, {"select": "id,airbnb_ical_url", "airbnb_ical_url": "not.is.null"},
    )
    dev_loft_url_by_id = {l["id"]: l["airbnb_ical_url"] for l in dev_lofts if l.get("airbnb_ical_url")}
    print(f"  ✅ {len(dev_loft_url_by_id)} lofts dev avec URL")

    print("\n📥 PROD : lecture lofts + property_sync_config...")
    prod_lofts = rest_get(f"{prod_cfg['url']}/rest/v1/lofts", prod_h, {"select": "id,name,airbnb_ical_url"})
    prod_loft_by_id = {l["id"]: l for l in prod_lofts}
    print(f"  ✅ {len(prod_loft_by_id)} lofts prod")
    prod_configs = rest_get(f"{prod_cfg['url']}/rest/v1/property_sync_config", prod_h, {"select": "loft_id"})
    prod_config_loft_ids = {c["loft_id"] for c in prod_configs}
    print(f"  ✅ {len(prod_config_loft_ids)} configs prod")

    to_patch, to_post, skip_baya, skip_no_source, skip_dev_only, skip_fake = [], [], [], [], [], []

    def consider(loft_id, dev_url):
        if loft_id not in prod_loft_by_id:
            skip_dev_only.append(loft_id)
            return
        if loft_id in PRESERVE_PROD_IDS:
            skip_baya.append((
                loft_id, prod_loft_by_id[loft_id]["name"],
                prod_loft_by_id[loft_id].get("airbnb_ical_url"), dev_url,
            ))
            return
        if loft_id in SKIP_NO_SOURCE_IDS:
            skip_no_source.append((loft_id, prod_loft_by_id[loft_id]["name"]))
            return
        if dev_url in FAKE_URLS:
            skip_fake.append((loft_id, prod_loft_by_id[loft_id]["name"]))
            return
        cur = prod_loft_by_id[loft_id].get("airbnb_ical_url")
        if cur != dev_url:
            to_patch.append((loft_id, dev_url, cur, prod_loft_by_id[loft_id]["name"]))
        if loft_id not in prod_config_loft_ids:
            to_post.append((loft_id, dev_url))

    for loft_id, conf in dev_config_by_loft.items():
        consider(loft_id, conf["ical_url_airbnb"])
    for loft_id, url in dev_loft_url_by_id.items():
        if loft_id in dev_config_by_loft:
            continue
        consider(loft_id, url)

    prod_no_url_no_source = [
        (lid, l["name"])
        for lid, l in prod_loft_by_id.items()
        if not l.get("airbnb_ical_url")
        and lid not in dev_config_by_loft
        and lid not in dev_loft_url_by_id
    ]

    print("\n" + "=" * 70)
    print("📋 PLAN DE MIGRATION")
    print("=" * 70)
    print(f"\n✅ PATCH prod.lofts.airbnb_ical_url ({len(to_patch)} lofts) :")
    for loft_id, new_url, cur, name in to_patch:
        cur_s = cur if cur else "(vide)"
        print(f"   • {name[:32]:32} | {cur_s[:40]:40} → {new_url[:50]}...")
    print(f"\n✅ POST prod.property_sync_config ({len(to_post)} nouvelles configs) :")
    for loft_id, url in to_post:
        print(f"   • {prod_loft_by_id[loft_id]['name'][:32]:32} | {url[:60]}...")
    print(f"\n⚠️  Baya (préservés, option Y) : {len(skip_baya)}")
    for lid, name, pu, du in skip_baya:
        print(f"   • {name} | prod={pu} | dev={du}")
    print(f"\n❌ Prod-only sans source dev (ex: Olympe) : {len(prod_no_url_no_source)}")
    for lid, name in prod_no_url_no_source:
        print(f"   • {name} (vide en prod, pas de source dev — à récupérer Airbnb manuellement)")
    print(f"\n❌ Dev-only (n'existent pas en prod) : {len(skip_dev_only)}")
    if skip_dev_only:
        for lid in skip_dev_only:
            print(f"   • {lid}")
    print(f"\n❌ URLs factices (test.ics) : {len(skip_fake)}")
    for lid, name in skip_fake:
        print(f"   • {name}")

    if args.dry_run:
        print("\n🔍 DRY-RUN : aucune modification.")
        return

    print(f"\n⚠️  Tu vas ÉCRIRE en PROD ({prod_cfg['url']}, ref={prod_ref})")
    if not args.yes:
        resp = input('Tape "GO PROD" pour confirmer : ')
        if resp.strip() != "GO PROD":
            print("Annulé.")
            return

    print("\n🚀 MIGRATION EN COURS...")
    ok_p, ko_p = 0, 0
    for loft_id, new_url, cur, name in to_patch:
        s, b = rest_patch(f"{prod_cfg['url']}/rest/v1/lofts?id=eq.{loft_id}", prod_h, {"airbnb_ical_url": new_url})
        if s in (200, 204):
            ok_p += 1
            print(f"  ✅ PATCH {name[:30]:30} | {s}")
        else:
            ko_p += 1
            print(f"  ❌ PATCH {name[:30]:30} | {s} {b[:80]}")

    ok_c, ko_c = 0, 0
    for loft_id, url in to_post:
        s, b = rest_post(
            f"{prod_cfg['url']}/rest/v1/property_sync_config",
            prod_h, {"loft_id": loft_id, "ical_url_airbnb": url, "is_active": True},
        )
        if s in (200, 201, 204):
            ok_c += 1
            print(f"  ✅ POST {prod_loft_by_id[loft_id]['name'][:30]:30} | {s}")
        else:
            ko_c += 1
            print(f"  ❌ POST {prod_loft_by_id[loft_id]['name'][:30]:30} | {s} {b[:80]}")

    print("\n" + "=" * 70)
    print("📊 RÉSULTAT")
    print("=" * 70)
    print(f"  PATCH lofts.airbnb_ical_url : {ok_p} ✅ / {ko_p} ❌")
    print(f"  POST property_sync_config   : {ok_c} ✅ / {ko_c} ❌")
    print(f"  Baya préservés              : {len(skip_baya)}")
    print(f"  Prod-only sans source       : {len(prod_no_url_no_source)}")
    print(f"  Dev-only (ignorés)          : {len(skip_dev_only)}")
    print(f"  URLs factices (ignorées)    : {len(skip_fake)}")


if __name__ == "__main__":
    main()
