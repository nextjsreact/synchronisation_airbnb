"""
TEST_SYSTEME_COMPLET.py - Test du système complet V2.1.1
=========================================================
Ce script teste :
1. La conversion des devises
2. La collecte des coordonnées (1 réservation)
3. L'envoi à l'API Next.js

Usage :
    python TEST_SYSTEME_COMPLET.py
"""

import os
import sys
import json
from datetime import datetime

# Forcer UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(encoding='utf-8')

# Imports
from currency_converter import enrich_with_currency_ratio, get_currency_rates
from airbnb_api_client import check_api_health, send_to_nextjs_api


def print_section(title):
    """Affiche une section."""
    print(f"\n{'='*70}")
    print(f"   {title}")
    print(f"{'='*70}\n")


def test_currency_conversion():
    """Test 1 : Conversion des devises."""
    print_section("TEST 1 : CONVERSION DES DEVISES")
    
    # Récupérer les taux
    print("📊 Récupération des taux depuis Supabase...")
    rates = get_currency_rates()
    
    if not rates:
        print("❌ Échec : Impossible de récupérer les taux")
        return False
    
    print(f"✅ {len(rates)} taux récupérés :")
    for code, ratio in sorted(rates.items()):
        print(f"   • {code} : {ratio}")
    
    # Test avec des réservations fictives
    print(f"\n📋 Test avec des réservations fictives...")
    
    test_reservations = [
        {
            "id": "TEST001",
            "montant_total": 653.0,
            "devise": "GBP",
            "voyageur": "Test User 1"
        },
        {
            "id": "TEST002",
            "montant_total": 150.0,
            "devise": "EUR",
            "voyageur": "Test User 2"
        },
    ]
    
    enriched = enrich_with_currency_ratio(test_reservations)
    
    print(f"\n✅ Réservations enrichies :")
    for res in enriched:
        montant = res.get("montant_total", 0)
        devise = res.get("currency_code", "DZD")
        ratio = res.get("currency_ratio", 1.0)
        montant_dzd = montant * ratio
        print(f"   • {res['id']} : {montant} {devise} × {ratio} = {montant_dzd:,.2f} DZD")
    
    return True


def test_api_health():
    """Test 2 : Santé de l'API Next.js."""
    print_section("TEST 2 : SANTÉ DE L'API NEXT.JS")
    
    print("🔍 Vérification de l'API Next.js...")
    health = check_api_health()
    
    if health["ok"]:
        print(f"✅ API accessible")
        print(f"   URL : {health['url']}")
        print(f"   Latence : {health['latency_ms']}ms")
        print(f"   Status : {health.get('status', 'N/A')}")
        return True
    else:
        print(f"❌ API inaccessible")
        print(f"   URL : {health['url']}")
        print(f"   Erreur : {health['error']}")
        return False


def test_api_send():
    """Test 3 : Envoi de données à l'API."""
    print_section("TEST 3 : ENVOI DE DONNÉES À L'API")
    
    # Créer une réservation de test avec tous les champs
    test_reservation = {
        "id": f"PYTEST_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "listing_id": "1361868072916616334",
        "statut": "Confirmée",
        "voyageur": "Test User",
        "telephone_voyageur": "+213 555 000 000",  # ✅ NOUVEAU V2.1
        "email_voyageur": "test@example.com",      # ✅ NOUVEAU V2.1
        "nb_voyageurs": 2,
        "logement": "Test Loft",
        "date_arrivee": "2026-12-10",
        "date_depart": "2026-12-15",
        "nb_nuits": 5,
        "montant_total": 100.0,
        "devise": "GBP",
        "currency_code": "GBP",                    # ✅ NOUVEAU V2.1.1
        "currency_ratio": 270.0,                   # ✅ NOUVEAU V2.1.1
        "date_creation": "2026-05-31"
    }
    
    print("📤 Envoi d'une réservation de test...")
    print(f"\n📋 Données envoyées :")
    print(json.dumps(test_reservation, indent=2, ensure_ascii=False))
    
    try:
        result = send_to_nextjs_api([test_reservation], sync_type="manual")
        
        if result.get("success"):
            print(f"\n✅ Envoi réussi !")
            metrics = result.get("metrics", {})
            print(f"   • Traitées : {metrics.get('processed', 0)}")
            print(f"   • Créées : {metrics.get('created', 0)}")
            print(f"   • Mises à jour : {metrics.get('updated', 0)}")
            
            errors = result.get("errors", [])
            if errors:
                print(f"\n⚠️  Erreurs ({len(errors)}) :")
                for err in errors[:3]:
                    print(f"   • {err}")
            
            return True
        else:
            print(f"\n❌ Échec de l'envoi")
            print(f"   Erreur : {result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception lors de l'envoi : {e}")
        return False


