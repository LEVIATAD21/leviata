"""
Provedores de LLM Modulares
Adicione qualquer API compatível com OpenAI ou implemente a interface base.
"""
from abc import ABC, abstractmethod
from typing import List, Dict
import base64
import mimetypes
from pathlib import Path


class BaseLLMProvider(ABC):
    """Interface base para todos os provedores de LLM."""
    
    @abstractmethod
    def generate(self, system: str, messages: List[Dict[str, str]]) -> str:
        pass

    def generate_multimodal(self, system: str, prompt: str, image_paths: List[str]) -> str:
        raise NotImplementedError("Este provedor não oferece análise de imagens nesta configuração.")


def _data_url(path: str) -> str:
    file_path = Path(path).expanduser()
    mime = mimetypes.guess_type(file_path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


class OpenAIProvider(BaseLLMProvider):
    """Provedor para OpenAI (GPT-4, GPT-4o, etc.)"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = None):
        from openai import OpenAI
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model = model

    def generate(self, system: str, messages: List[Dict[str, str]]) -> str:
        all_messages = [{"role": "system", "content": system}] + messages
        response = self.client.chat.completions.create(
            model=self.model,
            messages=all_messages,
            max_tokens=4096
        )
        return response.choices[0].message.content

    def generate_multimodal(self, system: str, prompt: str, image_paths: List[str]) -> str:
        content = [{"type": "text", "text": prompt}]
        content.extend({"type": "image_url", "image_url": {"url": _data_url(path)}} for path in image_paths)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
            max_tokens=4096,
        )
        return response.choices[0].message.content


class AnthropicProvider(BaseLLMProvider):
    """Provedor para Anthropic (Claude 3.5, Claude 4, etc.)"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate(self, system: str, messages: List[Dict[str, str]]) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=messages
        )
        return response.content[0].text

    def generate_multimodal(self, system: str, prompt: str, image_paths: List[str]) -> str:
        content = [{"type": "text", "text": prompt}]
        for path in image_paths:
            file_path = Path(path).expanduser()
            mime = mimetypes.guess_type(file_path.name)[0] or "image/jpeg"
            content.append({"type": "image", "source": {"type": "base64", "media_type": mime, "data": base64.b64encode(file_path.read_bytes()).decode("ascii")}})
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": content}],
        )
        return response.content[0].text


class GoogleProvider(BaseLLMProvider):
    """Provedor para Google Gemini (gemini-1.5-pro, gemini-2.0-flash, etc.)"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model_name = model
        self.system = ""

    def generate(self, system: str, messages: List[Dict[str, str]]) -> str:
        import google.generativeai as genai
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system
        )
        # Converte histórico para formato Gemini
        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})
        
        chat = model.start_chat(history=history)
        response = chat.send_message(messages[-1]["content"])
        return response.text

    def generate_multimodal(self, system: str, prompt: str, image_paths: List[str]) -> str:
        from PIL import Image
        model = genai.GenerativeModel(model_name=self.model_name, system_instruction=system)
        parts = [prompt]
        opened = []
        try:
            for path in image_paths:
                image = Image.open(Path(path).expanduser())
                opened.append(image)
                parts.append(image)
            response = model.generate_content(parts)
            return response.text
        finally:
            for image in opened:
                image.close()


class OllamaProvider(BaseLLMProvider):
    """Provedor para Ollama (modelos locais: llama3, mistral, etc.)"""
    
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate(self, system: str, messages: List[Dict[str, str]]) -> str:
        from openai import OpenAI
        client = OpenAI(
            api_key="ollama",
            base_url=f"{self.base_url}/v1"
        )
        all_messages = [{"role": "system", "content": system}] + messages
        response = client.chat.completions.create(
            model=self.model,
            messages=all_messages
        )
        return response.choices[0].message.content

    def generate_multimodal(self, system: str, prompt: str, image_paths: List[str]) -> str:
        from openai import OpenAI
        client = OpenAI(api_key="ollama", base_url=f"{self.base_url}/v1")
        content = [{"type": "text", "text": prompt}]
        content.extend({"type": "image_url", "image_url": {"url": _data_url(path)}} for path in image_paths)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
            max_tokens=4096,
        )
        return response.choices[0].message.content


class CustomAPIProvider(BaseLLMProvider):
    """Provedor genérico para qualquer API compatível com OpenAI."""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate(self, system: str, messages: List[Dict[str, str]]) -> str:
        all_messages = [{"role": "system", "content": system}] + messages
        response = self.client.chat.completions.create(
            model=self.model,
            messages=all_messages,
            max_tokens=4096
        )
        return response.choices[0].message.content

    def generate_multimodal(self, system: str, prompt: str, image_paths: List[str]) -> str:
        content = [{"type": "text", "text": prompt}]
        content.extend({"type": "image_url", "image_url": {"url": _data_url(path)}} for path in image_paths)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
            max_tokens=4096,
        )
        return response.choices[0].message.content


def get_provider(config: dict) -> BaseLLMProvider:
    """Fábrica de provedores baseada na configuração."""
    provider_name = config.get("provider", "openai").lower()
    
    providers = {
        "openai": lambda: OpenAIProvider(
            api_key=config["api_key"],
            model=config.get("model", "gpt-4o"),
            base_url=config.get("base_url")
        ),
        "anthropic": lambda: AnthropicProvider(
            api_key=config["api_key"],
            model=config.get("model", "claude-3-5-sonnet-20241022")
        ),
        "google": lambda: GoogleProvider(
            api_key=config["api_key"],
            model=config.get("model", "gemini-2.0-flash")
        ),
        "ollama": lambda: OllamaProvider(
            model=config.get("model", "llama3"),
            base_url=config.get("base_url", "http://localhost:11434")
        ),
        "custom": lambda: CustomAPIProvider(
            api_key=config["api_key"],
            base_url=config["base_url"],
            model=config["model"]
        ),
    }
    
    if provider_name not in providers:
        raise ValueError(f"Provedor '{provider_name}' não suportado. Opções: {list(providers.keys())}")
    
    return providers[provider_name]()
