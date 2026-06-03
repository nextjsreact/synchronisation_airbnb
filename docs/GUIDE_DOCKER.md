# 🐳 GUIDE DOCKER - SYNCHRONISATION AIRBNB

## Date : 31 mai 2026

---

## 🎯 POURQUOI DOCKER ?

### Avantages

✅ **Pas de fenêtres ouvertes** : Les services tournent en arrière-plan  
✅ **Redémarrage automatique** : En cas d'erreur, Docker redémarre le service  
✅ **Isolation** : Chaque service tourne dans son propre conteneur  
✅ **Logs centralisés** : Tous les logs sont accessibles facilement  
✅ **Démarrage au boot** : Les services peuvent démarrer automatiquement avec Windows  

### Inconvénients

⚠️ **Consommation mémoire** : Docker Desktop consomme ~2-3 GB de RAM  
⚠️ **Première fois plus lente** : Construction des images (2-3 minutes)  

---

## 📋 PRÉREQUIS

### 1. Docker Desktop installé

Vérifiez que Docker Desktop est installé et lancé :
```batch
docker --version
```

Si pas installé, téléchargez depuis : https://www.docker.com/products/docker-desktop

### 2. Docker Desktop lancé

Assurez-vous que Docker Desktop est en cours d'exécution (icône dans la barre des tâches).

---

## 🚀 DÉMARRAGE RAPIDE

### Étape 1 : Arrêter les fenêtres Python actuelles

Si vous avez des fenêtres Python ouvertes (iCal Watcher ou Targeted Scraper) :
1. Appuyez sur `Ctrl+C` dans chaque fenêtre
2. Fermez les fenêtres

### Étape 2 : Lancer les services Docker

```batch
DOCKER_START.bat
```

**Résultat attendu** :
```
[1/3] Arrêt des services existants...
   ✅ Services arrêtés

[2/3] Construction des images Docker...
   ⏳ Cela peut prendre 2-3 minutes la première fois...
   ✅ Images construites

[3/3] Démarrage des services en arrière-plan...
   ✅ Services démarrés

✅ SERVICES LANCÉS
```

### Étape 3 : Vérifier que ça fonctionne

```batch
DOCKER_LOGS.bat
```

Choisissez `3` pour voir les logs des 2 services.

**Résultat attendu** :
```
ical-watcher       | [19:30:00] Cycle 1 — Aucun changement
targeted-scraper   | [19:30:00] Cycle 1 — 5 entree(s) en attente
```

---

## 📋 COMMANDES DISPONIBLES

### Démarrer les services

```batch
DOCKER_START.bat
```

Lance les 2 services en arrière-plan.

### Arrêter les services

```batch
DOCKER_STOP.bat
```

Arrête les 2 services.

### Redémarrer les services

```batch
DOCKER_RESTART.bat
```

Redémarre les 2 services (utile après modification du code).

### Voir les logs

```batch
DOCKER_LOGS.bat
```

Affiche les logs en temps réel. Choisissez :
- `1` : Logs de l'iCal Watcher
- `2` : Logs du Targeted Scraper
- `3` : Logs des 2 services

Appuyez sur `Ctrl+C` pour quitter.

### Voir l'état des services

```batch
DOCKER_STATUS.bat
```

Affiche l'état actuel des services (en cours, arrêté, erreur).

---

## 🔍 SURVEILLANCE DES SERVICES

### Vérifier que les services tournent

```batch
DOCKER_STATUS.bat
```

**Résultat attendu** :
```
NAME               IMAGE                        STATUS
ical-watcher       airbnb_transfer_v2-ical-watcher       Up 5 minutes
targeted-scraper   airbnb_transfer_v2-targeted-scraper   Up 5 minutes
```

### Voir les logs en temps réel

```batch
DOCKER_LOGS.bat
```

Choisissez le service à surveiller.

### Vérifier la sync_queue

```batch
python voir_queue.py
```

**Résultat attendu** :
```
Sync Queue : 2 pending, 1 processing, 15 done
```

---

## 🛠️ DÉPANNAGE

### Problème : "Docker daemon is not running"

**Solution** : Lancez Docker Desktop depuis le menu Démarrer.

### Problème : "Error response from daemon"

**Solution** : Redémarrez Docker Desktop :
1. Clic droit sur l'icône Docker dans la barre des tâches
2. "Restart Docker Desktop"
3. Attendez 1-2 minutes
4. Relancez `DOCKER_START.bat`

