from tkinter import Label , Entry , Button, LabelFrame , Tk , StringVar, Frame , CENTER , GROOVE 
from datetime import datetime
from tkinter import filedialog
from tkinter import ttk
from tkinter.ttk import Style
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from getbhavcopy.core import GetBhavCopy
import json as js
import os
from pathlib import Path
from getbhavcopy.logging_config import setup_logging
import logging

# Initialize logging ONCE here
setup_logging(debug=True)

class TkinterLogHandler(logging.Handler):

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)

        def append():
            if record.levelno >= logging.ERROR:
                self.text_widget.insert("end", msg + "\n", "ERROR")
            elif record.levelno >= logging.WARNING:
                self.text_widget.insert("end", msg + "\n", "WARNING")
            else:
                self.text_widget.insert("end", msg + "\n")

            self.text_widget.see("end")

        self.text_widget.after(0, append)
        
def get_config_path() -> Path:
    appdata = os.getenv("APPDATA")
    base = Path(appdata) / "GetBhavCopy" if appdata else Path.home() / ".getbhavcopy"
    base.mkdir(parents=True, exist_ok=True)
    return base / "SaveDirPath.json"

def load_config() -> dict:
    path = get_config_path()
    if not path.exists():
        default = {"DirPath": str(Path.cwd())}
        path.write_text(js.dumps(default, indent=2))
        return default
    return js.loads(path.read_text())

def save_config(cfg: dict) -> None:
    path = get_config_path()
    path.write_text(js.dumps(cfg, indent=2))

def limitSizeDay(*args):
    value = day.get()
    # if int(value) > 31 or (str(value.lower()) >= 'a' and str(value.upper()) <= 'z'):
    if value != "":
        if not value.isdigit() or int(value) > 31:
            day.set("")
        else:
            if len(value) > 2:
                day.set(value[:2])
            if len(value) >= 2:
                if "month_entry" in globals():
                    month_entry.focus()
                    month_entry.select_range(0, 'end')
                    month_entry.icursor('end')

def limitSizeMonth(*args):
    value = month.get()
    if value != "":
        if not value.isdigit() or int(value) > 12:
            month.set("")
        else:
            if len(value) > 2:
                month.set(value[:2])
            if len(value) >= 2:
                if "year_entry" in globals():
                    year_entry.focus()
                    year_entry.select_range(0, 'end')
                    year_entry.icursor('end')

def limitSizeYear(*args):
    value = year.get()
    if value != "":
        if not value.isdigit():
            year.set("")
        else:
            if len(value) > 4:
                year.set(value[:4])
            if len(value) >= 4:
                if "Endday_entry" in globals():
                    Endday_entry.focus()
                    Endday_entry.select_range(0, 'end')
                    Endday_entry.icursor('end')

def EndlimitSizeDay(*args):
    value = Endday.get()
    # if int(value) > 31 or (str(value.lower()) >= 'a' and str(value.upper()) <= 'z'):
    if value != "":
        if not value.isdigit() or int(value) > 31:
            Endday.set("")
        else:
            if len(value) > 2:
                Endday.set(value[:2])
            if len(value) >= 2:
                if "Endmonth_entry" in globals():
                    Endmonth_entry.focus()
                    Endmonth_entry.select_range(0, 'end')
                    Endmonth_entry.icursor('end')

def EndlimitSizeMonth(*args):
    value = Endmonth.get()
    if value != "":
        if not value.isdigit() or int(value) > 12:
            Endmonth.set("")
        else:
            if len(value) > 2:
                Endmonth.set(value[:2])
            if len(value) >= 2:
                if "Endyear_entry" in globals():
                    Endyear_entry.focus()
                    Endyear_entry.select_range(0, 'end')
                    Endyear_entry.icursor('end')

def EndlimitSizeYear(*args):
    value = Endyear.get()
    if value != "":
        if not value.isdigit():
            Endyear.set("")
        else:
            if len(value) > 4:
                Endyear.set(value[:4])

def GetFolderPath():
    path= filedialog.askdirectory(title="Select a Folder")
    if path:
        FolderPathAnswer["text"] = path
        cfg = load_config()
        cfg["DirPath"] = path
        save_config(cfg)
    else:
        FolderPathAnswer["text"] = "Current Folder Location"

def clear_logs():
    log_box.delete("1.0", "end")

