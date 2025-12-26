"""Simple config loader/saver for AIToolsIDE."""
import json

DEFAULT = {
    "webview_theme": "light",
    "menu_items": {"stable_diffusion": {"name": "Stable Diffusion", "url": "http://127.0.0.1:7860"}}
}

def load(path):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        pass
    return DEFAULT.copy()

def save(path, cfg: dict):
    try:
        if not path.exists():
            # なければ作る
            with open(str(path),"w"):pass
        path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
        return
    except Exception:
        pass
