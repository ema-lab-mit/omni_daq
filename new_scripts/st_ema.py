import streamlit as st
import pandas as pd
import plotly.express as px
import threading
import time
from tkinter import Tk, filedialog
from served_reader import EMAServerReader  # Replace with the actual module name

# Initialize session state for readers and their data
if 'readers' not in st.session_state:
    st.session_state.readers = {}
    # autoupdate
if "autoupdate" not in st.session_state:
    st.session_state.autoupdate = False
    
if "update_interval" not in st.session_state:
    st.session_state.update_interval = 0.5

# Generate a list of predefined PV names
pv_names = ["LaserLab:wavenumber_3", "LaserLab:wavenumber_2", "LaserLab:wavenumber_1"]

def start_reader(pv_name, reading_frequency):
    if pv_name not in st.session_state.readers:
        try:
            reader = EMAServerReader(pv_name=pv_name,reading_frequency=reading_frequency, verbose=True)
            reader.start_reading()
            st.session_state.readers[pv_name] = reader
        except Exception as e:
            st.error(f"Error starting server {pv_name}: {e}")
    else:
        st.warning(f"Server {pv_name} already exists!")


def save_combined_dataframe():
    Tk().withdraw()  # Close the root window
    folder_path = filedialog.askdirectory()
    if folder_path:
        combined_df = pd.concat([reader.get_data_frame() for reader in st.session_state.readers.values()], ignore_index=True)
        combined_df.to_csv(f"{folder_path}/combined_data.csv", index=False)
        st.success(f"Combined data saved to {folder_path}/combined_data.csv")
        
def _sidebar(sidebar):
    global pv_names
    sidebar.title("Control Panel")
    with sidebar.expander("General settings"):
        st.session_state.autoupdate = st.checkbox("Auto Update", value=False)
        if st.session_state.autoupdate:
            st.session_state.update_interval = st.number_input(
                "Update Interval (s)", min_value=0.1, max_value=10., value=1., key="update_interval"
            )
    with sidebar.expander("Start saved server"):
        with st.form(key="start_saved_server"):
            pv_name = st.selectbox("Select Server", pv_names)
            reading_frequency = st.number_input("Reading Frequency (Hz)", min_value=0.1, max_value=10., value=1.)
            if st.form_submit_button("Start Server"):
                start_reader(pv_name, reading_frequency)
        sidebar.write("Don't see your server? Add it here.")
        new_pv_name = sidebar.text_input("Enter new server name")
        pv_names.append(new_pv_name)
        


    with st.sidebar.expander("Remove Server"):
        remove_server = st.selectbox("Select Server to Remove", list(st.session_state.readers.keys()))
        if st.button("Remove Server") and remove_server in st.session_state.readers:
            st.session_state.readers.pop(remove_server)
            st.sidebar.success(f"Server {remove_server} removed!")
                
    # Show all logged
    with st.sidebar.expander("Show All Servers"):
        for pv_name in st.session_state.readers:
            st.write(pv_name)
    # Button to save combined data frame
    st.sidebar.button("Save Combined Data", on_click=save_combined_dataframe)

    # Button to clear all servers
    if st.sidebar.button("Clear All Servers"):
        st.session_state.readers = {}
        st.sidebar.success("All servers cleared!")
        
def plot_time_series(data, title):
    fig = px.line(data, x='time', y='value', title=title)
    st.plotly_chart(fig)

def plot_histogram(data, bins, title):
    fig = px.histogram(data, x='value', nbins=bins, title=title)
    st.plotly_chart(fig)

def plot_x_vs_y(x_data, y_data, x_name, y_name, title):
    fig = px.scatter(x=x_data['value'], y=y_data['value'], labels={'x': x_name, 'y': y_name}, title=title)
    st.plotly_chart(fig)
    
def generate_plot(display_option):
    if display_option == "Time Series":
        with st.expander("Time Series Options"):
            reader = st.selectbox("Select Server", list(st.session_state.readers.keys()))
            data = st.session_state.readers[reader].get_data_frame()
            print(data)
            title = f"{reader} Time Series"
        plot_time_series(data, title)
    elif display_option == "Histogram": 
        with st.expander("Histogram Options"):
            reader = st.selectbox("Select Server", list(st.session_state.readers.keys()))
            data = st.session_state.readers[reader].get_batch(1000)
            title = f"{reader} Histogram"
            num_bins = st.number_input("Number of Bins", min_value=1, max_value=100, value=50)
            num_samples = st.number_input("Number of Samples", min_value=1, max_value=1000, value=100)
            data = reader.get_batch(num_samples)
        plot_histogram(data, num_bins, title)
    elif display_option == "X vs Y":
        with st.expander("X vs Y Options"):
            x_reader = st.selectbox("Select X Server", list(st.session_state.readers.keys()))
            y_reader = st.selectbox("Select Y Server", list(st.session_state.readers.keys()))
            x_data = st.session_state.readers[x_reader].get_data_frame()
            y_data = st.session_state.readers[y_reader].get_data_frame()
            title = f"{x_reader} vs {y_reader}"
        plot_x_vs_y(x_data, y_data, x_reader, y_reader, title)


def principal_element(placeholder):
    display_option = st.selectbox("Display Option", ["Time Series", "Histogram", "X vs Y"])
    with placeholder:
        if st.session_state.autoupdate:
            while True:
                generate_plot(display_option)
                time.sleep(st.session_state.update_interval)                 
                # Generate a stop button
                if st.button("Stop"):
                    break
        else:
            st.button("Generate Plot", on_click=generate_plot(display_option))
                    
                
                   
def main():
    st.set_page_config(page_title="Laser Lab Data Display", layout="wide")
    # Sidebar ############################################################
    sidebar = st.sidebar
    _sidebar(sidebar)
    # Main ##############################################################
    st.title("Combined Server EMA Display")
    if not st.session_state.readers:
        st.warning("No servers added yet. Use the control panel to add a server.")
    else:
        placeholder = st.empty()
        principal_element(placeholder)
    


main()
