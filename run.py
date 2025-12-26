import wx

########################################
# AI Tools IDE
#
# Programming assisted by GPT-5 mini
########################################
import sys
from pathlib import Path
from src import config
from src import main_frame

def config_path(relative_path: str) -> Path:
    if getattr(sys, 'frozen', False):
        # PyInstaller exe
        base_path = Path(sys.executable).parent
    else:
        # 通常 python 実行
        base_path = Path(__file__).resolve().parent
    return base_path / relative_path

PROJECT_CONFIG = config_path('aitools_ide_config.json')

def main():
    cfg = config.load(PROJECT_CONFIG)
    app = wx.App(False)
    frame = main_frame.MainFrame(cfg, PROJECT_CONFIG)
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
