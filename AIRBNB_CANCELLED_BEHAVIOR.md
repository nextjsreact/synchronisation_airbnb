# Comportement des annulations Airbnb

> Documentation du comportement actuel. Date : 2026-06-07.
> Réponse à la question "que se passe-t-il quand une résa Airbnb est annulée ?"

## TL;DR

Quand une réservation Airbnb est annulée, le système met à jour `reservations.status = 'cancelled'`, crée une notification `type='cancelled'`, et exclut la résa de la détection de conflits. Les champs `cancelled_at` et `cancellation_reason` restent `NULL` (le scraper Python ne les extrait pas).

## Flow complet

### Étape 1 : Scraping Python
**Fichier** : `D:\Airbnb_transfer_v2\airbnb_scraper.py:866-870`

Le scraper extrait le champ `user_facing_status_localized` du JSON Airbnb (ex: "Annulée" en français). Il **n'extrait PAS** `cancelled_at` ni `cancellation_reason` — ces champs n'existent pas dans le dict retourné par `_parse_reservation_node` (L881-894).

### Étape 2 : Mapping FR → EN
**Fichier** : `C:\Users\SERVICE-INFO\IA\algerie-loft\lib\utils\airbnb-status-translator.ts:21-26`

```typescript
"Annulée" → "cancelled"
"Annulé"  → "cancelled"
"Annulee" → "cancelled"  // sans accent
"Cancelled" → "cancelled"
```

### Étape 3 : Service Next.js
**Fichier** : `C:\Users\SERVICE-INFO\IA\algerie-loft\lib\services\airbnb-sync-service-optimized.ts:599`

Le service construit le payload :
```typescript
{ ..., status: 'cancelled' }
// PAS de cancelled_at ni cancellation_reason
```

### Étape 4 : DB

| Cas | Action | Champs affectés |
|---|---|---|
| Résa n'existait pas (rare) | `INSERT` | `status='cancelled'`, `cancelled_at=NULL`, `cancellation_reason=NULL` |
| Résa existait (cas typique) | `UPDATE` (upsert onConflict='id') | `status='cancelled'`, `cancelled_at=NULL`, `cancellation_reason=NULL` |

**Pourquoi `cancelled_at` et `cancellation_reason` restent NULL ?**

Ces 2 champs sont dans `ADMIN_PROTECTED_FIELDS` (`airbnb-sync-service-optimized.ts:51-54`) :
```typescript
private static readonly ADMIN_PROTECTED_FIELDS = [
  'special_requests', 'payment_status', 'guest_id',
  'cancelled_at', 'cancellation_reason',  // ← ici
];
```

L51-54 : Ces champs sont **préservés** (jamais écrasés) par le sync Airbnb, même si le scraper les envoyait. Donc même si on extrayait `cancelled_at` côté Python, le service l'ignorerait pour ne pas écraser une valeur admin.

**Conséquence** : Ces champs sont en pratique **inutiles** côté scraper Airbnb. Ils ne se remplissent que via l'UI admin (formulaire d'annulation manuelle).

### Étape 5 : Notification
**Fichier** : `C:\Users\SERVICE-INFO\IA\algerie-loft\lib\airbnb\create-notification.ts:125-129`

Une notif est créée avec :
- `type = 'cancelled'`
- `title = "❌ Réservation annulée - {loft}"`
- `message = "{guestName} • {checkIn} → {checkOut} ({nights} nuits) • {price}"`
- `metadata.created_at` (= timestamp de détection)
- `is_read = FALSE` (admin doit la marquer lue)

**Source** : `airbnb-sync-service-optimized.ts:421`
```typescript
const notifType = isLinked
  ? 'updated'  // même type, mais metadata differente
  : reservation.status === 'cancelled' ? 'cancelled' : 'updated';
```

### Étape 6 : Détection de conflits (exclusion)
**Fichier** : `airbnb-sync-service-optimized.ts:512, 516`

```typescript
if (newR.status === 'cancelled') continue;     // skip nouvelle si cancelled
if (existR.status === 'cancelled') continue;   // skip existante si cancelled
```

→ Une résa annulée ne **crée JAMAIS** de conflit, même si ses dates chevauchent une autre résa active. Logique correcte.

## Champs de la table `reservations` liés à l'annulation

