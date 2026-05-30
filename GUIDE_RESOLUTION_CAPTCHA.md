# 🎯 Guide : Résolution du CAPTCHA Arkose

**Date** : 25 mai 2026  
**Statut** : ✅ Détection fonctionne - Amélioration de la résolution

---

## ✅ SUCCÈS : Détection fonctionne !

Votre dernier test a montré que la détection fonctionne parfaitement :

```
⚠️  ═══════════════════════════════════════════════════════
   🤖 CAPTCHA DÉTECTÉ APRÈS EMAIL
   ═══════════════════════════════════════════════════════
```

**Le problème maintenant** : Le script n'a pas détecté que vous avez résolu le CAPTCHA (timeout après 5 minutes).

---

## 🔧 AMÉLIORATIONS AJOUTÉES

### 1. Debug en temps réel

Le script affiche maintenant toutes les 20 secondes :
```
🔍 Debug: URL=https://fr.airbnb.com/login?... | Password field=False
```

Cela vous permet de voir si le champ mot de passe apparaît.

### 2. Captures d'écran automatiques

Toutes les 30 secondes, le script sauvegarde une capture :
```
📸 Capture sauvegardée : output/debug_captcha_30s.png
📸 Capture sauvegardée : output/debug_captcha_60s.png
📸 Capture sauvegardée : output/debug_captcha_90s.png
...
```

Vous pourrez voir exactement ce qui se passe dans le navigateur.

### 3. Détection améliorée

Le script vérifie maintenant **3 conditions** pour détecter la résolution :

1. **Champ mot de passe apparu** : `"password"` ou `"mot de passe"` dans le texte visible
2. **Redirection hors login** : URL ne contient plus `/login` ou `/signin`
3. **Redirection vers page connectée** : URL contient `/host/`, `/trips`, `/account`, etc.

---

## 🧪 NOUVEAU TEST

### Relancez le script

```bash
python airbnb_scraper.py
```

### Ce que vous verrez

```
⚠️  🤖 CAPTCHA DÉTECTÉ APRÈS EMAIL
   ⏳ En attente de résolution manuelle...

   ⏳ 10s écoulées... (max 300s)
   ⏳ 20s écoulées... (max 300s)
   🔍 Debug: URL=https://fr.airbnb.com/login?... | Password field=False
   📸 Capture sauvegardée : output/debug_captcha_30s.png
   ⏳ 30s écoulées... (max 300s)
   ⏳ 40s écoulées... (max 300s)
   🔍 Debug: URL=https://fr.airbnb.com/login?... | Password field=False
   ...
```

### Actions à effectuer

1. **Regardez le navigateur Chrome** qui s'est ouvert
2. **Résolvez le CAPTCHA Arkose** :
   - Cliquez sur les images demandées
   - Suivez les instructions du CAPTCHA
   - Attendez la validation
3. **Observez la console** :
   - Le debug doit montrer `Password field=True` quand c'est résolu
   - Le script doit afficher `✅ CAPTCHA résolu !`

---

## 🔍 DIAGNOSTIC

### Si le timeout persiste

Après le test, vérifiez les captures d'écran dans `output/` :

```
output/debug_captcha_30s.png
output/debug_captcha_60s.png
output/debug_captcha_90s.png
...
```

**Regardez ces images pour voir** :
- ✅ Le CAPTCHA est-il visible ?
- ✅ Avez-vous cliqué dessus ?
- ✅ Le CAPTCHA a-t-il été validé ?
- ✅ Le champ mot de passe est-il apparu ?

### Scénarios possibles

#### Scénario 1 : CAPTCHA non résolu
**Symptôme** : Les captures montrent toujours le CAPTCHA  
**Solution** : Résolvez le CAPTCHA plus rapidement (vous avez 5 minutes)

#### Scénario 2 : CAPTCHA résolu mais champ mot de passe n'apparaît pas
**Symptôme** : Les captures montrent une page blanche ou un autre écran  
**Solution** : Airbnb utilise peut-être un autre flux (lien magique, redirection directe)

#### Scénario 3 : Champ mot de passe apparaît mais non détecté
**Symptôme** : Les captures montrent le champ mot de passe mais `Password field=False`  
**Solution** : Le texte du champ est peut-être en anglais ("Password") au lieu de français

