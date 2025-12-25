"""Simple config loader/saver for AIToolsIDE."""
import json
from pathlib import Path

CONFIG_PATH = Path.home() / '.aitools_ide_config.json'
# prefer project-level config file if present next to package root
PROJECT_CONFIG = Path(__file__).resolve().parents[1] / 'aitools_ide_config.json'

DEFAULT = {
    "stable_diffusion": {"name": "Stable Diffusion WebUI", "url": "http://127.0.0.1:7860"}
}

def load():
    try:
        # prefer repository workspace config if present
        if PROJECT_CONFIG.exists():
            return json.loads(PROJECT_CONFIG.read_text(encoding='utf-8'))
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    except Exception:
        pass
    return DEFAULT.copy()

def save(cfg: dict):
    # write to project config if package exists in a repo, otherwise to user config
    try:
        if PROJECT_CONFIG.parent.exists():
            PROJECT_CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
            return
    except Exception:
        pass
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
