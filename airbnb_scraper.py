"""
airbnb_scraper.py — Scrape complet Airbnb
==========================================
Version  : 2.0.0
Auteur   : Karim TIGUI
Date     : Mai 2026

Changements v2 vs v1 :
  + Pousse les réservations vers Supabase (upsert)
  + Collecte les URLs iCal de chaque annonce
  + Peuple la table listings pour le iCal Watcher
  + Log de synchronisation dans sync_logs
  + Garde l'export CSV + JSON local en parallèle

Dépendances :
    pip install cloakbrowser pyotp requests pandas

Usage :
    python airbnb_scraper.py
"""

import json
import csv
import os
import re
import sys
import time
from datetime import datetime

# Forcer UTF-8 sur Windows (évite UnicodeEncodeError avec les emojis)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# ── CloakBrowser avec fallback Playwright ───────────────────
try:
    from cloakbrowser import launch as cloak_launch
    USE_CLOAKBROWSER = True
except ImportError:
    USE_CLOAKBROWSER = False

# ── Client API Next.js (v2.0.1) ─────────────────────────────
try:
    from airbnb_api_client import (
        upsert_reservations,
        upsert_listings,
        log_sync,
        check_api_health,
    )
    USE_API = True
except Exception as e:
    print(f"⚠️  API Next.js désactivée : {e}")
    USE_API = False


# ============================================================
# CONFIGURATION — variables d'environnement (.env)
# ============================================================
EMAIL       = os.environ.get("AIRBNB_EMAIL",    "votre@email.com")
PASSWORD    = os.environ.get("AIRBNB_PASSWORD", "votre_mot_de_passe")
TOTP_SECRET = os.environ.get("TOTP_SECRET",     "")
SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "airbnb_session.json")
# Auto-encoder en base32 si nécessaire (pyotp exige du base32 : A-Z + 2-7)
if TOTP_SECRET:
    import base64 as _b64
    import re as _re
    if not _re.match(r'^[A-Z2-7]+=*$', TOTP_SECRET.upper()):
        TOTP_SECRET = _b64.b32encode(TOTP_SECRET.encode()).decode().rstrip("=")
        print(f"   ℹ️  TOTP_SECRET auto-encodé en base32 : {TOTP_SECRET}")
OUTPUT_CSV  = os.environ.get("OUTPUT_CSV",      "output/reservations_airbnb.csv")
OUTPUT_JSON = os.environ.get("OUTPUT_JSON",     "output/reservations_airbnb.json")
HEADLESS    = os.environ.get("HEADLESS", "false").lower() == "true"
PROXY_URL   = os.environ.get("PROXY_URL", "")  # ex: http://user:pass@residential-proxy:port
# ============================================================


# ============================================================
# AUTHENTIFICATION
# ============================================================

def handle_2fa(page):
    """Gère la vérification 2FA — SMS, Email ou TOTP."""
    print("\n🔒 Vérification 2FA détectée...")
    page_text = page.inner_text("body").lower()

    # Étape 1 : Si on est sur la page de sélection de méthode (SMS/Email),
    # cliquer sur "E-mail" pour recevoir le code
    email_btn = page.locator('button:has-text("E-mail"), button:has-text("Email")').first
    try:
        if email_btn.is_visible(timeout=3000):
            print("   📧 Sélection de la méthode E-mail...")
            email_btn.click()
            time.sleep(3)
            page_text = page.inner_text("body").lower()
    except Exception:
        pass

    # Étape 2 : Générer et saisir le code TOTP
    if TOTP_SECRET:
        try:
            import pyotp
            code = pyotp.TOTP(TOTP_SECRET).now()
            print(f"🔑 Code TOTP généré automatiquement : {code}")
            time.sleep(2)  # Attendre que le champ soit rendu
            _saisir_code(page, code)
            return
        except ImportError:
            print("⚠️  pyotp non installé — pip install pyotp")

    raise RuntimeError("2FA impossible — configurez TOTP_SECRET dans .env")


def _saisir_code(page, code):
    """Saisit le code 2FA dans le formulaire Airbnb."""
    try:
        # Attendre que le formulaire 2FA soit rendu (SPA dynamique)
        selectors = [
            '#otp-code-input',
            'input[name="code"]',
            'input[type="tel"]',
            'input[autocomplete="one-time-code"]',
            'input[autocomplete="one-time-code"]',
            'input[inputmode="numeric"]',
            'input[type="number"]',
        ]

        field = None
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                loc.wait_for(state="visible", timeout=10000)
                field = loc
                print(f"   ✓ Champ OTP trouvé : {sel}")
                break
            except Exception:
                continue

        if field:
            field.fill(code)
            time.sleep(0.5)
            page.keyboard.press("Enter")
            time.sleep(3)
            print("✅ Code 2FA saisi !")
            return

        # Fallback : cases individuelles (maxlength=1)
        boxes = page.locator('input[maxlength="1"]')
        try:
            boxes.first.wait_for(state="visible", timeout=5000)
            if boxes.count() >= 4:
                for i, digit in enumerate(code[:boxes.count()]):
                    boxes.nth(i).fill(digit)
                    time.sleep(0.1)
                page.keyboard.press("Enter")
                time.sleep(3)
                print("✅ Code 2FA saisi chiffre par chiffre !")
                return
        except Exception:
            pass

        # Dernier fallback : taper le code directement
        print(f"   ℹ️  Aucun champ OTP trouvé, saisie clavier directe...")
        page.keyboard.type(code, delay=100)
        time.sleep(0.5)
        page.keyboard.press("Enter")
        time.sleep(3)
        print("✅ Code 2FA saisi par clavier !")

    except Exception as e:
        print(f"⚠️  Erreur saisie code : {e}")


