import time
import numpy as np
from CaChannel.util import caget
import matplotlib.pyplot as plt
import pandas as pd
import ntplib
from time import ctime
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

class EMAServerReader:
    def __init__(self,
                 pv_name,
                 saving_dir=None,
                 reading_frequency=0.01,
                 saving_interval=1,
                 verbose=False):
        self.name = pv_name
        self.saving_dir = saving_dir
        self.ntp_client = ntplib.NTPClient()
        self.dataframe = None
        self.saving_interval = saving_interval
        self.reading_frequency = reading_frequency
        self.date_format = '%a %b %d %H:%M:%S %Y'
        self.verbose = verbose
        
    def get_time_from_network(self):
        try:
            response = self.ntp_client.request('pool.ntp.org')
            ct = ctime(response.tx_time)
            dt = datetime.strptime(ct, self.date_format)
            return dt.timestamp()
        except Exception as e:
            if self.verbose:
                print(f"Error getting time from network: {e}")
            return None
        
    def get_time(self, last_time):
        if last_time is None:
            return self.get_time_from_network()
        local_time = time.time()
        time_diff = local_time - last_time
        return last_time + time_diff
        
    def get_read_value(self):
        try:
            return caget(self.name)
        except Exception as e:
            if self.verbose:
                print(f"Error reading value for {self.name}: {e}")
            return None
    
    def get_batch(self, n_samples=100):
        batch_data = []
        last_time = self.get_time_from_network()
        for _ in range(n_samples):
            current_time = self.get_time(last_time)
            scalar = self.get_read_value()
            if current_time is not None and scalar is not None:
                batch_data.append({'time': current_time, 'value': scalar})
            last_time = current_time
            time.sleep(self.reading_frequency)
        return batch_data
    
    def start_reading(self, saving_time=None):
        t0 = self.get_time_from_network()
        if t0 is None:
            if self.verbose:
                print("Failed to get initial network time. Exiting.")
            return
        last_time = t0
        if not saving_time:
            saving_time = self.saving_interval
        
        while True:
            payload = self.get_batch()
            if not payload:
                if self.verbose:
                    print("Failed to get payload. Continuing.")
                time.sleep(self.reading_frequency)
                continue

            current_time = payload[-1]['time']
            if self.verbose:
                print(payload)
                
            if self.saving_dir is not None and (current_time - t0) >= saving_time:
                self.update_df(payload)
                self.save_df()
                t0 = current_time  # Reset the saving time interval
            last_time = current_time
            time.sleep(self.reading_frequency)
        
    def update_df(self, payload):
        df = pd.DataFrame(payload)
        if self.dataframe is None:
            self.dataframe = df
        else:
            self.dataframe = pd.concat([self.dataframe, df], ignore_index=True)
            
    def save_df(self):
        if self.dataframe is not None:
            self.dataframe.to_csv(self.saving_dir, index=False)
            if self.verbose:
                print(f"Data saved to {self.saving_dir}")

if __name__ == '__main__':
    reader = EMAServerReader(pv_name='LaserLab:wavenumber_3',
                             saving_interval=1,
                             reading_frequency=0.1,
                             saving_dir='C:\\Users\\EMALAB\\Desktop\\TW_DAQ\\DATA\\scans\\foo.csv',
                             verbose=True)
    reader.start_reading()