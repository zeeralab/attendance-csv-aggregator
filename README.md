# 勤怠CSV自動集計ツール

## 使い方
    python attendance.py sample_attendance.csv 結果.xlsx --config config.json

### GUIで使う
    pip install customtkinter openpyxl
    python gui.py
「選択…」でCSVを選び →「集計してExcel保存」→ 保存先を指定。
エラー時（CSV不備・Excelを開いたまま保存など）はメッセージが表示されます。
`config.json` が `gui.py`（exe化後は exe）と同じフォルダにあれば自動で読み込みます。

## 入力CSV（1行＝1勤務ブロック / UTF-8）
社員名,日付,出勤,退勤,休憩(分),現場名
- 退勤が出勤より前なら翌日扱い（日跨ぎ）
- 中抜け・掛け持ちは同じ日に複数行で入力

## 出力Excel
人別集計 / 日別明細 / 警告一覧

## 警告の種類
入力不備（空欄・形式不正） / 出勤＝退勤 / 時間帯重複 / 日跨ぎ勤務 / 長時間勤務

## 注意
- 深夜帯時間は休憩を控除していません（休憩の時間帯が入力にないため）
- 時間帯が重複していても総労働は補正せず、入力値のまま合算して警告します
- 給与の金額計算は行いません

## 検算テスト
    python -m unittest -v        （pytestがあれば python -m pytest -v）

## exe化の手順（PyInstaller）
    pip install pyinstaller customtkinter openpyxl
    pyinstaller --noconsole --onedir --name 勤怠集計 --collect-data customtkinter gui.py

1. `dist/勤怠集計/` フォルダができます。`config.json` をこのフォルダ内の `勤怠集計.exe` の隣にコピーします。
2. 配布は `dist/勤怠集計/` フォルダごとZIPにして渡します。
3. 必ず別PC（Pythonなし）で起動・集計・Excel保存まで動作確認してから渡してください。
4. `--collect-data customtkinter` は必須です（テーマ/画像ファイルが同梱されず、起動時に落ちるのを防ぎます）。
5. 起動しない場合は `--noconsole` を外してビルドし、コンソールのエラーを確認します。

## ウイルス対策ソフトの誤検知について
PyInstaller製のexeは、中身が悪意なくても誤検知されることがあります（特に `--onefile`）。

- **`--onefile` ではなく `--onedir` を使う**（上記の手順どおり。起動時に自己展開しないため誤検知されにくい）
- PyInstallerは**最新版**を使い、ビルドは**クリーンなPC**で行う（古い版のブートローダは検知されやすい）
- UPXによる圧縮は使わない（`--noupx`。圧縮されたexeは疑われやすい）
- 納品前に [VirusTotal](https://www.virustotal.com/) 等で確認し、結果をお客様に共有する
  （※CSVなど顧客データを含むファイルはアップロードしないこと。exe本体のみ）
- 納品時に伝えておく: 「未署名のexeのため、Windows SmartScreenが警告を出す場合があります。
  『詳細情報』→『実行』で起動できます」
- 検知された場合は、お客様のウイルス対策ソフトの**除外設定にフォルダを追加**してもらうか、
  ソースを渡して `python gui.py` で動かす方法を案内する
- 可能なら**コード署名証明書**で署名する（費用がかかるため、本ツールでは未対応）
- バージョンごとにexeを作り直したら、毎回あらためて上記を確認する
