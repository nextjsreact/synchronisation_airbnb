# Guide d'Intégration du Bouton "Synchroniser Maintenant" (Next.js & Supabase)

Puisque le scraper ciblé (`targeted_scraper.py`) surveille en continu la table `sync_queue` de Supabase pour y traiter les entrées ayant le statut `'pending'`, l'intégration dans ton application Next.js est extrêmement simple.

Il te suffit d'insérer une nouvelle ligne dans la table `sync_queue` directement depuis ton frontend ou ton backend Next.js à l'aide du client Supabase.

Voici le code exact à intégrer dans ton projet Next.js.

---

## 1. Code du Bouton React / Next.js

Tu peux créer un composant bouton réutilisable (par exemple `components/SyncLoftButton.tsx`). Ce bouton insère une demande de synchronisation pour le loft actuellement affiché.

```tsx
'use client';

import { useState } from 'react';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';

interface SyncLoftButtonProps {
  listingId: string | number;
  loftTitle: string;
}

export default function SyncLoftButton({ listingId, loftTitle }: SyncLoftButtonProps) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'queued' | 'error'>('idle');
  const supabase = createClientComponentClient();

  const handleSync = async () => {
    setLoading(true);
    setStatus('idle');

    try {
      // Insertion d'une tâche de synchronisation ciblée dans la queue
      const { error } = await supabase
        .from('sync_queue')
        .insert([
          {
            listing_id: Number(listingId),
            status: 'pending',
            reason: `Manual trigger from Next.js Dashboard for loft: ${loftTitle}`,
            retry_count: 0
          }
        ]);

      if (error) throw error;

      setStatus('queued');
      // Optionnel : remet à zéro le statut visuel après 5 secondes
      setTimeout(() => setStatus('idle'), 5000);
    } catch (err) {
      console.error('Erreur lors de la planification de la synchronisation:', err);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-start gap-2">
      <button
        onClick={handleSync}
        disabled={loading || status === 'queued'}
        className={`px-4 py-2 rounded-md font-medium text-sm transition-all flex items-center gap-2 ${
          status === 'queued'
            ? 'bg-green-600 text-white cursor-default'
            : status === 'error'
            ? 'bg-red-600 hover:bg-red-700 text-white'
            : 'bg-blue-600 hover:bg-blue-700 text-white disabled:bg-gray-400'
        }`}
      >
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Planification...
          </>
        ) : status === 'queued' ? (
          '⚡ Synchro planifiée !'
        ) : (
          '🔄 Synchroniser Maintenant'
        )}
      </button>

      {status === 'queued' && (
        <p className="text-xs text-green-600 animate-pulse">
          Le scraper commencera à synchroniser ce loft d'ici 30 secondes. (Durée : ~8 min)
        </p>
      )}
      {status === 'error' && (
        <p className="text-xs text-red-600">
          Une erreur est survenue. Veuillez réessayer ou vérifier les logs de la console.
        </p>
      )}
    </div>
  );
}
```

---

## 2. Intégration dans ta page de détail Loft

Dans ta page Next.js de gestion des lofts, importe simplement le bouton et passe-lui l'`airbnb_listing_id` et le titre du loft actuel :

```tsx
import SyncLoftButton from '@/components/SyncLoftButton';

// Exemple de page de détail d'un Loft
export default function LoftDetailPage({ loft }) {
  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">{loft.title}</h1>
          <p className="text-gray-500">ID Airbnb: {loft.airbnb_listing_id}</p>
        </div>
        
        {/* Le bouton magique */}
        <SyncLoftButton 
          listingId={loft.airbnb_listing_id} 
          loftTitle={loft.title} 
        />
      </div>
      
      {/* Reste du contenu du dashboard (réservations, calendrier, tarifs...) */}
    </div>
  );
}
```

---

## 3. Sécurité Supabase (Row Level Security - RLS)

Pour que tes utilisateurs ou ton application puissent insérer des lignes dans la table `sync_queue`, assure-toi que ta table `sync_queue` autorise l'insertion.

Si RLS (Row Level Security) est activé sur `sync_queue`, tu peux ajouter une règle simple dans la console Supabase SQL Editor :

```sql
-- Permettre à tous les utilisateurs authentifiés d'insérer des requêtes de synchro
CREATE POLICY "Allow authenticated inserts to sync_queue" 
ON public.sync_queue 
FOR INSERT 
TO authenticated 
WITH CHECK (true);
```

Si le dashboard Next.js utilise une clé de service secrète (`SUPABASE_SERVICE_ROLE_KEY`) côté serveur (Route API), la politique RLS n'est pas nécessaire car cette clé contourne les politiques RLS.

---

### Pourquoi c'est l'approche parfaite ?
1. **Zéro couplage direct** : Ton application Next.js n'a pas besoin de savoir sur quel serveur ou dans quel conteneur Docker tourne le scraper Python. Elle communique uniquement via la base de données (Supabase).
2. **Temps réel** : Grâce à la réactivité du `targeted_scraper.py` (qui scrute la base), l'action est prise en charge de manière quasi-instantanée (moins de 30 secondes).
