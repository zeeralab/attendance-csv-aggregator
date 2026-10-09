"""検算テスト。期待値は「手計算の正解一覧」そのまま。

実行: python -m pytest -v   （pytestが無ければ python -m unittest -v）
"""
import unittest
from datetime import date
from pathlib import Path

import attendance as at

SAMPLE = Path(__file__).parent / "sample_attendance.csv"


def hm(text: str) -> int:
    h, m = text.split(":")
    return int(h) * 60 + int(m)


D = lambda day: date(2026, 10, day)  # noqa: E731

# (社員, 日付): (総労働, 残業, 深夜帯, 警告の種類)
EXPECTED = {
    ("山田", D(1)): ("8:00", "0:00", "0:00", set()),                          # 基本
    ("山田", D(2)): ("9:30", "1:30", "0:00", set()),                          # 残業
    ("佐藤", D(1)): ("8:00", "0:00", "7:00", {at.W_CROSSDAY}),                # 日跨ぎ＋深夜
    ("田中", D(1)): ("6:00", "0:00", "1:00", set()),                          # 中抜け・4〜5時が深夜
    ("鈴木", D(3)): ("10:30", "2:30", "0:00", set()),                         # 掛け持ち
    ("高橋", D(2)): ("8:00", "0:00", "0:00", {at.W_OVERLAP}),                 # 二重勤務
    ("渡辺", D(4)): ("15:00", "7:00", "0:00", {at.W_LONG}),                   # 12時間超・22:00境界
    ("中村", D(5)): ("9:00", "1:00", "7:00", {at.W_CROSSDAY}),                # 日跨ぎ＋残業＋深夜
    ("小林", D(6)): ("0:00", "0:00", "0:00", {at.W_ZERO}),                    # 出勤＝退勤
    ("森", D(6)): ("8:00", "0:00", "7:00", {at.W_CROSSDAY, at.W_OVERLAP}),    # 前日からの日跨ぎ
    ("森", D(7)): ("3:00", "0:00", "0:00", {at.W_OVERLAP}),                   # 5:00ちょうどは深夜に入らない
}


class TestAttendance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = at.process(SAMPLE, at.Config())

    def test_daily_values_and_warnings(self):
        for key, (total, ot, night, kinds) in EXPECTED.items():
            with self.subTest(key=key):
                d = self.result.daily[key]
                self.assertEqual(d.total_min, hm(total), "総労働")
                self.assertEqual(d.overtime_min, hm(ot), "残業")
                self.assertEqual(d.night_min, hm(night), "深夜帯")
                self.assertEqual(self.result.warning_kinds(*key), kinds, "警告")

    def test_no_unexpected_daily_rows(self):
        # 伊藤（退勤空欄）は計算対象外。それ以外は正解一覧と同じ集合
        self.assertEqual(set(self.result.daily), set(EXPECTED))

    def test_blank_clockout_is_excluded_with_warning(self):
        self.assertNotIn(("伊藤", D(2)), self.result.daily)
        self.assertEqual(self.result.warning_kinds("伊藤", D(2)), {at.W_DEFECT})

    def test_overlap_is_counted_twice_not_corrected(self):
        self.assertEqual(self.result.daily[("高橋", D(2))].total_min, hm("8:00"))

    def test_overlap_detected_across_midnight(self):
        # 10/6 22:00〜翌06:00 と 10/7 05:00〜08:00 は 05:00〜06:00 が重複
        details = [w.detail for w in self.result.warnings
                   if w.name == "森" and w.kind == at.W_OVERLAP]
        self.assertTrue(all("10/07 05:00〜10/07 06:00" in t for t in details))
        self.assertEqual(len(details), 2)  # 10/6 と 10/7 の両方に出る

    def test_site_and_break_inputs_do_not_change_night(self):
        # 休憩は深夜帯から控除しない（中村: 休憩60分でも深夜は7:00）
        self.assertEqual(self.result.daily[("中村", D(5))].night_min, hm("7:00"))

    def test_person_summary(self):
        summary = {row[0]: row[1:] for row in self.result.person_summary()}
        self.assertEqual(summary["山田"], (2, hm("17:30"), hm("1:30"), 0))
        self.assertEqual(summary["森"], (2, hm("11:00"), 0, hm("7:00")))


class TestNightMinutes(unittest.TestCase):
    cfg = at.Config()

    def _night(self, s, e):
        from datetime import datetime
        f = "%Y-%m-%d %H:%M"
        return at.night_minutes(datetime.strptime(s, f), datetime.strptime(e, f), self.cfg)

    def test_boundaries(self):
        self.assertEqual(self._night("2026-10-04 06:00", "2026-10-04 22:00"), 0)
        self.assertEqual(self._night("2026-10-07 05:00", "2026-10-07 08:00"), 0)
        self.assertEqual(self._night("2026-10-06 23:30", "2026-10-07 00:30"), 60)
        self.assertEqual(self._night("2026-10-06 18:00", "2026-10-07 01:00"), 180)  # 22〜25時


if __name__ == "__main__":
    unittest.main()
