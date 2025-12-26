@echo off
cd /d %~dp0
if not exist venv (
    python -m venv venv
    venv\Scripts\activate.bat
    pip install -r requirements.txt
    python -m pip install --upgrade pip
    pyinstaller run.py -n AIToolsIDE.exe --clean --onefile --noconsole --add-data="app_icon.ico;." --icon=app_icon.ico
) else (
    venv\Scripts\activate.bat
    pyinstaller run.py -n AIToolsIDE.exe --clean --onefile --noconsole --add-data="app_icon.ico;." --icon=app_icon.ico
)