def login(page):
    """Connexion à Airbnb avec gestion complète du 2FA."""
    print("🔐 Connexion à Airbnb...")

    # Augmenter le timeout et utiliser domcontentloaded (plus rapide que load)
    try:
        page.goto("https://www.airbnb.com/login", timeout=60000, wait_until="domcontentloaded")
        print("   ✓ Page chargée")
    except Exception as e:
        print(f"   ⚠️  Timeout lors du chargement de la page")
        print(f"   ℹ️  Erreur: {str(e)[:100]}")
        print(f"   ℹ️  Tentative de continuation...")
        # La page peut être partiellement chargée, on continue
    
    page.wait_for_timeout(5000)

    for btn_text in [
        "Continuer avec l'e-mail",
        "Continue with email",
        "Se connecter par e-mail",
    ]:
        try:
            btn = page.locator(f"text={btn_text}")
            if btn.count() > 0:
                btn.first.click()
                page.wait_for_timeout(2000)
                break
        except Exception:
            continue

    # Remplir email
    email_filled = False
    for selector in [
        'input[type="email"]', 'input[name="email"]',
        'input[id*="email" i]', 'input[placeholder*="mail" i]',
        'input[type="text"]',
    ]:
        try:
            field = page.locator(selector).first
            if field.count() > 0 and field.is_visible():
                field.fill(EMAIL)
                email_filled = True
                print(f"   ✓ Email saisi")
                break
        except Exception:
            continue

    if not email_filled:
        raise RuntimeError("Champ email introuvable")

    page.wait_for_timeout(500)
    # Cliquer sur le bouton submit — multi-selectors pour robustesse
    submitted = False
    for btn_sel in [
        'button[type="submit"]',
        'button[data-testid="signup-login-submit-btn"]',
        'button:has-text("Continue")',
        'button:has-text("Continuer")',
    ]:
        try:
            btn = page.locator(btn_sel)
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click()
                submitted = True
                break
        except Exception:
            continue
    if not submitted:
        # Fallback: press Enter
        page.keyboard.press("Enter")
    page.wait_for_timeout(3000)

    # Vérifier si on est déjà redirigé (pas besoin de mot de passe)
    current_url = page.url
    page_html = page.content().lower()  # Utiliser content() au lieu de inner_text() pour capturer les iframes
    page_content = page.inner_text("body").lower()
    print(f"   🔍 URL après email : {current_url}")
    
    # Détecter CAPTCHA après soumission email (vérifier dans le HTML complet)
    is_captcha_after_email = any(kw in page_html for kw in [
        "captcha", "robot", "verify you are human", "verify you're human",
        "vérifiez que vous êtes", "prouvez que", "je ne suis pas un robot",
        "security check", "vérification de sécurité", "unusual activity",
        "arkose", "arkoselabs"
    ])
    
    if is_captcha_after_email:
        print("\n⚠️  ═══════════════════════════════════════════════════════")
        print("   🤖 CAPTCHA DÉTECTÉ APRÈS EMAIL")
        print("   ═══════════════════════════════════════════════════════")
        print("\n   Airbnb utilise Arkose Labs pour la vérification de sécurité.")
        print("\n   📋 ACTIONS :")
        print("   1. ✅ Résolvez le CAPTCHA MANUELLEMENT dans le navigateur ouvert")
        print("   2. ⏱️  Le script attendra jusqu'à 15 minutes")
        print("   3. 🔄 Une fois résolu, le script continuera automatiquement")
        print("\n   💡 PRÉVENTION pour les prochaines fois :")
        print("   • Configurez un proxy résidentiel (PROXY_URL dans .env)")
        print("   • La session sera sauvegardée après ce CAPTCHA")
        print("   • Les prochaines exécutions réutiliseront la session")
        print("   • Vous ne devriez plus voir de CAPTCHA après")
        print("\n   ⏳ En attente de résolution manuelle...")
        print("   ═══════════════════════════════════════════════════════\n")

        # Attendre que le CAPTCHA soit résolu (max 15 minutes)
        captcha_resolved = False
        for i in range(450):  # 450 * 2s = 15 minutes
            time.sleep(2)
            current_url = page.url
            current_html = page.content().lower()
            current_content = page.inner_text("body").lower()
            
            # Debug : sauvegarder une capture d'écran toutes les 30 secondes
            if (i + 1) % 15 == 0:  # 15 * 2s = 30s
                screenshot_path = os.path.join(os.path.dirname(OUTPUT_JSON) or ".", f"debug_captcha_{(i+1)*2}s.png")
                try:
                    page.screenshot(path=screenshot_path)
                    print(f"   📸 Capture sauvegardée : {screenshot_path}")
                except Exception:
                    pass
            
            # Debug : afficher l'URL et vérifier la présence du champ password
            if (i + 1) % 10 == 0:  # Toutes les 20 secondes
                has_password_field = "password" in current_content or "mot de passe" in current_content
                print(f"   🔍 Debug: URL={current_url[:50]}... | Password field={has_password_field}")
            
            # Vérifier si on a quitté la page de CAPTCHA/login
            is_login_page = any(kw in current_url for kw in ["login", "signin", "challenge"])
            if not is_login_page:
                # Vérifier qu'il n'y a plus de CAPTCHA dans le contenu
                still_captcha = any(kw in current_html for kw in [
                    "captcha", "robot", "verify you are human", "security check", "arkose"
                ])
                if not still_captcha:
                    captcha_resolved = True
                    print("\n   ✅ CAPTCHA résolu ! Continuation du script...")
                    break

            # Vérifier si le champ mot de passe est apparu (signe que CAPTCHA est résolu)
            if "password" in current_content or "mot de passe" in current_content:
                captcha_resolved = True
                print("\n   ✅ CAPTCHA résolu ! Champ mot de passe détecté...")
                break

            # Vérifier si on est sur une page de vérification email / 2FA / confirmation
            verification_keywords = ["confirmez", "confirm", "code de vérification",
                                     "verification code", "nous avons envoyé", "we sent",
                                     "entrez le code", "enter the code", "otp"]
            if any(kw in current_content for kw in verification_keywords):
                captcha_resolved = True
                print("\n   ✅ CAPTCHA résolu ! Page de vérification détectée...")
                break

            # Vérifier les URLs de pages connectées / 2FA / vérification
            logged_in_urls = ["/host/", "/trips", "/account", "/hosting", "/home",
                              "verification", "two-factor", "authenticate"]
            if any(kw in current_url for kw in logged_in_urls):
                captcha_resolved = True
                print("\n   ✅ CAPTCHA résolu ! Redirection détectée...")
                break

            # Vérifier si un champ de code OTP/input est apparu
            if any(kw in current_html for kw in ["otp-code-input", "code-input", "inputmode=\"numeric\""]):
                captcha_resolved = True
                print("\n   ✅ CAPTCHA résolu ! Champ de code détecté...")
                break

            # Afficher un point toutes les 10 secondes
            if (i + 1) % 5 == 0:
                elapsed = (i + 1) * 2
                print(f"   ⏳ {elapsed}s écoulées... (max 900s)")

        if not captcha_resolved:
            # Vérifier une dernière fois si l'utilisateur s'est connecté manuellement dans le VNC
            current_url = page.url
            still_on_login = any(kw in current_url for kw in ["login", "signin"])
            if not still_on_login:
                print("\n   ✅ Connexion manuelle détectée ! Sauvegarde de la session...")
                captcha_resolved = True
            else:
                raise Exception("❌ Timeout CAPTCHA — 15 minutes écoulées sans résolution")
        
        time.sleep(3)
        current_url = page.url
        page_content = page.inner_text("body").lower()
        print(f"   🔍 URL après CAPTCHA : {current_url}")
    
    if "login" not in current_url and "signin" not in current_url:
        print("   ℹ️  Déjà redirigé après email, pas besoin de mot de passe")
        # Peut-être un lien magique ou une autre méthode
        # Continuer directement à la vérification
    else:
        # Remplir mot de passe — attendre qu'il apparaisse
        password_filled = False
        for attempt in range(3):
            for selector in ['input[type="password"]', 'input[name="password"]', 'input[autocomplete="current-password"]']:
                try:
                    field = page.locator(selector).first
                    if field.count() > 0 and field.is_visible():
                        field.fill(PASSWORD)
                        password_filled = True
                        print(f"   ✓ Mot de passe saisi")
                        break
                except Exception:
                    continue
            if password_filled:
                break
            page.wait_for_timeout(2000)
        
        if not password_filled:
            # Sauvegarder la page pour debug
            debug_path = os.path.join(os.path.dirname(OUTPUT_JSON) or ".", "debug_no_password_field.html")
            os.makedirs(os.path.dirname(debug_path) or ".", exist_ok=True)
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(page.content())
            print(f"   🔍 Page sauvegardée : {debug_path}")
            
            # Vérifier si c'est un lien magique
            page_text = page.inner_text("body").lower()
            if any(kw in page_text for kw in ["email", "lien", "link", "check your", "vérifiez"]):
                print("\n   📧 Airbnb semble utiliser un lien magique par email")
                print("   ➤ Vérifiez votre boîte mail et cliquez sur le lien")
                print("   ➤ Le script attendra que vous soyez connecté...")
                
                # Attendre que l'utilisateur clique sur le lien
                for _ in range(120):  # 4 minutes
                    time.sleep(2)
                    if "login" not in page.url and "signin" not in page.url:
                        print("   ✅ Connexion détectée via lien email !")
                        break
                else:
                    raise RuntimeError("Timeout — lien email non cliqué dans les 4 minutes")
            else:
                raise RuntimeError(f"Champ mot de passe introuvable — voir {debug_path}")

    # Détecter 2FA ou CAPTCHA
    current_url  = page.url
    page_content = page.inner_text("body").lower()
    
    print(f"   🔍 URL actuelle : {current_url}")
    
    # Si on n'a pas saisi de mot de passe, on skip la soumission
    if password_filled:
        page.wait_for_timeout(500)
        # Cliquer sur le bouton submit — multi-selectors pour robustesse
        submitted = False
        for btn_sel in [
            'button[type="submit"]',
            'button[data-testid="login-btn"]',
            'button:has-text("Continue")',
            'button:has-text("Continuer")',
            'button:has-text("Se connecter")',
            'button:has-text("Log in")',
        ]:
            try:
                btn = page.locator(btn_sel)
                if btn.count() > 0 and btn.first.is_visible():
                    print(f"   ✓ Bouton trouvé : {btn_sel}")
                    btn.first.click()
                    submitted = True
                    break
            except Exception as e:
                continue
        if not submitted:
            # Fallback: press Enter
            print("   ℹ️  Aucun bouton trouvé, utilisation de Enter")
            page.keyboard.press("Enter")
        
        print("   ⏳ Attente de la réponse du serveur...")
        page.wait_for_timeout(8000)  # Augmenté à 8 secondes
        
        # Mettre à jour l'URL et le contenu
        current_url  = page.url
        page_content = page.inner_text("body").lower()
        print(f"   🔍 URL après mot de passe : {current_url}")
    
    # Détecter CAPTCHA
    is_captcha = any(kw in page_content for kw in [
        "captcha", "robot", "verify you are human", "verify you're human",
        "vérifiez que vous êtes", "prouvez que", "je ne suis pas un robot",
        "security check", "vérification de sécurité", "unusual activity"
    ])
    
    if is_captcha:
        print("\n⚠️  ═══════════════════════════════════════════════════════")
        print("   🤖 CAPTCHA DÉTECTÉ")
        print("   ═══════════════════════════════════════════════════════")
        print("\n   CloakBrowser ne peut PAS résoudre les CAPTCHAs automatiquement.")
        print("\n   📋 SOLUTIONS :")
        print("   1. ✅ Résolvez le CAPTCHA MANUELLEMENT dans le navigateur ouvert")
        print("   2. ⏱️  Le script attendra jusqu'à 15 minutes")
        print("   3. 🔄 Une fois résolu, le script continuera automatiquement")
        print("\n   💡 PRÉVENTION pour les prochaines fois :")
        print("   • Configurez un proxy résidentiel (PROXY_URL dans .env)")
        print("   • La session sera sauvegardée après ce CAPTCHA")
        print("   • Les prochaines exécutions réutiliseront la session")
        print("   • Vous ne devriez plus voir de CAPTCHA après")
        print("\n   ⏳ En attente de résolution manuelle...")
        print("   ═══════════════════════════════════════════════════════\n")

        # Attendre que le CAPTCHA soit résolu (max 15 minutes)
        captcha_resolved = False
        for i in range(450):  # 450 * 2s = 15 minutes
            time.sleep(2)
            current_url = page.url
            current_content = page.inner_text("body").lower()
            
            # Vérifier si on a quitté la page de CAPTCHA
            if "login" not in current_url and "signin" not in current_url and "challenge" not in current_url:
                # Vérifier qu'il n'y a plus de CAPTCHA dans le contenu
                still_captcha = any(kw in current_content for kw in [
                    "captcha", "robot", "verify you are human", "security check"
                ])
                if not still_captcha:
                    captcha_resolved = True
                    print("\n   ✅ CAPTCHA résolu ! Continuation du script...")
                    break
            
            # Afficher un point toutes les 10 secondes
            if (i + 1) % 5 == 0:
                elapsed = (i + 1) * 2
                print(f"   ⏳ {elapsed}s écoulées... (max 900s)")

        if not captcha_resolved:
            raise Exception("❌ Timeout CAPTCHA — 15 minutes écoulées sans résolution")

        time.sleep(3)
        current_url = page.url
        print(f"   🔍 URL après CAPTCHA : {current_url}")

    # Détecter 2FA
    is_2fa = (
        any(kw in current_url for kw in ["verification", "two-factor", "code"])
        or any(kw in page_content for kw in [
            "code de vérification", "verification code",
            "two-step", "sms", "one-time"
        ])
    )

    if is_2fa:
        handle_2fa(page)
    else:
        print("✅ Connecté sans 2FA !")

    time.sleep(3)

    # Vérifier qu'on n'est plus sur la page de login
    current_url = page.url
    print(f"   🔍 URL finale : {current_url}")
    
    if "login" in current_url or "signin" in current_url:
        # Sauvegarder la page pour debug
        debug_path = os.path.join(os.path.dirname(OUTPUT_JSON) or ".", "debug_login_failed.html")
        os.makedirs(os.path.dirname(debug_path) or ".", exist_ok=True)
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(page.content())
        print(f"   🔍 Page sauvegardée pour debug : {debug_path}")
        raise Exception(f"❌ Échec de connexion — toujours sur page login. Vérifiez {debug_path}")

    print("✅ Connexion réussie !")

    # Sauvegarder la session pour les prochains lancements
    try:
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        page.context.storage_state(path=SESSION_FILE)
        print(f"   💾 Session sauvegardée : {SESSION_FILE}")
    except Exception as e:
        print(f"   ⚠️  Impossible de sauvegarder la session : {e}")


