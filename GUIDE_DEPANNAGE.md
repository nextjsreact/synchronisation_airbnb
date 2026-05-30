# 🔧 Guide de Dépannage - airbnb_scraper.py

## ✅ Corrections Appliquées (25/05/2026 00:45)

### 1. Sélecteurs de boutons robustes
**Problème :** `ElementNotAttachedError: Element 'button[type="submit"]' failed`

**Solution :** Utilisation de multiples sélecteurs avec fallback sur Enter
```python
# Essaie plusieurs sélecteurs
for btn_sel in [
    'button[type="submit"]',
    'button[data-testid="signup-login-submit-btn"]',
    'button:has-text("Continue")',
    'button:has-text("Continuer")',
]:
    try:
        btn = page.locator(btn_sel)
        if btn.count() > 0 and btn.first.is_visible():
            btn.first.click()
            break
    except Exception:
        continue
# Fallback : appuyer sur Enter
if not submitted:
    page.keyboard.press("Enter")
```

### 2. Warning regex JavaScript corrigé
**Problème :** `SyntaxWarning: invalid escape sequence '\/'`

**Solution :** Utilisation de raw string `r"""..."""`

---

## 🚀 Relancer le Script

```bash
python airbnb_scraper.py
```

Le script devrait maintenant :
1. ✅ Saisir l'email
2. ✅ Cliquer sur "Continuer" (ou appuyer sur Enter)
3. ✅ Saisir le mot de passe
4. ✅ Se connecter

---

## 🔍 Diagnostic en Cas d'Erreur

### Erreur : "Champ email introuvable"
**Cause :** Le formulaire Airbnb a changé

**Solution :**
1. Ouvrir le navigateur en mode visible (`HEADLESS=false`)
2. Observer quel sélecteur fonctionne
3. Ajouter le sélecteur dans la liste

### Erreur : "Timeout 2FA"
**Cause :** Le code 2FA n'a pas été saisi à temps

**Solutions :**
- Configurer `TOTP_SECRET` dans `.env` pour automatisation
- Augmenter le timeout dans `handle_2fa()` (actuellement 4 minutes)

### Erreur : "CAPTCHA détecté"
**Cause :** Airbnb détecte un comportement automatisé

**Solutions :**
1. Utiliser un proxy résidentiel :
   ```bash
   PROXY_URL=http://user:pass@proxy:port
   ```
2. Supprimer la session et relancer :
   ```bash
   del output\airbnb_session.json
   python airbnb_scraper.py
   ```
3. Attendre quelques heures avant de réessayer

### Erreur : "API Next.js désactivée"
**Cause :** Le fichier `airbnb_api_client.py` est manquant ou a une erreur

**Solution :**
1. Vérifier que `airbnb_api_client.py` existe
2. Tester l'import :
   ```bash
   python -c "from airbnb_api_client import check_api_health"
   ```

---

## 📝 Logs de Debug

Le script crée automatiquement des fichiers de debug :

| Fichier | Contenu | Quand |
|---------|---------|-------|
| `output/debug_api_response.json` | Réponse API GraphQL | Toujours |
| `output/debug_login_page.html` | Page de login | Si champ email introuvable |
| `output/debug_captcha.png` | Screenshot CAPTCHA | Si CAPTCHA détecté |
| `output/debug_verification.png` | Vérification supplémentaire | Si bloqué après login |
| `output/airbnb_session.json` | Session sauvegardée | Après login réussi |

---

## 🎯 Checklist de Vérification

Avant de lancer le script :

- [ ] `.env` configuré avec `AIRBNB_EMAIL` et `AIRBNB_PASSWORD`
- [ ] `TOTP_SECRET` configuré (optionnel mais recommandé)
- [ ] `HEADLESS=false` pour la première exécution
- [ ] `airbnb_api_client.py` existe et fonctionne
- [ ] Connexion Internet stable
- [ ] Pas de VPN qui pourrait bloquer Airbnb

---

## 💡 Astuces

### 1. Mode Debug Complet
```bash
# Dans .env
HEADLESS=false
```
Permet de voir ce qui se passe dans le navigateur

### 2. Réutilisation de Session
Après la première connexion réussie, le script réutilise automatiquement la session :
```
🔍 Vérification de la session existante...
✅ Session valide — connexion non nécessaire
```

### 3. Proxy Résidentiel
Pour éviter les CAPTCHA :
```bash
# Dans .env
PROXY_URL=http://username:password@proxy.example.com:8080
```

### 4. Test Rapide de Connexion
```bash
# Tester uniquement la connexion (arrêter après login)
python -c "from airbnb_scraper import login; from cloakbrowser import launch; browser = launch(headless=False); page = browser.new_page(); login(page); input('Appuyez sur Enter pour fermer...')"
```

---

## 📞 Support

Si le problème persiste :

1. **Capturer les logs complets** :
   ```bash
   python airbnb_scraper.py > logs.txt 2>&1
   ```

2. **Vérifier les fichiers de debug** dans `output/`

3. **Partager** :
   - Le message d'erreur complet
   - Les fichiers `debug_*.html` ou `debug_*.png`
   - La version de Python : `python --version`
   - La version de CloakBrowser : `pip show cloakbrowser`

---

*Guide mis à jour le 25/05/2026 à 00:45*
