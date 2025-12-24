"""Simple config loader/saver for AIToolsIDE."""
import json
from pathlib import Path

CONFIG_PATH = Path.home() / '.aitools_ide_config.json'

DEFAULT = {
    "stable_diffusion": "http://127.0.0.1:7861",
    "iopaint": "http://127.0.0.1:8888"
}

def load():
    try:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    except Exception:
        pass
    return DEFAULT.copy()

def save(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
