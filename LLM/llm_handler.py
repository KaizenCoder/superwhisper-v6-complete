from llama_cpp import Llama

class LLMHandler:
    def __init__(self, config):
        self.config = config
        self.llm = Llama(
            model_path=config['model_path'],
            n_gpu_layers=config['n_gpu_layers'],
            main_gpu=config['gpu_device_index'],
            verbose=False
        )
        print(f"LLM Handler initialisé avec le modèle {self.config['model_path']}")

    def get_response(self, prompt):
        """Génère une réponse à partir du prompt."""
        print("🧠 Le LLM réfléchit...")
        output = self.llm(f"Q: {prompt} A: ", max_tokens=100, stop=["Q:", "\n"])
        response_text = output['choices'][0]['text'].strip()
        print(f"Réponse du LLM: '{response_text}'")
        return response_text 