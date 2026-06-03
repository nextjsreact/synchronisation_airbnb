"""
check_database_schema.py - Vérification de la structure de la base de données
==============================================================================
Ce script interroge Supabase pour obtenir la structure des tables.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

def execute_sql(query: str):
    """Exécute une requête SQL via l'API Supabase."""
    try:
        # Utiliser l'endpoint PostgREST pour exécuter du SQL
        url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
        
        # Si l'endpoint n'existe pas, utiliser une requête directe
        # On va utiliser une approche alternative avec information_schema
        
        print(f"\n🔍 Exécution de la requête SQL...")
        print(f"   Query: {query[:100]}...")
        
        # Pour Supabase, on doit utiliser PostgREST
        # On va faire une requête GET sur information_schema via une vue
        
        return None
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


def get_table_structure(table_name: str):
    """Récupère la structure d'une table via information_schema."""
    print(f"\n{'='*70}")
    print(f"📊 STRUCTURE DE LA TABLE : {table_name}")
    print(f"{'='*70}")
    
    # Requête SQL pour obtenir la structure de la table
    query = f"""
    SELECT 
        column_name,
        data_type,
        character_maximum_length,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name = '{table_name}'
    ORDER BY ordinal_position;
    """
    
    print(f"\n📋 Requête SQL à exécuter dans Supabase SQL Editor :")
    print(f"\n{query}")
    
    return query


def get_exchange_rates_info():
    """Récupère les informations sur la table de taux de change."""
    print(f"\n{'='*70}")
    print(f"💱 RECHERCHE DE LA TABLE DE TAUX DE CHANGE")
    print(f"{'='*70}")
    
    # Requête pour trouver les tables qui pourraient contenir les taux
    query = """
    SELECT 
        table_name,
        table_type
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND (
        table_name LIKE '%rate%' OR
        table_name LIKE '%exchange%' OR
        table_name LIKE '%currency%' OR
        table_name LIKE '%devise%' OR
        table_name LIKE '%taux%'
    )
    ORDER BY table_name;
    """
    
    print(f"\n📋 Requête SQL à exécuter dans Supabase SQL Editor :")
    print(f"\n{query}")
    
    return query


def get_reservations_structure():
    """Récupère la structure de la table reservations."""
    return get_table_structure('reservations')


def get_all_tables():
    """Liste toutes les tables de la base de données."""
    print(f"\n{'='*70}")
    print(f"📚 LISTE DE TOUTES LES TABLES")
    print(f"{'='*70}")
    
    query = """
    SELECT 
        table_name,
        table_type
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
    """
    
    print(f"\n📋 Requête SQL à exécuter dans Supabase SQL Editor :")
    print(f"\n{query}")
    
    return query


def main():
    print("="*70)
    print("🔍 VÉRIFICATION DE LA STRUCTURE DE LA BASE DE DONNÉES")
    print("="*70)
    print(f"\nURL Supabase: {SUPABASE_URL}")
    print(f"\n⚠️  IMPORTANT: Copiez les requêtes SQL ci-dessous et exécutez-les")
    print(f"   dans le SQL Editor de Supabase pour obtenir les résultats.")
    print(f"\n   https://supabase.com/dashboard/project/[votre-projet]/sql")
    
    # 1. Lister toutes les tables
    print(f"\n\n{'#'*70}")
    print(f"# ÉTAPE 1 : LISTER TOUTES LES TABLES")
    print(f"{'#'*70}")
    get_all_tables()
    
    # 2. Chercher la table de taux de change
    print(f"\n\n{'#'*70}")
    print(f"# ÉTAPE 2 : CHERCHER LA TABLE DE TAUX DE CHANGE")
    print(f"{'#'*70}")
    get_exchange_rates_info()
    
    # 3. Structure de la table reservations
    print(f"\n\n{'#'*70}")
    print(f"# ÉTAPE 3 : STRUCTURE DE LA TABLE RESERVATIONS")
    print(f"{'#'*70}")
    get_reservations_structure()
    
    print(f"\n\n{'='*70}")
    print(f"✅ REQUÊTES GÉNÉRÉES")
    print(f"{'='*70}")
    print(f"\n📋 INSTRUCTIONS :")
    print(f"\n1. Allez sur : https://supabase.com/dashboard")
    print(f"2. Sélectionnez votre projet")
    print(f"3. Allez dans 'SQL Editor'")
    print(f"4. Copiez et exécutez chaque requête ci-dessus")
    print(f"5. Envoyez-moi les résultats")
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
