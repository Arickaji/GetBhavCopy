import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
import requests

from getbhavcopy.settings_windows import load_symbol_mapping

logger = logging.getLogger("getbhavcopy")


class GetBhavCopy:
    def __init__(
        self,
        Start_date,
        End_date,
        SaveFolderName,
        Output_File_Formate: str,
        ProgramBarValue=None,
        RootWindow=None,
        max_workers=8,
    ):

        self.Start_date = Start_date
        self.End_date = End_date
        self.SaveFolderName = SaveFolderName
        self.ProgramBarValue = ProgramBarValue
        self.Output_File_Formate = Output_File_Formate
        self.rootWindow = RootWindow
        self.max_workers = max_workers

        self.failed_dates: list[str] = []

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.nseindia.com",
            }
        )
        self._symbol_mapping = load_symbol_mapping()

    def _validate_response_csv(self, r):

        if r.status_code != 200:
            raise ValueError("Bhavcopy not available")

        text = (r.text or "").strip()

        if "\n" not in text:
            raise ValueError("Invalid CSV")

        return text

    def _apply_symbol_mapping(self, df):
        if not self._symbol_mapping:
            return df
        df = df.copy()
        df["SYMBOL"] = df["SYMBOL"].map(
            lambda s: self._symbol_mapping.get(str(s).strip().upper(), s)
        )
        return df

    def _progress(self, value: int) -> None:
        if hasattr(self, "_progress_callback"):
            self._progress_callback(value)
        elif self.ProgramBarValue is not None:
            self.ProgramBarValue["value"] = value
        if self.rootWindow is not None:
            self.rootWindow.update_idletasks()

    def get_equity_bhavcopy_for_date(self, d):

        url = f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{d.strftime('%d%m%Y')}.csv"

        date_str = d.strftime("%Y%m%d")

        for attempt in range(3):
            try:
                r = self.session.get(url, timeout=15)

                text = self._validate_response_csv(r)

                break

            except Exception:
                if attempt == 2:
                    raise

                time.sleep(1 + attempt)

        df = pd.read_csv(StringIO(text))

        df.columns = df.columns.str.strip().str.upper()

        df = df.rename(
            columns={
                "OPEN_PRICE": "OPEN",
                "HIGH_PRICE": "HIGH",
                "LOW_PRICE": "LOW",
                "CLOSE_PRICE": "CLOSE",
                "TTL_TRD_QNTY": "VOLUME",
            }
        )

        df["DATE"] = date_str

        df = df[["SYMBOL", "DATE", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"]]
        return self._apply_symbol_mapping(df)

    def get_nse_indices_data_for_date(self, d):

        url = f"https://nsearchives.nseindia.com/content/indices/ind_close_all_{d.strftime('%d%m%Y')}.csv"

        date_str = d.strftime("%Y%m%d")

        r = self.session.get(url, timeout=15)

        text = self._validate_response_csv(r)

        df = pd.read_csv(StringIO(text))

        df.columns = df.columns.str.strip().str.upper()

        df = df.rename(
            columns={
                "INDEX NAME": "SYMBOL",
                "INDEX DATE": "DATE",
                "OPEN INDEX VALUE": "OPEN",
                "HIGH INDEX VALUE": "HIGH",
                "LOW INDEX VALUE": "LOW",
                "CLOSING INDEX VALUE": "CLOSE",
                "VOLUME": "VOLUME",
            }
        )

        df["DATE"] = date_str

        df = df[["SYMBOL", "DATE", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"]]
        return self._apply_symbol_mapping(df)

    def process_day(self, day):

        date_str = day.strftime("%Y-%m-%d")

        file_path = os.path.join(
            self.SaveFolderName,
            (
                f"bhavcopy_{date_str}.csv"
                if self.Output_File_Formate == "CSV"
                else f"bhavcopy_{date_str}.txt"
            ),
        )

        if os.path.exists(file_path):
            logger.info(f"Skipping existing {date_str}")

            return "skipped"

        try:
            eq = self.get_equity_bhavcopy_for_date(day)

            idx = self.get_nse_indices_data_for_date(day)

            final_df = pd.concat([eq, idx], ignore_index=True)

            final_df.to_csv(file_path, index=False, header=False)

            logger.info(f"Saved {file_path}")

            return "success"

        except Exception as e:
            logger.warning(f"Failed {date_str} : {str(e)}")

            return "failed"

    def get_bhavcopy(self):

        start_time = time.time()

        logger.info("Starting Bhavcopy download")

        start = datetime.strptime(self.Start_date, "%Y-%m-%d")
        end = datetime.strptime(self.End_date, "%Y-%m-%d")

        if start > end:
            raise ValueError("Start date must be before end date")

        os.makedirs(self.SaveFolderName, exist_ok=True)

        dates: list[datetime] = []

        d = start

        while d <= end:
            if d.weekday() < 5:
                dates.append(d)

            d += timedelta(days=1)

        total = len(dates)

        logger.info(f"Trading days to process: {total}")

        completed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_day, day): day for day in dates}

            for future in as_completed(futures):
                day = futures[future]

                result = future.result()

                if result == "failed":
                    self.failed_dates.append(day.strftime("%Y-%m-%d"))

                completed += 1

                progress = int((completed / total) * 90)

                self._progress(progress)

        end_time = time.time()

        logger.info("Download completed")
        logger.info(f"Total trading days: {total}")
        logger.info(f"Failed days: {len(self.failed_dates)}")
        logger.info(f"Execution time: {round(end_time - start_time, 2)} seconds")
