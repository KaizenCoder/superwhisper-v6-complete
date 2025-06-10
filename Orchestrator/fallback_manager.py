#!/usr/bin/env python3
"""
Fallback Manager - Luxa v1.1
=============================

Gestionnaire de fallback intelligent avec basculement automatique selon les métriques.
"""

import yaml
import torch
import time
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Import du GPU Manager
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.gpu_manager import get_gpu_manager

class FallbackManager:
    def __init__(self, config_path: str = "config/fallbacks.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.active_components = {}
        self.gpu_manager = get_gpu_manager()
        self.performance_history = {}
        
        print(f"🔄 Fallback Manager initialisé")
        print(f"📋 Configuration: {config_path}")
        
    def _load_config(self) -> dict:
        """Charge la configuration de fallback"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                print(f"✅ Configuration chargée: {self.config_path}")
                return config
            else:
                print(f"⚠️ Config introuvable, utilisation config par défaut")
                return self._get_default_config()
        except Exception as e:
            print(f"❌ Erreur chargement config: {e}")
            return self._get_default_config()
            
    def _get_default_config(self) -> dict:
        """Configuration par défaut si fichier absent"""
        return {
            "fallback_config": {
                "stt": {
                    "primary": "large-v3",
                    "fallback": "base",
                    "trigger": [
                        {"type": "latency", "threshold_ms": 500},
                        {"type": "vram", "threshold_gb": 2.0},
                        {"type": "exception", "exception": "OutOfMemoryError"}
                    ]
                },
                "llm": {
                    "primary": "llama-2-13b-chat.Q5_K_M.gguf",
                    "fallback": "phi-2.gguf",
                    "trigger": [
                        {"type": "latency", "threshold_ms": 2000},
                        {"type": "vram", "threshold_gb": 4.0},
                        {"type": "exception", "exception": "OutOfMemoryError"}
                    ]
                },
                "tts": {
                    "primary": "xtts-v2",
                    "fallback": "espeak",
                    "trigger": [
                        {"type": "latency", "threshold_ms": 1000},
                        {"type": "vram", "threshold_gb": 1.0},
                        {"type": "exception", "exception": "OutOfMemoryError"}
                    ]
                }
            }
        }
        
    def get_component(self, component_type: str, metrics: Optional[Dict[str, Any]] = None):
        """Retourne le composant actif ou bascule sur fallback si nécessaire"""
        
        # Enregistrer les métriques pour historique
        if metrics:
            self._record_performance(component_type, metrics)
        
        # Premier appel : charger le composant principal
        if component_type not in self.active_components:
            print(f"🚀 Chargement initial {component_type}")
            self.active_components[component_type] = {
                "component": self._load_primary(component_type),
                "type": "primary",
                "load_time": time.time()
            }
            
        # Vérifier si fallback nécessaire
        if metrics and self._should_fallback(component_type, metrics):
            current_type = self.active_components[component_type]["type"]
            
            if current_type == "primary":
                print(f"⚠️ Basculement {component_type} vers fallback")
                fallback_component = self._load_fallback(component_type)
                
                if fallback_component is not None:
                    # Nettoyer ancien composant si possible
                    self._cleanup_component(component_type)
                    
                    self.active_components[component_type] = {
                        "component": fallback_component,
                        "type": "fallback",
                        "load_time": time.time()
                    }
                else:
                    print(f"❌ Échec chargement fallback {component_type}")
            else:
                print(f"⚠️ Déjà en fallback pour {component_type}")
            
        return self.active_components[component_type]["component"]
        
    def _should_fallback(self, component_type: str, metrics: Dict[str, Any]) -> bool:
        """Détermine si on doit basculer sur fallback"""
        
        if component_type not in self.config["fallback_config"]:
            return False
            
        triggers = self.config["fallback_config"][component_type]["trigger"]
        
        for trigger in triggers:
            if trigger["type"] == "latency":
                if metrics.get("latency_ms", 0) > trigger["threshold_ms"]:
                    print(f"🔴 Trigger latence: {metrics.get('latency_ms'):.1f}ms > {trigger['threshold_ms']}ms")
                    return True
                    
            elif trigger["type"] == "vram":
                device_idx = self.gpu_manager.get_device_index(component_type)
                if torch.cuda.is_available() and device_idx < torch.cuda.device_count():
                    free, _ = torch.cuda.mem_get_info(device_idx)
                    free_gb = free / 1024**3
                    if free_gb < trigger["threshold_gb"]:
                        print(f"🔴 Trigger VRAM: {free_gb:.1f}GB < {trigger['threshold_gb']}GB")
                        return True
                        
            elif trigger["type"] == "exception":
                if metrics.get("exception_type") == trigger["exception"]:
                    print(f"🔴 Trigger exception: {trigger['exception']}")
                    return True
                    
        return False
        
    def _load_primary(self, component_type: str):
        """Charge le composant principal"""
        if component_type not in self.config["fallback_config"]:
            print(f"❌ Pas de config pour {component_type}")
            return None
            
        config = self.config["fallback_config"][component_type]
        
        try:
            if component_type == "stt":
                return self._load_stt_model(config["primary"])
            elif component_type == "llm":
                return self._load_llm_model(config["primary"])
            elif component_type == "tts":
                return self._load_tts_model(config["primary"])
        except Exception as e:
            print(f"❌ Erreur chargement {component_type} principal: {e}")
            return None
            
    def _load_fallback(self, component_type: str):
        """Charge le composant de fallback"""
        if component_type not in self.config["fallback_config"]:
            print(f"❌ Pas de config fallback pour {component_type}")
            return None
            
        config = self.config["fallback_config"][component_type]
        
        try:
            if component_type == "stt":
                return self._load_stt_model(config["fallback"], is_fallback=True)
            elif component_type == "llm":
                return self._load_llm_model(config["fallback"], is_fallback=True)
            elif component_type == "tts":
                return self._load_tts_model(config["fallback"], is_fallback=True)
        except Exception as e:
            print(f"❌ Erreur chargement {component_type} fallback: {e}")
            return None
            
    def _load_stt_model(self, model_name: str, is_fallback: bool = False):
        """Charge un modèle STT avec gestion d'erreur"""
        print(f"🎤 Chargement STT: {model_name} ({'fallback' if is_fallback else 'primary'})")
        
        try:
            if "whisper" in model_name.lower() and not is_fallback:
                try:
                    from faster_whisper import WhisperModel
                    device_idx = self.gpu_manager.get_device_index("stt")
                    
                    model = WhisperModel(
                        model_name,
                        device="cuda",
                        device_index=device_idx,
                        compute_type="int8_float16",
                        download_root="./models"
                    )
                    print(f"✅ faster-whisper chargé sur GPU {device_idx}")
                    return model
                    
                except Exception as e:
                    print(f"⚠️ Erreur faster-whisper: {e}, fallback whisper CPU")
                    import whisper
                    return whisper.load_model("base", device="cpu")
                    
            else:
                # Modèle fallback plus léger
                import whisper
                model_size = "tiny" if is_fallback else "base"
                device = "cpu" if is_fallback else "cuda"
                print(f"🔄 Chargement whisper {model_size} sur {device}")
                return whisper.load_model(model_size, device=device)
                
        except torch.cuda.OutOfMemoryError:
            print("❌ OOM sur STT, fallback CPU tiny")
            import whisper
            return whisper.load_model("tiny", device="cpu")
        except Exception as e:
            print(f"❌ Erreur chargement STT: {e}")
            return None
            
    def _load_llm_model(self, model_name: str, is_fallback: bool = False):
        """Charge un modèle LLM avec gestion d'erreur"""
        print(f"🧠 Chargement LLM: {model_name} ({'fallback' if is_fallback else 'primary'})")
        
        try:
            # Simuler chargement LLM (remplacer par vraie implémentation)
            device = self.gpu_manager.get_device("llm")
            
            # Ici on chargerait le vrai modèle LLM
            mock_model = {
                "name": model_name,
                "device": device,
                "type": "fallback" if is_fallback else "primary",
                "loaded": True
            }
            
            print(f"✅ LLM {model_name} chargé sur {device}")
            return mock_model
            
        except Exception as e:
            print(f"❌ Erreur chargement LLM: {e}")
            return None
            
    def _load_tts_model(self, model_name: str, is_fallback: bool = False):
        """Charge un modèle TTS avec gestion d'erreur"""
        print(f"🔊 Chargement TTS: {model_name} ({'fallback' if is_fallback else 'primary'})")
        
        try:
            # Simuler chargement TTS (remplacer par vraie implémentation)
            device = self.gpu_manager.get_device("tts")
            
            mock_model = {
                "name": model_name,
                "device": device,
                "type": "fallback" if is_fallback else "primary",
                "loaded": True
            }
            
            print(f"✅ TTS {model_name} chargé sur {device}")
            return mock_model
            
        except Exception as e:
            print(f"❌ Erreur chargement TTS: {e}")
            return None
            
    def _cleanup_component(self, component_type: str):
        """Nettoie l'ancien composant"""
        if component_type in self.active_components:
            try:
                component_info = self.active_components[component_type]
                component = component_info["component"]
                
                # Nettoyage spécifique selon le type
                if hasattr(component, 'model'):
                    del component.model
                elif hasattr(component, 'close'):
                    component.close()
                    
                print(f"🧹 Ancien {component_type} nettoyé")
                
            except Exception as e:
                print(f"⚠️ Erreur nettoyage {component_type}: {e}")
                
    def _record_performance(self, component_type: str, metrics: Dict[str, Any]):
        """Enregistre les métriques de performance"""
        if component_type not in self.performance_history:
            self.performance_history[component_type] = []
            
        record = {
            "timestamp": time.time(),
            "metrics": metrics.copy()
        }
        
        self.performance_history[component_type].append(record)
        
        # Garder seulement les 100 derniers enregistrements
        if len(self.performance_history[component_type]) > 100:
            self.performance_history[component_type] = self.performance_history[component_type][-100:]
            
    def get_performance_stats(self, component_type: str) -> Dict[str, Any]:
        """Retourne les statistiques de performance"""
        if component_type not in self.performance_history:
            return {}
            
        history = self.performance_history[component_type]
        if not history:
            return {}
            
        recent_latencies = [
            record["metrics"].get("latency_ms", 0) 
            for record in history[-10:]  # 10 dernières mesures
            if "latency_ms" in record["metrics"]
        ]
        
        if recent_latencies:
            import numpy as np
            return {
                "avg_latency_ms": np.mean(recent_latencies),
                "max_latency_ms": np.max(recent_latencies),
                "min_latency_ms": np.min(recent_latencies),
                "sample_count": len(recent_latencies)
            }
        else:
            return {}
            
    def force_fallback(self, component_type: str):
        """Force le basculement vers fallback"""
        print(f"🔄 Basculement forcé {component_type}")
        fake_metrics = {"latency_ms": 9999, "force_fallback": True}
        self.get_component(component_type, fake_metrics)
        
    def reset_component(self, component_type: str):
        """Remet le composant principal"""
        if component_type in self.active_components:
            self._cleanup_component(component_type)
            del self.active_components[component_type]
            print(f"🔄 Reset {component_type}, prochain appel chargera le principal")
            
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut complet du Fallback Manager"""
        status = {
            "active_components": {},
            "performance_stats": {},
            "gpu_status": {}
        }
        
        for comp_type, comp_info in self.active_components.items():
            status["active_components"][comp_type] = {
                "type": comp_info["type"],
                "load_time": comp_info["load_time"],
                "uptime_s": time.time() - comp_info["load_time"]
            }
            
            # Stats de performance
            status["performance_stats"][comp_type] = self.get_performance_stats(comp_type)
            
        # Statut GPU
        self.gpu_manager.update_memory_info()
        for i, caps in self.gpu_manager.device_capabilities.items():
            status["gpu_status"][f"gpu_{i}"] = {
                "name": caps["name"],
                "free_gb": caps["free_memory_gb"],
                "total_gb": caps["total_memory_gb"]
            }
            
        return status

# Test du Fallback Manager
def test_fallback_manager():
    """Test complet du Fallback Manager"""
    print("🧪 TEST FALLBACK MANAGER")
    print("="*35)
    
    # Créer le répertoire config s'il n'existe pas
    os.makedirs("config", exist_ok=True)
    
    # Créer config de test
    test_config = {
        "fallback_config": {
            "stt": {
                "primary": "large-v3",
                "fallback": "base",
                "trigger": [
                    {"type": "latency", "threshold_ms": 300},
                    {"type": "vram", "threshold_gb": 2.0}
                ]
            }
        }
    }
    
    with open("config/fallbacks.yaml", "w") as f:
        yaml.dump(test_config, f)
    
    fm = FallbackManager()
    
    # Test 1: Chargement normal
    print("\n🎯 Test 1: Chargement normal")
    stt_model = fm.get_component("stt")
    print(f"Modèle chargé: {stt_model}")
    
    # Test 2: Métriques normales
    print("\n🎯 Test 2: Métriques normales")
    normal_metrics = {"latency_ms": 150}
    stt_model = fm.get_component("stt", normal_metrics)
    
    # Test 3: Trigger fallback
    print("\n🎯 Test 3: Trigger fallback (latence élevée)")
    high_latency_metrics = {"latency_ms": 500}
    stt_model = fm.get_component("stt", high_latency_metrics)
    
    # Test 4: Statut
    print("\n🎯 Test 4: Statut complet")
    status = fm.get_status()
    print(f"Statut: {status}")
    
    print("\n✅ Test Fallback Manager terminé")

if __name__ == "__main__":
    test_fallback_manager() 