def is_logged_in(page):
    """Vérifie si la session est encore valide (pas besoin de login)."""
    try:
        page.goto("https://www.airbnb.com/hosting/reservations/upcoming",
                   wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        # Si on est redirigé vers login, la session est expirée
        if "login" in page.url or "signin" in page.url:
            return False
        return True
    except Exception:
        return False


# ============================================================
# COLLECTE DES URLS iCAL (NOUVEAU EN V2)
# ============================================================

def collect_ical_urls(page, listing_ids: list[str]) -> dict[str, str]:
    """
    Collecte les URLs iCal pour chaque annonce.
    Visite la page de disponibilité de chaque annonce.
    Retourne un dict {listing_id: ical_url}
    
    Note: L'URL iCal Airbnb contient 'calendarAccessSignature' comme paramètre.
    """
    print(f"\n📅 Collecte des URLs iCal pour {len(listing_ids)} annonces...")

    ical_urls = {}
    failed    = 0

    # Mode debug : tester sur les 3 premières annonces seulement
    DEBUG_ICAL = os.environ.get("DEBUG_ICAL", "false").lower() == "true"

    for i, listing_id in enumerate(listing_ids):
        try:
            url = f"https://www.airbnb.com/hosting/listings/{listing_id}/availability"
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)

            # Attendre que la page soit complètement chargée
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                page.wait_for_timeout(3000)

            ical_url = None

            # Debug : screenshot sur les 3 premières annonces
            if i < 3:
                debug_path = os.path.join(os.path.dirname(OUTPUT_JSON) or ".", f"debug_ical_{listing_id}.png")
                try:
                    page.screenshot(path=debug_path, full_page=True)
                    print(f"   📸 Debug iCal screenshot: debug_ical_{listing_id}.png")
                except Exception:
                    pass
                # Debug HTML
                html_path = os.path.join(os.path.dirname(OUTPUT_JSON) or ".", f"debug_ical_{listing_id}.html")
                try:
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(page.content())
                    print(f"   📄 Debug iCal HTML: debug_ical_{listing_id}.html")
                except Exception:
                    pass

            # Méthode 1 : chercher dans les inputs (URL complète avec signature)
            try:
                ical_url = page.evaluate("""
                    () => {
                        const inputs = document.querySelectorAll('input[type="text"], input[type="url"], input[readonly]');
                        for (const inp of inputs) {
                            if (inp.value && inp.value.includes('calendar/ical/') && inp.value.includes('calendarAccessSignature'))
                                return inp.value;
                        }
                        const links = document.querySelectorAll('a[href*="ical"], a[href*=".ics"]');
                        for (const link of links) {
                            if (link.href.includes('calendarAccessSignature'))
                                return link.href;
                        }
                        return null;
                    }
                """)
            except Exception:
                pass

            # Méthode 2 : regex dans le HTML pour URL iCal signée
            if not ical_url:
                content = page.content()
                for pattern in [
                    r'https://www\.airbnb\.com/calendar/ical/[\w.?=&%+\-]+',
                    r'airbnb\.com/calendar/ical/[^\s"\'<>]+',
                ]:
                    match = re.search(pattern, content)
                    if match:
                        ical_url = match.group(0)
                        break

            # Méthode 3 : JavaScript fallback
            if not ical_url:
                ical_url = page.evaluate(r"""
                    () => {
                        const links = document.querySelectorAll('a[href*="ical"], a[href*=".ics"]');
                        if (links.length > 0) return links[0].href;
                        const text = document.body.innerText;
                        const m = text.match(/https:\/\/www\.airbnb\.com\/calendar\/ical\/[^\s]+/);
                        return m ? m[0] : null;
                    }
                """)

            # Nettoyer l'URL
            if ical_url:
                ical_url = ical_url.rstrip("',\";)}]")
                if not ical_url.startswith("https://"):
                    ical_url = "https://" + ical_url
                ical_urls[listing_id] = ical_url
                if (i + 1) % 10 == 0:
                    print(f"   ↳ {i+1}/{len(listing_ids)} traitées...")
            else:
                failed += 1

            time.sleep(1.0)  # Pause polie (Airbnb est sensible au rate limiting)

        except Exception as e:
            failed += 1
            if failed <= 3:
                print(f"   ⚠️  Erreur iCal pour {listing_id}: {e}")

    print(f"   ✅ {len(ical_urls)} URLs iCal collectées ({failed} échouées)")
    return ical_urls


