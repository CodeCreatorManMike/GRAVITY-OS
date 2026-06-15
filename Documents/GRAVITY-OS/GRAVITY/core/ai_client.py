import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

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
        if self.provider == "groq":
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()

        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=messages,
                max_tokens=max_tokens
            )
            return response.content[0].text.strip()

        elif self.provider == "ollama":
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            response = self.client.chat(
                model=self.model,
                messages=full_messages,
                options={"num_predict": max_tokens},
            )
            return response["message"]["content"].strip()


if __name__ == "__main__":
    client = AIClient()
    response = client.complete(
        system_prompt="You are Gravity, an AI goal tracking assistant. Be direct and intelligent.",
        messages=[{"role": "user", "content": "Say exactly this and nothing else: AIClient is working."}]
    )
    print(response)
