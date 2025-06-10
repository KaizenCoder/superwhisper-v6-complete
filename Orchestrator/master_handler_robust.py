#!/usr/bin/env python3
"""
Master Handler Robuste - Luxa v1.1
====================================

Pipeline principal avec gestion d'erreurs complète et basculements automatiques.
"""

import time
import torch
import asyncio
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import sys

# Imports des modules Luxa
sys.path.append(str(Path(__file__).parent.parent))
from utils.gpu_manager import get_gpu_manager
from Orchestrator.fallback_manager import FallbackManager
from monitoring.prometheus_exporter_enhanced import EnhancedMetricsCollector
from STT.vad_manager import OptimizedVADManager

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RobustMasterHandler:
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialise le gestionnaire principal robuste"""
        
        print("🚀 Initialisation Master Handler Robuste...")
        
        # Composants de base
        self.gpu_manager = get_gpu_manager()
        self.fallback_manager = FallbackManager()
        self.metrics = EnhancedMetricsCollector(port=8000)
        self.vad_manager = None
        
        # État du pipeline
        self.components = {}
        self.is_initialized = False
        self.error_counts = {"stt": 0, "llm": 0, "tts": 0, "vad": 0}
        self.last_errors = {}
        
        # Statistiques de performance
        self.performance_stats = {
            "requests_processed": 0,
            "total_latency_ms": 0,
            "errors_total": 0,
            "last_24h_requests": []
        }
        
        # Démarrer monitoring en arrière-plan
        self._start_monitoring()
        
        print("✅ Master Handler initialisé")
        
    async def initialize(self):
        """Initialise tous les composants du pipeline"""
        if self.is_initialized:
            return
            
        print("🔧 Initialisation du pipeline complet...")
        
        try:
            # Initialiser VAD
            await self._initialize_vad()
            
            # Pré-charger composants critiques si configuré
            await self._preload_critical_components()
            
            self.is_initialized = True
            print("✅ Pipeline initialisé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation pipeline: {e}")
            raise
            
    async def _initialize_vad(self):
        """Initialise le VAD Manager"""
        try:
            self.vad_manager = OptimizedVADManager(
                chunk_ms=160,
                latency_threshold_ms=25
            )
            await self.vad_manager.initialize()
            self.metrics.set_component_status("vad", self.vad_manager.backend, True)
            print("✅ VAD Manager initialisé")
            
        except Exception as e:
            logger.error(f"⚠️ Erreur VAD: {e}, continuant sans VAD")
            self.vad_manager = None
            
    async def _preload_critical_components(self):
        """Pré-charge les composants critiques pour réduire la latence"""
        print("🔥 Pré-chargement des composants critiques...")
        
        # Pré-charger STT si possible
        try:
            start_time = time.time()
            stt_component = self.fallback_manager.get_component("stt")
            load_time = time.time() - start_time
            
            if stt_component:
                self.metrics.record_model_load_time("stt", "primary", load_time)
                self.metrics.set_component_status("stt", "primary", True)
                print(f"✅ STT pré-chargé ({load_time:.2f}s)")
                
        except Exception as e:
            logger.warning(f"⚠️ Pré-chargement STT échoué: {e}")
            
    async def process_audio_safe(self, audio_chunk: np.ndarray) -> Dict[str, Any]:
        """
        Traite l'audio avec gestion d'erreurs complète et fallbacks automatiques
        
        Args:
            audio_chunk: Array numpy contenant l'audio (16kHz, mono)
            
        Returns:
            Dict contenant le résultat du traitement et les métriques
        """
        
        if not self.is_initialized:
            await self.initialize()
            
        # Initialiser résultat
        result = {
            "success": False,
            "text": "",
            "confidence": 0.0,
            "latency_ms": 0,
            "components_used": {},
            "errors": [],
            "metrics": {}
        }
        
        pipeline_start = time.perf_counter()
        
        try:
            # Étape 1: VAD (optionnel)
            speech_detected = await self._process_vad(audio_chunk, result)
            
            if not speech_detected:
                result["text"] = ""
                result["confidence"] = 0.0
                result["success"] = True
                return result
                
            # Étape 2: STT avec fallback
            text = await self._process_stt_with_fallback(audio_chunk, result)
            
            if not text:
                result["errors"].append("STT returned empty text")
                return result
                
            # Étape 3: LLM (optionnel selon le contexte)
            enhanced_text = await self._process_llm_if_needed(text, result)
            
            # Étape 4: Finaliser résultat
            result["text"] = enhanced_text or text
            result["success"] = True
            result["confidence"] = 0.9  # Placeholder
            
            # Métriques finales
            total_latency = (time.perf_counter() - pipeline_start) * 1000
            result["latency_ms"] = total_latency
            result["metrics"]["pipeline_latency_ms"] = total_latency
            
            # Enregistrer succès
            self.metrics.increment_pipeline_requests("success")
            self._update_performance_stats(total_latency, success=True)
            
            print(f"✅ Pipeline réussi: '{text[:50]}...' ({total_latency:.1f}ms)")
            
        except Exception as e:
            # Gestion d'erreur globale
            error_msg = f"Pipeline error: {str(e)}"
            logger.error(error_msg)
            
            result["errors"].append(error_msg)
            result["success"] = False
            
            # Métriques d'erreur
            total_latency = (time.perf_counter() - pipeline_start) * 1000
            result["latency_ms"] = total_latency
            
            self.metrics.increment_pipeline_requests("error")
            self._update_performance_stats(total_latency, success=False)
            
        return result
        
    async def _process_vad(self, audio_chunk: np.ndarray, result: Dict) -> bool:
        """Traite la détection de voix avec métriques"""
        
        if not self.vad_manager:
            return True  # Pas de VAD, considérer tout comme parole
            
        try:
            vad_start = time.perf_counter()
            
            speech_detected = self.vad_manager.is_speech(audio_chunk)
            speech_prob = self.vad_manager.get_speech_probability(audio_chunk)
            
            vad_latency = (time.perf_counter() - vad_start) * 1000
            
            # Métriques VAD
            self.metrics.record_vad_latency(vad_latency / 1000, self.vad_manager.backend)
            self.metrics.set_speech_detection_rate(speech_prob)
            
            result["components_used"]["vad"] = {
                "backend": self.vad_manager.backend,
                "latency_ms": vad_latency,
                "speech_detected": speech_detected,
                "speech_probability": speech_prob
            }
            
            return speech_detected
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur VAD: {e}")
            self.error_counts["vad"] += 1
            return True  # Fallback: considérer comme parole
            
    async def _process_stt_with_fallback(self, audio_chunk: np.ndarray, result: Dict) -> str:
        """Traite STT avec gestion de fallback et timeout"""
        
        metrics = {"latency_ms": 0, "exception_type": None}
        text = ""
        
        try:
            # Mesure de performance STT
            stt_start = time.perf_counter()
            
            # Obtenir composant STT (avec fallback automatique)
            stt_model = self.fallback_manager.get_component("stt", metrics)
            
            if not stt_model:
                raise Exception("Aucun modèle STT disponible")
                
            # Transcription avec timeout
            text = await self._transcribe_with_timeout(stt_model, audio_chunk, timeout=5.0)
            
            # Métriques de latence
            stt_latency = (time.perf_counter() - stt_start) * 1000
            metrics["latency_ms"] = stt_latency
            
            # Enregistrer métriques
            self.metrics.record_stt_latency(stt_latency / 1000)
            
            # Vérifier si fallback nécessaire pour le prochain appel
            if stt_latency > 500:  # Seuil critique
                print(f"⚠️ STT lent ({stt_latency:.0f}ms), fallback potentiel")
                metrics["should_fallback"] = True
                
            # Mettre à jour résultat
            result["components_used"]["stt"] = {
                "model": getattr(stt_model, 'model_name', 'unknown'),
                "latency_ms": stt_latency,
                "backend": "faster-whisper"  # Placeholder
            }
            
        except torch.cuda.OutOfMemoryError as e:
            logger.error("❌ OOM STT, basculement forcé")
            metrics["exception_type"] = "OutOfMemoryError"
            self.error_counts["stt"] += 1
            
            # Forcer le fallback
            stt_model = self.fallback_manager.get_component("stt", metrics)
            text = await self._transcribe_with_timeout(stt_model, audio_chunk, timeout=10.0)
            
        except asyncio.TimeoutError:
            logger.error("⏱️ Timeout STT")
            self.metrics.increment_pipeline_requests("timeout")
            self.error_counts["stt"] += 1
            text = ""
            
        except Exception as e:
            logger.error(f"❌ Erreur STT générale: {e}")
            self.error_counts["stt"] += 1
            text = ""
            
        return text.strip() if text else ""
        
    async def _transcribe_with_timeout(self, stt_model, audio: np.ndarray, timeout: float = 5.0) -> str:
        """Transcription avec timeout et gestion d'erreur"""
        
        try:
            return await asyncio.wait_for(
                self._do_transcribe(stt_model, audio),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Timeout STT ({timeout}s)")
            return ""
            
    async def _do_transcribe(self, stt_model, audio: np.ndarray) -> str:
        """Effectue la transcription selon le type de modèle"""
        
        # Wrapper async pour transcription
        loop = asyncio.get_event_loop()
        
        def sync_transcribe():
            try:
                # Faster Whisper
                if hasattr(stt_model, 'transcribe'):
                    segments, _ = stt_model.transcribe(audio, beam_size=1)
                    return " ".join([segment.text for segment in segments])
                    
                # Whisper standard
                elif hasattr(stt_model, 'decode'):
                    result = stt_model.transcribe(audio)
                    return result.get('text', '')
                    
                # Fallback
                else:
                    return ""
                    
            except Exception as e:
                logger.error(f"❌ Erreur transcription: {e}")
                return ""
                
        return await loop.run_in_executor(None, sync_transcribe)
        
    async def _process_llm_if_needed(self, text: str, result: Dict) -> Optional[str]:
        """Traite LLM si nécessaire (placeholder pour l'instant)"""
        
        # Pour l'instant, on retourne le texte tel quel
        # Dans une vraie implémentation, on pourrait:
        # - Corriger la grammaire
        # - Améliorer la ponctuation
        # - Traiter les commandes
        
        result["components_used"]["llm"] = {
            "processed": False,
            "reason": "Not implemented yet"
        }
        
        return None
        
    def _start_monitoring(self):
        """Démarre le monitoring en arrière-plan"""
        try:
            self.metrics.start_background_updates()
            print("📊 Monitoring démarré")
        except Exception as e:
            logger.warning(f"⚠️ Erreur démarrage monitoring: {e}")
            
    def _update_performance_stats(self, latency_ms: float, success: bool):
        """Met à jour les statistiques de performance"""
        self.performance_stats["requests_processed"] += 1
        self.performance_stats["total_latency_ms"] += latency_ms
        
        if not success:
            self.performance_stats["errors_total"] += 1
            
        # Historique 24h (simpliste)
        current_time = time.time()
        self.performance_stats["last_24h_requests"].append({
            "timestamp": current_time,
            "latency_ms": latency_ms,
            "success": success
        })
        
        # Nettoyer ancien historique (garder 24h)
        cutoff = current_time - (24 * 3600)  # 24 heures
        self.performance_stats["last_24h_requests"] = [
            req for req in self.performance_stats["last_24h_requests"]
            if req["timestamp"] > cutoff
        ]
        
    def get_health_status(self) -> Dict[str, Any]:
        """Retourne le statut de santé complet du système"""
        
        # Mise à jour métriques GPU
        self.gpu_manager.update_memory_info()
        
        # Calculer moyennes
        avg_latency = 0
        if self.performance_stats["requests_processed"] > 0:
            avg_latency = (
                self.performance_stats["total_latency_ms"] / 
                self.performance_stats["requests_processed"]
            )
            
        error_rate = 0
        if self.performance_stats["requests_processed"] > 0:
            error_rate = (
                self.performance_stats["errors_total"] / 
                self.performance_stats["requests_processed"]
            ) * 100
            
        return {
            "status": "healthy" if error_rate < 5 else "degraded" if error_rate < 20 else "unhealthy",
            "initialized": self.is_initialized,
            "components": {
                "vad": self.vad_manager.get_status() if self.vad_manager else {"status": "disabled"},
                "fallback_manager": self.fallback_manager.get_status(),
                "gpu_manager": {
                    "devices": len(self.gpu_manager.device_capabilities),
                    "mapping": self.gpu_manager.gpu_map
                }
            },
            "performance": {
                "requests_processed": self.performance_stats["requests_processed"],
                "avg_latency_ms": avg_latency,
                "error_rate_percent": error_rate,
                "error_counts": self.error_counts.copy()
            },
            "system": self.metrics.get_current_metrics_summary(),
            "timestamp": time.time()
        }

# Test du Master Handler
async def test_master_handler():
    """Test complet du Master Handler"""
    print("🧪 TEST MASTER HANDLER ROBUSTE")
    print("="*40)
    
    # Créer handler
    handler = RobustMasterHandler()
    await handler.initialize()
    
    # Test avec audio synthétique
    print("\n🎯 Test traitement audio...")
    
    # Audio test (3 secondes de bruit)
    test_audio = np.random.randn(48000).astype(np.float32) * 0.1
    
    # Traiter audio
    result = await handler.process_audio_safe(test_audio)
    
    print(f"Résultat: {result}")
    
    # Statut de santé
    print("\n📊 Statut de santé:")
    health = handler.get_health_status()
    print(f"Statut global: {health['status']}")
    print(f"Composants initialisés: {health['initialized']}")
    print(f"Erreurs: {health['performance']['error_counts']}")
    
    print("\n✅ Test Master Handler terminé")

if __name__ == "__main__":
    asyncio.run(test_master_handler()) 