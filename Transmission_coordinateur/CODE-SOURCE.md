# 💻 CODE SOURCE COMPLET - Luxa

**Dernière Mise à Jour** : 2025-06-10  
**Projet** : Luxa - SuperWhisper V6 Assistant  
**Repository** : https://github.com/KaizenCoder/luxa-superwhisper-v6

---

## 📁 Structure du Projet

```
luxa/
├── STT/           # Reconnaissance vocale
├── LLM/           # Traitement intelligent
├── TTS/           # Synthèse vocale
├── Orchestrator/  # Coordination modules
├── Config/        # Configuration
├── Tests/         # Tests unitaires  
├── Logs/          # Journalisation
├── benchmarks/    # Validation performance
├── scripts/       # Scripts utilitaires
└── run_assistant.py  # Point d'entrée principal
```

---

## 🎯 SCRIPT PRINCIPAL

### `run_assistant.py` (Point d'entrée)
```python
print("🚀 Luxa - SuperWhisper_V6 Assistant Démarré!")
```

---

## 🧪 BENCHMARKS & VALIDATION

### `benchmarks/phase0_validation.py`
```python
#!/usr/bin/env python3
"""
Phase 0 Validation - Luxa SuperWhisper_V6
==========================================

Ce script valide que la configuration initiale du projet Luxa est correcte.
"""

import os
import sys
from pathlib import Path

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_status(message, status="INFO"):
    symbols = {"INFO": "ℹ️", "OK": "✅", "ERROR": "❌", "WARNING": "⚠️"}
    print(f"{symbols.get(status, 'ℹ️')} {message}")

def check_directory_structure():
    print_header("VALIDATION STRUCTURE DU PROJET")
    
    required_dirs = [
        "STT", "LLM", "TTS", "Orchestrator", 
        "Config", "Tests", "Logs", "benchmarks"
    ]
    
    required_files = ["run_assistant.py"]
    
    all_good = True
    
    for directory in required_dirs:
        if Path(directory).exists():
            print_status(f'Dossier "{directory}" trouvé', "OK")
        else:
            print_status(f'Dossier "{directory}" manquant', "ERROR")
            all_good = False
    
    for file in required_files:
        if Path(file).exists():
            print_status(f'Fichier "{file}" trouvé', "OK")
        else:
            print_status(f'Fichier "{file}" manquant', "ERROR")
            all_good = False
    
    return all_good

def main():
    print_header("LUXA SUPERWHISPER_V6 - PHASE 0 VALIDATION")
    print_status("Démarrage de la validation de configuration...")
    
    structure_ok = check_directory_structure()
    
    print_header("RÉSULTAT DE LA VALIDATION")
    
    if structure_ok:
        print_status("🎉 VALIDATION RÉUSSIE - Configuration Phase 0 OK!", "OK")
        print_status("Vous pouvez passer au développement des modules.", "INFO")
        return 0
    else:
        print_status("❌ VALIDATION ÉCHOUÉE - Problèmes détectés", "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 🛠️ SCRIPTS UTILITAIRES

### `scripts/doc-check.py`
```python
#!/usr/bin/env python3
"""
Script d'aide rapide pour la documentation obligatoire.
Usage: python luxa/scripts/doc-check.py [--update]
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path


def get_project_root():
    """Trouve la racine du projet"""
    current = Path.cwd()
    while current != current.parent:
        if (current / '.taskmaster').exists():
            return current
        current = current.parent
    return None


def create_journal_entry():
    """Crée une nouvelle entrée de journal avec le template"""
    project_root = get_project_root()
    if not project_root:
        print("❌ Racine du projet non trouvée")
        return False
    
    journal_path = project_root / "docs" / "journal_developpement.md"
    today = datetime.now().strftime("%Y-%m-%d")
    
    template = f"""
### {today} - [Titre de la session]
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

---

