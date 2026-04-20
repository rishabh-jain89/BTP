from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AGENTS_DIR = PROJECT_ROOT / "Agents"


def load_agent_config(filename: str, key: str) -> dict:
    path = AGENTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    with path.open("r", encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML structure in {path}")

    if key not in data:
        raise ValueError(f"Missing key '{key}' in {path}")

    agent = data[key]
    if not isinstance(agent, dict):
        raise ValueError(f"Invalid agent config for '{key}' in {path}")

    if "prompt" not in agent or "model" not in agent:
        raise ValueError(f"Agent config '{key}' in {path} must contain 'prompt' and 'model'")

    return agent