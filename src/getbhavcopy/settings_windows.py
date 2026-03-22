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
    SB_W = 14
    FONT = (
        "SF Pro"
        if sys.platform == "darwin"
        else "Segoe UI"
        if sys.platform == "win32"
        else "Ubuntu"
    )

    def __init__(self, parent: object) -> None:
        from tkinter import Toplevel

        self.win = Toplevel()
        self.win.withdraw()
        self.win.title("Settings - Symbol Mapping")
        self.win.geometry("620x460")
        self.win.minsize(500, 380)
        self.win.resizable(True, True)
        self.win.configure(bg=self.BG)
        self.win.transient(getattr(parent, "_w", None))

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

    def _center_on_parent(self, parent: object) -> None:
        self.win.update_idletasks()
        w = 620
        h = 460
        pw = int(getattr(parent, "winfo_width")())
        ph = int(getattr(parent, "winfo_height")())
        px = int(getattr(parent, "winfo_rootx")())
        py = int(getattr(parent, "winfo_rooty")())
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")
        self.win.after(10, self._show)

    # def _show(self) -> None:
    #     self.win.deiconify()
    #     self.win.lift()
    #     self.win.focus_force()
    #     self.win.after(100, self._apply_grab)

    def _show(self) -> None:
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self) -> None:
        self.win.unbind_all("<MouseWheel>")
        self.win.unbind_all("<Button-4>")
        self.win.unbind_all("<Button-5>")
        self.win.destroy()

    def _build_header(self) -> None:
        from tkinter import Frame, Label

        Label(
            self.win,
            text="Symbol Mapping",
            font=(self.FONT, 16, "bold"),
            fg=self.FG,
            bg=self.BG,
        ).pack(pady=(16, 2))

        Label(
            self.win,
            text="Rename any NSE symbol or index in your output files.",
            font=(self.FONT, 11),
            fg=self.HDR_FG,
            bg=self.BG,
        ).pack(pady=(0, 10))

        Frame(
            self.win,
            height=1,
            bg=self.SEP,
        ).pack(fill="x", padx=20)

    def _build_table(self) -> None:
        from tkinter import Frame, Label

        outer = Frame(self.win, bg=self.SEP)
        outer.pack(fill="both", expand=True, padx=20)

        # Fixed header
        hdr = Frame(outer, bg=self.HDR_BG)
        hdr.pack(fill="x", side="top")
        hdr.columnconfigure(0, weight=1)
        hdr.columnconfigure(1, weight=1)
        hdr.columnconfigure(2, minsize=72)
        hdr.columnconfigure(3, minsize=self.SB_W)

        Label(
            hdr,
            text=" Original Name (NSE)",
            font=(self.FONT, 10, "bold"),
            fg=self.HDR_FG,
            bg=self.HDR_BG,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", ipady=8)

        Frame(hdr, bg=self.SEP, width=1).grid(row=0, column=0, sticky="nes")

        Label(
            hdr,
            text=" Custom Name",
            font=(self.FONT, 10, "bold"),
            fg=self.HDR_FG,
            bg=self.HDR_BG,
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", ipady=8)

        Frame(hdr, bg=self.SEP, width=1).grid(row=0, column=1, sticky="nes")

        Label(
            hdr,
            text="Action",
            font=(self.FONT, 10, "bold"),
            fg=self.HDR_FG,
            bg=self.HDR_BG,
            anchor="center",
        ).grid(row=0, column=2, sticky="ew", ipady=8)

        Label(
            hdr,
            text="",
            bg=self.HDR_BG,
            width=self.SB_W,
        ).grid(row=0, column=3, sticky="ew", ipady=8)

        # Separator below header
        Frame(outer, bg=self.SEP, height=1).pack(fill="x", side="top")

        # Scrollable body
        from tkinter import Frame as TkFrame

        body = TkFrame(outer, bg=self.BG)
        body.pack(fill="both", expand=True, side="top")

        self.canvas = Canvas(
            body,
            bg=self.BG,
            highlightthickness=0,
            bd=0,
        )

        scrollbar = ctk.CTkScrollbar(
            body,
            orientation="vertical",
            command=self.canvas.yview,
            width=self.SB_W,
            fg_color=self.HDR_BG,
            button_color=self.SEP,
            button_hover_color="#666666",
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        from tkinter import Frame

        self.rows_frame = Frame(
            self.canvas,
            bg=self.BG,
        )
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

    def _update_count(self) -> None:
        count = len(self._rows)
        text = f"{count} mapping" if count == 1 else f"{count} mappings"
        self._count_label.config(text=text)

    def _build_footer(self) -> None:
        from tkinter import Frame, Label

        Frame(
            self.win,
            height=1,
            bg=self.SEP,
        ).pack(fill="x", padx=20)

        self._count_label = Label(
            self.win,
            text="",
            font=(self.FONT, 10),
            fg=self.HDR_FG,
            bg=self.BG,
        )
        self._count_label.pack(anchor="e", padx=24, pady=(4, 0))

        btn_row = Frame(
            self.win,
            bg=self.BG,
        )
        btn_row.pack(fill="x", padx=20, pady=12)

        ctk.CTkButton(
            btn_row,
            text="+ Add Row",
            font=(self.FONT, 11),
            fg_color=self.BTN_BG,
            text_color=self.BTN_FG,
            hover_color="#4a4a4a",
            corner_radius=6,
            command=self.add_row,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            font=(self.FONT, 11),
            fg_color=self.BTN_BG,
            text_color=self.HDR_FG,
            hover_color="#4a4a4a",
            corner_radius=6,
            command=self._on_close,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_row,
            text="Save",
            font=(self.FONT, 11, "bold"),
            fg_color=self.SAVE_BG,
            text_color=self.SAVE_FG,
            hover_color="#2a5a2a",
            corner_radius=6,
            command=self.save_mapping,
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Row management
    # ------------------------------------------------------------------

    def add_row(self, original: str = "", custom: str = "") -> None:
        from tkinter import Entry, Frame

        orig_var = StringVar(value=original)
        custom_var = StringVar(value=custom)
        r = self._data_row

        row_bg = self.ENTRY_BG if (r // 2) % 2 == 0 else "#333333"

        Entry(
            self.rows_frame,
            textvariable=orig_var,
            font=(self.FONT, 11),
            bg=row_bg,
            fg=self.ENTRY_FG,
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            highlightthickness=0,
        ).grid(row=r, column=0, sticky="ew", ipady=9, padx=(4, 0))

        Frame(
            self.rows_frame,
            bg=self.SEP,
            width=1,
        ).grid(row=r, column=0, sticky="nes")

        Entry(
            self.rows_frame,
            textvariable=custom_var,
            font=(self.FONT, 11),
            bg=row_bg,
            fg=self.ENTRY_FG,
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            highlightthickness=0,
        ).grid(row=r, column=1, sticky="ew", ipady=9, padx=(4, 0))

        ctk.CTkButton(
            self.rows_frame,
            text="✕",
            font=(self.FONT, 11),
            fg_color=self.DEL_BG,
            text_color=self.DEL_FG,
            hover_color="#6a2a2a",
            corner_radius=0,
            width=72,
            height=36,
            command=lambda rv=orig_var, cv=custom_var, ro=r: self._delete_row(
                rv, cv, ro
            ),
        ).grid(row=r, column=2, sticky="nsew")

        Frame(
            self.rows_frame,
            bg=self.SEP,
            height=1,
        ).grid(row=r + 1, column=0, columnspan=3, sticky="ew")

        self._rows.append((orig_var, custom_var, r))
        self._data_row += 2
        self._update_count()

    def _delete_row(
        self, orig_var: StringVar, custom_var: StringVar, row_index: int
    ) -> None:
        self._rows = [(ov, cv, ri) for ov, cv, ri in self._rows if ri != row_index]
        for widget in self.rows_frame.grid_slaves():
            if widget.grid_info().get("row") in (row_index, row_index + 1):
                widget.destroy()
        self._update_count()

    def _load_existing(self) -> None:
        mapping = load_symbol_mapping()
        for original, custom in mapping.items():
            self.add_row(original, custom)
        self._update_count()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save_mapping(self) -> None:
        mapping: dict[str, str] = {}
        for orig_var, custom_var, _ in self._rows:
            original = orig_var.get().strip().upper()
            custom = custom_var.get().strip()
            if not original or not custom:
                continue
            mapping[original] = custom
        try:
            save_symbol_mapping(mapping)
            self._on_close()
        except Exception as e:
            messagebox.showerror("Save Failed", f"Could not save mapping:\n{e}")

    # ------------------------------------------------------------------
    # Canvas / scroll / sync helpers
    # ------------------------------------------------------------------

    def _sync_column_widths(self, event: object = None) -> None:
        self.win.update_idletasks()
        total = self.canvas.winfo_width()
        if total < 10:
            return
        action_w = 72
        col_w = (total - action_w) // 2
        self.rows_frame.columnconfigure(0, minsize=col_w, weight=1)
        self.rows_frame.columnconfigure(1, minsize=col_w, weight=1)
        self.rows_frame.columnconfigure(2, minsize=action_w)
        self._hdr.columnconfigure(0, minsize=col_w, weight=1)
        self._hdr.columnconfigure(1, minsize=col_w, weight=1)
        self._hdr.columnconfigure(2, minsize=action_w)

    def _on_frame_configure(self, event: object = None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: object) -> None:
        if hasattr(event, "width"):
            w = getattr(event, "width")
            self.canvas.itemconfig(self.canvas_window, width=w)
        self._sync_column_widths()

    def _on_mousewheel(self, event: object) -> None:
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
