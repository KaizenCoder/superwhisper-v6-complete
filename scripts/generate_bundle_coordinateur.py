#!/usr/bin/env python3
"""
Générateur de Bundle Transmission Coordinateur
==============================================

Ce script génère automatiquement un bundle complet de documentation
pour la transmission aux coordinateurs du projet.

Usage:
    python scripts/generate_bundle_coordinateur.py [--timestamp] [--zip]
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import zipfile

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_status(message, status="INFO"):
    symbols = {"INFO": "ℹ️", "OK": "✅", "ERROR": "❌", "WARNING": "⚠️"}
    print(f"{symbols.get(status, 'ℹ️')} {message}")

def get_project_stats():
    """Récupère les statistiques du projet"""
    stats = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date_iso": datetime.now().strftime("%Y%m%d_%H%M"),
        "files_count": 0,
        "lines_count": 0,
        "modules_count": 0
    }
    
    # Compter les fichiers Python
    python_files = list(Path(".").rglob("*.py"))
    stats["files_count"] = len(python_files)
    
    # Compter les lignes de code
    total_lines = 0
    for file in python_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                total_lines += len(f.readlines())
        except:
            pass
    stats["lines_count"] = total_lines
    
    # Compter les modules
    modules = ["STT", "LLM", "TTS", "Orchestrator"]
    stats["modules_count"] = sum(1 for m in modules if Path(m).exists())
    
    return stats

def update_timestamps_in_files(transmission_dir):
    """Met à jour les timestamps dans tous les fichiers"""
    print_status("Mise à jour des timestamps...")
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md_files = list(Path(transmission_dir).glob("*.md"))
    
    for file_path in md_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remplacer les timestamps
            content = content.replace("2024-01-XX", current_time.split()[0])
            content = content.replace("**Dernière Mise à Jour** : 2024-01-XX", 
                                    f"**Dernière Mise à Jour** : {current_time}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print_status(f"Timestamps mis à jour dans {file_path.name}", "OK")
        except Exception as e:
            print_status(f"Erreur mise à jour {file_path.name}: {e}", "ERROR")

def copy_latest_journal():
    """Copie la dernière version du journal de développement"""
    print_status("Copie du journal de développement...")
    
    source = Path("docs/journal_developpement.md")
    target = Path("Transmission_coordinateur/JOURNAL-DEVELOPPEMENT.md")
    
    if source.exists():
        shutil.copy2(source, target)
        print_status("Journal de développement copié", "OK")
    else:
        print_status("Journal de développement non trouvé", "WARNING")

def update_readme_navigation(transmission_dir):
    """Met à jour le README avec la navigation complète"""
    print_status("Mise à jour navigation README...")
    
    stats = get_project_stats()
    
    readme_content = f"""# 🚀 SuperWhisper V6 - Transmission Coordinateurs

**Dernière Mise à Jour** : {stats['timestamp']}  
**Bundle Généré** : {stats['date_iso']}  
**Version** : LUXA v1.1

---

## 📋 NAVIGATION COORDINATEURS

| Document | Description | Dernière MAJ |
|----------|-------------|--------------|
| [📊 STATUS.md](STATUS.md) | État d'avancement détaillé | {stats['timestamp'].split()[0]} |
| [💻 CODE-SOURCE.md](CODE-SOURCE.md) | Code source intégral | {stats['timestamp'].split()[0]} |
| [🏗️ ARCHITECTURE.md](ARCHITECTURE.md) | Architecture technique | {stats['timestamp'].split()[0]} |
| [📈 PROGRESSION.md](PROGRESSION.md) | Suivi progression phases | {stats['timestamp'].split()[0]} |
| [📝 JOURNAL-DEVELOPPEMENT.md](JOURNAL-DEVELOPPEMENT.md) | Journal complet développement | {stats['timestamp'].split()[0]} |

---

## 🎯 RÉSUMÉ EXÉCUTIF

**SuperWhisper V6 (LUXA)** - Assistant vocal intelligent modulaire

### 📊 Métriques Actuelles
- **Fichiers Python** : {stats['files_count']} fichiers
- **Lignes de Code** : {stats['lines_count']:,} lignes
- **Modules Implémentés** : {stats['modules_count']}/4
- **Phase Actuelle** : Phase 1 - Implémentation Modules

### 🏗️ Architecture
```
STT (Speech-to-Text) → LLM (Language Model) → TTS (Text-to-Speech)
                              ↓
                        ORCHESTRATOR
                     (Coordination & Monitoring)
```

### 🎯 Objectifs Performance
- **Latence Pipeline** : < 2s end-to-end
- **Précision STT** : > 95%
- **Qualité TTS** : Voix naturelle
- **Disponibilité** : 99.9%

---

## 📈 PROGRESSION GLOBALE