def handle_get_data():
    # pb["value"] = 85

    GetDataBtn.config(state="disabled")

    status_var.set("Status: Downloading data...")
    root.update_idletasks()

    StartingDate = year.get() + "-" + month.get() + "-" + day.get()
    EndingDate = Endyear.get() + "-" + Endmonth.get() + "-" + Endday.get()

    b = GetBhavCopy(StartingDate , EndingDate , FolderPathAnswer["text"] , pb , root)

    returnValue = b.get_bhavcopy()

    skipped = getattr(b, "failed_dates", [])
    if skipped:
        messagebox.showwarning(
            "GetBhavCopy",
            "Some dates were skipped (holiday/unavailable):\n" + "\n".join(skipped[:10]) +
            ("" if len(skipped) <= 10 else f"\n...and {len(skipped)-10} more")
        )

    pb["value"] = 90
    root.update_idletasks()

    if returnValue.empty:
        msgBox = messagebox.showerror("GetBhavCopy", "No Data Downloaded")
        if msgBox:
            pb["value"] = 0
            currentDate = datetime.today().strftime("%d-%m-%Y")
            day.set(currentDate.split("-")[0])
            month.set(currentDate.split("-")[1])
            year.set(currentDate.split("-")[2])
            Endday.set(currentDate.split("-")[0])
            Endmonth.set(currentDate.split("-")[1])
            Endyear.set(currentDate.split("-")[2])
    
    #loading config for saved dir path
    config_file = load_config()

    pb["value"] = 100
    root.update_idletasks()

    out_dir = Path(config_file["DirPath"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{StartingDate}_{EndingDate}_bhavcopy.txt"
    returnValue.to_csv(out_path, sep="\t", index=False)

    successBox = messagebox.showinfo("BhavCopy - Aric Kaji","✅ BhavCopy Data has been saved successfully") 
    if successBox:
        pb["value"] = 0

    status_var.set("Status: Completed")
    GetDataBtn.config(state="normal")

root = Tk()
root.title("GetBhavCopy Downloader - NSE EQ Cash Segment - By Aric Kaji")
#root.geometry("700x550")
root.geometry("820x650")
#root.minsize(850, 600)
root.configure(bg="#1e1e1e")
width = 700 # Width 
height = 550 # Height

screen_width = root.winfo_screenwidth()  # Width of the screen
screen_height = root.winfo_screenheight() # Height of the screen
 
# Calculate Starting X and Y coordinates for Window
x = (screen_width/2) - (width/2)
y = (screen_height/2) - (height/2)
 
root.geometry('%dx%d+%d+%d' % (width + 3, height, x, y))
root.resizable(0, 0)

# ================= MAIN CONTAINER =================
main = Frame(root, bg="#1e1e1e", width=width, height=height)
main.pack(fill="both", expand=True, padx=30, pady=20)

# ================= TITLE =================
title = Label(
    main,
    text="GetBhavCopy Downloader",
    font=("SF Pro", 26, "bold"),
    fg="white",
    bg="#1e1e1e"
)
title.pack(pady=(0, 5))

subtitle = Label(
    main,
    text="NSE Equity & Indices Data Extraction Tool",
    font=("SF Pro", 13),
    fg="#bbbbbb",
    bg="#1e1e1e"
)
subtitle.pack(pady=(0, 5))

# ================= DATE FRAME =================
date_frame = LabelFrame(
    main,
    text=" Date Range ",
    font=("SF Pro", 12, "bold"),
    fg="white",
    bg="#1e1e1e",
    labelanchor="n"
)
date_frame.pack(fill="x", pady=5, ipady=5)

date_frame.columnconfigure(0, weight=1)
date_frame.columnconfigure(1, weight=1)

# Start Date
start_frame = Frame(date_frame, bg="#1e1e1e")
start_frame.grid(row=0, column=0, padx=20)

Label(start_frame, text="Start Date",
      bg="#1e1e1e", fg="white").pack(pady=5)

currentDate = datetime.today().strftime("%d-%m-%Y")

day = StringVar()  # date
day.trace('w', limitSizeDay)
day_entry = Entry(start_frame, textvar=day, width=4,
                  font=("SF Pro", 12 , "bold"), justify=CENTER)
#day_entry.place(x=width-480, y=height-207)
day.set(currentDate.split("-")[0])

month = StringVar()  # month
month.trace('w', limitSizeMonth)
month_entry = Entry(start_frame, textvar=month, width=4,
                    font=("SF Pro", 12 , "bold"), justify=CENTER)
#month_entry.place(x=width-440, y=height-207)
month.set(currentDate.split("-")[1])

year = StringVar()  # year
year.trace('w', limitSizeYear)
year_entry = Entry(start_frame, textvar=year, width=6,
                   font=("SF Pro", 12 , "bold"), justify=CENTER)
#year_entry.place(x=width-400, y=height-207)
# year_entry.bind("<Return>" , GetData)
year.set(currentDate.split("-")[2])

day_entry.pack(in_=start_frame, side="left", padx=5)
month_entry.pack(in_=start_frame, side="left", padx=5)
year_entry.pack(in_=start_frame, side="left", padx=5)

# End Date
end_frame = Frame(date_frame, bg="#1e1e1e")
end_frame.grid(row=0, column=1, padx=20)

Label(end_frame, text="End Date",
      bg="#1e1e1e", fg="white").pack(pady=5)

Endday = StringVar()  # date
Endday.trace('w', EndlimitSizeDay)
Endday_entry = Entry(end_frame, textvar=Endday, width=4,
                  font=("SF Pro", 12 , "bold"), justify=CENTER)
#Endday_entry.place(x=width-205, y=height-207)
Endday.set(currentDate.split("-")[0])

Endmonth = StringVar()  # month
Endmonth.trace('w', EndlimitSizeMonth)
Endmonth_entry = Entry(end_frame, textvar=Endmonth, width=4,
                    font=("SF Pro", 12 , "bold"), justify=CENTER)
#Endmonth_entry.place(x=width-165, y=height-207)
Endmonth.set(currentDate.split("-")[1])

Endyear = StringVar()  # year
Endyear.trace('w', EndlimitSizeYear)
Endyear_entry = Entry(end_frame, textvar=Endyear, width=6,
                   font=("SF Pro", 12 , "bold"), justify=CENTER)
#Endyear_entry.place(x=width-125, y=height-207)
Endyear.set(currentDate.split("-")[2])

Endday_entry.pack(in_=end_frame, side="left", padx=5)
Endmonth_entry.pack(in_=end_frame, side="left", padx=5)
Endyear_entry.pack(in_=end_frame, side="left", padx=5)

# ================= FOLDER FRAME =================
folder_frame = LabelFrame(
    main,
    text=" Output Folder ",
    font=("SF Pro", 12, "bold"),
    fg="white",
    bg="#1e1e1e"
)
folder_frame.pack(fill="x", pady=5)

folder_frame.columnconfigure(1, weight=1)

FolderPathLabel = Label(folder_frame, text="Folder Path :" , font=("SF Pro", 14))
#FolderPathLabel.place(x=width-580, y=height-160)

FolderPathButton = Button(folder_frame, bg="#1e1e1e", text="Select Folder", font=("SF Pro", 10),command=GetFolderPath)
#FolderPathButton.place(x=width-450, y=height-160)

FolderPathAnswer = Label(folder_frame, font=("SF Pro", 12 , "bold"), bg="#1e1e1e")
#FolderPathAnswer.place(x=width-350, y=height-160)

FolderPathButton.grid(in_=folder_frame, row=0, column=0, padx=5, pady=5)
FolderPathAnswer.grid(in_=folder_frame, row=0, column=1, sticky="w")

config_file = load_config() # Loading config for saved dir path
FolderPathAnswer["text"] = config_file.get("DirPath", str(Path.cwd()))

# ================= PROGRESS =================
s = Style()
s.theme_use("alt")
s.configure(
    "TProgressbar",
    thickness=25,
    background="#4CAF50",
    troughcolor="#2b2b2b"
)

pb = ttk.Progressbar(
    main,
    orient='horizontal',
    mode='determinate',
    length=570,
    style="TProgressbar",
    maximum=100
)

pb.pack(in_=main, fill="x", pady=10)

# ================= BUTTON FRAME =================
button_frame = Frame(main, bg="#1e1e1e")
button_frame.pack(fill="x")

GetDataBtn = Button(button_frame, text="Get Data", font=("SF Pro", 10 , "bold"), width=20 , relief=GROOVE , command=handle_get_data)
#GetDataBtn.place(x=width-580, y=height-80)
GetDataBtn.config(
    font=("SF Pro", 12, "bold"),
    relief="flat"
)

ExitBtn = Button(button_frame, text="Exit", font=("SF Pro", 10 , "bold"), width=20 , relief=GROOVE , command=root.destroy)
#ExitBtn.place(x=width-580, y=height-50)

ExitBtn.config(
    font=("SF Pro", 12, "bold"),
    relief="flat"
)

ClearLogBtn = Button(
    button_frame,
    text="Clear Logs",
    font=("SF Pro", 12 , "bold"),
    relief=GROOVE,
    command=clear_logs
)

GetDataBtn.pack(side="left", expand=True, fill="x", padx=5)
ClearLogBtn.pack(side="left", expand=True, fill="x", padx=5)
ExitBtn.pack(side="left", expand=True, fill="x", padx=5)

# ================= LOG FRAME =================
log_frame = LabelFrame(
    main,
    text=" Application Logs ",
    font=("SF Pro", 12, "bold"),
    fg="white",
    bg="#1e1e1e"
)
log_frame.pack(fill="both", expand=True, pady=20)

log_box = ScrolledText(
    log_frame,
    height=10,
    bg="#0f0f0f",
    fg="#d4d4d4",
    insertbackground="white",
    font=("JetBrains Mono", 10),
    state="normal"
)

log_box.pack(fill="both", expand=True)

log_box.tag_config("ERROR", foreground="#ff4d4d")
log_box.tag_config("WARNING", foreground="#ffa500")

log_box.config(
    bg="#0f0f0f",
    fg="#d4d4d4",
    insertbackground="white",
    font=("JetBrains Mono", 10)
)


status_var = StringVar()
status_var.set("Status: Ready")

status_bar = Label(
    root,
    textvariable=status_var,
    bg="#2b2b2b",
    fg="white",
    anchor="w",
    font=("SF Pro", 10)
)

status_bar.pack(fill="x", side="bottom")

# ===== CONNECT LOGGER TO UI =====
logger = logging.getLogger("getbhavcopy")

ui_handler = TkinterLogHandler(log_box)

ui_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

ui_handler.setFormatter(formatter)

logger.addHandler(ui_handler)
logger.propagate = False

logger.info("UI logging initialized successfully.")
#logger.warning("Logger test warning.")
#logger.error("Logger test error.")

root.mainloop()