### Problème : Les services ne démarrent pas

**Solution** : Vérifiez les logs :
```batch
DOCKER_LOGS.bat
```

Cherchez les erreurs et corrigez-les.

### Problème : "Port already in use"

**Solution** : Un autre service utilise le même port. Arrêtez-le ou modifiez le port dans `docker-compose.sync.yml`.

### Problème : Les services redémarrent en boucle

**Solution** : Il y a une erreur dans le code. Vérifiez les logs :
```batch
DOCKER_LOGS.bat
```

---

## 🔄 REDÉMARRAGE AUTOMATIQUE

### Configuration actuelle

Les services sont configurés avec `restart: unless-stopped` dans `docker-compose.sync.yml`.

**Cela signifie** :
- ✅ Redémarrage automatique en cas d'erreur
- ✅ Redémarrage automatique après redémarrage de Docker
- ❌ Pas de redémarrage automatique au démarrage de Windows

### Activer le démarrage automatique au boot

Pour que les services démarrent automatiquement avec Windows :

1. Configurez Docker Desktop pour démarrer avec Windows :
   - Ouvrez Docker Desktop
   - Settings → General
   - Cochez "Start Docker Desktop when you log in"

2. Les services démarreront automatiquement car ils ont `restart: unless-stopped`

---

## 📊 COMPARAISON : PYTHON vs DOCKER

| Critère | Python (fenêtres) | Docker (arrière-plan) |
|---------|-------------------|----------------------|
| Fenêtres ouvertes | ✅ 2 fenêtres | ❌ Aucune |
| Redémarrage auto | ❌ Non | ✅ Oui |
| Logs | ✅ Dans la fenêtre | ✅ Via DOCKER_LOGS.bat |
| Démarrage au boot | ❌ Non | ✅ Oui (si configuré) |
| Consommation RAM | ~500 MB | ~2-3 GB (Docker) |
| Facilité d'arrêt | ✅ Ctrl+C | ✅ DOCKER_STOP.bat |

---

## 🎯 WORKFLOW RECOMMANDÉ

### Démarrage quotidien

```batch
# Vérifier l'état
DOCKER_STATUS.bat

# Si arrêté, démarrer
DOCKER_START.bat

# Vérifier les logs
DOCKER_LOGS.bat
```

### Surveillance

```batch
# Voir l'état de la queue
python voir_queue.py

# Voir les réservations
python view_reservations.py

# Voir les logs en temps réel
DOCKER_LOGS.bat
```

### Arrêt

```batch
# Arrêter les services
DOCKER_STOP.bat
```

---

## 📝 NOTES IMPORTANTES

### Modification du code

Si vous modifiez le code Python (`ical_watcher.py` ou `targeted_scraper.py`) :

1. Arrêtez les services :
   ```batch
   DOCKER_STOP.bat
   ```

2. Reconstruisez les images :
   ```batch
   DOCKER_START.bat
   ```

Docker reconstruira automatiquement les images avec le nouveau code.

### Logs persistants

Les logs Docker sont conservés même après redémarrage. Pour voir les logs depuis le début :

```batch
docker-compose -f docker-compose.sync.yml logs
```

### Nettoyage

Pour supprimer complètement les conteneurs et images :

```batch
docker-compose -f docker-compose.sync.yml down --rmi all
```

⚠️ Attention : Cela supprime tout, vous devrez reconstruire avec `DOCKER_START.bat`.

---

## 🎉 AVANTAGES DU SYSTÈME DOCKER

1. **Pas de fenêtres** : Tout tourne en arrière-plan
2. **Fiable** : Redémarrage automatique en cas d'erreur
3. **Facile** : 1 commande pour tout lancer
4. **Logs** : Accessibles facilement à tout moment
5. **Isolation** : Chaque service dans son propre conteneur

---

## 📞 COMMANDES UTILES

```batch
# Démarrer
DOCKER_START.bat

# Arrêter
DOCKER_STOP.bat

# Redémarrer
DOCKER_RESTART.bat

# Voir les logs
DOCKER_LOGS.bat

# Voir l'état
DOCKER_STATUS.bat

# Voir la queue
python voir_queue.py

# Voir les réservations
python view_reservations.py
```

---

**Créé par Kiro le 31 mai 2026**