| Colonne | Type | Source | Valeur après annulation Airbnb |
|---|---|---|---|
| `status` | enum | Scraper Airbnb | `'cancelled'` ✅ |
| `cancelled_at` | timestamptz | UI admin uniquement | `NULL` (jamais set par scraper) |
| `cancellation_reason` | text | UI admin uniquement | `NULL` (jamais set par scraper) |

## Pourquoi on a fait ce choix (recommandation expert)

### ❌ Option rejetée : extraire `cancelled_at` côté Python + smart update

**Effort** : 2-3h (modif Python + modif service + tests)
**Risque** : Moyen
- Si l'admin annule manuellement avec une raison custom, le sync Airbnb suivant pourrait écraser (selon la logique)
- L'asymétrie temporelle : le scraper voit l'**état actuel**, pas l'**historique**. Si Airbnb a annulé il y a 30 jours, on ne récupère pas la date exacte.
- Le bénéfice est marginal : savoir "annulée il y a 30 jours" vs "annulée aujourd'hui" est rarement critique pour le business.

### ✅ Option choisie : documentation seule

**Effort** : 5 min (ce fichier)
**Risque** : 0
**Valeur** : Clarifier pour l'équipe le comportement actuel, sans toucher au code en production.

## Si on a un jour besoin de la date exacte d'annulation

### Option légère (30 min, risque faible)
Enrichir la **notification** `cancelled` avec le `detected_at` dans metadata. Le scraper n'est pas touché, seul le service Next.js est modifié pour ajouter le timestamp au moment où on détecte l'annulation.

```typescript
// Dans create-notification.ts, case 'cancelled'
metadata: {
  ...metadata,
  detected_at: new Date().toISOString(),
  // (lu depuis la notification elle-même, pas besoin de toucher au scraper)
}
```

### Option lourde (2-3h, risque moyen)
Extraire `cancelled_at` et `cancellation_reason` du JSON Airbnb + smart update conditionnel dans le service :
- Logique : "if scraped is cancelled AND db.cancelled_at IS NULL, set it from scrape"
- Sortir ces champs de `ADMIN_PROTECTED_FIELDS` ou ajouter une exception

**À faire SEULEMENT si le business en a vraiment besoin.** Pas urgent.

## Schéma récapitulatif

```
[Airbnb]              [Python]              [Next.js Service]         [DB]
   │                     │                         │                    │
   │ statut="Annulée"    │                         │                    │
   ├────────────────────▶│ statut="Annulée"        │                    │
   │                     ├────────────────────────▶│ status='cancelled'  │
   │                     │                         ├───────────────────▶│ UPDATE status
   │                     │                         │                    │
   │                     │                         │ createAirbnbNotif  │
   │                     │                         ├───────────────────▶│ INSERT notif
   │                     │                         │   type='cancelled' │   type='cancelled'
   │                     │                         │                    │
   │                     │                         │ (excluded)         │
   │                     │                         ├───────────────────▶│ no conflict
   │                     │                         │                    │
   ▼                     ▼                         ▼                    ▼
```

## Fichiers liés

- `D:\Airbnb_transfer_v2\airbnb_scraper.py:846-894` : `_parse_reservation_node` (extraction statut)
- `C:\Users\SERVICE-INFO\IA\algerie-loft\lib\utils\airbnb-status-translator.ts:21-26` : mapping FR→EN
- `C:\Users\SERVICE-INFO\IA\algerie-loft\lib\services\airbnb-sync-service-optimized.ts:51-54` : `ADMIN_PROTECTED_FIELDS`
- `C:\Users\SERVICE-INFO\IA\algerie-loft\lib\services\airbnb-sync-service-optimized.ts:419-421` : type notif selon status
- `C:\Users\SERVICE-INFO\IA\algerie-loft\lib\services\airbnb-sync-service-optimized.ts:512, 516` : exclusion conflits
- `C:\Users\SERVICE-INFO\IA\algerie-loft\lib\airbnb\create-notification.ts:125-129` : format notif cancelled
- `C:\Users\SERVICE-INFO\IA\algerie-loft\supabase\migrations\20260601000000_create_airbnb_notifications.sql:10` : type CHECK constraint

## Décision datée

- **2026-06-07** : Documentation créée. Aucun changement de code. Comportement actuel jugé suffisant pour les cas d'usage business connus.
