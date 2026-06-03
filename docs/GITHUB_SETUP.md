# 📦 Guide de Configuration GitHub

Ce guide vous aide à créer un repository GitHub et y pousser votre projet.

---

## 🚀 Étape 1 : Vérifier que Git est Installé

```bash
git --version
```

Si Git n'est pas installé, téléchargez-le depuis : https://git-scm.com/

---

## 📝 Étape 2 : Initialiser Git Localement

```bash
# Aller dans le dossier du projet
cd d:\Airbnb_transfer_v2

# Initialiser Git
git init

# Configurer votre identité (si pas déjà fait)
git config --global user.name "Votre Nom"
git config --global user.email "votre.email@example.com"

# Vérifier que .gitignore est bien présent
type .gitignore
```

---

## 🔒 Étape 3 : Vérifier les Fichiers Sensibles

**⚠️ IMPORTANT** : Avant de commiter, vérifiez que ces fichiers sont bien ignorés :

```bash
# Ces fichiers NE DOIVENT PAS être dans Git
git status | findstr ".env"
git status | findstr "airbnb_session.json"
```

Si vous voyez ces fichiers dans `git status`, c'est qu'ils ne sont PAS ignorés !

**Solution** :
```bash
# Vérifier que .gitignore contient bien :
# .env
# output/airbnb_session.json
```

---

## 📦 Étape 4 : Créer le Premier Commit

```bash
# Ajouter tous les fichiers (sauf ceux dans .gitignore)
git add .

# Vérifier ce qui va être commité
git status

# Créer le premier commit
git commit -m "Initial commit: Airbnb synchronization system v2.0"
```

---

## 🌐 Étape 5 : Créer le Repository sur GitHub

### Option A : Via l'Interface Web (Recommandé)

1. Allez sur https://github.com
2. Cliquez sur le bouton **"+"** en haut à droite
3. Sélectionnez **"New repository"**
4. Remplissez les informations :
   - **Repository name** : `airbnb-sync` (ou autre nom)
   - **Description** : `Système automatique de synchronisation Airbnb vers Supabase`
   - **Visibility** : 
     - ✅ **Private** (recommandé pour un projet avec credentials)
     - ⚠️ **Public** (seulement si vous êtes sûr qu'aucun secret n'est commité)
   - ❌ **Ne pas** cocher "Initialize with README" (vous en avez déjà un)
   - ❌ **Ne pas** ajouter .gitignore (vous en avez déjà un)
   - ✅ Choisir **MIT License** (optionnel)
5. Cliquez sur **"Create repository"**

### Option B : Via GitHub CLI

```bash
# Installer GitHub CLI : https://cli.github.com/
gh auth login
gh repo create airbnb-sync --private --source=. --remote=origin
```

---

## 🔗 Étape 6 : Lier le Repository Local à GitHub

Après avoir créé le repository sur GitHub, copiez l'URL qui s'affiche.

```bash
# Ajouter le remote (remplacez YOUR_USERNAME par votre nom d'utilisateur)
git remote add origin https://github.com/YOUR_USERNAME/airbnb-sync.git

# Vérifier que le remote est bien ajouté
git remote -v
```

---

## 🚀 Étape 7 : Pousser vers GitHub

```bash
# Renommer la branche principale en 'main' (si nécessaire)
git branch -M main

# Pousser vers GitHub
git push -u origin main
```

**Si vous avez une erreur d'authentification** :

### Windows
```bash
# Utiliser le gestionnaire de credentials Windows
git config --global credential.helper wincred
```

### Ou utiliser un Personal Access Token
1. Allez sur GitHub → Settings → Developer settings → Personal access tokens
2. Générez un nouveau token avec les permissions `repo`
3. Utilisez ce token comme mot de passe lors du push

---

## ✅ Étape 8 : Vérifier sur GitHub

