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


if __name__ == "__main__":
    client = AIClient()
    response = client.complete(
        system_prompt="You are Gravity, an AI goal tracking assistant. Be direct and intelligent.",
        messages=[{"role": "user", "content": "Say exactly this and nothing else: AIClient is working."}]
    )
    print(response)