def test_real_data():
    """Test 4 : Test avec des données réelles (optionnel)."""
    print_section("TEST 4 : TEST AVEC DONNÉES RÉELLES (OPTIONNEL)")
    
    # Charger les réservations existantes
    csv_file = "output/reservations_airbnb.csv"
    
    if not os.path.exists(csv_file):
        print(f"⚠️  Fichier {csv_file} introuvable")
        print(f"   Lancez d'abord un scraping complet")
        return None
    
    print(f"📂 Chargement des réservations depuis {csv_file}...")
    
    import csv
    reservations = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            reservations.append(row)
    
    print(f"✅ {len(reservations)} réservations chargées")
    
    # Prendre les 3 premières
    sample = reservations[:3]
    
    print(f"\n📊 Échantillon de 3 réservations :")
    for res in sample:
        print(f"   • {res.get('id')} : {res.get('montant_total')} {res.get('devise')} - {res.get('voyageur')}")
    
    # Enrichir avec les taux
    print(f"\n💱 Enrichissement avec les taux de conversion...")
    enriched = enrich_with_currency_ratio(sample)
    
    print(f"\n✅ Réservations enrichies :")
    for res in enriched:
        montant = float(res.get("montant_total", 0))
        devise = res.get("currency_code", "DZD")
        ratio = float(res.get("currency_ratio", 1.0))
        montant_dzd = montant * ratio
        print(f"   • {res['id']} : {montant} {devise} × {ratio} = {montant_dzd:,.2f} DZD")
    
    return True


def main():
    print("="*70)
    print("   🧪 TEST DU SYSTÈME COMPLET V2.1.1")
    print("="*70)
    print(f"\n   Date : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"   Tests : Conversion devises + API Next.js")
    
    results = {}
    
    # Test 1 : Conversion des devises
    try:
        results["currency"] = test_currency_conversion()
    except Exception as e:
        print(f"\n❌ Erreur Test 1 : {e}")
        results["currency"] = False
    
    # Test 2 : Santé de l'API
    try:
        results["api_health"] = test_api_health()
    except Exception as e:
        print(f"\n❌ Erreur Test 2 : {e}")
        results["api_health"] = False
    
    # Test 3 : Envoi à l'API (seulement si l'API est accessible)
    if results["api_health"]:
        try:
            results["api_send"] = test_api_send()
        except Exception as e:
            print(f"\n❌ Erreur Test 3 : {e}")
            results["api_send"] = False
    else:
        print_section("TEST 3 : ENVOI À L'API (SKIP)")
        print("⚠️  API inaccessible, test ignoré")
        results["api_send"] = None
    
    # Test 4 : Données réelles (optionnel)
    try:
        results["real_data"] = test_real_data()
    except Exception as e:
        print(f"\n❌ Erreur Test 4 : {e}")
        results["real_data"] = None
    
    # Résumé
    print_section("RÉSUMÉ DES TESTS")
    
    print("📊 Résultats :")
    print(f"   • Test 1 (Conversion devises) : {'✅ PASS' if results['currency'] else '❌ FAIL'}")
    print(f"   • Test 2 (Santé API) : {'✅ PASS' if results['api_health'] else '❌ FAIL'}")
    
    if results['api_send'] is not None:
        print(f"   • Test 3 (Envoi API) : {'✅ PASS' if results['api_send'] else '❌ FAIL'}")
    else:
        print(f"   • Test 3 (Envoi API) : ⚠️  SKIP")
    
    if results['real_data'] is not None:
        print(f"   • Test 4 (Données réelles) : {'✅ PASS' if results['real_data'] else '❌ FAIL'}")
    else:
        print(f"   • Test 4 (Données réelles) : ⚠️  SKIP")
    
    # Conclusion
    print(f"\n{'='*70}")
    
    all_pass = all(v for v in results.values() if v is not None)
    
    if all_pass:
        print("✅ TOUS LES TESTS SONT PASSÉS")
        print(f"{'='*70}")
        print("\n🎉 Le système est prêt à être utilisé !")
        print("\n📋 Prochaines étapes :")
        print("   1. Lancer un scraping complet : SCRAPING_COMPLET_MAINTENANT.bat")
        print("   2. Vérifier les données dans Supabase")
        print("   3. Vérifier l'affichage côté frontend")
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print(f"{'='*70}")
        print("\n📋 Actions recommandées :")
        
        if not results["currency"]:
            print("   • Vérifier la connexion à Supabase")
            print("   • Vérifier la table currencies")
        
        if not results["api_health"]:
            print("   • Vérifier que l'API Next.js est lancée")
            print("   • Vérifier l'URL dans .env (NEXTJS_API_URL)")
        
        if results["api_send"] is False:
            print("   • Vérifier les logs de l'API Next.js")
            print("   • Vérifier que l'API accepte les nouveaux champs")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
