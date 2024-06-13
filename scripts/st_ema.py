import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd
from datetime import datetime
from math import ceil, floor
from CaChannel.util import caget
import epics
import time

# Constants
SAVE_FILE_FOLDER = 'C:/Users/EMALAB/Desktop/TW_DAQ/DATA/scans/'

# EPICS Prefix
prefix = 'LaserLab:'

# Streamlit App
st.title("LaserLab Acquisition and Analysis")

# Sidebar Inputs
nbins = st.sidebar.number_input("Number of Bins", min_value=1, value=400)
tdc_start = st.sidebar.number_input("TDC Start", value=0.0)
tdc_stop = st.sidebar.number_input("TDC Stop", value=10.0)
tdc_bin = st.sidebar.number_input("TDC Bin Size", value=0.1)
wavenumber_bin = st.sidebar.number_input("Wavenumber Bin Size (MHz)", value=0.1)
record_data = st.sidebar.checkbox("Record Data")

# Generate some dummy data for demonstration purposes
data = np.random.normal(loc=5000, scale=1000, size=10000)
hist, bins = np.histogram(data, bins=nbins)

# Plot Histogram
fig = px.histogram(x=bins[:-1], y=hist, nbins=nbins, title="Wavenumber Histogram")
st.plotly_chart(fig, use_container_width=True)

# Record data if checkbox is selected
if record_data:
    file_tsamp = "{:%Y_%m_%d_%H_%M_%S}".format(datetime.now())
    file_name = SAVE_FILE_FOLDER + file_tsamp + '.csv'
    np.savetxt(file_name, np.column_stack([bins[:-1], hist]), delimiter=',')

# Update wavenumber based on EPICS PV
wavenumber = caget('LaserLab:wavenumber_3')
st.sidebar.write(f"Current Wavenumber: {wavenumber}")

# Function to update histogram with new data
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

# Placeholder for additional features and flexibility
# Add/remove features as needed

st.sidebar.markdown("Additional features can be added here.")

# Ensure flexibility for adding/removing features
# by organizing code into functions and modular components

# Streamlit main loop
if __name__ == '__main__':
    st.write("LaserLab Acquisition and Analysis")