# ============================================================
# PARSING DES RÉSERVATIONS (votre logique v1 conservée)
# ============================================================

def _extract_field(node, *paths, default=""):
    for path in paths:
        try:
            obj = node
            for key in path:
                if isinstance(obj, dict):
                    obj = obj[key]
                elif isinstance(obj, list) and isinstance(key, int) and key < len(obj):
                    obj = obj[key]
                else:
                    obj = None
                    break
            if obj is not None and obj != "":
                return obj
        except (KeyError, IndexError, TypeError):
            continue
    return default


def _parse_earnings(earnings_str):
    if not earnings_str or not isinstance(earnings_str, str):
        return 0, "GBP"
    cleaned  = earnings_str.strip().replace("\u00a0", "").replace(" ", "")
    currency = "GBP"
    if "€" in cleaned:
        currency = "EUR"
        cleaned  = cleaned.replace("€", "")
    elif "$" in cleaned:
        currency = "USD"
        cleaned  = cleaned.replace("$", "")
    elif "£" in cleaned:
        currency = "GBP"
        cleaned  = cleaned.replace("£", "")
    cleaned = cleaned.replace(",", ".").strip()
    try:
        return float(cleaned), currency
    except ValueError:
        return 0, currency


def _parse_reservation_node(node):
    earnings_raw = node.get("earnings", "")
    if isinstance(earnings_raw, dict):
        montant = earnings_raw.get("amount", 0)
        devise  = earnings_raw.get("currency", "GBP")
    else:
        montant, devise = _parse_earnings(earnings_raw)

    guest_count = _extract_field(node,
        ["guest_details", "number_of_guests"],
        ["guest_details", "number_of_adults"],
        ["guest_count"], ["guestCount"], ["numberOfGuests"],
        default=0)

    voyageur = _extract_field(node,
        ["guest_user", "full_name"],
        ["guest_user", "first_name"],
        ["guest", "first_name"], ["guest", "name"], ["guestName"],
        default="")

    statut = _extract_field(node,
        ["user_facing_status_localized"],
        ["user_facing_status_key"],
        ["status"], ["reservationStatus"],
        default="")

    logement = _extract_field(node,
        ["listing_name"], ["listingName"],
        ["listing", "name"], ["listing", "title"],
        default="")

    date_creation = _extract_field(node,
        ["booked_date"], ["created_at"], ["createdAt"],
        default="")

    return {
        "id":            _extract_field(node, ["confirmation_code"], ["confirmationCode"], ["id"], default=""),
        "statut":        statut,
        "voyageur":      voyageur,
        "nb_voyageurs":  guest_count,
        "logement":      logement,
        "listing_id":    _extract_field(node, ["listing_id"], ["listingId"], default=""),
        "date_arrivee":  _extract_field(node, ["start_date"], ["checkIn"], ["check_in"], default=""),
        "date_depart":   _extract_field(node, ["end_date"], ["checkOut"], ["check_out"], default=""),
        "nb_nuits":      _extract_field(node, ["nights"], ["nightsCount"], default=0),
        "montant_total": montant,
        "devise":        devise,
        "date_creation": date_creation,
    }


