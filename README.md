# AIToolsIDE (簡易統合ランチャー)

ローカルで動いている Web ベースのツール（例: Stable Diffusion WebUI、IOPaint など）を
1つのデスクトップアプリケーションにまとめる小さな GUI アプリです。

## セットアップ（Windows 想定）

1. Python 3.8+ を用意してください（プロジェクトは Python 仮想環境での実行を推奨）。
2. 任意で仮想環境を作成・有効化:

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

## 設定ファイル

アプリは設定を次の順で読み込みます:
- プロジェクト（リポジトリ）ルートの `aitools_ide_config.json` を優先
- 存在しない場合はユーザーのホームに `~/.aitools_ide_config.json` を使用

以下のようなフォーマットになっています。
```json
{
	"stable_diffusion": { "name": "Stable Diffusion WebUI", "url": "http://127.0.0.1:7861" },
	"iopaint": { "name": "IOPaint", "url": "http://127.0.0.1:8888" }
}
```
- キー（例: `stable_diffusion`）は内部識別用です。キーが存在しない場合は最初のエントリが選択されます。
- `name` がボタンラベルになっています。設定された内容をそのまま表示します。
- 表示したいツールのURLを `url` に入力してください。

## 設定の編集

- アプリ内の「設定」ボタンでツールを追加・削除・編集できます。
- 保存するとプロジェクトの `aitools_ide_config.json`（存在すれば）に書き戻され、UI が再構築されます。

## 挙動メモ

- 設定が開いている間は WebView を非表示にします。
- 設定中に別ツールに切り替えようとすると、設定をキャンセルした扱いになり元のビューに復帰します。
