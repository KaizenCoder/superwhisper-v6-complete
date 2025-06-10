#!/usr/bin/env python3
"""
VAD Manager Optimisé - Luxa v1.1
=================================

Gestionnaire VAD avec fenêtre de test réaliste et fallback automatique.
"""

import numpy as np
import time
import torch
import asyncio
from typing import Optional, Tuple

class OptimizedVADManager:
    def __init__(self, chunk_ms: int = 160, latency_threshold_ms: float = 25):
        self.chunk_ms = chunk_ms
        self.latency_threshold_ms = latency_threshold_ms
        self.chunk_samples = int(16000 * chunk_ms / 1000)  # 2560 samples @ 16kHz
        self.backend = None
        self.vad_model = None
        self.vad = None
        
        print(f"🎤 VAD Manager: chunks {chunk_ms}ms ({self.chunk_samples} samples)")
        print(f"⏱️ Seuil latence: {latency_threshold_ms}ms")
        
    async def initialize(self):
        """Initialise avec test de latence sur chunk réaliste"""
        print("🔧 Initialisation VAD...")
        
        # Test Silero d'abord
        silero_latency = await self._test_silero_performance()
        
        if silero_latency <= self.latency_threshold_ms:
            self.backend = "silero"
            print(f"✅ Silero VAD sélectionné ({silero_latency:.2f}ms)")
        else:
            print(f"⚠️ Silero trop lent ({silero_latency:.2f}ms), test WebRTC...")
            webrtc_latency = await self._test_webrtc_performance()
            
            if webrtc_latency <= self.latency_threshold_ms:
                self.backend = "webrtc"
                print(f"✅ WebRTC VAD sélectionné ({webrtc_latency:.2f}ms)")
            else:
                self.backend = "none"
                print(f"⚠️ Tous VAD trop lents, mode pass-through")
                
    async def _test_silero_performance(self) -> float:
        """Test de performance Silero VAD"""
        try:
            print("🧪 Test Silero VAD...")
            
            # Charger modèle Silero
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False
            )
            
            self.vad_model = model
            print("   Modèle Silero chargé")
            
            # Test latence sur chunk réaliste
            test_chunk = np.random.randn(self.chunk_samples).astype(np.float32)
            
            # Warmup pour stabiliser la GPU
            print("   Warmup...")
            for _ in range(5):
                with torch.no_grad():
                    _ = self.vad_model(torch.from_numpy(test_chunk), 16000)
                    
            # Mesure réelle sur 20 itérations
            print("   Mesure performance...")
            latencies = []
            for i in range(20):
                start = time.perf_counter()
                with torch.no_grad():
                    _ = self.vad_model(torch.from_numpy(test_chunk), 16000)
                latency_ms = (time.perf_counter() - start) * 1000
                latencies.append(latency_ms)
                
            avg_latency = np.mean(latencies)
            std_latency = np.std(latencies)
            max_latency = np.max(latencies)
            
            print(f"   Résultats: {avg_latency:.2f} ± {std_latency:.2f}ms (max: {max_latency:.2f}ms)")
            
            return avg_latency
            
        except Exception as e:
            print(f"❌ Erreur test Silero: {e}")
            return float('inf')
            
    async def _test_webrtc_performance(self) -> float:
        """Test de performance WebRTC VAD"""
        try:
            print("🧪 Test WebRTC VAD...")
            
            import webrtcvad
            self.vad = webrtcvad.Vad(3)  # Mode agressif pour meilleure détection
            print("   WebRTC VAD initialisé")
            
            # Test latence sur chunk réaliste
            test_chunk = np.random.randn(self.chunk_samples).astype(np.float32)
            
            # Conversion en PCM 16-bit pour WebRTC
            pcm16 = (test_chunk * 32767).clip(-32767, 32767).astype(np.int16).tobytes()
            
            # Warmup
            print("   Warmup...")
            for _ in range(10):
                _ = self.vad.is_speech(pcm16, 16000)
                
            # Mesure réelle
            print("   Mesure performance...")
            latencies = []
            for i in range(50):  # Plus d'itérations car WebRTC est rapide
                start = time.perf_counter()
                _ = self.vad.is_speech(pcm16, 16000)
                latency_ms = (time.perf_counter() - start) * 1000
                latencies.append(latency_ms)
                
            avg_latency = np.mean(latencies)
            std_latency = np.std(latencies)
            max_latency = np.max(latencies)
            
            print(f"   Résultats: {avg_latency:.2f} ± {std_latency:.2f}ms (max: {max_latency:.2f}ms)")
            
            return avg_latency
            
        except ImportError:
            print("❌ webrtcvad non installé")
            return float('inf')
        except Exception as e:
            print(f"❌ Erreur test WebRTC: {e}")
            return float('inf')
            
    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Détecte si le chunk contient de la parole"""
        if len(audio_chunk) != self.chunk_samples:
            # Redimensionner le chunk si nécessaire
            if len(audio_chunk) < self.chunk_samples:
                # Pad avec des zéros
                audio_chunk = np.pad(audio_chunk, (0, self.chunk_samples - len(audio_chunk)))
            else:
                # Tronquer
                audio_chunk = audio_chunk[:self.chunk_samples]
                
        if self.backend == "silero":
            return self._is_speech_silero(audio_chunk)
        elif self.backend == "webrtc":
            return self._is_speech_webrtc(audio_chunk)
        else:
            # Mode pass-through: tout est considéré comme parole
            return True
            
    def _is_speech_silero(self, audio_chunk: np.ndarray) -> bool:
        """Détection parole avec Silero"""
        try:
            with torch.no_grad():
                tensor = torch.from_numpy(audio_chunk)
                speech_prob = self.vad_model(tensor, 16000).item()
                return speech_prob > 0.5
        except Exception as e:
            print(f"❌ Erreur Silero VAD: {e}")
            return True  # Fallback: considérer comme parole
            
    def _is_speech_webrtc(self, audio_chunk: np.ndarray) -> bool:
        """Détection parole avec WebRTC"""
        try:
            # Conversion en PCM 16-bit
            pcm16 = (audio_chunk * 32767).clip(-32767, 32767).astype(np.int16).tobytes()
            return self.vad.is_speech(pcm16, 16000)
        except Exception as e:
            print(f"❌ Erreur WebRTC VAD: {e}")
            return True  # Fallback: considérer comme parole
            
    def get_speech_probability(self, audio_chunk: np.ndarray) -> float:
        """Retourne la probabilité de parole (0.0 à 1.0)"""
        if self.backend == "silero":
            try:
                with torch.no_grad():
                    tensor = torch.from_numpy(audio_chunk)
                    return self.vad_model(tensor, 16000).item()
            except Exception:
                return 0.5  # Fallback neutre
        elif self.backend == "webrtc":
            # WebRTC retourne bool, on convertit en probabilité binaire
            return 1.0 if self.is_speech(audio_chunk) else 0.0
        else:
            return 1.0  # Mode pass-through
            
    def benchmark_performance(self, num_iterations: int = 100) -> dict:
        """Benchmark de performance du VAD actuel"""
        if self.backend == "none":
            return {"backend": "none", "avg_latency_ms": 0.0}
            
        print(f"📊 Benchmark VAD ({self.backend})...")
        
        test_chunk = np.random.randn(self.chunk_samples).astype(np.float32)
        latencies = []
        
        for i in range(num_iterations):
            start = time.perf_counter()
            _ = self.is_speech(test_chunk)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)
            
        stats = {
            "backend": self.backend,
            "avg_latency_ms": np.mean(latencies),
            "std_latency_ms": np.std(latencies),
            "max_latency_ms": np.max(latencies),
            "min_latency_ms": np.min(latencies),
            "chunk_ms": self.chunk_ms,
            "iterations": num_iterations
        }
        
        print(f"   Latence moyenne: {stats['avg_latency_ms']:.2f} ± {stats['std_latency_ms']:.2f}ms")
        print(f"   Min/Max: {stats['min_latency_ms']:.2f}/{stats['max_latency_ms']:.2f}ms")
        
        return stats
        
    def get_status(self) -> dict:
        """Retourne le statut du VAD Manager"""
        return {
            "backend": self.backend,
            "chunk_ms": self.chunk_ms,
            "chunk_samples": self.chunk_samples,
            "latency_threshold_ms": self.latency_threshold_ms,
            "initialized": self.backend is not None
        }

# Test du VAD Manager
async def test_vad_manager():
    """Test complet du VAD Manager"""
    print("🧪 TEST VAD MANAGER")
    print("="*30)
    
    vad = OptimizedVADManager(chunk_ms=160, latency_threshold_ms=25)
    await vad.initialize()
    
    # Test avec audio synthétique
    print("\n🎯 Test détection...")
    
    # Chunk silencieux
    silence = np.zeros(vad.chunk_samples, dtype=np.float32)
    speech_detected = vad.is_speech(silence)
    speech_prob = vad.get_speech_probability(silence)
    print(f"Silence: {speech_detected} (prob: {speech_prob:.3f})")
    
    # Chunk avec "parole" (bruit)
    noise = np.random.randn(vad.chunk_samples).astype(np.float32) * 0.1
    speech_detected = vad.is_speech(noise)
    speech_prob = vad.get_speech_probability(noise)
    print(f"Bruit faible: {speech_detected} (prob: {speech_prob:.3f})")
    
    # Chunk avec signal fort
    strong_signal = np.random.randn(vad.chunk_samples).astype(np.float32) * 0.5
    speech_detected = vad.is_speech(strong_signal)
    speech_prob = vad.get_speech_probability(strong_signal)
    print(f"Signal fort: {speech_detected} (prob: {speech_prob:.3f})")
    
    # Benchmark
    print("\n📊 Benchmark performance...")
    stats = vad.benchmark_performance(100)
    
    # Statut final
    print(f"\n✅ Statut VAD: {vad.get_status()}")

if __name__ == "__main__":
    asyncio.run(test_vad_manager()) 