# ============================================================
# SCRAPING DES RÉSERVATIONS (votre logique v1 conservée)
# ============================================================

def get_reservations(page):
    """Récupère les réservations via l'API GraphQL interne d'Airbnb."""
    print("📋 Récupération des réservations (API GraphQL)...")

    all_reservations = []
    debug_saved      = False
    offset = 0
    limit  = 40

    page.goto("https://www.airbnb.com/hosting")
    page.wait_for_timeout(3000)

    while True:
        response = page.evaluate("""
            ({ offset, limit }) => {
                return fetch('/api/v3/HostReservationsList', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Airbnb-API-Key': document.cookie.match(/key=([^;]+)/)?.[1] || ''
                    },
                    body: JSON.stringify({
                        operationName: 'HostReservationsList',
                        variables: { first: limit, skip: offset, status: 'all' }
                    })
                })
                .then(r => r.json())
                .catch(() => null);
            }
        """, {"offset": offset, "limit": limit})

        if not response or "errors" in str(response):
            print(f"   ⚠️  API GraphQL vide ou erreur")
            break

        if not debug_saved:
            os.makedirs(os.path.dirname(OUTPUT_JSON) or ".", exist_ok=True)
            debug_path = os.path.join(
                os.path.dirname(OUTPUT_JSON), "debug_api_response.json"
            )
            with open(debug_path, "w", encoding="utf-8") as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
            print(f"   🔍 Debug API sauvegardé : {debug_path}")
            debug_saved = True

        items = []
        data  = response.get("data", {})
        edges = data.get("reservations", {}).get("edges", [])
        if edges:
            items = [e.get("node", e) for e in edges]
        else:
            res_list = data.get("reservations", [])
            if isinstance(res_list, list) and res_list:
                items = res_list
            else:
                for key, val in data.items():
                    if isinstance(val, dict):
                        inner_edges = val.get("edges", [])
                        if inner_edges:
                            items = [e.get("node", e) for e in inner_edges]
                            break
                    elif isinstance(val, list) and val and isinstance(val[0], dict):
                        items = val
                        break

        if not items:
            print(f"   ⚠️  Aucun item trouvé — clés : {list(data.keys())[:10]}")
            break

        for node in items:
            all_reservations.append(_parse_reservation_node(node))

        print(f"   ↳ {len(all_reservations)} réservations récupérées...")
        offset += limit

        if len(items) < limit:
            break

        time.sleep(1)

    return all_reservations


