# src/llm_client.py
from dataclasses import dataclass
from typing import Optional
from src.config import Config


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int


class LLMClient:
    def __init__(self, provider: str, model: str, api_key: str):
        if provider not in ("claude", "openai"):
            raise ValueError(f"Unsupported provider: {provider}")
        self.provider = provider
        self.model = model
        self.api_key = api_key

    def complete(
        self,
        system: str,
        prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        if self.provider == "claude":
            return self._complete_claude(system, prompt, temperature, max_tokens)
        else:
            return self._complete_openai(system, prompt, temperature, max_tokens)

    def _complete_claude(self, system: str, prompt: str, temperature: float, max_tokens: int) -> LLMResponse:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        return LLMResponse(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def _complete_openai(self, system: str, prompt: str, temperature: float, max_tokens: int) -> LLMResponse:
        import openai

        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return LLMResponse(
            text=response.choices[0].message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )


def create_llm_client(config: Config) -> LLMClient:
    return LLMClient(
        provider=config.llm.provider,
        model=config.llm.model,
        api_key=config.llm.get_api_key(),
    )
