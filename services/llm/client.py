import os
from langchain_ollama import ChatOllama


def get_llm(model: str, temperature: float = 0.0) -> ChatOllama:
    # Force use of IPv6 localhost to ensure we hit the SSH tunnel 
    # instead of the conflicting local IPv4 daemon.
    base_url = os.environ.get("OLLAMA_HOST", "http://[::1]:11434")
    return ChatOllama(
        base_url=base_url,
        model=model,
        temperature=temperature,
    )