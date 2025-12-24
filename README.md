# AIToolsIDE (簡易統合ランチャー)

ローカルで立ち上がっているWeb系ツール（例: Stable Diffusion WebUI、IOPaint）を1つのデスクトップGUIで開ける簡易アプリです。

セットアップと実行方法（Windows想定）:

1. Python 3.14 を用意してください。
2. 仮想環境を作る（任意）:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. 依存をインストール:

```powershell
pip install -r requirements.txt
```

4. アプリ起動:

```powershell
python run.py
```

初回起動時、デフォルトのURLはホームディレクトリの `~/.aitools_ide_config.json` に保存されます。
