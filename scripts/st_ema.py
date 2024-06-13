import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from epics import caget

# Constants
CHANNELS = {1: 8, 2: 15}
SAVE_FILE_FOLDER = 'T:\\RAPTOR\\DAQ\\scans\\'

# Initialize variables
data = pd.DataFrame(columns=['timestamp', 'wavenumber', 'bunch_no', 'events_per_bunch', 'channel', 'delta_t'])
record_file = None
file_name = None

def read_wavenumber():
    return caget('LaserLab:wavenumber_3')

def load_data():
    # Simulating loading data
    new_data = {
        'timestamp': pd.Timestamp.now(),
        'wavenumber': np.random.uniform(400, 800),
        'bunch_no': np.random.randint(1, 100),
        'events_per_bunch': np.random.randint(1, 100),
        'channel': np.random.choice([1, 2]),
        'delta_t': np.random.uniform(0, 1)
    }
    return new_data

def save_data(data):
    global record_file, file_name
    if record_file is not None:
        data.to_csv(record_file, mode='a', header=False)

def start_recording():
    global record_file, file_name
    file_tsamp = "{:%Y_%m_%d_%H_%M_%S}".format(pd.Timestamp.now())
    file_name = SAVE_FILE_FOLDER + file_tsamp + '.csv'
    record_file = open(file_name, 'a')
    data.to_csv(record_file, mode='a', header=True)

def stop_recording():
    global record_file
    if record_file is not None:
        record_file.close()
        record_file = None

def plot_histogram(data, channel):
    if channel:
        filtered_data = data[data['channel'] == channel]
    else:
        filtered_data = data
    fig = px.histogram(filtered_data, x='wavenumber', nbins=30, title='Wavenumber Histogram')
    st.plotly_chart(fig)

st.title('LaserLab Data Acquisition')

# Channel selection
channel = st.selectbox('Select Channel', options=[None, 1, 2], index=0, format_func=lambda x: f'Channel {x}' if x else 'All Channels')

# Data acquisition and recording
if st.button('Load Data'):
    new_data = load_data()
    data = data.append(new_data, ignore_index=True)
    save_data(data)

# Recording options
record = st.checkbox('Record Data')
if record:
    if record_file is None:
        start_recording()
else:
    if record_file is not None:
        stop_recording()

# Plot histogram
plot_histogram(data, channel)

st.write(data)
