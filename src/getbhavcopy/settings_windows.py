import json
import os
import sys
from pathlib import Path
from tkinter import Canvas, StringVar, messagebox

try:
    import customtkinter as ctk

    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("dark-blue")
    _CTK_AVAILABLE = True
except ImportError:
    _CTK_AVAILABLE = False


def get_mapping_path() -> Path:
    appdata = os.getenv("APPDATA")
    base = Path(appdata) / "GetBhavCopy" if appdata else Path.home() / ".getbhavcopy"
    base.mkdir(parents=True, exist_ok=True)
    return base / "symbol_mapping.json"


def load_symbol_mapping() -> dict:
    path = get_mapping_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {
                str(k).strip().upper(): str(v).strip()
                for k, v in data.items()
                if k and v
            }
    except Exception:
        pass
    return {}


def save_symbol_mapping(mapping: dict) -> None:
    path = get_mapping_path()
    path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")


def load_app_config() -> dict:
    from getbhavcopy.config import load_config

    return load_config()


def save_app_config(cfg: dict) -> None:
    from getbhavcopy.config import save_config

    save_config(cfg)


class SettingsWindow:
    # ── Dark palette ──────────────────────────────────────────────────────────
    DARK = {
        "WIN_BG": "#111111",
        "SB_BG": "#0d0d0d",
        "CONTENT_BG": "#111111",
        "CARD_BG": "#171717",
        "THEAD_BG": "#0d0d0d",
        "FOOTER_BG": "#0d0d0d",
        # text
        "FG1": "#ffffff",
        "FG2": "#cccccc",
        "FG3": "#777777",
        "FG4": "#333333",
        # separators / borders
        "SEP": "#1e1e1e",
        "ROW_SEP": "#161616",
        # nav
        "NAV_ACTIVE_BG": "#1a1a1a",
        "NAV_ACTIVE_FG": "#ffffff",
        "NAV_FG": "#777777",
        "NAV_SOON_FG": "#2e2e2e",
        "NAV_ACCENT": "#3fb950",
        # accent / green
        "ACCENT": "#3fb950",
        "PILL_BG": "#0d1e0d",
        "PILL_BORDER": "#173517",
        # add button
        "ADD_BG": "#0d1e0d",
        "ADD_BORDER": "#173517",
        "ADD_FG": "#3fb950",
        # remove button
        "DEL_BG": "#1e0e0e",
        "DEL_BORDER": "#2a1414",
        "DEL_FG": "#c04040",
        "DEL_HOVER": "#2e1414",
        # info box
        "INFO_BG": "#0b1c0b",
        "INFO_BORDER": "#162616",
        "INFO_FG": "#4a8a4a",
        # save button
        "SAVE_BG": "#142814",
        "SAVE_FG": "#3fb950",
        "SAVE_BORDER": "#1e4a1e",
        "SAVE_HOVER": "#1e3c1e",
        # cancel button
        "CANCEL_FG": "#777777",
        "CANCEL_HOVER": "#1e1e1e",
        # entry
        "ENTRY_BG": "#171717",
        "ENTRY_FG": "#eeeeee",
        "INSERT_BG": "#ffffff",
        "ALT_ROW": "#141414",
        # section label
        "SEC_FG": "#333333",
        # btn hover
        "BTN_HOVER": "#1e1e1e",
        # toggle colours
        "TOGGLE_ON": "#3fb950",
        "TOGGLE_OFF": "#c04040",
    }

    # ── Light palette ─────────────────────────────────────────────────────────
    LIGHT = {
        "WIN_BG": "#ffffff",
        "SB_BG": "#f5f5f5",
        "CONTENT_BG": "#ffffff",
        "CARD_BG": "#f8f8f8",
        "THEAD_BG": "#f5f5f5",
        "FOOTER_BG": "#f5f5f5",
        # text
        "FG1": "#111111",
        "FG2": "#333333",
        "FG3": "#666666",
        "FG4": "#aaaaaa",
        # separators
        "SEP": "#e8e8e8",
        "ROW_SEP": "#f0f0f0",
        # nav
        "NAV_ACTIVE_BG": "#ffffff",
        "NAV_ACTIVE_FG": "#111111",
        "NAV_FG": "#666666",
        "NAV_SOON_FG": "#cccccc",
        "NAV_ACCENT": "#1a6b1a",
        # accent / green
        "ACCENT": "#1a6b1a",
        "PILL_BG": "#eaf5ea",
        "PILL_BORDER": "#c0dcc0",
        # add button
        "ADD_BG": "#eaf5ea",
        "ADD_BORDER": "#c0dcc0",
        "ADD_FG": "#1a6b1a",
        # remove button
        "DEL_BG": "#fdf0f0",
        "DEL_BORDER": "#e8c0c0",
        "DEL_FG": "#cc3333",
        "DEL_HOVER": "#fae0e0",
        # info box
        "INFO_BG": "#eef7ee",
        "INFO_BORDER": "#c0dcc0",
        "INFO_FG": "#2a6a2a",
        # save button
        "SAVE_BG": "#1a5a1a",
        "SAVE_FG": "#ffffff",
        "SAVE_BORDER": "#145014",
        "SAVE_HOVER": "#236023",
        # cancel button
        "CANCEL_FG": "#666666",
        "CANCEL_HOVER": "#eeeeee",
        # entry
        "ENTRY_BG": "#ffffff",
        "ENTRY_FG": "#111111",
        "INSERT_BG": "#111111",
        "ALT_ROW": "#f5f5f5",
        # section label
        "SEC_FG": "#aaaaaa",
        # btn hover
        "BTN_HOVER": "#eeeeee",
        # toggle colours
        "TOGGLE_ON": "#1a6b1a",
        "TOGGLE_OFF": "#cc3333",
    }

    SB_W = 12
    NAV_W = 200

    FONT = (
        "SF Pro"
        if sys.platform == "darwin"
        else "Segoe UI"
        if sys.platform == "win32"
        else "Ubuntu"
    )

    # ─────────────────────────────────────────────────────────────────────────
    def __init__(
        self, parent: object, palette: dict | None = None, on_save: object = None
    ) -> None:
        from tkinter import IntVar, Toplevel

        self._p = palette if palette is not None else self.DARK
        self._par = parent

        self.win = Toplevel()
        self.win.withdraw()
        self.win.title("Preferences — GetBhavCopy")
        self.win.geometry("800x560")
        self.win.minsize(700, 480)
        self.win.resizable(True, True)
        self.win.configure(bg=self._p["WIN_BG"])
        self.win.transient(getattr(parent, "_w", None))

        self._rows: list[tuple[StringVar, StringVar, int]] = []
        self._data_row = 0
        self._workers_var = IntVar(value=load_app_config().get("max_workers", 8))
        self._active_key = "mapping"
        self._panels: dict[str, object] = {}
        self._nav_widgets: dict[str, dict] = {}
        self._on_save_callback = on_save

        from tkinter import BooleanVar
        from tkinter import StringVar as _SV

        cfg = load_app_config()
        self._schedule_enabled = BooleanVar(value=cfg.get("schedule_enabled", False))
        _saved_time = cfg.get("schedule_time", "17:30")
        _t = _saved_time.split(":") if ":" in _saved_time else ["17", "30"]
        self._schedule_hour_var = _SV(value=_t[0].zfill(2))
        self._schedule_min_var = _SV(value=_t[1].zfill(2))

        self._theme_var = _SV(value=cfg.get("theme", "system"))
        self._log_size_var = _SV(value=cfg.get("log_size", "medium"))
        self._filename_prefix_var = _SV(value=cfg.get("filename_pattern", ""))
        self._idx_filename_prefix_var = _SV(value=cfg.get("idx_filename_pattern", ""))
        self._split_files_var = BooleanVar(value=bool(cfg.get("split_eq_idx", False)))

        self._build_root()
        self._load_existing()
        if not self._rows:
            self.add_row()
        self._center(parent)

    # ── window helpers ────────────────────────────────────────────────────────
    def _center(self, parent: object) -> None:
        self.win.update_idletasks()
        w, h = 800, 560
        pw = int(getattr(parent, "winfo_width")())
        ph = int(getattr(parent, "winfo_height")())
        px = int(getattr(parent, "winfo_rootx")())
        py = int(getattr(parent, "winfo_rooty")())
        self.win.geometry(f"{w}x{h}+{px + (pw - w) // 2}+{py + (ph - h) // 2}")
        self.win.after(10, self._show)

    def _show(self) -> None:
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self) -> None:
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            try:
                self.win.unbind_all(ev)
            except Exception:
                pass
        self.win.destroy()

    # ── root layout ───────────────────────────────────────────────────────────
    def _build_root(self) -> None:
        from tkinter import Frame

        # sidebar
        self._sb = Frame(self.win, bg=self._p["SB_BG"], width=self.NAV_W)
        self._sb.pack(side="left", fill="y")
        self._sb.pack_propagate(False)

        Frame(self.win, bg=self._p["SEP"], width=1).pack(side="left", fill="y")

        # right column
        right = Frame(self.win, bg=self._p["CONTENT_BG"])
        right.pack(side="left", fill="both", expand=True)

        self._topbar = Frame(right, bg=self._p["CONTENT_BG"])
        self._topbar.pack(fill="x")

        Frame(right, bg=self._p["SEP"], height=1).pack(fill="x")

        # Footer must be packed BEFORE switcher so it is not pushed out
        Frame(right, bg=self._p["SEP"], height=1).pack(fill="x", side="bottom")
        self._build_footer(right)

        self._switcher = Frame(right, bg=self._p["CONTENT_BG"])
        self._switcher.pack(fill="both", expand=True)
        self._switcher.pack_propagate(False)

        self._build_sidebar()

        # Pre-build ALL panels once — fixes tab-switching delay & bug
        # Pre-build ALL panels using grid — tkraise() switches with zero flicker
        from tkinter import Frame as F

        self._switcher.grid_rowconfigure(0, weight=1)
        self._switcher.grid_columnconfigure(0, weight=1)

        pm = F(self._switcher, bg=self._p["CONTENT_BG"])
        pp = F(self._switcher, bg=self._p["CONTENT_BG"])
        ps = F(self._switcher, bg=self._p["CONTENT_BG"])
        pa = F(self._switcher, bg=self._p["CONTENT_BG"])
        po = F(self._switcher, bg=self._p["CONTENT_BG"])

        for panel in (pm, pp, ps, pa, po):
            panel.grid(row=0, column=0, sticky="nsew")

        self._build_panel_mapping(pm)
        self._build_panel_performance(pp)
        self._build_panel_scheduler(ps)
        self._build_panel_appearance(pa)
        self._build_panel_output(po)
        self._setup_time_validators()
        self._panels = {
            "mapping": pm,
            "performance": pp,
            "scheduler": ps,
            "appearance": pa,
            "output": po,
        }

        self._build_topbar("mapping")
        self.win.after(10, lambda: self._switch("mapping"))

        # # show mapping panel by default without triggering full switch
        # self._panels["mapping"].place(relx=0, rely=0, relwidth=1, relheight=1)
        # self._active_key = "mapping"
        # self._build_topbar("mapping")
        # # style the mapping nav item as active
        # self.win.after(50, lambda: self._switch("mapping"))

    # ── sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self) -> None:
        from tkinter import Frame, Label

        # App name block
        Frame(self._sb, bg=self._p["SB_BG"], height=20).pack()
        Label(
            self._sb,
            text="GetBhavCopy",
            font=(self.FONT, 13, "bold"),
            fg=self._p["FG1"],
            bg=self._p["SB_BG"],
        ).pack(anchor="w", padx=18)
        Label(
            self._sb,
            text="Preferences",
            font=(self.FONT, 10),
            fg=self._p["FG3"],
            bg=self._p["SB_BG"],
        ).pack(anchor="w", padx=18, pady=(3, 16))

        Frame(self._sb, bg=self._p["SEP"], height=1).pack(fill="x", padx=14)
        Frame(self._sb, bg=self._p["SB_BG"], height=10).pack()

        Label(
            self._sb,
            text="GENERAL",
            font=(self.FONT, 9),
            fg=self._p["SEC_FG"],
            bg=self._p["SB_BG"],
        ).pack(anchor="w", padx=18, pady=(0, 6))

        for key, label in [
            ("mapping", "Symbol Mapping"),
            ("performance", "Performance"),
        ]:
            self._nav_item(key, label, disabled=False)

        Frame(self._sb, bg=self._p["SB_BG"], height=6).pack()
        Frame(self._sb, bg=self._p["SEP"], height=1).pack(fill="x", padx=14)
        Frame(self._sb, bg=self._p["SB_BG"], height=10).pack()

        Label(
            self._sb,
            text="AUTOMATION",
            font=(self.FONT, 9),
            fg=self._p["SEC_FG"],
            bg=self._p["SB_BG"],
        ).pack(anchor="w", padx=18, pady=(0, 6))

        for key, label in [
            ("scheduler", "Scheduler"),
            ("output", "Output"),
            ("appearance", "Appearance"),
        ]:
            self._nav_item(key, label, disabled=False)

    def _nav_item(self, key: str, label: str, disabled: bool) -> None:
        from tkinter import Frame, Label

        wrap = Frame(
            self._sb, bg=self._p["SB_BG"], cursor="arrow" if disabled else "hand2"
        )
        wrap.pack(fill="x")

        bar = Frame(wrap, bg=self._p["SB_BG"], width=3)
        bar.pack(side="left", fill="y")

        inner = Frame(wrap, bg=self._p["SB_BG"])
        inner.pack(side="left", fill="x", expand=True, padx=(10, 12), pady=8)

        fg = self._p["NAV_SOON_FG"] if disabled else self._p["NAV_FG"]
        lbl = Label(
            inner,
            text=label,
            font=(self.FONT, 12),
            fg=fg,
            bg=self._p["SB_BG"],
            anchor="w",
        )
        lbl.pack(side="left", fill="x", expand=True)

        # mapping count pill — right-aligned
        pill = None
        if key == "mapping":
            pill = Label(
                inner,
                text="0",
                font=(self.FONT, 10, "bold"),
                fg=self._p["ACCENT"],
                bg=self._p["PILL_BG"],
                padx=7,
                pady=1,
            )
            pill.pack(side="right")

        self._nav_widgets[key] = {
            "wrap": wrap,
            "bar": bar,
            "inner": inner,
            "lbl": lbl,
            "pill": pill,
            "disabled": disabled,
        }

        if not disabled:
            for w in (wrap, bar, inner, lbl):
                w.bind("<Button-1>", lambda e, k=key: self._switch(k))  # type: ignore[misc]
                w.bind("<Enter>", lambda e, k=key: self._hover(k, True))  # type: ignore[misc]
                w.bind("<Leave>", lambda e, k=key: self._hover(k, False))  # type: ignore[misc]

    def _hover(self, key: str, entering: bool) -> None:
        if key == self._active_key:
            return
        nw = self._nav_widgets.get(key, {})
        if nw.get("disabled"):
            return
        bg = self._p["BTN_HOVER"] if entering else self._p["SB_BG"]
        for w in ("wrap", "inner", "lbl"):
            nw[w].configure(bg=bg)

    def _switch(self, key: str) -> None:
        if self._nav_widgets.get(key, {}).get("disabled", False):
            return
        self._active_key = key

        for k, nw in self._nav_widgets.items():
            active = k == key
            disabled = nw.get("disabled", False)
            bg = self._p["NAV_ACTIVE_BG"] if active else self._p["SB_BG"]
            fg = (
                self._p["NAV_ACTIVE_FG"]
                if active
                else self._p["NAV_SOON_FG"]
                if disabled
                else self._p["NAV_FG"]
            )
            bar_bg = self._p["NAV_ACCENT"] if active else self._p["SB_BG"]
            weight = "bold" if active else "normal"

            nw["wrap"].configure(bg=bg)
            nw["inner"].configure(bg=bg)
            nw["bar"].configure(bg=bar_bg)
            nw["lbl"].configure(fg=fg, bg=bg, font=(self.FONT, 12, weight))
            if nw.get("pill"):
                nw["pill"].configure(
                    bg=self._p["PILL_BG"] if active else self._p["SB_BG"]
                )

        # refresh topbar
        for w in self._topbar.winfo_children():
            w.destroy()
        self._build_topbar(key)

        # raise active panel to top — instant, no flicker, no delay
        if key in self._panels:
            panel = self._panels[key]
            getattr(panel, "tkraise")()

    # ── topbar ────────────────────────────────────────────────────────────────
    def _build_topbar(self, key: str) -> None:
        from tkinter import Frame, Label

        titles = {
            "mapping": (
                "Symbol Mapping",
                "Rename NSE symbols and indices in your output files",
            ),
            "performance": (
                "Performance",
                "Configure download speed and threading behaviour",
            ),
            "scheduler": (
                "Scheduler",
                "Auto-download today's bhavcopy at a set time every day",
            ),
            "appearance": (
                "Appearance",
                "Customise theme and log text size",
            ),
            "output": (
                "Output",
                "Configure output folders and filename pattern",
            ),
        }

        title, sub = titles.get(key, (key.title(), ""))

        Frame(self._topbar, bg=self._p["CONTENT_BG"], height=22).pack()
        Label(
            self._topbar,
            text=title,
            font=(self.FONT, 16, "bold"),
            fg=self._p["FG1"],
            bg=self._p["CONTENT_BG"],
            anchor="w",
        ).pack(anchor="w", padx=28)
        Label(
            self._topbar,
            text=sub,
            font=(self.FONT, 11),
            fg=self._p["FG3"],
            bg=self._p["CONTENT_BG"],
            anchor="w",
        ).pack(anchor="w", padx=28, pady=(3, 16))

    # ── mapping panel ─────────────────────────────────────────────────────────
    def _build_panel_mapping(self, parent: object) -> None:
        from tkinter import Frame, Label

        outer = Frame(parent, bg=self._p["CONTENT_BG"])  # type: ignore[arg-type]
        outer.pack(fill="both", expand=True, padx=28, pady=(16, 0))

        # table card
        card = Frame(
            outer,
            bg=self._p["CARD_BG"],
            highlightbackground=self._p["SEP"],
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True)

        # thead
        hdr = Frame(card, bg=self._p["THEAD_BG"])
        hdr.pack(fill="x")
        hdr.columnconfigure(0, weight=1)
        hdr.columnconfigure(1, weight=1)
        hdr.columnconfigure(2, minsize=86)
        hdr.columnconfigure(3, minsize=self.SB_W)

        for col, txt in enumerate(["  Original Name (NSE)", "  Custom Name"]):
            Label(
                hdr,
                text=txt,
                font=(self.FONT, 10),
                fg=self._p["FG3"],
                bg=self._p["THEAD_BG"],
                anchor="w",
            ).grid(row=0, column=col, sticky="ew", ipady=8)
            Frame(hdr, bg=self._p["SEP"], width=1).grid(row=0, column=col, sticky="nes")

        Label(
            hdr,
            text="Action",
            font=(self.FONT, 10),
            fg=self._p["FG3"],
            bg=self._p["THEAD_BG"],
            anchor="center",
        ).grid(row=0, column=2, sticky="ew", ipady=8)
        Label(hdr, text="", bg=self._p["THEAD_BG"], width=self.SB_W).grid(
            row=0, column=3, sticky="ew"
        )

        Frame(card, bg=self._p["SEP"], height=1).pack(fill="x")

        # scrollable body
        from tkinter import Frame as TF

        body = TF(card, bg=self._p["CARD_BG"])
        body.pack(fill="both", expand=True)

        self.canvas = Canvas(body, bg=self._p["CARD_BG"], highlightthickness=0, bd=0)
        sb = ctk.CTkScrollbar(
            body,
            orientation="vertical",
            command=self.canvas.yview,
            width=self.SB_W,
            fg_color=self._p["CARD_BG"],
            button_color=self._p["SEP"],
            button_hover_color=self._p["FG3"],
        )
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        from tkinter import Frame as RF

        self.rows_frame = RF(self.canvas, bg=self._p["CARD_BG"])
        self.rows_frame.columnconfigure(0, weight=1)
        self.rows_frame.columnconfigure(1, weight=1)
        self.rows_frame.columnconfigure(2, minsize=86)

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.rows_frame, anchor="nw"
        )

        self.rows_frame.bind("<Configure>", self._on_frame_cfg)
        self.canvas.bind("<Configure>", self._on_canvas_cfg)
        self.win.bind_all("<MouseWheel>", self._on_scroll)
        self.win.bind_all("<Button-4>", self._on_scroll)
        self.win.bind_all("<Button-5>", self._on_scroll)
        self._hdr = hdr
        hdr.bind("<Configure>", self._sync_cols)

        # bottom bar
        bot = Frame(outer, bg=self._p["CONTENT_BG"])
        bot.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            bot,
            text="+ Add Mapping",
            font=(self.FONT, 11, "bold"),
            fg_color=self._p["ADD_BG"],
            text_color=self._p["ADD_FG"],
            hover_color=self._p["PILL_BG"],
            border_color=self._p["ADD_BORDER"],
            border_width=1,
            corner_radius=6,
            height=30,
            command=self.add_row,
        ).pack(side="left")

        self._count_lbl = Label(
            bot,
            text="",
            font=(self.FONT, 10),
            fg=self._p["FG4"],
            bg=self._p["CONTENT_BG"],
        )
        self._count_lbl.pack(side="right")
        self._refresh_count()

    # ── performance panel ─────────────────────────────────────────────────────
    def _build_panel_performance(self, parent: object) -> None:
        from tkinter import Frame, Label

        outer = Frame(parent, bg=self._p["CONTENT_BG"])  # type: ignore[arg-type]
        outer.pack(fill="both", expand=True, padx=28, pady=20)

        # card
        card = Frame(
            outer,
            bg=self._p["CARD_BG"],
            highlightbackground=self._p["SEP"],
            highlightthickness=1,
            padx=22,
            pady=18,
        )
        card.pack(fill="x")

        # title row
        tr = Frame(card, bg=self._p["CARD_BG"])
        tr.pack(fill="x", pady=(0, 6))

        Label(
            tr,
            text="Parallel Downloads",
            font=(self.FONT, 13, "bold"),
            fg=self._p["FG1"],
            bg=self._p["CARD_BG"],
        ).pack(side="left")

        self._thread_badge = Label(
            tr,
            text=f"{self._workers_var.get()} threads",
            font=(self.FONT, 11, "bold"),
            fg=self._p["ACCENT"],
            bg=self._p["PILL_BG"],
            padx=10,
            pady=3,
        )
        self._thread_badge.pack(side="right")

        Label(
            card,
            text="Controls how many trading days are downloaded simultaneously.\n"
            "Higher values are faster but use more bandwidth and CPU.",
            font=(self.FONT, 11),
            fg=self._p["FG3"],
            bg=self._p["CARD_BG"],
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(0, 16))

        # slider
        ctk.CTkSlider(
            card,
            from_=1,
            to=16,
            number_of_steps=15,
            variable=self._workers_var,
            command=self._on_worker_change,
            button_color=self._p["ACCENT"],
            button_hover_color=self._p["ACCENT"],
            progress_color=self._p["ACCENT"],
            fg_color=self._p["SEP"],
            height=14,
        ).pack(fill="x")

        # slider labels
        lr = Frame(card, bg=self._p["CARD_BG"])
        lr.pack(fill="x", pady=(6, 0))
        for txt, anchor_side in [
            ("1 thread", "left"),
            ("16 threads", "right"),
        ]:
            Label(
                lr,
                text=txt,
                font=(self.FONT, 9),
                fg=self._p["FG4"],
                bg=self._p["CARD_BG"],
            ).pack(side=anchor_side)  # type: ignore[arg-type]

        Label(
            lr,
            text="8 — recommended",
            font=(self.FONT, 9),
            fg=self._p["FG4"],
            bg=self._p["CARD_BG"],
        ).pack(expand=True)

        # info box
        info = Frame(
            outer,
            bg=self._p["INFO_BG"],
            highlightbackground=self._p["INFO_BORDER"],
            highlightthickness=1,
            padx=16,
            pady=12,
        )
        info.pack(fill="x", pady=(16, 0))

        Label(
            info,
            text="Recommended: 8 threads for most connections. "
            "Reduce to 4 if you experience frequent timeouts or failed downloads.",
            font=(self.FONT, 11),
            fg=self._p["INFO_FG"],
            bg=self._p["INFO_BG"],
            wraplength=480,
            justify="left",
        ).pack(anchor="w")

    def _build_panel_scheduler(self, parent: object) -> None:
        from tkinter import Frame, Label

        outer = Frame(parent, bg=self._p["CONTENT_BG"])  # type: ignore[arg-type]
        outer.pack(fill="both", expand=True, padx=28, pady=20)

        # Enable card
        enable_card = Frame(
            outer,
            bg=self._p["CARD_BG"],
            highlightbackground=self._p["SEP"],
            highlightthickness=1,
            padx=22,
            pady=18,
        )
        enable_card.pack(fill="x")

        enable_row = Frame(enable_card, bg=self._p["CARD_BG"])
        enable_row.pack(fill="x", pady=(0, 6))

        Label(
            enable_row,
            text="Enable Scheduled Downloads",
            font=(self.FONT, 13, "bold"),
            fg=self._p["FG1"],
            bg=self._p["CARD_BG"],
        ).pack(side="left")

        self._enable_switch = ctk.CTkSwitch(
            enable_row,
            text="",
            variable=self._schedule_enabled,
            onvalue=True,
            offvalue=False,
            button_color=self._p["TOGGLE_OFF"],
            progress_color=self._p["TOGGLE_ON"],
            command=self._on_schedule_toggle,
        )
        self._enable_switch.pack(side="right")

        Label(
            enable_card,
            text="Automatically download today's bhavcopy at the time set below.\n"
            "No need to open the app — the OS handles it automatically.",
            font=(self.FONT, 11),
            fg=self._p["FG3"],
            bg=self._p["CARD_BG"],
            justify="left",
            anchor="w",
        ).pack(anchor="w")

        # Time card
        time_card = Frame(
            outer,
            bg=self._p["CARD_BG"],
            highlightbackground=self._p["SEP"],
            highlightthickness=1,
            padx=22,
            pady=18,
        )
        time_card.pack(fill="x", pady=(12, 0))

        time_row = Frame(time_card, bg=self._p["CARD_BG"])
        time_row.pack(fill="x", pady=(0, 6))

        Label(
            time_row,
            text="Download Time",
            font=(self.FONT, 13, "bold"),
            fg=self._p["FG1"],
            bg=self._p["CARD_BG"],
        ).pack(side="left")

        time_fields = ctk.CTkFrame(time_row, fg_color=self._p["CARD_BG"])
        time_fields.pack(side="right")

        self._hour_entry = ctk.CTkEntry(
            time_fields,
            textvariable=self._schedule_hour_var,
            width=52,
            font=(self.FONT, 14, "bold"),
            justify="center",
            fg_color=self._p["ENTRY_BG"],
            text_color=self._p["ACCENT"],
            border_color=self._p["ACCENT"],
            border_width=2,
            corner_radius=8,
        )
        self._hour_entry.pack(side="left")

        ctk.CTkLabel(
            time_fields,
            text=":",
            font=(self.FONT, 16, "bold"),
            text_color=self._p["FG1"],
            fg_color=self._p["CARD_BG"],
            width=12,
        ).pack(side="left")

        self._min_entry = ctk.CTkEntry(
            time_fields,
            textvariable=self._schedule_min_var,
            width=52,
            font=(self.FONT, 14, "bold"),
            justify="center",
            fg_color=self._p["ENTRY_BG"],
            text_color=self._p["ACCENT"],
            border_color=self._p["ACCENT"],
            border_width=2,
            corner_radius=8,
        )
        self._min_entry.pack(side="left")

        Label(
            time_card,
            text="Click the time field on the right to edit — use 24hr format.\n"
            "NSE closes at 15:30 IST so 17:30:00 or later is recommended.",
            font=(self.FONT, 11),
            fg=self._p["FG3"],
            bg=self._p["CARD_BG"],
            justify="left",
            anchor="w",
        ).pack(anchor="w")

        # Info box
        info = Frame(
            outer,
            bg=self._p["INFO_BG"],
            highlightbackground=self._p["INFO_BORDER"],
            highlightthickness=1,
            padx=16,
            pady=12,
        )
        info.pack(fill="x", pady=(16, 0))

        Label(
            info,
            text="Uses OS-level scheduling — works even when the app is closed. "
            "Mac uses LaunchAgent, Windows uses Task Scheduler, "
            "Linux uses crontab.",
            font=(self.FONT, 11),
            fg=self._p["INFO_FG"],
            bg=self._p["INFO_BG"],
            wraplength=480,
            justify="left",
        ).pack(anchor="w")

        # Set correct toggle colour on initial load
        self.win.after(
            50,
            lambda: self._enable_switch.configure(
                button_color=self._p["TOGGLE_ON"]
                if self._schedule_enabled.get()
                else self._p["TOGGLE_OFF"]
            ),
        )

    def _on_schedule_toggle(self) -> None:
        """Update switch colour immediately when toggled."""
        if self._schedule_enabled.get():
            self._enable_switch.configure(button_color=self._p["TOGGLE_ON"])
        else:
            self._enable_switch.configure(button_color=self._p["TOGGLE_OFF"])

    def _build_panel_appearance(self, parent: object) -> None:
        from tkinter import Frame, Label

        outer = Frame(parent, bg=self._p["CONTENT_BG"])  # type: ignore[arg-type]
        outer.pack(fill="both", expand=True, padx=28, pady=20)

        theme_card = Frame(
            outer,
            bg=self._p["CARD_BG"],
            highlightbackground=self._p["SEP"],
            highlightthickness=1,
            padx=22,
            pady=18,
        )
        theme_card.pack(fill="x")

        Label(
            theme_card,
            text="Appearance",
            font=(self.FONT, 13, "bold"),
            fg=self._p["FG1"],
            bg=self._p["CARD_BG"],
        ).pack(anchor="w", pady=(0, 4))

        Label(
            theme_card,
            text="Choose how GetBhavCopy looks. System follows your OS setting.",
            font=(self.FONT, 11),
            fg=self._p["FG3"],
            bg=self._p["CARD_BG"],
            justify="left",
        ).pack(anchor="w", pady=(0, 14))

        theme_row = Frame(theme_card, bg=self._p["CARD_BG"])
        theme_row.pack(anchor="w")

        for val, label in [
            ("system", "System"),
            ("dark", "Dark"),
            ("light", "Light"),
        ]:
            ctk.CTkRadioButton(
                theme_row,
                text=label,
                variable=self._theme_var,
                value=val,
                font=(self.FONT, 12),
                text_color=self._p["FG2"],
                fg_color=self._p["ACCENT"],
                hover_color=self._p["ACCENT"],
                border_color=self._p["SEP"],
                command=self._on_theme_change,
            ).pack(side="left", padx=(0, 20))

        log_card = Frame(
            outer,
            bg=self._p["CARD_BG"],
            highlightbackground=self._p["SEP"],
            highlightthickness=1,
            padx=22,
            pady=18,
        )
        log_card.pack(fill="x", pady=(12, 0))

        Label(
            log_card,
            text="Log Text Size",
            font=(self.FONT, 13, "bold"),
            fg=self._p["FG1"],
            bg=self._p["CARD_BG"],
        ).pack(anchor="w", pady=(0, 4))

        Label(
            log_card,
            text="Controls the font size in the Application Logs panel.",
            font=(self.FONT, 11),
            fg=self._p["FG3"],
            bg=self._p["CARD_BG"],
            justify="left",
        ).pack(anchor="w", pady=(0, 14))

        size_row = Frame(log_card, bg=self._p["CARD_BG"])
        size_row.pack(anchor="w")

        for val, label in [
            ("small", "Small"),
            ("medium", "Medium"),
            ("large", "Large"),
        ]:
            ctk.CTkRadioButton(
                size_row,
                text=label,
                variable=self._log_size_var,
                value=val,
                font=(self.FONT, 12),
                text_color=self._p["FG2"],
                fg_color=self._p["ACCENT"],
                hover_color=self._p["ACCENT"],
                border_color=self._p["SEP"],
            ).pack(side="left", padx=(0, 20))

        info = Frame(
            outer,
            bg=self._p["INFO_BG"],
            highlightbackground=self._p["INFO_BORDER"],
            highlightthickness=1,
            padx=16,
            pady=12,
        )
        info.pack(fill="x", pady=(16, 0))

        Label(
            info,
            text="Theme changes take effect immediately. "
            "Log size applies on next app launch.",
            font=(self.FONT, 11),
            fg=self._p["INFO_FG"],
            bg=self._p["INFO_BG"],
            wraplength=480,
            justify="left",
        ).pack(anchor="w")

    def _on_theme_change(self) -> None:
        try:
            ctk.set_appearance_mode(self._theme_var.get())
        except Exception:
            pass

    def _on_split_toggle(self) -> None:
        self._apply_split_state()

    def _apply_split_state(self) -> None:
        split = self._split_files_var.get()
        if split:
            self._split_switch.configure(button_color=self._p["TOGGLE_ON"])
            if hasattr(self, "_idx_entry"):
                self._idx_entry.configure(
                    state="normal",
                    text_color=self._p["ENTRY_FG"],
                    border_color=self._p["SEP"],
                )
        else:
            self._split_switch.configure(button_color=self._p["TOGGLE_OFF"])
            if hasattr(self, "_idx_entry"):
                self._idx_entry.configure(
                    state="disabled",
                    text_color=self._p["FG4"],
                    border_color=self._p["SEP"],
                )
        self._update_output_previews()

    def _update_output_previews(self) -> None:
        eq_pat = self._filename_prefix_var.get().strip() or "{date}-NSE-EQ"
        if hasattr(self, "_eq_preview"):
            self._eq_preview.config(
                text="→ " + eq_pat.replace("{date}", "2026-04-13") + ".txt"
            )
        idx_pat = self._idx_filename_prefix_var.get().strip() or "{date}-NSE-IDX"
        if hasattr(self, "_idx_preview"):
            self._idx_preview.config(
                text="→ " + idx_pat.replace("{date}", "2026-04-13") + ".txt"
            )

    def _build_panel_output(self, parent: object) -> None:
        from tkinter import Canvas, Frame, Label

        # scrollable container
        container = Frame(parent, bg=self._p["CONTENT_BG"])  # type: ignore[arg-type]
        container.pack(fill="both", expand=True)

        _canvas = Canvas(
            container,
            bg=self._p["CONTENT_BG"],
            highlightthickness=0,
            bd=0,
        )
        _sb = ctk.CTkScrollbar(
            container,
            orientation="vertical",
            command=_canvas.yview,
            width=self.SB_W,
            fg_color=self._p["CONTENT_BG"],
            button_color=self._p["SEP"],
            button_hover_color=self._p["FG3"],
        )
        _canvas.configure(yscrollcommand=_sb.set)
        _sb.pack(side="right", fill="y")
        _canvas.pack(side="left", fill="both", expand=True)

        inner_frame = Frame(_canvas, bg=self._p["CONTENT_BG"])
        _win_id = _canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        inner_frame.bind(
            "<Configure>",
            lambda e: _canvas.configure(scrollregion=_canvas.bbox("all")),
        )
        _canvas.bind(
            "<Configure>",
            lambda e: _canvas.itemconfig(
                _win_id, width=getattr(e, "width", _canvas.winfo_width())
            ),
        )

        # bind scroll on the canvas itself
        def _out_scroll(e: object) -> None:
            from tkinter import Event

            if not isinstance(e, Event):
                return
            if e.num == 4:
                _canvas.yview_scroll(-1, "units")
            elif e.num == 5:
                _canvas.yview_scroll(1, "units")
            elif getattr(e, "delta", 0):
                _canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        _canvas.bind("<MouseWheel>", _out_scroll)
        _canvas.bind("<Button-4>", _out_scroll)
        _canvas.bind("<Button-5>", _out_scroll)
        inner_frame.bind("<MouseWheel>", _out_scroll)
        inner_frame.bind("<Button-4>", _out_scroll)
        inner_frame.bind("<Button-5>", _out_scroll)

        outer = Frame(inner_frame, bg=self._p["CONTENT_BG"])
        outer.pack(fill="both", expand=True, padx=28, pady=20)

        # ── Filename patterns card (both together) ────────────────────────────
        pat_card = Frame(
            outer,
            bg=self._p["CARD_BG"],
            highlightbackground=self._p["SEP"],
            highlightthickness=1,
            padx=22,
            pady=18,
        )
        pat_card.pack(fill="x")

        Label(
            pat_card,
            text="Filename Patterns",
            font=(self.FONT, 13, "bold"),
            fg=self._p["FG1"],
            bg=self._p["CARD_BG"],
        ).pack(anchor="w", pady=(0, 4))

        Label(
            pat_card,
            text="Use {date} for the trading date. "
            "File extension (.txt / .csv) is added automatically.",
            font=(self.FONT, 11),
            fg=self._p["FG3"],
            bg=self._p["CARD_BG"],
            justify="left",
        ).pack(anchor="w", pady=(0, 14))

        # equity row
        eq_row = Frame(pat_card, bg=self._p["CARD_BG"])
        eq_row.pack(fill="x", pady=(0, 8))

        Label(
            eq_row,
            text="Equity",
            font=(self.FONT, 11),
            fg=self._p["FG2"],
            bg=self._p["CARD_BG"],
            width=8,
            anchor="w",
        ).pack(side="left")

        self._eq_entry = ctk.CTkEntry(
            eq_row,
            textvariable=self._filename_prefix_var,
            width=220,
            font=(self.FONT, 11),
            fg_color=self._p["ENTRY_BG"],
            text_color=self._p["ENTRY_FG"],
            border_color=self._p["SEP"],
            border_width=1,
            corner_radius=6,
            placeholder_text="{date}-NSE-EQ",
        )
        self._eq_entry.pack(side="left", padx=(8, 0))

        self._eq_preview = Label(
            eq_row,
            text="",
            font=(self.FONT, 10),
            fg=self._p["FG3"],
            bg=self._p["CARD_BG"],
        )
        self._eq_preview.pack(side="left", padx=(10, 0))
        self._filename_prefix_var.trace("w", lambda *_: self._update_output_previews())

        # indices row
        idx_row = Frame(pat_card, bg=self._p["CARD_BG"])
        idx_row.pack(fill="x")

        Label(
            idx_row,
            text="Indices",
            font=(self.FONT, 11),
            fg=self._p["FG2"],
            bg=self._p["CARD_BG"],
            width=8,
            anchor="w",
        ).pack(side="left")

        self._idx_entry = ctk.CTkEntry(
            idx_row,
            textvariable=self._idx_filename_prefix_var,
            width=220,
            font=(self.FONT, 11),
            fg_color=self._p["ENTRY_BG"],
            text_color=self._p["ENTRY_FG"],
            border_color=self._p["SEP"],
            border_width=2,
            corner_radius=6,
            placeholder_text="{date}-NSE-IDX",
        )
        self._idx_entry.pack(side="left", padx=(8, 0))

        self._idx_preview = Label(
            idx_row,
            text="",
            font=(self.FONT, 10),
            fg=self._p["FG3"],
            bg=self._p["CARD_BG"],
        )
        self._idx_preview.pack(side="left", padx=(10, 0))
        self._idx_filename_prefix_var.trace(
            "w", lambda *_: self._update_output_previews()
        )

        # ── Split toggle ──────────────────────────────────────────────────────
        split_card = Frame(
            outer,
            bg=self._p["CARD_BG"],
            highlightbackground=self._p["SEP"],
            highlightthickness=1,
            padx=22,
            pady=18,
        )
        split_card.pack(fill="x", pady=(12, 0))

        split_row = Frame(split_card, bg=self._p["CARD_BG"])
        split_row.pack(fill="x", pady=(0, 6))

        Label(
            split_row,
            text="Split Equity and Indices",
            font=(self.FONT, 13, "bold"),
            fg=self._p["FG1"],
            bg=self._p["CARD_BG"],
        ).pack(side="left")

        self._split_switch = ctk.CTkSwitch(
            split_row,
            text="",
            variable=self._split_files_var,
            onvalue=True,
            offvalue=False,
            button_color=self._p["TOGGLE_OFF"],
            progress_color=self._p["TOGGLE_ON"],
            command=self._on_split_toggle,
        )
        self._split_switch.pack(side="right")

        Label(
            split_card,
            text="When ON — two separate files saved per day using "
            "the patterns above.\n"
            "When OFF — one combined file using the Equity pattern.",
            font=(self.FONT, 11),
            fg=self._p["FG3"],
            bg=self._p["CARD_BG"],
            justify="left",
        ).pack(anchor="w")

        # apply initial state
        self.win.after(60, self._apply_split_state)
        self._update_output_previews()

    # ── footer ────────────────────────────────────────────────────────────────
    def _build_footer(self, parent: object) -> None:
        from tkinter import Frame

        footer = Frame(parent, bg=self._p["FOOTER_BG"])  # type: ignore[arg-type]
        footer.pack(fill="x", side="bottom")

        row = Frame(footer, bg=self._p["FOOTER_BG"])
        row.pack(fill="x", padx=24, pady=12)

        ctk.CTkButton(
            row,
            text="Cancel",
            font=(self.FONT, 12),
            fg_color="transparent",
            text_color=self._p["CANCEL_FG"],
            hover_color=self._p["CANCEL_HOVER"],
            border_color=self._p["SEP"],
            border_width=1,
            corner_radius=7,
            height=34,
            width=90,
            command=self._on_close,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            row,
            text="Save Settings",
            font=(self.FONT, 12, "bold"),
            fg_color=self._p["SAVE_BG"],
            text_color=self._p["SAVE_FG"],
            hover_color=self._p["SAVE_HOVER"],
            corner_radius=7,
            height=34,
            width=130,
            command=self.save_mapping,
        ).pack(side="right")

    def _setup_time_validators(self) -> None:
        self._schedule_hour_var.trace("w", self._limit_hour)
        self._schedule_min_var.trace("w", self._limit_min)

    def _limit_hour(self, *args: object) -> None:
        v = self._schedule_hour_var.get()
        if not v.isdigit():
            self._schedule_hour_var.set("".join(c for c in v if c.isdigit()))
            return
        if len(v) > 2:
            self._schedule_hour_var.set(v[:2])
            return
        if len(v) == 2:
            h = int(v)
            if h > 23:
                self._schedule_hour_var.set("23")
            else:
                # Auto advance to minutes
                if hasattr(self, "_min_entry"):
                    self._min_entry.focus()
                    self._min_entry.icursor("end")

    def _limit_min(self, *args: object) -> None:
        v = self._schedule_min_var.get()
        if not v.isdigit():
            self._schedule_min_var.set("".join(c for c in v if c.isdigit()))
            return
        if len(v) > 2:
            self._schedule_min_var.set(v[:2])
            return
        if len(v) == 2:
            m = int(v)
            if m > 59:
                self._schedule_min_var.set("59")

    # ── row management ────────────────────────────────────────────────────────
    def _refresh_count(self) -> None:
        n = len(self._rows)
        txt = f"{n} mapping" if n == 1 else f"{n} mappings"
        if hasattr(self, "_count_lbl"):
            self._count_lbl.config(text=txt)
        # update sidebar pill
        nw = self._nav_widgets.get("mapping", {})
        if nw.get("pill"):
            nw["pill"].config(text=str(n))

    def add_row(self, original: str = "", custom: str = "") -> None:
        from tkinter import Entry, Frame

        ov = StringVar(value=original)
        cv = StringVar(value=custom)
        r = self._data_row
        bg = self._p["ENTRY_BG"] if (r // 2) % 2 == 0 else self._p["ALT_ROW"]

        first_entry = None  # store reference

        for col, var in ((0, ov), (1, cv)):
            entry = Entry(
                self.rows_frame,
                textvariable=var,
                font=(self.FONT, 11),
                bg=bg,
                fg=self._p["ENTRY_FG"],
                insertbackground=self._p["INSERT_BG"],
                relief="flat",
                bd=0,
                highlightthickness=0,
            )

            entry.grid(row=r, column=col, sticky="ew", ipady=10, padx=(8, 0))

            if col == 0:
                first_entry = entry  # save first entry

            Frame(self.rows_frame, bg=self._p["SEP"], width=1).grid(
                row=r, column=col, sticky="nes"
            )

        ctk.CTkButton(
            self.rows_frame,
            text="Remove",
            font=(self.FONT, 10),
            fg_color=self._p["DEL_BG"],
            text_color=self._p["DEL_FG"],
            hover_color=self._p["DEL_HOVER"],
            corner_radius=0,
            width=86,
            height=40,
            command=lambda rv=ov, cv2=cv, ro=r: self._del_row(rv, cv2, ro),
        ).grid(row=r, column=2, sticky="nsew")

        Frame(self.rows_frame, bg=self._p["ROW_SEP"], height=1).grid(
            row=r + 1, column=0, columnspan=3, sticky="ew"
        )

        # Set focus to the first entry
        if first_entry:
            first_entry.focus_set()

        self._rows.append((ov, cv, r))
        self._data_row += 2
        self._refresh_count()

    def _del_row(self, ov: StringVar, cv: StringVar, ri: int) -> None:
        self._rows = [(o, c, r) for o, c, r in self._rows if r != ri]
        for w in self.rows_frame.grid_slaves():
            if w.grid_info().get("row") in (ri, ri + 1):
                w.destroy()
        self._refresh_count()

    def _load_existing(self) -> None:
        for orig, custom in load_symbol_mapping().items():
            self.add_row(orig, custom)
        self._refresh_count()

    # ── save ──────────────────────────────────────────────────────────────────
    def save_mapping(self) -> None:
        mapping: dict[str, str] = {}
        for ov, cv, _ in self._rows:
            k = ov.get().strip().upper()
            v = cv.get().strip()
            if k and v:
                mapping[k] = v
        try:
            cfg = load_app_config()
            cfg["max_workers"] = int(self._workers_var.get())
            cfg["schedule_enabled"] = bool(self._schedule_enabled.get())
            h = self._schedule_hour_var.get().zfill(2)
            m = self._schedule_min_var.get().zfill(2)
            cfg["schedule_time"] = f"{h}:{m}"
            cfg["theme"] = self._theme_var.get()
            cfg["log_size"] = self._log_size_var.get()
            cfg["filename_pattern"] = self._filename_prefix_var.get().strip()
            cfg["idx_filename_pattern"] = self._idx_filename_prefix_var.get().strip()
            cfg["split_eq_idx"] = bool(self._split_files_var.get())
            save_app_config(cfg)
            save_symbol_mapping(mapping)
            if self._on_save_callback:
                getattr(self._on_save_callback, "__call__")()
            self._on_close()
        except Exception as e:
            messagebox.showerror("Save Failed", str(e))

    # ── slider callback ───────────────────────────────────────────────────────
    def _on_worker_change(self, val: float) -> None:
        if hasattr(self, "_thread_badge"):
            self._thread_badge.config(text=f"{int(val)} threads")

    # ── canvas / scroll helpers ───────────────────────────────────────────────
    def _sync_cols(self, event: object = None) -> None:
        self.win.update_idletasks()
        total = self.canvas.winfo_width()
        if total < 10:
            return
        aw = 86
        colw = (total - aw) // 2
        for frame in (self.rows_frame, self._hdr):
            frame.columnconfigure(0, minsize=colw, weight=1)
            frame.columnconfigure(1, minsize=colw, weight=1)
            frame.columnconfigure(2, minsize=aw)

    def _on_frame_cfg(self, event: object = None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_cfg(self, event: object) -> None:
        if hasattr(event, "width"):
            self.canvas.itemconfig(self.canvas_window, width=getattr(event, "width"))
        self._sync_cols()

    def _on_scroll(self, event: object) -> None:
        from tkinter import Event

        try:
            if isinstance(event, Event):
                if event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")
                elif event.delta:
                    self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass
