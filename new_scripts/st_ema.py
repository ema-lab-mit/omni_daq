import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime
import time
from threading import Thread
from served_reader import EMAServerReader

SAVE_FILE_FOLDER = 'C:\\Users\\EMALAB\\Desktop\\TW_DAQ\\DATA\\scans\\'
prefix = 'LaserLab:'

st.title("LaserLab Distribution")

# Sidebar Inputs
n_lasers = 4
laser_id = st.sidebar.selectbox("Laser ID", list(range(1, n_lasers + 1)))
nbins = st.sidebar.number_input("Number of Bins", min_value=1, value=400)
wavenumber_bin = st.sidebar.number_input("Wavenumber Bin Size (MHz)", value=0.1)
record_data = st.sidebar.checkbox("Record Data")

# Initialize the EMAServerReader
pv_name = f'{prefix}wavenumber_{laser_id}'
reader = EMAServerReader(pv_name=pv_name, verbose=True)

# Data storage
data = np.array([])
timestamps = []

def update_histogram(batch_data):
    global data, timestamps
    new_data = [entry['value'] for entry in batch_data]
    new_timestamps = [datetime.fromtimestamp(entry['time']) for entry in batch_data]

    data = np.append(data, new_data)
    timestamps.extend(new_timestamps)

    hist, bins = np.histogram(data, bins=nbins)
    return hist, bins

# Function to update the time series plot
def update_timeseries():
    if len(timestamps) > 0:
        df = pd.DataFrame({'Timestamp': timestamps, 'Wavenumber': data})
        fig = px.line(df, x='Timestamp', y='Wavenumber', title="Wavenumber Time Series")
        st.plotly_chart(fig, use_container_width=True)

# Function to update the display
def update_display():
    batch_data = reader.get_batch()
    if batch_data:
        hist, bins = update_histogram(batch_data)
        if hist is not None and bins is not None:
            fig = px.histogram(x=bins[:-1], y=hist, nbins=nbins, title="Wavenumber Histogram")
            st.plotly_chart(fig, use_container_width=True)
            update_timeseries()

        # Save data if recording is enabled
        if record_data:
            file_tsamp = "{:%Y_%m_%d_%H_%M_%S}".format(datetime.now())
            file_name = SAVE_FILE_FOLDER + file_tsamp + '.csv'
            df = pd.DataFrame({'Timestamp': timestamps, 'Wavenumber': data})
            df.to_csv(file_name, index=False)
            st.sidebar.write(f"Data recorded to {file_name}")

# Add button to update histogram
if st.button("Update Histogram"):
    update_display()

# Display current wavenumber
wavenumber = reader.get_read_value()
st.sidebar.write(f"Current Wavenumber: {wavenumber}")

# Streamlit main loop
def main():
    st.write("LaserLab Acquisition and Analysis")

    # Automatically update the histogram and time series at a specified interval
    def auto_update():
        while True:
            update_display()
            time.sleep(1)  # Update interval in seconds

    # Start a background thread to update the histogram and time series automatically
    update_thread = Thread(target=auto_update)
    update_thread.daemon = True
    update_thread.start()

main()