"""入力検証のテスト（設定ファイル・CSVヘッダー・氏名なし行）。

test_attendance.py の検算テスト（集計の期待値）とは別ファイル。
ここで確認するのは「不正な入力を黙って通さない」ことだけで、
合理的な設定・入力まで禁止していないことも合わせて確認する。

実行: python -m unittest -v
"""
import tempfile
import unittest
from pathlib import Path

import attendance as at

ROOT = Path(__file__).parent


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def write(self, name: str, text: str, encoding: str = "utf-8") -> Path:
        p = self.tmp / name
        p.write_text(text, encoding=encoding)
        return p


# ---- S1: 設定ファイル ---------------------------------------------------
class TestLoadConfig(TempDirCase):
    def load(self, text: str) -> at.Config:
        return at.load_config(self.write("config.json", text))

    def test_default_when_no_path(self):
        self.assertEqual(at.load_config(None), at.Config())

    def test_bundled_config_json_is_valid(self):
        self.assertEqual(at.load_config(ROOT / "config.json"), at.Config())

    def test_custom_values_are_applied(self):
        cfg = self.load('{"night_start": "21:00", "night_end": "04:30",'
                        ' "daily_limit_hours": 7.5, "long_day_hours": 10}')
        self.assertEqual((cfg.night_start, cfg.night_end), ("21:00", "04:30"))
        self.assertEqual(cfg.daily_limit_min, 450)
        self.assertEqual(cfg.long_day_min, 600)

    def test_reasonable_settings_are_not_rejected(self):
        # 検証は「明らかな誤り」だけを弾く。以下はどれも運用としてあり得る。
        cases = {
            "長時間警告が残業閾値より小さい（独立した閾値）": '{"daily_limit_hours": 8, "long_day_hours": 6}',
            "日をまたがない深夜帯（0:00〜5:00）": '{"night_start": "00:00", "night_end": "05:00"}',
            "残業なし運用（上限24時間超）": '{"daily_limit_hours": 30}',
            "全時間を残業扱い（0時間）": '{"daily_limit_hours": 0}',
            "先頭ゼロなしの時刻": '{"night_start": "22:00", "night_end": "5:00"}',
            "コメント用キー（_始まり）は無視": '{"_comment": "メモ", "daily_limit_hours": 8}',
            "空のオブジェクト": "{}",
        }
        for label, text in cases.items():
            with self.subTest(label):
                self.load(text)

    def test_bom_prefixed_file_is_accepted(self):
        # Windowsのメモ帳で保存するとBOM付きUTF-8になることがある
        p = self.write("bom.json", '{"daily_limit_hours": 7}', encoding="utf-8-sig")
        self.assertEqual(at.load_config(p).daily_limit_hours, 7)

    def test_unknown_key_is_an_error(self):
        with self.assertRaises(at.ConfigError) as cm:
            self.load('{"daily_limit_hour": 7}')       # s の打ち間違い
        self.assertIn("daily_limit_hour", str(cm.exception))

    def test_property_name_is_not_a_valid_key(self):
        # daily_limit_min は Config の属性だが設定項目ではない
        with self.assertRaises(at.ConfigError):
            self.load('{"daily_limit_min": 480}')

    def test_invalid_values_are_errors_naming_the_key(self):
        cases = [
            ("night_start", '{"night_start": "25:00"}'),
            ("night_end", '{"night_end": "abc"}'),
            ("night_start", '{"night_start": 22}'),
            ("daily_limit_hours", '{"daily_limit_hours": "8"}'),
            ("daily_limit_hours", '{"daily_limit_hours": null}'),
            ("daily_limit_hours", '{"daily_limit_hours": true}'),
            ("daily_limit_hours", '{"daily_limit_hours": -1}'),
            ("daily_limit_hours", '{"daily_limit_hours": NaN}'),
            ("long_day_hours", '{"long_day_hours": Infinity}'),
            ("long_day_hours", '{"long_day_hours": -0.5}'),
        ]
        for key, text in cases:
            with self.subTest(text):
                with self.assertRaises(at.ConfigError) as cm:
                    self.load(text)
                self.assertIn(key, str(cm.exception))

    def test_night_start_equal_to_end_is_an_error(self):
        # 同じ時刻だと深夜帯が24時間（または0時間）になり意味を成さない
        with self.assertRaises(at.ConfigError) as cm:
            self.load('{"night_start": "22:00", "night_end": "22:00"}')
        self.assertIn("night_start", str(cm.exception))

    def test_broken_json_is_config_error(self):
        with self.assertRaises(at.ConfigError):
            self.load('{"daily_limit_hours": 8,}')

    def test_top_level_must_be_object(self):
        with self.assertRaises(at.ConfigError):
            self.load("[1, 2]")

    def test_config_error_is_a_value_error(self):
        self.assertTrue(issubclass(at.ConfigError, ValueError))


# ---- S2: CSVヘッダー ----------------------------------------------------
HEADER = "社員名,日付,出勤,退勤,休憩(分),現場名"
ROW = "山田,2026-10-01,09:00,18:00,60,現場A"


class TestCsvHeader(TempDirCase):
    def run_csv(self, text: str, encoding: str = "utf-8"):
        return at.process(self.write("in.csv", text, encoding), at.Config())

    def test_missing_break_column_is_an_error(self):
        # 列名の打ち間違いで休憩が0分扱いになり、8時間が9時間になるのを防ぐ
        with self.assertRaises(at.CsvFormatError) as cm:
            self.run_csv("社員名,日付,出勤,退勤,休憩,現場名\n" + ROW + "\n")
        self.assertIn("休憩(分)", str(cm.exception))

    def test_missing_name_column_is_an_error(self):
        with self.assertRaises(at.CsvFormatError) as cm:
            self.run_csv("名前,日付,出勤,退勤,休憩(分),現場名\n" + ROW + "\n")
        self.assertIn("社員名", str(cm.exception))

    def test_all_missing_columns_are_listed(self):
        with self.assertRaises(at.CsvFormatError) as cm:
            self.run_csv("a,b,c\n1,2,3\n")
        for col in ("社員名", "日付", "出勤", "退勤", "休憩(分)"):
            self.assertIn(col, str(cm.exception))

    def test_empty_file_is_an_error(self):
        with self.assertRaises(at.CsvFormatError):
            self.run_csv("")

    def test_site_column_is_optional(self):
        r = self.run_csv("社員名,日付,出勤,退勤,休憩(分)\n山田,2026-10-01,09:00,18:00,60\n")
        self.assertEqual(r.daily[("山田", at.date(2026, 10, 1))].total_min, 8 * 60)

    def test_column_order_does_not_matter(self):
        r = self.run_csv("現場名,休憩(分),退勤,出勤,日付,社員名\n現場A,60,18:00,09:00,2026-10-01,山田\n")
        self.assertEqual(r.daily[("山田", at.date(2026, 10, 1))].total_min, 8 * 60)

    def test_bom_and_crlf_are_accepted(self):
        # Excelで保存したCSVの典型形（BOM付きUTF-8 / CRLF）
        text = HEADER + "\r\n" + ROW + "\r\n"
        p = self.tmp / "excel.csv"
        p.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
        r = at.process(p, at.Config())
        self.assertEqual(len(r.daily), 1)

    def test_header_only_file_is_not_an_error(self):
        # 勤務が1件もないだけで、形式としては正しい
        r = self.run_csv(HEADER + "\n")
        self.assertEqual((len(r.daily), len(r.warnings)), (0, 0))

    def test_error_is_a_value_error(self):
        self.assertTrue(issubclass(at.CsvFormatError, ValueError))


if __name__ == "__main__":
    unittest.main()
