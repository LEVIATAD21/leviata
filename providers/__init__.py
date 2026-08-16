"""
Provedores de LLM Modulares
Adicione qualquer API compatível com OpenAI ou implemente a interface base.
"""
from abc import ABC, abstractmethod
from typing import List, Dict


class BaseLLMProvider(ABC):
    """Interface base para todos os provedores de LLM."""

    @abstractmethod
    def generate(self, system: str, messages: List[Dict[str, str]]) -> str:
        pass


class OpenAIProvider(BaseLLMProvider):
    """Provedor para OpenAI e APIs compatíveis."""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = None, max_output_tokens: int | None = None):
        from openai import OpenAI
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model = model
        self.max_output_tokens = max_output_tokens

    def generate(self, system: str, messages: List[Dict[str, str]]) -> str:
        all_messages = [{"role": "system", "content": system}] + messages
        request = {"model": self.model, "messages": all_messages}
        if self.max_output_tokens:
            request["max_tokens"] = self.max_output_tokens
        response = self.client.chat.completions.create(**request)
        return response.choices[0].message.content


class AnthropicProvider(BaseLLMProvider):
    """Provedor para Anthropic (Claude 3.5, Claude 4, etc.)."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", max_output_tokens: int | None = None):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_output_tokens = max_output_tokens

    def generate(self, system: str, messages: List[Dict[str, str]]) -> str:
        # O SDK Anthropic exige max_tokens; o valor configurável é usado quando fornecido.
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_output_tokens or 8192,
            system=system,
            messages=messages,
        )
        return response.content[0].text


class GoogleProvider(BaseLLMProvider):
    """Provedor para Google Gemini."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", max_output_tokens: int | None = None):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model_name = model
        self.max_output_tokens = max_output_tokens
        self.system = ""

    def generate(self, system: str, messages: List[Dict[str, str]]) -> str:
        import google.generativeai as genai
        model_kwargs = {"model_name": self.model_name, "system_instruction": system}
        if self.max_output_tokens:
            model_kwargs["generation_config"] = {"max_output_tokens": self.max_output_tokens}
        model = genai.GenerativeModel(**model_kwargs)
        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})
        chat = model.start_chat(history=history)
        response = chat.send_message(messages[-1]["content"])
        return response.text


class OllamaProvider(BaseLLMProvider):
    """Provedor para Ollama e inferência local."""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate(self, system: str, messages: List[Dict[str, str]]) -> str:
        from openai import OpenAI
        client = OpenAI(api_key="ollama", base_url=f"{self.base_url}/v1")
        all_messages = [{"role": "system", "content": system}] + messages
        response = client.chat.completions.create(model=self.model, messages=all_messages)
        return response.choices[0].message.content


class CustomAPIProvider(BaseLLMProvider):
    """Provedor genérico para qualquer API compatível com OpenAI."""

    def __init__(self, api_key: str, base_url: str, model: str, max_output_tokens: int | None = None):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_output_tokens = max_output_tokens

    def generate(self, system: str, messages: List[Dict[str, str]]) -> str:
        all_messages = [{"role": "system", "content": system}] + messages
        request = {"model": self.model, "messages": all_messages}
        if self.max_output_tokens:
            request["max_tokens"] = self.max_output_tokens
        response = self.client.chat.completions.create(**request)
        return response.choices[0].message.content


def get_provider(config: dict) -> BaseLLMProvider:
    """Fábrica de provedores baseada na configuração."""
    provider_name = config.get("provider", "openai").lower()
    max_output_tokens = config.get("max_output_tokens")

    providers = {
        "openai": lambda: OpenAIProvider(
            api_key=config["api_key"], model=config.get("model", "gpt-4o"),
            base_url=config.get("base_url"), max_output_tokens=max_output_tokens,
        ),
        "anthropic": lambda: AnthropicProvider(
            api_key=config["api_key"], model=config.get("model", "claude-3-5-sonnet-20241022"),
            max_output_tokens=max_output_tokens,
        ),
        "google": lambda: GoogleProvider(
            api_key=config["api_key"], model=config.get("model", "gemini-2.0-flash"),
            max_output_tokens=max_output_tokens,
        ),
        "ollama": lambda: OllamaProvider(
            model=config.get("model", "llama3"), base_url=config.get("base_url", "http://localhost:11434"),
        ),
        "custom": lambda: CustomAPIProvider(
            api_key=config["api_key"], base_url=config["base_url"], model=config["model"],
            max_output_tokens=max_output_tokens,
        ),
    }

    if provider_name not in providers:
        raise ValueError(f"Provedor '{provider_name}' não suportado. Opções: {list(providers.keys())}")
    return providers[provider_name]()
