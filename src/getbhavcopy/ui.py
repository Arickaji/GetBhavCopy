import json as js
import logging
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import StringVar, filedialog, messagebox
from typing import Any

import customtkinter as ctk

from getbhavcopy.core import GetBhavCopy
from getbhavcopy.logging_config import setup_logging
from getbhavcopy.settings_windows import SettingsWindow

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("dark-blue")

setup_logging(debug=True)

logger = logging.getLogger("getbhavcopy")


def get_config_path() -> Path:
    appdata = os.getenv("APPDATA")
    base = Path(appdata) / "GetBhavCopy" if appdata else Path.home() / ".getbhavcopy"
    base.mkdir(parents=True, exist_ok=True)
    return base / "SaveDirPath.json"


def load_config() -> Any:
    path = get_config_path()
    if not path.exists():
        default = {"DirPath": str(Path.cwd()), "theme": "system", "format": "TXT"}
        path.write_text(js.dumps(default, indent=2))
        return default
    return js.loads(path.read_text())


def save_config(cfg: dict) -> None:
    path = get_config_path()
    path.write_text(js.dumps(cfg, indent=2))


def open_folder(path: Path) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.call(["open", str(path)])
        else:
            subprocess.call(["xdg-open", str(path)])
    except Exception as e:
        logger.error(f"Could not open folder automatically: {e}")


class TkinterLogHandler(logging.Handler):
    def __init__(self, text_widget: ctk.CTkTextbox) -> None:
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)

        def append() -> None:
            self.text_widget.configure(state="normal")
            if record.levelno >= logging.ERROR:
                self.text_widget.insert("end", msg + "\n", "ERROR")
            elif record.levelno >= logging.WARNING:
                self.text_widget.insert("end", msg + "\n", "WARNING")
            else:
                self.text_widget.insert("end", msg + "\n")
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")

        self.text_widget.after(0, append)


class ProgressAdapter:
    def __init__(self, bar: ctk.CTkProgressBar) -> None:
        self._bar = bar

    def __setitem__(self, key: str, value: int) -> None:
        if key == "value":
            self._bar.set(value / 100)


