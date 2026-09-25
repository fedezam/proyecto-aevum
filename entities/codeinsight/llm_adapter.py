import os
import requests
from dotenv import load_dotenv

load_dotenv("../../../.env")

class LLMSymbiont:
    """
    Adaptador universal para conectar entidades LER al LLM.
    Implementación con API de Moonshot (free).
    """
    def __init__(self, model: str = "moonshot-v1-32k"):
        self.api_key = os.getenv("MOONSHOT_API_KEY")
        if not self.api_key:
            raise ValueError("Falta MOONSHOT_API_KEY en .env")
        self.model = model
        self.base_url = "https://api.moonshot.cn/v1/chat/completions"

    def chat(self, messages, temperature: float = 0.7, max_tokens: int = 2000):
        """
        Envía un prompt al LLM y devuelve la respuesta.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        resp = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise RuntimeError(f"Error procesando respuesta LLM: {data}") from e
