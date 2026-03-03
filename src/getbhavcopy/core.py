import requests
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
from typing import List
class GetBhavCopy:
    def __init__(self , Start_date , End_date , SaveFolderName , ProgramBarValue , RootWindow):
        self.Start_date = Start_date
        self.End_date = End_date
        self.SaveFolderName = SaveFolderName
        self.ProgramBarValue = ProgramBarValue
        self.rootWindow = RootWindow

    def _validate_response_csv(self, r) -> str:
        if r.status_code != 200:
            raise ValueError("Bhavcopy not available (holiday or invalid date)")
        text = (r.text or "").strip()
        if "\n" not in text:
            raise ValueError("Bhavcopy not available (holiday or invalid date)")
        return text
    
    def _progress(self, value: int) -> None:
        if self.ProgramBarValue is not None:
            self.ProgramBarValue["value"] = value
        if self.rootWindow is not None:
            self.rootWindow.update_idletasks()

    def get_nse_indices_data_for_date(self , d : datetime) -> pd.DataFrame:
        url = f"https://nsearchives.nseindia.com/content/indices/ind_close_all_{d.strftime('%d%m%Y')}.csv"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.nseindia.com"
        }

        r = requests.get(url, headers=headers, timeout=15)
        text = self._validate_response_csv(r)

        df = pd.read_csv(StringIO(text))
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

    def get_equity_bhavcopy_for_date(self, d: datetime) -> pd.DataFrame:
        url = f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{d.strftime('%d%m%Y')}.csv"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com"}

        r = requests.get(url, headers=headers, timeout=15)
        text = self._validate_response_csv(r)

        df = pd.read_csv(StringIO(text))
        df.columns = df.columns.str.strip().str.upper()

        df = df.rename(columns={
            "OPEN_PRICE": "OPEN",
            "HIGH_PRICE": "HIGH",
            "LOW_PRICE": "LOW",
            "CLOSE_PRICE": "CLOSE",
            "TTL_TRD_QNTY": "VOLUME",
        })

        df["DATE"] = d.strftime("%Y-%m-%d")

        return df[["SYMBOL", "DATE", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"]]

    def get_bhavcopy(self) -> pd.DataFrame:
        start = datetime.strptime(self.Start_date, "%Y-%m-%d")
        end = datetime.strptime(self.End_date, "%Y-%m-%d")

        if start > end:
            raise ValueError("Start date must be before end date")

        # Build list of weekdays in range (Mon-Fri)
        dates: List[datetime] = []
        d = start
        while d <= end:
            if d.weekday() < 5:  # 0=Mon ... 4=Fri
                dates.append(d)
            d += timedelta(days=1)

        if not dates:
            # Range contains only weekends
            return pd.DataFrame(columns=["SYMBOL", "DATE", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"])

        all_frames: List[pd.DataFrame] = []
        failed_dates: List[str] = []

        total = len(dates)
        for i, day in enumerate(dates, start=1):
            # progress: 0..90 while downloading, keep last 10% for UI saving
            self._progress(int((i - 1) / total * 90))

            try:
                eq = self.get_equity_bhavcopy_for_date(day)
                idx = self.get_nse_indices_data_for_date(day)
                all_frames.append(pd.concat([eq, idx], ignore_index=True, sort=False))
            except Exception:
                # Skip missing/blocked days (holiday/invalid date/403/etc.)
                failed_dates.append(day.strftime("%Y-%m-%d"))
                continue
        
        self.failed_dates = failed_dates  # optional: lets UI show “skipped dates”

        if not all_frames:
            return pd.DataFrame(columns=["SYMBOL", "DATE", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"])

        final_df = pd.concat(all_frames, ignore_index=True, sort=False)
        self._progress(90)
        return final_df[["SYMBOL", "DATE", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"]]