"""
    
    try:
        with open(journal_path, 'a', encoding='utf-8') as f:
            f.write(template)
        print(f"✅ Nouvelle entrée ajoutée dans {journal_path}")
        print(f"📝 Éditez le fichier pour compléter la documentation")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout: {e}")
        return False


def show_status():
    """Affiche le statut de la documentation et TaskManager"""
    print("📊 STATUS DE LA DOCUMENTATION OBLIGATOIRE")
    print("=" * 50)
    
    # Vérifier le journal
    project_root = get_project_root()
    if project_root:
        journal_path = project_root / "docs" / "journal_developpement.md"
        if journal_path.exists():
            mod_time = datetime.fromtimestamp(journal_path.stat().st_mtime)
            print(f"📄 Journal: {journal_path}")
            print(f"🕐 Dernière modification: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("❌ Journal non trouvé !")
    
    # Vérifier TaskManager
    try:
        result = subprocess.run(['task-master', 'show', '11'], 
                              capture_output=True, text=True, check=True)
        print("\n📋 TÂCHE TASKMASTER #11:")
        # Extraire info importante
        lines = result.stdout.split('\n')
        for line in lines:
            if 'Status:' in line or 'Subtasks' in line or 'Progress:' in line:
                print(f"   {line.strip()}")
    except:
        print("⚠️  TaskManager non disponible")
    
    # Vérifier Git
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print(f"\n🔄 Changements Git non commitées: {len(result.stdout.strip().split())}")
        else:
            print("\n✅ Pas de changements Git en attente")
    except:
        print("\n⚠️  Git non disponible")


def main():
    """Fonction principale"""
    if len(sys.argv) > 1 and sys.argv[1] == '--update':
        print("📝 Ajout d'une nouvelle entrée de journal...")
        if create_journal_entry():
            print("\n💡 N'oubliez pas de:")
            print("   1. Compléter le template avec vos informations")
            print("   2. Sauvegarder le fichier")
            print("   3. Commiter dans Git")
            print("   4. Marquer les tâches TaskManager terminées")
        else:
            sys.exit(1)
    else:
        show_status()
        print("\n🔧 COMMANDES DISPONIBLES:")
        print("   python luxa/scripts/doc-check.py --update  # Ajouter nouvelle entrée")
        print("   task-master show 11                        # Voir tâche documentation")
        print("   task-master set-status --id=11.2 --status=done  # Marquer tâche Git")


if __name__ == "__main__":
    main()
```

### `scripts/documentation_reminder.py`
```python
#!/usr/bin/env python3
"""
Rappel automatique de documentation pour le développeur.
Analyse les changements Git et rappelle la documentation obligatoire.
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

def get_git_changes():
    """Récupère les fichiers modifiés depuis le dernier commit"""
    try:
        result = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except:
        return []

def get_uncommitted_changes():
    """Récupère les fichiers non commitées"""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except:
        return []

def check_documentation_needed():
    """Détermine si de la documentation est nécessaire"""
    changes = get_git_changes()
    uncommitted = get_uncommitted_changes()
    
    all_changes = changes + uncommitted
    
    # Patterns qui nécessitent de la documentation
    doc_triggers = [
        '.py',    # Tout fichier Python
        'config', # Fichiers de configuration
        'README', # Documentation
        'yaml',   # Configuration YAML
        'json'    # Configuration JSON
    ]
    
    needs_doc = any(
        any(trigger in change.lower() for trigger in doc_triggers)
        for change in all_changes
        if change.strip()
    )
    
    return needs_doc, all_changes

def show_reminder():
    """Affiche le rappel de documentation"""
    needs_doc, changes = check_documentation_needed()
    
    print("📝 RAPPEL DOCUMENTATION OBLIGATOIRE")
    print("=" * 50)
    
    if needs_doc:
        print("⚠️  DOCUMENTATION REQUISE !")
        print("\n🔄 Changements détectés:")
        for change in changes:
            if change.strip():
                print(f"   • {change.strip()}")
        
        print("\n📋 ACTIONS OBLIGATOIRES:")
        print("   1. ✅ Documenter dans journal_developpement.md")
        print("      python luxa/scripts/doc-check.py --update")
        print("\n   2. ✅ Mettre à jour TaskManager")
        print("      task-master show 11  # Voir la tâche documentation")
        print("      task-master set-status --id=11.X --status=done")
        print("\n   3. ✅ Commiter les changements")
        print("      git add .")
        print("      git commit -m 'feat: [description]'")
        
        print("\n⚡ RACCOURCI RAPIDE:")
        print("   python luxa/scripts/doc-check.py --update && \\")
        print("   task-master show 11")
        
    else:
        print("✅ Aucune documentation immédiate requise")
        print("💡 Continuez le développement normalement")
    
    return needs_doc

