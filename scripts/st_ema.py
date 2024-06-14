import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime
from math import ceil, floor
from CaChannel.util import caget
import epics
import time

SAVE_FILE_FOLDER = 'C:\\Users\\EMALAB\\Desktop\\TW_DAQ\\DATA\\scans\\'

prefix = 'LaserLab:'

st.title("LaserLab distrubution")

# Sidebar Inputs
n_lasers = 4
laser_id = st.sidebar.selectbox("Laser ID", list(range(1, n_lasers+1)))
nbins = st.sidebar.number_input("Number of Bins", min_value=1, value=400)
wavenumber_bin = st.sidebar.number_input("Wavenumber Bin Size (MHz)", value=0.1)
record_data = st.sidebar.checkbox("Record Data")

data = np.random.normal(loc=5000, scale=1000, size=10000)
hist, bins = np.histogram(data, bins=nbins)

fig = px.histogram(x=bins[:-1], y=hist, nbins=nbins, title="Wavenumber Histogram")
st.plotly_chart(fig, use_container_width=True)

if record_data:
    file_tsamp = "{:%Y_%m_%d_%H_%M_%S}".format(datetime.now())
    file_name = SAVE_FILE_FOLDER + file_tsamp + '.csv'
    np.savetxt(file_name, np.column_stack([bins[:-1], hist]), delimiter=',')



wavenumber = caget(f'LaserLab:wavenumber_{laser_id}')
st.sidebar.write(f"Current Wavenumber: {wavenumber}")

def rcord_wavenumber():
    pass

def update_histogram():
    global data, hist, bins
    new_data = np.random.normal(loc=5000, scale=1000, size=1000)  # Replace with actual data acquisition
    data = np.concatenate((data, new_data))
    hist, bins = np.histogram(data, bins=nbins)
    return hist, bins

# Add button to update histogram
if st.button("Update Histogram"):
    hist, bins = update_histogram()
    fig = px.histogram(x=bins[:-1], y=hist, nbins=nbins, title="Wavenumber Histogram")
    st.plotly_chart(fig, use_container_width=True)


# Streamlit main loop
if __name__ == '__main__':
    st.write("LaserLab Acquisition and Analysis")

