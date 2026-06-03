"""
currency_converter.py - Conversion des devises vers DZD
========================================================
Ce module récupère les taux de conversion depuis Supabase
et enrichit les réservations avec le currency_ratio.

Dépendances :
    pip install requests python-dotenv

Usage :
    from currency_converter import enrich_with_currency_ratio
    
    reservations = [...]  # Liste des réservations scrapées
    enriched = enrich_with_currency_ratio(reservations)
"""

import os
import requests
from typing import List, Dict, Any
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(encoding='utf-8')
except ImportError:
    pass


# ============================================================================
# CONFIGURATION
# ============================================================================

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# Cache des taux de conversion (pour éviter de requêter à chaque fois)
_currency_cache = {}
_cache_timestamp = None
CACHE_DURATION = 3600  # 1 heure


# ============================================================================
# FONCTIONS PRINCIPALES
# ============================================================================

def get_currency_rates() -> Dict[str, float]:
    """
    Récupère les taux de conversion depuis la table currencies.
    
    Returns:
        Dict avec {code_devise: ratio}
        Exemple: {"GBP": 270, "EUR": 250, "USD": 250, "DZD": 1}
    """
    global _currency_cache, _cache_timestamp
    
    # Vérifier le cache
    if _currency_cache and _cache_timestamp:
        elapsed = (datetime.now() - _cache_timestamp).total_seconds()
        if elapsed < CACHE_DURATION:
            return _currency_cache
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/currencies"
        params = {"select": "code,ratio"}
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        
        currencies = response.json()
        
        # Construire le dictionnaire {code: ratio}
        rates = {}
        for currency in currencies:
            code = currency.get("code", "").upper()
            ratio = float(currency.get("ratio", 1.0))
            rates[code] = ratio
        
        # Mettre à jour le cache
        _currency_cache = rates
        _cache_timestamp = datetime.now()
        
        print(f"   ✅ {len(rates)} taux de conversion chargés depuis Supabase")
        return rates
        
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  Erreur lors de la récupération des taux: {e}")
        print(f"   ℹ️  Utilisation des taux par défaut")
        return get_default_rates()
    except Exception as e:
        print(f"   ⚠️  Erreur inattendue: {e}")
        return get_default_rates()


def get_default_rates() -> Dict[str, float]:
    """
    Retourne les taux de conversion par défaut (fallback).
    
    Returns:
        Dict avec les taux par défaut
    """
    return {
        "DZD": 1.0,
        "GBP": 270.0,
        "EUR": 250.0,
        "USD": 250.0,
        "CAD": 162.0,
    }


def enrich_with_currency_ratio(reservations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrichit les réservations avec le currency_ratio depuis la table currencies.
    
    Args:
        reservations: Liste des réservations avec 'devise' et 'montant_total'
        
    Returns:
        Liste des réservations enrichies avec 'currency_code' et 'currency_ratio'
        
    Exemple:
        Avant:
        {
            "montant_total": 653.0,
            "devise": "GBP"
        }
        
        Après:
        {
            "montant_total": 653.0,
            "devise": "GBP",
            "currency_code": "GBP",
            "currency_ratio": 270.0
        }
        
        Montant en DZD = 653.0 × 270.0 = 176,310 DZD
    """
    if not reservations:
        return reservations
    
    print(f"\n💱 Enrichissement avec les taux de conversion...")
    
    # Récupérer les taux de conversion
    rates = get_currency_rates()
    
    # Statistiques
    enriched_count = 0
    missing_rates = set()
    
    for reservation in reservations:
        devise = reservation.get("devise", "DZD").upper()
        
        # Récupérer le taux de conversion
        ratio = rates.get(devise)
        
        if ratio is None:
            # Devise inconnue, utiliser 1.0 par défaut
            ratio = 1.0
            missing_rates.add(devise)
        
        # Ajouter les champs pour Supabase
        reservation["currency_code"] = devise
        reservation["currency_ratio"] = ratio
        
        enriched_count += 1
    
    print(f"   ✅ {enriched_count} réservations enrichies avec currency_ratio")
    
    if missing_rates:
        print(f"   ⚠️  Devises inconnues (ratio=1.0 utilisé) : {', '.join(missing_rates)}")
    
    # Afficher un exemple
    if reservations:
        example = reservations[0]
        montant = example.get("montant_total", 0)
        devise = example.get("currency_code", "DZD")
        ratio = example.get("currency_ratio", 1.0)
        montant_dzd = montant * ratio
        
        print(f"\n   📊 Exemple de conversion :")
        print(f"      Montant original : {montant} {devise}")
        print(f"      Taux de conversion : {ratio}")
        print(f"      Montant en DZD : {montant_dzd:,.2f} DZD")
    
    return reservations


def calculate_amount_in_dzd(amount: float, currency_code: str, rates: Dict[str, float] = None) -> float:
    """
    Calcule le montant en DZD.
    
    Args:
        amount: Montant dans la devise d'origine
        currency_code: Code de la devise (GBP, EUR, etc.)
        rates: Dictionnaire des taux (optionnel, sera récupéré si None)
        
    Returns:
        Montant converti en DZD
        
    Exemple:
        >>> calculate_amount_in_dzd(100, "GBP")
        27000.0  # 100 GBP × 270 = 27,000 DZD
    """
    if rates is None:
        rates = get_currency_rates()
    
    currency_code = currency_code.upper()
    ratio = rates.get(currency_code, 1.0)
    
    return amount * ratio


# ============================================================================
# FONCTIONS DE TEST
# ============================================================================

def test_currency_conversion():
    """Test de la conversion des devises."""
    print("="*70)
    print("🧪 TEST DE CONVERSION DES DEVISES")
    print("="*70)
    
    # Récupérer les taux
    rates = get_currency_rates()
    
    print(f"\n📊 Taux de conversion disponibles :")
    for code, ratio in sorted(rates.items()):
        print(f"   • {code} : {ratio}")
    
    # Test avec des exemples
    print(f"\n💰 Exemples de conversion :")
    
    examples = [
        {"amount": 100, "currency": "GBP"},
        {"amount": 100, "currency": "EUR"},
        {"amount": 100, "currency": "USD"},
        {"amount": 100, "currency": "DZD"},
    ]
    
    for example in examples:
        amount = example["amount"]
        currency = example["currency"]
        amount_dzd = calculate_amount_in_dzd(amount, currency, rates)
        print(f"   • {amount} {currency} = {amount_dzd:,.2f} DZD")
    
    # Test avec des réservations
    print(f"\n📋 Test avec des réservations :")
    
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
        {
            "id": "TEST003",
            "montant_total": 5000.0,
            "devise": "DZD",
            "voyageur": "Test User 3"
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
    
    print(f"\n{'='*70}")
    print(f"✅ TEST TERMINÉ")
    print(f"{'='*70}\n")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    test_currency_conversion()
