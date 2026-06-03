# 🔐 Résolution du Problème d'Authentification GitHub

**Erreur** : `Permission denied to tigdittgolf-lab`

**Cause** : Vous êtes connecté avec le compte `tigdittgolf-lab` mais le repository appartient à `nextjsreact`.

---

## 🔧 Solutions

### Solution 1 : Utiliser un Personal Access Token (Recommandé)

#### Étape 1 : Générer un Token

1. Connectez-vous sur GitHub avec le compte **nextjsreact**
2. Allez sur : https://github.com/settings/tokens
3. Cliquez sur **"Generate new token"** → **"Generate new token (classic)"**
4. Remplissez :
   - **Note** : `Airbnb Sync - Windows`
   - **Expiration** : 90 days (ou No expiration)
   - **Cochez** : `repo` (Full control of private repositories)
5. Cliquez sur **"Generate token"**
6. **COPIEZ LE TOKEN** (vous ne le reverrez plus !)
   - Format : `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

#### Étape 2 : Configurer Git pour Utiliser le Token

**Option A : Via Credential Manager (Windows)**

```bash
# Supprimer les anciennes credentials
git credential-manager delete https://github.com

# Lors du prochain push, Git vous demandera :
# Username: nextjsreact
# Password: [COLLEZ VOTRE TOKEN ICI]
```

**Option B : Inclure le Token dans l'URL (Temporaire)**

```bash
# Supprimer le remote actuel
git remote remove origin

# Ajouter avec le token dans l'URL
git remote add origin https://nextjsreact:VOTRE_TOKEN@github.com/nextjsreact/synchronisation_airbnb.git

# Pousser
git push -u origin main
```

⚠️ **Attention** : Cette méthode stocke le token en clair dans `.git/config`

**Option C : Utiliser Git Credential Manager**

```bash
# Configurer le credential helper
git config --global credential.helper wincred

# Pousser (Git demandera les credentials)
git push -u origin main

# Entrez :
# Username: nextjsreact
# Password: [VOTRE TOKEN]
```

---

### Solution 2 : Utiliser GitHub CLI (Plus Simple)

#### Étape 1 : Installer GitHub CLI

Téléchargez depuis : https://cli.github.com/

#### Étape 2 : Se Connecter

```bash
# Se connecter avec le compte nextjsreact
gh auth login

# Suivez les instructions :
# 1. Choisir : GitHub.com
# 2. Choisir : HTTPS
# 3. Choisir : Login with a web browser
# 4. Copier le code affiché
# 5. Ouvrir le navigateur et coller le code
# 6. Se connecter avec nextjsreact
```

#### Étape 3 : Pousser

```bash
git push -u origin main
```

---

### Solution 3 : Utiliser SSH (Plus Sécurisé)

#### Étape 1 : Générer une Clé SSH

```bash
# Générer la clé
ssh-keygen -t ed25519 -C "votre.email@example.com"

# Appuyez sur Entrée pour accepter l'emplacement par défaut
# Entrez un mot de passe (optionnel)
```

#### Étape 2 : Ajouter la Clé à GitHub

```bash
# Copier la clé publique
type %USERPROFILE%\.ssh\id_ed25519.pub
```

1. Copiez le contenu affiché
2. Allez sur : https://github.com/settings/keys
3. Cliquez sur **"New SSH key"**
4. Titre : `Windows - Airbnb Sync`
5. Collez la clé
6. Cliquez sur **"Add SSH key"**

#### Étape 3 : Changer l'URL du Remote

```bash
# Supprimer le remote HTTPS
git remote remove origin

# Ajouter le remote SSH
git remote add origin git@github.com:nextjsreact/synchronisation_airbnb.git

# Pousser
git push -u origin main
```

---

## 🚀 Script Automatique avec Token

Créez un fichier `push_with_token.bat` :

```batch
@echo off
echo ========================================
echo   PUSH VERS GITHUB AVEC TOKEN
echo ========================================
echo.

set /p TOKEN="Entrez votre Personal Access Token : "

if "%TOKEN%"=="" (
    echo Erreur : Token vide
    pause
    exit /b 1
)

echo.
echo Configuration du remote avec token...
git remote remove origin 2>nul
git remote add origin https://nextjsreact:%TOKEN%@github.com/nextjsreact/synchronisation_airbnb.git

echo.
echo Push vers GitHub...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   PUSH REUSSI !
    echo ========================================
    echo.
    echo Nettoyage du token de l'URL...
    git remote remove origin
    git remote add origin https://github.com/nextjsreact/synchronisation_airbnb.git
    echo Token supprime de la config Git
) else (
    echo.
    echo Erreur lors du push
)

pause
```

---

## ✅ Vérification

Après avoir réussi le push, vérifiez :

1. Allez sur : https://github.com/nextjsreact/synchronisation_airbnb
2. Vérifiez que tous les fichiers sont présents
3. **IMPORTANT** : Vérifiez que `.env` n'est PAS visible
4. Vérifiez que le README s'affiche correctement

---

## 🔒 Sécurité

**⚠️ IMPORTANT** :

- Ne partagez JAMAIS votre Personal Access Token
- Ne commitez JAMAIS le token dans Git
- Utilisez des tokens avec expiration
- Révoquezle token si compromis : https://github.com/settings/tokens

---

## 🆘 Toujours des Problèmes ?

### Vérifier le Compte Actuel

```bash
# Voir quel compte est configuré
git config user.name
git config user.email

# Changer si nécessaire
git config user.name "nextjsreact"
git config user.email "email@example.com"
```

### Vérifier les Credentials Stockées

```bash
# Windows Credential Manager
control /name Microsoft.CredentialManager

# Cherchez "git:https://github.com" et supprimez
```

### Réessayer avec Verbose

```bash
# Voir plus de détails sur l'erreur
GIT_CURL_VERBOSE=1 git push -u origin main
```

---

**Dernière mise à jour** : 30 Mai 2026
