#!/usr/bin/env python3
"""
GPU Manager - Luxa v1.1
========================

Gestionnaire GPU dynamique avec détection automatique et mapping intelligent.
"""

import os
import torch
import subprocess
from typing import Dict, Optional

class GPUManager:
    def __init__(self):
        self.gpu_map = self._build_gpu_map()
        self.device_capabilities = self._analyze_devices()
        print(f"🎮 GPU Manager initialisé: {self.gpu_map}")
        
    def _build_gpu_map(self) -> Dict[str, int]:
        """Construit un mapping dynamique nom→index"""
        # Option 1: Variable d'environnement
        env_map = os.getenv("LUXA_GPU_MAP")
        if env_map:
            return self._parse_env_map(env_map)
            
        # Option 2: Détection automatique
        return self._auto_detect_gpus()
        
    def _parse_env_map(self, env_map: str) -> Dict[str, int]:
        """Parse LUXA_GPU_MAP=3090:0,4060:1"""
        gpu_map = {}
        try:
            for mapping in env_map.split(","):
                name, idx = mapping.split(":")
                gpu_map[name] = int(idx)
            print(f"🔧 GPU mapping depuis env: {gpu_map}")
        except Exception as e:
            print(f"⚠️ Erreur parsing env GPU map: {e}, fallback auto-detect")
            return self._auto_detect_gpus()
        return gpu_map
        
    def _auto_detect_gpus(self) -> Dict[str, int]:
        """Détecte les GPUs et crée un mapping intelligent"""
        gpu_map = {}
        
        if not torch.cuda.is_available():
            print("❌ CUDA non disponible")
            return gpu_map
            
        print("🔍 Détection automatique des GPUs...")
        
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            name = props.name
            memory_gb = props.total_memory / 1024**3
            
            print(f"   GPU {i}: {name} ({memory_gb:.1f}GB)")
            
            # Mapping par capacité mémoire et nom
            if "3090" in name or "4090" in name or memory_gb > 20:
                gpu_map["llm"] = i
                gpu_map["3090"] = i
            elif "4060" in name or "3060" in name or (10 < memory_gb <= 20):
                gpu_map["stt"] = i
                gpu_map["4060"] = i
            elif memory_gb <= 10:
                gpu_map["tts"] = i
                
        # Fallback si pas de distinction claire
        if "llm" not in gpu_map and torch.cuda.device_count() > 0:
            gpu_map["llm"] = 0
            print("🔄 Fallback: GPU 0 pour LLM")
            
        if "stt" not in gpu_map:
            if torch.cuda.device_count() > 1:
                gpu_map["stt"] = 1
                print("🔄 Fallback: GPU 1 pour STT")
            else:
                gpu_map["stt"] = 0
                print("🔄 Fallback: GPU 0 pour STT (GPU unique)")
                
        if "tts" not in gpu_map:
            gpu_map["tts"] = gpu_map.get("stt", 0)
            print("🔄 Fallback: TTS partage GPU STT")
            
        print(f"🎯 GPU auto-mapping: {gpu_map}")
        return gpu_map
        
    def _analyze_devices(self) -> Dict[int, Dict]:
        """Analyse les capacités de chaque GPU"""
        capabilities = {}
        
        if not torch.cuda.is_available():
            return capabilities
            
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            free, total = torch.cuda.mem_get_info(i)
            
            capabilities[i] = {
                "name": props.name,
                "total_memory_gb": total / 1024**3,
                "free_memory_gb": free / 1024**3,
                "compute_capability": f"{props.major}.{props.minor}",
                "multiprocessor_count": props.multi_processor_count,
                "max_threads_per_block": props.max_threads_per_block
            }
            
        return capabilities
        
    def get_device(self, purpose: str = "llm") -> str:
        """Retourne le device approprié pour un usage"""
        if purpose in self.gpu_map:
            return f"cuda:{self.gpu_map[purpose]}"
        elif purpose == "fallback":
            return "cuda:0" if torch.cuda.is_available() else "cpu"
        return "cuda:0" if torch.cuda.is_available() else "cpu"
        
    def get_device_index(self, purpose: str = "llm") -> int:
        """Retourne l'index du device"""
        return self.gpu_map.get(purpose, 0)
        
    def can_load_model(self, model_size_gb: float, purpose: str = "llm") -> bool:
        """Vérifie si on peut charger un modèle de taille donnée"""
        if not torch.cuda.is_available():
            return False
            
        device_idx = self.get_device_index(purpose)
        
        if device_idx not in self.device_capabilities:
            return False
            
        free_gb = self.device_capabilities[device_idx]["free_memory_gb"]
        
        # Marge de sécurité de 2GB
        can_load = free_gb > (model_size_gb + 2.0)
        
        print(f"🔍 GPU {device_idx} ({purpose}): {free_gb:.1f}GB libre, "
              f"modèle {model_size_gb:.1f}GB - {'✅' if can_load else '❌'}")
              
        return can_load
        
    def get_optimal_batch_size(self, purpose: str = "llm", base_batch_size: int = 1) -> int:
        """Calcule la taille de batch optimale selon la VRAM disponible"""
        if not torch.cuda.is_available():
            return 1
            
        device_idx = self.get_device_index(purpose)
        
        if device_idx not in self.device_capabilities:
            return base_batch_size
            
        free_gb = self.device_capabilities[device_idx]["free_memory_gb"]
        
        # Heuristique simple: 1 batch par 4GB disponible
        optimal_batch = max(1, int(free_gb / 4) * base_batch_size)
        optimal_batch = min(optimal_batch, 16)  # Cap à 16
        
        print(f"📊 Batch size optimal pour {purpose}: {optimal_batch}")
        return optimal_batch
        
    def update_memory_info(self):
        """Met à jour les informations mémoire"""
        if not torch.cuda.is_available():
            return
            
        for i in range(torch.cuda.device_count()):
            free, total = torch.cuda.mem_get_info(i)
            if i in self.device_capabilities:
                self.device_capabilities[i]["free_memory_gb"] = free / 1024**3
                
    def print_status(self):
        """Affiche le statut complet des GPUs"""
        print("\n🎮 STATUT GPU MANAGER")
        print("="*40)
        
        if not torch.cuda.is_available():
            print("❌ CUDA non disponible")
            return
            
        self.update_memory_info()
        
        for i, caps in self.device_capabilities.items():
            usage_pct = (1 - caps["free_memory_gb"] / caps["total_memory_gb"]) * 100
            status = "🟢" if usage_pct < 50 else "🟡" if usage_pct < 80 else "🔴"
            
            print(f"{status} GPU {i}: {caps['name']}")
            print(f"   VRAM: {caps['free_memory_gb']:.1f}/{caps['total_memory_gb']:.1f}GB ({usage_pct:.1f}% utilisé)")
            print(f"   Compute: {caps['compute_capability']}, SM: {caps['multiprocessor_count']}")
            
        print(f"\n🎯 Mapping actuel: {self.gpu_map}")
        
    def get_best_device_for_model(self, model_size_gb: float) -> tuple[str, int]:
        """Retourne le meilleur device pour un modèle donné"""
        if not torch.cuda.is_available():
            return "cpu", -1
            
        self.update_memory_info()
        
        best_device = None
        best_free_memory = 0
        
        for i, caps in self.device_capabilities.items():
            free_gb = caps["free_memory_gb"]
            if free_gb >= model_size_gb + 2.0 and free_gb > best_free_memory:
                best_device = i
                best_free_memory = free_gb
                
        if best_device is not None:
            return f"cuda:{best_device}", best_device
        else:
            print(f"⚠️ Aucun GPU avec assez de VRAM pour {model_size_gb:.1f}GB")
            return "cpu", -1

# Instance globale
gpu_manager = GPUManager()

def get_gpu_manager() -> GPUManager:
    """Retourne l'instance globale du GPU Manager"""
    return gpu_manager 