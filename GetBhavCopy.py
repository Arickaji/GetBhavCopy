import requests
import pandas as pd
from io import StringIO
from datetime import datetime
import os

class GetBhavCopy:
    def __init__(self , Start_date , End_date , SaveFolderName , ProgramBarValue , RootWindow):
        self.Start_date = Start_date
        self.End_date = End_date
        self.SaveFolderName = SaveFolderName
        self.ProgramBarValue = ProgramBarValue
        self.rootWindow = RootWindow

    def get_bhavcopy(self) -> pd.DataFrame:
        d = datetime.strptime(self.Start_date, "%Y-%m-%d")

        if d > datetime.strptime(self.End_date, "%Y-%m-%d"):
            raise ValueError("Start date must be before end date")
        
        

        url = f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{d.strftime('%d%m%Y')}.csv"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.nseindia.com"
        }

        self.ProgramBarValue["value"] = 10
        self.rootWindow.update_idletasks()

        r = requests.get(url, headers=headers, timeout=15)

        if r.status_code != 200 or len(r.text) < 100:
            raise ValueError("Bhavcopy not available (holiday or invalid date)")

        df = pd.read_csv(StringIO(r.text))
        df.columns = df.columns.str.strip().str.upper()

        self.ProgramBarValue["value"] = 50
        self.rootWindow.update_idletasks()

        df = df.rename(columns={
            "OPEN_PRICE": "OPEN",
            "HIGH_PRICE": "HIGH",
            "LOW_PRICE": "LOW",
            "CLOSE_PRICE": "CLOSE",
            "TTL_TRD_QNTY": "VOLUME"
        })

        # DATE comes from URL — safest
        df["DATE"] = d.strftime("%Y-%m-%d")

        self.ProgramBarValue["value"] = 80
        self.rootWindow.update_idletasks()

        return df[[
            "SYMBOL",
            "DATE",
            "OPEN",
            "HIGH",
            "LOW",
            "CLOSE",
            "VOLUME"
        ]]