def scrape_fallback(page):
    """Fallback : interception réseau + pagination UI."""
    print("🔄 Fallback : interception réseau + pagination...")

    all_reservations = []
    seen_ids         = set()
    page_responses   = []

    def handle_response(response):
        url = response.url
        if response.status != 200:
            return
        if "api/v2/reservations" in url:
            try:
                data = response.json()
                if isinstance(data, dict) and "reservations" in data:
                    page_responses.append({
                        "url":          url,
                        "reservations": data["reservations"],
                        "total_count":  data.get("metadata", {}).get("total_count", 0),
                    })
            except Exception:
                pass

    page.on("response", handle_response)

    pages_to_scan = [
        ("upcoming",  "https://www.airbnb.com/hosting/reservations/upcoming"),
        ("completed", "https://www.airbnb.com/hosting/reservations/completed"),
        ("all",       "https://www.airbnb.com/hosting/reservations/all"),
    ]

    for page_name, page_url in pages_to_scan:
        print(f"\n   📄 Page : {page_name}...")
        page_responses.clear()
        page.goto(page_url)
        page.wait_for_timeout(5000)

        for page_num in range(200):
            new_in_page = 0
            for resp in page_responses:
                for r in resp["reservations"]:
                    parsed = _parse_reservation_node(r)
                    if parsed["id"] and parsed["id"] not in seen_ids:
                        all_reservations.append(parsed)
                        seen_ids.add(parsed["id"])
                        new_in_page += 1
            total = page_responses[-1]["total_count"] if page_responses else 0
            print(f"      Page {page_num+1}: +{new_in_page} (total cat: {total}, cumul: {len(all_reservations)})")
            page_responses.clear()

            next_btn = None
            for selector in [
                'button:has-text("Suivant")', 'button:has-text("Next")',
                '[aria-label="Suivant"]',     '[aria-label="Next"]',
            ]:
                try:
                    btn = page.locator(selector)
                    if btn.count() > 0 and btn.first.is_visible() and btn.first.is_enabled():
                        next_btn = btn.first
                        break
                except Exception:
                    continue

            if not next_btn:
                break

            next_btn.click()
            page.wait_for_timeout(5000)

    page.remove_listener("response", handle_response)
    print(f"\n   ↳ {len(all_reservations)} réservations uniques (fallback)")
    return all_reservations


