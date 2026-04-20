from langchain_ollama import ChatOllama


def get_llm(model: str, temperature: float = 0.1) -> ChatOllama:
    return ChatOllama(
        model=model,
        temperature=temperature,
    )