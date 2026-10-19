"""Deterministic local adapter for exercising the proposal workflow without network access."""


class MockLLMAdapter:
    provider = "mock"
    model = "paperweave-deterministic-mock"

    def propose(self, *, selected_text: str, instruction: str) -> str:
        del instruction
        return f"[Демо-предложение] {selected_text}"
