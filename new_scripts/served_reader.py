import time
import numpy as np
from CaChannel.util import caget
import matplotlib.pyplot as plt
import pandas as pd
import ntplib
from time import ctime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import threading

class EMAServerReader:
    def __init__(self, pv_name: str, saving_dir: str = None, reading_frequency: float = 0.01,
                 saving_interval: float = 60, ntp_sync_interval: float = 3600, verbose: bool = False):
        self.name = pv_name
        self.saving_dir = saving_dir
        self.ntp_client = ntplib.NTPClient()
        self.dataframe = pd.DataFrame(columns=['time', 'value'])
        self.saving_interval = saving_interval
        self.reading_frequency = reading_frequency
        self.ntp_sync_interval = ntp_sync_interval
        self.date_format = '%a %b %d %H:%M:%S %Y'
        self.verbose = verbose
        self.last_ntp_sync_time = time.time()
        self.offset = 0
        self.reading_thread = None
        self.is_reading = False
        self.latest_data = None

    def sync_time_with_ntp(self):
        try:
            response = self.ntp_client.request('pool.ntp.org')
            ntp_time = response.tx_time
            self.offset = ntp_time - time.time()
            self.last_ntp_sync_time = time.time()
            if self.verbose:
                print(f"Time synchronized with NTP. Offset: {self.offset} seconds")
        except Exception as e:
            if self.verbose:
                print(f"Error syncing time with NTP: {e}")

    def get_time(self):
        if time.time() - self.last_ntp_sync_time > self.ntp_sync_interval:
            self.sync_time_with_ntp()
        return time.time() + self.offset

    def get_read_value(self):
        try:
            return caget(self.name)
        except Exception as e:
            if self.verbose:
                print(f"Error reading value for {self.name}: {e}")
            return None

    def get_batch(self, n_samples=100) -> List[Dict[str, Any]]:
        batch_data = []
        for _ in range(n_samples):
            current_time = self.get_time()
            scalar = self.get_read_value()
            if current_time is not None and scalar is not None:
                batch_data.append({'time': current_time, 'value': scalar})
            time.sleep(self.reading_frequency)
        return batch_data

    def start_reading(self):
        if self.is_reading:
            if self.verbose:
                print("Reading is already in progress.")
            return
        self.is_reading = True
        self.reading_thread = threading.Thread(target=self._reading_loop)
        self.reading_thread.start()

    def _reading_loop(self):
        t0 = self.get_time()
        while self.is_reading:
            payload = self.get_batch()
            if not payload:
                if self.verbose:
                    print("Failed to get payload. Continuing.")
                time.sleep(self.reading_frequency)
                continue

            current_time = payload[-1]['time']
            if self.verbose:
                print(payload)
                
            self.update_df(payload)
            self.latest_data = payload[-1]
            if self.saving_dir is not None and (current_time - t0) >= self.saving_interval:
                self.save_df()
                t0 = current_time  # Reset the saving time interval
            time.sleep(self.reading_frequency)

    def stop_reading(self):
        self.is_reading = False
        if self.reading_thread:
            self.reading_thread.join()

    def update_df(self, payload: List[Dict[str, Any]]):
        df = pd.DataFrame(payload)
        self.dataframe = pd.concat([self.dataframe, df], ignore_index=True)

    def save_df(self):
        if not self.dataframe.empty:
            self.dataframe.to_csv(self.saving_dir, index=False)
            if self.verbose:
                print(f"Data saved to {self.saving_dir}")

    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        return self.latest_data

    def get_data_frame(self) -> pd.DataFrame:
        return self.dataframe

# EXAMPLE:
def example_usage():
    reader = EMAServerReader(pv_name='LaserLab:wavenumber_3',
                             saving_interval=60,
                             reading_frequency=0.1,
                             saving_dir='C:\\Users\\EMALAB\\Desktop\\TW_DAQ\\DATA\\scans\\foo.csv',
                             verbose=True)
    reader.start_reading()
    
    import time
    from tkinter import Tk, Label, Button
    
    class DataDisplay:
        def __init__(self, master, reader):
            self.master = master
            self.reader = reader
            master.title("EMA Server Data Display")

            self.label = Label(master, text="Waiting for data...")
            self.label.pack()

            self.refresh_button = Button(master, text="Refresh", command=self.refresh_data)
            self.refresh_button.pack()

        def refresh_data(self):
            latest_data = self.reader.get_latest_data()
            if latest_data:
                self.label.config(text=f"Latest data: {latest_data}")
            else:
                self.label.config(text="No data available")

    root = Tk()
    display = DataDisplay(root, reader)
    
    root.protocol("WM_DELETE_WINDOW", lambda: (reader.stop_reading(), root.destroy()))
    root.mainloop()

if __name__ == '__main__':
    example_usage()