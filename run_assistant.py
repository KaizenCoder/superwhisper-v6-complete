#!/usr/bin/env python3
"""
Luxa - SuperWhisper_V6 Assistant v1.1
======================================

Assistant vocal intelligent avec pipeline STT → LLM → TTS
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.append(str(Path(__file__).parent))

from Orchestrator.master_handler_robust import RobustMasterHandler
import numpy as np

def parse_arguments():
    """Parse les arguments en ligne de commande"""
    parser = argparse.ArgumentParser(
        description="Luxa - Assistant Vocal Intelligent v1.1"
    )
    
    parser.add_argument(
        "--mode", 
        choices=["cli", "web", "api"],
        default="cli",
        help="Mode d'interface (défaut: cli)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port pour modes web/api (défaut: 8080)"
    )
    
    parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="Fichier de configuration (défaut: config/settings.yaml)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Active le mode debug"
    )
    
    return parser.parse_args()

async def run_cli_mode(handler):
    """Mode CLI interactif"""
    print("\n🎤 Mode CLI - Assistant Vocal")
    print("Commands: 'quit' pour quitter, 'status' pour le statut")
    print("=" * 50)
    
    try:
        while True:
            try:
                user_input = input("\n🗣️ Parlez (ou tapez): ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Au revoir!")
                    break
                    
                elif user_input.lower() == 'status':
                    health = handler.get_health_status()
                    print(f"\n📊 Statut: {health['status']}")
                    print(f"Requêtes traitées: {health['performance']['requests_processed']}")
                    print(f"Latence moyenne: {health['performance']['avg_latency_ms']:.1f}ms")
                    continue
                    
                elif user_input.lower() == 'test':
                    # Test avec audio synthétique
                    print("🧪 Test avec audio synthétique...")
                    test_audio = np.random.randn(16000).astype(np.float32) * 0.1
                    result = await handler.process_audio_safe(test_audio)
                    
                    print(f"✅ Résultat: {result['text']}")
                    print(f"⏱️ Latence: {result['latency_ms']:.1f}ms")
                    print(f"🎯 Succès: {result['success']}")
                    continue
                    
                if not user_input:
                    continue
                    
                print("📝 Traitement en cours...")
                
                # Pour l'instant, simuler avec du texte
                # Dans une vraie implémentation, on capturerait l'audio
                result = {
                    "success": True,
                    "text": f"Vous avez dit: {user_input}",
                    "latency_ms": 50
                }
                
                print(f"🎯 Réponse: {result['text']}")
                
            except KeyboardInterrupt:
                print("\n👋 Arrêt demandé...")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
                
    except Exception as e:
        print(f"❌ Erreur CLI: {e}")

async def run_web_mode(handler, port):
    """Mode web (placeholder)"""
    print(f"🌐 Mode Web sur port {port}")
    print("⚠️ Interface web non implémentée dans cette version")
    
    # Placeholder pour serveur web
    print("Appuyez sur Ctrl+C pour arrêter...")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Serveur web arrêté")

async def run_api_mode(handler, port):
    """Mode API REST (placeholder)"""
    print(f"🔌 Mode API REST sur port {port}")
    print("⚠️ API REST non implémentée dans cette version")
    
    # Placeholder pour API REST
    print("Appuyez sur Ctrl+C pour arrêter...")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("🛑 API REST arrêtée")

def print_banner():
    """Affiche la bannière Luxa v1.1"""
    banner = """
    ██╗     ██╗   ██╗██╗  ██╗ █████╗ 
    ██║     ██║   ██║╚██╗██╔╝██╔══██╗
    ██║     ██║   ██║ ╚███╔╝ ███████║
    ██║     ██║   ██║ ██╔██╗ ██╔══██║
    ███████╗╚██████╔╝██╔╝ ██╗██║  ██║
    ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
    
    🎤 Assistant Vocal Intelligent v1.1
    SuperWhisper_V6 - STT | LLM | TTS
    """
    print(banner)

async def main():
    """Point d'entrée principal"""
    
    # Bannière
    print_banner()
    print("🚀 LUXA v1.1 - Démarrage...")
    print("=" * 50)
    
    # Arguments
    args = parse_arguments()
    
    # Configuration debug
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        print("🐛 Mode debug activé")
    
    # Variables d'environnement
    gpu_map = os.getenv("LUXA_GPU_MAP", "3090:0,4060:1")
    print(f"🎮 Configuration GPU: {gpu_map}")
    
    try:
        # Initialiser le gestionnaire principal
        print("🔧 Initialisation du gestionnaire principal...")
        handler = RobustMasterHandler(config_path=args.config)
        await handler.initialize()
        
        print("✅ Luxa initialisé avec succès!")
        
        # Lancer le mode approprié
        if args.mode == "cli":
            await run_cli_mode(handler)
        elif args.mode == "web":
            await run_web_mode(handler, args.port)
        elif args.mode == "api":
            await run_api_mode(handler, args.port)
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)
    finally:
        print("🧹 Nettoyage en cours...")

if __name__ == "__main__":
    asyncio.run(main()) 