#!/usr/bin/env python3
"""
Test du TTSHandler avec le modèle fr_FR-upmc-medium
"""

import yaml
import sys
from pathlib import Path

# Ajouter le répertoire courant au PYTHONPATH
sys.path.append(str(Path(__file__).parent))

def test_tts_handler():
    """Test du TTSHandler avec le modèle upmc"""
    
    print("🧪 Test du TTSHandler avec modèle fr_FR-upmc-medium")
    print("=" * 60)
    
    try:
        # Charger la configuration
        with open("Config/mvp_settings.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        print("✅ Configuration chargée")
        print(f"📍 Modèle configuré: {config['tts']['model_path']}")
        
        # Vérifier que le modèle existe
        model_path = Path(config['tts']['model_path'])
        if not model_path.exists():
            print(f"❌ ERREUR: Modèle non trouvé: {model_path}")
            return False
            
        config_path = Path(f"{config['tts']['model_path']}.json")
        if not config_path.exists():
            print(f"❌ ERREUR: Configuration du modèle non trouvée: {config_path}")
            return False
            
        print("✅ Fichiers de modèle trouvés")
        
        # Importer et initialiser le TTSHandler
        from TTS.tts_handler import TTSHandler
        
        print("\n🔧 Initialisation du TTSHandler...")
        tts_handler = TTSHandler(config['tts'])
        
        print("\n🎵 Test de synthèse vocale...")
        test_phrases = [
            "Bonjour, je suis LUXA, votre assistant vocal intelligent.",
            "Test de synthèse vocale avec le modèle français.",
            "La synthèse fonctionne parfaitement!"
        ]
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"\n--- Test {i}/3 ---")
            tts_handler.speak(phrase)
            
            # Petite pause entre les tests
            input("Appuyez sur Entrée pour continuer...")
        
        print("\n✅ Tous les tests de synthèse ont été effectués avec succès!")
        return True
        
    except ImportError as e:
        print(f"❌ ERREUR d'import: {e}")
        print("Vérifiez que piper-tts est correctement installé.")
        return False
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        print(f"Détails: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_tts_handler()
    
    if success:
        print("\n🎉 Test terminé avec succès!")
        print("Le TTSHandler est prêt pour l'intégration dans run_assistant.py")
    else:
        print("\n❌ Test échoué!")
        print("Vérifiez l'installation de piper-tts et la configuration.")
        sys.exit(1) 