```
Phase 0: INIT     ████████████████████████████████ 100% ✅
Phase 1: MODULES  ████████░░░░░░░░░░░░░░░░░░░░░░░░  25% 🔄
Phase 2: INTÉGR   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0% ⏳
Phase 3: OPTIM    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0% ⏳
```

---

## 🚨 POINTS D'ATTENTION

### ✅ Points Positifs
- Structure modulaire solide
- Documentation complète
- Tests Phase 0 validés
- Timeline respectée

### ⚠️ Surveillances
- Performance GPU (STT)
- Intégration Ollama (LLM)
- Choix engine TTS
- Coordination pipeline

---

## 📞 CONTACTS

**Équipe Développement** : SuperWhisper Team  
**Repository** : https://github.com/KaizenCoder/superwhisper-v6-complete  
**Fréquence Reporting** : Quotidienne  
**Prochain Update** : {(datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + 
                       timedelta(days=1)).strftime("%Y-%m-%d %H:%M")}

---

## 📦 CONTENU DU BUNDLE

Ce bundle contient :
- 📊 État d'avancement complet
- 💻 Code source intégral ({stats['lines_count']:,} lignes)
- 🏗️ Architecture technique détaillée
- 📈 Progression et métriques
- 📝 Journal de développement complet
- 🔧 Procédures et guidelines

**Bundle généré automatiquement le {stats['timestamp']}**
"""
    
    readme_path = Path(transmission_dir) / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print_status("README navigation mis à jour", "OK")

def create_zip_bundle(transmission_dir, timestamp):
    """Crée un fichier ZIP du bundle"""
    print_status("Création du bundle ZIP...")
    
    zip_name = f"Transmission_Coordinateur_{timestamp}.zip"
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in Path(transmission_dir).rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(Path(transmission_dir).parent)
                zipf.write(file_path, arcname)
    
    print_status(f"Bundle ZIP créé: {zip_name}", "OK")
    return zip_name

def validate_bundle(transmission_dir):
    """Valide que tous les fichiers requis sont présents"""
    print_status("Validation du bundle...")
    
    required_files = [
        "README.md",
        "STATUS.md", 
        "CODE-SOURCE.md",
        "ARCHITECTURE.md",
        "PROGRESSION.md",
        "JOURNAL-DEVELOPPEMENT.md"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = Path(transmission_dir) / file
        if not file_path.exists():
            missing_files.append(file)
        else:
            size_kb = file_path.stat().st_size / 1024
            print_status(f"{file}: {size_kb:.1f} KB", "OK")
    
    if missing_files:
        print_status(f"Fichiers manquants: {missing_files}", "ERROR")
        return False
    
    print_status("Bundle validé avec succès", "OK")
    return True

def main():
    """Fonction principale"""
    import argparse
    from datetime import timedelta
    
    parser = argparse.ArgumentParser(description="Générateur Bundle Coordinateur")
    parser.add_argument("--timestamp", action="store_true", 
                       help="Ajouter timestamp au nom du répertoire")
    parser.add_argument("--zip", action="store_true",
                       help="Créer un fichier ZIP du bundle")
    parser.add_argument("--validate-only", action="store_true",
                       help="Seulement valider le bundle existant")
    
    args = parser.parse_args()
    
    print_header("GÉNÉRATEUR BUNDLE TRANSMISSION COORDINATEUR")
    
    transmission_dir = "Transmission_coordinateur"
    
    if args.timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        transmission_dir = f"Transmission_coordinateur_{timestamp}"
    
    if args.validate_only:
        if validate_bundle("Transmission_coordinateur"):
            print_status("✅ Bundle prêt pour transmission", "OK")
            sys.exit(0)
        else:
            print_status("❌ Bundle invalide", "ERROR")
            sys.exit(1)
    
    # Créer le répertoire si nécessaire
    Path(transmission_dir).mkdir(exist_ok=True)
    
    # Étapes de génération
    print_status("Démarrage génération bundle...")
    
    # 1. Copier le journal
    copy_latest_journal()
    
    # 2. Mettre à jour les timestamps
    update_timestamps_in_files(transmission_dir)
    
    # 3. Mettre à jour la navigation
    update_readme_navigation(transmission_dir)
    
    # 4. Valider le bundle
    if not validate_bundle(transmission_dir):
        sys.exit(1)
    
    # 5. Créer ZIP si demandé
    if args.zip:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        zip_file = create_zip_bundle(transmission_dir, timestamp)
        print_status(f"Bundle ZIP prêt: {zip_file}", "OK")
    
    print_header("BUNDLE TRANSMISSION TERMINÉ")
    print_status("🎯 Bundle prêt pour envoi aux coordinateurs", "OK")
    print_status(f"📁 Répertoire: {transmission_dir}", "INFO")
    
    if args.zip:
        print_status(f"📦 Archive: {zip_file}", "INFO")
    
    print_status("💡 Utilisez --zip pour créer une archive", "INFO")

if __name__ == "__main__":
    main() 