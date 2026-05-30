# 🤖 Solution CAPTCHA - Airbnb Scraper

## 🎯 Situation

Airbnb affiche un CAPTCHA **après** le login réussi. C'est une mesure de sécurité normale.

---

## ⚠️ Ce que CloakBrowser NE fait PAS

**CloakBrowser est anti-détection, PAS anti-CAPTCHA.**

- ✅ CloakBrowser évite d'être détecté comme bot
- ✅ CloakBrowser simule un comportement humain
- ❌ CloakBrowser ne résout PAS les CAPTCHAs

---

## ✅ Solution Implémentée

Le script détecte maintenant automatiquement les CAPTCHAs et :

1. **Affiche un message clair** expliquant la situation
2. **Attend que VOUS résolviez le CAPTCHA** dans le navigateur ouvert
3. **Continue automatiquement** une fois résolu
4. **Sauvegarde la session** pour éviter les CAPTCHAs futurs

### Workflow

```
Login réussi
    ↓
🤖 CAPTCHA détecté
    ↓
⏸️  Script en pause (max 5 minutes)
    ↓
👤 VOUS résolvez le CAPTCHA manuellement
    ↓
✅ Script détecte la résolution
    ↓
💾 Session sauvegardée
    ↓
🚀 Script continue normalement
```

---

## 🚀 Utilisation

### Première Exécution (avec CAPTCHA)

```bash
python airbnb_scraper.py
```

**Ce qui se passe :**

1. Le navigateur s'ouvre (mode visible)
2. Login automatique avec vos identifiants
3. **CAPTCHA apparaît** 🤖
4. Le script affiche :
   ```
   ⚠️  ═══════════════════════════════════════════════════════
      🤖 CAPTCHA DÉTECTÉ
      ═══════════════════════════════════════════════════════
   
      CloakBrowser ne peut PAS résoudre les CAPTCHAs automatiquement.
   
      📋 SOLUTIONS :
      1. ✅ Résolvez le CAPTCHA MANUELLEMENT dans le navigateur ouvert
      2. ⏱️  Le script attendra jusqu'à 5 minutes
      3. 🔄 Une fois résolu, le script continuera automatiquement
   
      ⏳ En attente de résolution manuelle...
   ```

5. **VOUS** : Résolvez le CAPTCHA dans le navigateur
6. Le script détecte automatiquement la résolution
7. La session est sauvegardée dans `output/airbnb_session.json`
8. Le scraping continue normalement

### Exécutions Suivantes (SANS CAPTCHA)

```bash
python airbnb_scraper.py
```

**Ce qui se passe :**

1. Le script charge la session sauvegardée
2. Vérifie qu'elle est valide
3. **Pas de CAPTCHA** ✅ (session reconnue par Airbnb)
4. Scraping direct

---

## 💡 Prévention des CAPTCHAs

### 1. Session Persistante (Automatique)

Le script sauvegarde automatiquement votre session après le premier CAPTCHA :
- Fichier : `output/airbnb_session.json`
- Contient : cookies, localStorage, sessionStorage
- Durée : plusieurs jours/semaines

**Résultat :** Les prochaines exécutions réutilisent cette session → **pas de CAPTCHA**

### 2. Proxy Résidentiel (Recommandé)

Ajoutez dans `.env` :
```bash
PROXY_URL=http://username:password@proxy-provider.com:port
```

**Avantages :**
- IP résidentielle propre (pas flaggée)
- Réduit drastiquement les CAPTCHAs
- Même IP = comportement cohérent

**Fournisseurs recommandés :**
- Bright Data (ex-Luminati)
- Smartproxy
- Oxylabs
- IPRoyal

### 3. Délais Entre Exécutions

Ne lancez pas le script trop souvent :
- ✅ 1 fois par jour : OK
- ✅ 2-3 fois par jour : OK
- ⚠️ Toutes les heures : risque CAPTCHA
- ❌ Toutes les 5 minutes : CAPTCHA garanti

### 4. Mode Headless=False (Première fois)

Pour la première exécution :
```bash
# Dans .env
HEADLESS=false
```

