"""
test_cloakbrowser.py - Test de CloakBrowser
============================================
Vérifie que CloakBrowser fonctionne correctement
"""

import sys

print("=" * 70)
print("   Test de CloakBrowser")
print("=" * 70)
print()

# Test 1: Import
print("1. Test d'import...")
try:
    from cloakbrowser import launch as cloak_launch
    print("   ✅ CloakBrowser importé avec succès")
except ImportError as e:
    print(f"   ❌ CloakBrowser non installé: {e}")
    print()
    print("   Solution:")
    print("   pip install cloakbrowser")
    sys.exit(1)

print()

# Test 2: Lancement
print("2. Test de lancement...")
try:
    browser = cloak_launch(headless=True, humanize=True)
    print("   ✅ Navigateur lancé en mode stealth")
    
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        locale="fr-FR",
    )
    page = context.new_page()
    
    print("   ✅ Page créée")
    
    # Test 3: Navigation
    print()
    print("3. Test de navigation...")
    page.goto("https://www.airbnb.com")
    page.wait_for_timeout(3000)
    
    title = page.title()
    print(f"   ✅ Navigation réussie: {title[:50]}...")
    
    browser.close()
    print()
    print("=" * 70)
    print("✅ CloakBrowser fonctionne parfaitement!")
    print("=" * 70)
    print()
    print("Le scraper Airbnb peut maintenant utiliser le mode stealth.")
    print()
    
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    print()
    print("   Vérifications:")
    print("   1. Docker est-il démarré? (docker ps)")
    print("   2. CloakBrowser est-il installé? (pip install cloakbrowser)")
    print("   3. Avez-vous les droits Docker?")
    sys.exit(1)
