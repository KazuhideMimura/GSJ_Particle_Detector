# 「砂つぶ」自動鑑定システム物体検出アプリケーション


## 開発環境の構築

事前にyolov9実行環境を構築しておく

```Anaconda PowerShell
PS> conda activate yolov9-dev
(yolov9-dev) PS> pip install -e src[dev]
```

## パッケージのビルド

### GUIリソースファイルのコンパイル

※以下のコマンドは `src/gsjpd` フォルダ内で実行

```Anaconda PowerShell
# 翻訳ファイルの更新
(yolov9-dev) PS> pyside6-lupdate -extensions py -target-language ja -locations absolute -recursive "@sources.list" -ts _resource\translations.ja.ts

# 翻訳ファイルのコンパイル
(yolov9-dev) PS> pyside6-lrelease _resource\translations.ja.ts -qm _resource\translations.ja.qm

# リソースファイルのコンパイル
(yolov9-dev) PS> pyside6-rcc -o application_rc.py _resource\.qrc
```

### Wheelファイルのビルド

※以下のコマンドは `src` フォルダ内で実行

```Anaconda PowerShell
(yolov9-dev) PS> python -m build --wheel
```

### 依存パッケージのダウンロード（オフラインインストール用）

※以下のコマンドは `src` フォルダ内で実行

```Anaconda PowerShell
(yolov9-dev) PS> pip download --dest "dist" .
```


## パッケージのインストール

```Anaconda PowerShell
(yolov9) PS> pip install --no-index --find-links="dist" GSJParticleDetector
```

