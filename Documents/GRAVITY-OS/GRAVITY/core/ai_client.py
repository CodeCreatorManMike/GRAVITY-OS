import os
from typing import Any
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


class AICompletion(str):
    """String-compatible AI output carrying provider and token metadata."""

    provider: str
    model: str
    prompt_tokens: int
    output_tokens: int

    def __new__(
        cls,
        content: str,
        *,
        provider: str,
        model: str,
        prompt_tokens: int = 0,
        output_tokens: int = 0,
    ):
        value = super().__new__(cls, content)
        value.provider = provider
        value.model = model
        value.prompt_tokens = prompt_tokens
        value.output_tokens = output_tokens
        return value


def _usage_value(usage: Any, *names: str) -> int:
    for name in names:
        value = getattr(usage, name, None)
        if value is None and isinstance(usage, dict):
            value = usage.get(name)
        if value is not None:
            return int(value)
    return 0

class AIClient:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "groq")

        if self.provider == "groq":
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

        elif self.provider == "ollama":
            import ollama as _ollama
            self._ollama = _ollama
            self.model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
            self._base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            # Point the ollama client at the configured host
            self.client = _ollama.Client(host=self._base_url)

        else:
            raise ValueError(f"Unknown AI provider: {self.provider}")

    def complete(self, system_prompt: str, messages: list, max_tokens: int = 1000) -> str:
        content = ""
        usage: Any = None
        if self.provider == "groq":
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=max_tokens
            )
            content = str(response.choices[0].message.content or "").strip()
            usage = response.usage

        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=messages,
                max_tokens=max_tokens
            )
            content = str(getattr(response.content[0], "text", "")).strip()
            usage = response.usage

        elif self.provider == "ollama":
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            response = self.client.chat(
                model=self.model,
                messages=full_messages,
                options={"num_predict": max_tokens},
            )
            content = response["message"]["content"].strip()
            usage = response

        return AICompletion(
            content,
            provider=self.provider,
            model=self.model,
            prompt_tokens=_usage_value(usage, "prompt_tokens", "input_tokens", "prompt_eval_count"),
            output_tokens=_usage_value(usage, "completion_tokens", "output_tokens", "eval_count"),
        )


if __name__ == "__main__":
    client = AIClient()
    response = client.complete(
        system_prompt="You are Gravity, an AI goal tracking assistant. Be direct and intelligent.",
        messages=[{"role": "user", "content": "Say exactly this and nothing else: AIClient is working."}]
    )
    print(response)
