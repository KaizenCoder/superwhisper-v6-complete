#!/usr/bin/env python3
"""
Enhanced Prometheus Exporter - Luxa v1.1
==========================================

Exportateur Prometheus complet avec métriques VRAM, système et performance.
"""

import time
import torch
import psutil
import threading
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, Histogram, Gauge, start_http_server, 
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
import http.server
import socketserver

class EnhancedMetricsCollector:
    def __init__(self, port: int = 8000, update_interval: float = 1.0):
        self.port = port
        self.update_interval = update_interval
        
        # Registry personnalisé pour éviter les conflits
        self.registry = CollectorRegistry()
        
        # Métriques pipeline
        self.stt_latency = Histogram(
            'luxa_stt_latency_seconds', 
            'STT processing time in seconds',
            registry=self.registry
        )
        
        self.llm_latency = Histogram(
            'luxa_llm_latency_seconds',
            'LLM processing time in seconds', 
            registry=self.registry
        )
        
        self.tts_latency = Histogram(
            'luxa_tts_latency_seconds',
            'TTS processing time in seconds',
            registry=self.registry
        )
        
        self.llm_tokens_per_second = Gauge(
            'luxa_llm_tokens_per_second', 
            'LLM generation speed in tokens/sec',
            registry=self.registry
        )
        
        self.pipeline_requests = Counter(
            'luxa_pipeline_requests_total', 
            'Total pipeline requests',
            ['status'],  # success, error, timeout
            registry=self.registry
        )
        
        # Métriques VRAM détaillées
        self.gpu_memory_used = Gauge(
            'luxa_gpu_memory_used_bytes', 
            'GPU memory used in bytes', 
            ['device', 'device_name'],
            registry=self.registry
        )
        
        self.gpu_memory_free = Gauge(
            'luxa_gpu_memory_free_bytes', 
            'GPU memory free in bytes', 
            ['device', 'device_name'],
            registry=self.registry
        )
        
        self.gpu_memory_total = Gauge(
            'luxa_gpu_memory_total_bytes', 
            'GPU memory total in bytes', 
            ['device', 'device_name'],
            registry=self.registry
        )
        
        self.gpu_utilization = Gauge(
            'luxa_gpu_utilization_percent',
            'GPU utilization percentage',
            ['device', 'device_name'],
            registry=self.registry
        )
        
        self.gpu_temperature = Gauge(
            'luxa_gpu_temperature_celsius',
            'GPU temperature in Celsius',
            ['device', 'device_name'], 
            registry=self.registry
        )
        
        # Métriques CPU et RAM
        self.cpu_usage = Gauge(
            'luxa_cpu_usage_percent', 
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.cpu_usage_per_core = Gauge(
            'luxa_cpu_usage_per_core_percent',
            'CPU usage per core percentage',
            ['core'],
            registry=self.registry
        )
        
        self.ram_usage = Gauge(
            'luxa_ram_usage_bytes', 
            'RAM usage in bytes',
            registry=self.registry
        )
        
        self.ram_usage_percent = Gauge(
            'luxa_ram_usage_percent',
            'RAM usage percentage', 
            registry=self.registry
        )
        
        self.swap_usage = Gauge(
            'luxa_swap_usage_bytes',
            'Swap usage in bytes',
            registry=self.registry
        )
        
        # Métriques composants
        self.component_status = Gauge(
            'luxa_component_status',
            'Component status (1=active, 0=inactive)',
            ['component', 'type'],  # component: stt/llm/tts, type: primary/fallback
            registry=self.registry
        )
        
        self.model_load_time = Histogram(
            'luxa_model_load_time_seconds',
            'Model loading time in seconds',
            ['component', 'model_name'],
            registry=self.registry
        )
        
        # Métriques VAD
        self.vad_latency = Histogram(
            'luxa_vad_latency_seconds',
            'VAD processing time in seconds',
            ['backend'],  # silero, webrtc, none
            registry=self.registry
        )
        
        self.speech_detection_rate = Gauge(
            'luxa_speech_detection_rate',
            'Rate of speech detection (0.0-1.0)',
            registry=self.registry
        )
        
        # Thread pour mise à jour automatique
        self.update_thread = None
        self.running = False
        
        print(f"📊 Enhanced Metrics Collector initialisé")
        print(f"🌐 Serveur Prometheus: http://localhost:{port}/metrics")
        
    def start_server(self):
        """Démarre le serveur Prometheus"""
        try:
            # Créer serveur HTTP personnalisé
            handler = self._create_metrics_handler()
            
            with socketserver.TCPServer(("", self.port), handler) as httpd:
                print(f"✅ Serveur Prometheus démarré sur port {self.port}")
                
                # Démarrer thread de mise à jour
                self.start_background_updates()
                
                # Servir indéfiniment
                httpd.serve_forever()
                
        except OSError as e:
            if e.errno == 98:  # Address already in use
                print(f"⚠️ Port {self.port} déjà utilisé, tentative port alternatif...")
                self.port += 1
                self.start_server()
            else:
                print(f"❌ Erreur serveur Prometheus: {e}")
                
    def _create_metrics_handler(self):
        """Crée le handler HTTP pour les métriques"""
        registry = self.registry
        
        class MetricsHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/metrics":
                    # Générer métriques Prometheus
                    output = generate_latest(registry)
                    
                    self.send_response(200)
                    self.send_header('Content-Type', CONTENT_TYPE_LATEST)
                    self.send_header('Content-Length', str(len(output)))
                    self.end_headers()
                    self.wfile.write(output)
                    
                elif self.path == "/health":
                    # Endpoint de santé
                    response = b"OK"
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.send_header('Content-Length', str(len(response)))
                    self.end_headers()
                    self.wfile.write(response)
                    
                else:
                    self.send_response(404)
                    self.end_headers()
                    
            def log_message(self, format, *args):
                # Supprimer logs HTTP verbeux
                pass
                
        return MetricsHandler
        
    def start_background_updates(self):
        """Démarre les mises à jour automatiques des métriques"""
        if self.update_thread and self.update_thread.is_alive():
            return
            
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        print(f"🔄 Mise à jour automatique démarrée (interval: {self.update_interval}s)")
        
    def stop_background_updates(self):
        """Arrête les mises à jour automatiques"""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join()
        print("🛑 Mise à jour automatique arrêtée")
        
    def _update_loop(self):
        """Boucle de mise à jour des métriques système"""
        while self.running:
            try:
                self.update_gpu_metrics()
                self.update_system_metrics()
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"⚠️ Erreur mise à jour métriques: {e}")
                time.sleep(self.update_interval)
                
    def update_gpu_metrics(self):
        """Met à jour toutes les métriques GPU"""
        if not torch.cuda.is_available():
            return
            
        try:
            for device_id in range(torch.cuda.device_count()):
                # Récupérer infos mémoire
                free, total = torch.cuda.mem_get_info(device_id)
                used = total - free
                
                # Infos device
                props = torch.cuda.get_device_properties(device_id)
                device_label = f"cuda:{device_id}"
                device_name = props.name.replace(" ", "_")
                
                # Métriques mémoire
                self.gpu_memory_used.labels(
                    device=device_label, 
                    device_name=device_name
                ).set(used)
                
                self.gpu_memory_free.labels(
                    device=device_label, 
                    device_name=device_name
                ).set(free)
                
                self.gpu_memory_total.labels(
                    device=device_label, 
                    device_name=device_name
                ).set(total)
                
                # Utilisation GPU (nécessite nvidia-ml-py pour vraies valeurs) 
                try:
                    import pynvml
                    pynvml.nvmlInit()
                    handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
                    
                    # Utilisation GPU
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    self.gpu_utilization.labels(
                        device=device_label,
                        device_name=device_name
                    ).set(util.gpu)
                    
                    # Température
                    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    self.gpu_temperature.labels(
                        device=device_label,
                        device_name=device_name  
                    ).set(temp)
                    
                except ImportError:
                    # Fallback sans pynvml
                    usage_pct = (used / total) * 100
                    self.gpu_utilization.labels(
                        device=device_label,
                        device_name=device_name
                    ).set(usage_pct)
                    
                except Exception as e:
                    print(f"⚠️ Erreur métriques GPU {device_id}: {e}")
                    
        except Exception as e:
            print(f"❌ Erreur générale métriques GPU: {e}")
            
    def update_system_metrics(self):
        """Met à jour les métriques système"""
        try:
            # CPU global
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_usage.set(cpu_percent)
            
            # CPU par core
            cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            for i, core_usage in enumerate(cpu_per_core):
                self.cpu_usage_per_core.labels(core=f"core_{i}").set(core_usage)
                
            # RAM
            memory = psutil.virtual_memory()
            self.ram_usage.set(memory.used)
            self.ram_usage_percent.set(memory.percent)
            
            # Swap
            swap = psutil.swap_memory()
            self.swap_usage.set(swap.used)
            
        except Exception as e:
            print(f"❌ Erreur métriques système: {e}")
            
    # Méthodes d'enregistrement des métriques business
    def record_stt_latency(self, latency_seconds: float):
        """Enregistre la latence STT"""
        self.stt_latency.observe(latency_seconds)
        
    def record_llm_latency(self, latency_seconds: float):
        """Enregistre la latence LLM"""
        self.llm_latency.observe(latency_seconds)
        
    def record_tts_latency(self, latency_seconds: float):
        """Enregistre la latence TTS"""
        self.tts_latency.observe(latency_seconds)
        
    def set_llm_tokens_per_second(self, tokens_per_sec: float):
        """Met à jour la vitesse de génération LLM"""
        self.llm_tokens_per_second.set(tokens_per_sec)
        
    def increment_pipeline_requests(self, status: str):
        """Incrémente le compteur de requêtes pipeline"""
        self.pipeline_requests.labels(status=status).inc()
        
    def record_vad_latency(self, latency_seconds: float, backend: str):
        """Enregistre la latence VAD"""
        self.vad_latency.labels(backend=backend).observe(latency_seconds)
        
    def set_speech_detection_rate(self, rate: float):
        """Met à jour le taux de détection de parole"""
        self.speech_detection_rate.set(rate)
        
    def set_component_status(self, component: str, component_type: str, active: bool):
        """Met à jour le statut d'un composant"""
        self.component_status.labels(
            component=component, 
            type=component_type
        ).set(1 if active else 0)
        
    def record_model_load_time(self, component: str, model_name: str, load_time_seconds: float):
        """Enregistre le temps de chargement d'un modèle"""
        self.model_load_time.labels(
            component=component,
            model_name=model_name
        ).observe(load_time_seconds)
        
    def can_load_model(self, model_size_gb: float, device_id: int = 0) -> bool:
        """Vérifie si on peut charger un modèle de taille donnée"""
        if not torch.cuda.is_available():
            return False
            
        try:
            free, _ = torch.cuda.mem_get_info(device_id)
            free_gb = free / 1024**3
            
            # Marge de sécurité de 2GB
            can_load = free_gb > (model_size_gb + 2.0)
            
            print(f"🔍 GPU {device_id}: {free_gb:.1f}GB libre, "
                  f"modèle {model_size_gb:.1f}GB - {'✅' if can_load else '❌'}")
                  
            return can_load
            
        except Exception as e:
            print(f"❌ Erreur vérification modèle: {e}")
            return False
            
    def get_current_metrics_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des métriques actuelles"""
        summary = {
            "timestamp": time.time(),
            "system": {},
            "gpu": {}
        }
        
        # Métriques système
        try:
            summary["system"] = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used_gb": psutil.virtual_memory().used / 1024**3,
                "memory_total_gb": psutil.virtual_memory().total / 1024**3
            }
        except Exception as e:
            print(f"⚠️ Erreur résumé système: {e}")
            
        # Métriques GPU
        if torch.cuda.is_available():
            try:
                for i in range(torch.cuda.device_count()):
                    free, total = torch.cuda.mem_get_info(i)
                    props = torch.cuda.get_device_properties(i)
                    
                    summary["gpu"][f"gpu_{i}"] = {
                        "name": props.name,
                        "memory_used_gb": (total - free) / 1024**3,
                        "memory_total_gb": total / 1024**3,
                        "memory_free_gb": free / 1024**3,
                        "memory_percent": ((total - free) / total) * 100
                    }
            except Exception as e:
                print(f"⚠️ Erreur résumé GPU: {e}")
                
        return summary

# Test de l'exportateur Prometheus
def test_prometheus_exporter():
    """Test complet de l'exportateur Prometheus"""
    print("🧪 TEST PROMETHEUS EXPORTER")
    print("="*35)
    
    # Créer collecteur
    collector = EnhancedMetricsCollector(port=8001, update_interval=2.0)
    
    # Test métriques manuelles
    print("📊 Test enregistrement métriques...")
    collector.record_stt_latency(0.25)
    collector.record_llm_latency(1.5)
    collector.set_llm_tokens_per_second(45.2)
    collector.increment_pipeline_requests("success")
    collector.set_component_status("stt", "primary", True)
    
    # Test mise à jour système
    print("🔄 Test mise à jour système...")
    collector.update_gpu_metrics()
    collector.update_system_metrics()
    
    # Résumé
    print("📋 Résumé métriques:")
    summary = collector.get_current_metrics_summary()
    for section, data in summary.items():
        if section != "timestamp":
            print(f"  {section}: {data}")
    
    print(f"\n✅ Test terminé")
    print(f"🌐 Pour démarrer le serveur: collector.start_server()")

if __name__ == "__main__":
    test_prometheus_exporter() 