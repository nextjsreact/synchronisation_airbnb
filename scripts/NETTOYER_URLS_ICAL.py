"""
NETTOYER_URLS_ICAL.py - Nettoyer les URLs iCal invalides
=========================================================
Ce script identifie et nettoie les URLs iCal invalides dans Supabase:
- URLs sans token (?t=, ?s=, calendarAccessSignature)
- URLs de test (test.ics)
- URLs qui retournent HTTP 400/404

Usage:
    python NETTOYER_URLS_ICAL.py
"""

import os
import requests
from typing import List, Dict, Any
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


def get_all_ical_urls():
    """Récupère toutes les URLs iCal depuis property_sync_config."""
    print("\n" + "="*70)
    print("🔍 RÉCUPÉRATION DES URLs iCAL")
    print("="*70)
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/property_sync_config"
        
        # Requête simple sans filtres complexes
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        all_configs = response.json()
        
        # Filtrer en Python ceux qui ont une ical_url_airbnb
        configs = [c for c in all_configs if c.get("ical_url_airbnb")]
        
        print(f"\n✅ {len(configs)} URLs iCal trouvées dans Supabase")
        print(f"   (sur {len(all_configs)} configurations totales)")
        
        return configs
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la récupération: {e}")
        print(f"\n💡 Essayez de vérifier:")
        print(f"   1. Que la table 'property_sync_config' existe dans Supabase")
        print(f"   2. Que SUPABASE_SERVICE_ROLE_KEY est correct dans .env")
        print(f"   3. Que l'API Supabase est accessible")
        return []


def check_url_validity(ical_url: str) -> Dict[str, Any]:
    """
    Vérifie si une URL iCal est valide.
    
    Returns:
        {
            "valid": bool,
            "reason": str,
            "status_code": int (optionnel)
        }
    """
    # Vérification 1: URL de test
    if "test.ics" in ical_url.lower():
        return {"valid": False, "reason": "URL de test"}
    
    # Vérification 2: URL sans token
    has_token = (
        "?t=" in ical_url or 
        "?s=" in ical_url or 
        "calendarAccessSignature=" in ical_url or
        "&t=" in ical_url or
        "&s=" in ical_url
    )
    
    if not has_token:
        return {"valid": False, "reason": "Pas de token d'authentification"}
    
    # Vérification 3: Tester l'URL (HTTP GET)
    try:
        response = requests.get(ical_url, timeout=10)
        
        if response.status_code == 200:
            # Vérifier que c'est bien un calendrier iCal
            content = response.text
            if "BEGIN:VCALENDAR" in content:
                return {"valid": True, "reason": "OK", "status_code": 200}
            else:
                return {"valid": False, "reason": "Pas un calendrier iCal valide", "status_code": 200}
        
        elif response.status_code == 400:
            return {"valid": False, "reason": "HTTP 400 Bad Request", "status_code": 400}
        
        elif response.status_code == 404:
            return {"valid": False, "reason": "HTTP 404 Not Found", "status_code": 404}
        
        elif response.status_code == 401 or response.status_code == 403:
            return {"valid": False, "reason": f"HTTP {response.status_code} Unauthorized", "status_code": response.status_code}
        
        else:
            return {"valid": False, "reason": f"HTTP {response.status_code}", "status_code": response.status_code}
    
    except requests.Timeout:
        return {"valid": False, "reason": "Timeout"}
    
    except requests.ConnectionError:
        return {"valid": False, "reason": "Erreur de connexion"}
    
    except Exception as e:
        return {"valid": False, "reason": f"Erreur: {str(e)[:50]}"}


