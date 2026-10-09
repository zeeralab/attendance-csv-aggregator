"""勤怠CSV集計ツール GUI（customtkinter）。

CSVを選ぶ → 実行 → Excel保存。集計ロジックは attendance.py の
process() / write_excel() を呼ぶだけで、ここでは一切触らない。
"""
from __future__ import annotations

import sys
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

import attendance


def app_dir() -> Path:
    """config.json を探す基準ディレクトリ（exe化時は exe のある場所）。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("勤怠CSV集計ツール")
        self.geometry("560x260")
        self.resizable(False, False)

        self.csv_path = ctk.StringVar()
        self.status = ctk.StringVar(value="CSVファイルを選んでください。")

        ctk.CTkLabel(self, text="勤怠CSV").grid(row=0, column=0, padx=16, pady=(24, 8), sticky="w")
        ctk.CTkEntry(self, textvariable=self.csv_path, width=340, state="readonly").grid(
            row=0, column=1, pady=(24, 8))
        ctk.CTkButton(self, text="選択…", width=70, command=self.choose_csv).grid(
            row=0, column=2, padx=16, pady=(24, 8))

        self.run_btn = ctk.CTkButton(self, text="集計してExcel保存", height=40, command=self.run)
        self.run_btn.grid(row=1, column=0, columnspan=3, padx=16, pady=16, sticky="ew")

        ctk.CTkLabel(self, textvariable=self.status, wraplength=520, justify="left").grid(
            row=2, column=0, columnspan=3, padx=16, pady=8, sticky="w")

        self.grid_columnconfigure(1, weight=1)

    def choose_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="勤怠CSVを選択", filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")])
        if path:
            self.csv_path.set(path)
            self.status.set("「集計してExcel保存」を押してください。")

    def run(self) -> None:
        src = self.csv_path.get()
        if not src:
            messagebox.showwarning("確認", "先に勤怠CSVを選んでください。")
            return

        default_name = Path(src).stem + "_集計.xlsx"
        out = filedialog.asksaveasfilename(
            title="Excelの保存先", defaultextension=".xlsx", initialfile=default_name,
            filetypes=[("Excelファイル", "*.xlsx")])
        if not out:
            return

        self.run_btn.configure(state="disabled")
        try:
            cfg_file = app_dir() / "config.json"
            cfg = attendance.load_config(cfg_file if cfg_file.exists() else None)
            result = attendance.process(src, cfg)
            attendance.write_excel(result, out)
        except PermissionError:
            self._fail("保存できませんでした。保存先のExcelファイルを開いている場合は閉じてから、もう一度お試しください。")
        except UnicodeDecodeError:
            self._fail("CSVの文字コードを読み取れませんでした。UTF-8で保存し直してください。")
        except Exception as e:  # 想定外も含め、画面にメッセージを出す
            self._fail(f"集計に失敗しました。\n\n{type(e).__name__}: {e}")
        else:
            msg = (f"集計完了: 日別明細{len(result.daily)}件、警告{len(result.warnings)}件\n"
                   f"保存先: {out}")
            self.status.set(msg)
            messagebox.showinfo("完了", msg)
        finally:
            self.run_btn.configure(state="normal")

    def _fail(self, message: str) -> None:
        self.status.set("エラーが発生しました。")
        messagebox.showerror("エラー", message)


def main() -> None:
    ctk.set_appearance_mode("system")
    App().mainloop()


if __name__ == "__main__":
    main()