class App:
    # ── Colours ───────────────────────────────────────────────────────
    BG = "#1a1a1a"
    BG2 = "#232323"
    BG3 = "#2d2d2d"
    FG = "#ffffff"
    FG2 = "#aaaaaa"
    FG3 = "#666666"
    SEP = "#2a2a2a"
    ACCENT = "#1a3a1a"
    ACCENT_FG = "#80ff80"
    FONT = (
        "SF Pro"
        if sys.platform == "darwin"
        else "Segoe UI"
        if sys.platform == "win32"
        else "Ubuntu"
    )

    def __init__(self) -> None:
        self.root = ctk.CTk()
        self.root.title("GetBhavCopy Downloader - NSE EQ Cash Segment - By Aric Kaji")
        # self.root.resizable(False, False)
        self.root.configure(fg_color=self.BG)

        self._cfg = load_config()
        self._apply_theme(self._cfg.get("theme", "system"))
        self._center_window(720, 600)

        self._build_ui()
        self._connect_logger()

        logger.info("UI logging initialized successfully.")

    def _apply_theme(self, mode: str) -> None:
        ctk.set_appearance_mode(mode)
        self._cfg["theme"] = mode
        save_config(self._cfg)

    def _center_window(self, w: int, h: int) -> None:
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def run(self) -> None:
        self.root.mainloop()

    def _build_ui(self) -> None:
        self._build_titlebar()
        self._build_date_section()
        self._build_output_section()
        self._build_progress()
        self._build_buttons()
        self._build_statusbar()
        self._build_logs()

    def _build_titlebar(self) -> None:
        bar = ctk.CTkFrame(self.root, fg_color=self.SEP, height=1, corner_radius=0)
        bar.pack(fill="x", padx=0, pady=0)

        main = ctk.CTkFrame(self.root, fg_color=self.BG, corner_radius=0)
        main.pack(fill="x", padx=36, pady=(20, 0))

        # Left — app name and subtitle
        left = ctk.CTkFrame(main, fg_color=self.BG, corner_radius=0)
        left.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            left,
            text="GetBhavCopy",
            font=(self.FONT, 22, "bold"),
            text_color=self.FG,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="NSE Equity & Indices Data Extraction Tool",
            font=(self.FONT, 12),
            text_color=self.FG3,
            anchor="w",
        ).pack(anchor="w")

        # Right — theme toggle and version badge
        right = ctk.CTkFrame(main, fg_color=self.BG, corner_radius=0)
        right.pack(side="right")

        self._theme_btn = ctk.CTkButton(
            right,
            text="☀ Light",
            font=(self.FONT, 11),
            fg_color=self.BG3,
            text_color=self.FG2,
            hover_color="#3a3a3a",
            corner_radius=6,
            width=80,
            height=28,
            command=self._toggle_theme,
        )
        self._theme_btn.pack(side="right", padx=(8, 0))

        ctk.CTkLabel(
            right,
            text="v1.0.5",
            font=(self.FONT, 11),
            fg_color=self.BG3,
            text_color=self.FG3,
            corner_radius=6,
            width=60,
            height=28,
        ).pack(side="right")

        # Separator line below header
        ctk.CTkFrame(self.root, fg_color=self.SEP, height=1, corner_radius=0).pack(
            fill="x", padx=36, pady=(12, 0)
        )

    def _toggle_theme(self) -> None:
        current = self._cfg.get("theme", "system")
        if current == "dark":
            new_theme = "light"
            btn_text = "☀ Light"
        elif current == "light":
            new_theme = "system"
            btn_text = "⚙ System"
        else:
            new_theme = "dark"
            btn_text = "☾ Dark"
        self._apply_theme(new_theme)
        self._theme_btn.configure(text=btn_text)

    def _build_date_section(self) -> None:
        outer = ctk.CTkFrame(self.root, fg_color=self.BG, corner_radius=0)
        outer.pack(fill="x", padx=36, pady=(16, 0))

        ctk.CTkLabel(
            outer,
            text="DATE RANGE",
            font=(self.FONT, 10, "bold"),
            text_color=self.FG3,
            anchor="w",
        ).pack(anchor="w", pady=(0, 6))

        row = ctk.CTkFrame(outer, fg_color=self.BG, corner_radius=0)
        row.pack(fill="x")
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        # Start date card
        start = ctk.CTkFrame(row, fg_color=self.BG2, corner_radius=8)
        start.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(
            start,
            text="Start Date",
            font=(self.FONT, 10),
            text_color=self.FG3,
            anchor="w",
        ).pack(anchor="w", padx=14, pady=(8, 2))

        fields_start = ctk.CTkFrame(start, fg_color=self.BG2, corner_radius=0)
        fields_start.pack(fill="x", padx=14, pady=(0, 10))

        currentDate = datetime.today().strftime("%d-%m-%Y")
        parts = currentDate.split("-")

        self._day = StringVar(value=parts[0])
        self._month = StringVar(value=parts[1])
        self._year = StringVar(value=parts[2])

        self._day.trace("w", self._limit_day)
        self._month.trace("w", self._limit_month)
        self._year.trace("w", self._limit_year)

        self._day_entry = self._date_field(fields_start, self._day, 4)
        self._day_entry.pack(side="left")

        ctk.CTkLabel(
            fields_start,
            text="/",
            font=(self.FONT, 14),
            text_color=self.FG3,
            fg_color=self.BG2,
        ).pack(side="left", padx=4)

        self._month_entry = self._date_field(fields_start, self._month, 4)
        self._month_entry.pack(side="left")

        ctk.CTkLabel(
            fields_start,
            text="/",
            font=(self.FONT, 14),
            text_color=self.FG3,
            fg_color=self.BG2,
        ).pack(side="left", padx=4)

        self._year_entry = self._date_field(fields_start, self._year, 6)
        self._year_entry.pack(side="left")

        # End date card
        end = ctk.CTkFrame(row, fg_color=self.BG2, corner_radius=8)
        end.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ctk.CTkLabel(
            end,
            text="End Date",
            font=(self.FONT, 10),
            text_color=self.FG3,
            anchor="w",
        ).pack(anchor="w", padx=14, pady=(8, 2))

        fields_end = ctk.CTkFrame(end, fg_color=self.BG2, corner_radius=0)
        fields_end.pack(fill="x", padx=14, pady=(0, 10))

        self._eday = StringVar(value=parts[0])
        self._emonth = StringVar(value=parts[1])
        self._eyear = StringVar(value=parts[2])

        self._eday.trace("w", self._limit_eday)
        self._emonth.trace("w", self._limit_emonth)
        self._eyear.trace("w", self._limit_eyear)

        self._eday_entry = self._date_field(fields_end, self._eday, 4)
        self._eday_entry.pack(side="left")

        ctk.CTkLabel(
            fields_end,
            text="/",
            font=(self.FONT, 14),
            text_color=self.FG3,
            fg_color=self.BG2,
        ).pack(side="left", padx=4)

        self._emonth_entry = self._date_field(fields_end, self._emonth, 4)
        self._emonth_entry.pack(side="left")

        ctk.CTkLabel(
            fields_end,
            text="/",
            font=(self.FONT, 14),
            text_color=self.FG3,
            fg_color=self.BG2,
        ).pack(side="left", padx=4)

        self._eyear_entry = self._date_field(fields_end, self._eyear, 6)
        self._eyear_entry.pack(side="left")

    def _date_field(
        self, parent: ctk.CTkFrame, var: StringVar, width: int
    ) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            parent,
            textvariable=var,
            width=width * 10,
            font=(self.FONT, 13, "bold"),
            justify="center",
            fg_color=self.BG3,
            text_color=self.FG,
            border_width=0,
            corner_radius=6,
        )

    def _limit_day(self, *args: object) -> None:
        v = self._day.get()
        if v and (not v.isdigit() or int(v) > 31):
            self._day.set("")
        elif len(v) > 2:
            self._day.set(v[:2])
        elif len(v) == 2:
            self._month_entry.focus()
            self._month_entry.icursor("end")

    def _limit_month(self, *args: object) -> None:
        v = self._month.get()
        if v and (not v.isdigit() or int(v) > 12):
            self._month.set("")
        elif len(v) > 2:
            self._month.set(v[:2])
        elif len(v) == 2:
            self._year_entry.focus()
            self._year_entry.icursor("end")

    def _limit_year(self, *args: object) -> None:
        v = self._year.get()
        if v and not v.isdigit():
            self._year.set("")
        elif len(v) > 4:
            self._year.set(v[:4])
        elif len(v) == 4:
            self._eday_entry.focus()
            self._eday_entry.icursor("end")

    def _limit_eday(self, *args: object) -> None:
        v = self._eday.get()
        if v and (not v.isdigit() or int(v) > 31):
            self._eday.set("")
        elif len(v) > 2:
            self._eday.set(v[:2])
        elif len(v) == 2:
            self._emonth_entry.focus()
            self._emonth_entry.icursor("end")

    def _limit_emonth(self, *args: object) -> None:
        v = self._emonth.get()
        if v and (not v.isdigit() or int(v) > 12):
            self._emonth.set("")
        elif len(v) > 2:
            self._emonth.set(v[:2])
        elif len(v) == 2:
            self._eyear_entry.focus()
            self._eyear_entry.icursor("end")

    def _limit_eyear(self, *args: object) -> None:
        v = self._eyear.get()
        if v and not v.isdigit():
            self._eyear.set("")
        elif len(v) > 4:
            self._eyear.set(v[:4])

    def _build_output_section(self) -> None:
        outer = ctk.CTkFrame(self.root, fg_color=self.BG, corner_radius=0)
        outer.pack(fill="x", padx=36, pady=(16, 0))

        ctk.CTkLabel(
            outer,
            text="OUTPUT",
            font=(self.FONT, 10, "bold"),
            text_color=self.FG3,
            anchor="w",
        ).pack(anchor="w", pady=(0, 6))

        row = ctk.CTkFrame(outer, fg_color=self.BG, corner_radius=0)
        row.pack(fill="x")

        # Folder path display
        self._folder_label = ctk.CTkLabel(
            row,
            text="",
            font=(self.FONT, 12),
            text_color=self.FG2,
            fg_color=self.BG2,
            anchor="w",
            corner_radius=8,
            height=40,
        )
        self._folder_label.pack(side="left", fill="x", expand=True, ipady=4)

        # Browse button
        ctk.CTkButton(
            row,
            text="Browse",
            font=(self.FONT, 12),
            fg_color=self.BG3,
            text_color=self.FG2,
            hover_color="#3a3a3a",
            corner_radius=8,
            width=88,
            height=40,
            command=self._get_folder_path,
        ).pack(side="left", padx=(8, 0))

        # Format dropdown
        self._format_var = StringVar(value=self._cfg.get("format", "TXT"))
        self._format_dropdown = ctk.CTkComboBox(
            row,
            variable=self._format_var,
            values=["TXT", "CSV"],
            font=(self.FONT, 12, "bold"),
            fg_color=self.BG3,
            text_color=self.FG,
            button_color=self.BG3,
            button_hover_color="#3a3a3a",
            border_color=self.BG3,
            dropdown_fg_color=self.BG3,
            dropdown_text_color=self.FG,
            dropdown_hover_color="#3a3a3a",
            corner_radius=8,
            width=80,
            height=40,
            state="readonly",
            command=self._on_format_change,
        )
        self._format_dropdown.pack(side="left", padx=(8, 0))

        # Load saved folder path
        saved_path = self._cfg.get("DirPath", str(Path.cwd()))
        self._folder_label.configure(text=f"  {saved_path}")
        self._current_folder = saved_path

    def _get_folder_path(self) -> None:
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self._folder_label.configure(text=f"  {path}")
            self._current_folder = path
            self._cfg["DirPath"] = path
            save_config(self._cfg)

    def _on_format_change(self, value: str) -> None:
        self._cfg["format"] = value
        save_config(self._cfg)

    def _build_progress(self) -> None:
        outer = ctk.CTkFrame(self.root, fg_color=self.BG, corner_radius=0)
        outer.pack(fill="x", padx=36, pady=(16, 0))

        self._progress = ctk.CTkProgressBar(
            outer,
            orientation="horizontal",
            mode="determinate",
            height=6,
            corner_radius=3,
            fg_color=self.BG2,
            progress_color="#4CAF50",
        )
        self._progress.pack(fill="x")
        self._progress.set(0)

    def _build_buttons(self) -> None:
        outer = ctk.CTkFrame(self.root, fg_color=self.BG, corner_radius=0)
        outer.pack(fill="x", padx=36, pady=(12, 0))

        self._get_data_btn = ctk.CTkButton(
            outer,
            text="↓  Get Data",
            font=(self.FONT, 13, "bold"),
            fg_color=self.ACCENT,
            text_color=self.ACCENT_FG,
            hover_color="#2a5a2a",
            corner_radius=8,
            height=40,
            command=self._start_download,
        )
        self._get_data_btn.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            outer,
            text="Clear Logs",
            font=(self.FONT, 13),
            fg_color=self.BG3,
            text_color=self.FG2,
            hover_color="#3a3a3a",
            corner_radius=8,
            height=40,
            command=self._clear_logs,
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

        ctk.CTkButton(
            outer,
            text="⚙  Settings",
            font=(self.FONT, 13),
            fg_color=self.BG3,
            text_color=self.FG2,
            hover_color="#3a3a3a",
            corner_radius=8,
            height=40,
            command=lambda: SettingsWindow(self.root),
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

        ctk.CTkButton(
            outer,
            text="Exit",
            font=(self.FONT, 13),
            fg_color=self.BG3,
            text_color=self.FG2,
            hover_color="#3a3a3a",
            corner_radius=8,
            height=40,
            command=self.root.destroy,
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def _build_logs(self) -> None:
        outer = ctk.CTkFrame(self.root, fg_color=self.BG, corner_radius=0)
        outer.pack(fill="both", expand=True, padx=36, pady=(16, 0))

        ctk.CTkLabel(
            outer,
            text="APPLICATION LOGS",
            font=(self.FONT, 10, "bold"),
            text_color=self.FG3,
            anchor="w",
        ).pack(anchor="w", pady=(0, 6))

        self._log_box = ctk.CTkTextbox(
            outer,
            font=("JetBrains Mono", 11),
            fg_color="#0f0f0f",
            text_color="#d4d4d4",
            corner_radius=8,
            wrap="none",
            state="disabled",
        )
        self._log_box.pack(fill="both", expand=True)

        self._log_box.tag_config("ERROR", foreground="#ff4d4d")
        self._log_box.tag_config("WARNING", foreground="#ffa500")

    def _build_statusbar(self) -> None:
        bar = ctk.CTkFrame(
            self.root,
            fg_color=self.SEP,
            height=32,
            corner_radius=0,
        )
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self._status_var = StringVar(value="Status: Ready")

        ctk.CTkLabel(
            bar,
            textvariable=self._status_var,
            font=(self.FONT, 11),
            text_color=self.FG3,
            anchor="w",
        ).pack(side="left", padx=16)

        ctk.CTkLabel(
            bar,
            text="By Aric Kaji",
            font=(self.FONT, 11),
            text_color=self.FG3,
            anchor="e",
        ).pack(side="right", padx=16)

    def _connect_logger(self) -> None:
        handler = TkinterLogHandler(self._log_box)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    def _clear_logs(self) -> None:
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    def _start_download(self) -> None:
        thread = threading.Thread(target=self._handle_get_data)
        thread.daemon = True
        thread.start()

    def _handle_get_data(self) -> None:
        self._get_data_btn.configure(state="disabled")
        self._status_var.set("Status: Downloading data...")
        self.root.update_idletasks()

        starting_date = (
            self._year.get() + "-" + self._month.get() + "-" + self._day.get()
        )
        ending_date = (
            self._eyear.get() + "-" + self._emonth.get() + "-" + self._eday.get()
        )

        logger.info(f"User requested download: {starting_date} -> {ending_date}")

        b = GetBhavCopy(
            starting_date,
            ending_date,
            self._current_folder,
            self._format_var.get(),
            ProgressAdapter(self._progress),
            self.root,
        )

        try:
            b.get_bhavcopy()
        except ValueError as e:
            logger.warning(f"User input error: {e}")
            messagebox.showwarning("Invalid Input", str(e))
            self._get_data_btn.configure(state="normal")
            self._status_var.set("Status: Download Failed")
            return
        except Exception:
            logger.exception("Unexpected download error")
            messagebox.showerror(
                "Download Failed",
                "Something went wrong while downloading.\nPlease check the logs.",
            )
            self._get_data_btn.configure(state="normal")
            self._status_var.set("Status: Download Failed")
            return

        self._progress.set(1.0)
        self.root.update_idletasks()

        out_dir = Path(self._current_folder)
        skipped = getattr(b, "failed_dates", [])

        message = "BhavCopy files downloaded successfully."
        if skipped:
            message += f"\n\nSkipped dates (holiday/unavailable): {len(skipped)}"

        if messagebox.showinfo("GetBhavCopy", message):
            self._progress.set(0.0)
            if messagebox.askyesno(
                "GetBhavCopy", "Do you want to open the download folder?"
            ):
                open_folder(out_dir)

        self._status_var.set("Status: Completed")
        self._get_data_btn.configure(state="normal")


if __name__ == "__main__":
    app = App()
    app.run()