1. Allez sur https://github.com/YOUR_USERNAME/airbnb-sync
2. Vérifiez que tous les fichiers sont bien présents
3. **IMPORTANT** : Vérifiez que `.env` et `output/airbnb_session.json` ne sont PAS visibles

---

## 📝 Étape 9 : Ajouter un README Badge (Optionnel)

Ajoutez des badges à votre README pour montrer le statut du projet :

```markdown
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
```

---

## 🔄 Workflow Quotidien

### Après avoir fait des modifications :

```bash
# Voir les fichiers modifiés
git status

# Ajouter les fichiers modifiés
git add .

# Ou ajouter des fichiers spécifiques
git add airbnb_scraper.py ical_watcher.py

# Créer un commit avec un message descriptif
git commit -m "feat: amélioration de la détection des changements iCal"

# Pousser vers GitHub
git push
```

### Types de messages de commit recommandés :

- `feat:` - Nouvelle fonctionnalité
- `fix:` - Correction de bug
- `docs:` - Modification de documentation
- `refactor:` - Refactoring de code
- `test:` - Ajout de tests
- `chore:` - Maintenance (mise à jour dépendances, etc.)

**Exemples** :
```bash
git commit -m "feat: ajout du monitoring automatique"
git commit -m "fix: correction erreur encodage UTF-8"
git commit -m "docs: mise à jour du guide d'installation"
```

---

## 🌿 Branches (Optionnel)

Pour travailler sur des fonctionnalités sans affecter la branche principale :

```bash
# Créer une nouvelle branche
git checkout -b feature/nouvelle-fonctionnalite

# Faire vos modifications...
git add .
git commit -m "feat: nouvelle fonctionnalité"

# Pousser la branche
git push -u origin feature/nouvelle-fonctionnalite

# Créer une Pull Request sur GitHub
# Puis merger dans main via l'interface GitHub
```

---

## 🔒 Sécurité - Checklist Finale

Avant de pousser vers GitHub, vérifiez :

- [ ] Le fichier `.env` est dans `.gitignore`
- [ ] Le fichier `output/airbnb_session.json` est dans `.gitignore`
- [ ] Aucun mot de passe en clair dans le code
- [ ] Le fichier `.env.example` ne contient pas de vraies credentials
- [ ] Les captures d'écran de debug sont ignorées
- [ ] Les logs sont ignorés

**Commande de vérification** :
```bash
# Voir ce qui sera commité
git status

# Voir le contenu exact qui sera commité
git diff --cached
```

---

## 🆘 Problèmes Courants

### Erreur : "remote origin already exists"

```bash
# Supprimer le remote existant
git remote remove origin

# Ajouter le nouveau
git remote add origin https://github.com/YOUR_USERNAME/airbnb-sync.git
```

### Erreur : "failed to push some refs"

```bash
# Récupérer les changements du remote
git pull origin main --rebase

# Puis pousser
git push origin main
```

### J'ai commité .env par erreur !

```bash
# Supprimer du cache Git (mais garder le fichier local)
git rm --cached .env

# Ajouter au .gitignore si pas déjà fait
echo .env >> .gitignore

# Commiter la suppression
git commit -m "fix: remove .env from git"

# Pousser
git push

# ⚠️ IMPORTANT : Si .env était déjà poussé sur GitHub,
# il reste dans l'historique ! Vous devez :
# 1. Changer tous les mots de passe/tokens
# 2. Ou utiliser git filter-branch pour nettoyer l'historique
```

---

## 📚 Ressources

- [Documentation Git](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [GitHub CLI](https://cli.github.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

## 🎉 Félicitations !

Votre projet est maintenant sur GitHub ! 🚀

**Prochaines étapes** :
1. Inviter des collaborateurs (si projet privé)
2. Configurer GitHub Actions pour CI/CD (optionnel)
3. Ajouter des issues pour suivre les bugs/features
4. Créer un Wiki pour la documentation détaillée

---

**Dernière mise à jour** : 30 Mai 2026
