"""Lädt die .env-Datei des Projektordners in os.environ.

Nach dem Import steht OPENROUTER_API_KEY allen Skripten zur Verfügung:
    import api_key                # lädt .env beim Import
    key = os.environ["OPENROUTER_API_KEY"]

Vorhandene Umgebungsvariablen werden NICHT überschrieben.
"""
import os
from pathlib import Path

def load_env(env_file: str | Path | None = None, override: bool = False) -> dict[str, str]:
    """Parst eine .env-Datei und setzt die Variablen in os.environ.

    Gibt die geladenen (neu gesetzten) Variablen zurück.
    """
    if env_file is None:
        env_file = Path(__file__).resolve().parent / ".env"
    env_file = Path(env_file)

    if not env_file.exists():
        raise RuntimeError(f".env-Datei nicht gefunden: {env_file}")

    loaded: dict[str, str] = {}
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if override or name not in os.environ:
            os.environ[name] = value
            loaded[name] = value
    return loaded

# Beim Import automatisch laden — danach ist der Key überall verfügbar.
load_env()