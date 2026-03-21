import json
import os
from pathlib import Path
from tkinter import (
    Canvas,
    Entry,
    Frame,
    Label,
    Scrollbar,
    StringVar,
    Toplevel,
    messagebox,
)


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


class SettingsWindow:
    BG = "#1e1e1e"
    FG = "#ffffff"
    ENTRY_BG = "#2d2d2d"
    ENTRY_FG = "#ffffff"
    BTN_BG = "#3a3a3a"
    BTN_FG = "#ffffff"
    HDR_BG = "#2a2a2a"
    HDR_FG = "#aaaaaa"
    SEP = "#444444"
    SAVE_BG = "#1a3a1a"
    SAVE_FG = "#80ff80"
    DEL_BG = "#3a1a1a"
    DEL_FG = "#ff6060"
    SB_W = 14  # scrollbar width — must match everywhere

    def __init__(self, parent):
        self.win = Toplevel(parent)
        self.win.withdraw()
        self.win.title("Settings - Symbol Mapping")
        self.win.geometry("620x460")
        self.win.minsize(500, 380)
        self.win.resizable(True, True)
        self.win.configure(bg=self.BG)

        self._rows: list[tuple[StringVar, StringVar, int]] = []
        self._data_row = 0

        self._build_header()
        self._build_table()
        self._build_footer()

        self._load_existing()
        if not self._rows:
            self.add_row()

        self._center_on_parent(parent)

    # ------------------------------------------------------------------
    # Build sections
    # ------------------------------------------------------------------

    def _center_on_parent(self, parent):
        self.win.update_idletasks()
        w = 620
        h = 460
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")
        self.win.after(10, self._show)

    def _show(self):
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()
        self.win.grab_set()

    def _build_header(self):
        Label(
            self.win,
            text="Symbol Mapping",
            font=("SF Pro", 16, "bold"),
            fg=self.FG,
            bg=self.BG,
        ).pack(pady=(16, 2))

        Label(
            self.win,
            text="Rename any NSE symbol or index in your output files.",
            font=("SF Pro", 11),
            fg=self.HDR_FG,
            bg=self.BG,
        ).pack(pady=(0, 10))

        Frame(self.win, bg=self.SEP, height=1).pack(fill="x", padx=20)

    def _build_table(self):
        outer = Frame(self.win, bg=self.SEP)
        outer.pack(fill="both", expand=True, padx=20)

        # ── Fixed header (never scrolls) ───────────────────────────────
        hdr = Frame(outer, bg=self.HDR_BG)
        hdr.pack(fill="x", side="top")
        hdr.columnconfigure(0, weight=1)
        hdr.columnconfigure(1, weight=1)
        hdr.columnconfigure(2, minsize=72)
        hdr.columnconfigure(3, minsize=self.SB_W)  # matches scrollbar width

        Label(
            hdr,
            text="  Original Name (NSE)",
            font=("SF Pro", 10, "bold"),
            fg=self.HDR_FG,
            bg=self.HDR_BG,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", ipady=8)

        Frame(hdr, bg=self.SEP, width=1).grid(row=0, column=0, sticky="nes")

        Label(
            hdr,
            text="  Custom Name",
            font=("SF Pro", 10, "bold"),
            fg=self.HDR_FG,
            bg=self.HDR_BG,
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", ipady=8)

        Frame(hdr, bg=self.SEP, width=1).grid(row=0, column=1, sticky="nes")

        Label(
            hdr,
            text="Action",
            font=("SF Pro", 10, "bold"),
            fg=self.HDR_FG,
            bg=self.HDR_BG,
            anchor="center",
        ).grid(row=0, column=2, sticky="ew", ipady=8)

        # Spacer that reserves exactly SB_W pixels — aligns with scrollbar
        Label(
            hdr,
            text="",
            bg=self.HDR_BG,
            width=1,
        ).grid(row=0, column=3, sticky="ew", ipady=8)

        # 1px separator below header
        Frame(outer, bg=self.SEP, height=1).pack(fill="x", side="top")

        # ── Scrollable body ────────────────────────────────────────────
        body = Frame(outer, bg=self.BG)
        body.pack(fill="both", expand=True, side="top")

        self.canvas = Canvas(
            body,
            bg=self.BG,
            highlightthickness=0,
            bd=0,
        )

        # Wrap scrollbar in a frame so we can control its background
        sb_frame = Frame(body, bg=self.HDR_BG, width=self.SB_W)
        sb_frame.pack(side="right", fill="y")
        sb_frame.pack_propagate(False)

        scrollbar = Scrollbar(
            sb_frame,
            orient="vertical",
            command=self.canvas.yview,
            bg=self.SEP,
            troughcolor=self.HDR_BG,
            activebackground="#666666",
            highlightthickness=0,
            highlightbackground=self.HDR_BG,
            bd=0,
            width=self.SB_W,
            elementborderwidth=0,
        )
        scrollbar.pack(fill="both", expand=True)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)

        # ── Rows frame inside canvas ───────────────────────────────────
        self.rows_frame = Frame(self.canvas, bg=self.BG)
        self.rows_frame.columnconfigure(0, weight=1)
        self.rows_frame.columnconfigure(1, weight=1)
        self.rows_frame.columnconfigure(2, minsize=72)

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.rows_frame, anchor="nw"
        )

        self.rows_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.win.bind_all("<MouseWheel>", self._on_mousewheel)
        self.win.bind_all("<Button-4>", self._on_mousewheel)
        self.win.bind_all("<Button-5>", self._on_mousewheel)

        self._hdr = hdr
        hdr.bind("<Configure>", self._sync_column_widths)

    def _update_count(self):
        count = len(self._rows)
        text = f"{count} mapping" if count == 1 else f"{count} mappings"
        self._count_label.configure(text=text)

    def _build_footer(self):
        Frame(self.win, bg=self.SEP, height=1).pack(fill="x", padx=20)

        self._count_label = Label(
            self.win,
            text="",
            font=("SF Pro", 10),
            fg=self.HDR_FG,
            bg=self.BG,
        )
        self._count_label.pack(anchor="e", padx=24, pady=(4, 0))

        btn_row = Frame(self.win, bg=self.BG)
        btn_row.pack(fill="x", padx=20, pady=12)

        add_btn = Label(
            btn_row,
            text="+ Add Row",
            font=("SF Pro", 11),
            bg=self.BTN_BG,
            fg=self.BTN_FG,
            anchor="center",
            cursor="hand2",
            padx=14,
            pady=7,
        )
        add_btn.pack(side="left")
        add_btn.bind("<Button-1>", lambda e: self.add_row())

        cancel_btn = Label(
            btn_row,
            text="Cancel",
            font=("SF Pro", 11),
            bg=self.BTN_BG,
            fg=self.HDR_FG,
            anchor="center",
            cursor="hand2",
            padx=14,
            pady=7,
        )
        cancel_btn.pack(side="right", padx=(8, 0))
        cancel_btn.bind("<Button-1>", lambda e: self.win.destroy())

        save_btn = Label(
            btn_row,
            text="Save",
            font=("SF Pro", 11, "bold"),
            bg=self.SAVE_BG,
            fg=self.SAVE_FG,
            anchor="center",
            cursor="hand2",
            padx=14,
            pady=7,
        )
        save_btn.pack(side="right")
        save_btn.bind("<Button-1>", lambda e: self.save_mapping())

    # ------------------------------------------------------------------
    # Row management
    # ------------------------------------------------------------------

    def add_row(self, original="", custom=""):
        orig_var = StringVar(value=original)
        custom_var = StringVar(value=custom)
        r = self._data_row

        row_bg = self.ENTRY_BG if (r // 2) % 2 == 0 else "#333333"

        Entry(
            self.rows_frame,
            textvariable=orig_var,
            font=("SF Pro", 11),
            bg=row_bg,
            fg=self.ENTRY_FG,
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            highlightthickness=0,
        ).grid(row=r, column=0, sticky="ew", ipady=9, padx=(4, 0))

        Entry(
            self.rows_frame,
            textvariable=custom_var,
            font=("SF Pro", 11),
            bg=row_bg,
            fg=self.ENTRY_FG,
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            highlightthickness=0,
        ).grid(row=r, column=1, sticky="ew", ipady=9, padx=(4, 0))

        Frame(self.rows_frame, bg=self.SEP, width=1).grid(row=r, column=0, sticky="nes")

        del_btn = Label(
            self.rows_frame,
            text="✕",
            font=("SF Pro", 11),
            bg=self.DEL_BG,
            fg=self.DEL_FG,
            anchor="center",
            cursor="hand2",
        )
        del_btn.grid(row=r, column=2, sticky="nsew", ipady=9)

        def on_delete(
            e: object,
            rv: StringVar = orig_var,
            cv: StringVar = custom_var,
            ro: int = r,
        ) -> None:
            self._delete_row(rv, cv, ro)

        del_btn.bind("<Button-1>", on_delete)

        Frame(self.rows_frame, bg=self.SEP, height=1).grid(
            row=r + 1, column=0, columnspan=3, sticky="ew"
        )

        self._rows.append((orig_var, custom_var, r))
        self._data_row += 2
        self._update_count()

    def _delete_row(self, orig_var, custom_var, row_index):
        self._rows = [(ov, cv, ri) for ov, cv, ri in self._rows if ri != row_index]
        for widget in self.rows_frame.grid_slaves():
            if widget.grid_info().get("row") in (row_index, row_index + 1):
                widget.destroy()

        self._update_count()

    def _load_existing(self):
        mapping = load_symbol_mapping()
        for original, custom in mapping.items():
            self.add_row(original, custom)
        self._update_count()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save_mapping(self):
        mapping = {}
        for orig_var, custom_var, _ in self._rows:
            original = orig_var.get().strip().upper()
            custom = custom_var.get().strip()
            if not original or not custom:
                continue
            mapping[original] = custom
        save_symbol_mapping(mapping)
        messagebox.showinfo(
            "Saved", f"Mapping saved successfully ({len(mapping)} entries)."
        )
        self.win.destroy()

    # ------------------------------------------------------------------
    # Canvas / scroll / sync helpers
    # ------------------------------------------------------------------

    def _sync_column_widths(self, event=None) -> None:
        self.win.update_idletasks()
        bbox0 = self._hdr.grid_bbox(0, 0)
        bbox1 = self._hdr.grid_bbox(1, 0)
        bbox2 = self._hdr.grid_bbox(2, 0)
        if bbox0 and bbox1 and bbox2:
            self.rows_frame.columnconfigure(0, minsize=bbox0[2])
            self.rows_frame.columnconfigure(1, minsize=bbox1[2])
            self.rows_frame.columnconfigure(2, minsize=bbox2[2])

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self._sync_column_widths()

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
