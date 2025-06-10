#!/bin/bash
# ==============================================
# Script de Lancement LUXA v1.1
# ==============================================
# Assistant Vocal Intelligent - SuperWhisper_V6

set -euo pipefail  # Arrêt strict sur erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Bannière Luxa
echo -e "${CYAN}"
echo "  ██╗     ██╗   ██╗██╗  ██╗ █████╗ "
echo "  ██║     ██║   ██║╚██╗██╔╝██╔══██╗"
echo "  ██║     ██║   ██║ ╚███╔╝ ███████║"
echo "  ██║     ██║   ██║ ██╔██╗ ██╔══██║"
echo "  ███████╗╚██████╔╝██╔╝ ██╗██║  ██║"
echo "  ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝"
echo -e "${NC}"
echo -e "${BLUE}🎤 Assistant Vocal Intelligent v1.1${NC}"
echo -e "${YELLOW}SuperWhisper_V6 - STT | LLM | TTS${NC}"
echo "=============================================="

# Configuration par défaut
DEFAULT_GPU_MAP="3090:0,4060:1"
DEFAULT_MODE="cli"
PYTHON_CMD="python"

# Fonctions utilitaires
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --validate          Lance la validation Phase 0"
    echo "  --mode MODE         Mode d'interface (cli|web|api) [défaut: cli]"
    echo "  --gpu-map MAP       Mapping GPU personnalisé [défaut: $DEFAULT_GPU_MAP]"
    echo "  --python CMD        Commande Python à utiliser [défaut: python]"
    echo "  --port PORT         Port pour mode web/api [défaut: 8080]"
    echo "  --debug             Active le mode debug"
    echo "  --benchmark         Lance uniquement les benchmarks"
    echo "  --help              Affiche cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 --validate                    # Validation système"
    echo "  $0 --mode web --port 8080        # Interface web"
    echo "  $0 --gpu-map \"4090:0,3060:1\"     # Mapping GPU personnalisé"
    echo "  $0 --benchmark                   # Benchmarks uniquement"
}

# Parse des arguments
VALIDATE=false
MODE="$DEFAULT_MODE"
GPU_MAP="$DEFAULT_GPU_MAP"
PORT=8080
DEBUG=false
BENCHMARK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --validate)
            VALIDATE=true
            shift
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --gpu-map)
            GPU_MAP="$2"
            shift 2
            ;;
        --python)
            PYTHON_CMD="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --benchmark)
            BENCHMARK=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Option inconnue: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Configuration des variables d'environnement
export LUXA_GPU_MAP="${GPU_MAP}"
export LUXA_MODE="${MODE}"
export LUXA_PORT="${PORT}"

if [ "$DEBUG" = true ]; then
    export LUXA_LOG_LEVEL="DEBUG"
    log_info "Mode debug activé"
fi

log_info "Configuration GPU: $GPU_MAP"
log_info "Mode d'interface: $MODE"

# Vérifications préliminaires
check_python() {
    log_info "Vérification Python..."
    
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        log_error "Python non trouvé: $PYTHON_CMD"
        exit 1
    fi
    
    # Vérifier version Python
    python_version=$("$PYTHON_CMD" --version 2>&1 | cut -d' ' -f2)
    log_info "Python version: $python_version"
    
    # Vérifier que c'est Python 3.8+
    if ! "$PYTHON_CMD" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        log_error "Python 3.8+ requis, trouvé: $python_version"
        exit 1
    fi
}

check_cuda() {
    log_info "Vérification CUDA..."
    
    if ! "$PYTHON_CMD" -c "import torch; print('CUDA disponible:', torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then
        log_warn "CUDA non disponible - fonctionnement en mode CPU uniquement"
        return 1
    fi
    
    # Afficher infos GPU
    log_info "GPUs détectés:"
    "$PYTHON_CMD" -c "
import torch
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        free, total = torch.cuda.mem_get_info(i)
        print(f'  GPU {i}: {props.name} ({free//1024**3}/{total//1024**3}GB libre)')
else:
    print('  Aucun GPU CUDA détecté')
" 2>/dev/null
}

