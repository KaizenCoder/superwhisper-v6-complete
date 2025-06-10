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
import yaml
from STT.stt_handler import STTHandler
from LLM.llm_handler import LLMHandler
from TTS.tts_handler import TTSHandler

# Ajouter le répertoire courant au PYTHONPATH pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

def main():
    """Fonction principale pour exécuter la boucle de l'assistant."""
    print("🚀 Démarrage de l'assistant vocal LUXA (MVP P0)...")

    # 1. Charger la configuration
    try:
        with open("Config/mvp_settings.yaml", 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ ERREUR: Le fichier 'Config/mvp_settings.yaml' est introuvable.")
        return

    # 2. Initialiser les modules
    try:
        print("🔧 Initialisation des modules...")
        stt_handler = STTHandler(config['stt'])
        llm_handler = LLMHandler(config['llm'])
        tts_handler = TTSHandler(config['tts'])
        print("✅ Tous les modules sont initialisés!")
    except Exception as e:
        print(f"❌ ERREUR lors de l'initialisation: {e}")
        print(f"   Détails: {str(e)}")
        return

    # 3. Boucle principale de l'assistant
    print("\n🎯 Assistant vocal LUXA prêt!")
    print("Appuyez sur Ctrl+C pour arrêter")
    
    try:
        while True:
            print("\n" + "="*50)
            input("Appuyez sur Entrée pour commencer l'écoute...")
            
            # Pipeline STT → LLM → TTS
            try:
                # 1. Écouter et transcrire
                transcription = stt_handler.listen_and_transcribe(duration=5)
                
                if transcription.strip():
                    print(f"📝 Transcription: '{transcription}'")
                    
                    # 2. Générer une réponse
                    response = llm_handler.get_response(transcription)
                    
                    if response.strip():
                        # 3. Prononcer la réponse
                        tts_handler.speak(response)
                    else:
                        print("⚠️ Le LLM n'a pas généré de réponse.")
                else:
                    print("⚠️ Aucune parole détectée, réessayez.")
                    
            except Exception as e:
                print(f"❌ Erreur dans le pipeline: {e}")
                continue
                
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'assistant vocal LUXA")

if __name__ == "__main__":
    main() 