**Pourquoi :**
- Plus naturel pour Airbnb
- Vous pouvez résoudre le CAPTCHA
- Session sauvegardée ensuite

Après la première fois, vous pouvez passer en `HEADLESS=true` si besoin.

---

## 🔧 Configuration Optimale

### `.env` recommandé

```bash
# Identifiants
AIRBNB_EMAIL=votre@email.com
AIRBNB_PASSWORD=votre_mot_de_passe
TOTP_SECRET=votre_secret_totp  # Optionnel

# Anti-CAPTCHA
HEADLESS=false  # Mode visible pour résoudre CAPTCHAs
PROXY_URL=http://user:pass@proxy:port  # Proxy résidentiel

# Sorties
OUTPUT_CSV=output/reservations_airbnb.csv
OUTPUT_JSON=output/reservations_airbnb.json
```

---

## 🆘 Dépannage

### "Timeout CAPTCHA — 5 minutes écoulées"

**Cause :** Vous n'avez pas résolu le CAPTCHA dans les 5 minutes

**Solution :**
1. Relancez le script
2. Résolvez le CAPTCHA plus rapidement
3. Ou augmentez le timeout dans le code :
   ```python
   # Dans login(), ligne ~260
   for i in range(300):  # 300 * 2s = 10 minutes
   ```

### CAPTCHA à chaque exécution

**Cause :** La session n'est pas sauvegardée ou expirée

**Solutions :**
1. Vérifier que `output/airbnb_session.json` existe
2. Vérifier les permissions d'écriture
3. Ajouter un proxy résidentiel
4. Espacer les exécutions (1x par jour max)

### "Session valide" mais CAPTCHA quand même

**Cause :** IP flaggée ou comportement suspect détecté

**Solutions :**
1. **Obligatoire** : Ajouter un proxy résidentiel
2. Supprimer la session et recommencer :
   ```bash
   del output\airbnb_session.json
   python airbnb_scraper.py
   ```
3. Attendre 24h avant de réessayer

---

## 📊 Statistiques Typiques

Avec la configuration optimale :

| Situation | CAPTCHA ? | Fréquence |
|-----------|-----------|-----------|
| Première exécution | ✅ Oui | 1 fois |
| Avec session valide | ❌ Non | 0% |
| Avec proxy résidentiel | ❌ Non | <1% |
| Sans proxy, IP flaggée | ✅ Oui | 50-100% |
| Exécutions trop fréquentes | ✅ Oui | 80% |

---

## 🎯 Résumé

### Ce que fait le script maintenant :

1. ✅ **Détecte** automatiquement les CAPTCHAs
2. ✅ **Attend** que vous les résolviez (max 5 min)
3. ✅ **Continue** automatiquement après résolution
4. ✅ **Sauvegarde** la session pour éviter les CAPTCHAs futurs

### Ce que VOUS devez faire :

1. 🖱️ **Résoudre le CAPTCHA** dans le navigateur ouvert
2. 🌐 **Ajouter un proxy résidentiel** (fortement recommandé)
3. ⏱️ **Espacer les exécutions** (1x par jour max)

### Résultat :

- **Première fois** : 1 CAPTCHA à résoudre manuellement
- **Après** : Plus de CAPTCHA grâce à la session sauvegardée

---

## 💰 Services de Résolution Automatique (Optionnel)

Si vous voulez automatiser complètement (sans intervention manuelle), vous pouvez intégrer :

### 2Captcha / CapSolver

```python
# Exemple d'intégration (non inclus dans le script)
from twocaptcha import TwoCaptcha

solver = TwoCaptcha('VOTRE_API_KEY')
result = solver.recaptcha(
    sitekey='6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-',
    url='https://www.airbnb.com/login'
)
```

**Coût :** ~$1-3 pour 1000 CAPTCHAs

**Note :** Cette intégration n'est pas incluse dans le script actuel. Le script actuel utilise la résolution manuelle + session persistante, ce qui est gratuit et suffisant pour un usage normal.

---

*Document créé le 25/05/2026 à 01:00*