check_dependencies() {
    log_info "Vérification des dépendances..."
    
    # Dépendances critiques
    critical_deps=(
        "torch"
        "numpy" 
        "yaml"
        "psutil"
    )
    
    # Dépendances optionnelles
    optional_deps=(
        "faster_whisper"
        "whisper"
        "prometheus_client"
    )
    
    missing_critical=false
    
    for dep in "${critical_deps[@]}"; do
        if ! "$PYTHON_CMD" -c "import $dep" 2>/dev/null; then
            log_error "Dépendance critique manquante: $dep"
            missing_critical=true
        fi
    done
    
    if [ "$missing_critical" = true ]; then
        log_error "Installation des dépendances requise:"
        log_error "pip install torch numpy pyyaml psutil"
        exit 1
    fi
    
    # Vérifier dépendances optionnelles
    for dep in "${optional_deps[@]}"; do
        if ! "$PYTHON_CMD" -c "import $dep" 2>/dev/null; then
            log_warn "Dépendance optionnelle manquante: $dep"
        fi
    done
    
    log_info "Dépendances critiques OK"
}

check_structure() {
    log_info "Vérification structure projet..."
    
    required_dirs=(
        "STT"
        "LLM" 
        "TTS"
        "Orchestrator"
        "utils"
        "monitoring"
        "config"
        "benchmarks"
    )
    
    missing_dirs=false
    
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            log_error "Répertoire manquant: $dir"
            missing_dirs=true
        fi
    done
    
    if [ "$missing_dirs" = true ]; then
        log_error "Structure de projet incomplète"
        exit 1
    fi
    
    log_info "Structure projet OK"
}

# Phase 0 - Validation système
run_phase0_validation() {
    log_info "🧪 Phase 0 - Validation système"
    
    if [ ! -f "benchmarks/phase0_validation.py" ]; then
        log_error "Script de validation Phase 0 introuvable"
        exit 1
    fi
    
    if ! "$PYTHON_CMD" benchmarks/phase0_validation.py; then
        log_error "Validation Phase 0 échouée"
        exit 1
    fi
    
    log_info "✅ Validation Phase 0 réussie"
}

# Benchmarks
run_benchmarks() {
    log_info "📊 Lancement des benchmarks..."
    
    # Benchmark STT
    if [ -f "benchmarks/benchmark_stt_realistic.py" ]; then
        log_info "🎤 Benchmark STT réaliste..."
        "$PYTHON_CMD" benchmarks/benchmark_stt_realistic.py
    fi
    
    # Autres benchmarks peuvent être ajoutés ici
    log_info "✅ Benchmarks terminés"
}

# Lancement principal
launch_luxa() {
    log_info "🚀 Lancement LUXA..."
    
    case "$MODE" in
        cli)
            log_info "Mode CLI - Interface en ligne de commande"
            "$PYTHON_CMD" run_assistant.py --mode cli
            ;;
        web)
            log_info "Mode WEB - Interface web sur port $PORT"
            "$PYTHON_CMD" run_assistant.py --mode web --port "$PORT"
            ;;
        api)
            log_info "Mode API - API REST sur port $PORT" 
            "$PYTHON_CMD" run_assistant.py --mode api --port "$PORT"
            ;;
        *)
            log_error "Mode invalide: $MODE (cli|web|api)"
            exit 1
            ;;
    esac
}

# Nettoyage à la sortie
cleanup() {
    log_info "🧹 Nettoyage..."
    # Arrêter processus en arrière-plan si nécessaire
    # Nettoyer fichiers temporaires
}

trap cleanup EXIT

# Exécution principale
main() {
    log_info "Démarrage LUXA v1.1..."
    
    # Vérifications système
    check_python
    check_cuda
    check_dependencies
    check_structure
    
    # Validation Phase 0 si demandée
    if [ "$VALIDATE" = true ]; then
        run_phase0_validation
    fi
    
    # Benchmarks uniquement si demandé
    if [ "$BENCHMARK" = true ]; then
        run_benchmarks
        exit 0
    fi
    
    # Validation minimale automatique
    if [ ! -f ".luxa_validated" ] || [ "$VALIDATE" = true ]; then
        log_info "Validation automatique..."
        run_phase0_validation
        touch .luxa_validated
    fi
    
    # Lancement principal
    launch_luxa
}

# Point d'entrée
main "$@" 