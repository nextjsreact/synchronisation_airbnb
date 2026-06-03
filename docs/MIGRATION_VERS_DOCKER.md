# 🐳 MIGRATION VERS DOCKER

## Date : 31 mai 2026

---

## 🎯 OBJECTIF

Passer des fenêtres Python (actuelles) aux services Docker (arrière-plan).

---

## 📊 SITUATION ACTUELLE

Vous avez **2 fenêtres Python ouvertes** :

1. **iCal Watcher** : Détecte les changements toutes les 5 min
2. **Targeted Scraper** : Traite la queue toutes les 30 sec

**Problème** : Les fenêtres doivent rester ouvertes en permanence.

---

## ✅ SOLUTION : DOCKER

Avec Docker, les services tournent **en arrière-plan** sans fenêtres ouvertes.

---

## 🚀 MIGRATION EN 3 ÉTAPES

### Étape 1 : Arrêter les fenêtres Python actuelles (2 min)

Dans chaque fenêtre Python ouverte :
1. Appuyez sur `Ctrl+C`
2. Attendez que le script s'arrête
3. Fermez la fenêtre

**Résultat** : Plus aucune fenêtre Python ouverte.

---

### Étape 2 : Lancer les services Docker (5 min)

```batch
DOCKER_START.bat
```

**Ce qui va se passer** :
1. Construction des images Docker (2-3 min la première fois)
2. Démarrage des 2 services en arrière-plan
3. Les services tournent maintenant sans fenêtres

**Résultat attendu** :
```
✅ SERVICES LANCÉS

Les 2 services tournent maintenant en arrière-plan :
  • ical-watcher (détection toutes les 5 min)
  • targeted-scraper (traitement toutes les 30 sec)
```

---

### Étape 3 : Vérifier que ça fonctionne (2 min)

```batch
DOCKER_LOGS.bat
```

Choisissez `3` pour voir les logs des 2 services.

**Résultat attendu** :
```
ical-watcher       | [19:30:00] Cycle 1 — Aucun changement
targeted-scraper   | [19:30:00] Cycle 1 — 5 entree(s) en attente
targeted-scraper   |    Queue #17 — listing 1637674182168800916
targeted-scraper   |    21 reservations trouvees pour 1637674182168800916
```

**Si vous voyez ça** : ✅ La migration est réussie !

Appuyez sur `Ctrl+C` pour quitter les logs.

---

## 📋 COMMANDES À CONNAÎTRE

### Démarrer les services

```batch
DOCKER_START.bat
```

### Arrêter les services

```batch
DOCKER_STOP.bat
```

### Voir les logs

```batch
DOCKER_LOGS.bat
```

### Voir l'état

```batch
DOCKER_STATUS.bat
```

---

## 🔍 VÉRIFICATION COMPLÈTE

### 1. Vérifier que Docker tourne

```batch
DOCKER_STATUS.bat
```

**Résultat attendu** :
```
NAME               STATUS
ical-watcher       Up 5 minutes
targeted-scraper   Up 5 minutes
```

### 2. Vérifier la sync_queue

```batch
python voir_queue.py
```

**Résultat attendu** :
```
Sync Queue : 2 pending, 1 processing, 15 done
```

### 3. Vérifier les réservations

```batch
python view_reservations.py
```

**Résultat attendu** :
```
3983 réservations dans la base
Dernière mise à jour : 31/05/2026 19:30
```

---

## 🎉 AVANTAGES DE DOCKER

| Avant (Python) | Après (Docker) |
|----------------|----------------|
| 2 fenêtres ouvertes | 0 fenêtre |
| Arrêt si fermeture accidentelle | Redémarrage automatique |
| Pas de logs après fermeture | Logs persistants |
| Démarrage manuel | Démarrage automatique (optionnel) |

---

## ⚠️ POINTS D'ATTENTION

### Docker Desktop doit être lancé

Les services Docker ne fonctionnent que si Docker Desktop est lancé.

**Vérification** : Icône Docker dans la barre des tâches.

### Consommation mémoire

Docker Desktop consomme ~2-3 GB de RAM.

**Si problème** : Fermez Docker Desktop quand vous n'en avez pas besoin.

### Modification du code

Si vous modifiez le code Python, vous devez reconstruire les images :

```batch
DOCKER_STOP.bat
DOCKER_START.bat
```

---

## 🔄 RETOUR EN ARRIÈRE (si besoin)

Si vous voulez revenir aux fenêtres Python :

1. Arrêtez Docker :
   ```batch
   DOCKER_STOP.bat
   ```

2. Lancez les fenêtres Python :
   ```batch
   LANCER_MAINTENANT.bat
   ```

---

## 📊 COMPARAISON DÉTAILLÉE

### Fenêtres Python

**Avantages** :
- ✅ Logs visibles en temps réel
- ✅ Facile à arrêter (Ctrl+C)
- ✅ Pas besoin de Docker

**Inconvénients** :
- ❌ 2 fenêtres toujours ouvertes
- ❌ Arrêt si fermeture accidentelle
- ❌ Pas de redémarrage automatique
- ❌ Pas de démarrage au boot

### Docker

**Avantages** :
- ✅ Pas de fenêtres ouvertes
- ✅ Redémarrage automatique
- ✅ Logs persistants
- ✅ Démarrage au boot (optionnel)
- ✅ Isolation des services

**Inconvénients** :
- ❌ Nécessite Docker Desktop
- ❌ Consomme plus de RAM (~2-3 GB)
- ❌ Logs via commande (pas en temps réel par défaut)

---

## 🎯 RECOMMANDATION

### Pour vous

**Utilisez Docker** car :
1. Vous voulez que ça tourne en arrière-plan
2. Vous ne voulez pas de fenêtres ouvertes
3. Vous voulez un système fiable 24/7

### Quand utiliser les fenêtres Python

- Pendant le développement (pour voir les logs en temps réel)
- Pour tester rapidement une modification
- Si Docker Desktop n'est pas disponible

---

## 📝 CHECKLIST DE MIGRATION

- [ ] Arrêter les fenêtres Python (Ctrl+C)
- [ ] Fermer les fenêtres
- [ ] Vérifier que Docker Desktop est lancé
- [ ] Lancer `DOCKER_START.bat`
- [ ] Attendre la construction des images (2-3 min)
- [ ] Vérifier avec `DOCKER_STATUS.bat`
- [ ] Voir les logs avec `DOCKER_LOGS.bat`
- [ ] Vérifier la queue avec `python voir_queue.py`
- [ ] ✅ Migration terminée !

---

## 🎉 APRÈS LA MIGRATION

Vous pouvez maintenant :
- ✅ Fermer toutes les fenêtres
- ✅ Laisser les services tourner en arrière-plan
- ✅ Vérifier les logs quand vous voulez avec `DOCKER_LOGS.bat`
- ✅ Arrêter/redémarrer facilement avec les scripts `.bat`

**Le système tourne maintenant 24/7 sans intervention !**

---

**Créé par Kiro le 31 mai 2026**
