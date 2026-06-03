"""
VERIFIER_DONNEES_SUPABASE.py - Vérifier les données dans Supabase
===================================================================
Ce script vérifie si les réservations ont été insérées dans Supabase
après le scraping complet.

Usage:
    python VERIFIER_DONNEES_SUPABASE.py
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

# Configuration
SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def check_reservations_count():
    """Compte le nombre total de réservations dans Supabase."""
    print("\n" + "="*70)
    print("📊 VÉRIFICATION DES DONNÉES SUPABASE")
    print("="*70)
    
    try:
        # Compter toutes les réservations
        url = f"{SUPABASE_URL}/rest/v1/reservations"
        params = {"select": "count", "count": "exact"}
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        
        # Le count est dans le header Content-Range
        content_range = response.headers.get("Content-Range", "")
        if content_range:
            # Format: "0-9/100" ou "*/100"
            total = content_range.split("/")[-1]
            print(f"\n✅ Total des réservations dans Supabase: {total}")
            return int(total)
        else:
            print(f"\n⚠️  Impossible de récupérer le count (Content-Range manquant)")
            return 0
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la vérification: {e}")
        return 0


def check_recent_reservations():
    """Affiche les 10 dernières réservations synchronisées."""
    print(f"\n{'='*70}")
    print("📅 DERNIÈRES RÉSERVATIONS SYNCHRONISÉES")
    print("="*70)
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/reservations"
        params = {
            "select": "airbnb_confirmation_code,guest_name,check_in_date,total_amount,currency_code,currency_ratio,synced_at",
            "order": "synced_at.desc.nullslast",
            "limit": 10
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        
        reservations = response.json()
        
        if not reservations:
            print("\n⚠️  Aucune réservation trouvée")
            return
        
        print(f"\n✅ {len(reservations)} dernières réservations:")
        print(f"\n{'Code':<15} {'Voyageur':<20} {'Arrivée':<12} {'Montant':<12} {'Devise':<6} {'Ratio':<8} {'Synced At':<20}")
        print("-" * 110)
        
        for res in reservations:
            code = res.get("airbnb_confirmation_code", "N/A")[:14]
            guest = res.get("guest_name", "N/A")[:19]
            checkin = res.get("check_in_date", "N/A")[:10]
            amount = res.get("total_amount", 0)
            currency = res.get("currency_code", "N/A")
            ratio = res.get("currency_ratio", 1.0)
            synced = res.get("synced_at", "N/A")
            
            if synced != "N/A":
                try:
                    synced_dt = datetime.fromisoformat(synced.replace("Z", "+00:00"))
                    synced = synced_dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass
            
            print(f"{code:<15} {guest:<20} {checkin:<12} {amount:<12.2f} {currency:<6} {ratio:<8.1f} {synced:<20}")
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la récupération: {e}")


def check_currency_ratios():
    """Vérifie les taux de conversion dans les réservations."""
    print(f"\n{'='*70}")
    print("💱 VÉRIFICATION DES TAUX DE CONVERSION")
    print("="*70)
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/reservations"
        params = {
            "select": "currency_code,currency_ratio",
            "limit": 1000
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        
        reservations = response.json()
        
        if not reservations:
            print("\n⚠️  Aucune réservation trouvée")
            return
        
        # Compter les ratios par devise
        ratios_by_currency = {}
        for res in reservations:
            currency = res.get("currency_code", "N/A")
            ratio = res.get("currency_ratio", 1.0)
            
            if currency not in ratios_by_currency:
                ratios_by_currency[currency] = {}
            
            if ratio not in ratios_by_currency[currency]:
                ratios_by_currency[currency][ratio] = 0
            
            ratios_by_currency[currency][ratio] += 1
        
        print(f"\n📊 Répartition des taux de conversion:")
        for currency, ratios in sorted(ratios_by_currency.items()):
            print(f"\n   {currency}:")
            for ratio, count in sorted(ratios.items()):
                status = "✅" if ratio > 1.0 else "⚠️"
                print(f"      {status} Ratio {ratio}: {count} réservations")
        
        # Vérifier si des ratios sont incorrects (1.0 pour GBP, EUR, USD)
        incorrect_ratios = []
        for currency in ["GBP", "EUR", "USD", "CAD"]:
            if currency in ratios_by_currency:
                if 1.0 in ratios_by_currency[currency]:
                    count = ratios_by_currency[currency][1.0]
                    incorrect_ratios.append(f"{currency}: {count} réservations avec ratio=1.0")
        
        if incorrect_ratios:
            print(f"\n⚠️  PROBLÈME DÉTECTÉ - Ratios incorrects:")
            for issue in incorrect_ratios:
                print(f"   • {issue}")
            print(f"\n   💡 Solution: Fixer le Dockerfile et relancer le scraping")
        else:
            print(f"\n✅ Tous les taux de conversion sont corrects!")
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la vérification: {e}")


def check_contact_info():
    """Vérifie si les contacts ont été collectés."""
    print(f"\n{'='*70}")
    print("📞 VÉRIFICATION DES CONTACTS")
    print("="*70)
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/reservations"
        params = {
            "select": "guest_phone,guest_email",
            "limit": 1000
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        
        reservations = response.json()
        
        if not reservations:
            print("\n⚠️  Aucune réservation trouvée")
            return
        
        total = len(reservations)
        with_phone = sum(1 for r in reservations if r.get("guest_phone"))
        with_email = sum(1 for r in reservations if r.get("guest_email"))
        
        print(f"\n📊 Statistiques des contacts:")
        print(f"   • Total réservations: {total}")
        print(f"   • Avec téléphone: {with_phone} ({with_phone/total*100:.1f}%)")
        print(f"   • Avec email: {with_email} ({with_email/total*100:.1f}%)")
        
        if with_phone == 0 and with_email == 0:
            print(f"\n⚠️  PROBLÈME DÉTECTÉ - Aucun contact collecté")
            print(f"   💡 Solution: Activer COLLECT_CONTACTS=true dans .env")
        elif with_phone < total * 0.5:
            print(f"\n⚠️  Peu de contacts collectés (< 50%)")
            print(f"   💡 Vérifier que COLLECT_CONTACTS=true dans .env")
        else:
            print(f"\n✅ Contacts collectés avec succès!")
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la vérification: {e}")


def check_recent_syncs():
    """Vérifie les synchronisations récentes (dernières 24h)."""
    print(f"\n{'='*70}")
    print("🔄 SYNCHRONISATIONS RÉCENTES (24h)")
    print("="*70)
    
    try:
        # Calculer la date d'il y a 24h
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        
        url = f"{SUPABASE_URL}/rest/v1/reservations"
        params = {
            "select": "count",
            "synced_at": f"gte.{yesterday}",
            "count": "exact"
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        
        content_range = response.headers.get("Content-Range", "")
        if content_range:
            count = content_range.split("/")[-1]
            print(f"\n✅ Réservations synchronisées dans les dernières 24h: {count}")
            
            if int(count) == 0:
                print(f"\n⚠️  Aucune synchronisation récente détectée")
                print(f"   💡 Le scraping complet n'a peut-être pas inséré de données")
            elif int(count) < 1000:
                print(f"\n⚠️  Peu de synchronisations récentes (< 1000)")
                print(f"   💡 Vérifier les logs de l'API Next.js")
            else:
                print(f"\n✅ Synchronisation récente réussie!")
        else:
            print(f"\n⚠️  Impossible de récupérer le count")
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la vérification: {e}")


def main():
    """Fonction principale."""
    
    # Vérifier la configuration
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\n❌ Configuration Supabase manquante dans .env")
        print("   Vérifiez NEXT_PUBLIC_SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY")
        return
    
    # Exécuter toutes les vérifications
    total = check_reservations_count()
    check_recent_syncs()
    check_recent_reservations()
    check_currency_ratios()
    check_contact_info()
    
    # Résumé final
    print(f"\n{'='*70}")
    print("📋 RÉSUMÉ")
    print("="*70)
    
    if total == 0:
        print(f"\n❌ PROBLÈME CRITIQUE: Aucune réservation dans Supabase")
        print(f"\n   Causes possibles:")
        print(f"   1. L'API Next.js ne reçoit pas les données")
        print(f"   2. La validation Zod échoue silencieusement")
        print(f"   3. Les contraintes UNIQUE rejettent les doublons")
        print(f"\n   Actions recommandées:")
        print(f"   1. Vérifier les logs de l'API Next.js")
        print(f"   2. Tester avec une seule réservation (TEST_RAPIDE_UNE_RESERVATION.py)")
        print(f"   3. Vérifier la structure de la table reservations")
    elif total < 1000:
        print(f"\n⚠️  Peu de réservations dans Supabase ({total})")
        print(f"   Attendu: ~6,000 réservations après le scraping complet")
    else:
        print(f"\n✅ Base de données Supabase opérationnelle ({total} réservations)")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
