# スクリーンショットの撮影手順

READMEに画像を足すための手順です。画像は `docs/images/` に置き、READMEから相対パスで参照します。
**撮影するのはダミーデータの画面だけ**です（実データは使わない）。

## 事前準備

1. 保存先を、ユーザー名が入らない場所にします（例: `C:\demo\`）。
   GUIの完了表示とファイル選択ダイアログに、保存先のフルパスが出るためです。
2. 手順どおりに仮想環境を作り、`pip install -r requirements.txt` を済ませます。
3. Windowsの「Win + Shift + S」（切り取りとスケッチ）で範囲を指定して撮影し、PNGで保存します。

## 撮る画像（優先順）

| # | ファイル名 | 撮り方 | 見せたいこと |
|---|---|---|---|
| 1 | `excel-daily.png` | `python attendance.py sample_attendance.csv C:\demo\out.xlsx --config config.json` で出力 → Excelで開いて「日別明細」シートを表示 | 警告行の黄色表示と備考欄 |
| 2 | `gui-main.png` | `python gui.py` を起動し、CSVを選んだ状態 | GUIの全体像 |
| 3 | `gui-done.png` | 「集計してExcel保存」を押した後の完了ダイアログ | 件数表示 |
| 4 | `excel-warnings.png` | 同じxlsxの「警告一覧」シート | 警告の種類と文言（行番号付き） |
| 5 | `gui-error.png` | 列名を `休憩(分)` → `休憩` に直したCSVを選んで実行 | 入力検証のエラー表示 |
| 6 | `test-run.png` | `python -m unittest -v` を実行したターミナル | テストの実測結果 |

## 撮影後のチェック

- [ ] ユーザー名・個人のフォルダ名・メールアドレスが写っていない（タイトルバー、パス欄、タスクバー含む）
- [ ] 表示されているのはサンプルのダミーデータだけ
- [ ] 画像の幅は1000px程度までに収める（READMEで見やすく、容量も小さい）

## READMEへの追加例

```markdown
![日別明細（警告行は黄色）](docs/images/excel-daily.png)
![GUI](docs/images/gui-main.png)
```

追加する画像は、実際に撮影したものだけを参照してください。ファイルが無いまま参照すると、GitHub上で画像が表示されません。
