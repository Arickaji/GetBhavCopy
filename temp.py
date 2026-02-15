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
        self.temp_folder = f"{self.SaveFolderName}/data"
        self.ProgramBarValue = ProgramBarValue
        self.rootWindow = RootWindow
        if not os.path.exists(self.temp_folder):
            os.makedirs(self.temp_folder)

    def get_bhavcopy(self) -> pd.DataFrame:
        d = datetime.strptime(self.Start_date, "%Y-%m-%d")

        url = f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{d.strftime('%d%m%Y')}.csv"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.nseindia.com"
        }

        r = requests.get(url, headers=headers, timeout=15)

        if r.status_code != 200 or len(r.text) < 100:
            raise ValueError("Bhavcopy not available (holiday or invalid date)")

        df = pd.read_csv(StringIO(r.text))
        df.columns = df.columns.str.strip().str.upper()

        df = df.rename(columns={
            "OPEN_PRICE": "OPEN",
            "HIGH_PRICE": "HIGH",
            "LOW_PRICE": "LOW",
            "CLOSE_PRICE": "CLOSE",
            "TTL_TRD_QNTY": "VOLUME"
        })

        # DATE comes from URL — safest
        df["DATE"] = d.strftime("%Y-%m-%d")

        return df[[
            "SYMBOL",
            "DATE",
            "OPEN",
            "HIGH",
            "LOW",
            "CLOSE",
            "VOLUME"
        ]]


'''
df = get_bhavcopy("2024-01-02")
df.to_csv("bhavcopy.csv", index=False)
df.to_csv("bhavcopy.txt", sep="\t", index=False)
print("✅ bhavcopy.csv saved successfully")
'''
