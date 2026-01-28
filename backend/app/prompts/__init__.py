from pathlib import Path

PROMPT_DIR = Path(__file__).parent

def load_prompt(name: str) -> str:
    """
    Load a prompt text file from the prompts directory.
    """
    path = PROMPT_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")

    return path.read_text(encoding="utf-8")