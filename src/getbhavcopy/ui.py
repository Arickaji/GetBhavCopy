from tkinter import Label , Entry , Button , Tk , StringVar , END , Frame , CENTER , GROOVE 
from datetime import datetime
from tkinter import filedialog
from tkinter import ttk
from tkinter.ttk import Style
from tkinter import messagebox
from getbhavcopy.core import GetBhavCopy as GBC
import json as js
import os



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
                try:
                    month_entry.focus()
                    month_entry.select_range(0, 'end')
                    month_entry.icursor('end')
                except NameError as e:
                    print(e)
                else:
                    month_entry.focus()
                    month_entry.icursor(END)
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
                try:
                    year_entry.focus()
                    year_entry.select_range(0, 'end')
                    year_entry.icursor('end')
                except NameError as e:
                    print(e)
                else:
                    year_entry.focus()
                    year_entry.select_range(0, 'end')
                    year_entry.icursor('end')
                # year.set("")


def limitSizeYear(*args):
    value = year.get()
    if value != "":
        if not value.isdigit():
            year.set("")
        else:
            if len(value) > 4:
                year.set(value[:4])
            if len(value) >= 4:
                try:
                    Endday_entry.focus()
                    Endday_entry.select_range(0, 'end')
                    Endday_entry.icursor('end')
                except NameError as e:
                    print(e)
                else:
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
                try:
                    Endmonth_entry.focus()
                    Endmonth_entry.select_range(0, 'end')
                    Endmonth_entry.icursor('end')
                except NameError as e:
                    print(e)
                else:
                    Endmonth_entry.focus()
                    Endmonth_entry.icursor(END)
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
                try:
                    Endyear_entry.focus()
                    Endyear_entry.select_range(0, 'end')
                    Endyear_entry.icursor('end')
                except NameError as e:
                    print(e)
                else:
                    Endyear_entry.focus()
                    Endyear_entry.select_range(0, 'end')
                    Endyear_entry.icursor('end')
                # year.set("")


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
    if path != "":
        FolderPathAnswer["text"] = path
        if not os.path.exists("SaveDirPath.json"):
            with open("SaveDirPath.json" , "r+") as f:
                data = js.load(f)
                data["DirPath"] = f"{path}"
                f.seek(0)  # rewind
                js.dump(data, f)
                f.truncate()
        else:
            with open("SaveDirPath.json" , "r+") as f:
                data = js.load(f)
                data["DirPath"] = f"{path}"
                f.seek(0)  # rewind
                js.dump(data, f)
                f.truncate()
    else:
       FolderPathAnswer["text"] = "Current Folder Location"

def GetData():
    # pb["value"] = 85
    StartingDate = year.get() + "-" + month.get() + "-" + day.get()
    EndingDate = Endyear.get() + "-" + Endmonth.get() + "-" + Endday.get()

        

    b = GBC.GetBhavCopy(StartingDate , EndingDate , FolderPathAnswer["text"] , pb , root)

    returnValue = b.get_bhavcopy()

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
    
    #returnValue.to_csv("bhavcopy.csv", index=False)
    with open("../SaveDirPath.json", "r") as f:
        config_file = js.load(f)

    pb["value"] = 100
    root.update_idletasks()

    returnValue.to_csv(f"{config_file['DirPath']}/{StartingDate}_{EndingDate}_bhavcopy.txt", sep="\t", index=False)
    successBox = messagebox.showinfo("BhavCopy - Aric Kaji","✅ BhavCopy Data has been saved successfully") 
    if successBox:
        pb["value"] = 0

root = Tk()
root.title("GetBhavCopy Downloader - NSE EQ Cash Segment - By Aric Kaji")
root.geometry("800x400")
width = 600 # Width 
height = 220 # Height

screen_width = root.winfo_screenwidth()  # Width of the screen
screen_height = root.winfo_screenheight() # Height of the screen
 
# Calculate Starting X and Y coordinates for Window
x = (screen_width/2) - (width/2)
y = (screen_height/2) - (height/2)
 
root.geometry('%dx%d+%d+%d' % (width + 3, height, x, y))
# root.resizable(0, 0)

#### start date

rootFrame = Frame(root, width=width, height=height)
rootFrame.place(x=0, y=0)


