"""
CORRIGER_RATIOS_INCORRECTS.py - Corriger les réservations avec ratio=1.0
==========================================================================
Ce script identifie les réservations avec currency_ratio=1.0 pour GBP/EUR/USD/CAD
et les re-scrape pour obtenir le bon ratio.

Usage:
    python CORRIGER_RATIOS_INCORRECTS.py
"""

import os
import sys
import requests
from datetime import datetime
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


def get_reservations_with_incorrect_ratios():
    """Récupère les réservations avec currency_ratio=1.0 pour devises étrangères."""
    print("\n" + "="*70)
    print("🔍 IDENTIFICATION DES RÉSERVATIONS AVEC RATIOS INCORRECTS")
    print("="*70)
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/reservations"
        
        # Chercher les réservations avec ratio=1.0 pour GBP, EUR, USD, CAD
        params = {
            "select": "id,airbnb_confirmation_code,guest_name,total_amount,currency_code,currency_ratio,check_in_date",
            "currency_ratio": "eq.1.0",
            "currency_code": "in.(GBP,EUR,USD,CAD)",
            "order": "check_in_date.desc",
            "limit": 10000  # Augmenté pour corriger toutes les réservations
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        
        reservations = response.json()
        
        if not reservations:
            print("\n✅ Aucune réservation avec ratio incorrect trouvée!")
            return []
        
        print(f"\n⚠️  {len(reservations)} réservations avec ratio=1.0 trouvées:")
        print(f"\n{'Code':<15} {'Voyageur':<20} {'Montant':<12} {'Devise':<6} {'Ratio':<8} {'Arrivée':<12}")
        print("-" * 90)
        
        # Grouper par devise
        by_currency = {}
        for res in reservations[:20]:  # Afficher max 20
            code = res.get("airbnb_confirmation_code", "N/A")[:14]
            guest = res.get("guest_name", "N/A")[:19]
            amount = res.get("total_amount", 0)
            currency = res.get("currency_code", "N/A")
            ratio = res.get("currency_ratio", 1.0)
            checkin = res.get("check_in_date", "N/A")[:10]
            
            print(f"{code:<15} {guest:<20} {amount:<12.2f} {currency:<6} {ratio:<8.1f} {checkin:<12}")
            
            if currency not in by_currency:
                by_currency[currency] = 0
            by_currency[currency] += 1
        
        if len(reservations) > 20:
            print(f"... et {len(reservations) - 20} autres")
        
        print(f"\n📊 Répartition par devise:")
        for currency, count in sorted(by_currency.items()):
            print(f"   • {currency}: {count} réservations")
        
        return reservations
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la récupération: {e}")
        return []


def get_correct_ratios():
    """Récupère les taux de conversion corrects depuis la table currencies."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/currencies"
        params = {"select": "code,ratio"}
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        
        currencies = response.json()
        
        rates = {}
        for currency in currencies:
            code = currency.get("code", "").upper()
            ratio = float(currency.get("ratio", 1.0))
            rates[code] = ratio
        
        return rates
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la récupération des taux: {e}")
        return {
            "DZD": 1.0,
            "GBP": 270.0,
            "EUR": 250.0,
            "USD": 250.0,
            "CAD": 162.0,
        }


def update_currency_ratios(reservations, correct_rates):
    """Met à jour les currency_ratio dans Supabase."""
    print(f"\n{'='*70}")
    print("🔧 CORRECTION DES RATIOS DANS SUPABASE")
    print("="*70)
    
    if not reservations:
        print("\n✅ Rien à corriger!")
        return
    
    print(f"\n📊 Taux de conversion corrects:")
    for code, ratio in sorted(correct_rates.items()):
        print(f"   • {code}: {ratio}")
    
    print(f"\n🔄 Mise à jour de {len(reservations)} réservations...")
    
    updated = 0
    errors = 0
    
    for i, res in enumerate(reservations, 1):
        try:
            res_id = res.get("id")
            currency = res.get("currency_code", "DZD").upper()
            correct_ratio = correct_rates.get(currency, 1.0)
            
            # Mettre à jour via l'API Supabase
            url = f"{SUPABASE_URL}/rest/v1/reservations"
            params = {"id": f"eq.{res_id}"}
            payload = {
                "currency_ratio": correct_ratio,
                "updated_at": datetime.now().isoformat() if hasattr(datetime, 'now') else datetime.utcnow().isoformat()
            }
            
            response = requests.patch(url, headers=HEADERS, params=params, json=payload, timeout=10)
            response.raise_for_status()
            
            updated += 1
            
            if i % 50 == 0 or i == len(reservations):
                print(f"   ✅ {i}/{len(reservations)} mises à jour...")
            
        except Exception as e:
            errors += 1
            if errors <= 5:  # Afficher max 5 erreurs
                print(f"   ⚠️  Erreur pour {res.get('airbnb_confirmation_code', 'N/A')}: {e}")
    
    print(f"\n{'='*70}")
    print(f"✅ CORRECTION TERMINÉE")
    print(f"{'='*70}")
    print(f"   • Mises à jour: {updated}")
    print(f"   • Erreurs: {errors}")
    print(f"{'='*70}\n")


def verify_corrections():
    """Vérifie que les corrections ont été appliquées."""
    print(f"\n{'='*70}")
    print("✅ VÉRIFICATION DES CORRECTIONS")
    print("="*70)
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/reservations"
        params = {
            "select": "currency_code,currency_ratio",
            "currency_ratio": "eq.1.0",
            "currency_code": "in.(GBP,EUR,USD,CAD)",
            "limit": 10
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        
        remaining = response.json()
        
        if not remaining:
            print("\n✅ Toutes les réservations ont été corrigées!")
            print("   Aucune réservation avec ratio=1.0 pour GBP/EUR/USD/CAD")
        else:
            print(f"\n⚠️  {len(remaining)} réservations avec ratio=1.0 restantes")
            print("   Relancez le script pour les corriger")
        
    except Exception as e:
        print(f"\n⚠️  Impossible de vérifier: {e}")


def main():
    """Fonction principale."""
    
    # Vérifier la configuration
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\n❌ Configuration Supabase manquante dans .env")
        print("   Vérifiez NEXT_PUBLIC_SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY")
        return
    
    print("\n" + "="*70)
    print("🔧 CORRECTION DES RATIOS DE CONVERSION")
    print("="*70)
    print("\nCe script va:")
    print("1. Identifier les réservations avec currency_ratio=1.0 (incorrect)")
    print("2. Récupérer les taux corrects depuis la table currencies")
    print("3. Mettre à jour les ratios dans Supabase")
    print("\n⚠️  Cette opération modifie directement la base de données!")
    
    # Demander confirmation
    print("\n" + "="*70)
    response = input("Voulez-vous continuer? (oui/non): ").strip().lower()
    
    if response not in ["oui", "o", "yes", "y"]:
        print("\n❌ Opération annulée")
        return
    
    # Étape 1: Identifier les réservations incorrectes
    reservations = get_reservations_with_incorrect_ratios()
    
    if not reservations:
        print("\n✅ Aucune correction nécessaire!")
        return
    
    # Étape 2: Récupérer les taux corrects
    correct_rates = get_correct_ratios()
    
    # Étape 3: Mettre à jour
    update_currency_ratios(reservations, correct_rates)
    
    # Étape 4: Vérifier
    verify_corrections()
    
    print("\n✅ Script terminé!\n")


if __name__ == "__main__":
    main()
