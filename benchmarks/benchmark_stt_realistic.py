#!/usr/bin/env python3
"""
Benchmark STT Réaliste - Luxa v1.1
===================================

Teste les performances STT avec insanely-fast-whisper et faster-whisper
avec mapping GPU dynamique et configuration réaliste.
"""

import os
import time
import numpy as np
import torch
import asyncio
from typing import Dict, Any

try:
    from insanely_fast_whisper.transcribe import Transcriber
except ImportError:
    Transcriber = None
    print("⚠️ insanely-fast-whisper non installé")

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None
    print("⚠️ faster-whisper non installé")

class STTBenchmark:
    def __init__(self):
        # Mapping GPU dynamique via env
        self.gpu_map = self._parse_gpu_map()
        self.device_index = self.gpu_map.get("4060", 1)
        print(f"🎮 GPU Mapping: {self.gpu_map}")
        print(f"🎯 Utilisation GPU {self.device_index} pour STT")
        
    def _parse_gpu_map(self):
        """Parse LUXA_GPU_MAP=3090:0,4060:1"""
        gpu_map_str = os.getenv("LUXA_GPU_MAP", "3090:0,4060:1")
        gpu_map = {}
        for mapping in gpu_map_str.split(","):
            name, idx = mapping.split(":")
            gpu_map[name] = int(idx)
        return gpu_map
        
    async def benchmark_insanely_fast_whisper(self):
        """Test réel avec insanely-fast-whisper"""
        print(f"\n🎯 Testing insanely-fast-whisper on GPU {self.device_index}")
        
        if Transcriber is None:
            print("❌ insanely-fast-whisper non disponible")
            return float('inf')
        
        try:
            # Configuration réaliste
            transcriber = Transcriber(
                model_name="openai/whisper-large-v3",
                device_id=self.device_index,
                torch_dtype="float16",  # Pas INT8 direct
                batch_size=4,
                better_tokenization=True
            )
            
            # Audio test 3 secondes
            test_audio = np.random.randn(48000).astype(np.float32)
            
            # Warmup
            print("🔥 Warmup...")
            for _ in range(3):
                _ = transcriber.transcribe(test_audio)
            
            # Mesure latence
            print("📊 Mesure des performances...")
            latencies = []
            for i in range(10):
                start = time.time()
                segments = transcriber.transcribe(test_audio)
                latency = (time.time() - start) * 1000
                latencies.append(latency)
                print(f"   Run {i+1}: {latency:.1f}ms")
            
            avg_latency = np.mean(latencies)
            std_latency = np.std(latencies)
            
            print(f"✅ insanely-fast-whisper:")
            print(f"   Latence moyenne: {avg_latency:.1f} ± {std_latency:.1f}ms")
            
            # Vérifier VRAM
            if torch.cuda.is_available():
                vram_used = torch.cuda.memory_allocated(self.device_index) / 1024**3
                print(f"   VRAM utilisée: {vram_used:.2f}GB")
            
            return avg_latency
            
        except Exception as e:
            print(f"❌ Erreur insanely-fast-whisper: {e}")
            return float('inf')
            
    async def benchmark_faster_whisper(self):
        """Alternative avec faster-whisper (quantification INT8)"""
        print(f"\n🎯 Testing faster-whisper INT8 on GPU {self.device_index}")
        
        if WhisperModel is None:
            print("❌ faster-whisper non disponible")
            return float('inf')
        
        try:
            # Modèle avec quantification INT8 réelle
            model = WhisperModel(
                "large-v3",
                device="cuda",
                device_index=self.device_index,
                compute_type="int8_float16",  # Quantification INT8 supportée
                num_workers=1,
                download_root="./models"
            )
            
            # Audio test
            test_audio = np.random.randn(48000).astype(np.float32)
            
            # Warmup
            print("🔥 Warmup...")
            for _ in range(3):
                segments, _ = model.transcribe(test_audio, beam_size=1)
                _ = list(segments)
            
            # Benchmark avec chunks streaming
            print("📊 Benchmark streaming...")
            latencies = []
            chunk_size = 16000  # 1 seconde
            
            for i in range(0, len(test_audio), chunk_size):
                chunk = test_audio[i:i+chunk_size]
                start = time.time()
                segments, _ = model.transcribe(chunk, beam_size=1)
                # Consommer le générateur
                _ = list(segments)
                latency = (time.time() - start) * 1000
                latencies.append(latency)
                
            avg_latency = np.mean(latencies)
            std_latency = np.std(latencies)
            
            print(f"✅ faster-whisper INT8:")
            print(f"   Latence moyenne: {avg_latency:.1f} ± {std_latency:.1f}ms")
            
            # Vérifier VRAM
            if torch.cuda.is_available():
                vram_used = torch.cuda.memory_allocated(self.device_index) / 1024**3
                print(f"   VRAM utilisée: {vram_used:.2f}GB")
            
            return avg_latency
            
        except Exception as e:
            print(f"❌ Erreur faster-whisper: {e}")
            return float('inf')
    
    async def run_full_benchmark(self):
        """Lance tous les benchmarks STT"""
        print("🚀 LUXA v1.1 - Benchmark STT Réaliste")
        print("="*50)
        
        # Vérifier CUDA
        if not torch.cuda.is_available():
            print("❌ CUDA non disponible")
            return {}
        
        print(f"🔧 Configuration GPU:")
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            free, total = torch.cuda.mem_get_info(i)
            print(f"   GPU {i}: {props.name} ({free/1024**3:.1f}/{total/1024**3:.1f}GB libre)")
        
        results = {}
        
        # Test insanely-fast-whisper
        results["insanely_fast"] = await self.benchmark_insanely_fast_whisper()
        
        # Test faster-whisper
        results["faster_whisper"] = await self.benchmark_faster_whisper()
        
        # Résumé
        print("\n📊 RÉSULTATS FINAUX:")
        print("="*30)
        for method, latency in results.items():
            if latency != float('inf'):
                status = "🟢" if latency < 500 else "🟡" if latency < 1000 else "🔴"
                print(f"{status} {method}: {latency:.1f}ms")
            else:
                print(f"🔴 {method}: ÉCHEC")
        
        # Recommandation
        best_method = min(results.items(), key=lambda x: x[1])
        if best_method[1] != float('inf'):
            print(f"\n🏆 Recommandé: {best_method[0]} ({best_method[1]:.1f}ms)")
        
        return results

async def main():
    """Point d'entrée principal"""
    benchmark = STTBenchmark()
    results = await benchmark.run_full_benchmark()
    
    # Sauvegarder résultats
    import json
    with open("benchmark_stt_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Résultats sauvés dans benchmark_stt_results.json")

if __name__ == "__main__":
    asyncio.run(main()) 