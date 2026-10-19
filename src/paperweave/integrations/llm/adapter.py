"""Provider-neutral LLM adapter contract used by AI proposal workflows."""

from typing import Protocol


class LLMAdapter(Protocol):
    provider: str
    model: str

    def propose(self, *, selected_text: str, instruction: str) -> str: ...