# ============================================================
# EXPORT LOCAL (CSV + JSON) — conservé de v1
# ============================================================

def export_csv(reservations, filename):
    if not reservations:
        print("⚠️  Aucune réservation à exporter.")
        return
    outdir = os.path.dirname(filename) or "."
    os.makedirs(outdir, exist_ok=True)
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=reservations[0].keys())
        writer.writeheader()
        writer.writerows(reservations)
    print(f"✅ CSV exporté : {filename} ({len(reservations)} réservations)")


def export_json(reservations, filename):
    outdir = os.path.dirname(filename) or "."
    os.makedirs(outdir, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(reservations, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON exporté : {filename}")


# ============================================================
# PUSH API NEXT.JS (NOUVEAU EN V2)
# ============================================================

def push_to_nextjs(reservations: list, ical_urls: dict, sync_type: str = "full"):
    """
    Envoie les données vers l'API Next.js :
    1. Réservations → table reservations
    2. Annonces + URLs iCal → table listings
    """
    if not USE_API:
        print("⚠️  API Next.js non configurée — skip push")
        return

    print("\n☁️  Envoi vers l'API Next.js...")

    # ── 1. Réservations ──────────────────────────────────────
    count = upsert_reservations(reservations, sync_type=sync_type)
    print(f"   ✅ {count} réservations envoyées à l'API Next.js")

    # ── 2. Annonces + URLs iCal ───────────────────────────────
    # Construire la liste des annonces uniques depuis les réservations
    listings_map = {}
    for r in reservations:
        lid  = r.get("listing_id", "")
        name = r.get("logement", "")
        if lid and lid not in listings_map:
            listings_map[lid] = {
                "listing_id": lid,
                "nom":        name,
                "ical_url":   ical_urls.get(lid, ""),
                "actif":      True,
            }

    if listings_map:
        upsert_listings(list(listings_map.values()))
        with_ical = sum(1 for l in listings_map.values() if l["ical_url"])
        print(f"   ✅ {len(listings_map)} annonces — {with_ical} avec URL iCal")


# ============================================================
# MAIN
# ============================================================

def main():
    start_time = time.time()

    print("=" * 55)
    print("   Airbnb Scraper — v2.0.0")
    print(f"   Démarré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"   Moteur     : {'CloakBrowser (stealth) ✅' if USE_CLOAKBROWSER else 'Playwright standard ⚠️'}")
    print(f"   Headless   : {'Oui' if HEADLESS else 'Non'}")
    print(f"   API Next.js: {'Activé ✅' if USE_API else 'Désactivé ⚠️'}")
    print("=" * 55)

    reservations = []
    ical_urls    = {}

    # ── Lancement du navigateur ───────────────────────────────
    if USE_CLOAKBROWSER:
        print("\n🕵️  Mode stealth activé\n")
        launch_args = {"headless": HEADLESS, "humanize": True}
        if PROXY_URL:
            launch_args["proxy"] = {"server": PROXY_URL}
            print(f"   🌐 Proxy configuré : {PROXY_URL.split('@')[-1] if '@' in PROXY_URL else PROXY_URL}")
        browser = cloak_launch(**launch_args)
    else:
        print("\n⚠️  Playwright standard\n")
        from playwright.sync_api import sync_playwright
        pw      = sync_playwright().start()
        launch_args = {
            "headless": HEADLESS,
            "args": ["--no-sandbox", "--disable-blink-features=AutomationControlled",
                     "--disable-dev-shm-usage"]
        }
        if PROXY_URL:
            launch_args["proxy"] = {"server": PROXY_URL}
            print(f"   🌐 Proxy configuré : {PROXY_URL.split('@')[-1] if '@' in PROXY_URL else PROXY_URL}")
        browser = pw.chromium.launch(**launch_args)

    # Charger la session si elle existe
    context_args = {
        "viewport": {"width": 1280, "height": 800},
        "locale": "fr-FR",
    }
    if os.path.exists(SESSION_FILE):
        try:
            context_args["storage_state"] = SESSION_FILE
            print(f"   💾 Session chargée : {SESSION_FILE}")
        except Exception as e:
            print(f"   ⚠️  Impossible de charger la session : {e}")

    context = browser.new_context(**context_args)
    page = context.new_page()

    try:
        # ── Étape 1 : Vérifier si déjà connecté ──────────────
        if os.path.exists(SESSION_FILE):
            print("\n🔍 Vérification de la session existante...")
            if is_logged_in(page):
                print("✅ Session valide — connexion non nécessaire")
            else:
                print("⚠️  Session expirée — nouvelle connexion requise")
                login(page)
        else:
            # ── Étape 1 : Connexion ───────────────────────────────
            login(page)

        # ── Étape 2 : Réservations (API GraphQL) ─────────────
        gql_reservations = get_reservations(page)

        # ── Étape 3 : Fallback réseau ─────────────────────────
        net_reservations = scrape_fallback(page)

        # ── Étape 4 : Fusion ──────────────────────────────────
        seen_ids = set()
        for r in gql_reservations:
            if r["id"]:
                reservations.append(r)
                seen_ids.add(r["id"])

        for r in net_reservations:
            if r["id"] and r["id"] not in seen_ids:
                reservations.append(r)
                seen_ids.add(r["id"])
            elif r["id"]:
                existing = next((x for x in reservations if x["id"] == r["id"]), None)
                if existing:
                    for key in ["statut", "voyageur", "nb_voyageurs", "logement",
                                "montant_total", "devise", "date_creation"]:
                        if not existing[key] and r[key]:
                            existing[key] = r[key]

        print(f"\n📊 Fusion : {len(gql_reservations)} GraphQL + "
              f"{len(net_reservations)} réseau → {len(reservations)} uniques")

        # ── Étape 5 : Collecte URLs iCal (NOUVEAU v2) ─────────
        listing_ids = list({r["listing_id"] for r in reservations if r["listing_id"]})
        if listing_ids:
            ical_urls = collect_ical_urls(page, listing_ids)
        else:
            print("⚠️  Aucun listing_id trouvé — iCal non collecté")

    finally:
        browser.close()

    # ── Étape 6 : Export local CSV + JSON (conservé v1) ───────
    print(f"\n💾 Export local...")
    export_csv(reservations,  OUTPUT_CSV)
    export_json(reservations, OUTPUT_JSON)

    # ── Étape 7 : Push API Next.js (NOUVEAU v2) ───────────────
    push_to_nextjs(reservations, ical_urls, sync_type='full')

    # ── Étape 8 : Log de sync ─────────────────────────────────
    duration = time.time() - start_time
    if USE_API:
        try:
            log_sync(
                sync_type="full",
                status="success",
                listings_count=len({r["listing_id"] for r in reservations}),
                reservations_count=len(reservations),
                duration=duration,
            )
        except Exception as e:
            print(f"   ⚠️  Erreur log sync : {e}")

    print(f"\n🎉 Terminé en {duration:.0f}s !")
    print(f"   → {OUTPUT_CSV}")
    print(f"   → {OUTPUT_JSON}")
    if USE_API:
        print(f"   → API Next.js mise à jour")


if __name__ == "__main__":
    main()
