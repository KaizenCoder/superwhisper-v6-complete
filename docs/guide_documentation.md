# Guide d'Utilisation - Documentation Obligatoire

## 🎯 Objectif
Système de documentation obligatoire pour tracer toutes les analyses et implémentations sur le projet Luxa (SuperWhisper_V6).

---

## 🚀 Utilisation Rapide

### 📝 Créer une nouvelle entrée
```bash
cd luxa
python scripts/doc-check.py --update
```

### 📊 Vérifier le statut
```bash
cd luxa  
python scripts/doc-check.py
```

### 📋 TaskManager - Tâche #11
```bash
# Voir la tâche principale
task-master show 11

# Marquer une sous-tâche terminée
task-master set-status --id=11.X --status=done
```

---

## 📁 Structure du Système

```
docs/
├── journal_developpement.md     # Journal principal
└── guide_documentation.md       # Ce guide

luxa/scripts/
├── doc-check.py                 # Script d'aide rapide
└── documentation_reminder.py    # Vérifications automatiques

.git/hooks/
└── pre-commit                   # Hook Git (non-fonctionnel Windows)

TaskManager:
└── Tâche #11: Documentation obligatoire (4 sous-tâches)
```

---

## 📋 Template d'Entrée Standard

```markdown
### YYYY-MM-DD - [Titre de la session]
**Contexte**: [Description du problème/objectif]

**Analyse**:
- [Point d'analyse 1]
- [Point d'analyse 2]

**Décisions techniques**:
- [Décision 1 avec justification]
- [Décision 2 avec justification]

**Implémentation**:
- [x] [Tâche complétée]
- [ ] [Tâche en cours]

**Tests/Validation**:
- [Résultat test 1]
- [Résultat test 2]

**Notes importantes**:
- [Note critique 1]
- [Note critique 2]

**Prochaines étapes**:
- [ ] [Action suivante]
- [ ] [Action suivante]
```

---

## 🔄 Workflow Recommandé

1. **Début de session**: `python luxa/scripts/doc-check.py` pour vérifier le statut
2. **Développement**: Travailler sur les fonctionnalités
3. **Fin de session**: `python luxa/scripts/doc-check.py --update` pour documenter
4. **Compléter**: Éditer `docs/journal_developpement.md` avec le template
5. **Synchroniser**: Commiter dans Git
6. **TaskManager**: Marquer les sous-tâches appropriées comme terminées

---

## 📊 Tâches TaskManager

| ID   | Titre                                      | Statut   | Description |
|------|--------------------------------------------| ---------|-------------|
| 11   | Maintenir un journal de développement     | pending  | Tâche principale |
| 11.1 | Créer le système de documentation         | ✅ done  | Système mis en place |
| 11.2 | Synchroniser avec Git                     | ✅ done  | Git intégré |
| 11.3 | Maintenir le système quotidien            | pending  | Usage quotidien |
| 11.4 | Valider et améliorer le système           | pending  | Optimisations |

---

## 🔧 Scripts Disponibles

### `doc-check.py`
```bash
# Vérifier le statut
python luxa/scripts/doc-check.py

# Créer une nouvelle entrée
python luxa/scripts/doc-check.py --update
```

### `documentation_reminder.py`
```bash
# Vérification complète (utilisé par hook Git)
python luxa/scripts/documentation_reminder.py
```

---

## 🚨 Rappels Automatiques

- **Hook Git**: Vérifie avant chaque commit (à améliorer sur Windows)
- **Scripts Python**: Vérifications on-demand disponibles
- **TaskManager**: Tâche priorité haute pour workflow obligatoire

---

## 📈 Métriques & Suivi

Le journal inclut des métriques de développement automatiques :
- Modules implémentés par catégorie
- Couverture fonctionnelle par phase
- Progression des tâches avec pourcentages

---

## 💡 Conseils d'Utilisation

1. **Fréquence**: Documenter à chaque session de développement significative
2. **Détail**: Inclure contexte, décisions techniques et justifications
3. **Tests**: Toujours noter les résultats de validation
4. **Git**: Synchroniser régulièrement pour traçabilité
5. **TaskManager**: Utiliser les sous-tâches pour suivi précis

---

## 🐛 Dépannage

### Script doc-check.py ne trouve pas le projet
- Vérifier que vous êtes dans le bon répertoire
- S'assurer que `.taskmaster/` existe dans la racine

### TaskManager non disponible  
- Vérifier l'installation: `task-master --version`
- S'assurer d'être dans le bon répertoire de projet

### Hook Git non-fonctionnel
- Problème connu sur Windows avec permissions
- Utiliser les scripts Python manuellement

---

*Ce système garantit la traçabilité complète du développement Luxa avec intégration TaskManager.* 