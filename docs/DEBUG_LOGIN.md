# 🔍 Debug Login Airbnb

## Problème Actuel

Le script affiche :
```
✅ Connecté sans 2FA !
❌ Échec de connexion — vérifiez vos identifiants dans .env
```

Cela signifie que le script pense être connecté, mais il est toujours sur la page de login.

---

## 🔧 Améliorations Ajoutées

### 1. Logs détaillés
Le script affiche maintenant :
- ✓ Quel bouton est trouvé et cliqué
- 🔍 L'URL actuelle à chaque étape
- 🔍 L'URL finale après connexion
- ⚠️ Les erreurs de chaque tentative de bouton

### 2. Délais augmentés
- Attente après soumission mot de passe : **5s → 8s**
- Attente finale : **2s → 3s**

### 3. Retry mot de passe
- 3 tentatives pour trouver le champ mot de passe
- Détection si déjà redirigé (pas besoin de mot de passe)

### 4. Fichier de debug automatique
Si échec, le script sauvegarde automatiquement :
- `output/debug_login_failed.html` - Page HTML complète

---

## 🚀 Prochaine Exécution

Relancez le script :
```bash
python airbnb_scraper.py
```

### Ce que vous devriez voir maintenant :

```
🔐 Connexion à Airbnb...
   ✓ Email saisi
   ✓ Mot de passe saisi
   ✓ Bouton trouvé : button[type="submit"]
   ⏳ Attente de la réponse du serveur...
   🔍 URL actuelle : https://www.airbnb.com/...
   ✅ Connecté sans 2FA !
   🔍 URL finale : https://www.airbnb.com/hosting
   ✅ Connexion réussie !
```

---

## 🔍 Diagnostic selon les Logs

### Cas 1 : "⚠️ Champ mot de passe introuvable"
**Cause :** Le formulaire Airbnb a changé ou vous êtes déjà connecté

**Solution :**
1. Vérifier `output/debug_login_failed.html`
2. Chercher le sélecteur du champ mot de passe
3. L'ajouter dans le script

### Cas 2 : "ℹ️ Aucun bouton trouvé, utilisation de Enter"
**Cause :** Les sélecteurs de boutons ne correspondent pas

**Solution :**
1. Observer le navigateur (mode visible)
2. Identifier le bon sélecteur
3. L'ajouter dans la liste

### Cas 3 : URL finale = "https://www.airbnb.com/login"
**Cause :** Identifiants incorrects OU formulaire non soumis

**Solutions :**
1. Vérifier `.env` :
   ```bash
   AIRBNB_EMAIL=votre@email.com
   AIRBNB_PASSWORD=votre_mot_de_passe
   ```
2. Tester manuellement dans le navigateur
3. Vérifier que le mot de passe ne contient pas de caractères spéciaux problématiques

### Cas 4 : URL finale = "https://www.airbnb.com/account-security/..."
**Cause :** Airbnb demande une vérification supplémentaire

**Solution :**
1. Compléter la vérification manuellement dans le navigateur
2. Le script attendra que vous terminiez
3. Configurer `TOTP_SECRET` pour automatiser

---

## 📝 Checklist de Vérification

Avant de relancer :

- [ ] `.env` contient le bon email
- [ ] `.env` contient le bon mot de passe
- [ ] Le mot de passe fonctionne sur airbnb.com (test manuel)
- [ ] `HEADLESS=false` (pour voir ce qui se passe)
- [ ] Pas de caractères spéciaux bizarres dans le mot de passe
- [ ] Connexion Internet stable

---

## 🎯 Actions Recommandées

### 1. Observer le navigateur
Avec `HEADLESS=false`, vous verrez exactement ce qui se passe :
- Le formulaire se remplit-il correctement ?
- Le bouton est-il cliqué ?
- Y a-t-il un message d'erreur ?

### 2. Vérifier le fichier debug
Après échec, ouvrir `output/debug_login_failed.html` dans un navigateur :
- Chercher les messages d'erreur
- Vérifier si le formulaire est différent
- Identifier les bons sélecteurs

### 3. Test manuel
Essayer de se connecter manuellement sur airbnb.com avec les mêmes identifiants :
- Si ça ne marche pas → problème d'identifiants
- Si ça demande une vérification → configurer TOTP
- Si ça marche → problème de sélecteurs dans le script

---

## 💡 Astuces

### Délai personnalisé
Si votre connexion est lente, augmentez les délais :
```python
# Dans login(), ligne ~240
page.wait_for_timeout(10000)  # 10 secondes au lieu de 8
```

### Mode ultra-verbose
Pour voir TOUT ce qui se passe :
```python
# Ajouter au début de login()
page.on("console", lambda msg: print(f"   [BROWSER] {msg.text}"))
```

### Screenshot automatique
Pour capturer l'écran à chaque étape :
```python
# Après chaque action importante
page.screenshot(path=f"output/step_{step_number}.png")
```

---

## 🆘 Si Rien ne Fonctionne

1. **Supprimer la session** :
   ```bash
   del output\airbnb_session.json
   ```

2. **Tester avec Playwright standard** :
   ```bash
   pip uninstall cloakbrowser
   # Le script basculera automatiquement sur Playwright
   ```

3. **Vérifier les versions** :
   ```bash
   python --version
   pip show cloakbrowser
   pip show playwright
   ```

4. **Partager les logs** :
   ```bash
   python airbnb_scraper.py > logs.txt 2>&1
   ```
   Puis envoyer `logs.txt` + `output/debug_login_failed.html`

---

*Guide créé le 25/05/2026 à 00:52*