StartLabel = Label(rootFrame, text="Start Date :" , font=("SF Pro", 14))
StartLabel.place(x=width-580, y=height-210)

currentDate = datetime.today().strftime("%d-%m-%Y")

day = StringVar()  # date
day.trace('w', limitSizeDay)
day_entry = Entry(rootFrame, textvar=day, width=4,
                  font=("SF Pro", 12 , "bold"), justify=CENTER)
day_entry.place(x=width-480, y=height-207)
day.set(currentDate.split("-")[0])

month = StringVar()  # month
month.trace('w', limitSizeMonth)
month_entry = Entry(rootFrame, textvar=month, width=4,
                    font=("SF Pro", 12 , "bold"), justify=CENTER)
month_entry.place(x=width-440, y=height-207)
month.set(currentDate.split("-")[1])

year = StringVar()  # year
year.trace('w', limitSizeYear)
year_entry = Entry(rootFrame, textvar=year, width=6,
                   font=("SF Pro", 12 , "bold"), justify=CENTER)
year_entry.place(x=width-400, y=height-207)
# year_entry.bind("<Return>" , GetData)
year.set(currentDate.split("-")[2])

# #### end date

EndDateLabel = Label(rootFrame, text="End Date :" , font=("SF Pro", 14))
EndDateLabel.place(x=width-300, y=height-210)

Endday = StringVar()  # date
Endday.trace('w', EndlimitSizeDay)
Endday_entry = Entry(rootFrame, textvar=Endday, width=4,
                  font=("SF Pro", 12 , "bold"), justify=CENTER)
Endday_entry.place(x=width-205, y=height-207)
Endday.set(currentDate.split("-")[0])

Endmonth = StringVar()  # month
Endmonth.trace('w', EndlimitSizeMonth)
Endmonth_entry = Entry(rootFrame, textvar=Endmonth, width=4,
                    font=("SF Pro", 12 , "bold"), justify=CENTER)
Endmonth_entry.place(x=width-165, y=height-207)
Endmonth.set(currentDate.split("-")[1])

Endyear = StringVar()  # year
Endyear.trace('w', EndlimitSizeYear)
Endyear_entry = Entry(rootFrame, textvar=Endyear, width=6,
                   font=("SF Pro", 12 , "bold"), justify=CENTER)
Endyear_entry.place(x=width-125, y=height-207)
# year_entry.bind("<Return>" , GetData)
Endyear.set(currentDate.split("-")[2])


# #### Folder Path

FolderPathLabel = Label(rootFrame, text="Folder Path :" , font=("SF Pro", 14))
FolderPathLabel.place(x=width-580, y=height-160)

FolderPathButton = Button(rootFrame, text="Select Folder", font=("SF Pro", 10) , command=GetFolderPath , cursor="hand2")
FolderPathButton.place(x=width-450, y=height-160)

FolderPathAnswer = Label(rootFrame, font=("SF Pro", 12 , "bold"))
FolderPathAnswer.place(x=width-350, y=height-160)

with open("../SaveDirPath.json", "r") as f:
    config_file = js.load(f)

FolderPathAnswer["text"] = config_file["DirPath"]

s = Style()
s.theme_use("alt")
s.configure("TProgressbar", thickness=20 , background="green" , foreground="green")

pb = ttk.Progressbar(
    rootFrame,
    orient='horizontal',
    mode='determinate',
    length=570,
    style="TProgressbar",
    maximum=100
)
pb.place(x=width-580, y=height-110)

GetData = Button(rootFrame, text="Get Data", font=("SF Pro", 10 , "bold"), width=70 , relief=GROOVE , command=GetData , cursor="hand2")
GetData.place(x=width-580, y=height-80)

ExitBtn = Button(rootFrame, text="Exit", font=("SF Pro", 10 , "bold"), width=70 , relief=GROOVE , command=root.destroy , cursor="hand2")
ExitBtn.place(x=width-580, y=height-50)

# if not os.path.exists("SaveDirPath.json"):
#     with open("SaveDirPath.json" , "w") as f:
#         f.write('{"DirPath": "None"}')
# else:
#     with open("SaveDirPath.json" , "r") as f:
#         fileData = js.load(f)
#         FolderPathAnswer["text"] = fileData["DirPath"]

root.mainloop()