---

## 💡 SOLUTIONS ALTERNATIVES

### Option 1 : Augmenter le timeout

Si vous avez besoin de plus de 5 minutes, modifiez dans `.env` :

```env
# Ajouter cette ligne (timeout en secondes)
CAPTCHA_TIMEOUT=600  # 10 minutes au lieu de 5
```

### Option 2 : Mode manuel complet

Si la détection automatique ne fonctionne pas, vous pouvez :

1. Résoudre le CAPTCHA
2. Saisir le mot de passe manuellement
3. Appuyer sur Entrée pour continuer
4. Le script reprendra après la connexion

### Option 3 : Proxy résidentiel (recommandé)

Configurez un proxy résidentiel dans `.env` :

```env
PROXY_URL=http://username:password@proxy-provider.com:port
```

**Avantages** :
- ✅ Moins de CAPTCHAs (IP résidentielle = plus de confiance)
- ✅ Session persistante après première connexion
- ✅ Vous ne verrez le CAPTCHA qu'une seule fois

**Providers recommandés** :
- Bright Data (ex-Luminati)
- Smartproxy
- Oxylabs

---

## 📊 LOGS DE DEBUG

### Interprétation des logs

```
🔍 Debug: URL=https://fr.airbnb.com/login?... | Password field=False
```

| Valeur | Signification |
|--------|---------------|
| `URL=.../login?...` | Toujours sur la page de login |
| `Password field=False` | Champ mot de passe pas encore visible |
| `Password field=True` | ✅ Champ mot de passe détecté = CAPTCHA résolu |

```
📸 Capture sauvegardée : output/debug_captcha_30s.png
```

| Fichier | Moment |
|---------|--------|
| `debug_captcha_30s.png` | 30 secondes après détection |
| `debug_captcha_60s.png` | 1 minute après détection |
| `debug_captcha_90s.png` | 1 minute 30 après détection |

---

## 🎯 CHECKLIST DE RÉSOLUTION

Pendant que le script attend :

- [ ] Le navigateur Chrome est ouvert et visible
- [ ] La page Airbnb affiche le CAPTCHA Arkose
- [ ] Vous cliquez sur le CAPTCHA et suivez les instructions
- [ ] Le CAPTCHA affiche une validation (✓ ou message de succès)
- [ ] La page se recharge ou affiche le champ mot de passe
- [ ] Le script détecte `Password field=True` dans les logs
- [ ] Le script affiche `✅ CAPTCHA résolu !`

---

## 🚨 PROBLÈMES CONNUS

### Le CAPTCHA ne s'affiche pas dans le navigateur

**Cause** : Le navigateur est en arrière-plan ou minimisé  
**Solution** : Cliquez sur la fenêtre Chrome pour la mettre au premier plan

### Le CAPTCHA est trop difficile

**Cause** : Airbnb utilise Arkose Labs qui peut être complexe  
**Solution** : 
- Prenez votre temps (vous avez 5 minutes)
- Si vous échouez, relancez le script
- Utilisez un proxy résidentiel pour éviter les CAPTCHAs difficiles

### Le script timeout même après résolution

**Cause** : La détection du champ mot de passe ne fonctionne pas  
**Solution** : Vérifiez les captures d'écran et partagez-les pour diagnostic

---

## 📝 PROCHAINES ÉTAPES

1. **Relancez le script** : `python airbnb_scraper.py`
2. **Résolvez le CAPTCHA** dans les 5 minutes
3. **Observez les logs** : Cherchez `Password field=True`
4. **Vérifiez les captures** : Regardez `output/debug_captcha_*.png`
5. **Partagez les résultats** : Dites-moi ce qui se passe !

---

## 🎉 OBJECTIF FINAL

Une fois le CAPTCHA résolu avec succès :

1. ✅ Le script continuera automatiquement
2. ✅ Il saisira le mot de passe
3. ✅ Il gérera le 2FA si nécessaire
4. ✅ Il sauvegardera la session dans `output/airbnb_session.json`
5. ✅ **Les prochaines exécutions ne montreront plus de CAPTCHA !**

---

**Relancez maintenant et observez les nouveaux logs de debug !** 🚀