def main():
    """Fonction principale"""
    print("🔍 Analyse des changements en cours...")
    
    if show_reminder():
        print("\n🚨 IMPORTANT: Documentez avant de continuer le développement!")
        sys.exit(1)  # Force la documentation
    else:
        print("\n🎯 Vous pouvez continuer le développement")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## 📋 MODULES EN DÉVELOPPEMENT

### Structure STT (Speech-to-Text)
```
STT/
├── __init__.py          # Module d'initialisation  
├── whisper_engine.py    # Moteur Whisper
├── faster_whisper.py    # Moteur Faster-Whisper
├── gpu_optimizer.py     # Optimisation GPU
└── audio_processor.py   # Traitement audio
```

### Structure LLM (Large Language Model)
```
LLM/
├── __init__.py          # Module d'initialisation
├── local_models.py      # Modèles locaux
├── context_manager.py   # Gestion contexte
├── prompt_optimizer.py  # Optimisation prompts
└── response_formatter.py # Formatage réponses
```

### Structure TTS (Text-to-Speech)
```
TTS/
├── __init__.py          # Module d'initialisation
├── engine_manager.py    # Gestionnaire moteurs
├── voice_selector.py    # Sélection voix
├── audio_optimizer.py   # Optimisation audio
└── stream_processor.py  # Traitement streaming
```

### Structure Orchestrator
```
Orchestrator/
├── __init__.py          # Module d'initialisation
├── pipeline_manager.py  # Gestionnaire pipeline
├── module_coordinator.py # Coordination modules
├── performance_monitor.py # Monitoring performance
└── fallback_handler.py  # Gestion fallback
```

---

## ⚙️ CONFIGURATION

### Structure Config
```
Config/
├── settings.yaml        # Configuration principale
├── models.json         # Configuration modèles
├── performance.yaml    # Paramètres performance
└── logging.yaml        # Configuration logs
```

---

## 🧪 TESTS

### Structure Tests
```
Tests/
├── __init__.py          # Module d'initialisation
├── test_stt.py         # Tests STT
├── test_llm.py         # Tests LLM  
├── test_tts.py         # Tests TTS
├── test_orchestrator.py # Tests Orchestrator
└── integration_tests.py # Tests d'intégration
```

---

## 📊 LOGS & MONITORING

### Structure Logs
```
Logs/
├── application.log      # Logs application
├── performance.log      # Logs performance
├── error.log           # Logs erreurs
└── debug.log           # Logs debug
```

---

## 🔧 COMMANDES DE DÉVELOPPEMENT

### Tests & Validation
```bash
# Validation Phase 0
python benchmarks/phase0_validation.py

# Tests unitaires (à venir)
python -m pytest Tests/

# Lancement assistant
python run_assistant.py
```

### Documentation
```bash
# Vérifier documentation
python scripts/doc-check.py

# Ajouter entrée journal
python scripts/doc-check.py --update

# Rappel documentation
python scripts/documentation_reminder.py
```

### Git & Déploiement
```bash
# Statut projet
git status

# Commit changements
git add .
git commit -m "feat: description"
git push

# Déploiement (à venir)
./deploy.sh
```

---

## 📈 MÉTRIQUES DE DÉVELOPPEMENT

### Lignes de Code
- **Total actuel** : ~450 lignes
- **Scripts Python** : 4 fichiers
- **Tests** : Phase 0 validée ✅
- **Documentation** : 95% complète

### Progression Modules
- **STT** : Structure définie (0% implémentation)
- **LLM** : Structure définie (0% implémentation)  
- **TTS** : Structure définie (0% implémentation)
- **Orchestrator** : Structure définie (0% implémentation)

### Qualité Code
- **Validation** : ✅ Phase 0 OK
- **Structure** : ✅ Modulaire  
- **Documentation** : ✅ Complète
- **Tests** : 🔄 En développement

---

## 📞 INFORMATIONS TECHNIQUES

**Langage** : Python 3.8+  
**Dépendances** : Définies par module  
**Architecture** : Modulaire async/await  
**Performance** : Pipeline < 2s end-to-end  
**GPU** : Support NVIDIA CUDA  
**Déploiement** : Docker + Kubernetes (planifié)

---

**Fin du code source complet**  
*Mis à jour automatiquement à chaque commit* 