# STT/stt_handler.py
import torch
import sounddevice as sd
import numpy as np
from transformers import WhisperProcessor, WhisperForConditionalGeneration

class STTHandler:
    def __init__(self, config):
        self.config = config
        self.device = config['gpu_device'] if torch.cuda.is_available() else "cpu"
        
        # Charger le modèle Whisper
        model_name = "openai/whisper-base"  # Modèle plus léger pour les tests
        self.processor = WhisperProcessor.from_pretrained(model_name)
        self.model = WhisperForConditionalGeneration.from_pretrained(model_name)
        self.model.to(self.device)
        
        self.sample_rate = 16000
        print(f"STT Handler initialisé avec Whisper sur {self.device}")

    def listen_and_transcribe(self, duration=5):
        """Écoute le microphone pendant une durée donnée et transcrit le son."""
        print("🎤 Écoute en cours...")
        audio_data = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()  # Attendre la fin de l'enregistrement
        print("🎤 Enregistrement terminé, transcription en cours...")
        
        # Préparer l'audio pour Whisper
        audio_input = audio_data.flatten()
        
        # Traitement avec Whisper
        input_features = self.processor(
            audio_input, 
            sampling_rate=self.sample_rate, 
            return_tensors="pt"
        ).input_features.to(self.device)
        
        # Génération du texte
        with torch.no_grad():
            predicted_ids = self.model.generate(input_features)
            transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        
        print(f"Transcription: '{transcription}'")
        return transcription 