import requests
import pandas as pd
from io import StringIO
from datetime import datetime

class GetBhavCopy:
    def __init__(self , Start_date , End_date , SaveFolderName , ProgramBarValue , RootWindow):
        self.Start_date = Start_date
        self.End_date = End_date
        self.SaveFolderName = SaveFolderName
        self.ProgramBarValue = ProgramBarValue
        self.rootWindow = RootWindow
    
    def _progress(self, value: int) -> None:
        if self.ProgramBarValue is not None:
            self.ProgramBarValue["value"] = value
        if self.rootWindow is not None:
            self.rootWindow.update_idletasks()

    def get_nse_indices_data(self) -> pd.DataFrame:
        d = datetime.strptime(self.Start_date, "%Y-%m-%d")

        url = f"https://nsearchives.nseindia.com/content/indices/ind_close_all_{d.strftime('%d%m%Y')}.csv"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.nseindia.com"
        }

        r = requests.get(url, headers=headers, timeout=15)

        if r.status_code != 200:
            raise ValueError("Bhavcopy not available (holiday or invalid date)")

        text = r.text.strip()
        if "\n" not in text:
            raise ValueError("Bhavcopy not available (holiday or invalid date)")

        df = pd.read_csv(StringIO(r.text))
        df.columns = df.columns.str.strip().str.upper()

        df = df.rename(columns={
            "INDEX NAME" : "SYMBOL",
            'INDEX DATE' : "DATE",
            "OPEN INDEX VALUE": "OPEN",
            "HIGH INDEX VALUE": "HIGH",
            "LOW INDEX VALUE": "LOW",
            "CLOSING INDEX VALUE": "CLOSE",
            "VOLUME": "VOLUME"
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

    def get_bhavcopy(self) -> pd.DataFrame:
        d = datetime.strptime(self.Start_date, "%Y-%m-%d")

        if d > datetime.strptime(self.End_date, "%Y-%m-%d"):
            raise ValueError("Start date must be before end date")
        
        
        url = f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{d.strftime('%d%m%Y')}.csv"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.nseindia.com"
        }

        self._progress(10)

        r = requests.get(url, headers=headers, timeout=15)

        if r.status_code != 200:
            raise ValueError("Bhavcopy not available (holiday or invalid date)")

        text = r.text.strip()
        if "\n" not in text:
            raise ValueError("Bhavcopy not available (holiday or invalid date)")

        df = pd.read_csv(StringIO(r.text))
        df.columns = df.columns.str.strip().str.upper()

        self._progress(50)

        df = df.rename(columns={
            "OPEN_PRICE": "OPEN",
            "HIGH_PRICE": "HIGH",
            "LOW_PRICE": "LOW",
            "CLOSE_PRICE": "CLOSE",
            "TTL_TRD_QNTY": "VOLUME"
        })

        indices_data_df = self.get_nse_indices_data()

        final_df = pd.concat([df, indices_data_df], ignore_index=True, sort=False)

        # DATE comes from URL — safest
        final_df["DATE"] = d.strftime("%Y-%m-%d")

        self._progress(80)

        return final_df[[
            "SYMBOL",
            "DATE",
            "OPEN",
            "HIGH",
            "LOW",
            "CLOSE",
            "VOLUME"
        ]]
