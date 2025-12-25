"""Simple config loader/saver for AIToolsIDE."""
import json
from pathlib import Path

PROJECT_CONFIG = Path(__file__).resolve().parents[1] / 'aitools_ide_config.json'
DEFAULT = {
    "webview_theme": "light",
    "menu_items": {"stable_diffusion": {"name": "Stable Diffusion WebUI", "url": "http://127.0.0.1:7860"}}
}

def load():
    try:
        if PROJECT_CONFIG.exists():
            return json.loads(PROJECT_CONFIG.read_text(encoding='utf-8'))
    except Exception:
        pass
    return DEFAULT.copy()

def save(cfg: dict):
    try:
        if PROJECT_CONFIG.parent.exists():
            PROJECT_CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
            return
    except Exception:
        pass