def analyze_urls(configs: List[Dict[str, Any]]):
    """Analyse toutes les URLs et identifie les invalides."""
    print(f"\n{'='*70}")
    print("🔍 ANALYSE DES URLs iCAL")
    print("="*70)
    
    valid_urls = []
    invalid_urls = []
    
    total = len(configs)
    
    for i, config in enumerate(configs, 1):
        listing_id = config.get("loft_id")  # Changé de listing_id à loft_id
        ical_url = config.get("ical_url_airbnb")  # Changé de ical_url à ical_url_airbnb
        config_id = config.get("id")
        
        # Afficher progression
        if i % 10 == 0 or i == total:
            print(f"   Vérification {i}/{total}...", end="\r")
        
        # Vérifier la validité
        result = check_url_validity(ical_url)
        
        if result["valid"]:
            valid_urls.append(config)
        else:
            invalid_urls.append({
                "id": config_id,
                "loft_id": listing_id,
                "ical_url": ical_url,
                "reason": result["reason"],
                "status_code": result.get("status_code")
            })
    
    print(f"\n\n📊 Résultats de l'analyse:")
    print(f"   ✅ URLs valides: {len(valid_urls)}")
    print(f"   ❌ URLs invalides: {len(invalid_urls)}")
    
    if invalid_urls:
        print(f"\n⚠️  URLs invalides détectées:")
        print(f"\n{'Loft ID':<25} {'Raison':<30} {'Status':<10}")
        print("-" * 70)
        
        # Grouper par raison
        by_reason = {}
        for invalid in invalid_urls[:20]:  # Afficher max 20
            loft_id = str(invalid["loft_id"]) if invalid["loft_id"] else "N/A"
            reason = invalid["reason"]
            status = str(invalid.get("status_code", "N/A"))
            
            print(f"{loft_id:<25} {reason:<30} {status:<10}")
            
            if reason not in by_reason:
                by_reason[reason] = 0
            by_reason[reason] += 1
        
        if len(invalid_urls) > 20:
            print(f"... et {len(invalid_urls) - 20} autres")
        
        print(f"\n📊 Répartition par type d'erreur:")
        for reason, count in sorted(by_reason.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {reason}: {count} URLs")
    
    return valid_urls, invalid_urls


def delete_invalid_urls(invalid_urls: List[Dict[str, Any]]):
    """Supprime les URLs invalides de Supabase."""
    print(f"\n{'='*70}")
    print("🗑️  SUPPRESSION DES URLs INVALIDES")
    print("="*70)
    
    if not invalid_urls:
        print("\n✅ Aucune URL invalide à supprimer!")
        return
    
    print(f"\n⚠️  {len(invalid_urls)} URLs invalides vont être supprimées")
    print("\nCela va:")
    print("1. Supprimer les URLs de property_sync_config")
    print("2. Le iCal Watcher ne les vérifiera plus")
    print("3. Vous pourrez les recollecte avec 2_collecter_ical.bat")
    
    # Demander confirmation
    print("\n" + "="*70)
    response = input("Voulez-vous continuer? (oui/non): ").strip().lower()
    
    if response not in ["oui", "o", "yes", "y"]:
        print("\n❌ Opération annulée")
        return
    
    # Supprimer les URLs
    deleted = 0
    errors = 0
    
    for i, invalid in enumerate(invalid_urls, 1):
        try:
            config_id = invalid["id"]
            
            # Supprimer via l'API Supabase (mettre ical_url_airbnb à NULL)
            url = f"{SUPABASE_URL}/rest/v1/property_sync_config"
            params = {"id": f"eq.{config_id}"}
            payload = {"ical_url_airbnb": None}
            
            response = requests.patch(url, headers=HEADERS, params=params, json=payload, timeout=10)
            response.raise_for_status()
            
            deleted += 1
            
            if i % 10 == 0 or i == len(invalid_urls):
                print(f"   ✅ {i}/{len(invalid_urls)} URLs supprimées...", end="\r")
        
        except Exception as e:
            errors += 1
            if errors <= 5:  # Afficher max 5 erreurs
                print(f"\n   ⚠️  Erreur pour {invalid.get('listing_id', 'N/A')}: {e}")
    
    print(f"\n\n{'='*70}")
    print(f"✅ SUPPRESSION TERMINÉE")
    print(f"{'='*70}")
    print(f"   • URLs supprimées: {deleted}")
    print(f"   • Erreurs: {errors}")
    print(f"{'='*70}\n")


def main():
    """Fonction principale."""
    
    # Vérifier la configuration
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\n❌ Configuration Supabase manquante dans .env")
        print("   Vérifiez NEXT_PUBLIC_SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY")
        return
    
    print("\n" + "="*70)
    print("🧹 NETTOYAGE DES URLs iCAL INVALIDES")
    print("="*70)
    print("\nCe script va:")
    print("1. Récupérer toutes les URLs iCal depuis Supabase")
    print("2. Vérifier chaque URL (token, HTTP status, contenu)")
    print("3. Identifier les URLs invalides")
    print("4. Proposer de les supprimer")
    
    # Étape 1: Récupérer les URLs
    configs = get_all_ical_urls()
    
    if not configs:
        print("\n⚠️  Aucune URL iCal trouvée dans Supabase")
        return
    
    # Étape 2: Analyser les URLs
    valid_urls, invalid_urls = analyze_urls(configs)
    
    # Étape 3: Supprimer les invalides
    if invalid_urls:
        delete_invalid_urls(invalid_urls)
        
        print("\n📋 PROCHAINES ÉTAPES:")
        print("1. Recollecte les URLs iCal avec tokens:")
        print("   .\\2_collecter_ical.bat")
        print("\n2. Relancez les services de synchronisation:")
        print("   docker compose -f docker-compose.sync.yml restart")
    else:
        print("\n✅ Toutes les URLs iCal sont valides!")
        print("   Aucune action nécessaire")
    
    print("\n✅ Script terminé!\n")


if __name__ == "__main__":
    main()
